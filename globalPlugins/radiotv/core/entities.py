# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

"""Immutable entities shared by catalog, persistence, and later UI layers."""

from dataclasses import dataclass
import urllib.parse


CATEGORIES = frozenset(("tv", "radio", "sport"))
HTTP_USER_AGENT_TAG_PREFIX = "http-user-agent:"
DEFAULT_HTTP_USER_AGENT = "RadioTV/0.1"
VERIFICATION_STATUSES = frozenset(
    ("unverified", "reachable", "playback-confirmed", "failed")
)


def is_safe_http_url(value: object) -> bool:
    """Validate before URL parsing can silently strip embedded control characters."""
    if not isinstance(value, str) or not value or len(value) > 8192:
        return False
    if any(character.isspace() or ord(character) < 32 or ord(character) == 127 for character in value):
        return False
    try:
        parts = urllib.parse.urlsplit(value)
        port = parts.port
        return bool(
            parts.scheme in ("http", "https") and parts.hostname
            and parts.username is None and parts.password is None
            and (port is None or 0 < port <= 65535)
        )
    except ValueError:
        return False


@dataclass(frozen=True, slots=True)
class Verification:
    status: str
    checked_at: str | None
    detail: str


@dataclass(frozen=True, slots=True)
class Station:
    station_id: str
    name: str
    stream_url: str
    country: str
    tags: tuple[str, ...]
    category: str
    enabled: bool
    availability_note: str
    verification: Verification

    @property
    def group(self) -> str:
        """Return the display group encoded in catalog metadata tags."""

        for tag in self.tags:
            if tag.startswith("group:"):
                return tag[len("group:"):]
        return "📦 Kênh Khác"

    @property
    def epg_id(self) -> str:
        """Return the XMLTV channel identifier, when the source supplied one."""

        for tag in self.tags:
            if tag.startswith("epg:"):
                return tag[len("epg:"):]
        return ""

    @property
    def http_user_agent(self) -> str:
        """Return a safe per-stream User-Agent or the RadioTV default."""

        for tag in self.tags:
            if not tag.startswith(HTTP_USER_AGENT_TAG_PREFIX):
                continue
            value = tag[len(HTTP_USER_AGENT_TAG_PREFIX):]
            if (
                value
                and len(value) <= 256
                and "\r" not in value
                and "\n" not in value
                and all(ord(character) >= 32 and ord(character) != 127 for character in value)
            ):
                return value
        return DEFAULT_HTTP_USER_AGENT


@dataclass(frozen=True, slots=True)
class CatalogMetadata:
    schema_version: int
    curator: str
    provenance: str
    imported_at: str
