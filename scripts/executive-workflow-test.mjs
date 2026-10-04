import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import { chromium } from 'playwright-core';

import { baseUrl, browserOptions } from './browser-config.mjs';
const browser = await chromium.launch(browserOptions());
const context = await browser.newContext({
  acceptDownloads: true,
  reducedMotion: 'reduce',
});
const page = await context.newPage();
const errors = [];
page.on('pageerror', (error) => errors.push(error.message));
try {
  await page.goto(`${baseUrl}/project-scenario?view=outlook`, { waitUntil: 'networkidle' });
  await page
    .getByRole('slider', { name: 'Selected project month', exact: true })
    .fill('14');
  const month = await page
    .getByRole('slider', { name: 'Selected project month', exact: true })
    .getAttribute('aria-valuetext');
  await page.getByRole('button', { name: /^Pin configuration$/ }).click();
  await page
    .getByRole('button', { name: 'Edit assumptions', exact: true })
    .click();
  await page
    .getByRole('spinbutton', { name: 'Base budget ($M)', exact: true })
    .fill('1600');
  await page.getByRole('button', { name: 'Cancel', exact: true }).click();
  await page
    .getByRole('button', { name: 'Edit assumptions', exact: true })
    .click();
  assert.equal(
    await page
      .getByRole('spinbutton', { name: 'Base budget ($M)', exact: true })
      .inputValue(),
    '1200',
  );
  await page
    .getByRole('spinbutton', { name: 'Base budget ($M)', exact: true })
    .fill('1500');
  await page
    .getByRole('button', { name: 'Apply changes', exact: true })
    .click();
  await page.getByRole('button', { name: 'Guided story', exact: true }).click();
  await page
    .getByRole('button', { name: /02Monthly exposure|02 Monthly exposure/ })
    .click();
  assert.equal(
    await page
      .getByRole('slider', { name: 'Briefing month', exact: true })
      .inputValue(),
    '14',
  );
  await page
    .getByRole('button', { name: /03Why it happens|03 Why it happens/ })
    .click();
  const driverButtons = page
    .locator('#workspace-content button[aria-pressed]')
    .filter({ hasText: /pp|Withheld/ });
  const driver = driverButtons.nth(1);
  const driverText = (await driver.innerText()).split('\n')[0];
  await driver.click();
  await page.getByRole('button', { name: 'Overview', exact: true }).click();
  assert.equal(
    await page
      .getByRole('slider', { name: 'Selected project month', exact: true })
      .getAttribute('aria-valuetext'),
    month,
  );
  assert.ok(
    (await page.locator('button[aria-pressed="true"]').allTextContents()).some(
      (text) => text.includes(driverText),
    ),
  );
  await page.getByRole('button', { name: 'Evidence', exact: true }).click();
  await page.getByRole('button', { name: /Public projects/ }).click();
  assert.match(await page.locator('#selected-evidence').innerText(), /Alberta/);
  await page
    .getByRole('button', { name: 'Open decision brief', exact: true })
    .click();
  const brief = page.locator('#executive-decision-brief');
  assert.equal(await brief.count(), 1);
  assert.match(await brief.innerText(), /Pinned alternative/);
  assert.ok((await brief.innerText()).includes(month));
  const pending = page.waitForEvent('download');
  await page
    .getByRole('button', { name: 'Download snapshot', exact: true })
    .click();
  const download = await pending;
  const envelope = JSON.parse(await readFile(await download.path(), 'utf8'));
  assert.match(
    execFileSync(
      process.execPath,
      ['scripts/verify-assessment-snapshot.mjs', await download.path()],
      { encoding: 'utf8' },
    ),
    /cashflow reproduced/,
  );
  assert.equal(
    createHash('sha256').update(envelope.payload).digest('hex'),
    envelope.sha256,
  );
  const record = JSON.parse(envelope.payload);
  assert.equal(record.focus.month, month);
  assert.equal(record.project.inputs.budgetMillions, 1500);
  assert.equal(record.comparison.inputs.budgetMillions, 1200);
  assert.ok(
    Math.abs(
      record.comparison.scenario_spend_delta_millions -
        record.result.combinedSpend * 0.2,
    ) < 1e-8,
  );
  assert.ok(
    Math.abs(
      record.result.combinedSpend -
        record.result.monthly.reduce((sum, row) => sum + row.combinedSpend, 0),
    ) < 1e-8,
  );
  await page.emulateMedia({ media: 'print' });
  await page.waitForFunction(
    () =>
      getComputedStyle(document.querySelector('button')).visibility ===
      'hidden',
  );
  assert.equal(
    await brief.evaluate((element) => getComputedStyle(element).visibility),
    'visible',
  );
  await page.waitForFunction(() => [...document.querySelectorAll('button')].filter(e => e.textContent === 'Download snapshot').every(e => getComputedStyle(e).visibility === 'hidden'));
  assert.equal(
    await page
      .getByRole('button', {
        name: 'Download snapshot',
        exact: true,
        includeHidden: true,
      })
      .evaluate((element) => getComputedStyle(element).visibility),
    'hidden',
  );
  const pdf = await page.pdf({
    path: '/tmp/aiio-enterprise-brief.pdf',
    format: 'A4',
    printBackground: true,
  });
  assert.equal(pdf.subarray(0, 5).toString(), '%PDF-');
  await page.emulateMedia({ media: 'screen' });
  await page.getByRole('button', { name: 'Share inputs', exact: true }).click();
  const shared = page.url();
  assert.equal(new URL(shared).searchParams.get('profile'), 'bell');
  await page.goto(shared, { waitUntil: 'networkidle' });
  await page
    .getByRole('button', { name: 'Edit assumptions', exact: true })
    .click();
  assert.equal(
    await page
      .getByRole('spinbutton', { name: 'Base budget ($M)', exact: true })
      .inputValue(),
    '1500',
  );
  await page.locator('input[type="month"]').fill('2041-01');
  await page
    .getByRole('button', { name: 'Apply changes', exact: true })
    .click();
  assert.match(
    await page.getByRole('alert').innerText(),
    /no later than the project start/,
  );
  await page.getByRole('button', { name: 'Cancel', exact: true }).click();
  await page.goto(`${baseUrl}/project-scenario?view=outlook&basis=2041-01`, { waitUntil: 'networkidle' });
  await page
    .getByRole('button', { name: 'Open decision brief', exact: true })
    .click();
  assert.equal(
    await page
      .getByRole('button', { name: 'Download snapshot', exact: true })
      .isDisabled(),
    true,
  );
  assert.match(await brief.innerText(), /withheld/);
  await page.goto(`${baseUrl}/project-scenario?view=outlook`, { waitUntil: 'networkidle' });
  await page.setViewportSize({ width: 390, height: 844 });
  await page
    .getByRole('button', { name: 'Edit assumptions', exact: true })
    .click();
  const drawer = page.getByRole('dialog', { name: 'Project & assumptions' });
  assert.equal(Math.round((await drawer.boundingBox()).width), 390);
  await page
    .getByRole('textbox', { name: 'Project', exact: true })
    .press('Escape');
  await drawer.waitFor({ state: 'hidden' });
  assert.equal(await drawer.isVisible(), false);
  assert.equal(
    await page
      .getByRole('button', { name: 'Edit assumptions', exact: true })
      .evaluate((element) => element === document.activeElement),
    true,
  );
  assert.equal(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
    true,
  );
  await page.screenshot({
    path: '/tmp/aiio-enterprise-mobile.png',
    fullPage: true,
  });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.screenshot({
    path: '/tmp/aiio-enterprise-desktop.png',
    fullPage: true,
  });
  assert.deepEqual(errors, []);
  console.log(
    'Executive workflow passed: shared focus, evidence navigation, changed-budget comparison, brief, snapshot checksum, PDF rendering, input link restore and invalid-input withholding.',
  );
} finally {
  await context.close();
  await browser.close();
}
