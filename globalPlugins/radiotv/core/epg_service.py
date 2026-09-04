# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

"""Non-blocking XMLTV schedule service for the RadioTV user interface."""

from __future__ import annotations

import datetime
import gzip
import io
import threading
import time
import urllib.request
import xml.etree.ElementTree as ElementTree
from collections.abc import Callable
from dataclasses import dataclass


DEFAULT_EPG_URL = "https://lichphatsong.io.vn/epg.xml"
MAX_DOWNLOAD_BYTES = 16 * 1024 * 1024
MAX_XML_BYTES = 32 * 1024 * 1024


def decode_payload(payload: bytes, encoding: str = "") -> bytes:
    if len(payload) > MAX_DOWNLOAD_BYTES:
        raise ValueError("EPG download is too large")
    if encoding.casefold() == "gzip" or payload.startswith(b"\x1f\x8b"):
        with gzip.GzipFile(fileobj=io.BytesIO(payload)) as compressed:
            payload = compressed.read(MAX_XML_BYTES + 1)
    if len(payload) > MAX_XML_BYTES:
        raise ValueError("EPG XML is too large")
    return payload


@dataclass(frozen=True, slots=True)
class Program:
    channel_id: str
    start: datetime.datetime
    stop: datetime.datetime
    title: str


def _parse_xmltv_time(value: str) -> datetime.datetime:
    compact = " ".join(value.split())
    if len(compact) >= 20 and compact[14] == " ":
        return datetime.datetime.strptime(compact[:20], "%Y%m%d%H%M%S %z")
    parsed = datetime.datetime.strptime(compact[:14], "%Y%m%d%H%M%S")
    return parsed.replace(tzinfo=datetime.timezone.utc)


def parse_xmltv(payload: bytes) -> dict[str, tuple[Program, ...]]:
    """Parse an XMLTV payload into immutable, time-ordered channel programs."""
    if len(payload) > MAX_XML_BYTES:
        raise ValueError("EPG XML is too large")
    # XMLTV feeds must be UTF-8 and cannot define DTDs or entity expansions.
    upper_text = payload.decode("utf-8-sig").upper()
    if "<!DOCTYPE" in upper_text or "<!ENTITY" in upper_text or "\x00" in upper_text:
        raise ValueError("EPG contains unsupported XML declarations")
    del upper_text
    programs: dict[str, list[Program]] = {}
    for _event, element in ElementTree.iterparse(io.BytesIO(payload), events=("end",)):
        if element.tag != "programme":
            continue
        channel_id = element.attrib.get("channel", "").strip()
        start_text = element.attrib.get("start", "")
        stop_text = element.attrib.get("stop", "")
        title_element = element.find("title")
        title = "" if title_element is None else "".join(title_element.itertext()).strip()
        try:
            start = _parse_xmltv_time(start_text)
            stop = _parse_xmltv_time(stop_text)
        except (TypeError, ValueError):
            element.clear()
            continue
        if channel_id and title and stop > start:
            programs.setdefault(channel_id.casefold(), []).append(
                Program(channel_id, start, stop, title)
            )
        element.clear()
    return {
        channel_id: tuple(sorted(items, key=lambda item: item.start))
        for channel_id, items in programs.items()
    }


class EPGService:
    """Fetch the shared guide once on a worker thread and serve cached results."""

    def __init__(self, url: str = DEFAULT_EPG_URL):
        self._url = url
        self._lock = threading.RLock()
        self._programs: dict[str, tuple[Program, ...]] = {}
        self._state = "idle"
        self._closed = False
        self._last_refresh = 0.0
        self._callback: Callable[[], None] | None = None

    @property
    def state(self) -> str:
        with self._lock:
            return self._state

    def refresh_async(self, callback: Callable[[], None]) -> None:
        with self._lock:
            if self._closed or self._state == "loading":
                return
            self._state = "loading"
            self._callback = callback
        worker = threading.Thread(
            target=self._refresh_worker,
            args=(callback,),
            name="RadioTV-EPG",
            daemon=True,
        )
        worker.start()

    def schedule(
        self,
        channel_id: str,
        *,
        now: datetime.datetime | None = None,
        limit: int = 20,
    ) -> tuple[str, ...]:
        with self._lock:
            state = self._state
            items = self._programs.get(channel_id.casefold(), ())
            callback = self._callback
            refresh_due = time.monotonic() - self._last_refresh >= (300 if state == "error" else 21600)
        if callback is not None and refresh_due and state != "loading":
            self.refresh_async(callback)
        if limit <= 0:
            return ()
        if not channel_id:
            return ("Kênh này chưa có mã lịch phát sóng.",)
        if state in ("idle", "loading"):
            return ("Đang tải lịch phát sóng…",)
        if state == "error":
            return ("Không tải được lịch phát sóng.",)
        if not items:
            return ("Chưa có lịch phát sóng cho kênh này.",)

        current_time = now or datetime.datetime.now().astimezone()
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=datetime.timezone.utc)
        upcoming = [item for item in items if item.stop > current_time][:limit]
        if not upcoming:
            return ("Không còn chương trình nào trong dữ liệu lịch hiện tại.",)
        lines: list[str] = []
        for item in upcoming:
            local_start = item.start.astimezone(current_time.tzinfo)
            local_stop = item.stop.astimezone(current_time.tzinfo)
            prefix = "Đang phát, " if item.start <= current_time < item.stop else ""
            lines.append(
                f"{prefix}{local_start:%H:%M}–{local_stop:%H:%M}, {item.title}"
            )
        return tuple(lines)

    def close(self) -> None:
        with self._lock:
            self._closed = True

    def _refresh_worker(self, callback: Callable[[], None]) -> None:
        state = "ready"
        programs: dict[str, tuple[Program, ...]] = {}
        try:
            request = urllib.request.Request(
                self._url,
                headers={
                    "Accept-Encoding": "gzip",
                    "User-Agent": "RadioTV/0.1 (+NVDA add-on)",
                },
            )
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = decode_payload(
                    response.read(MAX_DOWNLOAD_BYTES + 1),
                    response.headers.get("Content-Encoding", ""),
                )
            programs = parse_xmltv(payload)
            if not programs:
                state = "error"
        except Exception:
            state = "error"
        with self._lock:
            if self._closed:
                return
            self._programs = programs
            self._state = state
            self._last_refresh = time.monotonic()
        callback()
