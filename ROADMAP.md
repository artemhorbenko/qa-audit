# Roadmap

Ideas and planned work.

## Done in 1.1.0: two outputs, a report for people and a hand-off for AI agents

Shipped as `qa-handoff.md` (see `references/handoff-spec.md`). Still open from the plan below: `qa-handoff.json`, `--handoff-lang`, and the eval in which an agent fixes a fixture site from the hand-off alone.

**Idea.** Every run produces two files from the same `audit.json`:

1. **Report for people** (what exists now): `index.html` with the current design and layout, i.e. the verdict, charts, tooltips, light and dark themes.
2. **Hand-off for AI agents** (new): a plain, technical file that the requester gives to an AI coding agent (Claude Code, Cursor, Codex…) to implement the fixes. It has no icons, no design and no prose meant to persuade, only structure an agent can act on.

**Proposed format:** `qa-handoff.md`, Markdown with one YAML front-matter block. Markdown is easy for agents to read, diff and paste into a ticket; the front matter keeps the machine-readable parts. `audit.json` stays the full source of truth.

Draft structure:

```markdown
---
site: https://example.com
audited: 2026-11-22
deploy: redesign 21.11.2026
verdict: fix-before-next-deploy
stack: [WordPress, Contact Form 7, GA4 gtag.js, Polylang]   # what was detected
not_checked: [browsers, phone-390px]
tests: qa-tests/  (run: npx playwright test)
---

# Task list for an implementing agent

Rules: do not submit forms; do not change business facts (prices, terms)
without the owner; after each fix run the listed test; one commit per bug.

## BUG-01 · critical · analytics · observed
Title: Quote form success does not send generate_lead to GA4
Where: all pages with `.wpcf7` (form id 6066)
Reproduce:
  1. …
Expected: …
Actual: …
Evidence: dataLayer +0 after synthetic wpcf7mailsent
Fix:
  - file/place: theme functions.php or WPCode snippet (site-wide)
  - code: document.addEventListener('wpcf7mailsent', e => gtag('event','generate_lead',{form_id:e.detail.contactFormId}))
  - then: mark generate_lead as key event in GA4 (owner, admin UI)
Done when: test T05 passes + DebugView shows generate_lead
Owner action needed: yes (GA4 admin)
Risk: double counting if GTM is added later

## BUG-02 …
```

**Rules for the hand-off:**
- Order matches the report (severity, then ICE), with stable ids (`BUG-01`, which maps to bug #1, and test ids `T05`).
- Every bug gets: area, severity, observed/hypothesis, exact location (URL, selector, template, plugin, setting), reproduce steps, expected/actual, evidence as text, concrete fix steps with code where possible, the test that proves it, and whether the owner has to act (admin access, business wording).
- Hypotheses are marked "verify first, do not fix blindly".
- Not-checked areas are listed so the agent does not assume they are fine.
- Separate sections for the agent: **can do in code**, **needs CMS/admin access**, and **needs the owner's decision** (e.g. "keep the RU version or redirect it").
- No tooltips, icons, colours, charts or rhetorical headings; one fact per line.
- Same language as the report by default; optional `--handoff-lang en`, since agents work well in English.

**Build steps:**
- [x] `scripts/build_handoff.py audit.json out/qa-handoff.md`, called by `build_report.py` (flag `--no-handoff` to skip).
- [x] Add optional fields to `audit.json` that the hand-off needs and the report can ignore: `bugs[].where` (url/selector/template), `detail[].code` (patch snippet), `detail[].owner` (owner action needed), `stack` (detected CMS, plugins, analytics).
- [x] Validator: warn when a bug has no `where`; error when a fix in a hand-off has no test and no "done when".
- [ ] Optional `qa-handoff.json` (same content, strict schema) for agents and services that prefer JSON.
- [x] SKILL.md step 5: deliver both files, and in chat offer: "give `qa-handoff.md` to your coding agent".
- [ ] Eval: an agent fixes a test fixture site from the hand-off alone (without the HTML report), then the suite passes.

**Fits the WordPress QA service idea:** the hand-off is what a service would attach to a ticket or a PR, or pass straight to an agent that opens the PR, with the Playwright suite as the acceptance test.
