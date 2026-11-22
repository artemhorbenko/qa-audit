// qa-audit post-deploy tests. Run: npm install && npx playwright install chromium && npx playwright test
// Installed Chrome instead of a download: QA_CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" npx playwright test
// Cross-browser: BROWSERS=all npx playwright test   (adds Firefox and WebKit/Safari)
const { defineConfig, devices } = require('@playwright/test');
const suite = require('./qa-suite.json');

const projects = [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }];
if (process.env.BROWSERS === 'all') {
  projects.push({ name: 'firefox', use: { ...devices['Desktop Firefox'] } });
  projects.push({ name: 'webkit', use: { ...devices['Desktop Safari'] } });
}

module.exports = defineConfig({
  testDir: '.',
  testMatch: 'qa.spec.js',
  workers: 1,               // one request at a time: hosts block fast crawlers
  fullyParallel: false,
  retries: 1,
  timeout: 120000,
  reporter: [['list'], ['html', { open: 'never', outputFolder: 'qa-report' }]],
  use: {
    baseURL: suite.baseURL,
    locale: suite.locale || 'uk-UA',
    userAgent: suite.userAgent,
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    // QA_CHROME=/path/to/chrome uses an installed browser instead of 'npx playwright install'
    launchOptions: process.env.QA_CHROME ? { executablePath: process.env.QA_CHROME } : {},
  },
  projects,
});
