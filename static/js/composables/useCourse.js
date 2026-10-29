// ============================================================================
// useCourse — 课程大厅 · 章节目录 · 音标语法研习工坊 (3-Tier Course Engine)
// 100% 还原蛙学社/哇学社课程体系、IPA音标研习栏、语法成分彩色标签与下划线槽位填空
// ============================================================================

const Vue = window.Vue;
const COURSE_STORAGE_KEY = 'jjs_course_progress_v2';

export const COURSE_CATEGORIES = [
  { id: '全部', label: '全部', icon: 'squares-four' },
  { id: '零基础', label: '零基础', icon: 'sparkle' },
  { id: '日常实用', label: '日常实用', icon: 'chat-circle-dots' },
  { id: '综合提升', label: '综合提升', icon: 'trend-up' },
  { id: '商务英语', label: '商务英语', icon: 'briefcase' },
  { id: '认证备考', label: '认证备考', icon: 'certificate' },
  { id: '娱乐影音', label: '娱乐影音', icon: 'film-slate' },
  { id: '分级阅读', label: '分级阅读', icon: 'book-open-text' },
  { id: '中国文化', label: '中国文化', icon: 'globe-hemisphere-east' },
  { id: '行业英语', label: '行业英语', icon: 'cpu' },
  { id: '文学读物', label: '文学读物', icon: 'books' },
  { id: '英文演讲', label: '英文演讲', icon: 'microphone-stage' },
  { id: '其他', label: '其他', icon: 'lightbulb' }
];

