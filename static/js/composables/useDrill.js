// ============================================================================
// useDrill — 造句研习引擎（题库筛选 / 词块装配 / 答案校验 / 语法解构 /
// 学习积分与连胜 Streak / 自建题库生成）
// ============================================================================

const Vue = window.Vue;

const SCORE_KEY = 'jjs_score';
const STREAK_KEY = 'jjs_streak';

// 成年人五大题库分类（与后端 adultify 后的 category 对齐）
export const DRILL_CATEGORIES = [
  { id: 'all', label: '全部题库', icon: 'squares-four' },
  { id: 'daily', label: '日常社交', icon: 'chat-circle-dots' },
  { id: 'workplace', label: '职场沟通', icon: 'briefcase' },
  { id: 'travel', label: '出行出境', icon: 'airplane' },
  { id: 'grammar', label: '语法攻坚', icon: 'tree-structure' },
  { id: 'custom', label: '自定义精选', icon: 'sparkle' }
];

function migrateNumber(key, legacyKey, fallback) {
  try {
    let raw = localStorage.getItem(key);
    if (raw === null || raw === '') {
      const legacy = localStorage.getItem(legacyKey);
      if (legacy !== null && legacy !== '') {
        raw = legacy;
        localStorage.setItem(key, legacy);
      }
    }
    const n = parseInt(raw, 10);
    return Number.isFinite(n) ? n : fallback;
  } catch (e) {
    return fallback;
  }
}

