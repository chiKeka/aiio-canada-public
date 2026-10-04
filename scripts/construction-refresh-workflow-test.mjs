import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { chromium } from 'playwright-core';
import { baseUrl, browserOptions } from './browser-config.mjs';
const browser = await chromium.launch(browserOptions());
try {
  const context = await browser.newContext({ acceptDownloads: true, reducedMotion: 'reduce' });
  const page = await context.newPage();
  const metadata = await (
    await page.request.get(`${baseUrl}/api/construction/revision`)
  ).json();
  let update = false,
    fail = false,
    malformed = false;
  await page.route('**/api/construction/revision', (route) => {
    if (fail) return route.fulfill({ status: 503, body: 'Unavailable' });
    if (malformed) return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ revision: null }) });
    const revision = update ? 'test-new-publication' : metadata.revision;
    update = false;
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ ...metadata, revision }),
    });
  });
  const initialCheck = page.waitForResponse((r) =>
    r.url().includes('/api/construction/revision'),
  );
  await page.goto(`${baseUrl}/construction`);
  await initialCheck;
  await page.evaluate(() => new Promise(requestAnimationFrame));
  await page.getByTestId('alberta-overview').waitFor();
  await page.getByText('Source updates and freshness', { exact: true }).click();
  assert.equal(
    await page
      .getByRole('table', {
        name: 'Alberta source update cadence and freshness',
        exact: true,
      })
      .getByRole('row')
      .count(),
    8,
  );
  await page.getByText('Source updates and freshness', { exact: true }).click();
  const evidenceText = async () => (await page.getByTestId('alberta-overview').innerText())
    .replace(/^Update check unavailable[^\n]*\n|^This view checks for newly published evidence[^\n]*\n/gm, '');
  const initialOverview = await evidenceText();
  async function exportedRun() {
    await page.getByRole('button', { name: 'Demand model', exact: true }).click();
    const downloaded = page.waitForEvent('download');
    await page.getByRole('button', { name: 'Download scenario inputs (.json)', exact: true }).click();
    const file = await downloaded;
    const payload = JSON.parse(await readFile(await file.path(), 'utf8'));
    delete payload.createdAt;
    const mountedCheck = page.waitForResponse((r) => r.url().includes('/api/construction/revision'));
    await page.getByRole('button', { name: 'Alberta overview', exact: true }).click();
    await (await mountedCheck).finished();
    await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    await page.getByTestId('alberta-overview').waitFor();
    return payload;
  }
  const beforeRevision = await exportedRun();
  update = true;
  const refreshed = page.waitForRequest(
    (r) =>
      new URL(r.url()).pathname === '/construction' &&
      r.headers()['rsc'] === '1',
  );
  await page.evaluate(() => window.dispatchEvent(new Event('focus')));
  await refreshed;
  await page.evaluate(() => new Promise(requestAnimationFrame));
  assert.deepEqual(await exportedRun(), beforeRevision, 'unchanged evidence stays consistent after a revision check');
  fail = true;
  await page.evaluate(() => window.dispatchEvent(new Event('focus')));
  await page.getByText(/Update check unavailable/).waitFor();
  assert.equal(await evidenceText(), initialOverview,
    'a failed refresh must preserve every displayed evidence value');
  assert.deepEqual(await exportedRun(), beforeRevision, 'failed refresh preserves scenario export');
  fail = false;
  malformed = true;
  const invalid = page.waitForResponse((r) => r.url().includes('/api/construction/revision'));
  await page.evaluate(() => window.dispatchEvent(new Event('focus')));
  await invalid;
  await page.getByText(/Update check unavailable/).waitFor();
  assert.equal(await evidenceText(), initialOverview);
  malformed = false;
  await page.evaluate(() => window.dispatchEvent(new Event('focus')));
  await page
    .getByText(/This view checks for newly published evidence/)
    .waitFor();
  console.log(
    'Passed: source cadence, new-revision server refresh, HTTP/malformed revision failure retention, UI/export consistency and recovery.',
  );
} finally {
  await browser.close();
}
