import AxeBuilder from '@axe-core/playwright';
import { chromium } from 'playwright-core';

import { baseUrl, browserOptions } from './browser-config.mjs';
const routes = [
  '/',
  '/delivery',
  '/construction',
  '/construction/pilot',
  '/project-scenario',
  '/research',
  '/evidence',
  '/pressure',
  '/scenario',
  '/methods',
  '/historical-analog',
  '/digest',
  '/downloads',
  '/status',
];
const blockingImpacts = new Set(['serious', 'critical']);

const browser = await chromium.launch(browserOptions());
const context = await browser.newContext({ reducedMotion: 'reduce' });
const page = await context.newPage();
const report = [];

try {
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 1000 });
    for (const route of routes) {
    await page.goto(`${baseUrl}${route}`, { waitUntil: 'domcontentloaded' });
    await page.getByRole('main').waitFor({ state: 'visible' });
    await page.evaluate(() => document.fonts.ready);
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();
    report.push({
      route,
      width,
      violations: results.violations.map((violation) => ({
        id: violation.id,
        impact: violation.impact,
        nodes: violation.nodes.length,
        help: violation.help,
        examples: violation.nodes.slice(0, 12).map((node) => ({
          target: node.target,
          html: node.html,
          summary: node.failureSummary,
        })),
      })),
    });
    }
  }
} finally {
  await context.close();
  await browser.close();
}

const blockers = report.flatMap(({ route, width, violations }) =>
  violations.filter(({ impact }) => blockingImpacts.has(impact)).map((violation) => ({ route, width, ...violation })),
);

console.log(JSON.stringify({ baseUrl, routes: report, blockingViolations: blockers }, null, 2));
if (blockers.length > 0) process.exitCode = 1;
