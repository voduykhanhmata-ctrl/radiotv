# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

"""Apply the reviewed Vietnam catalog additions and a stable NVDA-friendly order."""

from __future__ import annotations

import argparse
import json
import pathlib
import unicodedata


ROOT = pathlib.Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "data" / "stations.json"
CHECKED_AT = "2026-08-30T17:11:50+07:00"


def confirmed(detail: str = "BASS/BASSHLS engine confirmed playback on x64 and x86.") -> dict:
    return {
        "status": "playback-confirmed",
        "checkedAt": CHECKED_AT,
        "detail": detail,
    }


NEW_STATIONS = (
    {
        "id": "vn-vtv10",
        "name": "VTV10 - Tây Nam Bộ",
        "streamUrl": "https://live-a.fptplay53.net/live/media/vtv10/live247-hls-avc/index.m3u8",
        "country": "VN",
        "tags": ["Vietnam", "VTV", "national", "Mekong", "tv"],
        "category": "tv",
        "enabled": True,
        "availabilityNote": "VTV Cần Thơ đổi nhận diện thành VTV10 từ 30/03/2026.",
        "verification": confirmed(),
    },
    {
        "id": "vn-vov4-taybac",
        "name": "VOV4 - Tây Bắc",
        "streamUrl": "http://media.kythuatvov.vn:1936/live/VOV4_TB.sdp/chunklist.m3u8",
        "country": "VN",
        "tags": ["Vietnam", "VOV", "ethnic", "northwest", "radio"],
        "category": "radio",
        "enabled": True,
        "availabilityNote": "Nguồn VOV4 khu vực Tây Bắc.",
        "verification": confirmed(),
    },
    {
        "id": "vn-vov4-taynguyen",
        "name": "VOV4 - Tây Nguyên",
        "streamUrl": "https://str.vov.gov.vn/vovlive/vov4.TayNguyen.sdp_aac/playlist.m3u8",
        "country": "VN",
        "tags": ["Vietnam", "VOV", "ethnic", "central-highlands", "radio"],
        "category": "radio",
        "enabled": True,
        "availabilityNote": "Nguồn VOV4 khu vực Tây Nguyên.",
        "verification": confirmed(),
    },
    {
        "id": "vn-vov4-dbscl",
        "name": "VOV4 - Đồng bằng sông Cửu Long",
        "streamUrl": "http://media.kythuatvov.vn:1936/live/VOV4_CT.sdp/chunklist.m3u8",
        "country": "VN",
        "tags": ["Vietnam", "VOV", "ethnic", "Mekong", "radio"],
        "category": "radio",
        "enabled": True,
        "availabilityNote": "Nguồn VOV4 khu vực Đồng bằng sông Cửu Long.",
        "verification": confirmed(),
    },
    {
        "id": "vn-vov4-hcmc",
        "name": "VOV4 - TP.HCM",
        "streamUrl": "http://media.kythuatvov.vn:1936/live/VOV4_HCM.sdp/chunklist.m3u8",
        "country": "VN",
        "tags": ["Vietnam", "VOV", "ethnic", "Ho Chi Minh City", "radio"],
        "category": "radio",
        "enabled": True,
        "availabilityNote": "Nguồn VOV4 khu vực TP.HCM.",
        "verification": confirmed(),
    },
    {
        "id": "vn-hanoi-fm90",
        "name": "Hà Nội FM90 - Tin tức và Giao thông",
        "streamUrl": "https://cloudcdnfm90.tek4tv.vn/HANOIFM90/stream.m3u8",
        "country": "VN",
        "tags": ["Vietnam", "Hanoi", "news", "traffic", "radio"],
        "category": "radio",
        "enabled": True,
        "availabilityNote": "Kênh phát thanh FM90 của Đài Hà Nội.",
        "verification": confirmed(),
    },
    {
        "id": "vn-hanoi-fm96",
        "name": "Hà Nội FM96",
        "streamUrl": "https://cloudcdnfm90.tek4tv.vn/HANOI96/stream.m3u8",
        "country": "VN",
        "tags": ["Vietnam", "Hanoi", "music", "radio"],
        "category": "radio",
        "enabled": True,
        "availabilityNote": "Kênh phát thanh FM96 của Đài Hà Nội.",
        "verification": confirmed(),
    },
    {
        "id": "vn-gialai-radio",
        "name": "Gia Lai Radio",
        "streamUrl": "https://tv.gialaitv.vn/radio.m3u8",
        "country": "VN",
        "tags": ["Vietnam", "Gia Lai", "local", "radio"],
        "category": "radio",
        "enabled": True,
        "availabilityNote": "Kênh phát thanh của Báo và Phát thanh, Truyền hình Gia Lai.",
        "verification": confirmed(),
    },
    {
        "id": "vn-tayninh-radio",
        "name": "Tây Ninh FM96.9 / 103.1",
        "streamUrl": "https://live-hq.evgcdn.net/live/2851dd3d9016ac74d84b0c4a7a659f76891/playlist.m3u8",
        "country": "VN",
        "tags": ["Vietnam", "Tay Ninh", "local", "radio"],
        "category": "radio",
        "enabled": True,
        "availabilityNote": "Cùng chương trình được phát trên FM96.9 và FM103.1.",
        "verification": confirmed(),
    },
    {
        "id": "vn-dongthap-radio",
        "name": "Đồng Tháp FM96.2 / 98.4",
        "streamUrl": "https://618b88f69e53b.streamlock.net/THDTR/thdtradio/playlist.m3u8",
        "country": "VN",
        "tags": ["Vietnam", "Dong Thap", "local", "radio"],
        "category": "radio",
        "enabled": True,
        "availabilityNote": "Kênh phát thanh Đồng Tháp.",
        "verification": confirmed(),
    },
    {
        "id": "vn-danang-radio",
        "name": "Đà Nẵng FM98.5",
        "streamUrl": "https://live.mediatech.vn/live/2858a998b1c7fbf4522accd5554588ceae3/playlist.m3u8",
        "country": "VN",
        "tags": ["Vietnam", "Da Nang", "local", "radio"],
        "category": "radio",
        "enabled": True,
        "availabilityNote": "Kênh phát thanh Đà Nẵng FM98.5.",
        "verification": confirmed(),
    },
    {
        "id": "vn-daknong-radio",
        "name": "Đắk Nông Radio",
        "streamUrl": "https://cloudstreamthdn.tek4tv.vn/audio/daknong_radio/playlist.m3u8",
        "country": "VN",
        "tags": ["Vietnam", "Dak Nong", "local", "radio"],
        "category": "radio",
        "enabled": True,
        "availabilityNote": "Kênh phát thanh Đắk Nông.",
        "verification": confirmed(),
    },
    {
        "id": "vn-hue-radio",
        "name": "Huế FM93.0",
        "streamUrl": "https://live.trt.com.vn/Radio-online/playlist.m3u8",
        "country": "VN",
        "tags": ["Vietnam", "Hue", "local", "radio"],
        "category": "radio",
        "enabled": True,
        "availabilityNote": "Kênh phát thanh Huế FM93.0.",
        "verification": confirmed(),
    },
    {
        "id": "vn-quangninh-qnr1",
        "name": "Quảng Ninh QNR1 - FM97.8",
        "streamUrl": "https://live.baoquangninh.vn/qtvlive/qnr1.m3u8",
        "country": "VN",
        "tags": ["Vietnam", "Quang Ninh", "local", "radio"],
        "category": "radio",
        "enabled": True,
        "availabilityNote": "Kênh QNR1 FM97.8 của Quảng Ninh.",
        "verification": confirmed(),
    },
    {
        "id": "vn-quangninh-qnr2",
        "name": "Quảng Ninh QNR2 - FM94.7",
        "streamUrl": "https://live.baoquangninh.vn/qtvlive/qnr2.m3u8",
        "country": "VN",
        "tags": ["Vietnam", "Quang Ninh", "local", "radio"],
        "category": "radio",
        "enabled": True,
        "availabilityNote": "Kênh QNR2 FM94.7 của Quảng Ninh.",
        "verification": confirmed(),
    },
)


