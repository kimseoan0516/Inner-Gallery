"""
Inner Gallery — DB layer.
- DATABASE_URL 환경변수가 있으면 PostgreSQL (Supabase) 사용
- 없으면 SQLite (로컬 개발용)
"""
import os, json
from pathlib import Path
from contextlib import contextmanager

DATABASE_URL = os.environ.get("DATABASE_URL", "")
_USE_PG = bool(DATABASE_URL)

if _USE_PG:
    import psycopg2
    import psycopg2.extras
    IntegrityError = psycopg2.IntegrityError
else:
    import sqlite3
    _BASE    = Path(__file__).resolve().parent.parent
    _HF_DATA = Path("/data")
    _DB_PATH = str(_HF_DATA / "solace.db") if (_HF_DATA.exists() and _HF_DATA.is_dir()) else str(_BASE / "solace.db")
    IntegrityError = sqlite3.IntegrityError


# ── Connection ────────────────────────────────────────────────────────────────

class _PgConn:
    """psycopg2 connection wrapper: ? 플레이스홀더 자동 변환, dict 행 반환."""
    def __init__(self, pg):
        self._pg = pg

    def execute(self, sql, params=()):
        cur = self._pg.cursor()
        cur.execute(sql.replace('?', '%s'), params)
        return cur


@contextmanager
def conn():
    if _USE_PG:
        c = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            yield _PgConn(c)
            c.commit()
        except Exception:
            c.rollback()
            raise
        finally:
            c.close()
    else:
        c = sqlite3.connect(_DB_PATH)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys = ON")
        try:
            yield c
            c.commit()
        except Exception:
            c.rollback()
            raise
        finally:
            c.close()


def _ddl(sql: str) -> str:
    """SQLite DDL → PostgreSQL DDL 변환 (CREATE TABLE 공통화)."""
    if not _USE_PG:
        return sql
    return sql.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")


# ── init_db ───────────────────────────────────────────────────────────────────

def init_db():
    """모든 테이블 생성 (idempotent)."""
    with conn() as c:
        c.execute(_ddl("""
            CREATE TABLE IF NOT EXISTS users (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                username        TEXT UNIQUE NOT NULL,
                email           TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                created_at      TEXT NOT NULL
            )
        """))

        c.execute(_ddl("""
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
        """))
        c.execute("CREATE INDEX IF NOT EXISTS idx_artists_name       ON artists(name)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_artists_name_lower ON artists(LOWER(name))")

        c.execute(_ddl("""
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
        """))
        c.execute("CREATE INDEX IF NOT EXISTS idx_artworks_title  ON artworks(LOWER(title))")
        c.execute("CREATE INDEX IF NOT EXISTS idx_artworks_artist ON artworks(artist_id)")

        c.execute(_ddl("""
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

                ticket_memo      TEXT DEFAULT '',
                era_data         TEXT DEFAULT '',
                question_answers TEXT DEFAULT '{}',
                created_at  TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """))
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_journal_user_date
            ON journal_entries(user_id, date DESC)
        """)

        c.execute(_ddl("""
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                token      TEXT NOT NULL UNIQUE,
                expires_at TEXT NOT NULL,
                used       INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # 컬럼 마이그레이션
        if _USE_PG:
            c.execute("ALTER TABLE journal_entries ADD COLUMN IF NOT EXISTS era_data TEXT DEFAULT ''")
            c.execute("ALTER TABLE journal_entries ADD COLUMN IF NOT EXISTS ticket_exhibition TEXT DEFAULT ''")
            c.execute("ALTER TABLE journal_entries ADD COLUMN IF NOT EXISTS question_answers TEXT DEFAULT '{}'")
        else:
            for col, default in [("era_data", "''"), ("ticket_exhibition", "''"), ("question_answers", "'{}'")]:
                try:
                    c.execute(f"ALTER TABLE journal_entries ADD COLUMN {col} TEXT DEFAULT {default}")
                except Exception:
                    pass


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
    out = dict(entry)
    for col in _LIST_COLS:
        if col in out:
            out[col] = _dumps(out[col])
    return out

def row_to_entry(row) -> dict:
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

_LIST_COLS = """
    id, user_id, date, entry_type,
    artwork_title, artwork_artist, artwork_year,
    essay_title,
    moods, dominant_colors, thumbnail,
    pre_emotions, post_emotions,
    mood_color, mood_color_name, mood_note,
    sketch_title, sketch_image, ticket_memo, ticket_exhibition,
    created_at
"""

def get_journal(user_id: int) -> list[dict]:
    """목록용 — 대용량 텍스트 필드 제외해 응답 크기 최소화."""
    with conn() as c:
        rows = c.execute(
            f"SELECT {_LIST_COLS} FROM journal_entries WHERE user_id = ? ORDER BY date DESC",
            (user_id,),
        ).fetchall()
    return [row_to_entry(r) for r in rows]

def get_journal_entry(user_id: int, date: str) -> dict | None:
    """상세용 — 전체 컬럼 반환."""
    with conn() as c:
        row = c.execute(
            "SELECT * FROM journal_entries WHERE user_id = ? AND date = ?",
            (user_id, date),
        ).fetchone()
    return row_to_entry(row) if row else None

def save_journal_entry(user_id: int, entry: dict) -> int:
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
        "era_data", "question_answers",
    ]
    vals = [user_id] + [row.get(c, "") for c in cols[1:]]
    ph   = ','.join(['?'] * len(cols))
    with conn() as c:
        if _USE_PG:
            cur = c.execute(
                f"INSERT INTO journal_entries ({','.join(cols)}) VALUES ({ph}) RETURNING id",
                vals,
            )
            return cur.fetchone()['id']
        else:
            cur = c.execute(
                f"INSERT INTO journal_entries ({','.join(cols)}) VALUES ({ph})",
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

def update_journal_sketch(user_id: int, date: str, sketch: dict):
    with conn() as c:
        c.execute(
            """UPDATE journal_entries
               SET sketch_image = ?, sketch_title = ?, sketch_note = ?,
                   sketch_guide = ?, sketch_reflection = ?,
                   mood_color = CASE WHEN ? != '' THEN ? ELSE mood_color END,
                   mood_color_name = CASE WHEN ? != '' THEN ? ELSE mood_color_name END,
                   moods = ?
               WHERE user_id = ? AND date = ?""",
            (
                sketch.get("sketch_image", ""),
                sketch.get("sketch_title", ""),
                sketch.get("sketch_note", ""),
                sketch.get("sketch_guide", ""),
                sketch.get("sketch_reflection", ""),
                sketch.get("mood_color", ""), sketch.get("mood_color", ""),
                sketch.get("mood_color_name", ""), sketch.get("mood_color_name", ""),
                _dumps(sketch.get("moods", [])),
                user_id, date,
            ),
        )

def update_journal_note(user_id: int, date: str, note: str):
    with conn() as c:
        c.execute(
            "UPDATE journal_entries SET ticket_memo = ? WHERE user_id = ? AND date = ?",
            (note, user_id, date),
        )

def update_journal_exhibition(user_id: int, date: str, exhibition: str):
    with conn() as c:
        c.execute(
            "UPDATE journal_entries SET ticket_exhibition = ? WHERE user_id = ? AND date = ?",
            (exhibition, user_id, date),
        )

def delete_user_journal(user_id: int):
    with conn() as c:
        c.execute("DELETE FROM journal_entries WHERE user_id = ?", (user_id,))
