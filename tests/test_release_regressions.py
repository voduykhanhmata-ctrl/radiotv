# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

"""Regression checks for failures found during the 0.1 source review."""

import gzip
import json
import pathlib
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "globalPlugins"))
from radiotv.audio.messages import ProtocolError, parse_engine_message
from radiotv.audio.supervisor import PlaybackSupervisor
from radiotv.core import epg_service
from radiotv.core.catalog_service import StationCatalog, CatalogDataError
from radiotv.core.entities import is_safe_http_url
from radiotv.core.persistence import StateStore
from radiotv.ui.controller import RadioTVController
import test_audio_supervisor as supervisor_tests
from test_audio_supervisor import EventRecorder, FAKE_ENGINE
from test_controller import FakeSupervisor


class ProtocolRegressionTests(unittest.TestCase):
    def test_malformed_types_cannot_escape_protocol_validation(self):
        for state in ([], {}, None, 1, True):
            with self.subTest(state=state), self.assertRaises(ProtocolError):
                parse_engine_message(json.dumps({"version": 1, "requestId": "x", "type": "state", "state": state}), "x")
        for version in (True, 1.0):
            with self.assertRaises(ProtocolError):
                parse_engine_message(json.dumps({"version": version, "requestId": "x", "type": "ready"}), "x")

    def test_error_code_cannot_leak_a_url_and_detail_cannot_inject_lines(self):
        for code, detail in (("https://private.invalid/token", ""), ("error", "line\nforged")):
            with self.assertRaises(ProtocolError):
                parse_engine_message(json.dumps({"version": 1, "requestId": "x", "type": "error", "code": code, "detail": detail}), "x")


class SupervisorRegressionTests(unittest.TestCase):
    make_supervisor = supervisor_tests.AudioSupervisorTests.make_supervisor

    def test_slow_worker_launch_does_not_block_play_or_stop(self):
        entered, release = threading.Event(), threading.Event()
        def command(request_id, *_args):
            entered.set()
            release.wait(1.0)
            return [sys.executable, "-B", "-u", str(FAKE_ENGINE), "--request-id", request_id, "--mode", "normal"]
        recorder = EventRecorder()
        supervisor = PlaybackSupervisor(command_builder=command, on_event=recorder)
        try:
            started = time.monotonic()
            request_id = supervisor.play("https://example.invalid/stream", 0)
            self.assertLess(time.monotonic() - started, 0.2)
            self.assertTrue(entered.wait(1))
            supervisor.stop()
            release.set()
            supervisor.shutdown()
            self.assertIsNone(supervisor.current_request_id)
            self.assertFalse(any(event.state == "playing" for event in recorder.events))
            self.assertTrue(any(event.request_id == request_id and event.state == "stopped" for event in recorder.events))
        finally:
            release.set()
            supervisor.shutdown()

    def test_terminal_and_malformed_messages_reap_the_worker(self):
        for mode in ("bad-state", "error-hang", "ended-hang", "oversized"):
            with self.subTest(mode=mode):
                supervisor, recorder = self.make_supervisor(lambda _url: mode)
                try:
                    request_id = supervisor.play("https://example.invalid/stream", 0)
                    recorder.wait_for("ended" if mode == "ended-hang" else "error", request_id=request_id)
                    supervisor.shutdown()
                    self.assertFalse(supervisor._monitor_threads)
                    self.assertIsNone(supervisor.current_request_id)
                finally:
                    supervisor.shutdown()

    def test_second_confirmed_crash_is_terminal(self):
        supervisor, recorder = self.make_supervisor(lambda _url: "crash")
        try:
            request_id = supervisor.play("https://example.invalid/stream", 0)
            recorder.wait_for("error", request_id=request_id)
            self.assertEqual(1, sum(event.state == "restarting" for event in recorder.events))
            self.assertIsNone(supervisor.current_request_id)
        finally:
            supervisor.shutdown()

    def test_launch_error_is_reported_and_closed_supervisor_rejects_play(self):
        def broken(*_args):
            raise OSError("private path")
        recorder = EventRecorder()
        supervisor = PlaybackSupervisor(command_builder=broken, on_event=recorder)
        request_id = supervisor.play("https://example.invalid/stream", 0)
        error = recorder.wait_for("error", request_id=request_id)
        self.assertNotIn("private path", error.detail)
        supervisor.shutdown()
        with self.assertRaises(RuntimeError):
            supervisor.play("https://example.invalid/stream", 0)


class ControllerRegressionTests(unittest.TestCase):
    def test_immediate_events_are_not_lost_or_overwritten(self):
        catalog = StationCatalog.from_file(ROOT / "data/stations.json")
        for state in ("playing", "error"):
            with self.subTest(state=state), tempfile.TemporaryDirectory() as directory:
                supervisor = FakeSupervisor()
                original_play = supervisor.play
                def immediate(*args, **kwargs):
                    request_id = original_play(*args, **kwargs)
                    supervisor.emit(request_id, state, "failed" if state == "error" else "")
                    return request_id
                supervisor.play = immediate
                controller = RadioTVController(catalog, StateStore(pathlib.Path(directory) / "state.json"), supervisor)
                try:
                    controller.play_selected()
                    self.assertEqual(state, controller.snapshot().playback_state)
                    controller.adjust_volume(-5)
                    self.assertEqual(state, controller.snapshot().playback_state)
                finally:
                    controller.close()

    def test_browsing_does_not_mislabel_current_playback(self):
        catalog = StationCatalog.from_file(ROOT / "data/stations.json")
        with tempfile.TemporaryDirectory() as directory:
            supervisor = FakeSupervisor()
            controller = RadioTVController(catalog, StateStore(pathlib.Path(directory) / "state.json"), supervisor)
            try:
                name = controller.snapshot().stations[0].name
                request_id = controller.play_selected()
                supervisor.emit(request_id, "playing")
                controller.set_category("radio")
                self.assertIn(name, controller.snapshot().status_text)
                controller.stop()
                supervisor.emit(request_id, "playing")
                self.assertEqual("stopped", controller.snapshot().playback_state)
            finally:
                controller.close()


class InputRegressionTests(unittest.TestCase):
    def test_unsafe_urls_are_rejected_without_exposing_values(self):
        for value in ("https://[", "https://a:invalid/path", "https://a:70000/", "https://a/path\r\nHeader:yes", "https://user:pass@a/", "file:///tmp/a"):
            self.assertFalse(is_safe_http_url(value))
            supervisor = PlaybackSupervisor()
            with self.assertRaises(ValueError):
                supervisor.play(value, 0)
            supervisor.shutdown()

    def test_gzip_expansion_and_xml_entities_are_bounded(self):
        with mock.patch.object(epg_service, "MAX_XML_BYTES", 64):
            with self.assertRaises(ValueError):
                epg_service.decode_payload(gzip.compress(b"x" * 1000))
        with self.assertRaises(ValueError):
            epg_service.parse_xmltv(b'<!DOCTYPE tv [<!ENTITY x "expanded">]><tv/>')

    def test_bad_catalog_timestamp_is_rejected(self):
        document = json.loads((ROOT / "data/stations.json").read_text(encoding="utf-8"))
        document["stations"][0]["verification"]["checkedAt"] = "yesterday"
        with self.assertRaises(CatalogDataError):
            StationCatalog.from_document(document)
