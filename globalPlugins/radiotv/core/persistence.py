# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

"""Versioned user-state storage with strict validation and atomic replacement."""

from __future__ import annotations

import json
import os
import pathlib
import tempfile
from dataclasses import dataclass
from typing import Any


CURRENT_SCHEMA_VERSION = 1
_CURRENT_FIELDS = frozenset(("schemaVersion", "favoriteIds", "volume"))
_LEGACY_FIELDS = frozenset(("favorites", "volume"))


class PersistenceError(ValueError):
    """Raised when user state is invalid or cannot be stored safely."""


@dataclass(frozen=True, slots=True)
class UserState:
    favorite_ids: tuple[str, ...] = ()
    volume: int = 100

    def __post_init__(self) -> None:
        if type(self.favorite_ids) is not tuple:
            raise PersistenceError("favorite_ids must be a tuple")
        if any(
            not isinstance(station_id, str) or not station_id.strip()
            for station_id in self.favorite_ids
        ):
            raise PersistenceError("favorite_ids must contain non-empty strings")
        if len(self.favorite_ids) != len(set(self.favorite_ids)):
            raise PersistenceError("favorite_ids must not contain duplicates")
        if type(self.volume) is not int or not 0 <= self.volume <= 100:
            raise PersistenceError("volume must be an integer from 0 to 100")


class StateStore:
    """Load and save one versioned JSON document at an explicit path."""

    def __init__(self, path: str | pathlib.Path):
        self.path = pathlib.Path(path)

    def load(self) -> UserState:
        state, _migrated = self._load_with_migration_flag()
        return state

    def load_and_upgrade(self) -> UserState:
        state, migrated = self._load_with_migration_flag()
        if migrated:
            self.save(state)
        return state

    def save(self, state: UserState) -> None:
        if not isinstance(state, UserState):
            raise PersistenceError("state must be a UserState")
        document = {
            "schemaVersion": CURRENT_SCHEMA_VERSION,
            "favoriteIds": list(state.favorite_ids),
            "volume": state.volume,
        }
        encoded = (
            json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        )
        temporary_path: pathlib.Path | None = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="\n",
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                dir=self.path.parent,
                delete=False,
            ) as temporary_file:
                temporary_path = pathlib.Path(temporary_file.name)
                temporary_file.write(encoded)
                temporary_file.flush()
                os.fsync(temporary_file.fileno())
            os.replace(temporary_path, self.path)
            temporary_path = None
        except OSError as error:
            raise PersistenceError(f"cannot save user state: {error}") from error
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass

    def _load_with_migration_flag(self) -> tuple[UserState, bool]:
        if not self.path.exists():
            return UserState(), False
        try:
            raw_text = self.path.read_text(encoding="utf-8")
        except UnicodeDecodeError as error:
            raise PersistenceError("user state is not valid UTF-8") from error
        except OSError as error:
            raise PersistenceError(f"cannot read user state: {error}") from error
        try:
            document = json.loads(raw_text)
        except json.JSONDecodeError as error:
            raise PersistenceError(f"user state is not valid JSON: {error}") from error
        if not isinstance(document, dict):
            raise PersistenceError("user state root must be an object")

        if "schemaVersion" not in document:
            if frozenset(document) != _LEGACY_FIELDS:
                raise PersistenceError("unsupported unversioned user state")
            state = self._decode_values(
                document["favorites"], document["volume"], "legacy user state"
            )
            return state, True

        if frozenset(document) != _CURRENT_FIELDS:
            raise PersistenceError("version 1 user state fields do not match")
        if type(document["schemaVersion"]) is not int:
            raise PersistenceError("schemaVersion must be an integer")
        if document["schemaVersion"] != CURRENT_SCHEMA_VERSION:
            raise PersistenceError(
                f"unsupported user-state schema: {document['schemaVersion']!r}"
            )
        return self._decode_values(
            document["favoriteIds"], document["volume"], "user state"
        ), False

    @staticmethod
    def _decode_values(favorites: Any, volume: Any, location: str) -> UserState:
        if not isinstance(favorites, list):
            raise PersistenceError(f"{location} favorites must be an array")
        try:
            favorite_ids = tuple(favorites)
            return UserState(favorite_ids=favorite_ids, volume=volume)
        except PersistenceError:
            raise
        except (TypeError, ValueError) as error:
            raise PersistenceError(f"invalid {location}: {error}") from error
