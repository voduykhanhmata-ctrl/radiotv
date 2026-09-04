# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

"""Build deterministic 0.1 archives only after x64 and x86 validation."""

import argparse
import hashlib
import json
import os
import pathlib
import sys
import tempfile
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from release_support import ROOT, package_files, source_files, version, require_validation

VERSION = version()
OUTPUT = ROOT / "dist" / f"RadioTV-{VERSION}.nvda-addon"
FIXED_TIME = (2026, 9, 4, 0, 0, 0)


def iter_package_files():
    return iter(package_files())


def archive_name(path: pathlib.Path) -> str:
    return path.relative_to(ROOT).as_posix()


def build(*, validation_dir: pathlib.Path | None = None, source: bool = False) -> dict:
    require_validation(validation_dir or ROOT / "work/validation")
    output = ROOT / "dist" / f"RadioTV-{VERSION}-source.zip" if source else OUTPUT
    files = source_files() if source else package_files()
    names = [archive_name(path) for path in files]
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(dir=output.parent, suffix=".tmp")
    os.close(descriptor)
    temporary = pathlib.Path(temporary_name)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as package:
            for path, name in zip(files, names, strict=True):
                if path.is_symlink() or ".." in pathlib.PurePosixPath(name).parts:
                    raise RuntimeError("unsafe archive input")
                info = zipfile.ZipInfo(name, FIXED_TIME)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                package.writestr(info, path.read_bytes())
        with zipfile.ZipFile(temporary) as package:
            if package.testzip() is not None or package.namelist() != names:
                raise RuntimeError("archive validation failed")
        require_validation(validation_dir or ROOT / "work/validation")
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)
    return {"output": str(output), "version": VERSION, "files": len(names),
            "bytes": output.stat().st_size,
            "sha256": hashlib.sha256(output.read_bytes()).hexdigest(), "crc": "ok"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validation-dir", type=pathlib.Path, default=ROOT / "work/validation")
    parser.add_argument("--source", action="store_true", help="Create the source archive instead of the installable add-on.")
    arguments = parser.parse_args()
    print(json.dumps(build(validation_dir=arguments.validation_dir, source=arguments.source), ensure_ascii=False))


if __name__ == "__main__":
    main()
