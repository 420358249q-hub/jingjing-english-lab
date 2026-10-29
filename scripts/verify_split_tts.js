const puppeteer = require('puppeteer-core');

(async () => {
  console.log('[Test] Launching Chrome for Split TTS test...');
  const browser = await puppeteer.launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--autoplay-policy=no-user-gesture-required']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 800 });

  await page.goto('http://127.0.0.1:8000', { waitUntil: 'networkidle2' });
  await page.waitForFunction(() => window.document.querySelector('.word-interactive-span') !== null, { timeout: 10000 });

  console.log('[Test] Clicking [ 单词拆分精读 ] button...');
  await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('button'));
    const btn = btns.find(b => b.innerText.includes('单词拆分精读') || b.innerText.includes('拆分'));
    if (btn) btn.click();
    else throw new Error('单词拆分精读 button not found');
  });

  console.log('[Test] Sampling split word stepping in real-time...');
  const samples = [];
  const startTime = Date.now();
  let durationMs = 8000;

  while (Date.now() - startTime < durationMs) {
    const state = await page.evaluate(() => {
      const activeSpan = document.querySelector('.word-highlight-active');
      const activeText = activeSpan ? activeSpan.innerText.trim() : null;
      const btns = Array.from(document.querySelectorAll('button'));
      const splitBtn = btns.find(b => b.innerText.includes('单词拆分精读') || b.innerText.includes('逐词慢读中'));
      const btnText = splitBtn ? splitBtn.innerText.trim() : '';
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
      if (samples.length > 3 && !state.hasHighlight && state.btnText.includes('单词拆分精读')) {
        console.log('[Test] Completed early and cleanly!');
        break;
      }
    }

    await new Promise(r => setTimeout(r, 80));
  }

  const distinct = samples.filter(s => s.activeText).map(s => s.activeText);
  console.log('[Test] Distinct split words highlighted:', distinct);

  const finalState = await page.evaluate(() => {
    const activeSpan = document.querySelector('.word-highlight-active');
    const btns = Array.from(document.querySelectorAll('button'));
    const splitBtn = btns.find(b => b.innerText.includes('单词拆分精读') || b.innerText.includes('逐词慢读中'));
    return {
      activeText: activeSpan ? activeSpan.innerText.trim() : null,
      btnText: splitBtn ? splitBtn.innerText.trim() : ''
    };
  });
  console.log('[Test] Final state:', finalState);

  await browser.close();

  if (distinct.length >= 5 && finalState.btnText.includes('单词拆分精读') && !finalState.btnText.includes('慢读中')) {
    console.log('✅ TEST PASSED: Split TTS word stepping completed smoothly without getting stuck!');
    process.exit(0);
  } else {
    console.error('❌ TEST FAILED: Split TTS failed or got stuck.');
    process.exit(1);
  }
})();
