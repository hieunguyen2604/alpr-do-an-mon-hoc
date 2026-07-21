/**
 * Capture the interface screenshots used in the thesis, from the running stack.
 *
 * Why a script rather than a person with a snipping tool
 * -----------------------------------------------------
 * The previous screenshots went stale silently. They were taken when the sidebar
 * still had five entries and the home page was the dashboard; two scope changes
 * later they showed an interface that no longer exists, and nothing in the build
 * could notice. Re-taking them by hand has the same failure mode next time.
 *
 * This script also fixes what those images actually showed. They were captured on
 * empty pages -- an upload box and nothing else -- which demonstrates the layout
 * and none of the recognition. Here the image page is driven through a real
 * detection first, so the figure in the thesis shows a plate, its confidence, the
 * plate family and the background colour: the things the chapter is about.
 *
 * Usage
 * -----
 *   npm run screenshots            (from frontend/)
 *   node scripts/capture-screenshots.mjs --url http://localhost:5173
 *
 * The stack must already be running (`docker compose up -d`).
 *
 * Lives under `frontend/` rather than the repo-level `scripts/` because
 * Playwright is a frontend dev dependency: Node resolves `playwright` from the
 * importing file upward, so a copy in the repo root cannot see it.
 */

import { chromium } from 'playwright';
import { existsSync, mkdirSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const OUT_DIR = resolve(REPO_ROOT, 'docs/screenshots');

/**
 * 1280x800 rather than a laptop's native resolution: NFR-U4 promises the layout
 * works from 1366x768 up, and a figure captured near that floor is evidence for
 * the claim. A 2560px capture would prove nothing about the requirement and
 * would be unreadable once scaled into an A4 page.
 */
const VIEWPORT = { width: 1280, height: 800 };

/** A two-line yellow plate: exercises the hardest path and every new badge. */
const SAMPLE_IMAGE = resolve(REPO_ROOT, 'demo/images/2dong-1.png');

/** Short clip, so the live preview has boxes on screen before the capture. */
const SAMPLE_VIDEO = resolve(REPO_ROOT, 'demo/demo-video.mp4');

const PAGES = [
  { path: '/', name: 'image-detection', label: 'Nhận dạng ảnh' },
  { path: '/video', name: 'video-detection', label: 'Nhận dạng video' },
  { path: '/history', name: 'history', label: 'Lịch sử' },
];

/**
 * Wait for the network to settle, then a beat more for layout to stabilise.
 *
 * `networkidle` alone still catches the moment a chart or image has arrived but
 * not yet been laid out, which shows up as a half-drawn figure.
 *
 * @param {import('playwright').Page} page - The page to settle.
 */
async function settle(page) {
  await page.waitForLoadState('networkidle').catch(() => {});
  await page.waitForTimeout(700);
}

/**
 * Drive the image page through one real detection so the capture shows results.
 *
 * @param {import('playwright').Page} page - A page already on the home route.
 * @returns {Promise<boolean>} Whether a result appeared.
 */
async function runDetection(page) {
  if (!existsSync(SAMPLE_IMAGE)) {
    console.log(`  [warn] sample image missing: ${SAMPLE_IMAGE}`);
    return false;
  }

  const input = page.locator('input[type="file"]').first();
  await input.setInputFiles(SAMPLE_IMAGE);
  await page.waitForTimeout(500);

  // The button label is the user-facing Vietnamese string, so this also fails
  // loudly if the interface is ever relabelled.
  const button = page.getByRole('button', { name: /Nhận dạng/i }).first();
  if (!(await button.isVisible().catch(() => false))) {
    console.log('  [warn] recognise button not found');
    return false;
  }
  await button.click();

  // Wait for the *absence* of the progress message, not the presence of the
  // results heading. The heading is the panel's static title and is on screen
  // from the first paint, so waiting for it returns immediately and captures a
  // spinner -- which is exactly what the first version of this script produced.
  //
  // Recognition is CPU-bound: about half a second warm, but the first request
  // after a container restart also pays the model load.
  try {
    await page
      .getByText(/Đang phát hiện và đọc biển số/i)
      .first()
      .waitFor({ state: 'hidden', timeout: 90_000 });
  } catch {
    console.log('  [warn] still processing after 90s');
    return false;
  }

  // Then confirm a plate really rendered, rather than an error panel.
  try {
    await page.getByText(/Độ tin cậy OCR/i).first().waitFor({ timeout: 15_000 });
  } catch {
    console.log('  [warn] finished but no plate card rendered');
    return false;
  }
  await page.waitForTimeout(900);
  return true;
}

/**
 * Load a video and let the live preview settle on a frame with boxes drawn.
 *
 * Captures the page mid-detection on purpose. An empty upload box demonstrates
 * the layout and nothing about the system; a frame with a plate boxed and
 * labelled is what the chapter is about.
 *
 * @param {import('playwright').Page} page - A page already on the video route.
 * @returns {Promise<boolean>} Whether the preview produced a box.
 */
async function startLivePreview(page) {
  if (!existsSync(SAMPLE_VIDEO)) {
    console.log(`  [warn] sample video missing: ${SAMPLE_VIDEO}`);
    return false;
  }

  await page.locator('input[type="file"]').first().setInputFiles(SAMPLE_VIDEO);

  try {
    await page.getByText(/Xem trực tiếp/i).first().waitFor({ timeout: 30_000 });
  } catch {
    console.log('  [warn] live preview panel did not appear');
    return false;
  }

  // Detection no longer starts on its own -- choosing a file shows the frame,
  // and the user asks for inference explicitly. The capture has to make that
  // same request, or the figure would show an idle player with an empty log.
  try {
    await page.getByRole('button', { name: /Chạy nhận dạng/i }).click({ timeout: 10_000 });
  } catch {
    console.log('  [warn] could not press the run button');
    return false;
  }

  // Play a couple of seconds so the frame on screen contains a vehicle, then
  // pause: a capture taken mid-motion shows a blurred plate and a stale box.
  //
  // Every step here is load-bearing, and the previous version had none of them.
  // It set `currentTime` immediately, before the blob URL had produced any
  // metadata, so the seek was discarded and the element sat at 0:00; and it
  // called `play()` unmuted, which headless Chromium refuses without a user
  // gesture. The preview then captured nothing at all -- the figure showed
  // "Đã gửi 0 khung" over a black player, which is a screenshot of the feature
  // not working.
  await page.evaluate(async () => {
    const video = document.querySelector('video');
    if (video === null) return;

    // Autoplay is only permitted for muted media without a user gesture.
    video.muted = true;

    if (video.readyState < 1) {
      await new Promise((resolve) => {
        video.addEventListener('loadedmetadata', resolve, { once: true });
        setTimeout(resolve, 5000);
      });
    }

    video.currentTime = 5;
    await new Promise((resolve) => {
      video.addEventListener('seeked', resolve, { once: true });
      setTimeout(resolve, 5000);
    });

    await video.play().catch(() => {});
  });

  // Long enough for several frames to complete a round trip: capture fires
  // every 450 ms and inference costs roughly 400 ms, so this is about a dozen
  // attempts and enough log lines to be worth showing.
  await page.waitForTimeout(9000);
  await page.evaluate(() => document.querySelector('video')?.pause());
  await page.waitForTimeout(1500);

  return true;
}

/**
 * Scroll the live preview to the top of the viewport.
 *
 * The upload card alone fills an 800 px viewport, so a capture taken at scroll
 * position zero shows the dropzone and cuts off the boxed plate and the log --
 * the two things this figure exists to show.
 *
 * Called *after* the general scroll-to-top reset rather than inside
 * {@link startLivePreview}, because that reset would otherwise undo it. The
 * ordering is the whole point: the first pass I wrote scrolled here and then
 * had the reset put it straight back, producing a screenshot identical to the
 * one before the change.
 *
 * @param {import('playwright').Page} page - A page on the video route.
 */
async function scrollToLivePreview(page) {
  await page.evaluate(() => {
    const heading = [...document.querySelectorAll('h2')].find((node) =>
      node.textContent?.includes('Xem trực tiếp'),
    );
    const card = heading?.closest('div[class*="rounded"]') ?? heading;
    card?.scrollIntoView({ block: 'start' });
  });
  await page.waitForTimeout(800);
}

async function main() {
  const urlArg = process.argv.indexOf('--url');
  const base = urlArg >= 0 ? process.argv[urlArg + 1] : 'http://localhost:5173';

  mkdirSync(OUT_DIR, { recursive: true });

  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: VIEWPORT,
    deviceScaleFactor: 2, // Legible when scaled down into a printed page.
    locale: 'vi-VN',
  });
  const page = await context.newPage();

  let failures = 0;
  for (const spec of PAGES) {
    const url = `${base}${spec.path}`;
    process.stdout.write(`  ${spec.label.padEnd(22)} ${url}\n`);
    try {
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30_000 });
      await settle(page);

      if (spec.path === '/') {
        const ok = await runDetection(page);
        if (!ok) failures += 1;
      }

      if (spec.path === '/video') {
        const ok = await startLivePreview(page);
        if (!ok) failures += 1;
      }

      // Viewport rather than fullPage. A full-page capture renders sticky
      // elements at their pinned offset, so the header and sidebar came out
      // drawn over the content -- an artefact no user ever sees. The viewport
      // shot is what the interface actually looks like, which is the point of
      // putting it in a thesis.
      await page.evaluate(() => window.scrollTo(0, 0));
      await page.waitForTimeout(250);
      if (spec.path === '/video') {
        await scrollToLivePreview(page);
      }
      const out = resolve(OUT_DIR, `${spec.name}.png`);
      await page.screenshot({ path: out });
      console.log(`    -> ${out}`);
    } catch (error) {
      failures += 1;
      console.log(`    [error] ${error.message.split('\n')[0]}`);
    }
  }

  await browser.close();

  if (failures > 0) {
    console.log(`\n  ${failures} trang gap van de - kiem tra stack co dang chay khong.`);
    process.exitCode = 1;
  } else {
    console.log('\n  Chup xong 3 anh giao dien.');
  }
}

main();
