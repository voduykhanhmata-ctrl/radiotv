# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

"""Test source-list alternates for failed stations and apply proven fallbacks."""

from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import subprocess
import struct
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from import_tinhlagi_tv import (  # noqa: E402
    DEFAULT_SOURCE_URL,
    canonical_channel_name,
    fetch_source,
    parse_playlist,
)
from catalog_io import write_catalog


def _smoke(url: str, timeout: float, user_agent: str = "RadioTV/0.1") -> dict:
    process = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "playback_smoke.py"),
            "--url",
            url,
            "--timeout",
            str(timeout),
            "--hold-seconds",
            "0.2",
            "--volume",
            "0",
            "--user-agent",
            user_agent,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=timeout + 15,
        check=False,
    )
    try:
        return json.loads(process.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        return {
            "outcome": "runner-error",
            "detail": "playback_smoke did not return valid JSON",
            "states": [],
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-report", type=pathlib.Path, required=True)
    parser.add_argument("--group", required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--timeout", type=float, default=22.0)
    parser.add_argument("--apply", action="store_true")
    arguments = parser.parse_args(argv)

    catalog_path = ROOT / "data" / "stations.json"
    document = json.loads(catalog_path.read_text(encoding="utf-8"))
    stations_by_id = {station["id"]: station for station in document["stations"]}
    audit = json.loads(arguments.audit_report.read_text(encoding="utf-8"))
    failed = [
        result for result in audit["results"]
        if result["group"] == arguments.group and result["outcome"] != "playing"
    ]
    parsed = parse_playlist(fetch_source(DEFAULT_SOURCE_URL))
    recovered = []
    checked_at = datetime.datetime.now().astimezone().isoformat(timespec="seconds")

    for index, failure in enumerate(failed, start=1):
        station = stations_by_id[failure["stationId"]]
        identity = canonical_channel_name(station["name"])
        candidates = []
        seen_urls = {station["streamUrl"]}
        for candidate in parsed.compatible_candidates:
            if canonical_channel_name(candidate.name) != identity:
                continue
            if candidate.stream_url in seen_urls:
                continue
            seen_urls.add(candidate.stream_url)
            candidates.append(candidate)

        attempts = []
        selected = None
        for candidate in candidates:
            try:
                result = _smoke(candidate.stream_url, arguments.timeout, candidate.http_user_agent or "RadioTV/0.1")
            except (OSError, subprocess.TimeoutExpired):
                result = {"outcome": "runner-error", "detail": "smoke runner failed or timed out", "states": []}
            attempts.append(
                {
                    "outcome": result.get("outcome", "runner-error"),
                    "detail": result.get("detail", ""),
                    "states": result.get("states", []),
                }
            )
            if result.get("outcome") == "playing":
                selected = candidate
                break

        if selected is not None and arguments.apply:
            station["streamUrl"] = selected.stream_url
            station["tags"] = [tag for tag in station["tags"] if not tag.startswith("http-user-agent:")]
            if selected.http_user_agent:
                station["tags"].append("http-user-agent:" + selected.http_user_agent)
            station["enabled"] = True
            station["availabilityNote"] = (
                f"Đã chuyển sang luồng dự phòng được kiểm tra lúc {checked_at}."
            )
            station["verification"] = {
                "status": "playback-confirmed",
                "checkedAt": checked_at,
                "detail": "Fallback playback-confirmed by RadioTV backend on " + ("x64" if struct.calcsize("P") == 8 else "x86") + ".",
            }
        recovered.append(
            {
                "stationId": station["id"],
                "name": station["name"],
                "candidateCount": len(candidates),
                "attempts": attempts,
                "recovered": selected is not None,
            }
        )
        print(
            f"{index}/{len(failed)} {station['id']} "
            f"candidates={len(candidates)} recovered={selected is not None}",
            flush=True,
        )

    report = {
        "generatedAt": checked_at,
        "group": arguments.group,
        "failedCount": len(failed),
        "recoveredCount": sum(item["recovered"] for item in recovered),
        "results": recovered,
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if arguments.apply:
        write_catalog(catalog_path, document)
    print(
        json.dumps(
            {
                "failed": report["failedCount"],
                "recovered": report["recoveredCount"],
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
