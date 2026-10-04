import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import AxeBuilder from '@axe-core/playwright';
import { chromium } from 'playwright-core';
import { baseUrl, browserOptions } from './browser-config.mjs';

const digest = JSON.parse(await readFile(new URL('../public/data/reviewed-digest.json', import.meta.url), 'utf8'));
const release = JSON.parse(await readFile(new URL('../public/data/latest.json', import.meta.url), 'utf8'));
const browser = await chromium.launch(browserOptions());
try {
  const context = await browser.newContext({ reducedMotion: 'reduce' });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto(`${baseUrl}/digest`, { waitUntil: 'domcontentloaded' });
  const status = page.getByTestId('reviewed-digest-status');
  await status.waitFor();
  assert.ok((await status.innerText()).includes(digest.edition_date));
  assert.ok((await status.innerText()).includes(digest.status));
  assert.equal(digest.status, 'approved', 'public reviewed artifact must be approved');
  const frozen = await page.getByTestId('frozen-model-vintage').innerText();
  assert.ok(frozen.includes(release.manifest.version));
  assert.ok(frozen.includes(release.digest.edition_date));
  assert.ok(frozen.includes(release.manifest.created_at.slice(0, 10)));
  assert.match(await page.getByRole('main').innerText(), /internal editorial review/);
  assert.match(await page.getByRole('main').innerText(), /not independent model validation/);
  const articles = page.getByRole('main').locator('article');
  assert.equal(await articles.count(), digest.items.length);
  for (const [index, item] of digest.items.entries()) {
    const article = articles.nth(index);
    assert.ok((await article.innerText()).includes(item.headline));
    assert.ok((await article.innerText()).includes(item.observed_change));
    assert.ok((await article.innerText()).includes(item.model_implication));
    const sources = article.getByRole('list', { name: `Official sources for ${item.headline}`, exact: true });
    assert.equal(await sources.getByRole('link').count(), item.sources.length);
    for (const source of item.sources) {
      const link = sources.getByRole('link', { name: `${source.source_id} (opens in a new tab)`, exact: true });
      assert.equal(await link.getAttribute('href'), source.source_url);
      assert.equal(await link.getAttribute('target'), '_blank');
    }
  }
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 1000 });
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `digest overflow at ${width}`);
    const results = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();
    assert.deepEqual(results.violations.map(({ id, impact, nodes }) => ({ id, impact, nodes: nodes.length })), [], `digest accessibility at ${width}`);
    await page.screenshot({ path: `/tmp/reviewed-digest-${width}.png`, fullPage: true });
  }
  assert.deepEqual(errors, []);
  console.log(`Passed reviewed digest ${digest.edition_date}/${digest.status}: all ${digest.items.reduce((sum, item) => sum + item.sources.length, 0)} source links, separate frozen model vintage, desktop/mobile accessibility.`);
} finally { await browser.close(); }
