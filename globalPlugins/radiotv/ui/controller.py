# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

"""Pure-Python state controller; it intentionally does not import wx or NVDA."""

from __future__ import annotations

import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass

from ..audio.supervisor import PlaybackEvent, PlaybackSupervisor
from ..core.catalog_service import StationCatalog
from ..core.epg_service import EPGService
from ..core.entities import Station
from ..core.persistence import PersistenceError, StateStore, UserState


CATEGORY_ORDER = ("tv", "radio", "sport", "favorites")


def adjacent_category(category: str, direction: int) -> str:
    """Return the wrapped previous or next category for keyboard navigation."""

    if category not in CATEGORY_ORDER:
        raise ValueError(f"unsupported UI category: {category!r}")
    if direction not in (-1, 1):
        raise ValueError("direction must be -1 or 1")
    index = CATEGORY_ORDER.index(category)
    return CATEGORY_ORDER[(index + direction) % len(CATEGORY_ORDER)]


@dataclass(frozen=True, slots=True)
class RadioTVSnapshot:
    category: str
    query: str
    stations: tuple[Station, ...]
    selected_index: int
    tv_groups: tuple[str, ...]
    selected_tv_group_index: int
    schedule_lines: tuple[str, ...]
    favorite_ids: tuple[str, ...]
    volume: int
    playback_state: str
    status_text: str


SnapshotCallback = Callable[[RadioTVSnapshot], None]


