# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

"""Resolve local Help without relying on an online page."""

import pathlib


def locate_help(addon_root: pathlib.Path, language: str) -> pathlib.Path:
    normalized = language.replace("-", "_").split("_", 1)[0].casefold()
    selected = "vi" if normalized == "vi" else "en"
    candidate = addon_root / "doc" / selected / "readme.html"
    if candidate.is_file():
        return candidate
    return addon_root / "doc" / "en" / "readme.html"
