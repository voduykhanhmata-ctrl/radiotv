# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

"""Import direct HLS football events from the user-supplied playlist."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys
import urllib.parse
from collections import Counter
from dataclasses import dataclass

TOOLS_DIR = pathlib.Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from import_tinhlagi_tv import (
    EPG_TAG_PREFIX,
    GROUP_TAG_PREFIX,
    PlaylistEntry,
    canonical_channel_name,
    fetch_source,
    parse_playlist,
    quality_score,
    HTTP_USER_AGENT_TAG_PREFIX,
)
from catalog_io import write_catalog


DEFAULT_SOURCE_URL = "https://tinhlagi.pro/s.m3u"
SOURCE_TAG = "source:tinhlagi-football"
_VARIANT_SUFFIX = re.compile(
    r"\s*\[(?:hls(?:\s*\d+)?|flv(?:\s*\d+)?)\]\s*$",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class FootballParseResult:
    entries: tuple[PlaylistEntry, ...]
    unsupported: tuple[dict[str, str], ...]
    skipped: Counter


def _base_event_name(name: str) -> str:
    cleaned = _VARIANT_SUFFIX.sub("", name).strip()
    return re.sub(
        r"(\[(?:4K|FHD|HD)\])(?:\s+\1)+", r"\1", cleaned,
        flags=re.IGNORECASE,
    )


def _provider_name(group: str) -> str:
    cleaned = re.sub(r"^[^\w]+", "", group, flags=re.UNICODE).strip()
    return cleaned or "Nguồn bóng đá"


def _is_hls_url(url: str) -> bool:
    return urllib.parse.urlsplit(url).path.casefold().endswith(".m3u8")


def _entry_rank(entry: PlaylistEntry) -> tuple[int, int, int]:
    name = entry.name.casefold()
    primary_hls = not bool(re.search(r"\[hls\s*\d+\]\s*$", name))
    return (
        quality_score(entry.name, entry.stream_url),
        int(primary_hls),
        -entry.source_index,
    )


def parse_football_playlist(text: str) -> FootballParseResult:
    """Keep one primary HLS stream per provider/event/commentator identity."""

    parsed = parse_playlist(text)
    skipped = Counter(parsed.skipped)
    by_event: dict[tuple[str, str], PlaylistEntry] = {}
    unsupported: list[dict[str, str]] = []

    for entry in parsed.compatible_candidates:
        if "tinhlagi.pro" in entry.group.casefold():
            skipped["metadata"] += 1
            continue
        if not _is_hls_url(entry.stream_url):
            path = urllib.parse.urlsplit(entry.stream_url).path.casefold()
            reason = "unsupported-flv" if path.endswith(".flv") else "non-hls"
            unsupported.append({
                "name": entry.name,
                "streamUrl": entry.stream_url,
                "group": entry.group,
                "reason": reason,
            })
            skipped[reason] += 1
            continue

        identity = canonical_channel_name(_base_event_name(entry.name))
        key = (entry.group.casefold(), identity)
        current = by_event.get(key)
        if current is None or _entry_rank(entry) > _entry_rank(current):
            if current is not None:
                skipped["preferred_primary_hls"] += 1
            by_event[key] = entry
        skipped["duplicate_event_variant"] += int(current is not None)

    unique_by_url: dict[str, PlaylistEntry] = {}
    for entry in sorted(by_event.values(), key=lambda item: item.source_index):
        current = unique_by_url.get(entry.stream_url)
        if current is None or _entry_rank(entry) > _entry_rank(current):
            unique_by_url[entry.stream_url] = entry
        skipped["duplicate_url"] += int(current is not None)

    return FootballParseResult(
        entries=tuple(sorted(
            unique_by_url.values(), key=lambda item: item.source_index
        )),
        unsupported=tuple(unsupported),
        skipped=skipped,
    )


def _station_name(entry: PlaylistEntry) -> str:
    return f"{_base_event_name(entry.name)} — {_provider_name(entry.group)}"


def _station_id(entry: PlaylistEntry) -> str:
    name = _station_name(entry)
    base = canonical_channel_name(name) or "football"
    digest = hashlib.sha256(
        f"{name}\0{entry.stream_url}".encode("utf-8")
    ).hexdigest()[:8]
    return f"fb-{base[:42]}-{digest}"


def _station_tags(entry: PlaylistEntry) -> list[str]:
    tags = ["football", "sport", f"{GROUP_TAG_PREFIX}{entry.group}", SOURCE_TAG]
    if entry.epg_id:
        tags.append(f"{EPG_TAG_PREFIX}{entry.epg_id}")
    if entry.http_user_agent:
        tags.append(f"{HTTP_USER_AGENT_TAG_PREFIX}{entry.http_user_agent}")
    return tags


def merge_catalog(
    document: dict, result: FootballParseResult
) -> tuple[dict, Counter]:
    """Replace the previous football-source import without touching other data."""
    if not result.entries:
        raise ValueError("refusing to replace the catalog with an empty playlist")
    stats: Counter = Counter()
    status_overrides = {
        (station["name"], station["streamUrl"]): station
        for station in document["stations"]
        if station["id"].startswith("fb-")
        and SOURCE_TAG in station.get("tags", ())
        and station["verification"]["status"] != "unverified"
    }
    retained = [
        station for station in document["stations"]
        if not (
            station["id"].startswith("fb-")
            and SOURCE_TAG in station.get("tags", ())
        )
    ]
    stats["removed_previous_import"] = len(document["stations"]) - len(retained)
    used_names = {station["name"] for station in retained}
    used_urls = {station["streamUrl"] for station in retained}

    imported: list[dict] = []
    for entry in result.entries:
        name = _station_name(entry)
        if name in used_names:
            stats["duplicate_existing_name"] += 1
            continue
        if entry.stream_url in used_urls:
            stats["duplicate_existing_url"] += 1
            continue
        station = {
            "id": _station_id(entry),
            "name": name,
            "streamUrl": entry.stream_url,
            "country": "VN",
            "tags": _station_tags(entry),
            "category": "sport",
            "enabled": True,
            "availabilityNote": (
                "Nguồn bóng đá HLS do người dùng cung cấp; lịch trận có thể thay đổi."
            ),
            "verification": {
                "status": "unverified",
                "checkedAt": None,
                "detail": (
                    "Đã loại bản FLV/trùng; chưa xác minh bằng backend RadioTV."
                ),
            },
        }
        override = status_overrides.get((name, entry.stream_url))
        if override is not None:
            station["enabled"] = override["enabled"]
            station["availabilityNote"] = override["availabilityNote"]
            station["verification"] = dict(override["verification"])
            stats["preserved_source_status_override"] += 1
        imported.append(station)
        used_names.add(name)
        used_urls.add(entry.stream_url)
        stats["added"] += 1

    non_sport = [station for station in retained if station["category"] != "sport"]
    existing_sport = [station for station in retained if station["category"] == "sport"]
    merged = dict(document)
    merged["stations"] = non_sport + existing_sport + imported
    return merged, stats


def unsupported_document(result: FootballParseResult, source_url: str) -> dict:
    return {
        "schemaVersion": 1,
        "source": source_url,
        "policy": (
            "Không đưa FLV hoặc URL không phải HLS vào RadioTV 0.1; "
            "không lưu chỉ dẫn hay khóa DRM."
        ),
        "entries": list(result.unsupported),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-url", default=DEFAULT_SOURCE_URL)
    parser.add_argument("--catalog", type=pathlib.Path, required=True)
    parser.add_argument("--unsupported-output", type=pathlib.Path)
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args(argv)

    result = parse_football_playlist(fetch_source(arguments.source_url))
    print(f"Compatible unique football entries: {len(result.entries)}")
    print(f"Unsupported candidates recorded: {len(result.unsupported)}")
    print("Groups:")
    group_counts = Counter(entry.group for entry in result.entries)
    for group, count in group_counts.items():
        print(f"  {group}: {count}")
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
            arguments.catalog.parent / "football_sources_unsupported.json"
        )
        unsupported_path.write_text(
            json.dumps(
                unsupported_document(result, arguments.source_url),
                ensure_ascii=False,
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )
        print(f"Recorded unsupported sources: {unsupported_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
