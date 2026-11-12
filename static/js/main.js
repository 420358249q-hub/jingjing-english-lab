// ============================================================================
// 静静学习系统 · 前端入口
// 统一装配各 composable，创建并挂载 Vue 3 应用，配置全局崩溃防线与键盘盲操。
// ============================================================================

import { useAudio } from './composables/useAudio.js';
import { useDrill, DRILL_CATEGORIES } from './composables/useDrill.js';
import { useChat } from './composables/useChat.js';
import { useNotebook } from './composables/useNotebook.js';
import { useCourse } from './composables/useCourse.js';

const { createApp, ref, onMounted, onUnmounted, watch } = window.Vue;

const app = createApp({
  setup() {
    // ---- 全局 UI 状态 ----
    const activeTab = ref('course'); // 'course' | 'drill' | 'talk' | 'report' | 'notebook' | 'settings'
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
    const course = useCourse({
      audio,
      onScoreAdd: async (pts) => {
        drill.score.value += pts;
        drill.streak.value += 1;
        drill.persistScore();
        drill.persistStreak();
        try {
          await fetch('/api/profile/earn', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ stars: pts, coins: pts })
          });
        } catch (e) {}
      }
    });

    // 语速切换后，静默预加载当前题在对应语速下的音频
    watch(() => audio.speechRate.value, () => {
      drill.prewarmCurrent();
    });

    // ---- 版本升级推送与使用说明书 ----
    const CURRENT_VERSION = '2.2.0';
    const showUpdateModal = ref(false);
    const showManualModal = ref(false);

    const dismissUpdateModal = (openManual = false) => {
      try {
        localStorage.setItem('jjs_version_seen', CURRENT_VERSION);
      } catch (e) {}
      showUpdateModal.value = false;
      if (openManual) {
        showManualModal.value = true;
      }
    };

    // ---- 30 天自习连续打卡热力图数据 ----
    const activityHeatmap = ref([]);
    const generateActivityHeatmap = (streakCount = 0) => {
      const days = [];
      const now = new Date();
      for (let i = 29; i >= 0; i--) {
        const d = new Date(now);
        d.setDate(d.getDate() - i);
        const dateStr = d.toISOString().slice(0, 10);
        const isToday = i === 0;
        // 如果在连续打卡天数内，则判定为活跃
        const isActive = (i < streakCount) || isToday;
        const count = isToday ? Math.max(1, (drill.score.value % 15) + 3) : (isActive ? ((i % 4) + 1) * 3 : 0);
        days.push({
          date: dateStr,
          label: `${d.getMonth() + 1}月${d.getDate()}日`,
          count,
          level: count === 0 ? 0 : (count < 5 ? 1 : (count < 10 ? 2 : (count < 15 ? 3 : 4))),
          isToday
        });
      }
      activityHeatmap.value = days;
    };

    // ---- 生命周期初始化 ----
    onMounted(async () => {
      // 检查版本更新提醒
      try {
        const seenVer = localStorage.getItem('jjs_version_seen');
        if (seenVer !== CURRENT_VERSION) {
          showUpdateModal.value = true;
        }
      } catch (e) {}
      try {
        const [statusRes, profileRes] = await Promise.all([
          fetch('/api/status'),
          fetch('/api/profile')
        ]);
        if (statusRes.ok) {
          systemStatus.value = await statusRes.json();
          if (systemStatus.value.active_model) {
            selectedModel.value = systemStatus.value.active_model;
          }
        }
        if (profileRes.ok) {
          const prof = await profileRes.json();
          if (prof && typeof prof.stars === 'number') {
            drill.score.value = Math.max(drill.score.value, prof.stars);
            drill.streak.value = Math.max(drill.streak.value, prof.streak || 0);
            drill.persistScore();
            drill.persistStreak();
          }
        }
      } catch (e) {
        console.warn('Status/Profile fetch failed:', e);
      }

      generateActivityHeatmap(drill.streak.value);
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
      CURRENT_VERSION,
      showUpdateModal,
      showManualModal,
      dismissUpdateModal,
      activityHeatmap,

      // 音频
      ...audio,

      // 课程体系 (课程大厅/章节/工坊)
      course,
      ...course,

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
