# Changelog

## 1.0.0 - 2026-11-22

First public release.

- 11 QA areas in 4 groups (works, looks right, technically healthy, measured), scored 0-100 with a fixed severity scale; areas that could not be checked show "not checked" instead of a guessed score.
- Process: source check (ok / demo / no), up to 4 skippable questions, checks, findings labelled observed or hypothesis with screenshot or log evidence, severity × ICE, top-3 fixes with fix options, done-when threshold and pre-mortem, validate, build, render check, fact check.
- Safety rules: never submit forms, payments or messages (form analytics tested with a synthetic "sent" event); polite crawling; never solve captchas; 429/503 caused by the audit are not reported as broken links.
- Report template in the same design as product-lens-audit: header picture of checks passed vs failed by area, release verdict, area radar, flow route, impact/effort matrix, bug table, full bug list with screenshots, post-deploy checklist, tests table, data and confidence; tooltips, stacked phone tables, uk/en labels, light and dark themes.
- `audit.schema.json`, `validate_audit.py`, `build_report.py` (copies evidence images, writes the tests), `check_report.py` (also fails on broken evidence images).
- Rerunnable tests: generic Playwright runner (`assets/qa-tests/qa.spec.js`) driven by `qa-suite.json`, 15 check types, one request at a time, skips instead of failing when the host rate-limits; `make_tests.py`.
- English demo (fictional "Harbourline Cargo"), runner self-test fixture in `evals/runner-fixture/`.
