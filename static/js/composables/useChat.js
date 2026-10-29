// ============================================================================
// useChat — 口语对练引擎（成人场景切换 / SSE 流式打字机 / 录音与 Whisper 转写 /
// 6 维口语诊断报告）
// ============================================================================

const Vue = window.Vue;

const CHAT_KEY_PREFIX = 'jjs_chat_';

function loadChatHistory(id) {
  const keys = [CHAT_KEY_PREFIX + id, 'wxs_chat_' + id];
  for (const key of keys) {
    try {
      const saved = localStorage.getItem(key);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          // 迁移到新 key
          if (key !== CHAT_KEY_PREFIX + id) localStorage.setItem(CHAT_KEY_PREFIX + id, saved);
          return parsed;
        }
      }
    } catch (e) { /* 忽略 */ }
  }
  return null;
}

function persistChatHistory(id, messages) {
  try {
    localStorage.setItem(CHAT_KEY_PREFIX + id, JSON.stringify(messages));
  } catch (e) { /* 忽略 */ }
}

export function useChat({ audio, addScore, selectedModel } = {}) {
  const { ref, computed, nextTick } = Vue;

  const scenarios = ref([]);
  const activeScenarioId = ref('freetalk');
  const chatMessages = ref([]);
  const textInput = ref('');
  const liveTranscript = ref('');
  const isSending = ref(false);
  const isRecording = ref(false);
  const recordDuration = ref(0);
  const chatContainer = ref(null);
  const waveformCanvas = ref(null);

  const currentScenario = computed(() => {
    return scenarios.value.find((s) => s.id === activeScenarioId.value) || scenarios.value[0] || null;
  });

  const formattedDuration = computed(() => {
    const m = Math.floor(recordDuration.value / 60).toString().padStart(2, '0');
    const s = (recordDuration.value % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  });

  const scrollToBottom = () => {
    nextTick(() => {
      if (chatContainer.value) {
        chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
      }
    });
  };

  const selectScenario = (id, forceReset = false) => {
    activeScenarioId.value = id;
    const scen = scenarios.value.find((s) => s.id === id);
    if (!scen) return;

    if (!forceReset) {
      const saved = loadChatHistory(id);
      if (saved) {
        chatMessages.value = saved;
        scrollToBottom();
        return;
      }
    }

    chatMessages.value = [
      {
        role: 'assistant',
        name: scen.partner_name,
        avatar: scen.partner_avatar,
        content: scen.initial_message,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ];
    persistChatHistory(id, chatMessages.value);
    if (audio && audio.playTTS) audio.playTTS(scen.initial_message);
  };

  const sendMessage = async (overrideContent = null) => {
    const content = (overrideContent || textInput.value || liveTranscript.value).trim();
    if (!content || isSending.value) return;

    textInput.value = '';
    liveTranscript.value = '';
    isSending.value = true;
    if (audio && audio.playAudioCue) audio.playAudioCue('click');

    chatMessages.value.push({
      role: 'user',
      name: 'You',
      avatar: '我',
      content: content,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    });
    scrollToBottom();

    const scen = currentScenario.value;
    const assistantMsg = {
      role: 'assistant',
      name: scen ? scen.partner_name : 'Partner',
      avatar: scen ? scen.partner_avatar : 'A',
      content: '',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    chatMessages.value.push(assistantMsg);
    scrollToBottom();

    try {
      const payload = {
        scenario: activeScenarioId.value,
        model: (selectedModel && selectedModel.value) || 'qwen2.5:1.5b',
        messages: chatMessages.value
          .filter((m) => m.content && m !== assistantMsg)
          .map((m) => ({ role: m.role, content: m.content }))
      };

      const res = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok && res.body) {
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n\n');
          buffer = lines.pop();

          for (const line of lines) {
            const trimmed = line.trim();
            if (trimmed === 'data: [DONE]') break;
            if (trimmed.startsWith('data: ')) {
              try {
                const chunk = JSON.parse(trimmed.slice(6));
                if (chunk.delta) {
                  assistantMsg.content += chunk.delta;
                  scrollToBottom();
                }
              } catch (pe) { /* 忽略残缺分片 */ }
            }
          }
        }
      }

      if (!assistantMsg.content.trim()) {
        assistantMsg.content = 'That sounds interesting, 静静! What do you think we should try next?';
      }

      scrollToBottom();
      if (audio && audio.playTTS) audio.playTTS(assistantMsg.content);
      if (addScore) addScore(10);
    } catch (err) {
      console.error('[Chat Stream Error]:', err);
      if (!assistantMsg.content.trim()) {
        assistantMsg.content = 'I hear you, 静静! Tell me a bit more about that.';
        if (audio && audio.playTTS) audio.playTTS(assistantMsg.content);
      }
    } finally {
      isSending.value = false;
      persistChatHistory(activeScenarioId.value, chatMessages.value);
    }
  };

  // ---- 录音控制（HTML5 MediaRecorder + 离线 Whisper 兜底转写）----
  let mediaStream = null;
  let mediaRecorder = null;
  let audioChunks = [];
  let recordInterval = null;
  let speechRecognizer = null;

  // ---- 高精度波形（AnalyserNode 实时频谱）----
  let waveCtx = null;
  let waveSource = null;
  let waveAnalyser = null;
  let waveFreq = null;
  let waveRaf = null;

  const drawWaveform = () => {
    const canvas = waveformCanvas.value;
    if (!canvas) return;
    const g = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;

    const frame = () => {
      waveRaf = requestAnimationFrame(frame);
      if (!waveAnalyser) return;
      waveAnalyser.getByteFrequencyData(waveFreq);
      g.clearRect(0, 0, w, h);
      const bars = 52;
      const gap = 2;
      const barW = (w - gap * (bars - 1)) / bars;
      for (let i = 0; i < bars; i++) {
        const idx = Math.floor((i * waveFreq.length) / bars);
        const v = waveFreq[idx] / 255;
        const bh = Math.max(2, v * h);
        const x = i * (barW + gap);
        const y = (h - bh) / 2;
        g.fillStyle = v > 0.72 ? 'rgba(212, 175, 55, 0.95)' : 'rgba(139, 92, 246, 0.75)';
        g.beginPath();
        if (typeof g.roundRect === 'function') {
          g.roundRect(x, y, barW, bh, 1.5);
        } else {
          g.rect(x, y, barW, bh);
        }
        g.fill();
      }
    };
    frame();
  };

  const startWaveform = (stream) => {
    try {
      if (!waveCtx) waveCtx = new (window.AudioContext || window.webkitAudioContext)();
      if (waveCtx.state === 'suspended') waveCtx.resume();
      waveSource = waveCtx.createMediaStreamSource(stream);
      waveAnalyser = waveCtx.createAnalyser();
      waveAnalyser.fftSize = 256;
      waveAnalyser.smoothingTimeConstant = 0.8;
      waveSource.connect(waveAnalyser);
      waveFreq = new Uint8Array(waveAnalyser.frequencyBinCount);
      waveRaf = requestAnimationFrame(drawWaveform);
    } catch (e) { /* 降级：波形失败不影响录音 */ }
  };

  const stopWaveform = () => {
    if (waveRaf) { cancelAnimationFrame(waveRaf); waveRaf = null; }
    if (waveSource) { try { waveSource.disconnect(); } catch (e) { /* 忽略 */ } waveSource = null; }
    waveAnalyser = null;
    const canvas = waveformCanvas.value;
    if (canvas) {
      try { canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height); } catch (e) { /* 忽略 */ }
    }
  };

  const startLiveSpeech = () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return;
    try {
      if (speechRecognizer) {
        try { speechRecognizer.abort(); } catch (e) { /* 忽略 */ }
      }
      speechRecognizer = new SR();
      speechRecognizer.lang = 'en-US';
      speechRecognizer.continuous = true;
      speechRecognizer.interimResults = true;

      speechRecognizer.onresult = (e) => {
        let str = '';
        for (let i = e.resultIndex; i < e.results.length; i++) {
          str += e.results[i][0].transcript;
        }
        if (str.trim()) {
          liveTranscript.value = str;
          textInput.value = str;
        }
      };

      speechRecognizer.onend = () => {
        if (isRecording.value && speechRecognizer) {
          try { speechRecognizer.start(); } catch (e) { /* 忽略 */ }
        }
      };

      speechRecognizer.start();
    } catch (e) {
      console.warn('[SpeechRecognition Live Error]:', e);
    }
  };

  const stopLiveSpeech = () => {
    if (speechRecognizer) {
      try { speechRecognizer.stop(); } catch (e) { /* 忽略 */ }
    }
  };

  const toggleRecording = async () => {
    if (!isRecording.value) {
      try {
        mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioChunks = [];
        mediaRecorder = new MediaRecorder(mediaStream);
        mediaRecorder.ondataavailable = (e) => {
          if (e.data.size > 0) audioChunks.push(e.data);
        };
        mediaRecorder.start(250);

        isRecording.value = true;
        recordDuration.value = 0;
        liveTranscript.value = '';
        if (recordInterval) clearInterval(recordInterval);
        recordInterval = setInterval(() => { recordDuration.value++; }, 1000);
        if (audio && audio.playAudioCue) audio.playAudioCue('pop');
        startWaveform(mediaStream);
        startLiveSpeech();
      } catch (err) {
        console.error('Microphone access error:', err);
        alert('麦克风无法访问：请在浏览器地址栏（或左上角锁头处）允许本页面使用麦克风权限。');
      }
    } else {
      isRecording.value = false;
      if (recordInterval) clearInterval(recordInterval);
      if (audio && audio.playAudioCue) audio.playAudioCue('click');

      if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
      }
      if (mediaStream) {
        mediaStream.getTracks().forEach((t) => t.stop());
      }
      stopWaveform();
      stopLiveSpeech();

      setTimeout(async () => {
        const recognized = textInput.value.trim() || liveTranscript.value.trim();
        if (recognized.length > 0) {
          sendMessage(recognized);
        } else if (audioChunks.length > 0) {
          isSending.value = true;
          const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
          const formData = new FormData();
          formData.append('file', audioBlob, 'record.webm');
          try {
            const res = await fetch('/api/transcribe', { method: 'POST', body: formData });
            const data = await res.json();
            if (data.status === 'success' && data.text.trim()) {
              sendMessage(data.text);
            } else {
              isSending.value = false;
            }
          } catch (e) {
            console.error('Transcribe failed:', e);
            isSending.value = false;
          }
        }
      }, 200);
    }
  };

  const cancelRecording = () => {
    isRecording.value = false;
    if (recordInterval) clearInterval(recordInterval);
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop();
    }
    if (mediaStream) {
      mediaStream.getTracks().forEach((t) => t.stop());
    }
    stopWaveform();
    stopLiveSpeech();
    textInput.value = '';
    liveTranscript.value = '';
    if (audio && audio.playAudioCue) audio.playAudioCue('click');
  };

  // ---- 6 维口语诊断报告 ----
  const currentReport = ref(null);
  const isEvaluating = ref(false);

  const generateEvaluation = async () => {
    if (!chatMessages.value.length) return;
    isEvaluating.value = true;
    if (audio && audio.playAudioCue) audio.playAudioCue('click');

    try {
      const payload = {
        conversation: chatMessages.value.map((m) => ({ role: m.role, content: m.content })),
        model: (selectedModel && selectedModel.value) || 'qwen2.5:1.5b'
      };
      const res = await fetch('/api/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      currentReport.value = data.report || null;
    } catch (err) {
      console.error('Evaluation error:', err);
    } finally {
      isEvaluating.value = false;
    }
  };

  // ---- 拉取场景 ----
  const loadScenarios = async (defaultId = 'freetalk') => {
    try {
      const res = await fetch('/api/scenarios');
      if (res.ok) {
        scenarios.value = await res.json();
        selectScenario(defaultId);
      }
    } catch (e) {
      console.warn('Scenarios fetch failed:', e);
    }
  };

  return {
    // 状态
    scenarios,
    activeScenarioId,
    currentScenario,
    chatMessages,
    textInput,
    liveTranscript,
    isSending,
    isRecording,
    recordDuration,
    formattedDuration,
    chatContainer,
    waveformCanvas,

    // 方法
    loadScenarios,
    selectScenario,
    sendMessage,
    toggleRecording,
    cancelRecording,

    // 报告
    currentReport,
    isEvaluating,
    generateEvaluation
  };
}
