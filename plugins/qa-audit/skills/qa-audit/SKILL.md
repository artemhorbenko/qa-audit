---
name: qa-audit
description: QA-audit a live website or web app after a deploy or redesign - key user flows, forms (never submitted), broken links and redirects, console and network errors, mobile and tablet layout, cross-browser, accessibility (axe), performance (PageSpeed), GA4 tags and key events, copy and translation errors, post-deploy checklist - and deliver a visual bug report, a hand-off file for AI coding agents and deterministic Playwright tests to rerun after every deploy. Use when someone asks to test, QA, smoke-test or check a site after a release, find bugs, verify tracking or events, or make post-deploy tests. Not for product strategy (use product-lens-audit).
---

# QA Audit

Test a live site the way a careful QA engineer would after a deploy, and hand back four things: a visual report for people, a bug list with steps / expected / actual / evidence, a plain hand-off file for the AI coding agent that will implement the fixes (`qa-handoff.md`), and Playwright tests the owner can rerun after every deploy. This skill covers QA only. Growth, positioning and conversion strategy belong to product-lens-audit.

Respond in the user's language, and write the report in it too.

Files next to this SKILL.md (read each when its step comes, not up front):
- `references/data-sources.md` - which tools to look for (browser, PageSpeed, CMS, GA4), fallbacks, politeness rules (steps 0-1).
- `references/areas.md` - the 11 QA areas: what to check in each, how to count checks, how to score, severity scale (steps 2-3).
- `references/test-suite.md` - the check types of the bundled Playwright runner and how to write `suite` (step 4).
- `references/report-spec.md` and `references/audit.schema.json` - the report's sections and the shape of `audit.json` (step 5).
- `assets/report-template.html` - the report page; it renders everything from one JSON block. `assets/example-audit.en.json` is a full example (fictional site "Northwind Freight").
- `assets/qa-tests/` - the generic Playwright runner (`qa.spec.js`), config and README that ship to the user.
- `scripts/validate_audit.py`, `scripts/build_report.py`, `scripts/build_handoff.py`, `scripts/make_tests.py`, `scripts/check_report.py` - data check, page + hand-off + tests build, render check.

## Safety rules (apply to every step)

- **Never submit real forms, payments, orders, sign-ups or messages.** Fill a form only to see validation, then stop before the submit button. To check what happens after a send, fire the form's "sent" DOM event in the browser (`wpcf7mailsent` for Contact Form 7, `submit_success` for Elementor forms, etc.) so nothing reaches the server. If the owner wants one real test submission, they do it themselves, marked "TEST".
- **Never send synthetic events into production analytics.** A simulated "form sent" must not become a fake lead in GA4 or Ads. Before firing one, either keep consent denied (most consent-mode sites then send nothing) or intercept and drop analytics requests (`/g/collect`, `googleadservices`, `doubleclick`, `facebook.com/tr`…). Do not grant consent in-page to "see the hit": gtag may hold its own references to the network functions and bypass your stub. Verify that hits really arrive in GA4 reports or DebugView, using the owner's real traffic. The generated tests abort every analytics hit automatically.
- **Do not click** tel:, mailto:, delete, logout, or anything that opens an OS dialog without preventing the navigation first (capture-phase `preventDefault`).
- **Be polite to the host.** One request at a time with ≥ 1 s between them; at most ~60 pages per run. If you get 429, 503 or a captcha, stop crawling, mark the area partial, and never solve the captcha. Do not count 429/503 that your own crawl caused as bugs.
- Use connected sources read-only. Do not change CMS content, plugins or analytics settings during the audit.

## 0. Check which tools and data sources are connected

Look at the tools this session actually has (search the tool list / ToolSearch; never assume). `references/data-sources.md` says what to look for. Build a source list with a status for each: `ok` (used), `demo` (partial: e.g. crawl stopped by rate limit, only one viewport), `no` (not available, or failing after one retry). Typical rows: browser, headless Playwright, PageSpeed Insights, CMS connector, GA4, second browser engine.

