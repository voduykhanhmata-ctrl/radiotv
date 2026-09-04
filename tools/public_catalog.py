# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

"""Withhold signed URLs from public snapshots without modifying their originals."""

import argparse
import copy
import json
import pathlib
import urllib.parse

SENSITIVE_PARAMETERS = frozenset(("token", "play_token", "access_token", "auth", "authorization",
    "apikey", "api_key", "key", "password", "pass", "secret", "signature", "sig", "sign", "mac",
    "hdnea", "hdnts", "policy", "expires", "expire", "x-amz-credential", "x-amz-signature"))


def has_sensitive_url(value: str) -> bool:
    try:
        parts = urllib.parse.urlsplit(value)
        parameters = {key.casefold() for key, _ in urllib.parse.parse_qsl(parts.query, keep_blank_values=True)}
        return bool(parts.username is not None or parts.password is not None or parameters & SENSITIVE_PARAMETERS)
    except ValueError:
        return True


def public_document(document: dict) -> tuple[dict, list[dict]]:
    field = "stations" if "stations" in document else "entries"
    public = copy.deepcopy(document)
    withheld = [item for item in public[field] if has_sensitive_url(item.get("streamUrl", ""))]
    public[field] = [item for item in public[field] if not has_sensitive_url(item.get("streamUrl", ""))]
    return public, withheld


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        parser.error("write the public snapshot to a different file; preserve the private original")
    document, withheld = public_document(json.loads(args.input.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"withheld": len(withheld)}))


if __name__ == "__main__":
    main()
