#!/usr/bin/env python3
"""Turn a QA audit.json into a finished report page, the rerunnable tests and the agent hand-off.

Usage: python build_report.py audit.json out/report.html [--template path] [--force] [--no-tests] [--no-handoff]

1. Validates the data (validate_audit.py) and stops on errors unless --force.
2. Puts the JSON into the template's <script type="application/json" id="audit">
   block, sets <html lang> and <title>, writes the page.
3. Copies evidence images (detail.*.evid[].src) next to the page, keeping
   their relative paths, so the folder can be published as one artifact.
4. If audit.json has a "suite", writes the Playwright tests to
   <out folder>/qa-tests/ (see make_tests.py) unless --no-tests.
5. Writes <out folder>/qa-handoff.md, the plain task list for AI coding
   agents (see build_handoff.py), unless --no-handoff.
Standard library only.
"""
import argparse
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from validate_audit import validate  # noqa: E402
from make_tests import write_tests  # noqa: E402
from build_handoff import write_handoff  # noqa: E402

BLOCK = re.compile(r'(<script type="application/json" id="audit">\n?)(.*?)(\n?</script>)', re.S)


def build(audit, template):
    blob = json.dumps(audit, ensure_ascii=False, indent=1)
    blob = blob.replace("</", "<\\/").replace("<!--", "<\\u0021--")
    if not BLOCK.search(template):
        raise ValueError('the template has no <script type="application/json" id="audit"> block')
    page = BLOCK.sub(lambda m: m.group(1) + blob + m.group(3), template, count=1)
    page = re.sub(r'<html lang="[^"]*"', f'<html lang="{audit.get("lang", "en")}"', page, count=1)
    title = audit.get("title")
    if title:
        safe = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        page = re.sub(r"<title>.*?</title>", lambda m: f"<title>{safe}</title>", page, count=1, flags=re.S)
    return page


def copy_evidence(audit, src_dir, out_dir):
    n = 0
    for d in (audit.get("detail") or {}).values():
        for e in d.get("evid") or []:
            rel = e.get("src")
            if not rel or re.match(r"^(https?:|data:|/)", rel):
                continue
            a, b = os.path.join(src_dir, rel), os.path.join(out_dir, rel)
            if os.path.abspath(a) != os.path.abspath(b) and os.path.exists(a):
                os.makedirs(os.path.dirname(b), exist_ok=True)
                shutil.copy2(a, b)
                n += 1
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audit")
    ap.add_argument("out")
    ap.add_argument("--template", default=os.path.join(HERE, "..", "assets", "report-template.html"))
    ap.add_argument("--force", action="store_true", help="write the page even if validation finds errors")
    ap.add_argument("--no-tests", action="store_true", help="do not write qa-tests/")
    ap.add_argument("--no-handoff", action="store_true", help="do not write qa-handoff.md")
    a = ap.parse_args()

    src_dir = os.path.dirname(os.path.abspath(a.audit))
    with open(a.audit, encoding="utf-8") as f:
        audit = json.load(f)
    err, warn = validate(audit, src_dir)
    for w in warn:
        print("[WARN] ", w)
    for e in err:
        print("[ERROR]", e)
    if err and not a.force:
        print(f"Not built: {len(err)} error(s). Fix them or pass --force.")
        return 1
    out_dir = os.path.dirname(os.path.abspath(a.out))
    os.makedirs(out_dir, exist_ok=True)
    with open(a.template, encoding="utf-8") as f:
        page = build(audit, f.read())
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(page)
    n = copy_evidence(audit, src_dir, out_dir)
    print(f"Written {a.out} ({len(page) // 1024} KB), {n} evidence file(s) copied.")
    if audit.get("suite") and not a.no_tests:
        t = write_tests(audit["suite"], os.path.join(out_dir, "qa-tests"))
        print(f"Tests: {t} ({len(audit['suite'].get('checks', []))} checks). Run: cd {t} && npm install && npx playwright test")
    if not a.no_handoff:
        h = write_handoff(audit, os.path.join(out_dir, "qa-handoff.md"))
        print(f"Hand-off for AI agents: {h}")
    print(f"Next: python {os.path.join(HERE, 'check_report.py')} {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
