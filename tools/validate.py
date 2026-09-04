# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

"""Run tests and write architecture-specific evidence for the package builder."""

import argparse
import datetime
import json
import pathlib
import struct
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from release_support import ROOT, fingerprint, version


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=pathlib.Path, default=ROOT / "work/validation")
    arguments = parser.parse_args()
    before = fingerprint()
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    successful = result.wasSuccessful() and before == fingerprint()
    architecture = "x64" if struct.calcsize("P") == 8 else "x86"
    report = {"version": version(), "architecture": architecture, "python": sys.version.split()[0],
              "generatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "fingerprint": before, "successful": successful, "testsRun": result.testsRun,
              "failures": len(result.failures), "errors": len(result.errors),
              "skipped": [{"test": str(test), "reason": reason} for test, reason in result.skipped],
              "manualNVDAAcceptance": "pending"}
    arguments.output_dir.mkdir(parents=True, exist_ok=True)
    path = arguments.output_dir / f"validation-{architecture}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Validation {architecture}: {'passed' if successful else 'failed'}; {result.testsRun} tests, {len(result.skipped)} skipped")
    return 0 if successful else 1


if __name__ == "__main__":
    raise SystemExit(main())
