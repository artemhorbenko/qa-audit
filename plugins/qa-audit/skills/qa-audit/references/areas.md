# The 11 QA areas

Each area is scored 0-100 and counted as checks passed / warnings / failed. Ids (`i`) and groups (`g`) are fixed: the template has an icon per id.

| Group (`g`) | Area | `i` | What to check |
|---|---|---|---|
| works | Key user flows | `flows` | Home → service/product → CTA → form or cart → "sent" state; every CTA target exists (anchors like `#quote`, pages); search, filters, tracking pages; login only with a test account the owner gave. |
| works | Forms and validation | `forms` | Required fields and their markers, input types (`tel`, `email`), `autocomplete`, labels, error messages on empty/invalid input (client side only), duplicate or legacy forms, locale of the form plugin (CF7 `_wpcf7_locale`), recipient (from the CMS, read-only). **Stop before submit.** |
| works | Links and redirects | `links` | Internal links from key pages and the sitemap, old URLs → new URLs (301, one hop), language redirects, 404 page. Polite crawl only (see data-sources.md). Ignore `/cdn-cgi/l/email-protection` (Cloudflare decodes it at runtime). |
| looks | Copy and translation | `copy` | Text that belongs to another block (copy-paste errors in cards), placeholders, lorem ipsum, wrong language in buttons/menus/form labels per language version, `<html lang>` per version, empty pages, missing titles and meta descriptions. |
| looks | Mobile and tablet | `mobile` | 390 px and 820 px: no sideways scroll, menu opens, CTA visible, form usable, tap targets ≥ 24 px, no overlapping fixed bars. |
| looks | Cross-browser | `browsers` | Chromium + Firefox + WebKit (Safari) at least for the key flow. If only one engine was available, set `s: null`. |
| health | Console and network | `errors` | JS errors, failed requests (≥ 400), mixed content, blocked third parties, on every key page. Ignore errors from `chrome-extension://` (the tester's own browser extensions). |
| health | Performance | `perf` | PageSpeed mobile + desktop: score, LCP, CLS, INP/TBT; field data (CrUX) if present; heavy hero images, render-blocking files. Lab numbers vary: report the run date and repeat for decisions. |
| health | Accessibility | `a11y` | axe or Lighthouse a11y: contrast, labels, alt, names of buttons and links, focus order, keyboard access to the menu and form. |
| measure | Analytics and events | `analytics` | Tag present on every template (GA4 id, GTM container), hits sent, consent mode if a banner exists, key events: form sent (`wpcf7mailsent` etc. → `generate_lead`), tel:/mailto: clicks, purchases; no double counting. |
| measure | Post-deploy checklist | `deploy` | The short list in the report: tag, events, redirects, forms, texts, languages, sitemap (+ console, speed). Its counts are the checklist's pass/warn/fail. |

## Counting checks

A check is one concrete question with a yes/no answer on one page or element ("GA4 hit sent on /", "phone field is type tel", "insurance card text is about insurance (UA)"). Count each once. Partial checks (crawl stopped, one viewport only) are `warn`. An area with no checks at all gets `s: null` and no counts.

## Scoring 0-100

Start at 100 and subtract per finding in the area: blocker 60, critical 40, major 20, minor 8, trivial 3; subtract 10 for each `warn` that hides real uncertainty (partial crawl). Floor at 5. For `flows`, also subtract half the points of any finding in another area that breaks a key flow (a form unusable on phones, a lead not sent). Two caps: `perf` is never higher than the PageSpeed mobile score, and `deploy` never higher than the share of checklist items passed (× 100). It is a judgment aid, so keep it consistent: below 40 = broken where it matters, 40-70 = works with real defects, above 70 = solid.

## Severity scale

| Severity | Meaning | Example |
|---|---|---|
| blocker | A key flow is impossible or the site is down for a group of users | quote form returns an error; checkout 500 |
| critical | The flow works but the business cannot see or trust the result; data loss; security | leads not tracked after a redesign; form sends to a dead mailbox |
| major | Visible defect on a key page, wrong content, broken language version, big performance problem | card shows another service's text; RU pages in Ukrainian; LCP 10 s |
| minor | Small defect or hygiene issue, workaround obvious | missing meta descriptions; legacy duplicate form |
| trivial | Cosmetic | 2 px misalignment; footer tap targets slightly small |

A `hyp` finding is at most `major`.

## Evidence kinds (`evid[].k`)

`shot` (screenshot file in `shots/`), `log` (a note of what you ran and saw), `console` (console line), `network` (request URL + status), `dom` (a DOM fact with numbers), `psi` (PageSpeed result), `axe` (axe violation). Observed findings need at least one.
