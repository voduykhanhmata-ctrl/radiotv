# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

import copy
import json
import pathlib
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "globalPlugins"))

from radiotv.core.catalog_service import (  # noqa: E402
    CatalogDataError,
    StationCatalog,
    normalize_text,
)


CATALOG_PATH = ROOT / "data" / "stations.json"


class CatalogServiceTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.catalog = StationCatalog.from_file(CATALOG_PATH)
        cls.document = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        cls.football_count = sum(
            "source:tinhlagi-football" in station["tags"]
            for station in cls.document["stations"]
        )

    def test_loads_expected_active_categories(self):
        self.assertGreater(self.football_count, 0)
        self.assertEqual(627 + self.football_count, len(self.catalog.stations))
        self.assertEqual(625 + self.football_count, len(self.catalog.select()))
        self.assertEqual(
            {"tv": 595, "radio": 29, "sport": 1 + self.football_count},
            self.catalog.category_counts(),
        )
        self.assertEqual(
            len(self.catalog.stations),
            sum(self.catalog.category_counts(include_disabled=True).values()),
        )

    def test_tv_groups_preserve_source_order_and_filter_stations(self):
        groups = self.catalog.tv_groups()
        self.assertEqual(23, len(groups))
        self.assertEqual("⭐ KÊNH YÊU THÍCH", groups[0])
        self.assertIn("📺 VTV", groups)
        vtv = self.catalog.search("", category="tv", group="📺 VTV")
        self.assertTrue(vtv)
        self.assertTrue(all(station.group == "📺 VTV" for station in vtv))
        with self.assertRaises(ValueError):
            self.catalog.search("", category="radio", group="📺 VTV")

    def test_search_ignores_vietnamese_accents_and_case(self):
        self.assertIn("vn-vov1", {item.station_id for item in self.catalog.search("THOI su")})
        self.assertIn("vn-vov3", {item.station_id for item in self.catalog.search("am nhac")})
        self.assertEqual("duy khanh", normalize_text("Duy Khánh"))

    def test_search_uses_tags_and_explicit_category(self):
        radio_results = self.catalog.search("music", category="radio")
        self.assertTrue(radio_results)
        self.assertTrue(all(item.category == "radio" for item in radio_results))
        self.assertEqual(
            1 + self.football_count,
            len(self.catalog.select(category="sport")),
        )
        with self.assertRaises(ValueError):
            self.catalog.select(category="guessed")

    def test_disabled_station_is_hidden_unless_requested(self):
        disabled_ids = {
            "vn-vsbet", "vn-xone-fm",
        }
        self.assertTrue(disabled_ids.isdisjoint(
            {item.station_id for item in self.catalog.select()}
        ))
        self.assertTrue(disabled_ids.issubset(
            {item.station_id for item in self.catalog.select(include_disabled=True)}
        ))

    def test_rejects_duplicate_identity_and_bad_shape(self):
        duplicate = copy.deepcopy(self.document)
        duplicate["stations"][1]["id"] = duplicate["stations"][0]["id"]
        with self.assertRaisesRegex(CatalogDataError, "duplicate station id"):
            StationCatalog.from_document(duplicate)

        bad_shape = copy.deepcopy(self.document)
        bad_shape["stations"][0]["unexpected"] = True
        with self.assertRaisesRegex(CatalogDataError, "fields do not match"):
            StationCatalog.from_document(bad_shape)

    def test_rejects_invalid_json_file(self):
        with tempfile.TemporaryDirectory(prefix="radiotv-catalog-test-") as directory:
            invalid_path = pathlib.Path(directory) / "invalid-catalog.json"
            invalid_path.write_text("{not json", encoding="utf-8")
            with self.assertRaises(CatalogDataError):
                StationCatalog.from_file(invalid_path)
            invalid_path.write_bytes(b"\xff")
            with self.assertRaisesRegex(CatalogDataError, "UTF-8"):
                StationCatalog.from_file(invalid_path)


if __name__ == "__main__":
    unittest.main()
