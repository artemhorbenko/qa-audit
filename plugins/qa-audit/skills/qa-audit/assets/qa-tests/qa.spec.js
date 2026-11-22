// qa-audit: deterministic post-deploy checks, driven by qa-suite.json.
// Never submits forms, payments or messages: form checks read fields and
// fire a synthetic "sent" DOM event to see whether analytics reacts.
const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

const suite = JSON.parse(fs.readFileSync(path.join(__dirname, 'qa-suite.json'), 'utf8'));
const DELAY = suite.delayMs ?? 1500;
const VIEWPORTS = { phone: [390, 844], tablet: [820, 1180], desktop: [1280, 900], ...(suite.viewports || {}) };
const IGNORE = (suite.ignoreUrls || []).concat(['/cdn-cgi/l/email-protection']);
const sleep = ms => new Promise(r => setTimeout(r, ms));
const only = (process.env.QA_ONLY || '').split(',').filter(Boolean);

// Records GA4 hits and dataLayer pushes; stops tel:/mailto: from leaving the page.
const SPY = () => {
  window.__qa = { pushes: [] };
  const hook = dl => {
    if (!dl || dl.__qaHooked) return dl;
    const orig = dl.push.bind(dl);
    dl.push = (...a) => { a.forEach(x => window.__qa.pushes.push(x)); return orig(...a); };
    dl.__qaHooked = true;
    return dl;
  };
  let dl = hook(window.dataLayer || []);
  try {
    Object.defineProperty(window, 'dataLayer', { configurable: true, get: () => dl, set: v => { dl = hook(v); } });
  } catch (e) { /* page defined it first */ }
  addEventListener('click', e => { if (e.target.closest && e.target.closest('a[href^="tel:"],a[href^="mailto:"]')) e.preventDefault(); }, true);
};

async function open(page, url) {
  await sleep(DELAY);
  const resp = await page.goto(url, { waitUntil: 'load', timeout: 45000 });
  const status = resp ? resp.status() : 0;
  const blocked = status === 429 || status === 503 ||
    await page.locator('input[name=response], iframe[src*="captcha"], #challenge-form').count() > 0;
  test.skip(blocked, `The host blocked the test runner (status ${status} or a captcha). Not checked: slow down (delayMs) or allowlist the runner IP. Never solve the captcha automatically.`);
  return resp;
}

function eventsSeen(pushes, hits) {
  const names = new Set();
  for (const p of pushes) {
    if (p && typeof p === 'object') {
      if (p.event) names.add(String(p.event));
      if (p[0] === 'event' && p[1]) names.add(String(p[1]));
    }
  }
  for (const u of hits) { const m = u.match(/[?&]en=([^&]+)/); if (m) names.add(decodeURIComponent(m[1])); }
  return names;
}

