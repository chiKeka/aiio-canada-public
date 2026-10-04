import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import AxeBuilder from '@axe-core/playwright';
import { chromium } from 'playwright-core';
import { baseUrl, browserOptions } from './browser-config.mjs';

const browser = await chromium.launch(browserOptions());
try {
  const context = await browser.newContext({
    acceptDownloads: true,
    reducedMotion: 'reduce',
  });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto(`${baseUrl}/project-scenario?view=assessment`, {
    waitUntil: 'domcontentloaded',
  });
  await page.getByTestId('project-assessment-workspace').waitFor();
  const workspace = page.getByTestId('project-assessment-workspace');
  async function exported(downloadJSON = false) {
    const printable = JSON.parse(
      await page.locator('#project-assessment-print-record pre').textContent(),
    );
    if (!downloadJSON) return printable;
    const pending = page.waitForEvent('download');
    await page
      .getByRole('button', {
        name: 'Export current assessment JSON',
        exact: true,
      })
      .click();
    const download = await pending;
    assert.equal(download.suggestedFilename(), 'aiio-project-assessment.json');
    const record = JSON.parse(await readFile(await download.path(), 'utf8'));
    const printed = JSON.parse(
      await page.locator('#project-assessment-print-record pre').textContent(),
    );
    const { createdAt, ...current } = record;
    assert.ok(createdAt);
    assert.deepEqual(
      current,
      printed,
      'export and printable current input/result record agree',
    );
    return record;
  }
  const initial = await exported(true);
  assert.equal(initial.result.qualified, 'qualitative');
  const evidenceStatus = await page
    .getByTestId('assessment-evidence-status')
    .innerText();
  assert.match(
    evidenceStatus,
    /Sources verified: \d+\/\d+.*Release:.*Independent review pending/,
  );
  const frozenRelease = JSON.parse(
    await readFile('public/data/source-freshness.json', 'utf8'),
  );
  assert.equal(
    initial.readiness.releaseVintage,
    frozenRelease.as_of_date,
    'verification attempts do not advance the frozen release vintage',
  );
  assert.ok(
    evidenceStatus.includes(`Release: ${initial.readiness.releaseVintage}`),
  );
  assert.equal(
    initial.inputs.packages.every((item) => item.hours === null),
    true,
  );
  assert.match(
    await page.getByTestId('project-assessment-result').innerText(),
    /not established/i,
  );
  await page
    .getByRole('button', {
      name: 'Load hypothetical $50M school example',
      exact: true,
    })
    .click();
  const fixture = await exported(true);
  assert.equal(fixture.configuration.budgetMillions, 50);
  assert.equal(
    fixture.inputs.packages.find((item) => item.scope === 'Electrical')
      .uncommittedCAD,
    8e6,
  );
  assert.equal(fixture.result.qualified, 'conditional');
  assert.ok(fixture.result.impacts.withDC.delayMonths > 0);
  assert.ok(fixture.result.impacts.withDC.totalAdditionalCAD > 0);
  assert.match(
    await page.getByTestId('withDC-delay').innerText(),
    new RegExp(`^${fixture.result.impacts.withDC.delayMonths} months$`),
  );

  await page
    .getByLabel('Project location', { exact: true })
    .fill('A different nearby site');
  const nearby = await exported();
  assert.deepEqual(
    nearby.result.impacts,
    fixture.result.impacts,
    'free location/proximity does not invent a resource match',
  );
  await workspace
    .locator('summary')
    .filter({ hasText: /^1\. Packages/ })
    .click();
  await workspace
    .locator('summary')
    .filter({ hasText: /^Electrical package$/ })
    .click();
  await page.getByLabel(/^Electrical commitment/).selectOption('fixed');
  const fixed = await exported();
  assert.equal(
    fixed.inputs.packages.find((item) => item.scope === 'Electrical')
      .uncommittedCAD,
    0,
    'fixed commitment clears variable exposure explicitly',
  );
  assert.equal(
    fixed.result.impacts.withDC.escalationCAD,
    0,
    'fixed commitment suppresses repricing',
  );
  assert.equal(
    fixed.result.impacts.withDC.delayMonths,
    fixture.result.impacts.withDC.delayMonths,
    'contract price protection does not create schedule capacity',
  );
  await page.getByLabel(/^Electrical commitment/).selectOption('variable');
  await page
    .getByLabel('Electrical remaining exposed value (CAD)', { exact: true })
    .fill('8000000');
  await page
    .getByLabel('Electrical paid labour hours', { exact: true })
    .fill('');
  const unknown = await exported();
  assert.equal(unknown.result.qualified, 'qualitative');
  assert.equal(
    unknown.result.impacts.withDC.delayMonths,
    null,
    'missing hours remain unknown rather than zero',
  );
  await page
    .getByLabel('Electrical paid labour hours', { exact: true })
    .fill('100');
  await page
    .getByLabel('Confirmed shared contractor catchment', { exact: true })
    .fill('different-pool');
  const differentPool = await exported();
  assert.equal(differentPool.result.matches.length, 0);
  assert.equal(
    differentPool.result.impacts.withDC.delayMonths,
    0,
    'different resource pools have no direct competition',
  );
  await page
    .getByLabel('Confirmed shared contractor catchment', { exact: true })
    .fill('hypothetical-shared-electrical-pool');
  await workspace
    .locator('summary')
    .filter({ hasText: /^2\. Shared resources/ })
    .click();
  await page
    .getByLabel('AI phase work starts', { exact: true })
    .fill('2029-01');
  await page
    .getByLabel('AI phase planned work finish', { exact: true })
    .fill('2029-09');
  const later = await exported();
  assert.equal(later.result.matches.length, 0);
  assert.equal(
    later.result.impacts.withDC.delayMonths,
    0,
    'later AI work after owner work does not backdate a delay',
  );
  await page
    .getByLabel('AI phase work starts', { exact: true })
    .fill('2026-01');
  await page
    .getByLabel('AI phase planned work finish', { exact: true })
    .fill('2026-09');
  await page.getByLabel('AI phase paid labour hours', { exact: true }).fill('');
  const unknownAI = await exported();
  assert.equal(
    unknownAI.result.impacts.withDC.delayMonths,
    null,
    'selected phase without hours is not a zero-DC control',
  );
  await page
    .getByLabel('AI phase paid labour hours', { exact: true })
    .fill('100');
  await page
    .getByLabel('Electrical shared capacity (paid hours / month)', {
      exact: true,
    })
    .fill('');
  await page
    .getByLabel(
      'Optional assumed capacity test grid (hours / month, comma separated)',
      { exact: true },
    )
    .fill('5,10,20,100');
  const capacityUnknown = await exported();
  assert.equal(
    capacityUnknown.result.qualified,
    'qualitative',
    'entered test grid does not become measured capacity',
  );
  assert.equal(
    capacityUnknown.inputs.capacity[
      'hypothetical-shared-electrical-pool:Electrical'
    ],
    null,
  );
  assert.equal(capacityUnknown.result.impacts.withDC.delayMonths, null);
  assert.ok(capacityUnknown.result.capacityThresholds.length);
  await page
    .getByLabel('Electrical shared capacity (paid hours / month)', {
      exact: true,
    })
    .fill('10');
  await page
    .getByLabel(
      'Optional assumed capacity test grid (hours / month, comma separated)',
      { exact: true },
    )
    .fill('');
  await workspace
    .locator('summary')
    .filter({ hasText: /^3\. Mitigation/ })
    .click();
  await page
    .getByLabel('Added shared-trade capacity (paid hours / month)', {
      exact: true,
    })
    .fill('100');
  const capacityMitigation = await exported();
  assert.ok(
    capacityMitigation.result.impacts.mitigation.delayMonths <=
      fixture.result.impacts.withDC.delayMonths,
  );
  assert.deepEqual(
    capacityMitigation.result.cases.withDC,
    fixture.result.cases.withDC,
    'mitigation does not rewrite the paired AI case',
  );
  await page
    .getByLabel('Added shared-trade capacity (paid hours / month)', {
      exact: true,
    })
    .fill('0');
  const beforeNavigation = await exported();
  const views = page.getByRole('navigation', {
    name: 'Executive dashboard views',
    exact: true,
  });
  await views.getByRole('button', { name: 'Overview', exact: true }).click();
  await views
    .getByRole('button', { name: 'Assess my project', exact: true })
    .click();
  await page.getByText(/Restored this visit’s draft/).waitFor();
  const afterNavigation = await exported(true);
  assert.deepEqual(
    afterNavigation.inputs,
    beforeNavigation.inputs,
    'draft survives view changes without browser persistence opt-in',
  );
  await page
    .getByLabel(/Save this draft in this browser across navigation/)
    .check();
  const saved = await exported();
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page
    .getByText('Restored your draft saved in this browser.', { exact: true })
    .waitFor();
  assert.deepEqual(
    (await exported()).inputs,
    saved.inputs,
    'opted-in draft survives reload',
  );
  // Malformed saved shapes must be ignored rather than applied to the model or context.
  const invalidContext = await browser.newContext();
  await invalidContext.addInitScript(() =>
    localStorage.setItem(
      'aiio-project-owner-draft-v1',
      JSON.stringify({
        version: 1,
        configuration: {},
        draft: { packages: [null, null, null, null] },
      }),
    ),
  );
  const invalidPage = await invalidContext.newPage();
  await invalidPage.goto(`${baseUrl}/project-scenario?view=assessment`, {
    waitUntil: 'domcontentloaded',
  });
  await invalidPage.getByText(/Saved draft has an unsupported shape/).waitFor();
  assert.match(
    await invalidPage.getByTestId('project-assessment-result').innerText(),
    /not established/i,
  );
  await invalidContext.close();

  for (const details of await workspace.locator('details').all()) {
    await details.evaluate((element) => {
      element.open = true;
    });
  }
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 1000 });
    assert.ok(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
      `page overflow at ${width}`,
    );
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();
    assert.deepEqual(
      results.violations.map(({ id, impact, nodes }) => ({
        id,
        impact,
        nodes: nodes.length,
      })),
      [],
      `accessibility at ${width}`,
    );
    await page.screenshot({
      path: `/tmp/project-assessment-${width}.png`,
      fullPage: true,
    });
  }
  await page.emulateMedia({ media: 'print' });
  assert.equal(
    await page.locator('#project-assessment-print-record').isVisible(),
    true,
  );
  assert.equal(
    await page
      .getByRole('button', {
        name: 'Export current assessment JSON',
        exact: true,
      })
      .isVisible(),
    false,
  );
  await page.emulateMedia({ media: 'screen' });
  await page
    .getByRole('button', { name: 'Reset package draft', exact: true })
    .click();
  const reset = await exported(true);
  assert.equal(
    reset.configuration.budgetMillions,
    50,
    'reset retains project context',
  );
  assert.ok(reset.inputs.packages.every((item) => item.hours === null));
  assert.equal(reset.result.qualified, 'qualitative');
  assert.deepEqual(errors, []);
  console.log(
    'Passed project-owner assessment: unknown defaults, hypothetical exposure bridge, contract/catchment/timing mechanisms, mitigation isolation, draft navigation/reload, malformed storage, JSON/print parity, reset and desktop/mobile accessibility.',
  );
  await context.close();
} finally {
  await browser.close();
}
