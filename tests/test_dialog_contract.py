# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

"""Exercise keyboard routing without pretending to test native wx focus."""

import importlib.util
import pathlib
import sys
import types
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "globalPlugins"))


class DialogContractTests(unittest.TestCase):
    def setUp(self):
        fake_wx = types.ModuleType("wx")
        fake_wx.Dialog = object
        for index, key in enumerate(("WXK_TAB", "WXK_PAGEUP", "WXK_PAGEDOWN", "WXK_NUMPAD1", "WXK_NUMPAD2", "WXK_NUMPAD3", "WXK_NUMPAD4", "WXK_RETURN", "WXK_NUMPAD_ENTER", "WXK_SPACE", "WXK_LEFT", "WXK_RIGHT", "WXK_F1", "WXK_ESCAPE"), 1000):
            setattr(fake_wx, key, index)
        self.channel = object()
        fake_wx.Window = types.SimpleNamespace(FindFocus=lambda: self.channel)
        self.wx = fake_wx
        spec = importlib.util.spec_from_file_location("radiotv.ui._dialog_contract", ROOT / "globalPlugins/radiotv/ui/main_window.py")
        module = importlib.util.module_from_spec(spec)
        with mock.patch.dict(sys.modules, {"wx": fake_wx, "ui": types.SimpleNamespace(message=mock.Mock())}):
            spec.loader.exec_module(module)
        self.dialog = object.__new__(module.RadioTVDialog)
        self.dialog._lists = {"tv": self.channel}
        self.dialog.notebook = mock.Mock()
        self.dialog.notebook.GetSelection.return_value = 0
        self.dialog._controller = mock.Mock()

    def press(self, key):
        event = mock.Mock()
        event.GetKeyCode.return_value = key
        event.ControlDown.return_value = False
        self.dialog._on_char_hook(event)
        return event

    def test_space_toggles_but_enter_only_plays(self):
        self.press(self.wx.WXK_SPACE)
        self.dialog._controller.toggle_play_stop.assert_called_once_with()
        self.dialog._controller.play_selected.assert_not_called()
        self.press(self.wx.WXK_RETURN)
        self.dialog._controller.play_selected.assert_called_once_with()

    def test_space_outside_channel_list_keeps_native_behavior(self):
        self.wx.Window.FindFocus = lambda: object()
        event = self.press(self.wx.WXK_SPACE)
        event.Skip.assert_called_once_with()
        self.dialog._controller.toggle_play_stop.assert_not_called()

    def test_direct_category_avoids_duplicate_page_change_event(self):
        self.dialog._announce_category = mock.Mock()
        self.dialog._set_category_and_focus("radio")
        self.dialog.notebook.ChangeSelection.assert_called_once_with(1)
        self.dialog.notebook.SetSelection.assert_not_called()
        self.dialog._announce_category.assert_called_once_with("radio", 1)
