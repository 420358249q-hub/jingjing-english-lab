// ============================================================================
// useAudio — Web Audio 发音引擎（单例 AudioContext · 4 档语速 · 内存缓存 ·
// 静默预加载 · 25ms 硬件时钟逐词卡拉OK追踪）
//
// 硬性约束：Web Audio 播放端 source.playbackRate.value 恒等于 1.0，
// 语速由后端 Kokoro 神经网络原生控制，前端绝不重采样变调。
// ============================================================================

const Vue = window.Vue;

export function useAudio() {
  const { ref } = Vue;

  // ---- 语速（4 档：0.6x / 0.75x / 1.0x / 1.25x）----
  const speechRate = ref(1.0);

  // ---- 播放状态 ----
  const currentlyPlayingText = ref('');
  const isAudioPlaying = ref(false);
  const activeWordIndex = ref(-1);
  const activeAudioContext = ref('');
  const isWordStepping = ref(false);

  // ---- AudioContext 单例 ----
  let audioCtx = null;
  const getAudioContext = () => {
    if (!audioCtx) {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioCtx.state === 'suspended') {
      audioCtx.resume();
    }
    return audioCtx;
  };

  // ---- 轻量提示音（克制、不花哨）----
  const playAudioCue = (type) => {
    try {
      const ctx = getAudioContext();
      const now = ctx.currentTime;

      if (type === 'click') {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(800, now);
        osc.frequency.exponentialRampToValueAtTime(400, now + 0.05);
        gain.gain.setValueAtTime(0.08, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.05);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(now);
        osc.stop(now + 0.05);
      } else if (type === 'pop') {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(320, now);
        osc.frequency.exponentialRampToValueAtTime(640, now + 0.06);
        gain.gain.setValueAtTime(0.07, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.06);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(now);
        osc.stop(now + 0.06);
      } else if (type === 'correct') {
        [523.25, 659.25, 783.99].forEach((freq, idx) => {
          const osc = ctx.createOscillator();
          const gain = ctx.createGain();
          osc.type = 'sine';
          osc.frequency.setValueAtTime(freq, now + idx * 0.08);
          gain.gain.setValueAtTime(0.1, now + idx * 0.08);
          gain.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.08 + 0.26);
          osc.connect(gain);
          gain.connect(ctx.destination);
          osc.start(now + idx * 0.08);
          osc.stop(now + idx * 0.08 + 0.26);
        });
      } else if (type === 'error') {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(150, now);
        osc.frequency.linearRampToValueAtTime(95, now + 0.18);
        gain.gain.setValueAtTime(0.08, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.18);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(now);
        osc.stop(now + 0.18);
      }
    } catch (e) { /* 静默降级：提示音失败不影响主流程 */ }
  };

  // ---- 语速参数映射（与后端 parse_kokoro_speed 对齐）----
  const getRateParam = (rateValue) => {
    const num = parseFloat(rateValue) || 1.0;
    if (num <= 0.65) return '0.6';
    if (num <= 0.85) return '0.75';
    if (num >= 1.2) return '1.25';
    return '1.0';
  };

  const setSpeechRate = (rate) => {
    stopWordAudio();
    speechRate.value = rate;
    playAudioCue('click');
  };

  // ---- 单词清洗（逐词卡拉OK索引与词块装配共用）----
  const getCleanWords = (text) => {
    if (!text) return [];
    return text.replace(/[*#_`]/g, '')
      .replace(/[,.?!:;"'()]/g, '')
      .trim()
      .split(/\s+/)
      .filter((w) => w.length > 0);
  };

  const getWordSlotsForWords = (words, totalDuration) => {
    if (!words || !words.length) return [];
    const weights = words.map((w) => Math.max(w.length, 2));
    const totalWeight = weights.reduce((a, b) => a + b, 0);
    let cur = 0;
    return words.map((w, idx) => {
      const start = cur;
      const dur = (weights[idx] / totalWeight) * totalDuration;
      cur += dur;
      return { word: w, start, end: cur };
    });
  };

  // ---- 内存音频缓存 + 并发去重 ----
  const audioBufferCache = new Map();
  const audioFetchingPromises = new Map();

  const fetchAudioBuffer = async (text, mode = 'normal') => {
    const clean = text.replace(/[*#_`]/g, '').trim();
    if (!clean) return null;
    const rateParam = getRateParam(speechRate.value);
    const cacheKey = `${clean}|${mode}|${rateParam}`;
    if (audioBufferCache.has(cacheKey)) {
      return audioBufferCache.get(cacheKey);
    }
    if (audioFetchingPromises.has(cacheKey)) {
      return await audioFetchingPromises.get(cacheKey);
    }

    const p = (async () => {
      try {
        const res = await fetch('/api/tts', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            text: clean,
            engine: 'kokoro',
            voice: 'af_heart',
            rate: rateParam,
            mode: mode
          })
        });
        if (!res.ok) throw new Error(`TTS server error ${res.status}`);
        const arrayBuffer = await res.arrayBuffer();
        const ctx = getAudioContext();
        const audioBuffer = await ctx.decodeAudioData(arrayBuffer);
        audioBufferCache.set(cacheKey, audioBuffer);
        return audioBuffer;
      } finally {
        audioFetchingPromises.delete(cacheKey);
      }
    })();

    audioFetchingPromises.set(cacheKey, p);
    return await p;
  };

  // ---- 静默后台预加载（不触碰 AudioContext，仅预热磁盘缓存）----
  const prewarmAudio = (text, mode = 'normal') => {
    if (!text) return;
    const clean = text.replace(/[*#_`]/g, '').trim();
    if (!clean) return;
    const rateParam = getRateParam(speechRate.value);
    try {
      fetch('/api/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: clean,
          engine: 'kokoro',
          voice: 'af_heart',
          rate: rateParam,
          mode: mode
        })
      }).catch(() => {});
    } catch (e) { /* 静默 */ }
  };

  // ---- 停止所有音频与计时器 ----
  let wordAudioTimer = null;
  let currentSourceNode = null;
  let karaokeTimerId = null;

  const stopWordAudio = () => {
    isWordStepping.value = false;
    if (wordAudioTimer) {
      clearTimeout(wordAudioTimer);
      wordAudioTimer = null;
    }
    if (karaokeTimerId) {
      clearInterval(karaokeTimerId);
      karaokeTimerId = null;
    }
    if (currentSourceNode) {
      try {
        currentSourceNode.stop(0);
        currentSourceNode.disconnect();
      } catch (e) { /* 忽略 */ }
      currentSourceNode = null;
    }
    activeWordIndex.value = -1;
    activeAudioContext.value = '';
    currentlyPlayingText.value = '';
    isAudioPlaying.value = false;
  };

  // ---- 整句连读（Web Audio 原生播放 + 25ms 硬件时钟逐词高亮）----
  const playTTS = async (text, id = null, mode = 'normal') => {
    if (!text) return;
    const clean = text.replace(/[*#_`]/g, '').trim();
    if (!clean) return;

    stopWordAudio();

    const targetId = id || clean;
    currentlyPlayingText.value = targetId;
    activeAudioContext.value = targetId;
    isAudioPlaying.value = true;

    try {
      const audioBuffer = await fetchAudioBuffer(clean, mode);
      if (!audioBuffer) {
        stopWordAudio();
        return;
      }

      const ctx = getAudioContext();
      if (ctx.state === 'suspended') {
        await ctx.resume();
      }

      const source = ctx.createBufferSource();
      source.buffer = audioBuffer;
      // 严格锁定 1.0：保持音高与真人音色，杜绝花栗鼠/怪兽变调
      source.playbackRate.value = 1.0;

      const gainNode = ctx.createGain();
      gainNode.gain.value = 1.0;
      source.connect(gainNode);
      gainNode.connect(ctx.destination);
      currentSourceNode = source;

      const totalDuration = audioBuffer.duration;
      const startTime = ctx.currentTime;
      const words = getCleanWords(clean);
      const slots = getWordSlotsForWords(words, totalDuration);

      const onFinished = () => {
        if (karaokeTimerId) {
          clearInterval(karaokeTimerId);
          karaokeTimerId = null;
        }
        currentSourceNode = null;
        activeWordIndex.value = -1;
        currentlyPlayingText.value = '';
        isAudioPlaying.value = false;
        activeAudioContext.value = '';
      };

      source.onended = onFinished;

      if (slots.length > 0) {
        activeWordIndex.value = 0;
        karaokeTimerId = setInterval(() => {
          const elapsed = ctx.currentTime - startTime;
          if (elapsed >= totalDuration) {
            onFinished();
            return;
          }
          for (let i = 0; i < slots.length; i++) {
            if (elapsed >= slots[i].start && elapsed < slots[i].end) {
              if (activeWordIndex.value !== i) {
                activeWordIndex.value = i;
              }
              break;
            }
          }
        }, 25);
      }

      // 安全兜底：防止按钮/高亮卡死
      setTimeout(() => {
        if (currentlyPlayingText.value === targetId) {
          onFinished();
        }
      }, (totalDuration + 0.3) * 1000);

      source.start(0);
    } catch (err) {
      console.error('[Audio Playback Error]:', err);
      stopWordAudio();
    }
  };

  // ---- 逐词拆分慢速精读（读哪个亮哪个，词间 300ms 自然停顿）----
  const playSplitTTS = async (text, id = null) => {
    if (!text) return;
    const clean = text.replace(/[*#_`]/g, '').trim();
    const words = getCleanWords(clean);
    if (!words.length) return;

    stopWordAudio();

    const targetId = id || ('split_' + clean);
    currentlyPlayingText.value = targetId;
    activeAudioContext.value = targetId;
    isAudioPlaying.value = true;
    isWordStepping.value = true;

    // 并行预取全部单词，确保逐词迭代零等待
    try {
      await Promise.all(words.map((w) => fetchAudioBuffer(w)));
    } catch (e) { /* 忽略 */ }

    const ctx = getAudioContext();
    if (ctx.state === 'suspended') {
      try { await ctx.resume(); } catch (e) { /* 忽略 */ }
    }

    for (let i = 0; i < words.length; i++) {
      if (!isWordStepping.value) break;
      activeWordIndex.value = i;
      const currentWord = words[i];

      try {
        const audioBuffer = await fetchAudioBuffer(currentWord);
        if (audioBuffer && isWordStepping.value) {
          await new Promise((resolve) => {
            const source = ctx.createBufferSource();
            source.buffer = audioBuffer;
            source.playbackRate.value = 1.0;
            const gainNode = ctx.createGain();
            gainNode.gain.value = 1.0;
            source.connect(gainNode);
            gainNode.connect(ctx.destination);
            currentSourceNode = source;

            const wordDuration = audioBuffer.duration;
            const timer = setTimeout(resolve, (wordDuration + 0.05) * 1000);

            source.onended = () => {
              clearTimeout(timer);
              resolve();
            };
            source.start(0);
          });
        }
      } catch (err) {
        console.warn('[Word-Step Audio Error]:', err);
      }

      if (!isWordStepping.value) break;
      await new Promise((resolve) => {
        wordAudioTimer = setTimeout(resolve, 300);
      });
    }

    if (isWordStepping.value) {
      stopWordAudio();
    }
  };

  // ---- 单击单词发音（金色流光高亮）----
  const playSingleWord = async (word, index = -1) => {
    stopWordAudio();
    activeWordIndex.value = index;
    activeAudioContext.value = 'drill';
    playAudioCue('click');

    const cleanWord = word.replace(/[.,?!:;"'()]/g, '').trim() || word;
    await playTTS(cleanWord, 'single_' + cleanWord, 'normal');

    setTimeout(() => {
      if (activeWordIndex.value === index) {
        activeWordIndex.value = -1;
      }
    }, 800);
  };

  // ---- 单击词块发音 ----
  const playTokenAudio = (tokenText) => {
    stopWordAudio();
    playTTS(tokenText, 'token_' + tokenText, 'normal');
  };

  return {
    // 状态
    speechRate,
    currentlyPlayingText,
    isAudioPlaying,
    activeWordIndex,
    activeAudioContext,
    isWordStepping,

    // 方法
    setSpeechRate,
    getRateParam,
    getCleanWords,
    playTTS,
    playSplitTTS,
    playSingleWord,
    playTokenAudio,
    prewarmAudio,
    stopWordAudio,
    playAudioCue
  };
}