If something important is missing, say which in one line and continue; never fill the gap with invented results. Each `no` lowers confidence, and an area you could not check gets `s: null` ("not checked"), not a guessed score.

## 0.5 Ask the requester (every question skippable)

First look for saved context: a previous `audit.json` or `qa-tests/qa-suite.json` in the project or attached. With a previous run, compare: which bugs are fixed, which tests now pass, what is new.

If the brief does not already say it, ask one round of up to 4 questions (multiple-choice tool when available, each with a "Skip" option; otherwise plain text). Never block: a skipped question becomes a stated assumption.
- **What changed** in this deploy (redesign, new plugin, migration, new language)?
- **Key flows** that must work (quote form, checkout, sign-up, call/email click).
- **Access**: GA4, Search Console, CMS, staging URL, test account.
- **Known issues** to confirm or rule out.

A detailed brief counts as answers: record them and skip the questions. List all questions with answers in `answers`.

## 1. Run the checks (before judging anything)

Read `references/areas.md` and go area by area. Use the browser for the live site:
- **Claude in Chrome / built-in / cloud browser:** navigate, read the DOM with JavaScript, read console and network, take screenshots with `save_to_disk` (they land in the workspace; copy them to `shots/NN-name.jpg` next to `audit.json`). The window may not shrink below ~600 px: to test 390 px, rely on headless Playwright or the generated `no_h_scroll` test and mark the phone check "not checked" until it runs.
- **Headless Playwright** in the shell, when the shell can reach the site: the most reliable way to test viewports and engines (Chromium, Firefox, WebKit). Run the generated suite (step 4) as your own check.
- **PageSpeed Insights** (pagespeed.web.dev in the browser, or its API) for performance, Core Web Vitals and Lighthouse accessibility.
- **CMS connector** (WordPress etc.), read-only: active plugins (forms, analytics, language, cache, SEO), menus, translations.

For analytics, instrument before acting: wrap `dataLayer.push`, block analytics requests (see the safety rules), then do the action (click, synthetic form event) and see what reached the dataLayer. Then close the loop from the other end:
- **Read the published GTM container** (`https://www.googletagmanager.com/gtm.js?id=GTM-…`, parse its `var data = {…}`): tags, triggers and their conditions (host, path, form id, event). Many tracking bugs are a mismatch between what the page pushes and what the trigger expects (`formId == demo-form` while the form is `contact-demo`), or a tag that never loads on one host.
- **GA4 (read only)**: Admin → Events → Key events ("No stream data detected" = a key event that never fires) and Reports → Events for 28-day counts; compare event pairs (form lead vs meeting booked).
- **Search Console (read only)**: Pages report reasons (5xx, 404, blocked by robots.txt) and their drill-down URL patterns; robots.txt report.
- Check every host the flow touches (www, get., landing-page subdomains): each needs the tag, the consent banner and the success push.

Count every check you run as pass / warn / fail per area; that is the header picture. Keep evidence as you go: a screenshot path, a console line, a network URL, a DOM fact with numbers.

## 2. Write findings

For each problem write a finding with:
- title (what is broken, specific), area, type `bug` (something is wrong) or `gap` (coverage or process missing: area not checked, no monitoring, no test);
- severity: blocker / critical / major / minor / trivial (scale in `references/areas.md`);
- **observed** (seen: screenshot, log, DOM) or **hypothesis** (likely but not proven). A hypothesis is never blocker or critical;
- steps to reproduce (≥ 2), expected, actual, environment, evidence;
- how to fix (concrete steps naming the real tools: the plugin, the setting, the selector), effort, risk;
- the automated test id that will catch it.

Known issues from the brief: confirm or rule out each with your own evidence. A fixed one goes into the post-deploy checklist as passed, with a note, and gets a regression test.

## 3. Prioritize

