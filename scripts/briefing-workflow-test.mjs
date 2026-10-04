import assert from 'node:assert/strict';
import { chromium } from 'playwright-core';
const browser = await chromium.launch({
  executablePath:
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  headless: true,
});
try {
  const page = await browser.newPage({ acceptDownloads: true });
  await page.goto('http://localhost:3002/construction');
  const button = page.getByRole('button', {
    name: 'Download Alberta briefing (.pptx)',
    exact: true,
  });
  await button.waitFor();
  const pending = page.waitForEvent('download');
  await button.click();
  const download = await pending;
  assert.match(
    download.suggestedFilename(),
    /^Alberta_Delivery_Briefing_.*\.pptx$/,
  );
  assert.equal(await download.failure(), null);
  await download.saveAs('/tmp/briefing-browser.pptx');
  await page.route('**/api/briefing', (route) =>
    route.fulfill({
      status: 503,
      contentType: 'application/json',
      body: '{"error":"Unavailable"}',
    }),
  );
  await button.click();
  await page.getByRole('alert').waitFor();
  assert.equal(await button.isEnabled(), true);
  await page.setViewportSize({ width: 390, height: 844 });
  assert.equal(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
    true,
  );
  await page.screenshot({ path: '/tmp/briefing-mobile.png' });
  console.log(
    'Passed: browser download, failure message, retry availability and mobile width.',
  );
} finally {
  await browser.close();
}
