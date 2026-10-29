"""
静静宝贝专属学习系统 - 本地 SQLite 持久化 + SM-2 记忆调度

Tables:
  profile      : 能量星 / 宝贝金币 / 连续天数
  cards        : 生词本卡片 + SM-2 记忆参数
  reviews      : 每次复习流水（用于成长曲线与统计）
  diagnostics  : 每次 6 维成长雷达诊断留档（用于成长曲线）
"""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import threading
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

DEFAULT_USER = "jingjing"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB = os.path.join(BASE_DIR, "data", "jingjing.db")

# 艾宾浩斯短阶梯（答错/遗忘时回退到更密集的复习点，单位：天）
EBBINGHAUS_LADDER = (1, 2, 4, 7, 15, 30, 60)

DIMENSION_KEYS = (
    "fluency", "grammar", "vocabulary",
    "pronunciation", "ideation", "confidence",
)

# 单进程内串行化写操作，避免多线程下 WAL 争用（RLock：import_cards 会嵌套调用 add_card）
_write_lock = threading.RLock()


def _now() -> datetime:
    return datetime.now()


def _today() -> date:
    return date.today()


def _iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat()


class SRSStore:
    def __init__(self, db_path: str = DEFAULT_DB, backup_keep: int = 7):
        self.db_path = db_path
        self.backup_keep = backup_keep
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    # ---------------- connection / schema ----------------
    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS profile (
                    user_id     TEXT PRIMARY KEY,
                    stars       INTEGER NOT NULL DEFAULT 0,
                    coins       INTEGER NOT NULL DEFAULT 0,
                    streak      INTEGER NOT NULL DEFAULT 0,
                    last_active TEXT,
                    created_at  TEXT NOT NULL,
                    updated_at  TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS cards (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id         TEXT NOT NULL,
                    english         TEXT NOT NULL,
                    chinese         TEXT,
                    source          TEXT,
                    ease_factor     REAL NOT NULL DEFAULT 2.5,
                    interval_days   INTEGER NOT NULL DEFAULT 0,
                    repetitions     INTEGER NOT NULL DEFAULT 0,
                    lapses          INTEGER NOT NULL DEFAULT 0,
                    due_at          TEXT NOT NULL,
                    last_reviewed_at TEXT,
                    created_at      TEXT NOT NULL,
                    updated_at      TEXT NOT NULL,
                    UNIQUE(user_id, english)
                );
                CREATE INDEX IF NOT EXISTS idx_cards_due ON cards(user_id, due_at);

                CREATE TABLE IF NOT EXISTS reviews (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    card_id     INTEGER NOT NULL,
                    user_id     TEXT NOT NULL,
                    quality     INTEGER NOT NULL,
                    reviewed_at TEXT NOT NULL,
                    FOREIGN KEY(card_id) REFERENCES cards(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_reviews_card ON reviews(card_id, reviewed_at);

                CREATE TABLE IF NOT EXISTS diagnostics (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id     TEXT NOT NULL,
                    created_at  TEXT NOT NULL,
                    overall     TEXT,
                    scores      TEXT NOT NULL,
                    payload     TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS chat_history (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id     TEXT NOT NULL,
                    role        TEXT NOT NULL,
                    content     TEXT NOT NULL,
                    created_at  TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_chat_user ON chat_history(user_id, created_at);
                """
            )
            conn.execute(
                """INSERT OR IGNORE INTO profile
                   (user_id, stars, coins, streak, last_active, created_at, updated_at)
                   VALUES (?, 150, 85, 0, NULL, ?, ?)""",
                (DEFAULT_USER, _iso(_now()), _iso(_now())),
            )

    # ---------------- profile ----------------
    def get_profile(self, user_id: str = DEFAULT_USER) -> Dict[str, Any]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM profile WHERE user_id=?", (user_id,)
            ).fetchone()
            due = conn.execute(
                "SELECT COUNT(*) AS c FROM cards WHERE user_id=? AND due_at<=?",
                (user_id, _iso(_now())),
            ).fetchone()

        if row is None:
            return {
                "user_id": user_id, "stars": 0, "coins": 0,
                "streak": 0, "due_count": 0,
            }
        return {
            "user_id": row["user_id"],
            "stars": row["stars"],
            "coins": row["coins"],
            "streak": row["streak"],
            "last_active": row["last_active"],
            "due_count": int(due["c"]) if due else 0,
        }

    def earn(self, stars: int = 0, coins: int = 0, user_id: str = DEFAULT_USER) -> Dict[str, Any]:
        """加分并维护连续天数（今天已活跃则保持不变，断签则重置为 1）。"""
        now = _now()
        today = _today()
        with _write_lock, self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM profile WHERE user_id=?", (user_id,)
            ).fetchone()
            if row is None:
                conn.execute(
                    """INSERT INTO profile
                       (user_id, stars, coins, streak, last_active, created_at, updated_at)
                       VALUES (?, ?, ?, 1, ?, ?, ?)""",
                    (user_id, max(0, stars), max(0, coins), today.isoformat(),
                     _iso(now), _iso(now)),
                )
            else:
                last = row["last_active"]
                streak = row["streak"] or 0
                if last == today.isoformat():
                    pass
                elif last == (today - timedelta(days=1)).isoformat():
                    streak += 1
                else:
                    streak = 1
                conn.execute(
                    """UPDATE profile SET stars=?, coins=?, streak=?, last_active=?, updated_at=?
                       WHERE user_id=?""",
                    (max(0, row["stars"] + stars), max(0, row["coins"] + coins),
                     streak, today.isoformat(), _iso(now), user_id),
                )
        return self.get_profile(user_id)

    # ---------------- cards CRUD ----------------
    def _row_to_card(self, row: sqlite3.Row) -> Dict[str, Any]:
        now = _now()
        due_at = datetime.fromisoformat(row["due_at"])
        last_reviewed = row["last_reviewed_at"]
        reviewed_today = bool(
            last_reviewed and last_reviewed[:10] == now.date().isoformat()
        )
        return {
            "id": row["id"],
            "english": row["english"],
            "chinese": row["chinese"],
            "source": row["source"],
            "ease_factor": round(row["ease_factor"], 3),
            "interval_days": row["interval_days"],
            "repetitions": row["repetitions"],
            "lapses": row["lapses"],
            "due_at": row["due_at"],
            "due_in_days": max(0, (due_at.date() - now.date()).days),
            "is_due": due_at <= now,
            "reviewed": reviewed_today,
            "last_reviewed_at": last_reviewed,
            "date": (row["created_at"] or "")[:10],
            "created_at": row["created_at"],
        }

    def add_card(self, english: str, chinese: str = "", source: str = "",
                 user_id: str = DEFAULT_USER) -> Dict[str, Any]:
        english = (english or "").strip()
        if not english:
            raise ValueError("english is required")

        now = _now()
        with _write_lock, self._conn() as conn:
            existing = conn.execute(
                "SELECT * FROM cards WHERE user_id=? AND english=?", (user_id, english)
            ).fetchone()
            if existing:
                return self._row_to_card(existing)
            conn.execute(
                """INSERT INTO cards
                   (user_id, english, chinese, source, ease_factor, interval_days,
                    repetitions, lapses, due_at, created_at, updated_at)
                   VALUES (?,?,?,?,2.5,0,0,0,?,?,?)""",
                (user_id, english, chinese, source, _iso(now), _iso(now), _iso(now)),
            )
            row = conn.execute(
                "SELECT * FROM cards WHERE user_id=? AND english=?", (user_id, english)
            ).fetchone()
        return self._row_to_card(row)

    def list_cards(self, user_id: str = DEFAULT_USER) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM cards WHERE user_id=? ORDER BY created_at DESC", (user_id,)
            ).fetchall()
        return [self._row_to_card(r) for r in rows]

    def due_cards(self, user_id: str = DEFAULT_USER, limit: int = 50) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT * FROM cards WHERE user_id=? AND due_at<=?
                   ORDER BY due_at ASC LIMIT ?""",
                (user_id, _iso(_now()), limit),
            ).fetchall()
        return [self._row_to_card(r) for r in rows]

    def delete_card(self, card_id: int, user_id: str = DEFAULT_USER) -> bool:
        with _write_lock, self._conn() as conn:
            cur = conn.execute(
                "DELETE FROM cards WHERE id=? AND user_id=?", (card_id, user_id)
            )
            return cur.rowcount > 0

    # ---------------- SM-2 ----------------
    def review(self, card_id: int, quality: int, user_id: str = DEFAULT_USER) -> Dict[str, Any]:
        """quality: 0-5（<3 视为遗忘，回到艾宾浩斯短阶梯）"""
        quality = max(0, min(5, int(quality)))
        now = _now()

        with _write_lock, self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM cards WHERE id=? AND user_id=?", (card_id, user_id)
            ).fetchone()
            if row is None:
                raise KeyError("card not found")

            ef = row["ease_factor"]
            reps = row["repetitions"]
            interval = row["interval_days"]
            lapses = row["lapses"]

            if quality < 3:
                reps = 0
                lapses += 1
                step = min(lapses - 1, len(EBBINGHAUS_LADDER) - 1)
                interval = EBBINGHAUS_LADDER[max(0, step)]
            else:
                reps += 1
                if reps == 1:
                    interval = 1
                elif reps == 2:
                    interval = 6
                else:
                    interval = max(1, round(interval * ef))
                ef = ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
                ef = max(1.3, ef)

            due = now + timedelta(days=interval)
            conn.execute(
                """UPDATE cards SET ease_factor=?, interval_days=?, repetitions=?,
                   lapses=?, due_at=?, last_reviewed_at=?, updated_at=?
                   WHERE id=?""",
                (ef, interval, reps, lapses, _iso(due), _iso(now), _iso(now), card_id),
            )
            conn.execute(
                "INSERT INTO reviews (card_id, user_id, quality, reviewed_at) VALUES (?,?,?,?)",
                (card_id, user_id, quality, _iso(now)),
            )
            row = conn.execute("SELECT * FROM cards WHERE id=?", (card_id,)).fetchone()

        return self._row_to_card(row)

    def stats(self, user_id: str = DEFAULT_USER) -> Dict[str, Any]:
        """单连接内完成，避免 cards 与 reviews 取自不同事务造成不一致。"""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM cards WHERE user_id=?", (user_id,)
            ).fetchall()
            total_reviews = conn.execute(
                "SELECT COUNT(*) AS c FROM reviews WHERE user_id=?", (user_id,)
            ).fetchone()["c"]

        cards = [self._row_to_card(r) for r in rows]
        return {
            "total": len(cards),
            "due": sum(1 for c in cards if c["is_due"]),
            "mastered": sum(
                1 for c in cards if c["repetitions"] >= 5 and c["ease_factor"] >= 2.3
            ),
            "total_reviews": int(total_reviews),
            "avg_ease": round(sum(c["ease_factor"] for c in cards) / len(cards), 3)
            if cards else 0.0,
        }

    # ---------------- diagnostics (成长雷达留档) ----------------
    def save_diagnostic(self, report: Dict[str, Any],
                        user_id: str = DEFAULT_USER) -> Dict[str, Any]:
        now = _now()
        dims = (report or {}).get("dimensions") or {}
        scores = {}
        for k in DIMENSION_KEYS:
            d = dims.get(k)
            v = d.get("score") if isinstance(d, dict) else d
            try:
                scores[k] = max(0, min(100, int(round(float(v)))))
            except (TypeError, ValueError):
                scores[k] = None
        overall = (report or {}).get("overallFeedback") or ""

        with _write_lock, self._conn() as conn:
            cur = conn.execute(
                """INSERT INTO diagnostics (user_id, created_at, overall, scores, payload)
                   VALUES (?,?,?,?,?)""",
                (user_id, _iso(now), overall,
                 json.dumps(scores, ensure_ascii=False),
                 json.dumps(report or {}, ensure_ascii=False)),
            )
            new_id = cur.lastrowid
        return {"id": new_id, "created_at": _iso(now), "scores": scores}

    def list_diagnostics(self, user_id: str = DEFAULT_USER,
                         limit: int = 20) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT id, created_at, overall, scores FROM diagnostics
                   WHERE user_id=? ORDER BY created_at DESC LIMIT ?""",
                (user_id, limit),
            ).fetchall()
        out = []
        for r in rows:
            try:
                scores = json.loads(r["scores"])
            except (TypeError, ValueError):
                scores = {}
            out.append({
                "id": r["id"],
                "created_at": r["created_at"],
                "date": (r["created_at"] or "")[:10],
                "overall": r["overall"],
                "scores": scores,
            })
        return out

    def save_chat_messages(self, messages: List[Dict[str, str]],
                           user_id: str = DEFAULT_USER) -> int:
        """批量追加对话消息（role: user/assistant）"""
        now = _now()
        with _write_lock, self._conn() as conn:
            for m in messages or []:
                role = (m.get("role") or "").strip()
                content = (m.get("content") or "").strip()
                if not role or not content:
                    continue
                conn.execute(
                    """INSERT INTO chat_history (user_id, role, content, created_at)
                       VALUES (?,?,?,?)""",
                    (user_id, role, content, _iso(now)),
                )
        return len(messages or [])

    def list_chat_history(self, user_id: str = DEFAULT_USER,
                          limit: int = 200) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT id, role, content, created_at FROM chat_history
                   WHERE user_id=? ORDER BY created_at ASC, id ASC LIMIT ?""",
                (user_id, limit),
            ).fetchall()
        return [{"id": r["id"], "role": r["role"], "content": r["content"],
                 "created_at": r["created_at"]} for r in rows]

    def clear_chat_history(self, user_id: str = DEFAULT_USER) -> int:
        with _write_lock, self._conn() as conn:
            cur = conn.execute("DELETE FROM chat_history WHERE user_id=?", (user_id,))
            return cur.rowcount

    def latest_diagnostic(self, user_id: str = DEFAULT_USER) -> Optional[Dict[str, Any]]:
        with self._conn() as conn:
            row = conn.execute(
                """SELECT * FROM diagnostics WHERE user_id=?
                   ORDER BY created_at DESC LIMIT 1""",
                (user_id,),
            ).fetchone()
        if row is None:
            return None
        try:
            payload = json.loads(row["payload"])
        except (TypeError, ValueError):
            payload = {}
        return {"id": row["id"], "created_at": row["created_at"], "report": payload}

    def trend(self, user_id: str = DEFAULT_USER, limit: int = 12) -> Dict[str, Any]:
        """成长曲线：按时间正序返回每个维度的分数序列。"""
        history = list(reversed(self.list_diagnostics(user_id, limit)))
        series = {k: [h["scores"].get(k) for h in history] for k in DIMENSION_KEYS}
        return {
            "labels": [h["date"] for h in history],
            "series": series,
            "count": len(history),
        }

    # ---------------- backup & integrity ----------------
    def backup(self, keep: Optional[int] = None) -> Optional[str]:
        """每日滚动备份到 data/backup/，只保留最近 keep 份。"""
        keep = self.backup_keep if keep is None else keep
        if not os.path.exists(self.db_path):
            return None
        backup_dir = os.path.join(os.path.dirname(self.db_path), "backup")
        os.makedirs(backup_dir, exist_ok=True)
        target = os.path.join(backup_dir, f"jingjing-{_today().isoformat()}.db")
        try:
            if not os.path.exists(target):
                shutil.copy2(self.db_path, target)
            files = sorted(
                f for f in os.listdir(backup_dir)
                if f.startswith("jingjing-") and f.endswith(".db")
            )
            for stale in files[:-keep] if keep > 0 else []:
                try:
                    os.unlink(os.path.join(backup_dir, stale))
                except OSError:
                    pass
            return target
        except OSError as e:
            print(f"[SRS] backup failed: {e}")
            return None

    def integrity_check(self) -> bool:
        try:
            with self._conn() as conn:
                row = conn.execute("PRAGMA integrity_check").fetchone()
            ok = bool(row and row[0] == "ok")
            if not ok:
                print("[SRS] integrity_check failed:", row[0] if row else "no result")
            return ok
        except sqlite3.Error as e:
            print(f"[SRS] integrity_check error: {e}")
            return False

    # ---------------- migration / export ----------------
    def import_cards(self, items: List[Dict[str, Any]],
                     user_id: str = DEFAULT_USER) -> int:
        imported = 0
        with _write_lock:
            for it in items or []:
                english = (it.get("english") or "").strip()
                if not english:
                    continue
                with self._conn() as conn:
                    existing = conn.execute(
                        "SELECT id FROM cards WHERE user_id=? AND english=?",
                        (user_id, english),
                    ).fetchone()
                    if existing:
                        continue
                self.add_card(
                    english=english,
                    chinese=it.get("chinese") or "",
                    source=it.get("source") or "静静自习室",
                    user_id=user_id,
                )
                imported += 1
        return imported

    def export_all(self, user_id: str = DEFAULT_USER) -> Dict[str, Any]:
        """导出为可读 JSON，便于备份或迁移到别的机器。"""
        return {
            "version": 1,
            "exported_at": _iso(_now()),
            "user_id": user_id,
            "profile": self.get_profile(user_id),
            "cards": self.list_cards(user_id),
            "diagnostics": self.list_diagnostics(user_id, limit=200),
        }

    def ensure_profile(self, stars: Optional[int] = None, coins: Optional[int] = None,
                       streak: Optional[int] = None, user_id: str = DEFAULT_USER) -> Dict[str, Any]:
        """迁移旧 localStorage 数值（仅当库内还是初始值时采用，避免覆盖线上数据）。"""
        with _write_lock, self._conn() as conn:
            row = conn.execute("SELECT * FROM profile WHERE user_id=?", (user_id,)).fetchone()
            if row is None:
                return self.get_profile(user_id)
            new_stars = max(row["stars"], stars or 0)
            new_coins = max(row["coins"], coins or 0)
            new_streak = max(row["streak"], streak or 0)
            conn.execute(
                "UPDATE profile SET stars=?, coins=?, streak=?, updated_at=? WHERE user_id=?",
                (new_stars, new_coins, new_streak, _iso(_now()), user_id),
            )
        return self.get_profile(user_id)


srs = SRSStore()
srs.integrity_check()
srs.backup()
