# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

import pathlib
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "globalPlugins"))

from radiotv.audio.supervisor import PlaybackEvent  # noqa: E402
from radiotv.core.catalog_service import StationCatalog  # noqa: E402
from radiotv.core.persistence import StateStore  # noqa: E402
from radiotv.ui.controller import (  # noqa: E402
    RadioTVController,
    adjacent_category,
)


class FakeSupervisor:

    def __init__(self):
        self.callback = None
        self.plays = []
        self.stops = 0

    def set_event_callback(self, callback):
        self.callback = callback

    def play(self, url, volume, user_agent="RadioTV/0.1", *, request_id=None):
        request_id = request_id or f"request-{len(self.plays) + 1}"
        self.plays.append((request_id, url, volume, user_agent))
        return request_id

    def set_volume(self, volume, *, request_id=None):
        _request_id, url, _old_volume, user_agent = self.plays[-1]
        return self.play(url, volume, user_agent, request_id=request_id)

    def stop(self):
        self.stops += 1

    def shutdown(self):
        self.stop()

    def emit(self, request_id, state, detail=""):
        if self.callback:
            self.callback(PlaybackEvent(request_id, state, detail))


class ControllerTests(unittest.TestCase):

    def test_adjacent_category_wraps_in_both_directions(self):
        self.assertEqual("radio", adjacent_category("tv", 1))
        self.assertEqual("sport", adjacent_category("radio", 1))
        self.assertEqual("tv", adjacent_category("favorites", 1))
        self.assertEqual("favorites", adjacent_category("tv", -1))
        with self.assertRaises(ValueError):
            adjacent_category("tv", 0)

    @classmethod
    def setUpClass(cls):
        cls.catalog = StationCatalog.from_file(ROOT / "data" / "stations.json")

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory(
            prefix="radiotv-controller-test-"
        )
        self.store = StateStore(
            pathlib.Path(self.temporary_directory.name) / "user-state.json"
        )
        self.supervisor = FakeSupervisor()
        self.controller = RadioTVController(
            self.catalog, self.store, self.supervisor
        )

    def tearDown(self):
        self.controller.close()
        self.temporary_directory.cleanup()

    def test_default_tv_and_accent_search(self):
        snapshot = self.controller.snapshot()
        self.assertEqual("tv", snapshot.category)
        self.assertEqual(23, len(snapshot.tv_groups))
        self.assertEqual("⭐ KÊNH YÊU THÍCH", snapshot.tv_groups[0])
        self.assertEqual(6, len(snapshot.stations))
        self.controller.set_category("radio")
        self.controller.set_query("thoi su")
        ids = {station.station_id for station in self.controller.snapshot().stations}
        self.assertIn("vn-vov1", ids)

    def test_browsing_tv_group_and_channel_does_not_play(self):
        self.controller.set_tv_group_index(1)
        snapshot = self.controller.snapshot()
        self.assertEqual(1, snapshot.selected_tv_group_index)
        self.controller.select_index(1)
        self.assertEqual([], self.supervisor.plays)
        self.controller.next_and_play(1)
        self.assertEqual(1, len(self.supervisor.plays))

    def test_play_reports_only_after_engine_event(self):
        self.controller.set_category("radio")
        request_id = self.controller.play_selected()
        self.assertEqual("starting", self.controller.snapshot().playback_state)
        self.supervisor.emit(request_id, "playing")
        self.assertEqual("playing", self.controller.snapshot().playback_state)

    def test_next_station_auto_plays_latest_selection(self):
        self.controller.set_category("radio")
        first_id = self.controller.snapshot().stations[0].station_id
        self.controller.next_and_play(1)
        snapshot = self.controller.snapshot()
        self.assertNotEqual(first_id, snapshot.stations[snapshot.selected_index].station_id)
        self.assertEqual(1, len(self.supervisor.plays))

    def test_favorite_and_volume_are_persisted(self):
        self.controller.set_category("radio")
        selected_id = self.controller.snapshot().stations[0].station_id
        self.assertTrue(self.controller.toggle_favorite())
        self.assertEqual(95, self.controller.adjust_volume(-5))
        loaded = self.store.load()
        self.assertIn(selected_id, loaded.favorite_ids)
        self.assertEqual(95, loaded.volume)

    def test_volume_restart_uses_new_request(self):
        self.controller.set_category("radio")
        first_request = self.controller.play_selected()
        self.supervisor.emit(first_request, "playing")
        self.controller.adjust_volume(-5)
        self.assertEqual(2, len(self.supervisor.plays))
        self.assertEqual(95, self.supervisor.plays[-1][2])


if __name__ == "__main__":
    unittest.main()
