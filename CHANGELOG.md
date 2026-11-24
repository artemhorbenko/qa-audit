# Changelog

## 1.1.0 - 2026-11-24

- **Hand-off for AI agents.** Every run now also writes `qa-handoff.md`: YAML front matter (site, verdict, stack, not-checked areas, test command), rules for the agent, a task table, and tasks grouped by owner (`code` / `admin` / `decision`). Each task has location, reproduce steps, expected and actual results, evidence, fix steps, a suggested code block, the done-when line and its test. New `scripts/build_handoff.py`, `references/handoff-spec.md` and `docs/example-qa-handoff.md`; `build_report.py` writes it (`--no-handoff` to skip).
- New optional `audit.json` fields for the hand-off: `bugs[].where`, `detail[].owner`, `detail[].code`, `detail[].codeLang`, top-level `stack`. The validator warns when a bug has no `where`.
- **No synthetic events in production analytics.** The test runner aborts every analytics and ad request (GA4, Google Ads, DoubleClick, Meta, LinkedIn, Bing, HubSpot) and only records its URL. SKILL.md forbids granting consent in-page to watch a hit.
- Runner: `form_event` supports jQuery events (Gravity Forms `gform_confirmation_loaded`); new checks `tag_present` (GTM/GA ids on a page, any host) and `robots_disallow` (robots.txt as Google reads it, RFC 9309).
- SKILL.md: close the analytics loop by parsing the published GTM container, reading GA4 key events and counts, and reading Search Console's Pages report. Also check every host the flow touches.
- Fix: `build_report.py` escaped `<!--` as `<\!--`, which is invalid JSON and blanked the report; now `<\u0021--`.

## 1.0.0 - 2026-11-22

First public release.

- 11 QA areas in 4 groups (works, looks right, technically healthy, measured), scored 0-100 with a fixed severity scale; areas that could not be checked show "not checked" instead of a guessed score.
- Process: source check (ok / demo / no), up to 4 skippable questions, checks, findings labelled observed or hypothesis with screenshot or log evidence, severity × ICE, top-3 fixes with fix options, done-when threshold and pre-mortem, validate, build, render check, fact check.
- Safety rules: never submit forms, payments or messages (form analytics tested with a synthetic "sent" event); polite crawling; never solve captchas; 429/503 caused by the audit are not reported as broken links.
- Report template in the same design as product-lens-audit: header picture of checks passed vs failed by area, release verdict, area radar, flow route, impact/effort matrix, bug table, full bug list with screenshots, post-deploy checklist, tests table, data and confidence; tooltips, stacked phone tables, uk/en labels, light and dark themes.
- `audit.schema.json`, `validate_audit.py`, `build_report.py` (copies evidence images, writes the tests), `check_report.py` (also fails on broken evidence images).
- Rerunnable tests: generic Playwright runner (`assets/qa-tests/qa.spec.js`) driven by `qa-suite.json`, 15 check types, one request at a time, skips instead of failing when the host rate-limits; `make_tests.py`.
- English demo (fictional "Harbourline Cargo"), runner self-test fixture in `evals/runner-fixture/`.
