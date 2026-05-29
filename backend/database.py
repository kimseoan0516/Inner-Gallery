"""
Inner Gallery — SQLite 데이터베이스 계층.

Tables:
  users           — 계정 (auth.py 관리)
  artists         — 화가 정보 (Kaggle CSV 임포트)
  artworks        — 작품 메타데이터
  journal_entries — 사용자 감상 + 스케치 기록
"""
import sqlite3, json
from pathlib import Path

_BASE   = Path(__file__).resolve().parent.parent
DB_PATH = str(_BASE / "solace.db")


def conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    return c


def init_db():
    """모든 테이블 생성 (idempotent — 매 시작 시 호출해도 안전)."""
    with conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                username        TEXT    UNIQUE NOT NULL,
                email           TEXT    UNIQUE NOT NULL,
                hashed_password TEXT    NOT NULL,
                created_at      TEXT    NOT NULL
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS artists (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                name           TEXT NOT NULL,
                name_ko        TEXT DEFAULT '',
                nationality    TEXT DEFAULT '',
                years          TEXT DEFAULT '',
                genre          TEXT DEFAULT '',
                bio            TEXT DEFAULT '',
                wikipedia      TEXT DEFAULT '',
                painting_count INTEGER DEFAULT 0,
                created_at     TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_artists_name       ON artists(name)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_artists_name_lower ON artists(LOWER(name))")

        c.execute("""
            CREATE TABLE IF NOT EXISTS artworks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT DEFAULT '',
                title_ko    TEXT DEFAULT '',
                artist_id   INTEGER REFERENCES artists(id) ON DELETE SET NULL,
                year        TEXT DEFAULT '',
                medium      TEXT DEFAULT '',
                museum      TEXT DEFAULT '',
                genre       TEXT DEFAULT '',
                description TEXT DEFAULT '',
                created_at  TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_artworks_title  ON artworks(LOWER(title))")
        c.execute("CREATE INDEX IF NOT EXISTS idx_artworks_artist ON artworks(artist_id)")

        # essay_body, questions, moods 등 리스트 컬럼은 JSON 텍스트로 직렬화 저장
        c.execute("""
            CREATE TABLE IF NOT EXISTS journal_entries (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                date          TEXT    NOT NULL,
                entry_type    TEXT    DEFAULT '',

                artwork_title  TEXT DEFAULT '',
                artwork_artist TEXT DEFAULT '',
                artwork_year   TEXT DEFAULT '',

                essay_title TEXT DEFAULT '',
                essay_body  TEXT DEFAULT '[]',
                questions   TEXT DEFAULT '[]',
                comfort     TEXT DEFAULT '',
                reflection  TEXT DEFAULT '',

                moods           TEXT DEFAULT '[]',
                dominant_colors TEXT DEFAULT '[]',
                thumbnail       TEXT DEFAULT '',
                pre_emotions    TEXT DEFAULT '[]',
                post_emotions   TEXT DEFAULT '[]',
                mood_color      TEXT DEFAULT '',
                mood_color_name TEXT DEFAULT '',
                mood_note       TEXT DEFAULT '',

                sketch_image      TEXT DEFAULT '',
                sketch_title      TEXT DEFAULT '',
                sketch_note       TEXT DEFAULT '',
                sketch_guide      TEXT DEFAULT '',
                sketch_reflection TEXT DEFAULT '',

                ticket_memo TEXT DEFAULT '',
                created_at  TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_journal_user_date
            ON journal_entries(user_id, date DESC)
        """)


# ── 직렬화 헬퍼 ───────────────────────────────────────────────────────────────

_LIST_COLS = {
    "essay_body", "questions", "moods",
    "dominant_colors", "pre_emotions", "post_emotions",
}

def _dumps(v) -> str:
    return json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else (v or "")

def _loads(v, default=None):
    if v is None:
        return default
    try:
        return json.loads(v)
    except Exception:
        return default

def entry_to_row(entry: dict) -> dict:
    """JournalEntry dict → INSERT용 dict (리스트 컬럼 JSON 직렬화)."""
    out = dict(entry)
    for col in _LIST_COLS:
        if col in out:
            out[col] = _dumps(out[col])
    return out

def row_to_entry(row) -> dict:
    """DB row → dict (리스트 컬럼 역직렬화)."""
    d = dict(row)
    for col in _LIST_COLS:
        if col in d:
            d[col] = _loads(d[col], default=[])
    return d


# ── 화가 헬퍼 ─────────────────────────────────────────────────────────────────

def get_artist_by_name(name: str) -> dict | None:
    with conn() as c:
        row = c.execute(
            "SELECT * FROM artists WHERE LOWER(name) = LOWER(?)", (name,)
        ).fetchone()
    return dict(row) if row else None

def search_artists(query: str, limit: int = 10) -> list[dict]:
    q = f"%{query.lower()}%"
    with conn() as c:
        rows = c.execute(
            "SELECT * FROM artists WHERE LOWER(name) LIKE ? LIMIT ?", (q, limit)
        ).fetchall()
    return [dict(r) for r in rows]


# ── 저널 헬퍼 ─────────────────────────────────────────────────────────────────

def get_journal(user_id: int) -> list[dict]:
    with conn() as c:
        rows = c.execute(
            "SELECT * FROM journal_entries WHERE user_id = ? ORDER BY date DESC",
            (user_id,),
        ).fetchall()
    return [row_to_entry(r) for r in rows]

def save_journal_entry(user_id: int, entry: dict) -> int:
    """저널 항목 저장. 새 row id 반환."""
    row  = entry_to_row(entry)
    cols = [
        "user_id", "date", "entry_type",
        "artwork_title", "artwork_artist", "artwork_year",
        "essay_title", "essay_body", "questions", "comfort", "reflection",
        "moods", "dominant_colors", "thumbnail",
        "pre_emotions", "post_emotions",
        "mood_color", "mood_color_name", "mood_note",
        "sketch_image", "sketch_title", "sketch_note",
        "sketch_guide", "sketch_reflection", "ticket_memo",
    ]
    vals = [user_id] + [row.get(c, "") for c in cols[1:]]
    with conn() as c:
        cur = c.execute(
            f"INSERT INTO journal_entries ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})",
            vals,
        )
        return cur.lastrowid

def delete_journal_entry(user_id: int, date: str) -> int:
    with conn() as c:
        cur = c.execute(
            "DELETE FROM journal_entries WHERE user_id = ? AND date = ?",
            (user_id, date),
        )
        return cur.rowcount

def update_journal_note(user_id: int, date: str, note: str):
    with conn() as c:
        c.execute(
            "UPDATE journal_entries SET ticket_memo = ? WHERE user_id = ? AND date = ?",
            (note, user_id, date),
        )

def delete_user_journal(user_id: int):
    with conn() as c:
        c.execute("DELETE FROM journal_entries WHERE user_id = ?", (user_id,))
