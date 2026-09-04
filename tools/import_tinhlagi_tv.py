# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

"""Import direct, non-DRM TV streams from the user-supplied playlist.

The remote document uses an M3U payload despite its ``.json`` suffix.  This
tool keeps every compatible domestic and international channel, prefers the
highest labelled quality when a channel is duplicated, and records unsupported
DRM/DASH URLs separately without retaining DRM directives or decryption keys.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys
import unicodedata
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import dataclass

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "globalPlugins"))
from radiotv.core.entities import is_safe_http_url
from catalog_io import write_catalog


DEFAULT_SOURCE_URL = "https://tinhlagi.pro/tv.json"
DEFAULT_EPG_URL = "https://lichphatsong.io.vn/epg.xml"
GROUP_TAG_PREFIX = "group:"
EPG_TAG_PREFIX = "epg:"
SOURCE_TAG = "source:tinhlagi"
SOURCE_METADATA_TAG = "source-meta:tinhlagi"
HTTP_USER_AGENT_TAG_PREFIX = "http-user-agent:"
FALLBACK_GROUP = "📦 Kênh Khác"
_ATTRIBUTE_PATTERN = re.compile(r'([A-Za-z0-9_-]+)="([^"]*)"')
_QUALITY_TOKEN_PATTERN = re.compile(
    r"\b(?:4k|uhd|2160p?|fhd|full\s*hd|1080[pi]?|hd|720[pi]?|sd|576[pi]?|480[pi]?)\b",
    re.IGNORECASE,
)
_ALTERNATE_TOKEN_PATTERN = re.compile(
    r"\b(?:backup|du\s*phong|server\s*\d+|link\s*\d+)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class PlaylistEntry:
    name: str
    stream_url: str
    group: str
    epg_id: str
    source_index: int
    http_user_agent: str


@dataclass(frozen=True, slots=True)
class UnsupportedEntry:
    name: str
    stream_url: str
    group: str
    epg_id: str
    source_index: int
    reason: str


@dataclass(frozen=True, slots=True)
class ParseResult:
    entries: tuple[PlaylistEntry, ...]
    compatible_candidates: tuple[PlaylistEntry, ...]
    unsupported_entries: tuple[UnsupportedEntry, ...]
    epg_url: str
    group_order: tuple[str, ...]
    skipped: Counter


def _clean_text(value: str) -> str:
    return " ".join(value.replace("\ufeff", "").split()).strip()


def _normalise(value: str) -> str:
    replaced = value.translate(str.maketrans({"đ": "d", "Đ": "D"}))
    decomposed = unicodedata.normalize("NFKD", replaced)
    return "".join(
        character for character in decomposed
        if unicodedata.category(character) != "Mn"
    ).casefold()


def canonical_channel_name(value: str) -> str:
    """Return a quality-neutral identity for duplicate channel comparison."""

    normalised = _normalise(value)
    without_quality = _QUALITY_TOKEN_PATTERN.sub(" ", normalised)
    without_alternates = _ALTERNATE_TOKEN_PATTERN.sub(" ", without_quality)
    canonical = "".join(
        character for character in without_alternates if character.isalnum()
    )
    sctv_match = re.fullmatch(
        r"sctv(\d+)(?:todaytv|fim360|tintuc|phim|vietnamkyuc)?",
        canonical,
    )
    if sctv_match is not None:
        return f"sctv{sctv_match.group(1)}"
    return canonical or "".join(
        character for character in normalised if character.isalnum()
    )


def quality_score(name: str, stream_url: str = "") -> int:
    """Rank labelled stream quality; a larger value is preferred."""

    name_text = _normalise(name)
    url_text = urllib.parse.unquote(stream_url).casefold()
    for text, explicit_bonus in ((name_text, 20), (url_text, 0)):
        if re.search(r"\b(?:4k|uhd|2160p?)\b", text):
            return 500 + explicit_bonus
        if re.search(r"\b(?:fhd|full\s*hd|1080[pi]?)\b", text):
            return 400 + explicit_bonus
        if re.search(r"\b(?:hd|720[pi]?)\b", text):
            return 300 + explicit_bonus
        if re.search(r"\b(?:sd|576[pi]?|480[pi]?)\b", text):
            return 100 + explicit_bonus
    return 200


def _prefer_entry(current, candidate):
    channel_key = canonical_channel_name(current.name)

    def source_group_rank(entry) -> int:
        return int(
            channel_key.startswith("sctv")
            and "sctv" in _normalise(entry.group)
        )

    current_rank = (
        source_group_rank(current),
        quality_score(current.name, current.stream_url),
        -current.source_index,
    )
    candidate_rank = (
        source_group_rank(candidate),
        quality_score(candidate.name, candidate.stream_url),
        -candidate.source_index,
    )
    return candidate if candidate_rank > current_rank else current


def _deduplicate_entries(entries, skipped: Counter, *, prefix: str = ""):
    by_channel = {}
    for entry in entries:
        key = canonical_channel_name(entry.name)
        current = by_channel.get(key)
        if current is None:
            by_channel[key] = entry
            continue
        preferred = _prefer_entry(current, entry)
        if preferred is not current:
            skipped[f"{prefix}preferred_higher_quality"] += 1
        by_channel[key] = preferred
        skipped[f"{prefix}duplicate_channel"] += 1

    by_url = {}
    for entry in sorted(by_channel.values(), key=lambda item: item.source_index):
        current = by_url.get(entry.stream_url)
        if current is None:
            by_url[entry.stream_url] = entry
            continue
        preferred = _prefer_entry(current, entry)
        if preferred is not current:
            skipped[f"{prefix}preferred_higher_quality"] += 1
        by_url[entry.stream_url] = preferred
        skipped[f"{prefix}duplicate_url"] += 1
    return sorted(by_url.values(), key=lambda item: item.source_index)


def _safe_http_url(value: str) -> bool:
    return is_safe_http_url(value)


def _is_dash_url(value: str) -> bool:
    return urllib.parse.urlsplit(value).path.casefold().endswith(".mpd")


def _safe_user_agent(value: str) -> str:
    cleaned = _clean_text(value.strip().strip('"'))
    if (
        not cleaned
        or len(cleaned) > 256
        or any(ord(character) < 32 or ord(character) == 127 for character in cleaned)
    ):
        return ""
    return cleaned


def parse_playlist(text: str) -> ParseResult:
    """Parse safe direct entries without retaining any DRM material."""

    lines = [line.strip() for line in text.splitlines()]
    if not lines or not lines[0].lstrip("\ufeff").startswith("#EXTM3U"):
        raise ValueError("source is not an M3U playlist")
    header_attributes = dict(_ATTRIBUTE_PATTERN.findall(lines[0]))
    epg_url = header_attributes.get("url-tvg", DEFAULT_EPG_URL)
    if not _safe_http_url(epg_url):
        epg_url = DEFAULT_EPG_URL

    entries: list[PlaylistEntry] = []
    unsupported_entries: list[UnsupportedEntry] = []
    group_order: list[str] = []
    skipped: Counter = Counter()
    pending: dict[str, object] | None = None
    source_index = 0

    for line in lines[1:]:
        if line.startswith("#EXTINF"):
            source_index += 1
            attributes = dict(_ATTRIBUTE_PATTERN.findall(line))
            _, separator, display_name = line.partition(",")
            group = _clean_text(attributes.get("group-title", "")) or FALLBACK_GROUP
            name = _clean_text(display_name if separator else attributes.get("tvg-name", ""))
            pending = {
                "name": name,
                "group": group,
                "epg_id": _clean_text(attributes.get("tvg-id", "")),
                "source_index": source_index,
                "has_drm": False,
                "http_user_agent": "",
            }
            continue
        if pending is None or not line:
            continue
        if line.startswith("#"):
            lowered = line.casefold()
            if lowered.startswith("#extvlcopt:http-user-agent="):
                user_agent = _safe_user_agent(line.partition("=")[2])
                if user_agent:
                    pending["http_user_agent"] = user_agent
                else:
                    skipped["unsafe_http_user_agent"] += 1
                continue
            if (
                lowered.startswith("#kodiprop:")
                or "license_key" in lowered
                or "license_type" in lowered
                or "inputstream.adaptive" in lowered
            ):
                pending["has_drm"] = True
            continue

        name = str(pending["name"])
        group = str(pending["group"])
        if group == "🎯 TINHLAGI.PRO" or not name:
            skipped["metadata"] += 1
        elif not _safe_http_url(line):
            skipped["unsafe_url"] += 1
        elif bool(pending["has_drm"]) or _is_dash_url(line):
            reason = "drm" if bool(pending["has_drm"]) else "mpeg-dash"
            unsupported_entries.append(
                UnsupportedEntry(
                    name=name,
                    stream_url=line,
                    group=group,
                    epg_id=str(pending["epg_id"]),
                    source_index=int(pending["source_index"]),
                    reason=reason,
                )
            )
            skipped["unsupported_drm_or_dash"] += 1
        else:
            if group not in group_order:
                group_order.append(group)
            entries.append(
                PlaylistEntry(
                    name=name,
                    stream_url=line,
                    group=group,
                    epg_id=str(pending["epg_id"]),
                    source_index=int(pending["source_index"]),
                    http_user_agent=str(pending["http_user_agent"]),
                )
            )
        pending = None

    unique_entries = _deduplicate_entries(entries, skipped)
    unique_unsupported = _deduplicate_entries(
        unsupported_entries,
        skipped,
        prefix="unsupported_",
    )
    non_empty_groups = {entry.group for entry in unique_entries}
    return ParseResult(
        entries=tuple(unique_entries),
        compatible_candidates=tuple(entries),
        unsupported_entries=tuple(unique_unsupported),
        epg_url=epg_url,
        group_order=tuple(
            group for group in group_order if group in non_empty_groups
        ),
        skipped=skipped,
    )


def fetch_source(url: str) -> str:
    if not _safe_http_url(url):
        raise ValueError("source must be a safe HTTP(S) URL")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "RadioTV/0.1 (+NVDA add-on)"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = response.read(16 * 1024 * 1024 + 1)
        if len(payload) > 16 * 1024 * 1024:
            raise ValueError("playlist is too large")
        return payload.decode("utf-8-sig")


def _station_id(entry: PlaylistEntry) -> str:
    base = _normalise(entry.name)
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-") or "tv"
    digest = hashlib.sha256(
        f"{entry.name}\0{entry.stream_url}".encode("utf-8")
    ).hexdigest()[:8]
    return f"tl-{base[:42].rstrip('-')}-{digest}"


def _metadata_tags(entry: PlaylistEntry) -> list[str]:
    tags = ["tv", f"{GROUP_TAG_PREFIX}{entry.group}", SOURCE_TAG]
    if entry.epg_id:
        tags.append(f"{EPG_TAG_PREFIX}{entry.epg_id}")
    if entry.http_user_agent:
        tags.append(f"{HTTP_USER_AGENT_TAG_PREFIX}{entry.http_user_agent}")
    return tags


def _replace_metadata_tags(tags: list[str], entry: PlaylistEntry) -> list[str]:
    kept = [
        tag for tag in tags
        if not tag.startswith(GROUP_TAG_PREFIX)
        and not tag.startswith(EPG_TAG_PREFIX)
        and tag != SOURCE_TAG
        and tag != SOURCE_METADATA_TAG
        and not tag.startswith(HTTP_USER_AGENT_TAG_PREFIX)
    ]
    metadata_tags = ["tv", f"{GROUP_TAG_PREFIX}{entry.group}", SOURCE_METADATA_TAG]
    if entry.epg_id:
        metadata_tags.append(f"{EPG_TAG_PREFIX}{entry.epg_id}")
    if entry.http_user_agent:
        metadata_tags.append(
            f"{HTTP_USER_AGENT_TAG_PREFIX}{entry.http_user_agent}"
        )
    for tag in metadata_tags:
        if tag not in kept:
            kept.append(tag)
    return kept


def merge_catalog(document: dict, result: ParseResult) -> tuple[dict, Counter]:
    """Merge all compatible channels and prefer HD when identities collide."""
    if not result.entries:
        raise ValueError("refusing to replace the catalog with an empty playlist")
    stats: Counter = Counter()
    source_status_overrides = {
        (canonical_channel_name(station["name"]), station["streamUrl"]): station
        for station in document["stations"]
        if station["id"].startswith("tl-")
        and SOURCE_TAG in station.get("tags", ())
        and station["verification"]["status"] in ("reachable", "playback-confirmed")
    }
    failed_source_overrides = {
        (canonical_channel_name(station["name"]), station["streamUrl"]): station
        for station in document["stations"]
        if station["id"].startswith("tl-")
        and SOURCE_TAG in station.get("tags", ())
        and station["verification"]["status"] == "failed"
    }
    source_metadata_ids = {
        station["id"] for station in document["stations"]
        if SOURCE_METADATA_TAG in station.get("tags", ())
    }
    failed_source_metadata_ids = {
        station["id"] for station in document["stations"]
        if station["id"] in source_metadata_ids
        and station["verification"]["status"] == "failed"
    }
    old_stations = [
        {
            **station,
            "tags": list(station["tags"]),
            "verification": dict(station["verification"]),
        }
        for station in document["stations"]
        if not (
            station["id"].startswith("tl-")
            and SOURCE_TAG in station.get("tags", ())
        )
    ]
    stats["removed_previous_import"] = len(document["stations"]) - len(old_stations)
    for station in old_stations:
        if SOURCE_METADATA_TAG not in station["tags"]:
            continue
        station["tags"] = [
            tag for tag in station["tags"]
            if tag != SOURCE_METADATA_TAG
            and not tag.startswith(GROUP_TAG_PREFIX)
            and not tag.startswith(EPG_TAG_PREFIX)
            and not tag.startswith(HTTP_USER_AGENT_TAG_PREFIX)
        ]

    retained: list[dict] = []
    existing_by_channel: dict[str, dict] = {}
    for station in old_stations:
        if station["category"] != "tv":
            retained.append(station)
            continue
        channel_key = canonical_channel_name(station["name"])
        current = existing_by_channel.get(channel_key)
        if current is None:
            existing_by_channel[channel_key] = station
            retained.append(station)
            continue
        current_rank = (
            quality_score(current["name"], current["streamUrl"]),
            current["enabled"],
            current["verification"]["status"] == "playback-confirmed",
        )
        candidate_rank = (
            quality_score(station["name"], station["streamUrl"]),
            station["enabled"],
            station["verification"]["status"] == "playback-confirmed",
        )
        if candidate_rank > current_rank:
            retained.remove(current)
            retained.append(station)
            existing_by_channel[channel_key] = station
        stats["removed_existing_duplicate"] += 1
    old_stations = retained
    used_urls = {station["streamUrl"] for station in old_stations}
    source_rank: dict[str, int] = {}

    for entry in result.entries:
        channel_key = canonical_channel_name(entry.name)
        source_rank.setdefault(channel_key, entry.source_index)
        existing = existing_by_channel.get(channel_key)
        if existing is not None:
            higher_quality = quality_score(
                entry.name, entry.stream_url
            ) > quality_score(
                existing["name"], existing["streamUrl"]
            )
            refresh_managed_source = (
                channel_key.startswith("sctv")
                and entry.stream_url != existing["streamUrl"]
            )
            if higher_quality or refresh_managed_source:
                if entry.stream_url in used_urls and entry.stream_url != existing["streamUrl"]:
                    stats["duplicate_existing_url"] += 1
                    existing["tags"] = _replace_metadata_tags(existing["tags"], entry)
                    continue
                used_urls.discard(existing["streamUrl"])
                existing["name"] = entry.name
                existing["streamUrl"] = entry.stream_url
                existing["availabilityNote"] = (
                    "Nguồn hiện tại do người dùng cung cấp; luồng HTTP(S) trực tiếp, không DRM."
                )
                existing["verification"] = {
                    "status": "unverified",
                    "checkedAt": None,
                    "detail": (
                        "Đã cập nhật theo danh mục nguồn hiện tại; "
                        "chưa xác minh bằng backend RadioTV mới."
                    ),
                }
                existing["enabled"] = True
                used_urls.add(entry.stream_url)
                if higher_quality:
                    stats["upgraded_existing_to_higher_quality"] += 1
                if refresh_managed_source:
                    stats["refreshed_existing_source_url"] += 1
            if existing["id"] in failed_source_metadata_ids:
                existing["enabled"] = True
                existing["availabilityNote"] = (
                    "Đã khôi phục nguồn người dùng cung cấp để kiểm tra với backend mới."
                )
                existing["verification"] = {
                    "status": "unverified",
                    "checkedAt": None,
                    "detail": (
                        "Lỗi backend cũ không còn được coi là bằng chứng nguồn chết."
                    ),
                }
                stats["restored_failed_source"] += 1
            existing["tags"] = _replace_metadata_tags(existing["tags"], entry)
            stats["matched_existing"] += 1
            continue
        if entry.stream_url in used_urls:
            stats["duplicate_existing_url"] += 1
            continue
        station = {
            "id": _station_id(entry),
            "name": entry.name,
            "streamUrl": entry.stream_url,
            "country": "VN",
            "tags": _metadata_tags(entry),
            "category": "tv",
            "enabled": True,
            "availabilityNote": (
                "Nguồn TV do người dùng cung cấp; luồng HTTP(S) trực tiếp, không DRM."
            ),
            "verification": {
                "status": "unverified",
                "checkedAt": None,
                "detail": "Người dùng đã kiểm tra nguồn; chưa xác minh bằng backend RadioTV.",
            },
        }
        status_override = source_status_overrides.get(
            (channel_key, entry.stream_url)
        )
        if status_override is not None:
            station["enabled"] = status_override["enabled"]
            station["availabilityNote"] = status_override["availabilityNote"]
            station["verification"] = dict(status_override["verification"])
            stats["preserved_source_status_override"] += 1
        elif (channel_key, entry.stream_url) in failed_source_overrides:
            station["availabilityNote"] = (
                "Đã khôi phục nguồn người dùng cung cấp để kiểm tra với backend mới."
            )
            station["verification"]["detail"] = (
                "Lỗi backend cũ không còn được coi là bằng chứng nguồn chết."
            )
            stats["restored_failed_source"] += 1
        old_stations.append(station)
        existing_by_channel[channel_key] = station
        used_urls.add(entry.stream_url)
        stats["added"] += 1

    for station in old_stations:
        if station["category"] != "tv":
            continue
        if not any(tag.startswith(GROUP_TAG_PREFIX) for tag in station["tags"]):
            station["tags"].append(f"{GROUP_TAG_PREFIX}{FALLBACK_GROUP}")
            stats["assigned_fallback_group"] += 1

    group_rank = {group: index for index, group in enumerate(result.group_order)}

    def tv_sort_key(station: dict) -> tuple[int, int, str]:
        group = next(
            (
                tag[len(GROUP_TAG_PREFIX):]
                for tag in station["tags"]
                if tag.startswith(GROUP_TAG_PREFIX)
            ),
            FALLBACK_GROUP,
        )
        channel_key = canonical_channel_name(station["name"])
        return (
            group_rank.get(group, len(group_rank)),
            source_rank.get(channel_key, 1_000_000),
            channel_key,
        )

    tv_stations = sorted(
        (station for station in old_stations if station["category"] == "tv"),
        key=tv_sort_key,
    )
    non_tv = [station for station in old_stations if station["category"] != "tv"]
    merged = dict(document)
    merged["stations"] = tv_stations + non_tv
    return merged, stats


def unsupported_document(result: ParseResult, source_url: str) -> dict:
    """Build a key-free inventory for a future backend with DASH/DRM support."""

    return {
        "schemaVersion": 1,
        "source": source_url,
        "policy": (
            "Không đưa vào RadioTV 0.1 vì BASS/BASSHLS không hỗ trợ. "
            "Không lưu chỉ dẫn hoặc khóa DRM."
        ),
        "entries": [
            {
                "name": entry.name,
                "streamUrl": entry.stream_url,
                "group": entry.group,
                "epgId": entry.epg_id,
                "reason": entry.reason,
            }
            for entry in result.unsupported_entries
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-url", default=DEFAULT_SOURCE_URL)
    parser.add_argument("--catalog", type=pathlib.Path, required=True)
    parser.add_argument("--unsupported-output", type=pathlib.Path)
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args(argv)

    result = parse_playlist(fetch_source(arguments.source_url))
    print(f"EPG: {result.epg_url}")
    print(f"Compatible unique entries: {len(result.entries)}")
    print(f"Unsupported unique entries recorded: {len(result.unsupported_entries)}")
    print("Groups:")
    group_counts = Counter(entry.group for entry in result.entries)
    for group in result.group_order:
        print(f"  {group}: {group_counts[group]}")
    print("Skipped:")
    for reason, count in result.skipped.most_common():
        print(f"  {reason}: {count}")

    document = json.loads(arguments.catalog.read_text(encoding="utf-8"))
    merged, merge_stats = merge_catalog(document, result)
    print("Merge preview:")
    for reason, count in merge_stats.items():
        print(f"  {reason}: {count}")
    print(f"  total stations: {len(merged['stations'])}")
    if arguments.write:
        write_catalog(arguments.catalog, merged)
        print(f"Updated: {arguments.catalog}")
        unsupported_path = arguments.unsupported_output or (
            arguments.catalog.parent / "tv_sources_unsupported.json"
        )
        unsupported_path.write_text(
            json.dumps(
                unsupported_document(result, arguments.source_url),
                ensure_ascii=False,
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )
        print(f"Recorded unsupported sources without DRM keys: {unsupported_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
