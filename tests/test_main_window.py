# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "globalPlugins"))

try:
    import wx
except ImportError:
    wx = None

from radiotv.audio.supervisor import PlaybackSupervisor  # noqa: E402
from radiotv.core.catalog_service import StationCatalog  # noqa: E402
from radiotv.core.persistence import StateStore  # noqa: E402
from radiotv.ui.controller import RadioTVController  # noqa: E402


class MainWindowNavigationTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if wx is None:
            raise unittest.SkipTest("wxPython is not available in current test environment")
        cls.app = wx.App()
        cls.catalog = StationCatalog.from_file(ROOT / "data" / "stations.json")

    def setUp(self):
        if wx is None:
            self.skipTest("wxPython is not available")
        from radiotv.ui.main_window import RadioTVDialog

        self.temporary_directory = tempfile.TemporaryDirectory(prefix="radiotv-wx-")
        self.store = StateStore(pathlib.Path(self.temporary_directory.name) / "user-state.json")
        self.controller = RadioTVController(
            self.catalog, self.store, PlaybackSupervisor()
        )
        self.dialog = RadioTVDialog(
            None, self.controller, ROOT / "doc" / "vi" / "readme.html", None
        )
        self.dialog.Show()

    def tearDown(self):
        if hasattr(self, "dialog") and self.dialog:
            self.dialog.Destroy()
        if hasattr(self, "controller") and self.controller:
            self.controller.close()
        if hasattr(self, "temporary_directory"):
            self.temporary_directory.cleanup()

    def test_ctrl_tab_and_ctrl_shift_tab_navigation_keys(self):
        # Forward Ctrl+Tab
        nav = wx.NavigationKeyEvent()
        nav.SetDirection(True)
        nav.SetWindowChange(True)
        nav.SetCurrentFocus(self.dialog.search)
        self.dialog.GetEventHandler().ProcessEvent(nav)
        self.assertEqual("radio", self.controller.snapshot().category)
        self.assertEqual(1, self.dialog.notebook.GetSelection())

        # Backward Ctrl+Shift+Tab
        nav.SetDirection(False)
        nav.SetWindowChange(True)
        self.dialog.GetEventHandler().ProcessEvent(nav)
        self.assertEqual("tv", self.controller.snapshot().category)
        self.assertEqual(0, self.dialog.notebook.GetSelection())

    def test_direct_category_shortcuts_in_char_hook(self):
        direct_tests = [
            (ord("2"), "radio", 1),
            (ord("3"), "sport", 2),
            (ord("4"), "favorites", 3),
            (ord("1"), "tv", 0),
        ]
        for key_code, category, page_idx in direct_tests:
            hook_evt = wx.KeyEvent(wx.wxEVT_CHAR_HOOK)
            hook_evt.SetKeyCode(key_code)
            hook_evt.SetControlDown(True)
            self.dialog.GetEventHandler().ProcessEvent(hook_evt)
            self.assertEqual(category, self.controller.snapshot().category)
            self.assertEqual(page_idx, self.dialog.notebook.GetSelection())

    def test_forward_tab_chain_on_tv_tab(self):
        self.controller.set_category("tv")
        self.dialog.search.SetFocus()
        chain = []
        for _ in range(8):
            w = wx.Window.FindFocus()
            name = w.GetName() or getattr(w, "GetLabel", lambda: "")()
            chain.append(name)
            w.Navigate(wx.NavigationKeyEvent.IsForward)
        expected = [
            "text",
            "Chọn mục TV, Radio, Bóng đá hoặc Yêu thích",
            "Chọn nhóm TV",
            "Danh sách kênh TV",
            "Lịch phát sóng",
            "button",
            "button",
            "button",
        ]
        self.assertEqual(expected, chain)

    def test_backward_tab_chain_on_tv_tab(self):
        self.controller.set_category("tv")
        self.dialog.search.SetFocus()
        chain = []
        for _ in range(8):
            w = wx.Window.FindFocus()
            name = w.GetName() or getattr(w, "GetLabel", lambda: "")()
            chain.append(name)
            w.Navigate(wx.NavigationKeyEvent.IsBackward)
        expected = [
            "text",
            "button",
            "button",
            "button",
            "Lịch phát sóng",
            "Danh sách kênh TV",
            "Chọn nhóm TV",
            "Chọn mục TV, Radio, Bóng đá hoặc Yêu thích",
        ]
        self.assertEqual(expected, chain)


if __name__ == "__main__":
    unittest.main()