TV_PRIORITY = (
    "vn-vtv1", "vn-vtv2", "vn-vtv3", "vn-vtv4", "vn-vtv5",
    "vn-vtv6-iptv", "vn-vtv7", "vn-vtv8", "vn-vtv9", "vn-vtv10",
    "vn-nhandan-tv", "vn-antv", "vn-qpvn", "vn-hanoi1", "vn-hanoi2",
    "vn-htv1", "vn-htv2", "vn-htv3", "vn-htv4", "vn-htv7", "vn-htv9",
)

RADIO_PRIORITY = (
    "vn-vov1", "vn-vov2", "vn-vov3", "vn-vov4-taybac",
    "vn-vov4-taynguyen", "vn-vov4-dbscl", "vn-vov4-hcmc", "vn-vov5",
    "vn-vov-gt-hanoi", "vn-vov-gt-hcmc", "vn-vov-mekong",
    "vn-vov-english", "vn-vov5-world", "vn-hanoi-fm90", "vn-hanoi-fm96",
    "vn-voh-999", "vn-voh-956", "vn-voh-877", "vn-voh-am610",
    "vn-danang-radio", "vn-daknong-radio", "vn-dongthap-radio",
    "vn-gialai-radio", "vn-hue-radio", "vn-quangninh-qnr1",
    "vn-quangninh-qnr2", "vn-tayninh-radio", "vn-rfi-viet",
    "vn-zing-bolero", "vn-xone-fm",
)

