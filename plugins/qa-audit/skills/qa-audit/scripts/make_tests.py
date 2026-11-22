#!/usr/bin/env python3
"""Write the rerunnable Playwright tests for a QA audit.

Usage: python make_tests.py audit.json out/qa-tests

Copies assets/qa-tests/ (generic runner, config, package.json, README) and
writes qa-suite.json from audit.json's "suite". The user reruns them after
each deploy: npm install && npx playwright test. Standard library only.
"""
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ASSET = os.path.join(HERE, "..", "assets", "qa-tests")


def write_tests(suite, out):
    os.makedirs(out, exist_ok=True)
    for name in os.listdir(ASSET):
        if name != "qa-suite.json":
            shutil.copy2(os.path.join(ASSET, name), os.path.join(out, name))
    with open(os.path.join(out, "qa-suite.json"), "w", encoding="utf-8") as f:
        json.dump(suite, f, ensure_ascii=False, indent=2)
    return out


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    sys.path.insert(0, HERE)
    from validate_audit import validate_suite
    with open(sys.argv[1], encoding="utf-8") as f:
        a = json.load(f)
    suite = a.get("suite", a)  # also accepts a bare suite file
    err, warn = validate_suite(suite)
    for w in warn:
        print("[WARN] ", w)
    for e in err:
        print("[ERROR]", e)
    if err:
        return 1
    print("Written", write_tests(suite, sys.argv[2]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
