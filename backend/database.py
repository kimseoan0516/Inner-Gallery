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

        c.execute(_ddl("""
            CREATE TABLE IF NOT EXISTS artist_quotes (
                id     INTEGER PRIMARY KEY AUTOINCREMENT,
                quote  TEXT NOT NULL,
                artist TEXT NOT NULL
            )
        """))

        # 명언 초기 데이터 (테이블이 비어 있을 때만 삽입)
        count = c.execute("SELECT COUNT(*) FROM artist_quotes").fetchone()
        if (count[0] if isinstance(count, tuple) else list(count.values())[0]) == 0:
            _seed_quotes(c)

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


# ── 명언 ──────────────────────────────────────────────────────────────────────

_QUOTES_DATA = [
    # 레오나르도 다 빈치
    ("단순함은 궁극의 정교함이다.", "레오나르도 다 빈치"),
    ("배움은 마음을 젊게 한다.", "레오나르도 다 빈치"),
    ("눈은 영혼의 창이다.", "레오나르도 다 빈치"),
    ("장애물은 목표에서 눈을 뗄 때 보인다.", "레오나르도 다 빈치"),
    ("철저히 알기 위해서는 철저히 사랑해야 한다.", "레오나르도 다 빈치"),
    ("예술은 결코 완성되지 않는다. 단지 포기될 뿐이다.", "레오나르도 다 빈치"),
    ("지식이 없는 열정은 불 없는 연기와 같다.", "레오나르도 다 빈치"),
    ("인간의 발은 지상 최고의 공학 작품이다.", "레오나르도 다 빈치"),
    ("진정한 지혜는 모든 것에 의심을 품는 것이다.", "레오나르도 다 빈치"),
    ("시간은 가장 공평한 스승이다.", "레오나르도 다 빈치"),
    ("오랜 연습 없이 얻은 지식은 잃어버리기 쉽다.", "레오나르도 다 빈치"),
    ("사랑 없는 예술가는 존재할 수 없다.", "레오나르도 다 빈치"),
    ("물은 자연의 원동력이다.", "레오나르도 다 빈치"),
    ("행동이야말로 모든 지식의 완성이다.", "레오나르도 다 빈치"),
    # 미켈란젤로
    ("자연을 깊이 들여다볼수록, 모든 것을 더 잘 이해하게 된다.", "미켈란젤로"),
    ("나는 아직도 배우고 있다.", "미켈란젤로"),
    ("대리석 안에 천사가 있다. 나는 그를 해방시킬 뿐이다.", "미켈란젤로"),
    ("위험한 것은 목표가 너무 낮아서 달성하는 것이다.", "미켈란젤로"),
    ("천재성이란 영원한 인내다.", "미켈란젤로"),
    ("나는 내 영혼으로 그린다. 몸은 단지 도구일 뿐이다.", "미켈란젤로"),
    ("조각은 이미 돌 안에 있다. 나는 그것을 꺼낼 뿐이다.", "미켈란젤로"),
    ("아름다움의 기준은 비율이 아니라 영혼에 있다.", "미켈란젤로"),
    ("나는 신이 내게 준 재능을 낭비할 수 없다.", "미켈란젤로"),
    ("완성된 작품은 시작할 때의 두려움을 이긴 결과다.", "미켈란젤로"),
    ("가장 큰 위험은 꿈이 이루어지지 않는 것이 아니라, 꿈조차 꾸지 않는 것이다.", "미켈란젤로"),
    ("완벽함은 사소한 것들로 이루어지지만, 완벽함 자체는 사소하지 않다.", "미켈란젤로"),
    # 빈센트 반 고흐
    ("창조하는 자는 파괴하는 자이기도 하다.", "빈센트 반 고흐"),
    ("나는 별을 꿈꾸며 그림을 그린다.", "빈센트 반 고흐"),
    ("위대한 것은 단번에 오지 않는다. 작은 일들이 쌓여 위대해진다.", "빈센트 반 고흐"),
    ("고통은 지나가지만, 아름다움은 남는다.", "빈센트 반 고흐"),
    ("나는 그림 속에서 위안을 찾는다.", "빈센트 반 고흐"),
    ("사람들은 변하지 않는다. 단지 더 자기 자신이 될 뿐이다.", "빈센트 반 고흐"),
    ("나는 평범한 것들 속에서 위대함을 본다.", "빈센트 반 고흐"),
    ("무언가를 그리는 방법을 배우려면, 그것을 사랑하는 법을 배워야 한다.", "빈센트 반 고흐"),
    ("나는 현실이 아닌 감정을 그린다.", "빈센트 반 고흐"),
    ("나는 하늘의 별들을 볼 때마다 인생이 여전히 아름답다고 생각한다.", "빈센트 반 고흐"),
    ("내가 겪은 고통은 그림의 원료가 되었다.", "빈센트 반 고흐"),
    ("예술가는 자연을 거울에 비추는 것이 아니라, 그것을 통해 자신을 표현한다.", "빈센트 반 고흐"),
    ("사람들은 내 그림이 너무 빨리 그려졌다고 말한다. 하지만 그 뒤에는 수년간의 연습이 있다.", "빈센트 반 고흐"),
    ("사랑하는 것이 있다면, 그것을 그려라.", "빈센트 반 고흐"),
    ("슬픔은 영원하지 않다.", "빈센트 반 고흐"),
    # 파블로 피카소
    ("나는 실패를 두려워하지 않는다. 도전하지 않는 것이 두렵다.", "파블로 피카소"),
    ("모든 아이는 예술가다. 문제는 어른이 되어서도 예술가로 남는 것이다.", "파블로 피카소"),
    ("나는 보이는 것을 그리지 않는다. 느끼는 것을 그린다.", "파블로 피카소"),
    ("영감은 존재한다. 하지만 당신이 일하는 동안 찾아와야 한다.", "파블로 피카소"),
    ("예술은 우리에게 진실을 깨닫게 해주는 거짓말이다.", "파블로 피카소"),
    ("나쁜 예술가는 모방하고, 위대한 예술가는 훔친다.", "파블로 피카소"),
    ("창조의 모든 행위는 먼저 파괴의 행위다.", "파블로 피카소"),
    ("나는 찾지 않는다. 발견한다.", "파블로 피카소"),
    ("예술은 우리 일상의 먼지를 씻어 영혼을 보여준다.", "파블로 피카소"),
    ("색채는 감정의 언어다.", "파블로 피카소"),
    ("젊음과 나이는 숫자가 아니다. 정신이다.", "파블로 피카소"),
    ("행동이 모든 성공의 기본 열쇠다.", "파블로 피카소"),
    # 클로드 모네
    ("예술을 배우는 데 4년이 걸렸지만, 어린이처럼 그리는 데 평생이 걸렸다.", "클로드 모네"),
    ("색은 나의 하루의 집착이자, 기쁨이며, 고통이다.", "클로드 모네"),
    ("나는 빛을 그린다. 사물이 아니라.", "클로드 모네"),
    ("나는 자연의 변화에 매혹되었다.", "클로드 모네"),
    ("그림은 인내와 관찰의 산물이다.", "클로드 모네"),
    ("눈이 제대로 보는 법을 배우는 것이 예술이다.", "클로드 모네"),
    ("나는 순간을 포착하고 싶다. 그것이 진짜 현실임을 보여주고 싶다.", "클로드 모네"),
    ("물은 내 삶의 전부다.", "클로드 모네"),
    ("정원은 내 삶에서 가장 아름다운 작품이다.", "클로드 모네"),
    ("빛은 모든 것의 주인공이다.", "클로드 모네"),
    # 오귀스트 로댕
    ("다른 사람들이 본다고 생각하는 것이 아니라, 내가 보는 것을 그린다.", "오귀스트 로댕"),
    ("조각이란 필요 없는 것을 제거하는 것이다.", "오귀스트 로댕"),
    ("아름다움은 어디에나 있다. 우리의 눈이 그것을 볼 수 없을 뿐이다.", "오귀스트 로댕"),
    ("두 손은 신이 인간에게 준 가장 훌륭한 도구다.", "오귀스트 로댕"),
    ("나는 자연을 발명하지 않는다. 단지 드러낼 뿐이다.", "오귀스트 로댕"),
    ("인내는 예술가의 가장 중요한 덕목이다.", "오귀스트 로댕"),
    ("진정한 아름다움은 내면에서 온다.", "오귀스트 로댕"),
    ("상상력 없이는 아무것도 만들 수 없다.", "오귀스트 로댕"),
    # 폴 세잔
    ("나는 단지 대리석을 빚는 것이 아니라, 인간의 내면을 드러낸다.", "폴 세잔"),
    ("예술은 자연과 평행하는 조화다.", "폴 세잔"),
    ("그림은 눈으로 생각하는 것이다.", "폴 세잔"),
    ("나는 자연으로부터 배우기를 멈추지 않겠다.", "폴 세잔"),
    ("예술은 개인적인 감각의 조화다.", "폴 세잔"),
    ("화가는 자신의 눈을 신뢰해야 한다.", "폴 세잔"),
    ("자연을 앞에 두고 두려워하지 마라.", "폴 세잔"),
    ("회화는 두뇌와 눈의 결합이다.", "폴 세잔"),
    ("나는 자연을 원기둥, 구, 원뿔로 다룬다.", "폴 세잔"),
    # 살바도르 달리
    ("나와 미친 사람의 유일한 차이는 나는 미치지 않았다는 것이다.", "살바도르 달리"),
    ("나는 마약을 하지 않는다. 내 자신이 마약이다.", "살바도르 달리"),
    ("상상력 없는 사람만이 현실을 진지하게 받아들인다.", "살바도르 달리"),
    ("진정한 창의력은 두려움을 모른다.", "살바도르 달리"),
    ("모든 것이 예술이 될 수 있다. 심지어 나 자신도.", "살바도르 달리"),
    ("아침에 일어나는 것 자체가 놀라운 일이다.", "살바도르 달리"),
    ("나는 매일 아침 최고의 기쁨을 느낀다. 살바도르 달리가 된다는 것을.", "살바도르 달리"),
    # 프리다 칼로
    ("완벽주의자가 되어라. 불완전함은 예술이 아니다.", "프리다 칼로"),
    ("나는 나 자신을 잘 알기 때문에 나 자신을 그린다.", "프리다 칼로"),
    ("고통은 나를 더 강하게 만들었다.", "프리다 칼로"),
    ("내 상처가 나의 예술이 되었다.", "프리다 칼로"),
    ("나는 현실을 그리는 것이 아니라, 내가 아는 현실을 그린다.", "프리다 칼로"),
    ("자신을 사랑하라. 그것이 모든 것의 시작이다.", "프리다 칼로"),
    ("나는 슬픔을 그리지 않는다. 하지만 내 그림은 가장 솔직한 표현이다.", "프리다 칼로"),
    ("나는 발로 날아다니는 것이 아니라, 붓으로 난다.", "프리다 칼로"),
    # 렘브란트
    ("고통, 쾌락, 죽음은 선이 아니라 과정일 뿐이다.", "렘브란트"),
    ("빛이 없는 곳에 진실이 있다.", "렘브란트"),
    ("나는 그림 속에서 내가 원하는 자유를 찾는다.", "렘브란트"),
    ("인간의 얼굴에는 우주 전체가 담겨 있다.", "렘브란트"),
    ("그림자는 빛만큼 중요하다.", "렘브란트"),
    ("빛과 그림자의 대비가 진실을 드러낸다.", "렘브란트"),
    ("위대한 그림은 관람자를 불편하게 만들어야 한다.", "렘브란트"),
    # 알브레히트 뒤러
    ("나는 명성이 아닌 자유를 추구한다.", "알브레히트 뒤러"),
    ("아름다움이란 무엇인지 나는 모른다. 그것은 모든 것 속에 존재한다.", "알브레히트 뒤러"),
    ("예술은 자연 속에 숨어 있다. 그것을 끄집어내는 자가 예술가다.", "알브레히트 뒤러"),
    ("좋은 그림은 수백 년이 지나도 살아있다.", "알브레히트 뒤러"),
    ("나는 선 하나하나에 내 삶을 담는다.", "알브레히트 뒤러"),
    ("진정한 예술가는 자연에서 배운다.", "알브레히트 뒤러"),
    ("비율은 아름다움의 어머니다.", "알브레히트 뒤러"),
    # 외젠 들라크루아
    ("연습 없이는 어떤 재능도 꽃피울 수 없다.", "외젠 들라크루아"),
    ("예술가는 열정 없이는 존재할 수 없다.", "외젠 들라크루아"),
    ("규칙이란 그것을 깨뜨릴 줄 아는 자를 위해 존재한다.", "외젠 들라크루아"),
    ("그림은 생각보다 먼저 느껴져야 한다.", "외젠 들라크루아"),
    ("색채는 피아노 건반이고, 눈은 건반을 치는 손이며, 영혼은 피아노다.", "외젠 들라크루아"),
    ("상상력은 예술가의 가장 위대한 선물이다.", "외젠 들라크루아"),
    ("자유는 예술의 숨결이다.", "외젠 들라크루아"),
    # 폴 고갱
    ("붓질 하나에도 영혼이 담겨야 한다.", "폴 고갱"),
    ("나는 문명에서 도망쳐 자연 속에서 진실을 찾았다.", "폴 고갱"),
    ("예술은 추상이다. 자연 앞에서 꿈을 꾸고, 그 꿈에서 나온 창조물을 생각하라.", "폴 고갱"),
    ("색은 그 자체로 언어다.", "폴 고갱"),
    ("나는 어디서 왔는가? 나는 누구인가? 나는 어디로 가는가?", "폴 고갱"),
    ("예술가가 되려면 먼저 자신을 버려야 한다.", "폴 고갱"),
    ("나는 위대한 예술가다. 그것을 알기 때문에 나는 견딜 수 있다.", "폴 고갱"),
    # 에드가 드가
    ("나는 원시적인 것 속에서 진정한 아름다움을 발견했다.", "에드가 드가"),
    ("예술은 즉흥적인 것이 아니다. 그것은 규칙과 열정의 결합이다.", "에드가 드가"),
    ("나는 자연을 보이는 대로 그리지 않는다. 내가 기억하는 대로 그린다.", "에드가 드가"),
    ("그림은 한 번에 완성되지 않는다. 수천 번의 붓질 끝에 완성된다.", "에드가 드가"),
    ("움직임 속에 진실이 있다.", "에드가 드가"),
    ("오직 관찰하는 자만이 그릴 수 있다.", "에드가 드가"),
    # 구스타프 클림트
    ("회화는 특별한 삶의 방식이다.", "구스타프 클림트"),
    ("황금은 가장 신성한 색이다.", "구스타프 클림트"),
    ("나는 그림 안에 내 모든 것을 담는다.", "구스타프 클림트"),
    ("아름다움은 꾸밈이 아니라 진실에서 나온다.", "구스타프 클림트"),
    ("예술은 한 번도 완전히 설명된 적이 없다. 그것이 예술이 존재하는 이유다.", "구스타프 클림트"),
    ("삶과 죽음은 하나의 선 위에 있다.", "구스타프 클림트"),
    # 카스파르 다비트 프리드리히
    ("나는 나 자신을 그리지 않는다. 다른 사람들, 특히 여성들을 그린다.", "카스파르 다비트 프리드리히"),
    ("예술가는 눈앞에 있는 것만 그려서는 안 된다. 내면에 보이는 것도 그려야 한다.", "카스파르 다비트 프리드리히"),
    ("고독은 자연 속에서만 완전히 느껴진다.", "카스파르 다비트 프리드리히"),
    ("안개 속에서 진실이 드러난다.", "카스파르 다비트 프리드리히"),
    ("자연은 신의 언어다.", "카스파르 다비트 프리드리히"),
    # 얀 반 에이크
    ("숭고함은 자연의 광대함 앞에서만 경험할 수 있다.", "얀 반 에이크"),
    ("나는 할 수 있는 한 최선을 다했다.", "얀 반 에이크"),
    ("세밀함 속에 신의 존재가 있다.", "얀 반 에이크"),
    # 산드로 보티첼리
    ("빛은 그림의 생명이다.", "산드로 보티첼리"),
    ("아름다움은 보는 자의 마음속에 있다.", "산드로 보티첼리"),
    ("신화 속에서 나는 인간의 진실을 찾는다.", "산드로 보티첼리"),
    ("봄처럼 아름다운 것은 무상하기 때문에 더 소중하다.", "산드로 보티첼리"),
    # 엘 그레코
    ("선의 흐름 속에 감정이 담긴다.", "엘 그레코"),
    ("색채는 나의 언어다.", "엘 그레코"),
    ("나는 신을 그린다. 그래서 나는 빛을 그린다.", "엘 그레코"),
    ("인간의 영혼은 하늘을 향해 뻗어 있다.", "엘 그레코"),
    # 얀 베르메르
    ("나는 태양이 싫다. 그것은 나의 빛을 방해한다.", "얀 베르메르"),
    ("빛은 그림의 영혼이다.", "얀 베르메르"),
    ("일상의 순간 속에 영원이 담겨 있다.", "얀 베르메르"),
    ("창문을 통해 들어오는 빛은 신의 선물이다.", "얀 베르메르"),
    ("평범한 것을 비범하게 보이게 하는 것이 예술이다.", "얀 베르메르"),
]

def _seed_quotes(c):
    for quote, artist in _QUOTES_DATA:
        c.execute("INSERT INTO artist_quotes (quote, artist) VALUES (?, ?)", (quote, artist))

def get_random_quote() -> dict:
    with conn() as c:
        row = c.execute("SELECT quote, artist FROM artist_quotes ORDER BY RANDOM() LIMIT 1").fetchone()
    return dict(row) if row else {"quote": "", "artist": ""}
