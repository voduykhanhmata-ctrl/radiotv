# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

import pathlib
import sys
import threading
import time
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "globalPlugins"))

from radiotv.audio.supervisor import PlaybackSupervisor  # noqa: E402


FAKE_ENGINE = ROOT / "tests" / "fixtures" / "fake_engine.py"


class EventRecorder:

    def __init__(self):
        self.events = []
        self.condition = threading.Condition()

    def __call__(self, event):
        with self.condition:
            self.events.append(event)
            self.condition.notify_all()

    def wait_for(
        self, state, *, request_id=None, replay_count=None, timeout=3.0
    ):
        deadline = time.monotonic() + timeout
        with self.condition:
            while True:
                for event in reversed(self.events):
                    if event.state == state and (
                        request_id is None or event.request_id == request_id
                    ) and (
                        replay_count is None or event.replay_count == replay_count
                    ):
                        return event
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    self.fail_message(state, request_id)
                self.condition.wait(remaining)

    def fail_message(self, state, request_id):
        observed = [(event.request_id, event.state) for event in self.events]
        raise AssertionError(
            f"event {state!r}/{request_id!r} not seen; observed={observed}"
        )


class AudioSupervisorTests(unittest.TestCase):

    def make_supervisor(self, mode_selector, *, startup_timeout=2.0):
        recorder = EventRecorder()

        def command_builder(request_id, url, _volume, _runtime):
            mode = mode_selector(url)
            return (
                sys.executable,
                "-B",
                "-u",
                str(FAKE_ENGINE),
                "--request-id",
                request_id,
                "--mode",
                mode,
            )

        supervisor = PlaybackSupervisor(
            runtime_root=ROOT / "globalPlugins" / "radiotv" / "runtime",
            on_event=recorder,
            startup_timeout=startup_timeout,
            stop_grace=0.2,
            command_builder=command_builder,
        )
        return supervisor, recorder

    def test_latest_request_wins_and_stop_is_nonblocking(self):
        supervisor, recorder = self.make_supervisor(lambda _url: "normal")
        try:
            first = supervisor.play("https://example.invalid/first", 50)
            recorder.wait_for("playing", request_id=first)
            second = supervisor.play("https://example.invalid/second", 60)
            recorder.wait_for("playing", request_id=second)
            self.assertEqual(second, supervisor.current_request_id)
            started = time.monotonic()
            supervisor.stop()
            self.assertLess(time.monotonic() - started, 0.2)
            recorder.wait_for("stopped", request_id=second)
            self.assertIsNone(supervisor.current_request_id)
        finally:
            supervisor.shutdown()

    def test_startup_timeout_terminates_silent_worker(self):
        supervisor, recorder = self.make_supervisor(
            lambda _url: "silent", startup_timeout=0.2
        )
        try:
            request_id = supervisor.play("https://example.invalid/silent", 50)
            error = recorder.wait_for("error", request_id=request_id)
            self.assertIn("timeout", error.detail)
            self.assertIsNone(supervisor.current_request_id)
        finally:
            supervisor.shutdown()

    def test_confirmed_crash_replays_exactly_once(self):
        launches = 0

        def mode_selector(_url):
            nonlocal launches
            launches += 1
            return "crash" if launches == 1 else "normal"

        supervisor, recorder = self.make_supervisor(mode_selector)
        try:
            request_id = supervisor.play("https://example.invalid/crash", 70)
            recorder.wait_for("restarting", request_id=request_id)
            replay = recorder.wait_for(
                "playing", request_id=request_id, replay_count=1
            )
            self.assertEqual(1, replay.replay_count)
            self.assertEqual(2, launches)
        finally:
            supervisor.shutdown()

    def test_protocol_failure_is_reported_without_url(self):
        supervisor, recorder = self.make_supervisor(lambda _url: "bad-protocol")
        try:
            request_id = supervisor.play("https://example.invalid/private", 50)
            error = recorder.wait_for("error", request_id=request_id)
            self.assertIn("protocol", error.detail)
            self.assertNotIn("example.invalid", error.detail)
        finally:
            supervisor.shutdown()

    def test_rejects_header_injection_in_user_agent(self):
        supervisor, _recorder = self.make_supervisor(lambda _url: "normal")
        try:
            with self.assertRaises(ValueError):
                supervisor.play(
                    "https://example.invalid/stream",
                    50,
                    "RadioTV/0.1\r\nX-Injected: yes",
                )
        finally:
            supervisor.shutdown()


if __name__ == "__main__":
    unittest.main()
