# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

"""Strict station catalog loading, filtering, and accent-insensitive search."""

from __future__ import annotations

import datetime
import json
import pathlib
import re
import unicodedata
from collections import Counter
from collections.abc import Mapping
from typing import Any

from .entities import (
    CATEGORIES,
    VERIFICATION_STATUSES,
    CatalogMetadata,
    Station,
    Verification,
    is_safe_http_url,
)


_ROOT_FIELDS = frozenset(
    ("schemaVersion", "curator", "provenance", "importedAt", "stations")
)
_STATION_FIELDS = frozenset(
    (
        "id",
        "name",
        "streamUrl",
        "country",
        "tags",
        "category",
        "enabled",
        "availabilityNote",
        "verification",
    )
)
_VERIFICATION_FIELDS = frozenset(("status", "checkedAt", "detail"))
_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_COUNTRY_PATTERN = re.compile(r"^[A-Z]{2}$")


class CatalogDataError(ValueError):
    """Raised when a catalog cannot be read or does not match the data contract."""


def normalize_text(value: str) -> str:
    """Return a case-folded search form with Vietnamese accents removed."""

    replaced = value.translate(str.maketrans({"đ": "d", "Đ": "D"}))
    decomposed = unicodedata.normalize("NFKD", replaced)
    return "".join(
        character for character in decomposed
        if unicodedata.category(character) != "Mn"
    ).casefold()


