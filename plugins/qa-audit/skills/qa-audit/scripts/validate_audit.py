#!/usr/bin/env python3
"""Check a QA audit.json before it becomes a report.

Usage: python validate_audit.py audit.json

Errors (exit 1) break the report or the skill's rules; warnings (exit 0)
are worth a look. Evidence image paths are checked relative to the
audit.json folder. Standard library only.
"""
import json
import os
import re
import sys

AREAS = {"flows", "forms", "links", "errors", "mobile", "browsers", "a11y", "perf", "analytics", "copy", "deploy"}
GROUPS = {"works", "looks", "health", "measure"}
SEV = ["blocker", "critical", "major", "minor", "trivial"]
LANGS = {"uk", "en"}
STATUSES = {"ok", "demo", "no"}
CHECK_ST = {"pass", "fail", "warn", "nc"}
TEST_ST = {"pass", "fail", "new", "nc"}
TOKENS = re.compile(r"\{(health|qw|n|conf|passed|failed|warned|checks|crit|tests|nc)\}")
TEXT_KEYS = ["headline", "lead", "areasH", "flowsH", "matrixH", "bugsH", "nextH", "planH", "dataH"]
EVID_KINDS = {"shot", "log", "console", "network", "dom", "psi", "axe"}
# check types the bundled runner (assets/qa-tests/qa.spec.js) understands
SUITE_TYPES = {"status", "redirect", "ga4_tag", "click_event", "form_event", "form_fields", "text", "no_text",
               "ui_language", "console_clean", "no_h_scroll", "page_links", "sitemap", "axe", "meta",
               "tag_present", "robots_disallow"}


def rank(o):
    ice = o.get("I", 0) * o.get("C", 0) * o.get("E", 0) if all(isinstance(o.get(k), int) for k in "ICE") else 0
    s = SEV.index(o["sev"]) if o.get("sev") in SEV else 9
    return s, -ice


