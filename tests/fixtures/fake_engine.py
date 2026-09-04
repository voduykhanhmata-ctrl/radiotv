# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

import argparse
import json
import os
import sys
import time


def emit(request_id, message_type, **fields):
    message = {"version": 1, "requestId": request_id, "type": message_type}
    message.update(fields)
    print(json.dumps(message), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--request-id", required=True)
    parser.add_argument(
        "--mode",
        choices=("normal", "silent", "crash", "ended", "bad-protocol", "bad-state", "error-hang", "ended-hang", "oversized"),
        required=True,
    )
    arguments = parser.parse_args()
    command = json.loads(sys.stdin.readline())
    if command["requestId"] != arguments.request_id:
        return 3
    if arguments.mode == "silent":
        time.sleep(5)
        return 0
    if arguments.mode == "bad-protocol":
        print("not-json", flush=True)
        time.sleep(1)
        return 0
    if arguments.mode == "bad-state":
        emit(arguments.request_id, "state", state=[])
        time.sleep(5)
        return 0
    if arguments.mode == "error-hang":
        emit(arguments.request_id, "error", code="failed", detail="2")
        time.sleep(5)
        return 0
    if arguments.mode == "oversized":
        print("x" * 10000, flush=True)
        time.sleep(5)
        return 0
    emit(arguments.request_id, "ready")
    emit(arguments.request_id, "state", state="playing")
    if arguments.mode == "crash":
        os._exit(7)
    if arguments.mode in ("ended", "ended-hang"):
        emit(arguments.request_id, "state", state="ended")
        if arguments.mode == "ended-hang":
            time.sleep(5)
        return 0
    time.sleep(5)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
