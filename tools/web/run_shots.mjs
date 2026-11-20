// Preview pictures of the browser version in several window sizes (?shots): the game reports "shot" when a
// scene stands, the picture is taken then. Usage: node run_shots.mjs <base url> <shots dir>
import { webkit } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const [base, shots] = process.argv.slice(2);
fs.mkdirSync(shots, { recursive: true });
const SIZES = [
  ['handy_app', 412, 915, 3],        // as tall as the app: unchanged
  ['handy_chrome', 412, 807, 3],     // Philip's Chrome with its bars
  ['iphone_safari', 402, 714, 3],
  ['ipad_hoch', 834, 1194, 2],
  ['ipad_quer', 1194, 834, 2],
];
const browser = await webkit.launch();
for (const [name, w, h, dpr] of SIZES) {
  const page = await (await browser.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: dpr, isMobile: true, hasTouch: true })).newPage();
  let done = false;
  const taking = [];
  page.on('console', m => {
    const t = m.text();
    if (!t.startsWith('PROBE ')) return;
    let p; try { p = JSON.parse(t.slice(6)); } catch { return; }
    if (p.kind === 'shot') taking.push(page.screenshot({ path: path.join(shots, `${name}_${p.name}.png`) }).catch(() => {}));
    if (p.kind === 'done') done = true;
  });
  await page.goto(`${base}/index.html?probe&shots&dev=${name}`, { timeout: 120000 });
  const start = Date.now();
  while (!done && Date.now() - start < 180000) await page.waitForTimeout(1000);
  await Promise.all(taking);
  console.log(name, done ? 'fertig' : 'NICHT fertig');
  await page.context().close();
}
await browser.close();
