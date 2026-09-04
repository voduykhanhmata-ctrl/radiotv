# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

import copy
import importlib.util
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))
MODULE_PATH = TOOLS / "import_tinhlagi_football.py"
SPEC = importlib.util.spec_from_file_location(
    "import_tinhlagi_football", MODULE_PATH
)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class FootballSourceImportTests(unittest.TestCase):

    PLAYLIST = """#EXTM3U
#EXTINF:-1 group-title="🔴 COLA TV",19:00 Đội A vs Đội B (FHD) [flv]
https://example.test/match.flv
#EXTINF:-1 group-title="🔴 COLA TV",19:00 Đội A vs Đội B (FHD) [hls 2]
https://example.test/match-backup.m3u8
#EXTINF:-1 group-title="🔴 COLA TV",19:00 Đội A vs Đội B (FHD) [hls]
https://example.test/match.m3u8
#EXTINF:-1 group-title="🌈 TINHLAGI.PRO",Cập Nhật
https://example.test/banner.jpg
"""

    def test_parser_keeps_primary_hls_and_drops_metadata_and_flv(self):
        result = MODULE.parse_football_playlist(self.PLAYLIST)
        self.assertEqual(1, len(result.entries))
        self.assertEqual(
            "https://example.test/match.m3u8", result.entries[0].stream_url
        )
        self.assertEqual(1, len(result.unsupported))
        self.assertEqual("unsupported-flv", result.unsupported[0]["reason"])
        self.assertEqual(1, result.skipped["duplicate_event_variant"])

    def test_merge_is_repeatable_and_preserves_other_sport_stations(self):
        result = MODULE.parse_football_playlist(self.PLAYLIST)
        document = {"stations": [{
            "id": "existing-sport",
            "name": "HTV Thể thao",
            "streamUrl": "https://existing.test/sport.m3u8",
            "country": "VN",
            "tags": ["sport"],
            "category": "sport",
            "enabled": True,
            "availabilityNote": "",
            "verification": {
                "status": "unverified", "checkedAt": None, "detail": ""
            },
        }]}
        first, _stats = MODULE.merge_catalog(copy.deepcopy(document), result)
        second, _stats = MODULE.merge_catalog(copy.deepcopy(first), result)
        self.assertEqual(first, second)
        self.assertEqual(2, len(first["stations"]))
        imported = first["stations"][1]
        self.assertEqual("sport", imported["category"])
        self.assertIn("source:tinhlagi-football", imported["tags"])
        self.assertTrue(imported["name"].endswith("— COLA TV"))

    def test_unsupported_inventory_is_key_free(self):
        result = MODULE.parse_football_playlist(self.PLAYLIST)
        raw = str(MODULE.unsupported_document(result, "https://example.test/s.m3u"))
        self.assertNotIn("license_key", raw.casefold())
        self.assertNotIn("clearkey", raw.casefold())


if __name__ == "__main__":
    unittest.main()