class RadioTVController:
    """Coordinate catalog, state storage, and process playback without GUI code."""

    def __init__(
        self,
        catalog: StationCatalog,
        state_store: StateStore,
        supervisor: PlaybackSupervisor,
        epg_service: EPGService | None = None,
        *,
        announce: Callable[[str], None] | None = None,
    ):
        self._catalog = catalog
        self._state_store = state_store
        self._supervisor = supervisor
        self._epg_service = epg_service
        self._announce = announce
        self._lock = threading.RLock()
        self._on_change: SnapshotCallback | None = None
        self._category = "tv"
        self._query = ""
        self._tv_group = ""
        self._selected_ids: dict[str, str] = {}
        self._playback_state = "stopped"
        self._current_request_id: str | None = None
        self._current_station_id: str | None = None
        self._notice = ""

        try:
            loaded_state = state_store.load_and_upgrade()
        except PersistenceError:
            loaded_state = UserState()
            self._notice = "Không thể đọc cấu hình cũ; đang dùng giá trị mặc định."
        known_ids = {station.station_id for station in catalog.stations}
        favorite_ids = tuple(
            station_id for station_id in loaded_state.favorite_ids
            if station_id in known_ids
        )
        if favorite_ids != loaded_state.favorite_ids:
            self._notice = "Đã bỏ mục yêu thích không còn trong danh mục."
        self._state = UserState(favorite_ids, loaded_state.volume)
        supervisor.set_event_callback(self._handle_audio_event)
        with self._lock:
            self._ensure_tv_group_locked()
            self._ensure_selection_locked()
        if self._epg_service is not None:
            self._epg_service.refresh_async(self._notify)

    def set_on_change(self, callback: SnapshotCallback | None) -> None:
        with self._lock:
            self._on_change = callback
        if callback is not None:
            callback(self.snapshot())

    def snapshot(self) -> RadioTVSnapshot:
        with self._lock:
            stations = self._visible_locked()
            selected_index = self._selected_index_locked(stations)
            selected_name = (
                stations[selected_index].name if selected_index >= 0 else "Không có đài"
            )
            if self._current_station_id is not None:
                selected_name = self._catalog.get(self._current_station_id).name
            playback_labels = {
                "starting": "Đang mở",
                "ready": "Đang mở",
                "playing": "Đang phát",
                "stalled": "Đang chờ dữ liệu",
                "restarting": "Đang khôi phục sau lỗi",
                "stopped": "Đã dừng",
                "ended": "Nguồn đã kết thúc",
                "error": "Không phát được",
            }
            status = (
                f"{playback_labels.get(self._playback_state, self._playback_state)}; "
                f"{selected_name}; âm lượng {self._state.volume}%"
            )
            if self._notice:
                status = f"{self._notice} {status}"
            tv_groups = self._catalog.tv_groups(self._query)
            try:
                selected_tv_group_index = tv_groups.index(self._tv_group)
            except ValueError:
                selected_tv_group_index = -1
            selected_station = (
                stations[selected_index] if selected_index >= 0 else None
            )
            if self._category == "tv" and selected_station is not None:
                if self._epg_service is None:
                    schedule_lines = ("Lịch phát sóng chưa được nạp.",)
                else:
                    schedule_lines = self._epg_service.schedule(selected_station.epg_id)
            else:
                schedule_lines = ()
            return RadioTVSnapshot(
                category=self._category,
                query=self._query,
                stations=stations,
                selected_index=selected_index,
                tv_groups=tv_groups,
                selected_tv_group_index=selected_tv_group_index,
                schedule_lines=schedule_lines,
                favorite_ids=self._state.favorite_ids,
                volume=self._state.volume,
                playback_state=self._playback_state,
                status_text=status,
            )

    def set_category(self, category: str) -> None:
        if category not in CATEGORY_ORDER:
            raise ValueError(f"unsupported UI category: {category!r}")
        with self._lock:
            self._category = category
            self._ensure_selection_locked()
        self._notify()

    def set_query(self, query: str) -> None:
        with self._lock:
            self._query = query
            self._ensure_tv_group_locked()
            self._ensure_selection_locked()
        self._notify()

    def set_tv_group_index(self, index: int) -> None:
        with self._lock:
            groups = self._catalog.tv_groups(self._query)
            if not 0 <= index < len(groups):
                return
            self._tv_group = groups[index]
            self._ensure_selection_locked()
        self._notify()

    def select_index(self, index: int) -> None:
        with self._lock:
            stations = self._visible_locked()
            if not 0 <= index < len(stations):
                return
            self._selected_ids[self._category] = stations[index].station_id
        self._notify()

    def play_selected(self) -> str | None:
        with self._lock:
            station = self._selected_station_locked()
            volume = self._state.volume
        if station is None:
            with self._lock:
                self._notice = "Không có đài để phát."
            self._notify()
            return None
        request_id = str(uuid.uuid4())
        with self._lock:
            self._current_request_id = request_id
            self._current_station_id = station.station_id
            self._playback_state = "starting"
            self._notice = ""
            try:
                self._supervisor.play(
                    station.stream_url, volume, station.http_user_agent,
                    request_id=request_id,
                )
            except (ValueError, RuntimeError):
                self._current_request_id = None
                self._current_station_id = None
                self._playback_state = "error"
                self._notice = "Không thể mở nguồn phát."
        self._notify()
        return request_id

    def next_and_play(self, delta: int) -> str | None:
        if delta not in (-1, 1):
            raise ValueError("delta must be -1 or 1")
        with self._lock:
            stations = self._visible_locked()
            if not stations:
                return None
            current_index = self._selected_index_locked(stations)
            next_index = (current_index + delta) % len(stations)
            self._selected_ids[self._category] = stations[next_index].station_id
        self._notify()
        return self.play_selected()

    def toggle_play_stop(self) -> str | None:
        with self._lock:
            active = self._current_request_id is not None
        if active:
            self.stop()
            return None
        return self.play_selected()

    def stop(self) -> None:
        self._supervisor.stop()
        with self._lock:
            self._current_request_id = None
            self._current_station_id = None
            self._playback_state = "stopped"
            self._notice = ""
        self._notify()

    def toggle_favorite(self) -> bool | None:
        with self._lock:
            station = self._selected_station_locked()
            if station is None:
                return None
            favorites = list(self._state.favorite_ids)
            if station.station_id in favorites:
                favorites.remove(station.station_id)
                is_favorite = False
            else:
                favorites.append(station.station_id)
                is_favorite = True
            self._state = UserState(tuple(favorites), self._state.volume)
            self._save_state_locked()
            self._ensure_selection_locked()
        self._notify()
        return is_favorite

    def adjust_volume(self, delta: int) -> int:
        with self._lock:
            new_volume = max(0, min(100, self._state.volume + delta))
            if new_volume == self._state.volume:
                return new_volume
            self._state = UserState(self._state.favorite_ids, new_volume)
            self._save_state_locked()
            should_restart = self._current_request_id is not None
        if should_restart:
            with self._lock:
                request_id = str(uuid.uuid4())
                self._current_request_id = request_id
                self._playback_state = "starting"
                returned_id = self._supervisor.set_volume(new_volume, request_id=request_id)
                if returned_id is None and self._current_request_id == request_id:
                    self._current_request_id = None
                    self._current_station_id = None
                    self._playback_state = "stopped"
        self._notify()
        return new_volume

    def close(self) -> None:
        self._announce = None
        self.set_on_change(None)
        self._supervisor.set_event_callback(None)
        self._supervisor.shutdown()
        if self._epg_service is not None:
            self._epg_service.close()

    def _handle_audio_event(self, event: PlaybackEvent) -> None:
        with self._lock:
            if event.request_id != self._current_request_id:
                return
            self._playback_state = event.state
            if event.state == "error":
                self._notice = "Lỗi phát: " + event.detail
                self._current_request_id = None
                self._current_station_id = None
            elif event.state in ("ended", "stopped"):
                self._current_request_id = None
                self._current_station_id = None
            elif event.state == "playing":
                self._notice = ""
        self._notify()
        if self._announce is not None and event.state in ("playing", "error", "ended"):
            self._announce(self.snapshot().status_text)

    def _visible_locked(self) -> tuple[Station, ...]:
        if self._category == "favorites":
            favorite_set = set(self._state.favorite_ids)
            return tuple(
                station for station in self._catalog.search(self._query)
                if station.station_id in favorite_set
            )
        if self._category == "tv":
            return self._catalog.search(
                self._query,
                category="tv",
                group=self._tv_group or None,
            )
        return self._catalog.search(self._query, category=self._category)

    def _ensure_tv_group_locked(self) -> None:
        groups = self._catalog.tv_groups(self._query)
        if self._tv_group not in groups:
            self._tv_group = groups[0] if groups else ""

    def _selected_station_locked(self) -> Station | None:
        stations = self._visible_locked()
        index = self._selected_index_locked(stations)
        return stations[index] if index >= 0 else None

    def _selected_index_locked(self, stations: tuple[Station, ...]) -> int:
        if not stations:
            return -1
        selected_id = self._selected_ids.get(self._category)
        for index, station in enumerate(stations):
            if station.station_id == selected_id:
                return index
        return 0

    def _ensure_selection_locked(self) -> None:
        stations = self._visible_locked()
        if not stations:
            self._selected_ids.pop(self._category, None)
            return
        selected_id = self._selected_ids.get(self._category)
        if selected_id not in {station.station_id for station in stations}:
            self._selected_ids[self._category] = stations[0].station_id

    def _save_state_locked(self) -> None:
        try:
            self._state_store.save(self._state)
            self._notice = ""
        except PersistenceError:
            self._notice = "Không thể lưu cấu hình."

    def _notify(self) -> None:
        with self._lock:
            callback = self._on_change
        if callback is not None:
            callback(self.snapshot())
