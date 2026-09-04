# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

"""Apply redacted playback evidence to the station catalog."""

from __future__ import annotations

import argparse
import datetime
import json
import pathlib
from catalog_io import write_catalog


ROOT = pathlib.Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-report", type=pathlib.Path, required=True)
    parser.add_argument("--group", action="append", required=True)
    parser.add_argument("--recovery-report", type=pathlib.Path)
    arguments = parser.parse_args(argv)

    catalog_path = ROOT / "data" / "stations.json"
    document = json.loads(catalog_path.read_text(encoding="utf-8"))
    stations_by_id = {station["id"]: station for station in document["stations"]}
    audit = json.loads(arguments.audit_report.read_text(encoding="utf-8"))
    audit_datetime = datetime.datetime.fromisoformat(audit["generatedAt"])
    audit_date = audit_datetime.strftime("%d/%m/%Y")
    architecture = audit.get("architecture", "unknown")
    recovered_ids = set()
    if arguments.recovery_report is not None:
        recovery = json.loads(arguments.recovery_report.read_text(encoding="utf-8"))
        recovered_ids = {
            item["stationId"] for item in recovery["results"] if item["recovered"]
        }

    updated_playing = 0
    kept_failed_visible = 0
    wanted_groups = set(arguments.group)
    for result in audit["results"]:
        if result["group"] not in wanted_groups:
            continue
        station = stations_by_id[result["stationId"]]
        if station["id"] in recovered_ids:
            continue
        if result["outcome"] == "playing":
            station["enabled"] = True
            station["availabilityNote"] = (
                f"Phát được trong kiểm tra backend ngày {audit_date}."
            )
            station["verification"] = {
                "status": "playback-confirmed",
                "checkedAt": audit["generatedAt"],
                "detail": (
                    "Playback-confirmed by RadioTV backend "
                    f"on {architecture}."
                ),
            }
            updated_playing += 1
            continue
        station["enabled"] = True
        station["availabilityNote"] = (
            f"Giữ hiển thị sau kiểm tra backend ngày {audit_date}; "
            "lỗi backend không được coi là bằng chứng nguồn chết."
        )
        station["verification"] = {
            "status": "unverified",
            "checkedAt": None,
            "detail": (
                f"RadioTV backend {result['detail']} on {architecture}; "
                "source kept visible for later retry."
            ),
        }
        kept_failed_visible += 1

    write_catalog(catalog_path, document)
    print(
        json.dumps(
            {
                "playbackConfirmed": updated_playing,
                "keptFailedVisible": kept_failed_visible,
                "recoveredKept": len(recovered_ids),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
