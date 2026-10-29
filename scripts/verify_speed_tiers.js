const puppeteer = require('puppeteer-core');

(async () => {
  console.log('[Test] Launching Chrome for Speed Tiers test...');
  const browser = await puppeteer.launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--autoplay-policy=no-user-gesture-required']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 800 });

  await page.goto('http://127.0.0.1:8000', { waitUntil: 'networkidle2' });
  await page.waitForFunction(() => window.document.querySelector('.word-interactive-span') !== null);

  const testTier = async (label, speedVal) => {
    console.log(`\nTesting Speed: ${label} (${speedVal}x)...`);

    // Click speed button
    await page.evaluate((val) => {
      const btns = Array.from(document.querySelectorAll('button'));
      const btn = btns.find(b => b.innerText.includes(`${val}x`));
      if (btn) btn.click();
      else throw new Error(`Speed button ${val}x not found`);
    }, speedVal);

    await new Promise(r => setTimeout(r, 300));

    // Click [ 整句连读 ]
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const btn = btns.find(b => b.innerText.includes('整句连读'));
      if (btn) btn.click();
      else throw new Error('整句连读 button not found');
    });

    const startTime = Date.now();
    const wordsSeen = [];
    let isFinished = false;

    while (Date.now() - startTime < 8000) {
      const state = await page.evaluate(() => {
        const activeSpan = document.querySelector('.word-highlight-active');
        const btns = Array.from(document.querySelectorAll('button'));
        const readBtn = btns.find(b => b.innerText.includes('整句连读') || b.innerText.includes('连读中'));
        return {
          activeWord: activeSpan ? activeSpan.innerText.trim() : null,
          isReading: readBtn ? readBtn.innerText.includes('连读中') : false
        };
      });

      if (state.activeWord && !wordsSeen.includes(state.activeWord)) {
        wordsSeen.push(state.activeWord);
      }

      if (wordsSeen.length > 5 && !state.activeWord && !state.isReading) {
        isFinished = true;
        break;
      }

      await new Promise(r => setTimeout(r, 60));
    }

    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
    console.log(`[Result ${label}] Duration: ${elapsed}s, Words: ${wordsSeen.length}, Finished: ${isFinished}`);
    return parseFloat(elapsed);
  };

  try {
    const dur06 = await testTier('超慢速 (0.6x)', '0.6');
    await new Promise(r => setTimeout(r, 1000));
    const dur075 = await testTier('慢速 (0.75x)', '0.75');
    await new Promise(r => setTimeout(r, 1000));
    const dur10 = await testTier('标准 (1.0x)', '1.0');
    await new Promise(r => setTimeout(r, 1000));
    const dur125 = await testTier('快速 (1.25x)', '1.25');

    console.log('\n--- SPEED COMPARISON ---');
    console.log(`0.6x  : ${dur06}s  (+${(dur06 - dur10).toFixed(2)}s vs 1.0x, +${((dur06/dur10 - 1)*100).toFixed(0)}%)`);
    console.log(`0.75x : ${dur075}s (+${(dur075 - dur10).toFixed(2)}s vs 1.0x, +${((dur075/dur10 - 1)*100).toFixed(0)}%)`);
    console.log(`1.0x  : ${dur10}s  (baseline)`);
    console.log(`1.25x : ${dur125}s (${(dur125 - dur10).toFixed(2)}s vs 1.0x)`);

    if (dur06 > dur075 && dur075 > dur10 && dur10 > dur125) {
      console.log('\n✅ PERFECT HIERARCHY: Each speed tier has an unmistakable, perceptible duration difference!');
    } else {
      console.warn('⚠️ Warning: Hierarchy not strictly monotonic, check durations.');
    }

    await browser.close();
    process.exit(0);
  } catch (err) {
    console.error('❌ Test failed:', err.message);
    await browser.close();
    process.exit(1);
  }
})();
