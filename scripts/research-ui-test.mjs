import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { chromium } from 'playwright-core';
import AxeBuilder from '@axe-core/playwright';

const baseUrl = process.env.AIIO_BASE_URL ?? 'http://127.0.0.1:3002';
const artifactDirectory = '/tmp/aiio-all-screens';
await mkdir(artifactDirectory, { recursive: true });
const browser = await chromium.launch({
  executablePath:
    process.env.CHROME_EXECUTABLE ??
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  headless: true,
});
const context = await browser.newContext({ reducedMotion: 'reduce' });
const page = await context.newPage();
page.setDefaultTimeout(10000);
const errors = [];
const report = [];
page.on('pageerror', (error) => errors.push(error.message));
page.on('console', (message) => {
  if (/Encountered two children|uncontrolled FieldControl/.test(message.text()))
    errors.push(message.text());
});
const routes = [
  ['/', 'Alberta delivery outlook'],
  ['/delivery', 'From evidence to delivery action'],
  ['/research', 'Research observatory'],
  ['/evidence', 'Evidence register'],
  ['/pressure', 'Market pressure'],
  ['/scenario', 'Scenario lab'],
  ['/methods', 'Methods & limitations'],
  ['/digest', 'Evidence digest'],
  ['/downloads', 'Downloads & releases'],
  ['/status', 'System status'],
  ['/not-a-real-aiio-route', 'That route does not exist.'],
];
try {
  for (const width of [1440, 1024, 390]) {
    await page.setViewportSize({ width, height: 1000 });
    for (const [route, title] of routes) {
      // Assert rendered content rather than waiting for unrelated background traffic.
      const response = await page.goto(`${baseUrl}${route}`, {
        waitUntil: 'load',
      });
      await page.evaluate(() => document.fonts.ready);
      assert.equal(
        response.status(),
        route.includes('not-a-real') ? 404 : 200,
        route,
      );
      assert.equal(
        await page
          .getByRole('heading', { level: 1, name: title, exact: true })
          .count(),
        1,
        route,
      );
      assert.equal(
        await page.getByRole('main').count(),
        1,
        `${route}: one main landmark`,
      );
      const overflow = await page.evaluate(() => ({
        viewport: innerWidth,
        content: document.documentElement.scrollWidth,
      }));
      const missingAnchors = await page
        .locator('nav[aria-label="On this page"] a')
        .evaluateAll((links) =>
          links
            .filter(
              (link) =>
                !document.getElementById(link.getAttribute('href').slice(1)),
            )
            .map((link) => link.textContent),
        );
      assert.deepEqual(missingAnchors, [], `${route}: section links`);
      const axe = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
        .analyze();
      report.push({
        route,
        width,
        overflow,
        violations: axe.violations.map((v) => ({
          id: v.id,
          impact: v.impact,
          nodes: v.nodes.map((n) => ({
            target: n.target,
            summary: n.failureSummary,
          })),
        })),
      });
      await page.screenshot({
        path: `${artifactDirectory}/${route.slice(1)}-${width}.png`,
      });
    }
  }
  await page.goto(`${baseUrl}/evidence`, { waitUntil: 'load' });
  await page
    .getByRole('textbox', { name: 'Search projects' })
    .fill('no-such-project-for-design-check');
  assert.equal(
    await page
      .getByRole('heading', { name: 'No projects match your filters' })
      .isVisible(),
    true,
  );
  await page
    .getByRole('button', { name: 'Clear filters', exact: true })
    .click();
  assert.equal(
    await page.getByRole('textbox', { name: 'Search projects' }).inputValue(),
    '',
  );
  await page
    .getByRole('button', { name: 'Core facilities', exact: true })
    .click();
  assert.equal(
    await page
      .getByRole('button', { name: 'Core facilities', exact: true })
      .getAttribute('aria-pressed'),
    'true',
  );
  await page.locator('#labour-geography').selectOption('PR_35');
  assert.match(
    await page.locator('#labour table caption').innerText(),
    /Ontario/,
  );
  await page
    .getByRole('combobox', { name: 'Regional macro jurisdiction' })
    .selectOption('PR_59');
  assert.equal(
    await page
      .getByRole('combobox', { name: 'Regional macro jurisdiction' })
      .inputValue(),
    'PR_59',
  );
  await page
    .getByRole('button', { name: 'Open site navigation', exact: true })
    .click();
  await page
    .getByRole('navigation', { name: 'Mobile primary navigation' })
    .getByRole('link', { name: 'Scenario lab', exact: true })
    .click();
  await page.waitForURL('**/scenario');
  assert.equal(
    await page
      .getByRole('heading', { level: 1, name: 'Scenario lab' })
      .isVisible(),
    true,
  );
  await page
    .locator('[aria-label="Alberta scenario variant"]')
    .getByRole('button', { name: /Front.loaded/ })
    .click();
  await page.getByRole('button', { name: /^high$/i }).click();
  await page
    .getByRole('button', { name: 'Share this view', exact: true })
    .click();
  const shared = page.url();
  assert.equal(new URL(shared).searchParams.get('variant'), 'front_loaded');
  assert.equal(new URL(shared).searchParams.get('power'), 'high');
  await page.goto(shared, { waitUntil: 'load' });
  assert.equal(
    await page
      .locator('[aria-label="Alberta scenario variant"]')
      .getByRole('button', { name: /Front.loaded/ })
      .getAttribute('aria-pressed'),
    'true',
  );
  assert.equal(
    await page
      .getByRole('button', { name: /^high$/i })
      .getAttribute('aria-pressed'),
    'true',
  );
  await page.goto(`${baseUrl}/research`, { waitUntil: 'load' });
  await page
    .getByRole('slider', {
      name: 'AI infrastructure investment in billions of dollars',
    })
    .fill('70');
  await page.getByRole('button', { name: '5 years', exact: true }).click();
  assert.equal(
    await page
      .getByRole('button', { name: '5 years', exact: true })
      .getAttribute('aria-pressed'),
    'true',
  );
  assert.match(await page.locator('#scenario').innerText(), /\$70B/);
  assert.deepEqual(errors, []);
} finally {
  await writeFile(
    `${artifactDirectory}/report.json`,
    JSON.stringify({ report, errors }, null, 2),
  );
  await context.close();
  await browser.close();
}
const failures = report.filter(
  (r) => r.overflow.content > r.overflow.viewport || r.violations.length > 0,
);
assert.deepEqual(
  failures,
  [],
  'Responsive layout and accessibility findings; see /tmp/aiio-all-screens/report.json',
);
console.log(
  'Research UI passed: all routes and 404 at desktop, tablet and mobile widths; accessibility, section links, search/empty/reset, classification, labour and macro selection, mobile navigation, scenario sharing/restore and sandbox controls.',
);
