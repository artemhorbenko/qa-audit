# Report specification

One self-contained HTML page plus a `shots/` folder. `assets/report-template.html` renders everything from one `<script type="application/json" id="audit">` block; you write only that JSON (`audit.schema.json`, example `assets/example-audit.en.json`). The look and code are shared with product-lens-audit, so the two reports read as one family.

## Look

Annual-report style: white ground, black ink, one vermilion accent (#ff4a1c) for failures, critical bugs and the top 3 fixes; amber for warnings; hatching for "not checked". Dark theme on #120d0b (follows `prefers-color-scheme` and a `data-theme` attribute). Sofia Sans Condensed 800 for titles and figures, Sofia Sans for text (Latin + Cyrillic). Stroke SVG icons per area, no emoji. Works at 360 px: tables become stacked cards, the flow route turns vertical. Every derived number (health index, totals, ICE, quick fixes, confidence, % passed) is computed by the template.

Headings state their point ("Leads are not tracked"), not a topic ("Analytics").

## Sections, in order

1. **Header** - label (how it was tested), headline = the main finding, target line (URL, environment, deploy, date), lead, 4 KPIs, then **checks passed vs failed by area**: one stacked bar per area (black passed, amber warnings, vermilion failed; hatched "not checked") with % passed. Under it the **release verdict** strip (blocks release / fix before next deploy / fix in backlog / ready) with one sentence.
2. **Areas** - radar of the 11 area scores beside the grouped list (works, looks right, technically healthy, measured). Not-checked areas show "—" and are left out of the index.
3. **Flows** - 6-8 stops of the key user flows: where, step, one-line result, status ok / friction / broken.
4. **Matrix** - impact vs effort; filled dots = bugs, outlined = gaps, vermilion = top 3.
5. **Bugs table** - sorted by severity, then ICE; filters: all / blockers and critical / bugs / gaps; columns #, title + observed/hypothesis badge, area, severity, I, C, E, ICE.
6. **Top 3 fixes** - cards: what is broken, done when, how to verify.
7. **All bugs** - one collapsible row each (top 3 open): steps to reproduce, expected, actual, environment, evidence (screenshot thumbnails that open full size, log lines), how to fix, automated test, effort, risk; top 3 also fix options, done-when threshold, pre-mortem.
8. **Post-deploy checklist** - a strip of squares and the list: GA4 tag, key events, redirects, forms, texts and cards, language versions, sitemap and hreflang, console, speed. Each pass / warn / fail / not checked with a note.
9. **Tests** - table of the generated checks (id, what it checks, area, status now) and the command to run them.
10. **Data and confidence** - sources with statuses, confidence meter, start questions and answers, glossary, "how this report was made".

## Data shapes (the parts that are easy to get wrong)

- `lang` `uk` or `en` picks the interface labels (`UI` in the template; add a language with the same keys).
- `text`: `label`, `headline`, `lead`, `areasNote`, `…H` / `…P` for `areas`, `flows`, `matrix`, `bugs`, `next`, `plan`, `check`, `tests`, `data`; `testsCmd` (shown as a code block), `how` (list), `footer`. Tokens: `{health} {checks} {passed} {failed} {warned} {crit} {qw} {n} {tests} {nc} {conf}`; `[[words]]` turns red. HTML is escaped.
- `target`: `{url, env, deploy, date}`.
- `kpis`: up to 4 `{v, l, hot?, src?}`; a literal number needs `src` = a source name.
- `verdict`: `{cur: 0-3, note}`.
- `areas`: 11 × `{k, n, i, g, s, pass, fail, warn, sub?}`; `s: null` and no counts = not checked.
- `route`: `{t, w, st: ok|warn|bad, p}`.
- `bugs`: `{t, l, ln, x: bug|gap, sev, ev: obs|hyp, I, C, E}`; ids are 1-based positions; `detail` and `plans` keyed by id string.
- `detail[id]`: `{steps[], exp, act, env, evid[{k, src?, t?}], fix[], test, effort, risk, alt?, thr?, pm?}`. `src` is a relative path (`shots/01-name.jpg`).
- `plans[id]` for the top 3: `{h: what is broken, m: done when, t: how to verify}`.
- `checklist`: `{t, st: pass|warn|fail|nc, note}`; `tests`: `{id, t, area, st: pass|fail|new|nc}`; `suite`: see test-suite.md.
- `answers`: `{q, a, skipped?}`; `sources`: `{name, note, status}`; `glossary`: `{term: {g, d}}`.

## Tooltips, phone tables, robustness

Same as product-lens-audit: every term in `glossary` becomes a dotted button (hover on desktop, tap on touch, a second tap closes, Escape closes); stacked table cells are wrapped in one `.cv`; charts use ResizeObserver; all script sits in one block wrapped in `{ }`. Do not depend on localStorage.
