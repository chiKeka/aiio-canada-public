import { existsSync } from 'node:fs';

export const baseUrl = process.env.AIIO_BASE_URL ?? 'http://127.0.0.1:3002';
// CI installs Playwright Chromium; a developer can use an installed browser.
export function browserOptions() {
  const candidates = process.platform === 'darwin'
    ? ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome']
    : ['/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser'];
  const executablePath = process.env.CHROME_EXECUTABLE ?? candidates.find(existsSync);
  return { headless: true, ...(executablePath ? { executablePath } : {}) };
}
