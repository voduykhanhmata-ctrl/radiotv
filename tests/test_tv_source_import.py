# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

import copy
import importlib.util
import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "import_tinhlagi_tv.py"
SPEC = importlib.util.spec_from_file_location("import_tinhlagi_tv", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class TVSourceImportTests(unittest.TestCase):

    def test_parser_keeps_direct_stream_and_drops_drm_and_duplicates(self):
        playlist = """#EXTM3U url-tvg="https://example.test/epg.xml"
#EXTINF:-1 tvg-id="one" group-title="Nhóm A",Kênh Một
#EXTVLCOPT:http-user-agent=VThanhTivi
https://example.test/one.m3u8
#EXTINF:-1 tvg-id="drm" group-title="Nhóm A",Kênh DRM
#KODIPROP:inputstream.adaptive.license_type=clearkey
https://example.test/drm.mpd
#EXTINF:-1 tvg-id="one-copy" group-title="Nhóm B",Kênh Một
https://example.test/one-copy.m3u8
"""
        result = MODULE.parse_playlist(playlist)
        self.assertEqual(1, len(result.entries))
        self.assertEqual("Nhóm A", result.entries[0].group)
        self.assertEqual("one", result.entries[0].epg_id)
        self.assertEqual("VThanhTivi", result.entries[0].http_user_agent)
        self.assertEqual(1, len(result.unsupported_entries))
        self.assertEqual(1, result.skipped["unsupported_drm_or_dash"])
        self.assertEqual(1, result.skipped["duplicate_channel"])

    def test_hd_variant_wins_over_unlabelled_duplicate(self):
        playlist = """#EXTM3U
#EXTINF:-1 tvg-id="vtv1" group-title="VTV",VTV1
https://example.test/vtv1.m3u8
#EXTINF:-1 tvg-id="vtv1-hd" group-title="VTV",VTV1 HD
https://example.test/vtv1-hd.m3u8
"""
        result = MODULE.parse_playlist(playlist)
        self.assertEqual(1, len(result.entries))
        self.assertEqual("VTV1 HD", result.entries[0].name)
        self.assertEqual(1, result.skipped["preferred_higher_quality"])

    def test_unsupported_inventory_never_contains_drm_directives_or_keys(self):
        playlist = """#EXTM3U
#EXTINF:-1 tvg-id="drm" group-title="VTV",Kênh DRM
#KODIPROP:inputstream.adaptive.license_type=clearkey
#KODIPROP:inputstream.adaptive.license_key=secret-value
https://example.test/drm.mpd
"""
        result = MODULE.parse_playlist(playlist)
        inventory = MODULE.unsupported_document(result, "https://example.test/list")
        encoded = str(inventory).casefold()
        self.assertNotIn("secret-value", encoded)
        self.assertNotIn("license_key", encoded)
        self.assertEqual("https://example.test/drm.mpd", inventory["entries"][0]["streamUrl"])

    def test_catalog_merge_is_repeatable_and_preserves_existing_station(self):
        playlist = """#EXTM3U
#EXTINF:-1 tvg-id="one" group-title="Nhóm A",Kênh Một
https://example.test/one.m3u8
#EXTINF:-1 tvg-id="two" group-title="Nhóm A",Kênh Hai
https://example.test/two.m3u8
"""
        result = MODULE.parse_playlist(playlist)
        document = {
            "stations": [{
                "id": "existing-one",
                "name": "Kênh Một",
                "streamUrl": "https://existing.test/one.m3u8",
                "country": "VN",
                "tags": ["tv"],
                "category": "tv",
                "enabled": True,
                "availabilityNote": "",
                "verification": {
                    "status": "unverified",
                    "checkedAt": None,
                    "detail": "",
                },
            }],
        }
        first, _stats = MODULE.merge_catalog(copy.deepcopy(document), result)
        second, _stats = MODULE.merge_catalog(copy.deepcopy(first), result)
        self.assertEqual(first, second)
        self.assertEqual("existing-one", first["stations"][0]["id"])
        self.assertIn("source-meta:tinhlagi", first["stations"][0]["tags"])

    def test_failed_new_source_is_restored_for_the_new_backend(self):
        playlist = """#EXTM3U
#EXTINF:-1 tvg-id="mma" group-title="Thể thao",MMA-TV.com
https://example.test/mma.m3u8
"""
        result = MODULE.parse_playlist(playlist)
        document = {"stations": [{
            "id": "tl-mma-example",
            "name": "MMA-TV.com",
            "streamUrl": "https://example.test/mma.m3u8",
            "country": "VN",
            "tags": ["tv", "source:tinhlagi", "group:Thể thao"],
            "category": "tv",
            "enabled": False,
            "availabilityNote": "Tạm ẩn sau lỗi phát.",
            "verification": {
                "status": "failed",
                "checkedAt": "2026-08-31T09:26:59+07:00",
                "detail": "stream_open_failed: 41",
            },
        }]}
        merged, stats = MODULE.merge_catalog(copy.deepcopy(document), result)
        self.assertTrue(merged["stations"][0]["enabled"])
        self.assertEqual("unverified", merged["stations"][0]["verification"]["status"])
        self.assertEqual(1, stats["restored_failed_source"])

    def test_sctv_descriptive_suffixes_are_deduplicated(self):
        self.assertEqual(
            MODULE.canonical_channel_name("SCTV2 - TODAY TV"),
            MODULE.canonical_channel_name("SCTV2"),
        )
        self.assertEqual(
            MODULE.canonical_channel_name("SCTV14 - Phim"),
            MODULE.canonical_channel_name("SCTV14"),
        )

    def test_sctv_group_wins_over_duplicate_in_another_group(self):
        playlist = """#EXTM3U
#EXTINF:-1 group-title="📺 SCTV",SCTV6
#EXTVLCOPT:http-user-agent=VThanhTivi
https://example.test/sctv6.m3u8
#EXTINF:-1 group-title="Phim Truyện",SCTV6 - FIM 360 HD
https://example.test/sctv6.m3u8
"""
        result = MODULE.parse_playlist(playlist)
        self.assertEqual(1, len(result.entries))
        self.assertEqual("📺 SCTV", result.entries[0].group)
        self.assertEqual("VThanhTivi", result.entries[0].http_user_agent)

    def test_active_tv_catalog_has_no_quality_neutral_duplicate(self):
        document = json.loads((ROOT / "data" / "stations.json").read_text(encoding="utf-8"))
        tv_names = [
            station["name"] for station in document["stations"]
            if station["category"] == "tv" and station["enabled"]
        ]
        identities = [MODULE.canonical_channel_name(name) for name in tv_names]
        self.assertEqual(len(identities), len(set(identities)))


if __name__ == "__main__":
    unittest.main()
