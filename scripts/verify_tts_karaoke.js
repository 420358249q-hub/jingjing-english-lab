const puppeteer = require('puppeteer-core');
const fs = require('fs');

(async () => {
  console.log('[Test] Launching Chrome...');
  const browser = await puppeteer.launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--autoplay-policy=no-user-gesture-required']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 800 });

  console.log('[Test] Navigating to http://127.0.0.1:8000 ...');
  await page.goto('http://127.0.0.1:8000', { waitUntil: 'networkidle2' });

  // Wait for Vue mount and drills load
  await page.waitForFunction(() => window.document.querySelector('.word-interactive-span') !== null, { timeout: 10000 });
  console.log('[Test] Vue mounted successfully.');

  // Check drill words
  const words = await page.evaluate(() => {
    const spans = Array.from(document.querySelectorAll('.word-interactive-span'));
    return spans.map(s => s.innerText.trim());
  });
  console.log('[Test] Current drill words on screen:', words);

  // Click [ 整句连读 ] button
  console.log('[Test] Clicking [ 整句连读 ] button...');
  const playButtonSelector = 'button:has(i.ph-speaker-high)';
  await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('button'));
    const btn = btns.find(b => b.innerText.includes('整句连读'));
    if (btn) btn.click();
    else throw new Error('整句连读 button not found');
  });

  // Sample activeWordIndex and highlighted word every 100ms for 4 seconds
  console.log('[Test] Sampling word highlighting in real-time...');
  const samples = [];
  const startTime = Date.now();
  let durationMs = 4200;

  while (Date.now() - startTime < durationMs) {
    const state = await page.evaluate(() => {
      const activeSpan = document.querySelector('.word-highlight-active');
      const activeText = activeSpan ? activeSpan.innerText.trim() : null;
      const btns = Array.from(document.querySelectorAll('button'));
      const readBtn = btns.find(b => b.innerText.includes('整句连读') || b.innerText.includes('连读中'));
      const btnText = readBtn ? readBtn.innerText.trim() : '';
      return {
        activeText,
        btnText,
        hasHighlight: !!activeSpan
      };
    });

    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
    if (samples.length === 0 || samples[samples.length - 1].activeText !== state.activeText) {
      console.log(`  [+${elapsed}s] Active Word: "${state.activeText || '(none)'}", Button: "${state.btnText}"`);
      samples.push({ elapsed, ...state });
    }

    await new Promise(r => setTimeout(r, 80));
  }

  // Take screenshot
  await page.screenshot({ path: 'scripts/karaoke_verified.png' });
  console.log('[Test] Screenshot saved to scripts/karaoke_verified.png');

  // Verify transitions
  const highlightedWords = samples.filter(s => s.activeText).map(s => s.activeText);
  console.log('[Test] Distinct words highlighted in sequence:', highlightedWords);

  const finalState = await page.evaluate(() => {
    const activeSpan = document.querySelector('.word-highlight-active');
    const btns = Array.from(document.querySelectorAll('button'));
    const readBtn = btns.find(b => b.innerText.includes('整句连读') || b.innerText.includes('连读中'));
    return {
      activeText: activeSpan ? activeSpan.innerText.trim() : null,
      btnText: readBtn ? readBtn.innerText.trim() : ''
    };
  });

  console.log('[Test] Final state:', finalState);

  await browser.close();

  if (highlightedWords.length > 2 && finalState.btnText.includes('整句连读') && !finalState.btnText.includes('连读中')) {
    console.log('✅ TEST PASSED: Karaoke progressed word-by-word and completed cleanly without getting stuck!');
    process.exit(0);
  } else {
    console.error('❌ TEST FAILED: Highlighting did not progress as expected.');
    process.exit(1);
  }
})();
