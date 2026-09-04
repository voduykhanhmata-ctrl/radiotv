# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

import collections
import json
import pathlib
import unittest
import urllib.parse


ROOT = pathlib.Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "data" / "stations.json"
UNSUPPORTED_PATH = ROOT / "data" / "tv_sources_unsupported.json"


class StationDataTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        cls.stations = cls.document["stations"]
        cls.active = [item for item in cls.stations if item["enabled"]]
        cls.football_count = sum(
            "source:tinhlagi-football" in item["tags"]
            for item in cls.stations
        )

    def test_root_provenance_and_schema_version(self):
        self.assertEqual(1, self.document["schemaVersion"])
        self.assertEqual("Võ Duy Khánh", self.document["curator"])
        self.assertIn("personally collected", self.document["provenance"])

    def test_counts_and_explicit_categories(self):
        self.assertGreater(self.football_count, 0)
        self.assertEqual(627 + self.football_count, len(self.stations))
        self.assertEqual(625 + self.football_count, len(self.active))
        self.assertEqual(
            {"tv": 595, "radio": 29, "sport": 1 + self.football_count},
            dict(collections.Counter(item["category"] for item in self.active)),
        )
        disabled = {item["id"] for item in self.stations if not item["enabled"]}
        self.assertEqual({"vn-vsbet", "vn-xone-fm"}, disabled)

    def test_ids_names_and_urls_are_unique_and_safe_to_log_by_parts(self):
        self.assertEqual(len(self.stations), len({item["id"] for item in self.stations}))
        self.assertEqual(len(self.stations), len({item["name"] for item in self.stations}))
        self.assertEqual(len(self.stations), len({item["streamUrl"] for item in self.stations}))
        for item in self.stations:
            parts = urllib.parse.urlsplit(item["streamUrl"])
            self.assertIn(parts.scheme, ("http", "https"), item["id"])
            self.assertTrue(parts.hostname, item["id"])
            self.assertIsNone(parts.username, item["id"])
            self.assertIsNone(parts.password, item["id"])

    def test_station_shape_and_verification_evidence(self):
        expected = {
            "id", "name", "streamUrl", "country", "tags", "category",
            "enabled", "availabilityNote", "verification",
        }
        confirmed_ids = {
            "vn-vov1", "vn-rfi-viet", "vn-vtv6-iptv", "vn-vtv10",
            "vn-vov4-taybac", "vn-vov4-taynguyen", "vn-vov4-dbscl",
            "vn-vov4-hcmc", "vn-hanoi-fm90", "vn-hanoi-fm96",
            "vn-gialai-radio", "vn-tayninh-radio", "vn-dongthap-radio",
            "vn-vov2", "vn-vov3", "vn-vov5", "vn-vov-gt-hcmc",
            "vn-vov-mekong", "vn-zing-bolero", "vn-danang-radio",
            "vn-daknong-radio", "vn-hue-radio", "vn-quangninh-qnr1",
            "vn-quangninh-qnr2", "vn-vov-gt-hanoi", "vn-vov-english",
            "vn-vov5-world", "vn-voh-999", "vn-voh-956", "vn-voh-877",
            "vn-voh-am610",
        }
        for item in self.stations:
            self.assertEqual(expected, set(item), item.get("id"))
            self.assertEqual("VN", item["country"])
            self.assertTrue(item["name"].strip())
            self.assertTrue(all(isinstance(tag, str) and tag.strip() for tag in item["tags"]))
            self.assertEqual(len(item["tags"]), len(set(item["tags"])))
            status = item["verification"]["status"]
            if item["id"] in confirmed_ids:
                self.assertEqual(
                    "playback-confirmed", item["verification"]["status"]
                )
            if status == "playback-confirmed":
                self.assertIsInstance(item["verification"]["checkedAt"], str)
                self.assertIn("x64", item["verification"]["detail"])
            elif status == "failed":
                self.assertFalse(item["enabled"])
                self.assertIsInstance(item["verification"]["checkedAt"], str)
            else:
                self.assertEqual("unverified", status)
                self.assertIsNone(item["verification"]["checkedAt"])

    def test_active_plain_http_sources_are_explicit(self):
        http_ids = {
            item["id"] for item in self.active
            if urllib.parse.urlsplit(item["streamUrl"]).scheme == "http"
        }
        self.assertTrue(
            {
                "vn-onviedrama", "vn-lamdong", "vn-vov4-taybac",
                "vn-vov4-dbscl", "vn-vov4-hcmc",
            }.issubset(http_ids)
        )
        by_id = {item["id"]: item for item in self.active}
        imported_http = http_ids - {
            "vn-onviedrama", "vn-lamdong", "vn-vov4-taybac",
            "vn-vov4-dbscl", "vn-vov4-hcmc",
        }
        self.assertTrue(all(
            "source:tinhlagi" in by_id[station_id]["tags"]
            for station_id in imported_http
        ))

    def test_catalog_order_is_stable_and_screen_reader_friendly(self):
        categories = [item["category"] for item in self.stations]
        self.assertEqual(categories, sorted(categories, key={"tv": 0, "radio": 1, "sport": 2}.get))
        radio_ids = [item["id"] for item in self.active if item["category"] == "radio"]
        tv_groups = [
            next(tag[6:] for tag in item["tags"] if tag.startswith("group:"))
            for item in self.active if item["category"] == "tv"
        ]
        seen_groups = []
        for group in tv_groups:
            if not seen_groups or seen_groups[-1] != group:
                self.assertNotIn(group, seen_groups)
                seen_groups.append(group)
        self.assertEqual("⭐ KÊNH YÊU THÍCH", seen_groups[0])
        self.assertIn("📺 VTV", seen_groups)
        self.assertEqual(
            ["vn-vov1", "vn-vov2", "vn-vov3", "vn-vov4-taybac",
             "vn-vov4-taynguyen", "vn-vov4-dbscl", "vn-vov4-hcmc", "vn-vov5"],
            radio_ids[:8],
        )

    def test_unsupported_source_inventory_is_key_free(self):
        raw_text = UNSUPPORTED_PATH.read_text(encoding="utf-8")
        document = json.loads(raw_text)
        self.assertEqual(1, document["schemaVersion"])
        self.assertEqual(29, len(document["entries"]))
        self.assertNotIn("license_key", raw_text.casefold())
        self.assertNotIn("clearkey", raw_text.casefold())
        for entry in document["entries"]:
            self.assertEqual(
                {"name", "streamUrl", "group", "epgId", "reason"},
                set(entry),
            )
            self.assertIn(entry["reason"], ("drm", "mpeg-dash"))

    def test_sctv_sources_are_restored_with_safe_request_metadata(self):
        sctv = [
            item for item in self.stations
            if "group:📺 SCTV" in item["tags"]
        ]
        self.assertEqual(21, len(sctv))
        self.assertTrue(all(item["enabled"] for item in sctv))
        by_name = {item["name"]: item for item in sctv}
        self.assertIn("http-user-agent:Dalvik/2.1.0", by_name["SCTV2 - TODAY TV"]["tags"])
        self.assertIn("http-user-agent:VThanhTivi", by_name["SCTV6"]["tags"])

        unsupported = json.loads(UNSUPPORTED_PATH.read_text(encoding="utf-8"))
        unsupported_sctv = {
            item["name"] for item in unsupported["entries"]
            if item["name"].startswith("SCTV")
        }
        self.assertEqual({"SCTV15", "SCTV17", "SCTV22"}, unsupported_sctv)

    def test_football_import_is_hls_only_and_tagged(self):
        imported = [
            item for item in self.stations
            if "source:tinhlagi-football" in item["tags"]
        ]
        self.assertEqual(self.football_count, len(imported))
        self.assertGreater(len(imported), 0)
        self.assertTrue(all(item["category"] == "sport" for item in imported))
        self.assertTrue(all(
            urllib.parse.urlsplit(item["streamUrl"]).path.casefold().endswith(".m3u8")
            for item in imported
        ))


if __name__ == "__main__":
    unittest.main()
