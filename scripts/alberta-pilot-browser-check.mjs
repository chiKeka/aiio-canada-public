import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import AxeBuilder from '@axe-core/playwright';
import { chromium } from 'playwright-core';
import { baseUrl, browserOptions } from './browser-config.mjs';

const browser = await chromium.launch(browserOptions());
try {
  const context = await browser.newContext({ acceptDownloads: true, reducedMotion: 'reduce' });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto(`${baseUrl}/construction/pilot`, { waitUntil: 'domcontentloaded' });
  await page.getByTestId('pilot-result').waitFor();
  const capacity = page.getByLabel('Monthly shared capacity (normalized units)', { exact: true });
  const policy = page.getByLabel('Allocation policy', { exact: true });
  for (const label of [
    'Other private demand multiplier',
    'Mobility supply (normalized units)',
    'AI work shift (months)',
  ]) await page.getByLabel(label, { exact: true }).waitFor();
  assert.match(await page.getByRole('main').innerText(), /normalized/i);
  assert.match(await page.getByRole('main').innerText(), /uncalibrated|illustrative|scenario/i);
  assert.match(await page.getByRole('main').innerText(), /omits dollar impacts|not.{0,60}(monetary|dollar|cost)|no.{0,60}(monetary|dollar|cost)/i,
    'pilot explains that normalized work is not a monetary estimate');

  async function exportRun() {
    const pending = page.waitForEvent('download');
    await page.getByRole('button', { name: 'Export pilot JSON', exact: true }).click();
    const download = await pending;
    assert.equal(download.suggestedFilename(), 'alberta-cal3-windsong-pilot.json');
    const payload = JSON.parse(await readFile(await download.path(), 'utf8'));
    assert.ok(payload.evidence && payload.input && payload.result, 'export includes evidence, inputs, result');
    assert.ok(payload.result.cases && payload.thresholdResult.thresholds, 'export contains reverse-stress evidence');
    assert.ok(!JSON.stringify(payload).includes('additionalCAD'), 'normalized pilot does not export a dollar premium');
    return payload;
  }
  const initial = await exportRun();
  assert.equal(initial.evidence.facts.publicWholeProjectEstimateCad.value, 64300000);
  assert.equal(initial.evidence.facts.actualTradeCapacity.value, null);
  assert.equal(initial.evidence.facts.publicUncommittedExposureCad.value, null);
  assert.match(await page.getByRole("main").innerText(), /\$64\.3 million/);
  assert.ok(await page.getByTestId('pilot-result').innerText());

  await capacity.selectOption('100');
  const ample = await exportRun();
  assert.equal(ample.result.cases[0].incrementalDelayMonths, 0, 'adequate capacity removes incremental public delay');
  await capacity.selectOption('5');
  await policy.selectOption('protect-background');
  const protectedPublic = await exportRun();
  assert.equal(protectedPublic.result.cases[0].incrementalDelayMonths, 0, 'protect-public allocation preserves baseline public completion');

  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 1000 });
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `overflow at ${width}`);
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();
    assert.deepEqual(results.violations.map(({ id, impact, nodes }) => ({ id, impact, nodes: nodes.length })), [],
      `pilot accessibility at ${width}`);
    await page.screenshot({ path: `/tmp/alberta-pilot-${width}.png`, fullPage: true });
  }
  assert.deepEqual(errors, []);
  console.log(JSON.stringify({ route: '/construction/pilot', initialIncrementalDelayMonths: initial.result.cases[0].incrementalDelayMonths,
    adequateCapacityDelayMonths: ample.result.cases[0].incrementalDelayMonths,
    protectPublicDelayMonths: protectedPublic.result.cases[0].incrementalDelayMonths,
    widths: [1440, 390], status: 'passed' }));
  await context.close();
} finally {
  await browser.close();
}
