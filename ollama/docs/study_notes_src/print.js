// Prints report_final.html (built by build.py) to a PDF via a locally-installed Chrome.
// Usage: node print.js <output-pdf-path>
const puppeteer = require('puppeteer-core');
const path = require('path');

const CHROME_CANDIDATES = [
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/usr/bin/google-chrome',
  '/usr/bin/chromium-browser',
];

(async () => {
  const fs = require('fs');
  const executablePath = CHROME_CANDIDATES.find((p) => fs.existsSync(p));
  if (!executablePath) {
    console.error('No Chrome/Chromium executable found. Edit CHROME_CANDIDATES in print.js.');
    process.exit(1);
  }

  const browser = await puppeteer.launch({
    executablePath,
    headless: 'new',
    args: ['--no-sandbox', '--disable-gpu'],
  });
  const page = await browser.newPage();
  const htmlPath = 'file://' + path.resolve(__dirname, 'report_final.html');
  await page.goto(htmlPath, { waitUntil: 'networkidle0' });
  await page.emulateMediaType('print');
  await page.pdf({
    path: process.argv[2],
    printBackground: true,
    displayHeaderFooter: false,
    preferCSSPageSize: true,
  });
  await browser.close();
  console.log('Wrote', process.argv[2]);
})();
