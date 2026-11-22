# Tools and data sources

Check what this session can reach before testing: search the tool list (ToolSearch or similar). Never assume a connector exists; never fill a gap with invented results. Everything read-only.

## Status

| Status | When |
|---|---|
| `ok` | Used for real in this run. |
| `demo` | Partial: crawl stopped by the host's rate limit, one viewport only, a sample. |
| `no` | Not available; or fails twice (try once more, then move on); or blocked (captcha). |

Confidence = average of ok 1, demo 0.6, no 0.

## Browser (the main tool)

- **Claude in Chrome** (the user's Chrome, signed in), the built-in browser, or a cloud browser. Read the DOM with JavaScript, read console messages and network requests, take screenshots with `save_to_disk` and copy them into `shots/`.
- **Analytics recipe:** before the action, wrap `window.dataLayer.push` to record pushes and add a capture-phase click listener that calls `preventDefault()` on `tel:`/`mailto:` links; then click or dispatch the form's "sent" event; wait 1.5 s; read the recorded pushes and `performance.getEntriesByType('resource')` for `/g/collect?…&en=<event>`.
- **Language recipe:** fetch each language's sitemap and pages, compare `<html lang>`, the final URL (redirected?), and visible menu/button text against the expected alphabet (e.g. Ukrainian-only letters `[іїєґ]` on a RU page).
- **Viewport limits:** a real Chrome window often cannot be narrower than ~600 px; an iframe of the same site at 390 px works only if the host does not challenge it. Prefer headless Playwright for phone widths.

## Headless Playwright (shell)

`pip install playwright` / `npm i -D @playwright/test`; a system Chrome can be used with `QA_CHROME=/path`. Many sandboxes cannot reach arbitrary sites: try one request; if the proxy refuses, mark it `no` and give the user the suite to run locally.

## PageSpeed Insights

pagespeed.web.dev in the browser (wait ~30 s for the result), or the API `https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=…&strategy=mobile` when the shell can reach it. Record the date, mobile/desktop, lab vs field (CrUX "No data" is common on small sites), score, FCP, LCP, TBT, CLS, the top opportunities. Screenshot the score block as evidence.

## CMS connector (WordPress and others)

Read-only: active plugins (forms: Contact Form 7, WPForms, Fluent Forms, Elementor forms; analytics: Site Kit, MonsterInsights, GTM4WP, WPCode snippets; language: Polylang, WPML; cache; SEO: Yoast, AIOSEO, Rank Math), form settings (recipient, messages), menus per language, redirects plugin, PHP error log. A connector for another site is not this site's connector: check the domain.

## GA4 and Search Console

If connected (or the user's browser is signed in and they agree), read: key events list, DebugView/realtime for a test action, Search Console crawl stats (429/5xx for Googlebot), sitemap status. Otherwise mark `no` and test the page side only.

## Politeness (hosts block fast crawlers)

- One request at a time, ≥ 1 s apart (the generated tests default to 1.5 s), ≤ 60 pages per run.
- Shared hosts (e.g. adm.tools / ukraine.com.ua, Cloudflare "Under attack") answer bursts with 429, 503 or a captcha page ("Захищена сторінка", "Checking your browser"). When that happens: stop, wait, record the area as partial (`demo`), and do **not** report the 429/503 you caused as broken links. Never solve the captcha.
- A host that blocks bursts may also block uptime monitors or CI; that is worth a `gap` finding (with Search Console crawl stats as the way to check Googlebot), labelled hypothesis unless you have the stats.
