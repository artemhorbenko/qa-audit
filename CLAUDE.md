# qa-audit — notes for Claude and contributors

Start every session by reading this file and STATUS.md, then continue from Next. End every session by updating STATUS.md and committing.

A public Claude skill (Claude Code plugin + Claude app skill ZIP) that QA-tests a live website after a deploy across 11 areas (flows, forms, links, console, mobile, cross-browser, accessibility, performance, analytics events, copy, post-deploy checklist). From one `audit.json` it outputs a visual HTML report for people, a Markdown hand-off (`qa-handoff.md`) for AI coding agents, and deterministic Playwright tests to rerun after every deploy. QA only: strategy belongs to `product-lens-audit`.

## Layout

```
.claude-plugin/marketplace.json        this repo is a plugin marketplace
plugins/qa-audit/                      the only folder that ships to users
  .claude-plugin/plugin.json
  skills/qa-audit/
    SKILL.md                           the process Claude follows (keep it short)
    references/                        areas, data sources, test suite, report spec, hand-off spec, audit.schema.json
    assets/                            report-template.html, example-audit.en.json + shots/, qa-tests/ (generic Playwright runner)
    scripts/                           validate_audit, build_report, build_handoff, make_tests, check_report
evals/                                 scenarios, trigger prompts, results log (anonymised), runner-fixture/
docs/                                  README screenshots, example hand-off
qa-audit-skill.zip                     Claude app upload, rebuilt on every skill change
CLAUDE.md, STATUS.md, CHANGELOG.md,    repo docs; never move them into plugins/
ROADMAP.md
```

## Rules

- Reply to the maintainer in Ukrainian; code, docs and commits in English.
- Never invent numbers. Unknown counts stay null and show as "not checked" / "no data", and lower confidence.
- Audit only the production domain the user names. Other hosts or subdomains (found in code, search or redirects) are out of scope unless the user confirms they are live production.
- Real audits stay private (private artifacts or local files). Nothing in this repo may name a real audited site, client data or private links; log runs in `evals/results.md` anonymised.
- Public demos use fictional products only.
- Claude writes only `audit.json`; the template and scripts render the report, the hand-off and the tests. When layout breaks, change the template, not the data.
- Keep `SKILL.md` short; details go to `references/`.
- Data sources are read-only (browser, GA4, Search Console, GTM, CMS). Never submit real forms, payments or messages; never send synthetic events into production analytics (the runner aborts analytics hits); crawl politely and never solve captchas.

## Build and check

```
S=plugins/qa-audit/skills/qa-audit
python $S/scripts/validate_audit.py audit.json
python $S/scripts/build_report.py audit.json out/index.html     # also writes out/qa-handoff.md and out/qa-tests/
python $S/scripts/build_handoff.py audit.json out/qa-handoff.md  # hand-off only
python $S/scripts/check_report.py out/index.html --out ./report-check   # needs playwright + Chromium
node --check out/qa-tests/qa.spec.js
```

Before committing a template or script change, run them on `$S/assets/example-audit.en.json` and check that a deliberately broken input fails validation. After a runner change, run `evals/runner-fixture/` (see `evals/README.md`): the checks marked "expected to FAIL" must fail and the rest pass. After a template change, re-embed the example data: `build()` from `build_report.py` over `assets/report-template.html`.

## Release

1. Bump the version in `.claude-plugin/marketplace.json` and `plugins/qa-audit/.claude-plugin/plugin.json`.
2. Add a section to `CHANGELOG.md` (user-facing changes only).
3. Rebuild the ZIP: `cd plugins/qa-audit/skills && zip -qr ../../../qa-audit-skill.zip qa-audit -x '*/__pycache__/*'`
4. `claude plugin validate .`
5. Commit and push. Tags and GitHub releases are created by the maintainer.

## Related repos

Same report core and design: `product-lens-audit` (reference; shared core changes are made there first, then copied), `seo-audit`, `ui-review`, `ux-review`, `competitor-teardown` (all under github.com/artemhorbenko).
