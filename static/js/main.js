// ============================================================================
// 静静学习系统 · 前端入口
// 统一装配各 composable，创建并挂载 Vue 3 应用，配置全局崩溃防线与键盘盲操。
// ============================================================================

import { useAudio } from './composables/useAudio.js';
import { useDrill, DRILL_CATEGORIES } from './composables/useDrill.js';
import { useChat } from './composables/useChat.js';
import { useNotebook } from './composables/useNotebook.js';

const { createApp, ref, onMounted, onUnmounted, watch } = window.Vue;

const app = createApp({
  setup() {
    // ---- 全局 UI 状态 ----
    const activeTab = ref('drill'); // 'drill' | 'talk' | 'report' | 'notebook' | 'settings'
    const showTargetText = ref(true); // 逐词看板“遮词考听力”开关
    const systemStatus = ref({
      ollama_connected: false,
      models: [],
      active_model: 'qwen2.5:1.5b',
      kokoro: { available: false }
    });
    const selectedModel = ref('qwen2.5:1.5b');
    const ttsEngine = ref('kokoro'); // 锁定本地离线引擎
    const ttsVoice = ref('af_heart'); // 锁定单一母语拟真音色

    // ---- 装配 composable ----
    const audio = useAudio();
    const notebook = useNotebook({ audio });
    const drill = useDrill({ audio });
    const chat = useChat({ audio, addScore: drill.addScore, selectedModel });

    // 语速切换后，静默预加载当前题在对应语速下的音频
    watch(() => audio.speechRate.value, () => {
      drill.prewarmCurrent();
    });

    // ---- 生命周期初始化 ----
    onMounted(async () => {
      try {
        const res = await fetch('/api/status');
        if (res.ok) {
          systemStatus.value = await res.json();
          if (systemStatus.value.active_model) {
            selectedModel.value = systemStatus.value.active_model;
          }
        }
      } catch (e) {
        console.warn('Status fetch failed:', e);
      }

      await drill.loadDrills();
      await chat.loadScenarios('freetalk');
    });

    // ---- 全局键盘盲操（生产力快捷键）----
    const isEditable = (el) => {
      if (!el) return false;
      const tag = el.tagName || '';
      return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || el.isContentEditable;
    };

    const handleKeydown = (e) => {
      if (isEditable(e.target)) return;

      // 数字键 1/2/3/4 —— 盲切 0.6x / 0.75x / 1.0x / 1.25x（全局）
      if (e.key === '1') { e.preventDefault(); audio.setSpeechRate(0.6); return; }
      if (e.key === '2') { e.preventDefault(); audio.setSpeechRate(0.75); return; }
      if (e.key === '3') { e.preventDefault(); audio.setSpeechRate(1.0); return; }
      if (e.key === '4') { e.preventDefault(); audio.setSpeechRate(1.25); return; }

      // 以下快捷键仅在造句研习区生效
      if (activeTab.value !== 'drill') return;

      if (e.key === ' ' || e.code === 'Space') {
        e.preventDefault();
        const d = drill.currentDrill.value;
        if (d && d.english) {
          audio.playTTS(d.english, 'target_' + d.id);
        }
      } else if (e.key === 'Enter') {
        e.preventDefault();
        drill.checkAnswer();
      } else if (e.key === 'ArrowRight') {
        e.preventDefault();
        drill.nextDrill();
      } else if (e.key === 'ArrowLeft') {
        e.preventDefault();
        drill.prevDrill();
      }
    };

    onMounted(() => window.addEventListener('keydown', handleKeydown));
    onUnmounted(() => window.removeEventListener('keydown', handleKeydown));

    // ---- 合并导出到模板作用域 ----
    return {
      // 全局
      activeTab,
      showTargetText,
      systemStatus,
      selectedModel,
      ttsEngine,
      ttsVoice,
      DRILL_CATEGORIES,

      // 音频
      ...audio,

      // 造句研习
      ...drill,

      // 口语对练
      ...chat,

      // 生词手账
      ...notebook
    };
  }
});

// ================= 全局崩溃防线 (Crash-Safe Error Boundary) =================
app.config.errorHandler = (err, instance, info) => {
  console.error('[Vue Global Error Handler]', err, info);
  try {
    const logs = JSON.parse(localStorage.getItem('jjs_error_logs') || '[]');
    logs.unshift({
      time: new Date().toISOString(),
      message: String(err && err.message ? err.message : err),
      info: info
    });
    localStorage.setItem('jjs_error_logs', JSON.stringify(logs.slice(0, 10)));
  } catch (e) { /* 忽略 */ }
};

window.addEventListener('unhandledrejection', (event) => {
  console.warn('[Global Unhandled Rejection]', event.reason);
});

window.addEventListener('error', (event) => {
  console.warn('[Global Window Error]', event.message);
});

app.mount('#app');
