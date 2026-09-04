# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

import copy
import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import release_support
from import_tinhlagi_tv import parse_playlist, merge_catalog
from import_tinhlagi_football import parse_football_playlist, merge_catalog as merge_football
from catalog_io import write_catalog


class ReleaseToolTests(unittest.TestCase):
    def test_build_gate_rejects_missing_failed_and_stale_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory)
            with self.assertRaises(RuntimeError):
                release_support.require_validation(path)
            for architecture in ("x64", "x86"):
                report = {"architecture": architecture, "successful": True,
                          "version": release_support.version(), "fingerprint": release_support.fingerprint(), "testsRun": 1}
                (path / f"validation-{architecture}.json").write_text(json.dumps(report), encoding="utf-8")
            release_support.require_validation(path)
            with mock.patch.object(release_support, "fingerprint", return_value="modified"):
                with self.assertRaises(RuntimeError):
                    release_support.require_validation(path)
            report["successful"] = False
            (path / "validation-x86.json").write_text(json.dumps(report), encoding="utf-8")
            with self.assertRaises(RuntimeError):
                release_support.require_validation(path)

    def test_package_allowlist_excludes_scratch_and_unsupported_inventory(self):
        names = [path.relative_to(ROOT).as_posix() for path in release_support.package_files()]
        self.assertFalse(any("unsupported" in name or name.startswith(("work/", "vendor/", "tests/", "reports/")) for name in names))
        self.assertIn("globalPlugins/radiotv/support/diagnostics.py", names)

    def test_empty_import_cannot_delete_the_existing_catalog(self):
        document = json.loads((ROOT / "data/stations.json").read_text(encoding="utf-8"))
        original = copy.deepcopy(document)
        with self.assertRaises(ValueError):
            merge_catalog(document, parse_playlist("#EXTM3U\n"))
        with self.assertRaises(ValueError):
            merge_football(document, parse_football_playlist("#EXTM3U\n"))
        self.assertEqual(original, document)

    def test_invalid_catalog_never_overwrites_previous_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "stations.json"
            path.write_bytes(b"previous data")
            with self.assertRaises(ValueError):
                write_catalog(path, {})
            self.assertEqual(b"previous data", path.read_bytes())

    def test_malformed_playlist_url_is_skipped(self):
        parsed = parse_playlist('#EXTM3U\n#EXTINF:-1 group-title="TV",Broken\nhttps://[\n')
        self.assertEqual((), parsed.entries)
        self.assertEqual(1, parsed.skipped["unsafe_url"])
