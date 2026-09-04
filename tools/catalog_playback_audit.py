# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

"""Run redacted backend playback checks for selected catalog groups."""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime
import json
import pathlib
import struct
import subprocess
import sys
from collections import Counter


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "globalPlugins"))

from radiotv.core.catalog_service import StationCatalog  # noqa: E402


def _test_station(station, timeout: float, hold_seconds: float) -> dict:
    command = [
        sys.executable,
        str(ROOT / "tools" / "playback_smoke.py"),
        "--station-id",
        station.station_id,
        "--timeout",
        str(timeout),
        "--hold-seconds",
        str(hold_seconds),
        "--volume",
        "0",
    ]
    try:
        process = subprocess.run(
            command, cwd=ROOT, capture_output=True, text=True,
            encoding="utf-8", timeout=timeout + hold_seconds + 15, check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        engine_report = json.loads(process.stdout.strip().splitlines()[-1])
        if not isinstance(engine_report, dict):
            raise ValueError("invalid report")
    except (IndexError, ValueError, OSError, subprocess.TimeoutExpired):
        engine_report = {
            "outcome": "runner-error",
            "detail": "playback_smoke did not return valid JSON",
            "states": [],
        }
    source_kind = (
        "new"
        if "source:tinhlagi" in station.tags
        else "existing"
    )
    return {
        "stationId": station.station_id,
        "name": station.name,
        "group": station.group,
        "sourceKind": source_kind,
        "outcome": engine_report.get("outcome", "runner-error"),
        "detail": engine_report.get("detail", ""),
        "states": engine_report.get("states", []),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--group", action="append", default=[])
    parser.add_argument("--station-id", action="append", default=[])
    parser.add_argument("--jobs", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=22.0)
    parser.add_argument("--hold-seconds", type=float, default=0.2)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    arguments = parser.parse_args(argv)
    if not arguments.group and not arguments.station_id:
        parser.error("at least one --group or --station-id is required")

    catalog = StationCatalog.from_file(ROOT / "data" / "stations.json")
    wanted_groups = set(arguments.group)
    stations = []
    seen_ids = set()
    for station_id in arguments.station_id:
        station = catalog.get(station_id)
        if station.station_id not in seen_ids:
            stations.append(station)
            seen_ids.add(station.station_id)
    for station in catalog.select(category="tv", include_disabled=True):
        if station.group in wanted_groups and station.station_id not in seen_ids:
            stations.append(station)
            seen_ids.add(station.station_id)
    results: list[dict] = []
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=max(1, min(6, arguments.jobs))
    ) as executor:
        futures = {
            executor.submit(
                _test_station,
                station,
                arguments.timeout,
                arguments.hold_seconds,
            ): station
            for station in stations
        }
        for completed, future in enumerate(
            concurrent.futures.as_completed(futures),
            start=1,
        ):
            result = future.result()
            results.append(result)
            print(
                f"{completed}/{len(stations)} "
                f"{result['stationId']} {result['outcome']}",
                flush=True,
            )

    order = {station.station_id: index for index, station in enumerate(stations)}
    results.sort(key=lambda item: order[item["stationId"]])
    report = {
        "generatedAt": datetime.datetime.now().astimezone().isoformat(),
        "architecture": "x64" if struct.calcsize("P") == 8 else "x86",
        "groups": arguments.group,
        "stationIds": arguments.station_id,
        "counts": dict(Counter(item["outcome"] for item in results)),
        "results": results,
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report["counts"], ensure_ascii=False), flush=True)
    return 0 if all(item["outcome"] == "playing" for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
