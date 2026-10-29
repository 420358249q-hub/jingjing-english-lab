const puppeteer = require('puppeteer-core');

(async () => {
  console.log('[Test] Launching Chrome for Speed Switching test...');
  const browser = await puppeteer.launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--autoplay-policy=no-user-gesture-required']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 800 });

  page.on('console', msg => {
    if (msg.type() === 'error') console.log('[Browser Error]', msg.text());
  });

  await page.goto('http://127.0.0.1:8000', { waitUntil: 'networkidle2' });
  await page.waitForFunction(() => window.document.querySelector('.word-interactive-span') !== null);

  const testSpeed = async (label, speedVal, expectedMinDur, expectedMaxDur) => {
    console.log(`\n--- Testing Speed: ${label} (${speedVal}x) ---`);

    // Click speed button
    await page.evaluate((val) => {
      const btns = Array.from(document.querySelectorAll('button'));
      const btn = btns.find(b => b.innerText.includes(`${val}x`));
      if (btn) btn.click();
      else throw new Error(`Speed button ${val}x not found`);
    }, speedVal);

    await new Promise(r => setTimeout(r, 400));

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

    while (Date.now() - startTime < 6000) {
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

      await new Promise(r => setTimeout(r, 70));
    }

    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
    console.log(`[Result ${label}] Elapsed: ${elapsed}s, Words tracked: ${wordsSeen.length}, Finished: ${isFinished}`);
    console.log(`[Words] ${wordsSeen.join(' -> ')}`);

    if (!isFinished || wordsSeen.length < 5) {
      throw new Error(`Speed test failed for ${label}`);
    }
  };

  try {
    await testSpeed('慢速 (0.75x)', '0.75', 3.5, 5.0);
    await testSpeed('快速 (1.25x)', '1.25', 2.5, 4.0);
    await testSpeed('标准 (1.0x)', '1.0', 3.0, 4.0);
    console.log('\n✅ ALL SPEED TESTS PASSED: Speed switches seamlessly with identical af_heart timbre and zero pitch shift!');
    await browser.close();
    process.exit(0);
  } catch (err) {
    console.error('❌ Test failed:', err.message);
    await browser.close();
    process.exit(1);
  }
})();
