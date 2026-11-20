// Runs the browser test (?probe) in Playwright's WebKit (Safari's engine), WebKit as an iPhone and iPad,
// and Chromium; screenshots along the way. Usage: node run_browsers.mjs <base url> <logs dir> <shots dir>
import { webkit, chromium, devices } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const [base, logs, shots] = process.argv.slice(2);
fs.mkdirSync(shots, { recursive: true });
const RUNS = [
  ['webkit-desktop', webkit, { viewport: { width: 450, height: 1000 } }],
  ['webkit-iphone', webkit, devices['iPhone 15 Pro']],
  ['webkit-ipad', webkit, devices['iPad Pro 11']],
  ['chromium', chromium, { viewport: { width: 450, height: 1000 } }],
];

function done(dev) {
  const f = path.join(logs, dev + '.jsonl');
  if (!fs.existsSync(f)) return false;
  return fs.readFileSync(f, 'utf8').split('\n').some(l => {
    try {
      const m = JSON.parse(l).msg || '';
      return m.startsWith('PROBE ') && JSON.parse(m.slice(6)).kind === 'done';
    } catch { return false; }
  });
}

for (const [dev, type, opts] of RUNS) {
  let browser;
  try {
    browser = await type.launch();
    const page = await (await browser.newContext(opts)).newPage();
    page.on('crash', () => fs.appendFileSync(path.join(logs, dev + '.jsonl'), JSON.stringify({ dev, type: 'crash' }) + '\n'));
    await page.goto(`${base}/index.html?probe&dev=${dev}`, { timeout: 120000 });
    const start = Date.now();
    let n = 0;
    while (Date.now() - start < 360000 && !done(dev)) {
      await page.waitForTimeout(15000);
      await page.screenshot({ path: path.join(shots, `${dev}_${String(n++).padStart(2, '0')}.png`) }).catch(() => {});
    }
    await page.screenshot({ path: path.join(shots, `${dev}_ende.png`) }).catch(() => {});
    console.log(dev, done(dev) ? 'fertig' : 'NICHT fertig', Math.round((Date.now() - start) / 1000) + ' s');
  } catch (e) {
    console.log(dev, 'Fehler', String(e));
    fs.appendFileSync(path.join(logs, dev + '.jsonl'), JSON.stringify({ dev, type: 'runner', msg: String(e) }) + '\n');
  } finally {
    if (browser) await browser.close();
  }
}
