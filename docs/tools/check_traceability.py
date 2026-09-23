#!/usr/bin/env python3
"""Checks that every business rule (BR-xx) of the SRS is covered by at least one test.

Usage (from the repository root):
    python docs/tools/check_traceability.py            # report only, exit 1 if a covered BR lost its test
    python docs/tools/check_traceability.py --write    # also update docs/test/traceability.csv
    python docs/tools/check_traceability.py --strict   # exit 1 while any BR has no test (use before release)

A test covers a rule when its name starts with the rule id without the dash,
following the naming convention `<RuleId>_<Scenario>_<Expected>`, e.g.
`BR28_longStopBelowLiquidation_returnsBlocking`.
Searched: backend/src/test, ai-service/test, web/src, mobile/test.
"""
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "docs" / "test" / "traceability.csv"
SEARCH = [
    (ROOT / "backend" / "src" / "test", {".java"}),
    (ROOT / "ai-service" / "test", {".ts"}),
    (ROOT / "web" / "src", {".ts", ".tsx"}),
    (ROOT / "mobile" / "test", {".dart"}),
]
TEST_NAME = re.compile(r"\b(BR\d{2})_[A-Za-z0-9_]+")
SKIP_DIRS = {"target", "node_modules", "dist", "build", ".dart_tool", "coverage"}


def find_tests():
    found = defaultdict(list)
    for base, exts in SEARCH:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.suffix not in exts or any(p in SKIP_DIRS for p in path.parts):
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for m in TEST_NAME.finditer(text):
                rule = m.group(1)[:2] + "-" + m.group(1)[2:]
                found[rule].append((str(path.relative_to(ROOT)), m.group(0)))
    return found


def main():
    write = "--write" in sys.argv
    strict = "--strict" in sys.argv
    if not CSV_PATH.exists():
        print(f"missing {CSV_PATH}")
        return 1

    with CSV_PATH.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        rows = list(reader)

    found = find_tests()
    br_rows = [r for r in rows if r["kind"] == "BusinessRule"]
    covered = [r for r in br_rows if r["id"] in found]
    missing = [r for r in br_rows if r["id"] not in found]
    regressed = [r for r in missing if r["status"] == "COVERED"]

    for r in rows:
        if r["kind"] == "BusinessRule" and r["id"] in found:
            files = sorted({p for p, _ in found[r["id"]]})
            names = sorted({n for _, n in found[r["id"]]})
            r["test_name"] = "; ".join(names[:3]) + (" …" if len(names) > 3 else "")
            r["code_namespace"] = r["code_namespace"] or "; ".join(files[:2])
            r["status"] = "COVERED"
        elif r["kind"] == "BusinessRule" and r["status"] == "COVERED":
            r["status"] = "REGRESSED"

    pct = 100 * len(covered) // max(1, len(br_rows))
    print(f"Business rules covered by tests: {len(covered)}/{len(br_rows)} ({pct}%)")
    if regressed:
        print("REGRESSED (was covered, test no longer found): " + ", ".join(r["id"] for r in regressed))
    if missing and ("--verbose" in sys.argv or strict):
        print("Not covered: " + ", ".join(r["id"] for r in missing))

    if write:
        with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
        print(f"updated {CSV_PATH.relative_to(ROOT)}")

    if regressed or (strict and missing):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
