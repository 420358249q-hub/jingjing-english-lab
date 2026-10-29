// ============================================================================
// useAudio — 桌面级发音引擎（Web Audio 硬件时钟 + HTML5 Audio 坚固双轨回退 ·
// 单例 AudioContext · 4 档原生无变调语速 · 内存缓存 · 25ms 逐词卡拉OK高亮）
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

  // ---- Web AudioContext 单例与主动激活防线 ----
  let audioCtx = null;
  const getAudioContext = () => {
    try {
      if (!audioCtx) {
        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
        if (AudioContextClass) {
          audioCtx = new AudioContextClass();
        }
      }
      if (audioCtx && audioCtx.state === 'suspended') {
        audioCtx.resume().catch(() => {});
      }
    } catch (e) {
      console.warn('[AudioContext init warning]:', e);
    }
    return audioCtx;
  };

  // 捕获阶段立刻激活音频上下文（解决 Quark/Safari/Chrome 等严格拦截无声问题）
  const unlockAudio = () => {
    getAudioContext();
  };
  ['click', 'keydown', 'pointerdown', 'touchstart'].forEach((evt) => {
    window.addEventListener(evt, unlockAudio, { capture: true, passive: true });
  });

  // ---- 轻量提示音 ----
  const playAudioCue = (type) => {
    try {
      const ctx = getAudioContext();
      if (!ctx || ctx.state !== 'running') return;
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
      }
    } catch (e) { /* 静默降级 */ }
  };

  // ---- 语速参数映射 ----
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

  // ---- 单词清洗 ----
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

  // ---- 双轨缓存系统（AudioBuffer + Blob URL，带 LRU 自动内存回收防泄漏） ----
  const audioDataCache = new Map();
  const audioFetchingPromises = new Map();
  const MAX_AUDIO_CACHE_SIZE = 60;

  const setAudioCache = (key, data) => {
    if (audioDataCache.has(key)) {
      audioDataCache.delete(key);
    } else if (audioDataCache.size >= MAX_AUDIO_CACHE_SIZE) {
      // 达到容量阈值，淘汰最旧的音频，显式释放底层 Blob URL 句柄，消除内存泄漏
      const oldestKey = audioDataCache.keys().next().value;
      const oldestData = audioDataCache.get(oldestKey);
      if (oldestData && oldestData.blobUrl) {
        try {
          URL.revokeObjectURL(oldestData.blobUrl);
        } catch (e) {}
      }
      audioDataCache.delete(oldestKey);
    }
    audioDataCache.set(key, data);
  };

  const clearAudioCache = () => {
    for (const data of audioDataCache.values()) {
      if (data && data.blobUrl) {
        try {
          URL.revokeObjectURL(data.blobUrl);
        } catch (e) {}
      }
    }
    audioDataCache.clear();
  };
  window.addEventListener('beforeunload', clearAudioCache);

  const fetchAudioData = async (text, mode = 'normal') => {
    const clean = text.replace(/[*#_`]/g, '').trim();
    if (!clean) return null;
    const rateParam = getRateParam(speechRate.value);
    const cacheKey = `${clean}|${mode}|${rateParam}`;

    if (audioDataCache.has(cacheKey)) {
      const data = audioDataCache.get(cacheKey);
      // 重新标记为最近使用
      audioDataCache.delete(cacheKey);
      audioDataCache.set(cacheKey, data);
      return data;
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

        // 1. 创建原生 Blob URL（坚不可摧的底层播放源）
        const blob = new Blob([arrayBuffer], { type: 'audio/wav' });
        const blobUrl = URL.createObjectURL(blob);

        // 2. 解码 Web AudioBuffer（支持毫秒级卡拉OK）
        let audioBuffer = null;
        try {
          const ctx = getAudioContext();
          if (ctx) {
            audioBuffer = await ctx.decodeAudioData(arrayBuffer.slice(0));
          }
        } catch (e) {
          console.warn('[Web Audio decode skipped, will use HTML5 Audio fallback]:', e);
        }

        const data = {
          audioBuffer,
          blobUrl,
          duration: audioBuffer ? audioBuffer.duration : 2.5
        };
        setAudioCache(cacheKey, data);
        return data;
      } finally {
        audioFetchingPromises.delete(cacheKey);
      }
    })();

    audioFetchingPromises.set(cacheKey, p);
    return await p;
  };

  // ---- 静默后台预加载 ----
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
  let currentHtmlAudio = null;
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
    if (currentHtmlAudio) {
      try {
        currentHtmlAudio.pause();
        currentHtmlAudio.currentTime = 0;
      } catch (e) { /* 忽略 */ }
      currentHtmlAudio = null;
    }
    activeWordIndex.value = -1;
    activeAudioContext.value = '';
    currentlyPlayingText.value = '';
    isAudioPlaying.value = false;
  };

  // ---- 整句连读（智能双轨播放：优先 Web Audio，降级 HTML5 Audio，绝不静音）----
  const playTTS = async (text, id = null, mode = 'normal') => {
    if (!text) return;
    const clean = text.replace(/[*#_`]/g, '').trim();
    if (!clean) return;

    // 同步唤醒音频硬件
    const ctx = getAudioContext();

    stopWordAudio();

    const targetId = id || clean;
    currentlyPlayingText.value = targetId;
    activeAudioContext.value = targetId;
    isAudioPlaying.value = true;

    try {
      const audioData = await fetchAudioData(clean, mode);
      if (!audioData) {
        stopWordAudio();
        return;
      }

      const words = getCleanWords(clean);
      const totalDuration = audioData.duration || 2.0;
      const slots = getWordSlotsForWords(words, totalDuration);

      const onFinished = () => {
        if (karaokeTimerId) {
          clearInterval(karaokeTimerId);
          karaokeTimerId = null;
        }
        currentSourceNode = null;
        currentHtmlAudio = null;
        activeWordIndex.value = -1;
        currentlyPlayingText.value = '';
        isAudioPlaying.value = false;
        activeAudioContext.value = '';
      };

      // 启动 25ms 硬件时钟卡拉OK高亮
      const startKaraoke = (getElapsedSec) => {
        if (slots.length > 0) {
          activeWordIndex.value = 0;
          karaokeTimerId = setInterval(() => {
            const elapsed = getElapsedSec();
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
      };

      // 轨道 A：如果 Web Audio 可用且已唤醒，采用 Web Audio 原生流
      if (ctx && ctx.state === 'running' && audioData.audioBuffer) {
        const source = ctx.createBufferSource();
        source.buffer = audioData.audioBuffer;
        source.playbackRate.value = 1.0;

        const gainNode = ctx.createGain();
        gainNode.gain.value = 1.0;
        source.connect(gainNode);
        gainNode.connect(ctx.destination);
        currentSourceNode = source;

        const startTime = ctx.currentTime;
        source.onended = onFinished;

        startKaraoke(() => ctx.currentTime - startTime);
        source.start(0);
      } else {
        // 轨道 B：HTML5 Audio 坚固回退（绕过浏览器严格的 AudioContext 拦截，100% 必响）
        const audio = new Audio(audioData.blobUrl);
        audio.playbackRate = 1.0;
        currentHtmlAudio = audio;
        audio.onended = onFinished;

        const startPerfTime = performance.now();
        startKaraoke(() => (performance.now() - startPerfTime) / 1000);

        await audio.play();
      }

      // 安全超时兜底
      setTimeout(() => {
        if (currentlyPlayingText.value === targetId) {
          onFinished();
        }
      }, (totalDuration + 0.5) * 1000);

    } catch (err) {
      console.error('[Audio Playback Error]:', err);
      // 终极应急：直接尝试 Audio 标签
      try {
        const data = await fetchAudioData(clean, mode);
        if (data && data.blobUrl) {
          const audio = new Audio(data.blobUrl);
          currentHtmlAudio = audio;
          audio.onended = stopWordAudio;
          await audio.play();
          return;
        }
      } catch (e2) {}
      stopWordAudio();
    }
  };

  // ---- 逐词拆分慢速精读 ----
  const playSplitTTS = async (text, id = null) => {
    if (!text) return;
    const clean = text.replace(/[*#_`]/g, '').trim();
    const words = getCleanWords(clean);
    if (!words.length) return;

    getAudioContext();
    stopWordAudio();

    const targetId = id || ('split_' + clean);
    currentlyPlayingText.value = targetId;
    activeAudioContext.value = targetId;
    isAudioPlaying.value = true;
    isWordStepping.value = true;

    try {
      await Promise.all(words.map((w) => fetchAudioData(w)));
    } catch (e) { /* 忽略 */ }

    for (let i = 0; i < words.length; i++) {
      if (!isWordStepping.value) break;
      activeWordIndex.value = i;
      const currentWord = words[i];

      try {
        const data = await fetchAudioData(currentWord);
        if (data && isWordStepping.value) {
          await new Promise((resolve) => {
            const ctx = getAudioContext();
            if (ctx && ctx.state === 'running' && data.audioBuffer) {
              const source = ctx.createBufferSource();
              source.buffer = data.audioBuffer;
              source.playbackRate.value = 1.0;
              source.connect(ctx.destination);
              currentSourceNode = source;
              source.onended = resolve;
              source.start(0);
            } else if (data.blobUrl) {
              const audio = new Audio(data.blobUrl);
              currentHtmlAudio = audio;
              audio.onended = resolve;
              audio.play().catch(resolve);
            } else {
              resolve();
            }
          });
        }
      } catch (e) {}

      if (!isWordStepping.value) break;
      await new Promise((r) => { wordAudioTimer = setTimeout(r, 260); });
    }

    stopWordAudio();
  };

  // ---- 单击单词发音 ----
  const playSingleWord = async (word, index = -1) => {
    getAudioContext();
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
    getAudioContext();
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
    playAudioCue,
    clearAudioCache
  };
}
