# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

import datetime
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "globalPlugins"))

from radiotv.core.epg_service import EPGService, parse_xmltv  # noqa: E402


SAMPLE = b"""<?xml version="1.0" encoding="UTF-8"?>
<tv>
  <programme start="20260831120000 +0700" stop="20260831123000 +0700" channel="vtv1.vn">
    <title lang="vi">Thoi su</title>
  </programme>
  <programme start="20260831123000 +0700" stop="20260831130000 +0700" channel="vtv1.vn">
    <title lang="vi">Du bao thoi tiet</title>
  </programme>
</tv>
"""


class EPGServiceTests(unittest.TestCase):

    def test_xmltv_parser_and_accessible_schedule_lines(self):
        service = EPGService()
        service._programs = parse_xmltv(SAMPLE)
        service._state = "ready"
        now = datetime.datetime(
            2026, 8, 31, 12, 15,
            tzinfo=datetime.timezone(datetime.timedelta(hours=7)),
        )
        lines = service.schedule("VTV1.VN", now=now)
        self.assertEqual(2, len(lines))
        self.assertTrue(lines[0].startswith("Đang phát, 12:00–12:30"))
        self.assertIn("Du bao thoi tiet", lines[1])

    def test_missing_channel_and_loading_have_clear_messages(self):
        service = EPGService()
        self.assertIn("chưa có mã", service.schedule("")[0])
        self.assertIn("Đang tải", service.schedule("vtv1.vn")[0])


if __name__ == "__main__":
    unittest.main()