const RUN = {
  async status(page, c) {
    const r = await open(page, c.url);
    expect(r.status(), `${c.url} status`).toBe(c.expect ?? 200);
  },

  async redirect(page, c) {
    await open(page, c.from);
    const got = new URL(page.url());
    const want = new URL(c.to, suite.baseURL);
    expect(got.pathname, `${c.from} should end at ${c.to}`).toBe(want.pathname);
  },

  async ga4_tag(page, c) {
    const hits = [];
    page.on('request', r => { if (/google-analytics\.com\/g\/collect|\/g\/collect\?/.test(r.url())) hits.push(r.url()); });
    await open(page, c.url);
    await page.waitForTimeout(2500);
    const tag = await page.evaluate(id => [...document.scripts].some(s => (s.src || '').includes(id) || s.textContent.includes(id)), c.measurementId);
    expect(tag, `gtag with ${c.measurementId} on the page`).toBeTruthy();
    expect(hits.some(u => u.includes(`tid=${c.measurementId}`)), `a GA4 hit with tid=${c.measurementId}`).toBeTruthy();
  },

  async click_event(page, c) {
    const hits = [];
    page.on('request', r => { if (/\/g\/collect/.test(r.url())) hits.push(r.url()); });
    await page.addInitScript(SPY);
    await open(page, c.url);
    const el = page.locator(c.selector).filter({ visible: true }).first();
    await expect(el, `${c.selector} exists`).toHaveCount(1);
    await el.scrollIntoViewIfNeeded();
    await el.click({ noWaitAfter: true });
    await page.waitForTimeout(2500);
    const seen = eventsSeen(await page.evaluate(() => window.__qa.pushes.map(x => JSON.parse(JSON.stringify(x)))), hits);
    expect([...seen], `GA4 event "${c.event}" after clicking ${c.selector}`).toContain(c.event);
  },

  async form_event(page, c) {
    const hits = [];
    page.on('request', r => { if (/\/g\/collect/.test(r.url())) hits.push(r.url()); });
    await page.addInitScript(SPY);
    await open(page, c.url);
    const ok = await page.evaluate(({ form, domEvent }) => {
      const f = document.querySelector(form);
      if (!f) return false;
      f.dispatchEvent(new CustomEvent(domEvent, { bubbles: true, detail: { status: 'mail_sent', qaSynthetic: true } }));
      return true;
    }, { form: c.form, domEvent: c.domEvent || 'wpcf7mailsent' });
    expect(ok, `form ${c.form} exists`).toBeTruthy();
    await page.waitForTimeout(2500);
    const seen = eventsSeen(await page.evaluate(() => window.__qa.pushes.map(x => JSON.parse(JSON.stringify(x)))), hits);
    expect([...seen], `GA4 event "${c.event}" after ${c.domEvent || 'wpcf7mailsent'} (no real submit)`).toContain(c.event);
  },

  async form_fields(page, c) {
    await open(page, c.url);
    const form = page.locator(c.form).first();
    await expect(form, `form ${c.form}`).toHaveCount(1);
    for (const name of c.required || []) {
      const f = form.locator(`[name="${name}"]`).first();
      await expect(f, `field ${name}`).toHaveCount(1);
      const req = await f.evaluate(e => e.required || e.getAttribute('aria-required') === 'true');
      expect(req, `field ${name} is required`).toBeTruthy();
    }
    for (const [name, type] of Object.entries(c.types || {})) {
      expect(await form.locator(`[name="${name}"]`).first().getAttribute('type'), `field ${name} type`).toBe(type);
    }
  },

  async text(page, c) {
    await open(page, c.url);
    const items = await page.locator(c.selector).evaluateAll((els, f) => els.filter(e => !f || e.innerText.includes(f)).map(e => e.innerText.replace(f || '', '').replace(/\s+/g, ' ').trim()), c.filter || '');
    expect(items.length, `${c.selector}${c.filter ? ` with "${c.filter}"` : ''} found`).toBeGreaterThan(0);
    const re = c.pattern ? new RegExp(c.pattern, c.flags || 'i') : null;
    for (const t of items) {
      if (re) expect(t, `text should match /${c.pattern}/`).toMatch(re);
      else expect(t).toContain(c.text);
    }
  },

  async no_text(page, c) {
    await open(page, c.url);
    const body = await page.locator(c.selector || 'body').first().innerText();
    if (c.pattern) expect(body).not.toMatch(new RegExp(c.pattern, c.flags || 'i'));
    else expect(body).not.toContain(c.text);
  },

  async ui_language(page, c) {
    await open(page, c.url);
    const bad = await page.locator(c.selector).evaluateAll((els, forbid) => {
      const re = new RegExp(forbid);
      return [...new Set(els.filter(e => e.offsetParent && re.test((e.value || e.innerText || '').trim())).map(e => (e.value || e.innerText).trim().replace(/\s+/g, ' ').slice(0, 60)))];
    }, c.forbid);
    expect(bad, `UI text in the wrong language on ${c.url}`).toEqual([]);
  },

  async console_clean(page, c) {
    const errors = [];
    page.on('pageerror', e => errors.push(`pageerror: ${e.message}`));
    page.on('console', m => { if (m.type() === 'error' && !/chrome-extension:\/\//.test(m.location().url || '')) errors.push(`console: ${m.text()}`); });
    page.on('response', r => { if (r.status() >= 400 && !IGNORE.some(i => r.url().includes(i))) errors.push(`${r.status()} ${r.url()}`); });
    await open(page, c.url);
    await page.waitForTimeout(2000);
    const allow = (c.allow || []).map(a => new RegExp(a));
    expect(errors.filter(e => !allow.some(r => r.test(e))), `errors on ${c.url}`).toEqual([]);
  },

  async no_h_scroll(page, c) {
    for (const v of c.viewports || ['phone', 'tablet']) {
      const [w, h] = VIEWPORTS[v];
      await page.setViewportSize({ width: w, height: h });
      await open(page, c.url);
      const sw = await page.evaluate(() => document.documentElement.scrollWidth);
      await page.screenshot({ path: test.info().outputPath(`${c.id}-${v}.png`) });
      expect(sw, `${c.url} at ${v} ${w}px: page width`).toBeLessThanOrEqual(w + 1);
    }
  },

  async page_links(page, c, request) {
    await open(page, c.url);
    const origin = new URL(suite.baseURL).origin;
    let links = await page.$$eval('a[href]', as => as.map(a => a.href.split('#')[0]));
    links = [...new Set(links)].filter(h => h.startsWith('http') && (c.external || h.startsWith(origin)) && !IGNORE.some(i => h.includes(i))).slice(0, c.max || 60);
    const bad = [];
    for (const h of links) {
      await sleep(DELAY);
      const r = await request.get(h, { maxRedirects: 5, failOnStatusCode: false, timeout: 30000 }).catch(e => ({ status: () => 0, e }));
      if (r.status() === 429 || r.status() === 503) test.skip(true, 'The host started rate limiting the link check: raise delayMs.');
      if (r.status() >= 400 || r.status() === 0) bad.push(`${r.status()} ${h}`);
    }
    expect(bad, `broken links on ${c.url}`).toEqual([]);
  },

  async sitemap(page, c, request) {
    const seen = new Set(), urls = [];
    const walk = async u => {
      if (seen.has(u) || urls.length >= (c.max || 40)) return;
      seen.add(u);
      await sleep(DELAY);
      const x = await (await request.get(new URL(u, suite.baseURL).href)).text();
      const locs = [...x.matchAll(/<loc>(.*?)<\/loc>/g)].map(m => m[1].trim());
      if (/<sitemapindex/.test(x)) { for (const l of locs) await walk(l); } else urls.push(...locs);
    };
    await walk(c.url || '/sitemap.xml');
    const bad = [];
    for (const u of urls.slice(0, c.max || 40)) {
      await sleep(DELAY);
      const r = await request.get(u, { maxRedirects: 0, failOnStatusCode: false, timeout: 30000 });
      if (r.status() === 429 || r.status() === 503) test.skip(true, 'The host started rate limiting the sitemap check: raise delayMs.');
      if (r.status() !== 200) bad.push(`${r.status()} ${u}${r.headers().location ? ' → ' + r.headers().location : ''}`);
    }
    expect(urls.length, 'sitemap has URLs').toBeGreaterThan(0);
    expect(bad, 'every sitemap URL answers 200 without a redirect').toEqual([]);
  },

  async axe(page, c) {
    let AxeBuilder;
    try { AxeBuilder = require('@axe-core/playwright').default; } catch (e) { test.skip(true, 'npm i -D @axe-core/playwright to run accessibility checks'); }
    await open(page, c.url);
    const r = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze();
    const bad = r.violations.filter(v => (c.impact || ['serious', 'critical']).includes(v.impact)).map(v => `${v.impact} ${v.id}: ${v.nodes.length} element(s)`);
    expect(bad, `axe violations on ${c.url}`).toEqual([]);
  },

  async meta(page, c) {
    await open(page, c.url);
    if (c.description) expect((await page.locator('meta[name=description]').getAttribute('content').catch(() => '')) || '', 'meta description').not.toBe('');
    if (c.title) expect(await page.title()).not.toBe('');
    for (const l of c.hreflang || []) expect(await page.locator(`link[rel=alternate][hreflang="${l}"]`).count(), `hreflang ${l}`).toBeGreaterThan(0);
    if (c.lang) expect(await page.locator('html').getAttribute('lang')).toMatch(new RegExp('^' + c.lang));
  },
};

for (const c of suite.checks) {
  if (only.length && !only.includes(c.id)) continue;
  const name = `${c.id} ${c.type}${c.title ? ' - ' + c.title : ''}`;
  if (c.skip) { test.skip(name, () => {}); continue; }
  test(name, async ({ page, request }) => {
    test.setTimeout((c.timeoutS || 120) * 1000);
    await RUN[c.type](page, c, request);
  });
}
