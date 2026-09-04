# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh
"""NVDA adapter for the RadioTV 0.1 clean-room development build."""

import pathlib

import addonHandler
import globalPluginHandler
import globalVars
import gui
import languageHandler
import scriptHandler
import ui
import wx
from logHandler import log

from .audio.supervisor import PlaybackSupervisor
from .core.catalog_service import StationCatalog
from .core.epg_service import EPGService
from .core.persistence import StateStore
from .support.help_locator import locate_help
from .support.diagnostics import create_logger, close_logger
from .ui.controller import RadioTVController
from .ui.main_window import RadioTVDialog


addonHandler.initTranslation()
_ADDON_ROOT = pathlib.Path(__file__).resolve().parents[2]


class GlobalPlugin(globalPluginHandler.GlobalPlugin):

    def __init__(self):
        super().__init__()
        self._controller = None
        self._dialog = None
        self._diagnostics = None

    def terminate(self):
        if self._dialog is not None:
            self._dialog.Destroy()
            self._dialog = None
        if self._controller is not None:
            self._controller.close()
            self._controller = None
        if self._diagnostics is not None:
            close_logger(self._diagnostics)
            self._diagnostics = None
        super().terminate()

    def _ensure_controller(self):
        if self._controller is None:
            catalog = StationCatalog.from_file(_ADDON_ROOT / "data" / "stations.json")
            config_path = (
                pathlib.Path(globalVars.appArgs.configPath)
                / "radiotv"
                / "user-state.json"
            )
            if self._diagnostics is None:
                self._diagnostics = create_logger(config_path.parent)
            supervisor = PlaybackSupervisor(logger=self._diagnostics)
            self._controller = RadioTVController(
                catalog,
                StateStore(config_path),
                supervisor,
                EPGService(),
                announce=lambda message: wx.CallAfter(ui.message, message),
            )
        return self._controller

    def _show_dialog(self):
        try:
            controller = self._ensure_controller()
        except Exception:
            log.exception("RadioTV initialization failed")
            ui.message(_("RadioTV không thể khởi tạo. Hãy kiểm tra nhật ký NVDA."))
            return
        if self._dialog is not None:
            self._dialog.Raise()
            self._dialog.SetFocus()
            return
        help_path = locate_help(_ADDON_ROOT, languageHandler.getLanguage())
        gui.mainFrame.prePopup()
        try:
            self._dialog = RadioTVDialog(
                gui.mainFrame,
                controller,
                help_path,
                self._dialog_closed,
            )
            self._dialog.Show()
        finally:
            gui.mainFrame.postPopup()

    def _dialog_closed(self):
        self._dialog = None

    @scriptHandler.script(
        description=_("Mở cửa sổ RadioTV"),
        gesture="kb:windows+alt+v",
        category="RadioTV",
    )
    def script_showRadioTV(self, _gesture):
        wx.CallAfter(self._show_dialog)

    @scriptHandler.script(
        description=_("Phát hoặc dừng đài RadioTV đang chọn"),
        gesture="kb:windows+alt+p",
        category="RadioTV",
    )
    def script_togglePlayback(self, _gesture):
        try:
            request_id = self._ensure_controller().toggle_play_stop()
            ui.message(_("Đang mở đài") if request_id else _("Đã dừng"))
        except Exception:
            log.exception("RadioTV play toggle failed")
            ui.message(_("RadioTV không thể thực hiện lệnh phát."))

    @scriptHandler.script(
        description=_("Dừng RadioTV"),
        gesture="kb:windows+alt+s",
        category="RadioTV",
    )
    def script_stopPlayback(self, _gesture):
        try:
            self._ensure_controller().stop()
            ui.message(_("Đã dừng RadioTV"))
        except Exception:
            log.exception("RadioTV stop failed")
            ui.message(_("RadioTV không thể thực hiện lệnh dừng."))

    @scriptHandler.script(
        description=_("Tăng âm lượng RadioTV"),
        gesture="kb:windows+alt+upArrow",
        category="RadioTV",
    )
    def script_volumeUp(self, _gesture):
        try:
            volume = self._ensure_controller().adjust_volume(5)
            ui.message(_("Âm lượng %d phần trăm") % volume)
        except Exception:
            log.exception("RadioTV volume increase failed")
            ui.message(_("Không thể đổi âm lượng RadioTV."))

    @scriptHandler.script(
        description=_("Giảm âm lượng RadioTV"),
        gesture="kb:windows+alt+downArrow",
        category="RadioTV",
    )
    def script_volumeDown(self, _gesture):
        try:
            volume = self._ensure_controller().adjust_volume(-5)
            ui.message(_("Âm lượng %d phần trăm") % volume)
        except Exception:
            log.exception("RadioTV volume decrease failed")
            ui.message(_("Không thể đổi âm lượng RadioTV."))
