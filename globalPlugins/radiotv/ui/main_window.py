# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

"""Minimal accessible wx dialog for the RadioTV development build."""

from __future__ import annotations

import os
import pathlib

import wx

from .controller import (
    CATEGORY_ORDER,
    RadioTVController,
    RadioTVSnapshot,
    adjacent_category,
)

try:
    import ui
except Exception:
    ui = None


_TAB_LABELS = {
    "tv": "TV",
    "radio": "Radio",
    "sport": "Bóng đá",
    "favorites": "Yêu thích",
}


class RadioTVDialog(wx.Dialog):

    def __init__(
        self,
        parent,
        controller: RadioTVController,
        help_path: pathlib.Path,
        on_destroy,
    ):
        super().__init__(parent, title="RadioTV 0.1", size=(720, 520))
        self._controller = controller
        self._help_path = help_path
        self._on_destroy_callback = on_destroy
        self._lists: dict[str, wx.ListBox] = {}
        self._last_snapshot: RadioTVSnapshot | None = None

        panel = wx.Panel(self)
        root_sizer = wx.BoxSizer(wx.VERTICAL)
        search_label = wx.StaticText(panel, label="Tìm kiếm tên hoặc thẻ, không cần dấu:")
        root_sizer.Add(search_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 12)
        self.search = wx.TextCtrl(panel)
        self.search.ChangeValue(controller.snapshot().query)
        root_sizer.Add(self.search, 0, wx.EXPAND | wx.ALL, 12)

        self.notebook = wx.Notebook(panel)
        self.notebook.SetName("Chọn mục TV, Radio, Bóng đá hoặc Yêu thích")
        for category in CATEGORY_ORDER:
            page = wx.Panel(self.notebook)
            page_sizer = wx.BoxSizer(wx.VERTICAL)
            if category == "tv":
                group_label = wx.StaticText(page, label="Nhóm TV:")
                page_sizer.Add(group_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
                self.tv_group = wx.Choice(page)
                self.tv_group.SetName("Chọn nhóm TV")
                page_sizer.Add(self.tv_group, 0, wx.EXPAND | wx.ALL, 8)

                channel_label = wx.StaticText(page, label="Kênh trong nhóm:")
                page_sizer.Add(channel_label, 0, wx.LEFT | wx.RIGHT, 8)
                station_list = wx.ListBox(page, style=wx.LB_SINGLE)
                station_list.SetName("Danh sách kênh TV")
                page_sizer.Add(station_list, 1, wx.EXPAND | wx.ALL, 8)

                schedule_label = wx.StaticText(page, label="Lịch phát sóng:")
                page_sizer.Add(schedule_label, 0, wx.LEFT | wx.RIGHT, 8)
                self.schedule = wx.ListBox(page, style=wx.LB_SINGLE)
                self.schedule.SetName("Lịch phát sóng")
                page_sizer.Add(self.schedule, 1, wx.EXPAND | wx.ALL, 8)
                self.tv_group.Bind(wx.EVT_CHOICE, self._on_tv_group)
            else:
                station_list = wx.ListBox(page, style=wx.LB_SINGLE)
                station_list.SetName(f"Danh sách {_TAB_LABELS[category]}")
                page_sizer.Add(station_list, 1, wx.EXPAND | wx.ALL, 8)
            page.SetSizer(page_sizer)
            self.notebook.AddPage(page, _TAB_LABELS[category])
            self._lists[category] = station_list
            station_list.Bind(wx.EVT_LISTBOX, self._on_selection)
            station_list.Bind(wx.EVT_LISTBOX_DCLICK, self._on_channel_activate)
        root_sizer.Add(self.notebook, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 12)

        self.status = wx.StaticText(panel, label="")
        root_sizer.Add(self.status, 0, wx.EXPAND | wx.ALL, 12)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.favorite_button = wx.Button(panel, label="Thêm hoặc bỏ yêu thích")
        self.help_button = wx.Button(panel, label="Trợ giúp F1")
        self.close_button = wx.Button(panel, wx.ID_CLOSE, label="Đóng")
        for button in (
            self.favorite_button,
            self.help_button,
            self.close_button,
        ):
            button_sizer.Add(button, 0, wx.RIGHT, 8)
        root_sizer.Add(button_sizer, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)
        panel.SetSizer(root_sizer)

        self.search.Bind(wx.EVT_TEXT, self._on_search)
        self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self._on_page_changed)
        self.favorite_button.Bind(wx.EVT_BUTTON, self._on_favorite)
        self.help_button.Bind(wx.EVT_BUTTON, self._on_help)
        self.close_button.Bind(wx.EVT_BUTTON, self._on_close)
        self.Bind(wx.EVT_CHAR_HOOK, self._on_char_hook)
        self.Bind(wx.EVT_CLOSE, self._on_close)

        self._bind_navigation_recursive(self)

        controller.set_on_change(self._receive_snapshot)
        wx.CallAfter(self.notebook.SetFocus)

    def _receive_snapshot(self, snapshot: RadioTVSnapshot) -> None:
        if wx.IsMainThread():
            self._apply_snapshot(snapshot)
        else:
            wx.CallAfter(self._apply_snapshot, snapshot)

    def _apply_snapshot(self, snapshot: RadioTVSnapshot) -> None:
        if not self:
            return
        self._last_snapshot = snapshot
        category_index = CATEGORY_ORDER.index(snapshot.category)
        if self.notebook.GetSelection() != category_index:
            self.notebook.ChangeSelection(category_index)
        station_list = self._lists[snapshot.category]
        names = [station.name for station in snapshot.stations]
        current_names = list(station_list.GetStrings())
        if current_names != names:
            station_list.Set(names)
        if snapshot.selected_index >= 0:
            station_list.SetSelection(snapshot.selected_index)
        if snapshot.category == "tv":
            group_names = list(snapshot.tv_groups)
            if list(self.tv_group.GetStrings()) != group_names:
                self.tv_group.Set(group_names)
            if snapshot.selected_tv_group_index >= 0:
                self.tv_group.SetSelection(snapshot.selected_tv_group_index)
            schedule_lines = list(snapshot.schedule_lines) or [
                "Chưa có lịch phát sóng."
            ]
            if list(self.schedule.GetStrings()) != schedule_lines:
                self.schedule.Set(schedule_lines)
                if schedule_lines:
                    self.schedule.SetSelection(0)
        self.status.SetLabel(snapshot.status_text)
        self.Layout()

    def _bind_navigation_recursive(self, win: wx.Window) -> None:
        win.Bind(wx.EVT_NAVIGATION_KEY, self._on_navigation_key)
        for child in win.GetChildren():
            self._bind_navigation_recursive(child)

    def _announce_category(self, category: str, index: int) -> None:
        label = _TAB_LABELS.get(category, category)
        message = f"{label}, thẻ {index + 1} trên {len(CATEGORY_ORDER)}"
        if ui is not None:
            ui.message(message)

    def _on_search(self, _event) -> None:
        self._controller.set_query(self.search.GetValue())

    def _on_page_changed(self, event) -> None:
        selection = event.GetSelection()
        if 0 <= selection < len(CATEGORY_ORDER):
            category = CATEGORY_ORDER[selection]
            self._controller.set_category(category)
            self._announce_category(category, selection)
        event.Skip()

    def _on_tv_group(self, event) -> None:
        self._controller.set_tv_group_index(event.GetSelection())

    def _on_selection(self, event) -> None:
        self._controller.select_index(event.GetSelection())

    def _on_channel_activate(self, _event) -> None:
        self._controller.play_selected()

    def _on_favorite(self, _event) -> None:
        self._controller.toggle_favorite()

    def _on_help(self, _event) -> None:
        try:
            os.startfile(self._help_path)
        except OSError:
            wx.MessageBox(
                "Không mở được tệp trợ giúp.",
                "RadioTV",
                wx.OK | wx.ICON_ERROR,
                self,
            )

    def _on_navigation_key(self, event: wx.NavigationKeyEvent) -> None:
        if event.IsWindowChange():
            direction = 1 if event.GetDirection() else -1
            self._switch_category(direction)
            return

        cur = event.GetCurrentFocus() or wx.Window.FindFocus()
        is_fwd = event.GetDirection()
        cat = (
            self._last_snapshot.category
            if self._last_snapshot is not None
            else self._controller.snapshot().category
        )
        first_page_ctrl = self.tv_group if cat == "tv" else self._lists.get(cat)
        last_page_ctrl = self.schedule if cat == "tv" else self._lists.get(cat)

        if is_fwd:
            if cur is self.notebook and first_page_ctrl is not None:
                first_page_ctrl.SetFocus()
                return
            if cur is self.close_button:
                self.search.SetFocus()
                return
            if cur is last_page_ctrl:
                self.favorite_button.SetFocus()
                return
        else:
            if cur is first_page_ctrl:
                self.notebook.SetFocus()
                return
            if cur is self.favorite_button and last_page_ctrl is not None:
                last_page_ctrl.SetFocus()
                return
            if cur is self.search:
                self.close_button.SetFocus()
                return
            if cur is self.notebook:
                self.search.SetFocus()
                return
        event.Skip()

    def _on_char_hook(self, event) -> None:
        key = event.GetKeyCode()
        if event.ControlDown():
            if key in (wx.WXK_TAB, wx.WXK_PAGEUP, wx.WXK_PAGEDOWN):
                direction = (
                    -1
                    if key == wx.WXK_PAGEUP
                    or (key == wx.WXK_TAB and event.ShiftDown())
                    else 1
                )
                self._switch_category(direction)
                return
            direct_keys = {
                ord("1"): "tv",
                wx.WXK_NUMPAD1: "tv",
                ord("2"): "radio",
                wx.WXK_NUMPAD2: "radio",
                ord("3"): "sport",
                wx.WXK_NUMPAD3: "sport",
                ord("4"): "favorites",
                wx.WXK_NUMPAD4: "favorites",
            }
            category = direct_keys.get(key)
            if category is not None:
                self._set_category_and_focus(category)
                return
        focus = wx.Window.FindFocus()
        category_index = self.notebook.GetSelection()
        category = (
            CATEGORY_ORDER[category_index]
            if 0 <= category_index < len(CATEGORY_ORDER)
            else None
        )
        channel_list = self._lists.get(category)
        if focus is channel_list:
            if key in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
                self._controller.play_selected()
                return
            if key == wx.WXK_SPACE:
                self._controller.toggle_play_stop()
                return
            if key == wx.WXK_LEFT:
                self._controller.next_and_play(-1)
                return
            if key == wx.WXK_RIGHT:
                self._controller.next_and_play(1)
                return
        if key == wx.WXK_F1:
            self._on_help(event)
            return
        if key == wx.WXK_ESCAPE:
            self._controller.stop()
            self._close()
            return
        event.Skip()

    def _switch_category(self, direction: int) -> None:
        selection = self.notebook.GetSelection()
        current = (
            CATEGORY_ORDER[selection]
            if 0 <= selection < len(CATEGORY_ORDER)
            else "tv"
        )
        self._set_category_and_focus(adjacent_category(current, direction))

    def _set_category_and_focus(self, category: str) -> None:
        category_index = CATEGORY_ORDER.index(category)
        self.notebook.ChangeSelection(category_index)
        self._controller.set_category(category)
        self._announce_category(category, category_index)
        self.notebook.SetFocus()

    def _on_close(self, _event) -> None:
        self._controller.stop()
        self._close()

    def _close(self) -> None:
        self._controller.set_on_change(None)
        callback = self._on_destroy_callback
        self._on_destroy_callback = None
        self.Destroy()
        if callback is not None:
            callback()
