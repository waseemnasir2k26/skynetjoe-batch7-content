// render-batch7.js
// Playwright renderer: opens SKYNETJOE-BATCH7-CONTENT-ENGINE.html, screenshots each .post-card's
// .img-mock at 1080x1080 -> images/img-NN-<slug>.png matching CSV URLs.
//
// Usage:
//   npm i -D playwright
//   npx playwright install chromium
//   node scripts/render-batch7.js
//
// Output naming matches the CSV references (img-01-stack.png, img-02-agencies.png, ...).

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const HTML = path.resolve(__dirname, '..', '..', 'SKYNETJOE-BATCH7-CONTENT-ENGINE.html');
const OUT  = path.resolve(__dirname, '..', 'images');

// Maintain slug list in sync with the CSV /images/ references.
const SLUGS = [
  'stack', 'agencies', '9to5', 'vibecoding', 'savings',
  'freelancer', 'transformation', '5signs', 'nomoreclients', 'hierarchy',
  '48hrs', 'perfection', 'casestudies', 'soloagency', 'aiaudit',
];

(async () => {
  if (!fs.existsSync(HTML)) {
    console.error('Missing HTML preview:', HTML);
    process.exit(1);
  }
  fs.mkdirSync(OUT, { recursive: true });

  const browser = await chromium.launch();
  const ctx = await browser.newContext({
    viewport: { width: 1280, height: 1600 },
    deviceScaleFactor: 2,
  });
  const page = await ctx.newPage();
  await page.goto('file://' + HTML.replace(/\\/g, '/'));
  await page.waitForLoadState('networkidle');

  // Scope to first 15 image-pillar post-cards (the "IMAGE POSTS" section).
  const cards = await page.$$('section#images .post-card .img-mock');
  console.log(`Found ${cards.length} image-mock cards`);

  const count = Math.min(cards.length, SLUGS.length);
  for (let i = 0; i < count; i++) {
    const n = String(i + 1).padStart(2, '0');
    const file = path.join(OUT, `img-${n}-${SLUGS[i]}.png`);

    // Force 1080x1080 on the mock before screenshot (CSS square aspect already enforced in HTML).
    await cards[i].evaluate(el => {
      el.style.width  = '1080px';
      el.style.height = '1080px';
      el.style.maxWidth = '1080px';
      el.scrollIntoView({ block: 'center' });
    });
    await page.waitForTimeout(120);
    await cards[i].screenshot({ path: file, type: 'png' });
    console.log('  ->', path.basename(file));
  }

  await browser.close();
  console.log('\nDone. Rendered', count, 'PNGs to', OUT);
})().catch(err => {
  console.error(err);
  process.exit(1);
});
