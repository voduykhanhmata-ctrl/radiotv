# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

"""Find public audio/video stream URLs exposed by a broadcaster web page."""

from __future__ import annotations

import argparse
import html
import json
import re
import urllib.parse
import urllib.request


STREAM_PATTERN = re.compile(
    r"https?://[^\s\"'<>\\]+?(?:\.m3u8|\.mp3|\.aac)(?:\?[^\s\"'<>\\]*)?",
    re.IGNORECASE,
)
SCRIPT_PATTERN = re.compile(r"<script[^>]+src=[\"']([^\"']+)[\"']", re.IGNORECASE)
LINK_PATTERN = re.compile(r"<a[^>]+href=[\"']([^\"']+)[\"']", re.IGNORECASE)


def fetch(url: str, timeout: float) -> str:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "RadioTV clean-room stream verifier/0.1"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", "replace")


def streams_in(text: str) -> set[str]:
    decoded = html.unescape(text).replace("\\/", "/")
    return {match.rstrip("),]") for match in STREAM_PATTERN.findall(decoded)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--follow-scripts", action="store_true")
    parser.add_argument("--link-contains", help="Also list same-host links containing this text.")
    parser.add_argument("--timeout", type=float, default=20.0)
    arguments = parser.parse_args()

    page = fetch(arguments.url, arguments.timeout)
    found = streams_in(page)
    page_host = urllib.parse.urlsplit(arguments.url).hostname
    matching_links = []
    if arguments.link_contains:
        matching_links = sorted({
            urllib.parse.urljoin(arguments.url, html.unescape(link))
            for link in LINK_PATTERN.findall(page)
            if arguments.link_contains in link
            and urllib.parse.urlsplit(
                urllib.parse.urljoin(arguments.url, html.unescape(link))
            ).hostname == page_host
        })
    checked_scripts = []
    if arguments.follow_scripts:
        for source in SCRIPT_PATTERN.findall(page):
            script_url = urllib.parse.urljoin(arguments.url, html.unescape(source))
            if urllib.parse.urlsplit(script_url).hostname != page_host:
                continue
            checked_scripts.append(script_url)
            try:
                found.update(streams_in(fetch(script_url, arguments.timeout)))
            except Exception:
                continue

    print(json.dumps({
        "page": arguments.url,
        "streams": sorted(found),
        "matchingLinks": matching_links,
        "sameHostScriptsChecked": len(checked_scripts),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
