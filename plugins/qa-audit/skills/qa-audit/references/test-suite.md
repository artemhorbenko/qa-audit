# The rerunnable test suite

`assets/qa-tests/qa.spec.js` is a generic Playwright runner. Each check is one object in `suite.checks`; `build_report.py` (or `make_tests.py`) writes them to `qa-tests/qa-suite.json` beside the runner, config, `package.json` and README. The user runs:

```
cd qa-tests && npm install && npx playwright install chromium
npx playwright test                  # after every deploy
BROWSERS=all npx playwright test     # + Firefox and WebKit
QA_ONLY=T04,T05 npx playwright test  # some checks
QA_CHROME=/path/to/chrome npx playwright test   # use an installed Chrome
```

## Suite fields

```json
{
 "baseURL": "https://example.com",
 "locale": "uk-UA",
 "delayMs": 1500,
 "ignoreUrls": ["/wp-json/"],
 "viewports": {"phone": [390, 844], "tablet": [820, 1180]},
 "checks": [ ... ]
}
```

Every check has `id` (stable: `T01`, `T02`, … - the report's `tests[].id` and `detail[].test` point to it), `type`, optional `title`, `skip`, `timeoutS`. Paths are relative to `baseURL`.

## Check types

| type | Fields | Passes when |
|---|---|---|
| `status` | `url`, `expect` (200) | the page answers with that status |
| `redirect` | `from`, `to` | opening `from` ends at path `to` |
| `ga4_tag` | `url`, `measurementId` | the gtag script with that id is on the page and a `/g/collect` hit with `tid=` that id is generated (and aborted). Consent-mode "basic" sites send nothing before consent: use `tag_present` |
| `tag_present` | `url`, `ids` ["GTM-…", "G-…"] | each id appears in a script src, inline script or loaded resource. `url` may be absolute to check another host |
| `click_event` | `url`, `selector`, `event` | clicking the first visible match (tel:/mailto: navigation is prevented) pushes `event` to dataLayer or sends a GA4 hit with `en=event` |
| `form_event` | `url`, `form`, `event`, and either `domEvent` (default `wpcf7mailsent`, a DOM event on the form) or `jqueryEvent` + `jqueryArgs` (Gravity Forms: `gform_confirmation_loaded`, `[4]`) | the synthetic success signal produces `event` in dataLayer or in a (blocked) GA4 hit. **No submit.** |
| `form_fields` | `url`, `form`, `required` [names], `types` {name: type} | each field exists, is required (`required` or `aria-required`), has the type |
| `text` | `url`, `selector`, `filter`, `pattern` or `text`, `flags` | every element whose text contains `filter` has, in the rest of its text, a match for `pattern` (catches copy-paste in cards) |
| `no_text` | `url`, `selector`, `pattern` or `text` | the text is not there |
| `ui_language` | `url`, `selector`, `forbid` (regex) | no visible element matching `selector` has text matching `forbid` (e.g. `[іїєґІЇЄҐ]` on a RU page) |
| `console_clean` | `url`, `allow` [regex] | no page errors, console errors or responses ≥ 400 while loading |
| `no_h_scroll` | `url`, `viewports` | page width ≤ viewport width at each viewport; saves screenshots |
| `page_links` | `url`, `max`, `external` | links found on the page (same origin unless `external`) answer < 400, checked one by one |
| `sitemap` | `url`, `max` | every URL in the sitemap (index followed) answers 200 without a redirect |
| `axe` | `url`, `impact` | no axe violations of those impacts (needs `@axe-core/playwright`, in package.json) |
| `robots_disallow` | `url` (/robots.txt), `agent`, `disallowed` [paths], `allowed` [paths] | robots.txt read as Google does (RFC 9309: the most specific user-agent group alone, longest rule wins) blocks / allows those paths for that agent |
| `meta` | `url`, `description`, `title`, `hreflang` [codes], `lang` | those head tags exist |

If the host answers 429/503 or shows a captcha, the check is **skipped** ("not checked"), not failed.

Every check aborts requests to analytics and ad endpoints (GA4 `/g/collect`, Google Ads, DoubleClick, Meta, LinkedIn, Bing, HubSpot tracking) and only records their URLs, so a synthetic event never reaches production data.

## What to cover

1. One check per bug, written so it **fails today** and passes after the fix (state `st: "fail"` in `tests`).
2. Regression checks for things that broke before or matter most: GA4 tag, key redirects, form fields, key pages' status, no console errors.
3. One `no_h_scroll` for phone and tablet, one `axe` on the key page, one `sitemap`, one `page_links` - slow but cheap insurance.
4. Keep it under ~25 checks and ~5 minutes; the point is that people actually run it after each deploy.

Never add a check that clicks a submit button, pays, signs up, or sends a message. `validate_audit.py` refuses checks with `"submit": true` or a `click` on a submit control.

## Fit for a WordPress QA service

The suite is data, so a service can store one `qa-suite.json` per site, run it after each deploy (CI, a cron, or a WP deploy hook), and keep the HTML report from `npx playwright show-report`. WordPress specifics live in the data (CF7 event names, Polylang paths, `wp-sitemap.xml`), not in the runner.
