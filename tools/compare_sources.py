# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

"""Read legacy code only inside this comparison process; output aggregate counts.

No legacy text, symbol names, file names, architecture, or matching fragments are
returned. Results must not be used to rewrite code around individual matches.
This is a limited similarity screen, not proof of authorship or legal clearance.
"""

import argparse
import ast
import datetime
import hashlib
import io
import json
import keyword
import pathlib
import subprocess
import tokenize

ROOT = pathlib.Path(__file__).resolve().parents[1]
WINDOW = 80


def python_features(raw: bytes):
    text = raw.decode("utf-8-sig")
    tree = ast.parse(text)
    # Data, module constants and imports do not establish code authorship.
    functions = [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    exact, normalized = set(), set()
    for node in functions:
        if len(list(ast.walk(node))) < 40:
            continue
        body = node.body
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
            body = body[1:]
        segment = "\n".join(ast.unparse(statement) for statement in body if not isinstance(statement, (ast.Import, ast.ImportFrom)))
        tokens = []
        renamed = []
        names = {}
        for token in tokenize.generate_tokens(io.StringIO(segment).readline):
            if token.type in (tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.ENDMARKER):
                continue
            tokens.append((token.type, token.string))
            value = token.string
            if token.type == tokenize.NAME and not keyword.iskeyword(value):
                value = names.setdefault(value, f"name{len(names)}")
            elif token.type in (tokenize.STRING, tokenize.NUMBER):
                value = f"literal{token.type}"
            renamed.append((token.type, value))
        for sequence, target in ((tokens, exact), (renamed, normalized)):
            for index in range(max(0, len(sequence) - WINDOW + 1)):
                encoded = repr(sequence[index:index + WINDOW]).encode("utf-8")
                target.add(hashlib.sha256(encoded).digest())
    return hashlib.sha256(raw).hexdigest(), exact, normalized


def summarize(raw_files):
    hashes, exact, normalized = set(), set(), set()
    count = failures = 0
    for raw in raw_files:
        count += 1
        try:
            digest, first, second = python_features(raw)
        except (ValueError, SyntaxError, UnicodeError, tokenize.TokenError):
            failures += 1
            continue
        hashes.add(digest)
        exact.update(first)
        normalized.update(second)
    return count, failures, hashes, exact, normalized


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legacy-root", type=pathlib.Path)
    parser.add_argument("--git-index", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    current = summarize(path.read_bytes() for path in (ROOT / "globalPlugins/radiotv").rglob("*.py"))
    references = []
    if args.git_index:
        listing = subprocess.run(["git", "-C", str(args.git_index), "ls-files", "-z", "--", "freeradio/globalPlugins"], capture_output=True, check=True).stdout
        names = [name for name in listing.decode("utf-8").split("\0") if name.endswith(".py") and "/python/" not in name]
        blobs = [subprocess.run(["git", "-C", str(args.git_index), "show", ":" + name], capture_output=True, check=True).stdout for name in names]
        references.append(("FreeRadio snapshot in local Git index", summarize(blobs)))
    if args.legacy_root:
        folder = args.legacy_root / "globalPlugins"
        paths = [path for path in folder.rglob("*.py") if not any(part in ("python", "__pycache__", "vendor") for part in path.parts)]
        references.append(("Legacy RadioTV local source", summarize(path.read_bytes() for path in paths)))
    report = {"generatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "currentPythonFiles": current[0], "currentParseFailures": current[1],
              "windowTokens": WINDOW, "scope": "Python playback addon functions; excludes DLLs, data, module constants, short functions and imports",
              "references": [], "limitations": "Aggregate token windows are not a plagiarism verdict. Renamed/literal-normalized matches can be generic code. Only the supplied snapshots were checked; no old code was exposed to the implementer."}
    for label, reference in references:
        report["references"].append({"label": label, "pythonFiles": reference[0], "parseFailures": reference[1],
            "identicalFiles": len(current[2] & reference[2]), "exact80TokenWindows": len(current[3] & reference[3]),
            "normalized80TokenWindows": len(current[4] & reference[4])})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if references and all(item[1][0] > 0 for item in references) else 1


if __name__ == "__main__":
    raise SystemExit(main())
