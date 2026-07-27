/**
 * Render the A0 poster from docs/poster/poster.html.
 *
 * Outputs, both next to the source:
 *   poster.pdf  — print-ready, exactly 841 x 1189 mm (A0 portrait)
 *   poster.png  — screen preview at 1/4 scale, for review without a PDF viewer
 *
 * Lives under frontend/scripts because that is where Playwright is installed
 * (same reason as capture-screenshots.mjs):
 *
 *   cd frontend && node scripts/build_poster.mjs
 *
 * printBackground is on because the poster's whole visual system is background
 * colour — the title bar, the hook bars, the block tints. Without it Chrome
 * drops every one of them and the PDF comes out as grey text on white.
 */

import { chromium } from 'playwright';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { dirname, resolve } from 'node:path';
import { existsSync, statSync } from 'node:fs';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, '../..');
const SOURCE = resolve(ROOT, 'docs/poster/poster.html');
const PDF = resolve(ROOT, 'docs/poster/poster.pdf');
const PNG = resolve(ROOT, 'docs/poster/poster.png');

// A0 portrait in millimetres, and the same size in CSS pixels (96 dpi) so the
// screenshot viewport matches the print layout instead of reflowing it.
const MM_TO_PX = 96 / 25.4;
const WIDTH_MM = 841;
const HEIGHT_MM = 1189;
const PREVIEW_SCALE = 0.25;

async function main() {
  if (!existsSync(SOURCE)) {
    console.error(`[error] missing source: ${SOURCE}`);
    process.exit(1);
  }

  const browser = await chromium.launch();
  const page = await browser.newPage({
    viewport: {
      width: Math.round(WIDTH_MM * MM_TO_PX),
      height: Math.round(HEIGHT_MM * MM_TO_PX),
    },
    deviceScaleFactor: 1,
  });

  const failures = [];
  page.on('requestfailed', (request) => failures.push(request.url()));

  await page.goto(pathToFileURL(SOURCE).href, { waitUntil: 'networkidle' });

  // A missing screenshot or plate crop leaves a blank rectangle that is easy to
  // miss on a poster this large, so report it rather than let it reach print.
  if (failures.length > 0) {
    console.log(`[warn] ${failures.length} asset(s) failed to load:`);
    for (const url of failures) console.log(`        ${url}`);
  }

  await page.pdf({
    path: PDF,
    width: `${WIDTH_MM}mm`,
    height: `${HEIGHT_MM}mm`,
    printBackground: true,
    preferCSSPageSize: true,
  });

  await page.screenshot({ path: PNG, fullPage: true, scale: 'css' });
  await browser.close();

  for (const [label, file] of [['PDF', PDF], ['PNG', PNG]]) {
    const mb = (statSync(file).size / 1e6).toFixed(1);
    console.log(`[ok] ${label} -> ${file} (${mb} MB)`);
  }
  console.log(`[info] khổ in: ${WIDTH_MM} x ${HEIGHT_MM} mm (A0 dọc), xem trước PNG ở tỷ lệ ${PREVIEW_SCALE}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
