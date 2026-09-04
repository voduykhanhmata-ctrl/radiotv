# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

"""Explicit release contents and evidence bound to their exact contents."""

import hashlib
import json
import pathlib
import re
from public_catalog import has_sensitive_url

ROOT = pathlib.Path(__file__).resolve().parents[1]


def version() -> str:
    text = (ROOT / "manifest.ini").read_text(encoding="utf-8")
    match = re.search(r"^version\s*=\s*(\S+)\s*$", text, re.MULTILINE)
    if match is None or re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[a-z0-9.]+)?", match[1]) is None:
        raise ValueError("manifest version is missing or unsafe")
    return match[1]


def package_files() -> list[pathlib.Path]:
    names = ["manifest.ini", "LICENSE", "LICENSING.md", "THIRD_PARTY_NOTICES.md",
             "data/stations.json", "data/stations.schema.json",
             "doc/vi/readme.html", "doc/en/readme.html",
             "third_party/BASS/BASS.txt", "third_party/BASS/BASSHLS.txt"]
    for arch in ("x64", "x86"):
        names.extend(f"globalPlugins/radiotv/runtime/{arch}/{name}" for name in ("bass.dll", "basshls.dll"))
    names.extend(path.relative_to(ROOT).as_posix()
                 for path in (ROOT / "globalPlugins/radiotv").rglob("*")
                 if path.suffix in (".py", ".ps1") and "__pycache__" not in path.parts)
    paths = [ROOT / name for name in sorted(set(names))]
    for path in paths:
        if not path.is_file() or path.is_symlink():
            raise RuntimeError("missing or symbolic release file: " + path.relative_to(ROOT).as_posix())
    return paths


def source_files() -> list[pathlib.Path]:
    paths = set(package_files())
    paths.update(ROOT.glob("*.md"))
    paths.update(ROOT / name for name in (".gitignore", ".gitattributes"))
    for directory, pattern in (("tools", "*.py"), ("tests", "*.py"), (".github", "*.yml"), ("reports", "*.md")):
        paths.update(path for path in (ROOT / directory).rglob(pattern) if "__pycache__" not in path.parts)
    paths.update((ROOT / "data").glob("*_unsupported.json"))
    return sorted(paths, key=lambda path: path.relative_to(ROOT).as_posix())


def fingerprint() -> str:
    digest = hashlib.sha256()
    for path in source_files():
        relative = path.relative_to(ROOT).as_posix()
        if relative.startswith("reports/"):
            continue
        if path.is_symlink():
            raise RuntimeError("symbolic source file: " + relative)
        digest.update(relative.encode("utf-8") + b"\0" + hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def require_validation(directory: pathlib.Path) -> None:
    current = fingerprint()
    for path in (ROOT / "data").glob("*.json"):
        document = json.loads(path.read_text(encoding="utf-8"))
        for entry in document.get("stations", document.get("entries", [])):
            if has_sensitive_url(entry.get("streamUrl", "")):
                raise RuntimeError("public release contains a signed URL; use tools/public_catalog.py first")
    for architecture in ("x64", "x86"):
        path = directory / f"validation-{architecture}.json"
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise RuntimeError(f"run tools/validate.py on {architecture} before packaging") from error
        if (report.get("architecture") != architecture or report.get("successful") is not True
                or report.get("fingerprint") != current or report.get("version") != version()
                or not isinstance(report.get("testsRun"), int) or report["testsRun"] < 1):
            raise RuntimeError(f"missing, failed, or stale {architecture} validation")
