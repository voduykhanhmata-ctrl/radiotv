# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

"""Versioned JSON-line messages emitted by the isolated audio worker."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


PROTOCOL_VERSION = 1
_STATES = frozenset(("playing", "stalled", "ended"))


class ProtocolError(ValueError):
    """Raised when a worker line violates the protocol contract."""


@dataclass(frozen=True, slots=True)
class EngineMessage:
    request_id: str
    message_type: str
    state: str | None = None
    code: str | None = None
    detail: str = ""


def parse_engine_message(line: str, expected_request_id: str) -> EngineMessage:
    if len(line) > 4096:
        raise ProtocolError("worker message is too large")
    try:
        value: Any = json.loads(line)
    except json.JSONDecodeError as error:
        raise ProtocolError("worker message is not valid JSON") from error
    if not isinstance(value, dict):
        raise ProtocolError("worker message root must be an object")
    if type(value.get("version")) is not int or value["version"] != PROTOCOL_VERSION:
        raise ProtocolError("worker protocol version is unsupported")
    if value.get("requestId") != expected_request_id:
        raise ProtocolError("worker request ID does not match")

    message_type = value.get("type")
    if message_type == "ready":
        if set(value) != {"version", "requestId", "type"}:
            raise ProtocolError("ready message fields do not match")
        return EngineMessage(expected_request_id, "ready")
    if message_type == "state":
        if set(value) != {"version", "requestId", "type", "state"}:
            raise ProtocolError("state message fields do not match")
        state = value.get("state")
        if not isinstance(state, str) or state not in _STATES:
            raise ProtocolError("worker state is unsupported")
        return EngineMessage(expected_request_id, "state", state=state)
    if message_type == "error":
        if set(value) != {"version", "requestId", "type", "code", "detail"}:
            raise ProtocolError("error message fields do not match")
        code = value.get("code")
        detail = value.get("detail")
        if not isinstance(code, str) or re.fullmatch(r"[a-z][a-z0-9_]{0,79}", code) is None:
            raise ProtocolError("worker error code is invalid")
        if not isinstance(detail, str) or len(detail) > 500:
            raise ProtocolError("worker error detail is invalid")
        if any(ord(character) < 32 or ord(character) == 127 for character in detail):
            raise ProtocolError("worker error detail contains control characters")
        if "http://" in detail.casefold() or "https://" in detail.casefold():
            raise ProtocolError("worker error detail contains a URL")
        return EngineMessage(
            expected_request_id,
            "error",
            code=code,
            detail=detail,
        )
    raise ProtocolError("worker message type is unsupported")
