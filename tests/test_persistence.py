# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "globalPlugins"))

from radiotv.core.persistence import (  # noqa: E402
    PersistenceError,
    StateStore,
    UserState,
)


class PersistenceTests(unittest.TestCase):

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory(
            prefix="radiotv-persistence-test-"
        )
        self.directory = pathlib.Path(self.temporary_directory.name)
        self.path = self.directory / "user-state.json"
        self.store = StateStore(self.path)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_missing_file_returns_safe_defaults(self):
        self.assertEqual(UserState(), self.store.load())
        self.assertFalse(self.path.exists())

    def test_round_trip_preserves_favorites_and_volume(self):
        expected = UserState(("vn-vov1", "vn-vov3"), 37)
        self.store.save(expected)
        self.assertEqual(expected, self.store.load())
        document = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(1, document["schemaVersion"])
        self.assertEqual(["vn-vov1", "vn-vov3"], document["favoriteIds"])

    def test_legacy_document_is_migrated_by_explicit_upgrade(self):
        self.path.write_text(
            json.dumps({"favorites": ["vn-vov2"], "volume": 65}),
            encoding="utf-8",
        )
        state = self.store.load_and_upgrade()
        self.assertEqual(UserState(("vn-vov2",), 65), state)
        upgraded = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(
            {"schemaVersion": 1, "favoriteIds": ["vn-vov2"], "volume": 65},
            upgraded,
        )

    def test_rejects_invalid_json_and_invalid_types(self):
        self.path.write_text("[", encoding="utf-8")
        with self.assertRaises(PersistenceError):
            self.store.load()

        self.path.write_bytes(b"\xff")
        with self.assertRaisesRegex(PersistenceError, "UTF-8"):
            self.store.load()

        self.path.write_text(
            json.dumps({"schemaVersion": 1, "favoriteIds": [], "volume": "80"}),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(PersistenceError, "volume"):
            self.store.load()

    def test_rejects_duplicates_and_unknown_fields(self):
        with self.assertRaisesRegex(PersistenceError, "duplicates"):
            UserState(("vn-vov1", "vn-vov1"), 100)

        self.path.write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "favoriteIds": [],
                    "volume": 100,
                    "surprise": True,
                }
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(PersistenceError, "fields"):
            self.store.load()

    def test_failed_replace_preserves_old_file_and_removes_temp_file(self):
        original = UserState(("vn-vov1",), 20)
        self.store.save(original)
        with mock.patch(
            "radiotv.core.persistence.os.replace",
            side_effect=OSError("simulated replace failure"),
        ):
            with self.assertRaises(PersistenceError):
                self.store.save(UserState(("vn-vov2",), 90))
        self.assertEqual(original, self.store.load())
        self.assertEqual([], list(self.directory.glob("*.tmp")))
        self.assertEqual([], list(self.directory.glob(".*.tmp")))


if __name__ == "__main__":
    unittest.main()