def validate(a, base="."):
    err, warn = [], []
    E, W = err.append, warn.append
    if not isinstance(a, dict):
        return ["the file is not a JSON object"], []

    if a.get("lang") not in LANGS:
        W(f"lang '{a.get('lang')}' has no interface dictionary; labels fall back to English")
    text = a.get("text") or {}
    for k in TEXT_KEYS:
        if not str(text.get(k, "")).strip():
            E(f"text.{k} is missing: every section needs a heading that states its point")
    if "<" in json.dumps({k: v for k, v in text.items() if k != "testsCmd"}, ensure_ascii=False):
        W("text contains '<': HTML is shown as plain text; use [[...]] to highlight words")

    # areas
    areas = a.get("areas") or []
    ids = [x.get("i") for x in areas]
    if set(ids) != AREAS:
        W(f"areas should cover all 11 QA areas; missing: {sorted(AREAS - set(ids))}")
    if len(ids) != len(set(ids)):
        E("an area id appears twice")
    nc = 0
    for i, x in enumerate(areas):
        p = f"areas[{i}]"
        if x.get("i") not in AREAS:
            E(f"{p}.i '{x.get('i')}' is not an area id ({', '.join(sorted(AREAS))})")
        if x.get("g") not in GROUPS:
            E(f"{p}.g '{x.get('g')}' is not a group ({', '.join(sorted(GROUPS))})")
        if not x.get("k"):
            E(f"{p}.k (short name) is missing")
        s = x.get("s")
        if s is None:
            nc += 1
            if any(x.get(k) for k in ("pass", "fail", "warn")):
                E(f"{p} is not checked (s: null) but has check counts")
            continue
        if not isinstance(s, (int, float)) or not 0 <= s <= 100:
            E(f"{p}.s must be 0-100, or null when the area was not checked")
        for k in ("pass", "fail", "warn"):
            v = x.get(k, 0)
            if not isinstance(v, int) or v < 0:
                E(f"{p}.{k} must be a whole number >= 0")
        if not (x.get("pass", 0) + x.get("fail", 0) + x.get("warn", 0)):
            E(f"{p} has a score but no checks: give pass/fail/warn counts or set s to null")
    if nc and not any(s.get("status") == "no" for s in a.get("sources", [])):
        W("some areas are not checked but no source is marked 'no': say what was missing")

    v = a.get("verdict")
    if v is not None and (not isinstance(v.get("cur"), int) or not 0 <= v["cur"] <= 3):
        E("verdict.cur must be 0-3 (blocks release, fix before next deploy, fix in backlog, ready)")
    for i, r in enumerate(a.get("route") or []):
        if r.get("st") not in ("ok", "warn", "bad"):
            E(f"route[{i}].st must be ok, warn or bad")

    # bugs
    bugs = a.get("bugs") or []
    detail = a.get("detail") or {}
    tests = {t.get("id") for t in a.get("tests") or []}
    for i, o in enumerate(bugs):
        oid, p = i + 1, f"bugs[{i}] (#{i + 1})"
        for k in ("I", "C", "E"):
            if not isinstance(o.get(k), int) or not 1 <= o[k] <= 10:
                E(f"{p}.{k} must be a whole number 1-10")
        if o.get("x") not in ("bug", "gap"):
            E(f"{p}.x must be bug or gap")
        if o.get("sev") not in SEV:
            E(f"{p}.sev must be one of {', '.join(SEV)}")
        if o.get("ev") not in ("obs", "hyp"):
            E(f"{p}.ev must be obs (observed) or hyp (hypothesis)")
        if o.get("l") not in AREAS:
            E(f"{p}.l '{o.get('l')}' is not an area id")
        if not o.get("t") or not o.get("ln"):
            E(f"{p} needs t (title) and ln (area label)")
        if o.get("ev") == "hyp" and o.get("sev") in ("blocker", "critical"):
            W(f"{p} is a hypothesis marked {o['sev']}: confirm it before calling it critical")
        if o.get("ev") == "hyp" and isinstance(o.get("C"), int) and o["C"] > 7:
            W(f"{p} is a hypothesis with confidence {o['C']}: confidence above 7 needs evidence")
        d = detail.get(str(oid))
        if not d:
            E(f"{p} has no detail[\"{oid}\"]: every bug needs steps, expected, actual and evidence")
            continue
        if len(d.get("steps") or []) < 2:
            E(f"detail[\"{oid}\"].steps needs at least 2 steps to reproduce")
        for k in ("exp", "act", "effort", "risk"):
            if not str(d.get(k, "")).strip():
                E(f"detail[\"{oid}\"].{k} is missing")
        if not d.get("fix"):
            E(f"detail[\"{oid}\"].fix needs at least one step")
        ev = d.get("evid") or []
        if o.get("ev") == "obs" and not ev:
            E(f"detail[\"{oid}\"].evid is empty: an observed bug needs a screenshot or a log line")
        for j, e in enumerate(ev):
            if e.get("k") not in EVID_KINDS:
                E(f"detail[\"{oid}\"].evid[{j}].k must be one of {', '.join(sorted(EVID_KINDS))}")
            if not e.get("src") and not e.get("t"):
                E(f"detail[\"{oid}\"].evid[{j}] needs src (image) or t (log text)")
            src = e.get("src")
            if src:
                if re.match(r"^(https?:|data:|/)", src):
                    W(f"detail[\"{oid}\"].evid[{j}].src should be a relative path next to the report (e.g. shots/01.jpg)")
                elif not os.path.exists(os.path.join(base, src)):
                    E(f"detail[\"{oid}\"].evid[{j}].src '{src}' does not exist next to audit.json")
        if d.get("test") and tests and d["test"] not in tests:
            E(f"detail[\"{oid}\"].test '{d['test']}' is not in tests")
        if not o.get("where"):
            W(f"{p} has no where (url / selector / file / plugin / setting): the agent hand-off needs a location")
        if d.get("owner") and d["owner"] not in ("code", "admin", "decision"):
            E(f"detail[\"{oid}\"].owner must be code, admin or decision")
        if not d.get("test") and o.get("x") == "bug":
            W(f"{p} has no automated test: add one to the suite so the fix is checked after each deploy")
    for k in detail:
        if not k.isdigit() or not 1 <= int(k) <= len(bugs):
            E(f"detail[\"{k}\"] does not match any bug")

    ranked = sorted(range(1, len(bugs) + 1), key=lambda j: (rank(bugs[j - 1]), j))
    for oid in ranked[:3]:
        pl = (a.get("plans") or {}).get(str(oid))
        if not pl or not all(str(pl.get(k, "")).strip() for k in ("h", "m", "t")):
            E(f"top-3 bug #{oid} needs plans[\"{oid}\"] with h (what is broken), m (done when), t (how to verify)")
        d = detail.get(str(oid)) or {}
        for k in ("alt", "thr", "pm"):
            if not d.get(k):
                E(f"top-3 bug #{oid} needs detail.{k} (fix options, done-when threshold, pre-mortem)")

    # checklist, tests, suite
    for i, c in enumerate(a.get("checklist") or []):
        if c.get("st") not in CHECK_ST or not c.get("t"):
            E(f"checklist[{i}] needs t and st ({', '.join(sorted(CHECK_ST))})")
    seen = set()
    for i, t in enumerate(a.get("tests") or []):
        if not t.get("id") or not t.get("t"):
            E(f"tests[{i}] needs id and t")
        if t.get("id") in seen:
            E(f"tests[{i}].id '{t.get('id')}' is used twice")
        seen.add(t.get("id"))
        if t.get("st") not in TEST_ST:
            E(f"tests[{i}].st must be one of {', '.join(sorted(TEST_ST))}")
        if t.get("area") not in AREAS:
            E(f"tests[{i}].area '{t.get('area')}' is not an area id")
    suite = a.get("suite")
    if suite:
        err2, warn2 = validate_suite(suite)
        err += err2
        warn += warn2
        sids = {c.get("id") for c in suite.get("checks", [])}
        for t in a.get("tests") or []:
            if t.get("id") not in sids:
                E(f"tests '{t.get('id')}' has no check with that id in suite.checks")
    elif a.get("tests"):
        W("tests are listed but there is no suite: the user cannot rerun them")

    # sources and numbers
    sources = a.get("sources") or []
    names = {s.get("name") for s in sources}
    if not sources:
        E("sources is empty: list what was used and what was missing")
    for i, s in enumerate(sources):
        if s.get("status") not in STATUSES:
            E(f"sources[{i}].status must be ok, demo or no")
    for i, k in enumerate(a.get("kpis") or []):
        val = str(k.get("v", ""))
        if not TOKENS.search(val) and re.search(r"\d", val):
            if not k.get("src"):
                E(f"kpis[{i}] '{val}' has a number but no src")
            elif k["src"] not in names:
                E(f"kpis[{i}].src '{k['src']}' is not in sources")
            elif next((s for s in sources if s.get("name") == k["src"]), {}).get("status") == "no":
                E(f"kpis[{i}] cites '{k['src']}', which is marked as not available")
    for i, q in enumerate(a.get("answers") or []):
        if not q.get("q") or not q.get("a"):
            E(f"answers[{i}] needs q and a (for a skipped question, a = the assumption taken)")
    st = a.get("stack")
    if st is not None and not (isinstance(st, list) and all(isinstance(x, str) for x in st)):
        E("stack must be a list of strings (detected CMS, plugins, analytics)")
    gl = a.get("glossary") or {}
    for k, val in gl.items():
        if not val.get("g") or not val.get("d"):
            E(f"glossary['{k}'] needs g and d")
    if not gl:
        W("glossary is empty: terms will have no tooltips")
    return err, warn


