# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

"""Play one catalog station briefly and report redacted engine states."""

import argparse
import json
import pathlib
import struct
import sys
import threading
import time


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "globalPlugins"))

from radiotv.audio.supervisor import PlaybackSupervisor  # noqa: E402
from radiotv.core.catalog_service import StationCatalog  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--station-id")
    source.add_argument("--url", help="Test a candidate URL before adding it to the catalog.")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--hold-seconds", type=float, default=3.0)
    parser.add_argument("--volume", type=int, default=35)
    parser.add_argument("--user-agent")
    parser.add_argument("--runtime-root", type=pathlib.Path)
    arguments = parser.parse_args()

    station = None
    if arguments.station_id:
        catalog = StationCatalog.from_file(ROOT / "data" / "stations.json")
        station = catalog.get(arguments.station_id)
        stream_url = station.stream_url
    else:
        stream_url = arguments.url
    condition = threading.Condition()
    events = []

    def on_event(event):
        with condition:
            events.append(event)
            condition.notify_all()

    supervisor = PlaybackSupervisor(
        on_event=on_event,
        startup_timeout=arguments.timeout,
        runtime_root=arguments.runtime_root,
    )
    volume = max(0, min(100, arguments.volume))
    user_agent = arguments.user_agent or (
        station.http_user_agent if station else "RadioTV/0.1"
    )
    request_id = supervisor.play(stream_url, volume, user_agent)
    deadline = time.monotonic() + arguments.timeout
    outcome = "timeout"
    detail = ""
    try:
        with condition:
            while time.monotonic() < deadline:
                for event in events:
                    if event.request_id != request_id:
                        continue
                    if event.state == "playing":
                        outcome = "playing"
                        break
                    if event.state == "error":
                        outcome = "error"
                        detail = event.detail
                        break
                if outcome != "timeout":
                    break
                condition.wait(deadline - time.monotonic())
        if outcome == "playing":
            time.sleep(max(0.0, arguments.hold_seconds))
    finally:
        supervisor.shutdown()

    report = {
        "architecture": "x64" if struct.calcsize("P") == 8 else "x86",
        "stationId": station.station_id if station else None,
        "category": station.category if station else None,
        "outcome": outcome,
        "detail": detail,
        "states": [
            event.state for event in events if event.request_id == request_id
        ],
    }
    print(json.dumps(report, ensure_ascii=False))
    return 0 if outcome == "playing" else 1


if __name__ == "__main__":
    raise SystemExit(main())
