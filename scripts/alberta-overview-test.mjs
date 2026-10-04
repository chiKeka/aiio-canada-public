import assert from 'node:assert/strict';
import fs from 'node:fs';
import { chromium } from 'playwright-core';
import AxeBuilder from '@axe-core/playwright';
const evidence = JSON.parse(
  fs.readFileSync('public/data/construction/briefing.json', 'utf8'),
);
import { baseUrl, browserOptions } from './browser-config.mjs';
const browser = await chromium.launch(browserOptions());
try {
  const context = await browser.newContext();
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto(`${baseUrl}/construction`);
  const overview = page.getByTestId('alberta-overview');
  await overview.waitFor();
  assert.equal(
    await page
      .getByRole('button', { name: 'Alberta overview', exact: true })
      .getAttribute('aria-pressed'),
    'true',
  );
  for (const v of [
    '$49.01B',
    '$10.687B',
    '48,800',
    '43,500',
    '43,700',
    '5,300',
    '541',
    '166',
  ])
    assert.ok((await overview.innerText()).includes(v), v);
  const prices = page.getByRole('table', {
    name: 'Calgary and Edmonton year-over-year construction price changes',
    exact: true,
  });
  for (const row of evidence.prices)
    assert.ok(
      (await prices.innerText()).includes(
        `${row.year_over_year_percent_change.toFixed(2)}%`,
      ),
    );
  const labour = page.getByRole('table', {
    name: 'Alberta trade employment and vacancies',
    exact: true,
  });
  assert.equal(await labour.getByRole('row').count(), 7);
  assert.ok((await labour.innerText()).includes('Not published'));
  const procurement = page.getByRole('table', {
    name: 'Published equipment procurement lead-time ranges',
    exact: true,
  });
  assert.equal(await procurement.getByRole('row').count(), 9);
  for (const rows of [
    evidence.guidance.packages.rows,
    evidence.guidance.pathways.rows,
    evidence.guidance.mitigations.rows,
  ])
    for (const row of rows)
      for (const cell of row)
        assert.ok((await overview.innerText()).includes(cell), cell);
  await page
    .getByText('Full project register · 19 records', { exact: true })
    .click();
  assert.equal(
    await page
      .getByRole('table', {
        name: 'Full Alberta data-centre register',
        exact: true,
      })
      .getByRole('row')
      .count(),
    20,
  );
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 1000 });
    assert.ok(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
      `overflow at ${width}`,
    );
    const axe = await new AxeBuilder({ page })
      .include('[data-testid="alberta-overview"]')
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
      .analyze();
    assert.deepEqual(
      axe.violations.map((v) => ({
        id: v.id,
        impact: v.impact,
        nodes: v.nodes.length,
      })),
      [],
    );
    await page.screenshot({
      path: `/tmp/alberta-overview-${width}.png`,
      fullPage: true,
    });
  }
  await page.getByRole('button', { name: 'Demand model', exact: true }).click();
  assert.equal(await overview.count(), 0);
  await page
    .getByRole('button', { name: 'Alberta overview', exact: true })
    .click();
  await overview.waitFor();
  assert.ok((await overview.innerText()).includes('$49.01B'));
  assert.deepEqual(errors, []);
  console.log(
    'Passed: PPT metrics, all eight prices, complete inventory, shared analytical tables, desktop/mobile accessibility and scenario-tab isolation.',
  );
} finally {
  await browser.close();
}