def validate_suite(s):
    err, warn = [], []
    E, W = err.append, warn.append
    if not str(s.get("baseURL", "")).startswith("http"):
        E("suite.baseURL must be an http(s) URL")
    ids = set()
    for i, c in enumerate(s.get("checks") or []):
        p = f"suite.checks[{i}] ({c.get('id')})"
        if not c.get("id"):
            E(f"{p} needs an id")
        if c.get("id") in ids:
            E(f"{p} id is used twice")
        ids.add(c.get("id"))
        if c.get("type") not in SUITE_TYPES:
            E(f"{p}.type '{c.get('type')}' is not supported ({', '.join(sorted(SUITE_TYPES))})")
        if c.get("submit") or "submit" in str(c.get("click", "")).lower():
            E(f"{p} would submit a form: tests must stop before submit")
        if c.get("type") in ("click_event", "form_event") and not c.get("event"):
            E(f"{p} needs event (the GA4 event name expected)")
        if c.get("type") in ("text", "no_text") and not (c.get("text") or c.get("pattern")):
            E(f"{p} needs text or pattern")
        if c.get("type") == "tag_present" and not c.get("ids"):
            E(f"{p} needs ids (e.g. [\"GTM-XXXX\"])")
        if c.get("type") == "robots_disallow" and not (c.get("agent") and (c.get("disallowed") or c.get("allowed"))):
            E(f"{p} needs agent and disallowed/allowed paths")
        if c.get("type") == "redirect" and not (c.get("from") and c.get("to")):
            E(f"{p} needs from and to")
    if not s.get("checks"):
        E("suite.checks is empty")
    if (s.get("delayMs") or 0) < 500:
        W("suite.delayMs below 500: many hosts block fast crawlers (429, captcha); keep 1000+")
    return err, warn


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    path = sys.argv[1]
    with open(path, encoding="utf-8") as f:
        try:
            a = json.load(f)
        except json.JSONDecodeError as e:
            print(f"[ERROR] not valid JSON: {e}")
            return 1
    err, warn = validate(a, os.path.dirname(os.path.abspath(path)))
    for e in err:
        print("[ERROR]", e)
    for w in warn:
        print("[WARN] ", w)
    print("OK" if not err else f"{len(err)} error(s)")
    return 1 if err else 0


if __name__ == "__main__":
    sys.exit(main())