Sort by severity first, then ICE (Impact, Confidence, Ease, each 1-10). Be honest: low confidence for anything not reproduced. For the top 3, add: 2 fix options considered (`alt`), a "done when" threshold (`thr`) and a pre-mortem (`pm`: "it is next week and the fix did not work - why?").

Set the release verdict: 0 blocks release, 1 fix before next deploy, 2 fix in backlog, 3 ready.

## 4. Write the tests

Read `references/test-suite.md`. Add a `suite` to `audit.json`: `baseURL`, `delayMs` (≥ 1000), and one check per bug plus regression checks for what works now (GA4 tag, key redirects, form fields). The bundled runner is generic; you only write data. Never write a check that submits. List the tests in `tests` with what each checks and its status now (`pass` / `fail` from your manual checks, `new` if you could not try it) and say in the report whether the suite was actually run.

## 5. Output: report for people + hand-off for agents + tests

Read `references/report-spec.md` and `references/handoff-spec.md`. Write `audit.json` following `references/audit.schema.json` (start from `assets/example-audit.en.json`). You write data only; the template draws the charts and computes the health index, totals, ICE, quick fixes and confidence.

For the hand-off, give every bug `where` (url / selector / file / template / plugin / setting / tool) and in `detail`: `owner` (`code` the agent can change it in the repo, `admin` needs an admin UI, `decision` needs the owner's answer) and, when you can, `code` (the exact snippet, rule or config) with `codeLang`. Add top-level `stack` (what you detected, saying when it is inferred).

- **With a shell:** `python scripts/build_report.py audit.json out/index.html`. It validates first (refuses on errors: an observed bug without evidence, a missing evidence file, a top-3 bug without fix options or pre-mortem, a KPI number with no source, a test that would submit), copies the screenshots next to the page, and writes `out/qa-tests/` and `out/qa-handoff.md`. Fix the data, not the template.
- **Without a shell:** copy `assets/report-template.html`, set `<html lang>` and `<title>`, replace the JSON block's content (write `<\/` for `</` in strings), put screenshots in `shots/` beside it, and copy `assets/qa-tests/` with your `qa-suite.json`.

Deliver: publish `out/` (index.html + shots/) as one artifact when an artifact tool exists, private unless the user says otherwise; send `qa-handoff.md` as a file (it is meant to be pasted or attached to a coding agent) and the `qa-tests/` folder (or a ZIP of it). In chat: 3-5 bullets (verdict, top bugs, what was not checked), the link, "give `qa-handoff.md` to your coding agent", and how to run the tests.

## 6. Check before delivering

1. **Facts.** Every number in the text and KPIs traces to a source or a check you ran; counts in the header match the area counts; arithmetic holds. In Claude Code, hand this to a subagent that has not seen your reasoning: give it `audit.json` and the raw material and ask for every number it cannot trace.
2. **Render:** `python scripts/check_report.py out/index.html --out ./report-check` (needs `pip install playwright` and a Chromium). It fails on page errors, sideways scroll, empty charts, overflowing labels, tooltips that do not open on hover or tap, broken phone table cells, filters that break the table, evidence images that do not load. Look at the screenshots, including dark mode.
3. **Hand-off reads standalone:** open `qa-handoff.md` and check that an agent who never saw the report could act on each task: location, steps, fix, done-when, owner.
4. **Tests parse:** `node --check out/qa-tests/qa.spec.js`; if the shell can reach the site, run the suite and update `tests[].st` with the real results.
5. Fix and re-check, at most twice; say plainly what is still unverified.

## Rules
- Every finding points to evidence or is labelled a hypothesis.
- No invented numbers: unknown counts stay null and show as "not checked".
- QA only: do not drift into growth or positioning advice; point to product-lens-audit if the user wants that.
- Prefer one precise bug with steps over five vague ones.
- When a fix changes visible copy, give the corrected text (or ask the owner for it if it states a business fact you do not know: prices, guarantees, insurance terms).
- Design for repeat runs: keep ids stable (`T01`...), save `audit.json` and `qa-suite.json`; the next run compares against them.