SPORT_PRIORITY = ("vn-htv-thethao", "vn-vsbet")


def normalized(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.casefold())
    return "".join(character for character in decomposed if not unicodedata.combining(character))


def order_key(station: dict) -> tuple:
    priorities = {
        "tv": TV_PRIORITY,
        "radio": RADIO_PRIORITY,
        "sport": SPORT_PRIORITY,
    }
    category_rank = {"tv": 0, "radio": 1, "sport": 2}[station["category"]]
    priority = priorities[station["category"]]
    try:
        station_rank = priority.index(station["id"])
    except ValueError:
        station_rank = len(priority)
    return (
        category_rank,
        not station["enabled"],
        station_rank,
        normalized(station["name"]),
        station["id"],
    )


def curate(document: dict) -> dict:
    stations = document["stations"]
    by_id = {station["id"]: station for station in stations}
    for station in NEW_STATIONS:
        if station["id"] in by_id:
            by_id[station["id"]].update(station)
        else:
            stations.append(station)
            by_id[station["id"]] = station

    vtv6 = by_id["vn-vtv6-iptv"]
    vtv6["availabilityNote"] = "Kênh thể thao VTV6; nguồn đã mở và phát bằng backend của addon."
    vtv6["verification"] = confirmed(
        "BASS/BASSHLS engine confirmed playback on x64 and x86; channel identity follows the 2026 VTV6 sports relaunch."
    )

    for station_id in (
        "vn-vov2", "vn-vov3", "vn-vov5", "vn-vov-gt-hcmc",
        "vn-zing-bolero",
    ):
        by_id[station_id]["verification"] = confirmed()

    vov_mekong = by_id["vn-vov-mekong"]
    vov_mekong["streamUrl"] = "https://play.vovgiaothong.vn/live/mekong3/playlist.m3u8"
    vov_mekong["availabilityNote"] = "Nguồn trực tiếp Mekong FM đã được thay sau khi URL cũ ngừng hoạt động."
    vov_mekong["verification"] = confirmed()

    broken_radio = {
        "vn-vov-gt-hanoi": 41,
        "vn-vov-english": 2,
        "vn-vov5-world": 2,
        "vn-voh-999": 2,
        "vn-voh-956": 2,
        "vn-voh-am610": 2,
        "vn-voh-877": 2,
        "vn-xone-fm": 41,
    }
    for station_id, error_code in broken_radio.items():
        station = by_id[station_id]
        station["enabled"] = False
        station["availabilityNote"] = (
            "Tạm ẩn: nguồn không mở được trong kiểm tra ngày 30/08/2026; cần tìm URL thay thế."
        )
        station["verification"] = {
            "status": "failed",
            "checkedAt": CHECKED_AT,
            "detail": f"BASS/BASSHLS stream_open_failed: {error_code} on x64.",
        }

    vsbet = by_id["vn-vsbet"]
    vsbet["enabled"] = False
    vsbet["availabilityNote"] = "Tắt khỏi danh sách: nguồn không mở được trong kiểm tra ngày 30/08/2026."
    vsbet["verification"] = {
        "status": "failed",
        "checkedAt": CHECKED_AT,
        "detail": "BASS/BASSHLS stream_open_failed: 41 on x64.",
    }

    document["provenance"] = (
        "The original 83 station facts were personally collected by Võ Duy Khánh. "
        "Fifteen 2026 additions were independently sourced and playback-tested for this clean-room project."
    )
    document["stations"] = sorted(stations, key=order_key)
    return document


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="Write the curated catalog in place.")
    arguments = parser.parse_args()
    if arguments.write:
        parser.error("This historical 2026-08-30 migration is read-only; use the current import/audit tools to avoid overwriting later repairs.")
    document = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    document = curate(document)
    if arguments.write:
        CATALOG_PATH.write_text(
            json.dumps(document, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(json.dumps({
        "stations": len(document["stations"]),
        "active": sum(station["enabled"] for station in document["stations"]),
        "written": arguments.write,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
