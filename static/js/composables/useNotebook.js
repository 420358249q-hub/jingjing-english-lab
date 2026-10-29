// ============================================================================
// useNotebook — 核心生词与地道短语手账（CRUD + localStorage 持久化）
// ============================================================================

const Vue = window.Vue;

const NOTEBOOK_KEY = 'jjs_notebook';

export function useNotebook({ audio } = {}) {
  const { ref } = Vue;

  const notebookItems = ref(loadNotebook());

  function loadNotebook() {
    try {
      const raw = localStorage.getItem(NOTEBOOK_KEY);
      const parsed = JSON.parse(raw || '[]');
      return Array.isArray(parsed) ? parsed : [];
    } catch (e) {
      return [];
    }
  }

  function persist() {
    try {
      localStorage.setItem(NOTEBOOK_KEY, JSON.stringify(notebookItems.value));
    } catch (e) { /* 忽略配额/隐私模式异常 */ }
  }

  const addToNotebook = (english, chinese = '日常收藏短语') => {
    if (!english) return;
    if (audio && audio.playAudioCue) audio.playAudioCue('pop');

    const exists = notebookItems.value.some(
      (item) => (item.english || '').toLowerCase() === String(english).toLowerCase()
    );
    if (exists) return;

    notebookItems.value.unshift({
      id: Date.now(),
      english: String(english),
      chinese: String(chinese),
      date: new Date().toLocaleDateString()
    });
    persist();
  };

  const removeFromNotebook = (id) => {
    if (audio && audio.playAudioCue) audio.playAudioCue('click');
    notebookItems.value = notebookItems.value.filter((item) => item.id !== id);
    persist();
  };

  return {
    notebookItems,
    addToNotebook,
    removeFromNotebook
  };
}
