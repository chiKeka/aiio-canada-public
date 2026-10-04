import assert from 'node:assert/strict';
import { chromium } from 'playwright-core';
import AxeBuilder from '@axe-core/playwright';
import fs from 'node:fs/promises';
const base = process.env.AIIO_BASE_URL ?? 'http://127.0.0.1:3013';
const browser = await chromium.launch({
  executablePath:
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  headless: true,
});
const errors = [];
const context = await browser.newContext();
const page = await context.newPage();
page.on('pageerror', (e) => errors.push(e.message));
await fs.mkdir('output/review-qa', { recursive: true });
try {
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 950 });
    for (const route of [
      '/',
      '/project-scenario',
      '/historical-analog',
      '/pressure',
      '/methods#planning-gates',
      '/downloads',
    ]) {
      await page.goto(base + route, { waitUntil: 'networkidle' });
      assert.ok(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth + 1,
        ),
        `${route} overflows at ${width}`,
      );
      if (route === '/project-scenario') {
        await page
          .getByRole('heading', { name: 'What this scenario says' })
          .waitFor();
        assert.equal(
          await page
            .getByRole('button', { name: 'Guided story', exact: true })
            .getAttribute('aria-current'),
          'page',
        );
        assert.ok(
          (await page.locator('body').innerText()).includes(
            'not a confidence interval',
          ) === false,
        ); // Details stay collapsed.
      }
      if (route === '/methods#planning-gates')
        assert.equal(await page.locator('#planning-gates article').count(), 7);
      if (route === '/pressure') {
        const panel = page
          .locator('section')
          .filter({
            has: page.getByRole('heading', {
              name: 'Shared material-cost signals',
              exact: true,
            }),
          });
        const labels = await panel.locator('article').allInnerTexts();
        const edmontonSteel = labels.filter(
          (v) =>
            v.toLowerCase().includes('edmonton') &&
            v.toLowerCase().includes('structural steel'),
        );
        assert.equal(edmontonSteel.length, 1);
      }
      if (
        route === '/historical-analog' ||
        route === '/project-scenario' ||
        route === '/'
      ) {
        await page.screenshot({
          path: `output/review-qa/${route === '/' ? 'home' : route.slice(1)}-${width}.png`,
          fullPage: false,
        });
        const axe = await new AxeBuilder({ page })
          .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
          .analyze();
        const severe = axe.violations.filter((v) =>
          ['serious', 'critical'].includes(v.impact),
        );
        assert.equal(
          severe.length,
          0,
          JSON.stringify(
            severe.map((v) => ({
              id: v.id,
              nodes: v.nodes.map((n) => n.target),
            })),
          ),
        );
      }
    }
  }
  const health = await (await page.request.get(base + '/api/health')).json();
  assert.ok(
    !/CLI|context window|authenticated session/.test(JSON.stringify(health)),
  );
  assert.ok(
    Object.values(health.governance.independent_review).every(
      (v) => v.status === 'blocked',
    ),
  );
  const json = await page.request.get(base + '/data/alberta-boom-analog.json');
  assert.equal(json.status(), 200);
  assert.equal((await json.json()).observations.length, 4);
  for (const file of [
    'Alberta_ADM_Decision_Briefing_Risk_Review',
    'Alberta_ADM_Evidence_Appendix_Risk_Review',
  ])
    assert.equal(
      (await page.request.get(base + '/downloads/' + file + '.pptx')).status(),
      200,
    );
  assert.deepEqual(errors, []);
  console.log(
    'PASS: desktop/mobile entry, guided default, gates, deduplicated series, analog, public governance, downloads, accessibility and console',
  );
} finally {
  await browser.close();
}