export function useDrill({ audio } = {}) {
  const { ref, computed } = Vue;

  // ---- 题库 ----
  const allDrills = ref([]);
  const selectedCategory = ref('all');
  const currentDrillIndex = ref(0);
  const userTokens = ref([]);
  const availableTokens = ref([]);
  const drillFeedback = ref(null); // null | 'correct' | 'wrong'
  const isShaking = ref(false);
  const showBreakdown = ref(false);

  // ---- 积分与连胜 ----
  const score = ref(migrateNumber(SCORE_KEY, 'wxs_score', 0));
  const streak = ref(migrateNumber(STREAK_KEY, 'wxs_streak', 0));

  const persistScore = () => {
    try { localStorage.setItem(SCORE_KEY, String(score.value)); } catch (e) { /* 忽略 */ }
  };
  const persistStreak = () => {
    try { localStorage.setItem(STREAK_KEY, String(streak.value)); } catch (e) { /* 忽略 */ }
  };

  const filteredDrills = computed(() => {
    if (selectedCategory.value === 'all') return allDrills.value;
    return allDrills.value.filter((d) => d.category === selectedCategory.value);
  });

  const currentDrill = computed(() => {
    return filteredDrills.value[currentDrillIndex.value] || null;
  });

  // 逐词卡拉OK与装配共用的干净单词序列
  const currentDrillWords = computed(() => {
    if (!currentDrill.value) return [];
    return currentDrill.value.english
      .replace(/[,.?!:;"'()]/g, '')
      .split(/\s+/)
      .filter((w) => w.trim());
  });

  const getCategoryCount = (cat) => {
    if (cat === 'all') return allDrills.value.length;
    return allDrills.value.filter((d) => d.category === cat).length;
  };

  // ---- 静默预加载当前 + 下一题 + 逐词音频 ----
  const prewarmCurrent = () => {
    const drill = currentDrill.value;
    if (!drill) return;
    if (audio && audio.prewarmAudio) {
      if (drill.english) audio.prewarmAudio(drill.english);
      const next = filteredDrills.value[currentDrillIndex.value + 1];
      if (next && next.english) audio.prewarmAudio(next.english);
      const words = currentDrillWords.value;
      if (words && words.length) words.forEach((w) => audio.prewarmAudio(w));
    }
  };

  const initDrill = (index = 0) => {
    if (audio && audio.stopWordAudio) audio.stopWordAudio();
    if (!filteredDrills.value.length) return;
    currentDrillIndex.value = Math.max(0, Math.min(index, filteredDrills.value.length - 1));
    const drill = currentDrill.value;
    if (!drill) return;

    userTokens.value = [];
    drillFeedback.value = null;
    showBreakdown.value = false;

    const shuffled = [...drill.tokens].map((text, idx) => ({
      id: `${drill.id}-${idx}`,
      text: text,
      used: false
    })).sort(() => Math.random() - 0.5);

    availableTokens.value = shuffled;
    prewarmCurrent();
  };

  // ---- 词块装配槽 ----
  const addTokenToSlot = (tokenObj) => {
    if (tokenObj.used) return;
    if (audio && audio.playAudioCue) audio.playAudioCue('click');
    tokenObj.used = true;
    userTokens.value.push(tokenObj);
    drillFeedback.value = null;
  };

  const removeTokenFromSlot = (index) => {
    if (audio && audio.playAudioCue) audio.playAudioCue('pop');
    const removed = userTokens.value.splice(index, 1)[0];
    if (removed) removed.used = false;
    drillFeedback.value = null;
  };

  const shuffleTokens = () => {
    if (audio && audio.playAudioCue) audio.playAudioCue('click');
    userTokens.value.forEach((t) => { t.used = false; });
    userTokens.value = [];
    availableTokens.value.sort(() => Math.random() - 0.5);
    drillFeedback.value = null;
  };

  const giveHint = () => {
    if (!currentDrill.value) return;
    const targetTokens = currentDrill.value.tokens;
    const nextIdx = userTokens.value.length;
    if (nextIdx >= targetTokens.length) return;

    const neededText = targetTokens[nextIdx];
    const match = availableTokens.value.find(
      (t) => !t.used && t.text.toLowerCase().trim() === neededText.toLowerCase().trim()
    );
    if (match) addTokenToSlot(match);
  };

  // ---- 答案校验 ----
  const checkAnswer = () => {
    if (!currentDrill.value || !userTokens.value.length) return;

    const userSentence = userTokens.value.map((t) => t.text).join(' ');
    const target = currentDrill.value.english;

    const cleanUser = userSentence.replace(/\s+/g, ' ').replace(/[.,?!'’"]/g, '').toLowerCase().trim();
    const cleanTarget = target.replace(/\s+/g, ' ').replace(/[.,?!'’"]/g, '').toLowerCase().trim();

    if (cleanUser === cleanTarget) {
      if (audio && audio.playAudioCue) audio.playAudioCue('correct');
      drillFeedback.value = 'correct';
      showBreakdown.value = true;
      score.value += 15;
      streak.value += 1;
      persistScore();
      persistStreak();
      if (audio && audio.playTTS) audio.playTTS(target);
    } else {
      if (audio && audio.playAudioCue) audio.playAudioCue('error');
      drillFeedback.value = 'wrong';
      streak.value = 0;
      persistStreak();
      isShaking.value = true;
      setTimeout(() => { isShaking.value = false; }, 450);
    }
  };

  // ---- 关卡切换 ----
  const nextDrill = () => {
    if (currentDrillIndex.value < filteredDrills.value.length - 1) {
      initDrill(currentDrillIndex.value + 1);
    } else {
      initDrill(0);
    }
  };

  const prevDrill = () => {
    if (currentDrillIndex.value > 0) {
      initDrill(currentDrillIndex.value - 1);
    }
  };

  const randomDrill = () => {
    if (!filteredDrills.value.length) return;
    if (audio && audio.playAudioCue) audio.playAudioCue('click');
    const randIdx = Math.floor(Math.random() * filteredDrills.value.length);
    initDrill(randIdx);
  };

  // ---- 供口语对练复用的积分累加 ----
  const addScore = (n) => {
    score.value += n;
    persistScore();
  };

  // ---- 自建题库（AI 课文制卡）----
  const showCustomModal = ref(false);
  const customText = ref('');
  const customTag = ref('静静精选课文');
  const isGeneratingCustom = ref(false);
  const generatedPreviewDrills = ref([]);

  const customDrills = computed(() => {
    return allDrills.value.filter((d) => d.category === 'custom');
  });

  const openCustomModal = () => {
    showCustomModal.value = true;
    if (!customText.value) {
      customTag.value = '静静精选课文';
    }
  };

  const closeCustomModal = () => {
    showCustomModal.value = false;
    generatedPreviewDrills.value = [];
  };

  const fillSampleText = () => {
    customTag.value = '职场进阶 · 精选长句';
    customText.value = `The secret of getting ahead is getting started.
Where there is a will, there is a way. 有志者事竟成。
Success is not final, failure is not fatal: it is the courage to continue that counts.
Technology has dramatically transformed the way people communicate in modern society.`;
  };

  const generateCustomDrills = async () => {
    if (!customText.value.trim()) return;
    isGeneratingCustom.value = true;
    try {
      const res = await fetch('/api/drills/custom/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: customText.value,
          tag: customTag.value || '静静精选课文'
        })
      });
      const data = await res.json();
      if (data.status === 'success' && data.drills) {
        generatedPreviewDrills.value = data.drills;
        if (audio && audio.playAudioCue) audio.playAudioCue('correct');
      } else {
        alert('解析失败，请检查输入的文本内容');
      }
    } catch (e) {
      console.error('Failed to generate custom drills:', e);
      alert('解析出错，请确认本地大模型服务正常运行');
    } finally {
      isGeneratingCustom.value = false;
    }
  };

  const removePreviewDrill = (idx) => {
    generatedPreviewDrills.value.splice(idx, 1);
  };

  const saveAndPlayCustomDrills = async () => {
    if (!generatedPreviewDrills.value.length) return;
    try {
      const res = await fetch('/api/drills/custom/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ drills: generatedPreviewDrills.value })
      });
      const data = await res.json();
      if (data.status === 'success') {
        const drillsRes = await fetch('/api/drills');
        allDrills.value = await drillsRes.json();
        closeCustomModal();
        customText.value = '';
        selectedCategory.value = 'custom';
        initDrill(0);
        if (audio && audio.playAudioCue) audio.playAudioCue('correct');
      }
    } catch (e) {
      console.error('Failed to save custom drills:', e);
      alert('保存自建题库失败');
    }
  };

  const deleteCustomDrill = async (drillId) => {
    if (!confirm('确定要删除这道自建关卡吗？')) return;
    try {
      const res = await fetch(`/api/drills/custom/${drillId}`, { method: 'DELETE' });
      const data = await res.json();
      if (data.status === 'success') {
        allDrills.value = allDrills.value.filter((d) => d.id !== drillId);
        if (filteredDrills.value.length) {
          initDrill(Math.min(currentDrillIndex.value, filteredDrills.value.length - 1));
        } else {
          selectedCategory.value = 'all';
          initDrill(0);
        }
      }
    } catch (e) {
      console.error('Failed to delete drill:', e);
    }
  };

  // ---- 拉取题库 ----
  const loadDrills = async () => {
    try {
      const res = await fetch('/api/drills');
      if (res.ok) {
        allDrills.value = await res.json();
        initDrill(0);
      }
    } catch (e) {
      console.warn('Drills fetch failed:', e);
    }
  };

  return {
    // 状态
    allDrills,
    selectedCategory,
    currentDrillIndex,
    filteredDrills,
    currentDrill,
    currentDrillWords,
    userTokens,
    availableTokens,
    drillFeedback,
    isShaking,
    showBreakdown,
    score,
    streak,

    // 方法
    loadDrills,
    initDrill,
    prewarmCurrent,
    addTokenToSlot,
    removeTokenFromSlot,
    shuffleTokens,
    giveHint,
    checkAnswer,
    nextDrill,
    prevDrill,
    randomDrill,
    getCategoryCount,
    addScore,

    // 自建题库
    showCustomModal,
    customText,
    customTag,
    isGeneratingCustom,
    generatedPreviewDrills,
    customDrills,
    openCustomModal,
    closeCustomModal,
    fillSampleText,
    generateCustomDrills,
    removePreviewDrill,
    saveAndPlayCustomDrills,
    deleteCustomDrill
  };
}