def _require_mapping(value: Any, location: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise CatalogDataError(f"{location} must be an object")
    return value


def _require_exact_fields(
    value: Mapping[str, Any], expected: frozenset[str], location: str
) -> None:
    actual = frozenset(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise CatalogDataError(
            f"{location} fields do not match; missing={missing}, extra={extra}"
        )


def _require_string(value: Any, location: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise CatalogDataError(f"{location} must be a string")
    if not allow_empty and not value.strip():
        raise CatalogDataError(f"{location} must not be empty")
    return value


def _parse_verification(value: Any, location: str) -> Verification:
    document = _require_mapping(value, location)
    _require_exact_fields(document, _VERIFICATION_FIELDS, location)
    status = _require_string(document["status"], f"{location}.status")
    if status not in VERIFICATION_STATUSES:
        raise CatalogDataError(f"{location}.status is unsupported: {status!r}")
    checked_at = document["checkedAt"]
    if checked_at is not None:
        checked_at = _require_string(checked_at, f"{location}.checkedAt")
        try:
            checked_time = datetime.datetime.fromisoformat(checked_at.replace("Z", "+00:00"))
            if checked_time.tzinfo is None:
                raise ValueError("timezone required")
        except ValueError as error:
            raise CatalogDataError(f"{location}.checkedAt must include an ISO timestamp and timezone") from error
    if status != "unverified" and checked_at is None:
        raise CatalogDataError(
            f"{location}.checkedAt is required for status {status!r}"
        )
    detail = _require_string(
        document["detail"], f"{location}.detail", allow_empty=True
    )
    return Verification(status=status, checked_at=checked_at, detail=detail)


def _parse_station(value: Any, index: int) -> Station:
    location = f"stations[{index}]"
    document = _require_mapping(value, location)
    _require_exact_fields(document, _STATION_FIELDS, location)

    station_id = _require_string(document["id"], f"{location}.id")
    if _ID_PATTERN.fullmatch(station_id) is None:
        raise CatalogDataError(f"{location}.id has an invalid format")
    name = _require_string(document["name"], f"{location}.name")
    stream_url = _require_string(document["streamUrl"], f"{location}.streamUrl")
    if not is_safe_http_url(stream_url):
        raise CatalogDataError(f"{location}.streamUrl is not a safe HTTP(S) URL")
    country = _require_string(document["country"], f"{location}.country")
    if _COUNTRY_PATTERN.fullmatch(country) is None:
        raise CatalogDataError(f"{location}.country must be an ISO-style code")

    raw_tags = document["tags"]
    if not isinstance(raw_tags, list):
        raise CatalogDataError(f"{location}.tags must be an array")
    tags = tuple(
        _require_string(tag, f"{location}.tags[{tag_index}]")
        for tag_index, tag in enumerate(raw_tags)
    )
    if len(tags) != len(set(tags)):
        raise CatalogDataError(f"{location}.tags contains duplicates")

    category = _require_string(document["category"], f"{location}.category")
    if category not in CATEGORIES:
        raise CatalogDataError(f"{location}.category is unsupported: {category!r}")
    enabled = document["enabled"]
    if type(enabled) is not bool:
        raise CatalogDataError(f"{location}.enabled must be a boolean")
    availability_note = _require_string(
        document["availabilityNote"],
        f"{location}.availabilityNote",
        allow_empty=True,
    )
    verification = _parse_verification(
        document["verification"], f"{location}.verification"
    )
    return Station(
        station_id=station_id,
        name=name,
        stream_url=stream_url,
        country=country,
        tags=tags,
        category=category,
        enabled=enabled,
        availability_note=availability_note,
        verification=verification,
    )


class StationCatalog:
    """Validated, immutable view over the station facts."""

    def __init__(self, metadata: CatalogMetadata, stations: tuple[Station, ...]):
        self.metadata = metadata
        self.stations = stations
        self._by_id = {station.station_id: station for station in stations}
        self._search_index = {
            station.station_id: normalize_text(
                " ".join((station.name, station.station_id, *station.tags))
            )
            for station in stations
        }

    @classmethod
    def from_file(cls, path: str | pathlib.Path) -> StationCatalog:
        catalog_path = pathlib.Path(path)
        try:
            raw_text = catalog_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as error:
            raise CatalogDataError("catalog is not valid UTF-8") from error
        except OSError as error:
            raise CatalogDataError(f"cannot read catalog: {error}") from error
        try:
            document = json.loads(raw_text)
        except json.JSONDecodeError as error:
            raise CatalogDataError(f"catalog is not valid JSON: {error}") from error
        return cls.from_document(document)

    @classmethod
    def from_document(cls, value: Any) -> StationCatalog:
        document = _require_mapping(value, "catalog")
        _require_exact_fields(document, _ROOT_FIELDS, "catalog")
        if type(document["schemaVersion"]) is not int or document["schemaVersion"] != 1:
            raise CatalogDataError("catalog.schemaVersion must be 1")
        curator = _require_string(document["curator"], "catalog.curator")
        provenance = _require_string(document["provenance"], "catalog.provenance")
        imported_at = _require_string(document["importedAt"], "catalog.importedAt")
        try:
            datetime.date.fromisoformat(imported_at)
        except ValueError as error:
            raise CatalogDataError("catalog.importedAt must be an ISO date") from error
        raw_stations = document["stations"]
        if not isinstance(raw_stations, list):
            raise CatalogDataError("catalog.stations must be an array")
        stations = tuple(
            _parse_station(station, index)
            for index, station in enumerate(raw_stations)
        )
        if not stations:
            raise CatalogDataError("catalog.stations must not be empty")

        for label, values in (
            ("id", [station.station_id for station in stations]),
            ("name", [station.name for station in stations]),
            ("streamUrl", [station.stream_url for station in stations]),
        ):
            if len(values) != len(set(values)):
                duplicates = sorted(
                    value for value, count in Counter(values).items() if count > 1
                )
                raise CatalogDataError(f"duplicate station {label}: {len(duplicates)} duplicate values")

        metadata = CatalogMetadata(
            schema_version=1,
            curator=curator,
            provenance=provenance,
            imported_at=imported_at,
        )
        return cls(metadata, stations)

    def get(self, station_id: str) -> Station:
        return self._by_id[station_id]

    def select(
        self, *, category: str | None = None, include_disabled: bool = False
    ) -> tuple[Station, ...]:
        self._require_category(category)
        return tuple(
            station for station in self.stations
            if (include_disabled or station.enabled)
            and (category is None or station.category == category)
        )

    def search(
        self,
        query: str,
        *,
        category: str | None = None,
        group: str | None = None,
        include_disabled: bool = False,
    ) -> tuple[Station, ...]:
        self._require_category(category)
        if group is not None and category not in (None, "tv"):
            raise ValueError("group filtering is only supported for TV")
        terms = tuple(term for term in normalize_text(query).split() if term)
        candidates = self.select(
            category=category, include_disabled=include_disabled
        )
        return tuple(
            station for station in candidates
            if (group is None or station.group == group)
            and all(term in self._search_index[station.station_id] for term in terms)
        )

    def tv_groups(self, query: str = "") -> tuple[str, ...]:
        """Return visible TV groups in their stable catalog order."""

        groups: list[str] = []
        for station in self.search(query, category="tv"):
            if station.group not in groups:
                groups.append(station.group)
        return tuple(groups)

    def category_counts(self, *, include_disabled: bool = False) -> dict[str, int]:
        counts = Counter(
            station.category for station in self.stations
            if include_disabled or station.enabled
        )
        return {category: counts[category] for category in ("tv", "radio", "sport")}

    @staticmethod
    def _require_category(category: str | None) -> None:
        if category is not None and category not in CATEGORIES:
            raise ValueError(f"unsupported category: {category!r}")
