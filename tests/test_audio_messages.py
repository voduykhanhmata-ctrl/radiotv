# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "globalPlugins"))

from radiotv.audio.messages import ProtocolError, parse_engine_message  # noqa: E402


class AudioMessageTests(unittest.TestCase):

    def test_parses_ready_state_and_redacted_error(self):
        request_id = "request-1"
        ready = parse_engine_message(
            json.dumps({"version": 1, "requestId": request_id, "type": "ready"}),
            request_id,
        )
        self.assertEqual("ready", ready.message_type)
        state = parse_engine_message(
            json.dumps(
                {
                    "version": 1,
                    "requestId": request_id,
                    "type": "state",
                    "state": "playing",
                }
            ),
            request_id,
        )
        self.assertEqual("playing", state.state)
        error = parse_engine_message(
            json.dumps(
                {
                    "version": 1,
                    "requestId": request_id,
                    "type": "error",
                    "code": "stream_open_failed",
                    "detail": "2",
                }
            ),
            request_id,
        )
        self.assertEqual("stream_open_failed", error.code)

    def test_rejects_wrong_id_unknown_fields_and_url_leak(self):
        with self.assertRaises(ProtocolError):
            parse_engine_message(
                '{"version":1,"requestId":"other","type":"ready"}',
                "expected",
            )
        with self.assertRaises(ProtocolError):
            parse_engine_message(
                '{"version":1,"requestId":"x","type":"ready","extra":1}',
                "x",
            )
        with self.assertRaisesRegex(ProtocolError, "URL"):
            parse_engine_message(
                json.dumps(
                    {
                        "version": 1,
                        "requestId": "x",
                        "type": "error",
                        "code": "bad",
                        "detail": "https://secret.example/token",
                    }
                ),
                "x",
            )


if __name__ == "__main__":
    unittest.main()