function loadStoredProgress() {
  try {
    const raw = localStorage.getItem(COURSE_STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch (e) {
    return {};
  }
}

function saveStoredProgress(data) {
  try {
    localStorage.setItem(COURSE_STORAGE_KEY, JSON.stringify(data));
  } catch (e) {
    // ignore
  }
}

export function useCourse({ audio, onScoreAdd } = {}) {
  const { ref, computed, watch, onMounted, onUnmounted } = Vue;

  // View state: 'catalog' (课程大厅) | 'chapters' (章节列表) | 'practice' (研习工坊)
  const courseViewMode = ref('catalog');
  const courseList = ref([]);
  const courseSelectedCategory = ref('全部');
  const courseSearchQuery = ref('');

  // Active selection
  const currentCourse = ref(null);
  const chapters = ref([]);
  const currentChapter = ref(null);
  const chapterDrills = ref([]);
  const courseDrillIndex = ref(0);

  // Drill practice interactive state
  const userTypedWords = ref([]); // array of strings for each word
  const activeWordSlot = ref(0);   // currently focused word index
  const isDrillCorrect = ref(false);
  const showAnswerHint = ref(false);
  const drillPracticeMode = ref('typing'); // 'typing' | 'blocks' | 'shadow'
  const isPracticing = ref(false);

  // AI 影子跟读与发音评测状态
  const isRecordingSpeech = ref(false);
  const isEvaluatingSpeech = ref(false);
  const speechScore = ref(null);
  const speechRecognizedText = ref('');
  const speechWordMatches = ref([]);
  let mediaRecorder = null;
  let audioChunks = [];

  // Progress store
  const storedProgress = ref(loadStoredProgress());

  // 后端 SQLite 进度同步防抖计时器
  let syncTimer = null;
  const syncProgressToBackend = (data) => {
    if (syncTimer) clearTimeout(syncTimer);
    syncTimer = setTimeout(async () => {
      try {
        await fetch('/api/progress', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
      } catch (e) {}
    }, 1200);
  };

  const loadBackendProgress = async () => {
    try {
      const res = await fetch('/api/progress');
      if (res.ok) {
        const serverProgress = await res.json();
        if (serverProgress && Object.keys(serverProgress).length > 0) {
          storedProgress.value = { ...storedProgress.value, ...serverProgress };
          saveStoredProgress(storedProgress.value);
        }
      }
    } catch (e) {}
  };

  // Timer for tracking active study duration
  let studyTimer = null;
  const sessionSeconds = ref(0);

  const startStudyTimer = () => {
    if (studyTimer) clearInterval(studyTimer);
    studyTimer = setInterval(() => {
      sessionSeconds.value += 1;
      if (currentCourse.value && currentChapter.value) {
        recordStudyTime(1);
      }
    }, 1000);
  };

  const stopStudyTimer = () => {
    if (studyTimer) {
      clearInterval(studyTimer);
      studyTimer = null;
    }
  };

  const recordStudyTime = (seconds) => {
    if (!currentCourse.value || !currentChapter.value) return;
    const cid = currentCourse.value.id;
    const chid = currentChapter.value.id;
    const p = storedProgress.value;

    if (!p[cid]) {
      p[cid] = { total_seconds: 0, last_active: Date.now(), chapters: {} };
    }
    p[cid].total_seconds = (p[cid].total_seconds || 0) + seconds;
    p[cid].last_active = Date.now();
    p[cid].last_chapter_id = chid;

    if (!p[cid].chapters[chid]) {
      p[cid].chapters[chid] = {
        seconds: 0,
        status: 'recent',
        completed_count: 0,
        mastered: []
      };
    }
    p[cid].chapters[chid].seconds = (p[cid].chapters[chid].seconds || 0) + seconds;
    p[cid].chapters[chid].status = 'recent';
    saveStoredProgress(p);
    syncProgressToBackend(p);
  };

  // ---- Fetch Courses ----
  const loadCourses = async () => {
    try {
      const res = await fetch('/api/courses');
      if (res.ok) {
        courseList.value = await res.json();
      }
    } catch (e) {
      console.warn('[useCourse] Failed to fetch courses:', e);
    }
  };

  const getCourseCategoryCount = (catId) => {
    if (catId === '全部') return courseList.value.length;
    return courseList.value.filter(c => {
      if (Array.isArray(c.categories) && c.categories.includes(catId)) return true;
      return c.category_name === catId || c.category === catId;
    }).length;
  };
  const getCategoryCount = getCourseCategoryCount;

  const filteredCourses = computed(() => {
    let list = courseList.value;
    if (courseSelectedCategory.value !== '全部') {
      const cat = courseSelectedCategory.value;
      list = list.filter(c => {
        if (Array.isArray(c.categories) && c.categories.includes(cat)) {
          return true;
        }
        return c.category_name === cat || c.category === cat;
      });
    }
    const q = courseSearchQuery.value.trim().toLowerCase();
    if (!q) return list;
    return list.filter(c => {
      const matchTitle = (c.title || '').toLowerCase().includes(q);
      const matchEng = (c.english_title || '').toLowerCase().includes(q);
      const matchDesc = (c.description || '').toLowerCase().includes(q);
      const matchTag = (c.tag || '').toLowerCase().includes(q);
      const matchCat = Array.isArray(c.categories) && c.categories.some(tag => tag.toLowerCase().includes(q));
      return matchTitle || matchEng || matchDesc || matchTag || matchCat;
    });
  });

  // ---- Course Chapter Status & Progress Calculation ----
  const getChapterProgress = (courseId, chapterId) => {
    const cp = storedProgress.value[courseId];
    if (!cp || !cp.chapters || !cp.chapters[chapterId]) {
      return { status: 'unstarted', seconds: 0, completed_count: 0, mastered: [] };
    }
    return cp.chapters[chapterId];
  };

  const courseStudyTimeText = computed(() => {
    if (!currentCourse.value) return '0分钟';
    const cp = storedProgress.value[currentCourse.value.id];
    const totalSec = cp ? cp.total_seconds || 0 : 0;
    const mins = Math.floor(totalSec / 60);
    const secs = totalSec % 60;
    return `${mins}分钟${secs}秒`;
  });

  const courseRecentTimeText = computed(() => {
    if (!currentCourse.value) return '暂未练习';
    const cp = storedProgress.value[currentCourse.value.id];
    if (!cp || !cp.last_active) return '暂未练习';
    const diffMs = Date.now() - cp.last_active;
    const diffMins = Math.floor(diffMs / 60000);
    if (diffMins < 1) return '刚刚';
    if (diffMins < 60) return `大约${diffMins}分钟前`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `大约${diffHours}小时前`;
    return '1天前';
  });

  const courseProgressPercent = computed(() => {
    if (!currentCourse.value || !chapters.value.length) return 0;
    const cp = storedProgress.value[currentCourse.value.id];
    if (!cp || !cp.chapters) return 0;
    let completed = 0;
    chapters.value.forEach(ch => {
      const info = cp.chapters[ch.id];
      if (info && (info.status === 'completed' || info.completed_count > 0)) {
        completed += 1;
      }
    });
    return Math.round((completed / chapters.value.length) * 100);
  });

  const formatDuration = (seconds) => {
    if (!seconds || seconds <= 0) return '0分钟';
    if (seconds < 60) return `${seconds}秒`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return secs > 0 ? `${mins}分钟${secs}秒` : `${mins}分钟`;
  };

  // ---- Open Course -> Chapter Grid (Tier 2) ----
  const openCourse = async (courseId) => {
    try {
      const res = await fetch(`/api/courses/${courseId}`);
      if (res.ok) {
        const detail = await res.json();
        currentCourse.value = detail;

        // Enhance chapters with local stored progress
        const cp = storedProgress.value[courseId] || { chapters: {} };
        const lastChId = cp.last_chapter_id;

        chapters.value = detail.chapters.map((ch, idx) => {
          const chData = cp.chapters ? cp.chapters[ch.id] : null;
          let status = 'unstarted';
          let duration_seconds = 0;
          let completed_count = 0;

          if (chData) {
            status = chData.status || (chData.completed_count > 0 ? 'completed' : 'unstarted');
            duration_seconds = chData.seconds || 0;
            completed_count = chData.completed_count || 0;
          } else if (courseId === 'oral_900') {
            // Preset mock progress matching screenshot if first time opening
            if (idx === 0) {
              status = 'completed';
              duration_seconds = 1060;
              completed_count = 1;
            } else if (idx === 1) {
              status = 'completed';
              duration_seconds = 1034;
              completed_count = 1;
            } else if (idx === 2) {
              status = 'recent';
              duration_seconds = 60;
              completed_count = 0;
            }
          }

          if (lastChId && lastChId === ch.id && status !== 'completed') {
            status = 'recent';
          }

          return {
            ...ch,
            status,
            duration_seconds,
            completed_count
          };
        });

        courseViewMode.value = 'chapters';
      }
    } catch (e) {
      console.warn('[useCourse] Failed to load course detail:', e);
    }
  };

  // ---- Open Chapter -> Practice Drill Screen (Tier 3) ----
  const openChapter = async (chapterId, startIdx = 0) => {
    if (!currentCourse.value) return;
    try {
      const res = await fetch(`/api/courses/${currentCourse.value.id}/chapters/${chapterId}`);
      if (res.ok) {
        const data = await res.json();
        currentChapter.value = data;
        chapterDrills.value = data.drills || [];
        courseDrillIndex.value = Math.max(0, Math.min(startIdx, chapterDrills.value.length - 1));
        initDrillSlotState();
        courseViewMode.value = 'practice';
        startStudyTimer();
        prewarmDrillAudio();
        // Play current sentence audio on enter
        setTimeout(() => {
          playCurrentDrillAudio();
        }, 300);
      }
    } catch (e) {
      console.warn('[useCourse] Failed to load chapter drills:', e);
    }
  };

  const courseDrill = computed(() => {
    return chapterDrills.value[courseDrillIndex.value] || null;
  });
  const currentDrill = courseDrill;

  // Prepare words for underline slots
  const drillWords = computed(() => {
    if (!courseDrill.value) return [];
    // Clean words without ending punctuation
    return courseDrill.value.english
      .split(/\s+/)
      .map(w => w.replace(/[.,?!;:'"()]/g, '').trim())
      .filter(w => w.length > 0);
  });

  // Thematic scene illustration mapping for Tier 3 Drill Workshop
  const currentDrillScene = computed(() => {
    const course = currentCourse.value;
    const ch = currentChapter.value;
    const cid = course ? course.id : '';
    const chTitle = ch ? (ch.chapter_title || ch.title || '') : '';

    if (cid === 'movie_classics') {
      if (chTitle.includes('肖申克')) {
        return { image: '/static/images/scenes/scene_shawshank.jpg', tag: '🎬 影史名篇 · 《肖申克的救赎》', icon: 'film-slate' };
      }
      if (chTitle.includes('阿甘')) {
        return { image: '/static/images/scenes/scene_forrest.jpg', tag: '🎬 经典电影 · 《阿甘正传》', icon: 'film-slate' };
      }
      if (chTitle.includes('泰坦尼克')) {
        return { image: '/static/images/scenes/scene_titanic.jpg', tag: '🎬 影史巨作 · 《泰坦尼克号》', icon: 'heart' };
      }
      if (chTitle.includes('教父')) {
        return { image: '/static/images/scenes/scene_godfather.jpg', tag: '🎬 经典黑帮 · 《教父》', icon: 'crown' };
      }
      return { image: '/static/images/scenes/scene_cinema.jpg', tag: '🎬 好莱坞经典原声台词', icon: 'film-slate' };
    }

    if (cid === 'tv_slang_hot') {
      if (chTitle.includes('老友记')) {
        return { image: '/static/images/scenes/scene_friends.jpg', tag: '📺 经典美剧 · 《老友记》', icon: 'coffee' };
      }
      return { image: '/static/images/scenes/scene_tv.jpg', tag: '📺 美剧地道口语俚语', icon: 'television' };
    }

    if (cid === 'ted_talks_master') {
      return { image: '/static/images/scenes/scene_ted.jpg', tag: '🎙️ TED 传奇公开演讲', icon: 'microphone-stage' };
    }

    if (cid === 'classic_prose') {
      if (chTitle.includes('傲慢与偏见')) {
        return { image: '/static/images/scenes/scene_pride.jpg', tag: '📖 传世名著 · 《傲慢与偏见》', icon: 'book-bookmark' };
      }
      if (chTitle.includes('小王子')) {
        return { image: '/static/images/scenes/scene_prince.jpg', tag: '✨ 纯真哲思 · 《小王子》', icon: 'sparkle' };
      }
      return { image: '/static/images/scenes/scene_literature.jpg', tag: '📖 世界经典名著晨读', icon: 'book-open' };
    }

    if (cid === 'china_heritage' || cid === 'china_landmarks') {
      return { image: '/static/images/scenes/scene_china.jpg', tag: '🏮 东方风骨 · 中国文化', icon: 'mountains' };
    }

    if (cid === 'china_gourmet' || cid === 'oral_8000_dining') {
      return { image: '/static/images/scenes/scene_dining.jpg', tag: '🍲 舌尖寻味 · 餐厅就餐', icon: 'bowl-food' };
    }

    if (cid === 'oral_8000_travel' || cid === 'aviation_hospitality') {
      return { image: '/static/images/scenes/scene_travel.jpg', tag: '✈️ 环球漫旅 · 机场出行', icon: 'airplane-tilt' };
    }

    if (cid === 'it_tech_pro') {
      return { image: '/static/images/scenes/scene_tech.jpg', tag: '💻 极客职场 · IT研发英语', icon: 'cpu' };
    }

    if (cid.startsWith('biz_')) {
      return { image: '/static/images/scenes/scene_business.jpg', tag: '💼 跨国商务 · 职场实战', icon: 'briefcase' };
    }

    if (cid === 'finance_investing') {
      return { image: '/static/images/scenes/scene_finance.jpg', tag: '📈 华尔街金融 · 资本市场', icon: 'chart-line-up' };
    }

    if (cid.includes('ielts') || cid.includes('toefl') || cid.includes('cet') || cid.includes('kaoyan')) {
      return { image: '/static/images/scenes/scene_exam.jpg', tag: '🎓 官方认证题库冲刺', icon: 'certificate' };
    }

    if (cid.startsWith('primary_') || cid.startsWith('pattern_')) {
      return { image: '/static/images/scenes/scene_kids.jpg', tag: '🎨 启蒙乐园 · 核心句式', icon: 'palette' };
    }

    if (cid.startsWith('nce_')) {
      return { image: '/static/images/scenes/scene_library.jpg', tag: '📚 新概念正统英式英语', icon: 'books' };
    }

    if (cid === 'oral_8000_health') {
      return { image: '/static/images/scenes/scene_health.jpg', tag: '🌿 养生健康 · 医疗就诊', icon: 'first-aid' };
    }

    if (cid === 'oral_8000_romance') {
      return { image: '/static/images/scenes/scene_romance.jpg', tag: '🌹 浪漫约会 · 甜蜜表白', icon: 'heart' };
    }

    if (cid === 'oral_8000_shopping') {
      return { image: '/static/images/scenes/scene_shopping.jpg', tag: '🛍️ 时尚街区 · 购物血拼', icon: 'shopping-bag' };
    }

    if (cid === 'pop_music_lyrics') {
      return { image: '/static/images/scenes/scene_music.jpg', tag: '🎵 欧美流行金曲 · 诗意歌词', icon: 'music-notes' };
    }

    return {
      image: `/static/images/courses/${cid}.jpg`,
      fallback: '/static/images/scenes/scene_daily.jpg',
      tag: `✨ ${course?.title || '地道口语实战'}`,
      icon: course?.icon || 'sparkle'
    };
  });

  // Init slot state for new drill
  const initDrillSlotState = () => {
    const words = drillWords.value;
    userTypedWords.value = new Array(words.length).fill('');
    activeWordSlot.value = 0;
    isDrillCorrect.value = false;
    showAnswerHint.value = false;
    speechScore.value = null;
    speechRecognizedText.value = '';
    speechWordMatches.value = [];
  };

  const prewarmDrillAudio = () => {
    const drill = courseDrill.value;
    if (!drill || !audio || !audio.prewarmAudio) return;
    if (drill.english) audio.prewarmAudio(drill.english);
    const nextDrill = chapterDrills.value[courseDrillIndex.value + 1];
    if (nextDrill && nextDrill.english) audio.prewarmAudio(nextDrill.english);
  };

  // Play Kokoro neural TTS for current drill
  const playCurrentDrillAudio = () => {
    const drill = courseDrill.value;
    if (drill && drill.english && audio && audio.playTTS) {
      audio.playTTS(drill.english, 'course_drill_' + drill.id);
    }
  };

  // Play single chunk or word audio
  const playChunkAudio = (text) => {
    if (!text || !audio || !audio.playTTS) return;
    audio.playTTS(text, 'chunk_' + text);
  };

  // ---- AI 影子跟读 (Shadow Reading) 录音与实时发音评测 ----
  const startShadowRecording = async () => {
    if (isRecordingSpeech.value) return;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunks = [];
      mediaRecorder = new MediaRecorder(stream);
      mediaRecorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) audioChunks.push(e.data);
      };
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        stream.getTracks().forEach(t => t.stop());
        await evaluateShadowSpeech(audioBlob);
      };
      mediaRecorder.start();
      isRecordingSpeech.value = true;
      speechScore.value = null;
      speechRecognizedText.value = '';
      if (audio && audio.playAudioCue) audio.playAudioCue('click');
    } catch (e) {
      alert('请开启浏览器麦克风权限以体验 AI 影子跟读评测');
    }
  };

  const stopShadowRecording = () => {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop();
      isRecordingSpeech.value = false;
      isEvaluatingSpeech.value = true;
    }
  };

  const evaluateShadowSpeech = async (audioBlob) => {
    try {
      const formData = new FormData();
      formData.append('file', audioBlob, 'speech.webm');
      const res = await fetch('/api/transcribe', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      const recognized = (data.text || '').trim();
      speechRecognizedText.value = recognized;

      const target = (courseDrill.value ? courseDrill.value.english : '').trim();
      const targetWords = target.replace(/[,.?!:;"'()]/g, '').toLowerCase().split(/\s+/).filter(Boolean);
      const recWords = recognized.replace(/[,.?!:;"'()]/g, '').toLowerCase().split(/\s+/).filter(Boolean);

      let matchedCount = 0;
      const matches = targetWords.map(tw => {
        const isMatched = recWords.includes(tw);
        if (isMatched) matchedCount++;
        return { word: tw, matched: isMatched };
      });

      speechWordMatches.value = matches;
      const calcScore = targetWords.length > 0 ? Math.round((matchedCount / targetWords.length) * 100) : 0;
      speechScore.value = calcScore;

      if (calcScore >= 75) {
        if (audio && audio.playAudioCue) audio.playAudioCue('pop');
        if (onScoreAdd) onScoreAdd(20);
        recordDrillCompletion(courseDrill.value.id);
      }
    } catch (e) {
      console.warn('[Shadow evaluation error]:', e);
    } finally {
      isEvaluatingSpeech.value = false;
    }
  };

  // Underline Slot Typing Input Handler
  const handleKeyInput = (key) => {
    if (courseViewMode.value !== 'practice' || !courseDrill.value) return;

    const words = drillWords.value;
    if (!words.length) return;

    const currentWord = words[activeWordSlot.value] || '';
    let currentInput = userTypedWords.value[activeWordSlot.value] || '';

    if (key === 'Backspace') {
      if (currentInput.length > 0) {
        userTypedWords.value[activeWordSlot.value] = currentInput.slice(0, -1);
      } else if (activeWordSlot.value > 0) {
        activeWordSlot.value -= 1;
      }
      return;
    }

    if (key === ' ' || key === 'Space') {
      // Space advances to next slot or checks if at last slot
      if (activeWordSlot.value < words.length - 1) {
        activeWordSlot.value += 1;
      } else {
        checkDrillAnswer();
      }
      return;
    }

    // Letters or numbers
    if (/^[a-zA-Z0-9'-]$/.test(key)) {
      if (currentInput.length < currentWord.length + 3) {
        currentInput += key.toLowerCase();
        userTypedWords.value[activeWordSlot.value] = currentInput;

        // Auto-advance if matches current word
        if (currentInput.toLowerCase() === currentWord.toLowerCase()) {
          if (activeWordSlot.value < words.length - 1) {
            activeWordSlot.value += 1;
          } else {
            checkDrillAnswer();
          }
        }
      }
    }
  };

  // Reveal answer / hint
  const revealAnswer = () => {
    if (!courseDrill.value) return;
    showAnswerHint.value = true;
    const words = drillWords.value;
    userTypedWords.value = words.map(w => w);
    activeWordSlot.value = words.length - 1;
    if (audio && audio.playAudioCue) audio.playAudioCue('click');
  };

  // Check user answer
  const checkDrillAnswer = () => {
    const words = drillWords.value;
    const typed = userTypedWords.value;
    const isAllFilled = typed.every((w, idx) => w.toLowerCase() === (words[idx] || '').toLowerCase());

    if (isAllFilled || showAnswerHint.value) {
      isDrillCorrect.value = true;
      if (audio && audio.playAudioCue) audio.playAudioCue('correct');
      if (onScoreAdd) onScoreAdd(15);
      // Auto play full sentence audio
      playCurrentDrillAudio();

      // Record progress
      recordDrillCompletion(courseDrill.value.id);

      // Auto advance after 1.6s
      setTimeout(() => {
        nextChapterDrill();
      }, 1600);
    } else {
      if (audio && audio.playAudioCue) audio.playAudioCue('error');
    }
  };

  const recordDrillCompletion = (drillId) => {
    if (!currentCourse.value || !currentChapter.value) return;
    const cid = currentCourse.value.id;
    const chid = currentChapter.value.id;
    const p = storedProgress.value;

    if (!p[cid]) p[cid] = { total_seconds: 0, chapters: {} };
    if (!p[cid].chapters[chid]) {
      p[cid].chapters[chid] = { seconds: 0, status: 'recent', completed_count: 0, mastered: [] };
    }
    const ch = p[cid].chapters[chid];
    if (!ch.mastered.includes(drillId)) {
      ch.mastered.push(drillId);
    }
    // If all drills completed
    if (ch.mastered.length >= (currentChapter.value.drill_count || chapterDrills.value.length)) {
      ch.status = 'completed';
      ch.completed_count += 1;
    }
    saveStoredProgress(p);
  };

  const nextChapterDrill = () => {
    if (courseDrillIndex.value < chapterDrills.value.length - 1) {
      courseDrillIndex.value += 1;
      initDrillSlotState();
      prewarmDrillAudio();
      setTimeout(playCurrentDrillAudio, 200);
    } else {
      // Completed chapter!
      if (audio && audio.playAudioCue) audio.playAudioCue('correct');
      backToChapters();
    }
  };

  const prevChapterDrill = () => {
    if (courseDrillIndex.value > 0) {
      courseDrillIndex.value -= 1;
      initDrillSlotState();
      prewarmDrillAudio();
      setTimeout(playCurrentDrillAudio, 200);
    }
  };

  const markMastered = () => {
    if (!courseDrill.value) return;
    recordDrillCompletion(courseDrill.value.id);
    if (audio && audio.playAudioCue) audio.playAudioCue('pop');
    nextChapterDrill();
  };

  const markUnfamiliar = () => {
    if (audio && audio.playAudioCue) audio.playAudioCue('pop');
    revealAnswer();
  };

  // Reset course progress
  const resetCurrentCourseProgress = () => {
    if (!currentCourse.value) return;
    const cid = currentCourse.value.id;
    delete storedProgress.value[cid];
    saveStoredProgress(storedProgress.value);
    openCourse(cid);
  };

  // Navigations
  const backToCatalog = () => {
    stopStudyTimer();
    courseViewMode.value = 'catalog';
  };

  const backToChapters = () => {
    stopStudyTimer();
    if (currentCourse.value) {
      openCourse(currentCourse.value.id);
    } else {
      courseViewMode.value = 'catalog';
    }
  };

  // Keyboard shortcut listener for Tier 3
  const handleKeydown = (e) => {
    if (courseViewMode.value !== 'practice') return;

    // Ignore if user is inside an input/textarea
    const tag = (e.target && e.target.tagName) || '';
    if (tag === 'INPUT' || tag === 'TEXTAREA') return;

    // Ctrl + A: 朗读
    if ((e.ctrlKey || e.metaKey) && (e.key === 'a' || e.key === 'A')) {
      e.preventDefault();
      playCurrentDrillAudio();
      return;
    }

    // Ctrl + M: 掌握
    if ((e.ctrlKey || e.metaKey) && (e.key === 'm' || e.key === 'M')) {
      e.preventDefault();
      markMastered();
      return;
    }

    // Ctrl + Q: 不熟悉
    if ((e.ctrlKey || e.metaKey) && (e.key === 'q' || e.key === 'Q')) {
      e.preventDefault();
      markUnfamiliar();
      return;
    }

    // Down arrow or Up arrow: 答案/提示
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      revealAnswer();
      return;
    }

    // Shift + Right Arrow: 下一题
    if (e.shiftKey && e.key === 'ArrowRight') {
      e.preventDefault();
      nextChapterDrill();
      return;
    }

    // Shift + Left Arrow: 上一题
    if (e.shiftKey && e.key === 'ArrowLeft') {
      e.preventDefault();
      prevChapterDrill();
      return;
    }

    // Tab: 朗读原句
    if (e.key === 'Tab') {
      e.preventDefault();
      playCurrentDrillAudio();
      return;
    }

    // Letters, backspace, space for slot filling
    if (e.key === 'Backspace' || e.key === ' ' || /^[a-zA-Z0-9'-]$/.test(e.key)) {
      if (!e.ctrlKey && !e.metaKey && !e.altKey) {
        e.preventDefault();
        handleKeyInput(e.key);
      }
    }
  };

  onMounted(() => {
    loadCourses();
    loadBackendProgress();
    window.addEventListener('keydown', handleKeydown);
  });

  onUnmounted(() => {
    stopStudyTimer();
    window.removeEventListener('keydown', handleKeydown);
  });

  return {
    courseViewMode,
    courseList,
    courseSelectedCategory,
    selectedCategory: courseSelectedCategory,
    courseSearchQuery,
    getCourseCategoryCount,
    getCategoryCount: getCourseCategoryCount,
    COURSE_CATEGORIES,
    filteredCourses,
    currentCourse,
    chapters,
    currentChapter,
    chapterDrills,
    courseDrillIndex,
    currentDrillIndex: courseDrillIndex,
    courseDrill,
    currentDrill: courseDrill,
    currentDrillScene,
    drillWords,
    userTypedWords,
    activeWordSlot,
    isDrillCorrect,
    showAnswerHint,
    drillPracticeMode,
    isRecordingSpeech,
    isEvaluatingSpeech,
    speechScore,
    speechRecognizedText,
    speechWordMatches,
    startShadowRecording,
    stopShadowRecording,
    courseStudyTimeText,
    courseRecentTimeText,
    courseProgressPercent,
    formatDuration,
    loadCourses,
    openCourse,
    openChapter,
    backToCatalog,
    backToChapters,
    playCurrentDrillAudio,
    playChunkAudio,
    nextChapterDrill,
    prevChapterDrill,
    markMastered,
    markUnfamiliar,
    revealAnswer,
    checkDrillAnswer,
    handleKeyInput,
    resetCurrentCourseProgress
  };
}
