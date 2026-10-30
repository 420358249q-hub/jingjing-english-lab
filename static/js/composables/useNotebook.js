// ============================================================================
// useNotebook — 核心生词与地道短语手账（Local-First + SQLite 双向持久化 + SM-2 艾宾浩斯复习调度）
// ============================================================================

const Vue = window.Vue;
const NOTEBOOK_KEY = 'jjs_notebook';

export function useNotebook({ audio } = {}) {
  const { ref, computed, onMounted } = Vue;

  const notebookItems = ref(loadNotebook());
  const dueCards = ref([]);
  const srsStats = ref({ total: 0, due: 0, mastered: 0, total_reviews: 0 });
  const activeReviewCard = ref(null);
  const showReviewModal = ref(false);
  const showNotebookEnglish = ref(true); // 生词本小眼睛开关

  const toggleNotebookEnglish = () => {
    showNotebookEnglish.value = !showNotebookEnglish.value;
  };

  function loadNotebook() {
    try {
      const raw = localStorage.getItem(NOTEBOOK_KEY);
      const parsed = JSON.parse(raw || '[]');
      return Array.isArray(parsed) ? parsed : [];
    } catch (e) {
      return [];
    }
  }

  function persistLocal() {
    try {
      localStorage.setItem(NOTEBOOK_KEY, JSON.stringify(notebookItems.value));
    } catch (e) { /* 忽略配额/隐私模式异常 */ }
  }

  // ---- 与后端 SQLite 数据库双向同步 ----
  const syncWithBackend = async () => {
    try {
      // 1. 获取后端持久化卡片
      const res = await fetch('/api/cards');
      if (res.ok) {
        const serverCards = await res.json();
        if (Array.isArray(serverCards)) {
          // 如果后端已有卡片，以后端为主并合并
          if (serverCards.length > 0) {
            notebookItems.value = serverCards;
            persistLocal();
          } else if (notebookItems.value.length > 0) {
            // 后端为空但本地有历史生词，自动迁移同步至后端 SQLite
            await fetch('/api/cards/import', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ items: notebookItems.value })
            });
          }
        }
      }

      // 2. 刷新待复习与统计
      await refreshDueCards();
    } catch (e) {
      console.warn('[Notebook Sync Warning]:', e);
    }
  };

  const refreshDueCards = async () => {
    try {
      const [dueRes, statsRes] = await Promise.all([
        fetch('/api/cards/due'),
        fetch('/api/cards/stats')
      ]);
      if (dueRes.ok) dueCards.value = await dueRes.json();
      if (statsRes.ok) srsStats.value = await statsRes.json();
    } catch (e) {}
  };

  onMounted(() => {
    syncWithBackend();
  });

  const addToNotebook = async (english, chinese = '日常收藏短语') => {
    if (!english) return;
    if (audio && audio.playAudioCue) audio.playAudioCue('pop');

    const cleanEn = String(english).trim();
    const exists = notebookItems.value.some(
      (item) => (item.english || '').toLowerCase() === cleanEn.toLowerCase()
    );
    if (exists) return;

    const tempItem = {
      id: Date.now(),
      english: cleanEn,
      chinese: String(chinese),
      date: new Date().toLocaleDateString(),
      ease_factor: 2.5,
      interval_days: 0,
      repetitions: 0
    };
    notebookItems.value.unshift(tempItem);
    persistLocal();

    // 异步同步到后端 SQLite
    try {
      const res = await fetch('/api/cards', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ english: cleanEn, chinese: String(chinese), source: '静静自习室' })
      });
      if (res.ok) {
        const savedCard = await res.json();
        const idx = notebookItems.value.findIndex(item => item.english === cleanEn);
        if (idx !== -1) {
          notebookItems.value[idx] = savedCard;
          persistLocal();
        }
        refreshDueCards();
      }
    } catch (e) {}
  };

  const removeFromNotebook = async (id) => {
    if (audio && audio.playAudioCue) audio.playAudioCue('click');
    notebookItems.value = notebookItems.value.filter((item) => item.id !== id);
    persistLocal();

    try {
      await fetch(`/api/cards/${id}`, { method: 'DELETE' });
      refreshDueCards();
    } catch (e) {}
  };

  // ---- 艾宾浩斯复习评分提交 ----
  const submitReview = async (cardId, quality) => {
    if (audio && audio.playAudioCue) audio.playAudioCue('click');
    try {
      const res = await fetch(`/api/cards/${cardId}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ quality })
      });
      if (res.ok) {
        const updated = await res.json();
        // 更新本地对应卡片状态
        const idx = notebookItems.value.findIndex(c => c.id === cardId);
        if (idx !== -1) notebookItems.value[idx] = updated;
        dueCards.value = dueCards.value.filter(c => c.id !== cardId);
        persistLocal();
        refreshDueCards();
      }
    } catch (e) {
      console.warn('[Review submit warning]:', e);
    }
  };

  return {
    notebookItems,
    dueCards,
    srsStats,
    activeReviewCard,
    showReviewModal,
    showNotebookEnglish,
    toggleNotebookEnglish,
    addToNotebook,
    removeFromNotebook,
    submitReview,
    refreshDueCards
  };
}
