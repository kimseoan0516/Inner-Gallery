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
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                quote     TEXT NOT NULL,
                quote_en  TEXT DEFAULT '',
                artist    TEXT NOT NULL,
                artist_en TEXT DEFAULT ''
            )
        """))

        # 컬럼 마이그레이션
        if _USE_PG:
            c.execute("ALTER TABLE artist_quotes ADD COLUMN IF NOT EXISTS quote_en TEXT DEFAULT ''")
            c.execute("ALTER TABLE artist_quotes ADD COLUMN IF NOT EXISTS artist_en TEXT DEFAULT ''")
            c.execute("ALTER TABLE journal_entries ADD COLUMN IF NOT EXISTS era_data TEXT DEFAULT ''")
            c.execute("ALTER TABLE journal_entries ADD COLUMN IF NOT EXISTS ticket_exhibition TEXT DEFAULT ''")
            c.execute("ALTER TABLE journal_entries ADD COLUMN IF NOT EXISTS question_answers TEXT DEFAULT '{}'")
        else:
            for col, default in [("quote_en", "''"), ("artist_en", "''")]:
                try: c.execute(f"ALTER TABLE artist_quotes ADD COLUMN {col} TEXT DEFAULT {default}")
                except: pass
            for col, default in [("era_data", "''"), ("ticket_exhibition", "''"), ("question_answers", "'{}'")]:
                try:
                    c.execute(f"ALTER TABLE journal_entries ADD COLUMN {col} TEXT DEFAULT {default}")
                except Exception:
                    pass

        # 명언 초기 데이터 (기존 데이터 삭제 후 갱신)
        c.execute("DELETE FROM artist_quotes")
        _seed_quotes(c)


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

_SELECT_COLS = """
    id, user_id, date, entry_type,
    artwork_title, artwork_artist, artwork_year,
    essay_title,
    moods, dominant_colors,
    pre_emotions, post_emotions,
    mood_color, mood_color_name, mood_note,
    sketch_title, ticket_memo, ticket_exhibition,
    created_at
"""

def get_journal(user_id: int) -> list[dict]:
    """목록용 — 대용량 텍스트 필드 제외해 응답 크기 최소화."""
    with conn() as c:
        rows = c.execute(
            f"SELECT {_SELECT_COLS} FROM journal_entries WHERE user_id = ? ORDER BY date DESC",
            (user_id,),
        ).fetchall()
    return [row_to_entry(r) for r in rows]

def get_journal_thumbs(user_id: int, dates: list[str]) -> dict[str, str]:
    """날짜 목록에 해당하는 thumbnail(또는 sketch_image) 만 반환."""
    if not dates:
        return {}
    ph = ','.join(['?'] * len(dates))
    with conn() as c:
        rows = c.execute(
            f"SELECT date, thumbnail, sketch_image, entry_type FROM journal_entries WHERE user_id = ? AND date IN ({ph})",
            [user_id] + list(dates),
        ).fetchall()
    result = {}
    for r in rows:
        d = dict(r)
        img = d.get('thumbnail') or ''
        if not img and d.get('entry_type') == 'sketch':
            img = d.get('sketch_image') or ''
        result[d['date']] = img
    return result

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
    ("단순함은 궁극의 정교함이다.", "Simplicity is the ultimate sophistication.", "레오나르도 다 빈치", "Leonardo da Vinci"),
    ("배움은 마음을 젊게 한다.", "Learning keeps the mind young.", "레오나르도 다 빈치", "Leonardo da Vinci"),
    ("눈은 영혼의 창이다.", "The eye is the window of the soul.", "레오나르도 다 빈치", "Leonardo da Vinci"),
    ("장애물은 목표에서 눈을 뗄 때 보인다.", "Obstacles appear when you take your eyes off the goal.", "레오나르도 다 빈치", "Leonardo da Vinci"),
    ("철저히 알기 위해서는 철저히 사랑해야 한다.", "To know thoroughly, one must love thoroughly.", "레오나르도 다 빈치", "Leonardo da Vinci"),
    ("예술은 결코 완성되지 않는다. 단지 포기될 뿐이다.", "Art is never finished, only abandoned.", "레오나르도 다 빈치", "Leonardo da Vinci"),
    ("지식이 없는 열정은 불 없는 연기와 같다.", "Knowledge without passion is smoke without fire.", "레오나르도 다 빈치", "Leonardo da Vinci"),
    ("인간의 발은 지상 최고의 공학 작품이다.", "The human foot is the greatest engineering masterpiece on earth.", "레오나르도 다 빈치", "Leonardo da Vinci"),
    ("진정한 지혜는 모든 것에 의심을 품는 것이다.", "True wisdom is questioning everything.", "레오나르도 다 빈치", "Leonardo da Vinci"),
    ("시간은 가장 공평한 스승이다.", "Time is the fairest teacher.", "레오나르도 다 빈치", "Leonardo da Vinci"),
    ("오랜 연습 없이 얻은 지식은 잃어버리기 쉽다.", "Knowledge gained without long practice is easily lost.", "레오나르도 다 빈치", "Leonardo da Vinci"),
    ("사랑 없는 예술가는 존재할 수 없다.", "An artist without love cannot exist.", "레오나르도 다 빈치", "Leonardo da Vinci"),
    ("물은 자연의 원동력이다.", "Water is the driving force of nature.", "레오나르도 다 빈치", "Leonardo da Vinci"),
    ("행동이야말로 모든 지식의 완성이다.", "Action is the ultimate fulfillment of all knowledge.", "레오나르도 다 빈치", "Leonardo da Vinci"),
    ("자연을 깊이 들여다볼수록, 모든 것을 더 잘 이해하게 된다.", "The more I look deeply into nature, the better I understand everything.", "미켈란젤로", "Michelangelo"),
    ("나는 아직도 배우고 있다.", "I am still learning.", "미켈란젤로", "Michelangelo"),
    ("대리석 안에 천사가 있다. 나는 그를 해방시킬 뿐이다.", "There is an angel in the marble, and I set him free.", "미켈란젤로", "Michelangelo"),
    ("위험한 것은 목표가 너무 낮아서 달성하는 것이다.", "The greatest danger is not that our aim is too high and we miss it, but that it is too low and we achieve it.", "미켈란젤로", "Michelangelo"),
    ("천재성이란 영원한 인내다.", "Genius is eternal patience.", "미켈란젤로", "Michelangelo"),
    ("나는 내 영혼으로 그린다. 몸은 단지 도구일 뿐이다.", "I paint with my soul. The body is merely a tool.", "미켈란젤로", "Michelangelo"),
    ("조각은 이미 돌 안에 있다. 나는 그것을 꺼낼 뿐이다.", "The sculpture is already in the stone. I just release it.", "미켈란젤로", "Michelangelo"),
    ("아름다움의 기준은 비율이 아니라 영혼에 있다.", "The standard of beauty lies not in proportion but in the soul.", "미켈란젤로", "Michelangelo"),
    ("나는 신이 내게 준 재능을 낭비할 수 없다.", "I cannot waste the talent God has given me.", "미켈란젤로", "Michelangelo"),
    ("완성된 작품은 시작할 때의 두려움을 이긴 결과다.", "A finished work is the result of overcoming the fear of beginning.", "미켈란젤로", "Michelangelo"),
    ("가장 큰 위험은 꿈이 이루어지지 않는 것이 아니라, 꿈조차 꾸지 않는 것이다.", "The greatest danger is not that we fail to achieve our dreams, but that we have no dreams at all.", "미켈란젤로", "Michelangelo"),
    ("완벽함은 사소한 것들로 이루어지지만, 완벽함 자체는 사소하지 않다.", "Perfection is composed of trifles, but perfection itself is no trifle.", "미켈란젤로", "Michelangelo"),
    ("창조하는 자는 파괴하는 자이기도 하다.", "The creator is also the destroyer.", "빈센트 반 고흐", "Vincent van Gogh"),
    ("나는 별을 꿈꾸며 그림을 그린다.", "I dream of painting, and then I paint my dream.", "빈센트 반 고흐", "Vincent van Gogh"),
    ("위대한 것은 단번에 오지 않는다. 작은 일들이 쌓여 위대해진다.", "Great things do not come all at once. Small things accumulate and become great.", "빈센트 반 고흐", "Vincent van Gogh"),
    ("고통은 지나가지만, 아름다움은 남는다.", "The pain passes, but the beauty remains.", "빈센트 반 고흐", "Vincent van Gogh"),
    ("나는 그림 속에서 위안을 찾는다.", "I find comfort in my paintings.", "빈센트 반 고흐", "Vincent van Gogh"),
    ("사람들은 변하지 않는다. 단지 더 자기 자신이 될 뿐이다.", "People don\'t change. They just become more themselves.", "빈센트 반 고흐", "Vincent van Gogh"),
    ("나는 평범한 것들 속에서 위대함을 본다.", "I see greatness in ordinary things.", "빈센트 반 고흐", "Vincent van Gogh"),
    ("무언가를 그리는 방법을 배우려면, 그것을 사랑하는 법을 배워야 한다.", "To learn to draw something, you must first learn to love it.", "빈센트 반 고흐", "Vincent van Gogh"),
    ("나는 현실이 아닌 감정을 그린다.", "I paint emotions, not reality.", "빈센트 반 고흐", "Vincent van Gogh"),
    ("나는 하늘의 별들을 볼 때마다 인생이 여전히 아름답다고 생각한다.", "Every time I look at the stars in the sky, I think life is still beautiful.", "빈센트 반 고흐", "Vincent van Gogh"),
    ("내가 겪은 고통은 그림의 원료가 되었다.", "The suffering I endured became the raw material of my paintings.", "빈센트 반 고흐", "Vincent van Gogh"),
    ("예술가는 자연을 거울에 비추는 것이 아니라, 그것을 통해 자신을 표현한다.", "An artist does not mirror nature but expresses himself through it.", "빈센트 반 고흐", "Vincent van Gogh"),
    ("사람들은 내 그림이 너무 빨리 그려졌다고 말한다. 하지만 그 뒤에는 수년간의 연습이 있다.", "People say my paintings were done too quickly, but years of practice lie behind them.", "빈센트 반 고흐", "Vincent van Gogh"),
    ("사랑하는 것이 있다면, 그것을 그려라.", "If you love something, paint it.", "빈센트 반 고흐", "Vincent van Gogh"),
    ("슬픔은 영원하지 않다.", "Sorrow does not last forever.", "빈센트 반 고흐", "Vincent van Gogh"),
    ("나는 실패를 두려워하지 않는다. 도전하지 않는 것이 두렵다.", "I am not afraid of failure. What I fear is not trying.", "파블로 피카소", "Pablo Picasso"),
    ("모든 아이는 예술가다. 문제는 어른이 되어서도 예술가로 남는 것이다.", "Every child is an artist. The problem is remaining an artist when you grow up.", "파블로 피카소", "Pablo Picasso"),
    ("나는 보이는 것을 그리지 않는다. 느끼는 것을 그린다.", "I don\'t paint what I see. I paint what I feel.", "파블로 피카소", "Pablo Picasso"),
    ("영감은 존재한다. 하지만 당신이 일하는 동안 찾아와야 한다.", "Inspiration exists, but it has to find you working.", "파블로 피카소", "Pablo Picasso"),
    ("예술은 우리에게 진실을 깨닫게 해주는 거짓말이다.", "Art is a lie that makes us realize the truth.", "파블로 피카소", "Pablo Picasso"),
    ("나쁜 예술가는 모방하고, 위대한 예술가는 훔친다.", "Bad artists copy, great artists steal.", "파블로 피카소", "Pablo Picasso"),
    ("창조의 모든 행위는 먼저 파괴의 행위다.", "Every act of creation is first an act of destruction.", "파블로 피카소", "Pablo Picasso"),
    ("나는 찾지 않는다. 발견한다.", "I do not seek. I find.", "파블로 피카소", "Pablo Picasso"),
    ("예술은 우리 일상의 먼지를 씻어 영혼을 보여준다.", "Art washes away from the soul the dust of everyday life.", "파블로 피카소", "Pablo Picasso"),
    ("색채는 감정의 언어다.", "Color is the language of emotion.", "파블로 피카소", "Pablo Picasso"),
    ("젊음과 나이는 숫자가 아니다. 정신이다.", "Youth and age are not numbers. They are states of mind.", "파블로 피카소", "Pablo Picasso"),
    ("행동이 모든 성공의 기본 열쇠다.", "Action is the foundational key to all success.", "파블로 피카소", "Pablo Picasso"),
    ("예술을 배우는 데 4년이 걸렸지만, 어린이처럼 그리는 데 평생이 걸렸다.", "It took me four years to learn art, but a lifetime to paint like a child.", "클로드 모네", "Claude Monet"),
    ("색은 나의 하루의 집착이자, 기쁨이며, 고통이다.", "Color is my day-long obsession, joy, and torment.", "클로드 모네", "Claude Monet"),
    ("나는 빛을 그린다. 사물이 아니라.", "I paint light, not objects.", "클로드 모네", "Claude Monet"),
    ("나는 자연의 변화에 매혹되었다.", "I am captivated by the changing face of nature.", "클로드 모네", "Claude Monet"),
    ("그림은 인내와 관찰의 산물이다.", "Painting is the product of patience and observation.", "클로드 모네", "Claude Monet"),
    ("눈이 제대로 보는 법을 배우는 것이 예술이다.", "Art is learning to see with the eyes correctly.", "클로드 모네", "Claude Monet"),
    ("나는 순간을 포착하고 싶다. 그것이 진짜 현실임을 보여주고 싶다.", "I want to capture the moment and show that it is the true reality.", "클로드 모네", "Claude Monet"),
    ("물은 내 삶의 전부다.", "Water is everything to me.", "클로드 모네", "Claude Monet"),
    ("정원은 내 삶에서 가장 아름다운 작품이다.", "My garden is the most beautiful work in my life.", "클로드 모네", "Claude Monet"),
    ("빛은 모든 것의 주인공이다.", "Light is the protagonist of everything.", "클로드 모네", "Claude Monet"),
    ("다른 사람들이 본다고 생각하는 것이 아니라, 내가 보는 것을 그린다.", "I do not paint what others think they see, but what I see.", "오귀스트 로댕", "Auguste Rodin"),
    ("조각이란 필요 없는 것을 제거하는 것이다.", "Sculpture is the art of taking away what is unnecessary.", "오귀스트 로댕", "Auguste Rodin"),
    ("아름다움은 어디에나 있다. 우리의 눈이 그것을 볼 수 없을 뿐이다.", "Beauty is everywhere. It is only our eyes that fail to see it.", "오귀스트 로댕", "Auguste Rodin"),
    ("두 손은 신이 인간에게 준 가장 훌륭한 도구다.", "Two hands are the finest tools God gave to man.", "오귀스트 로댕", "Auguste Rodin"),
    ("나는 자연을 발명하지 않는다. 단지 드러낼 뿐이다.", "I do not invent nature. I only reveal it.", "오귀스트 로댕", "Auguste Rodin"),
    ("인내는 예술가의 가장 중요한 덕목이다.", "Patience is the most important virtue of an artist.", "오귀스트 로댕", "Auguste Rodin"),
    ("진정한 아름다움은 내면에서 온다.", "True beauty comes from within.", "오귀스트 로댕", "Auguste Rodin"),
    ("상상력 없이는 아무것도 만들 수 없다.", "Without imagination, nothing can be created.", "오귀스트 로댕", "Auguste Rodin"),
    ("나는 단지 대리석을 빚는 것이 아니라, 인간의 내면을 드러낸다.", "I do not merely sculpt marble — I reveal the inner life of man.", "폴 세잔", "Paul Cézanne"),
    ("예술은 자연과 평행하는 조화다.", "Art is a harmony parallel to nature.", "폴 세잔", "Paul Cézanne"),
    ("그림은 눈으로 생각하는 것이다.", "Painting is thinking with the eyes.", "폴 세잔", "Paul Cézanne"),
    ("나는 자연으로부터 배우기를 멈추지 않겠다.", "I shall never stop learning from nature.", "폴 세잔", "Paul Cézanne"),
    ("예술은 개인적인 감각의 조화다.", "Art is the harmony of personal sensation.", "폴 세잔", "Paul Cézanne"),
    ("화가는 자신의 눈을 신뢰해야 한다.", "The painter must trust his own eyes.", "폴 세잔", "Paul Cézanne"),
    ("자연을 앞에 두고 두려워하지 마라.", "Do not be afraid before nature.", "폴 세잔", "Paul Cézanne"),
    ("회화는 두뇌와 눈의 결합이다.", "Painting is the union of the brain and the eye.", "폴 세잔", "Paul Cézanne"),
    ("나는 자연을 원기둥, 구, 원뿔로 다룬다.", "I treat nature by the cylinder, the sphere, the cone.", "폴 세잔", "Paul Cézanne"),
    ("나와 미친 사람의 유일한 차이는 나는 미치지 않았다는 것이다.", "The only difference between me and a madman is that I am not mad.", "살바도르 달리", "Salvador Dalí"),
    ("나는 마약을 하지 않는다. 내 자신이 마약이다.", "I don\'t do drugs. I am drugs.", "살바도르 달리", "Salvador Dalí"),
    ("상상력 없는 사람만이 현실을 진지하게 받아들인다.", "Only those without imagination take reality seriously.", "살바도르 달리", "Salvador Dalí"),
    ("진정한 창의력은 두려움을 모른다.", "True creativity knows no fear.", "살바도르 달리", "Salvador Dalí"),
    ("모든 것이 예술이 될 수 있다. 심지어 나 자신도.", "Everything can be art. Even myself.", "살바도르 달리", "Salvador Dalí"),
    ("아침에 일어나는 것 자체가 놀라운 일이다.", "Waking up in the morning is itself a remarkable thing.", "살바도르 달리", "Salvador Dalí"),
    ("나는 매일 아침 최고의 기쁨을 느낀다. 살바도르 달리가 된다는 것을.", "Each morning I experience the supreme pleasure of being Salvador Dalí.", "살바도르 달리", "Salvador Dalí"),
    ("완벽주의자가 되어라. 불완전함은 예술이 아니다.", "Be a perfectionist. Imperfection is not art.", "프리다 칼로", "Frida Kahlo"),
    ("나는 나 자신을 잘 알기 때문에 나 자신을 그린다.", "I paint myself because I know myself so well.", "프리다 칼로", "Frida Kahlo"),
    ("고통은 나를 더 강하게 만들었다.", "Pain has made me stronger.", "프리다 칼로", "Frida Kahlo"),
    ("내 상처가 나의 예술이 되었다.", "My wounds became my art.", "프리다 칼로", "Frida Kahlo"),
    ("나는 현실을 그리는 것이 아니라, 내가 아는 현실을 그린다.", "I do not paint reality, but the reality I know.", "프리다 칼로", "Frida Kahlo"),
    ("자신을 사랑하라. 그것이 모든 것의 시작이다.", "Love yourself. That is the beginning of everything.", "프리다 칼로", "Frida Kahlo"),
    ("나는 슬픔을 그리지 않는다. 하지만 내 그림은 가장 솔직한 표현이다.", "I don\'t paint sadness, but my paintings are the most honest expression.", "프리다 칼로", "Frida Kahlo"),
    ("나는 발로 날아다니는 것이 아니라, 붓으로 난다.", "I do not fly with my feet, but with my brush.", "프리다 칼로", "Frida Kahlo"),
    ("고통, 쾌락, 죽음은 선이 아니라 과정일 뿐이다.", "Pain, pleasure, and death are not lines, but processes.", "렘브란트", "Rembrandt"),
    ("빛이 없는 곳에 진실이 있다.", "In places without light, truth is found.", "렘브란트", "Rembrandt"),
    ("나는 그림 속에서 내가 원하는 자유를 찾는다.", "I find in painting the freedom I desire.", "렘브란트", "Rembrandt"),
    ("인간의 얼굴에는 우주 전체가 담겨 있다.", "In a human face, the entire universe is contained.", "렘브란트", "Rembrandt"),
    ("그림자는 빛만큼 중요하다.", "Shadows are as important as light.", "렘브란트", "Rembrandt"),
    ("빛과 그림자의 대비가 진실을 드러낸다.", "The contrast of light and shadow reveals truth.", "렘브란트", "Rembrandt"),
    ("위대한 그림은 관람자를 불편하게 만들어야 한다.", "A great painting must make the viewer uncomfortable.", "렘브란트", "Rembrandt"),
    ("나는 명성이 아닌 자유를 추구한다.", "I seek freedom, not fame.", "알브레히트 뒤러", "Albrecht Dürer"),
    ("아름다움이란 무엇인지 나는 모른다. 그것은 모든 것 속에 존재한다.", "What beauty is, I do not know. It exists in all things.", "알브레히트 뒤러", "Albrecht Dürer"),
    ("예술은 자연 속에 숨어 있다. 그것을 끄집어내는 자가 예술가다.", "Art lies hidden in nature. The one who can extract it is the artist.", "알브레히트 뒤러", "Albrecht Dürer"),
    ("좋은 그림은 수백 년이 지나도 살아있다.", "A good painting lives for hundreds of years.", "알브레히트 뒤러", "Albrecht Dürer"),
    ("나는 선 하나하나에 내 삶을 담는다.", "I pour my life into every single line.", "알브레히트 뒤러", "Albrecht Dürer"),
    ("진정한 예술가는 자연에서 배운다.", "A true artist learns from nature.", "알브레히트 뒤러", "Albrecht Dürer"),
    ("비율은 아름다움의 어머니다.", "Proportion is the mother of beauty.", "알브레히트 뒤러", "Albrecht Dürer"),
    ("연습 없이는 어떤 재능도 꽃피울 수 없다.", "Without practice, no talent can blossom.", "외젠 들라크루아", "Eugène Delacroix"),
    ("예술가는 열정 없이는 존재할 수 없다.", "An artist cannot exist without passion.", "외젠 들라크루아", "Eugène Delacroix"),
    ("규칙이란 그것을 깨뜨릴 줄 아는 자를 위해 존재한다.", "Rules exist for those who know how to break them.", "외젠 들라크루아", "Eugène Delacroix"),
    ("그림은 생각보다 먼저 느껴져야 한다.", "A painting must be felt before it is understood.", "외젠 들라크루아", "Eugène Delacroix"),
    ("색채는 피아노 건반이고, 눈은 건반을 치는 손이며, 영혼은 피아노다.", "Color is the piano keyboard, the eye is the hand that strikes the keys, and the soul is the piano.", "외젠 들라크루아", "Eugène Delacroix"),
    ("상상력은 예술가의 가장 위대한 선물이다.", "Imagination is the artist\'s greatest gift.", "외젠 들라크루아", "Eugène Delacroix"),
    ("자유는 예술의 숨결이다.", "Freedom is the breath of art.", "외젠 들라크루아", "Eugène Delacroix"),
    ("붓질 하나에도 영혼이 담겨야 한다.", "Even a single brushstroke must carry the soul.", "폴 고갱", "Paul Gauguin"),
    ("나는 문명에서 도망쳐 자연 속에서 진실을 찾았다.", "I fled civilization and found truth in nature.", "폴 고갱", "Paul Gauguin"),
    ("예술은 추상이다. 자연 앞에서 꿈을 꾸고, 그 꿈에서 나온 창조물을 생각하라.", "Art is abstraction. Dream in front of nature, and think of the creation that emerges from that dream.", "폴 고갱", "Paul Gauguin"),
    ("색은 그 자체로 언어다.", "Color is a language unto itself.", "폴 고갱", "Paul Gauguin"),
    ("나는 어디서 왔는가? 나는 누구인가? 나는 어디로 가는가?", "Where do I come from? Who am I? Where am I going?", "폴 고갱", "Paul Gauguin"),
    ("예술가가 되려면 먼저 자신을 버려야 한다.", "To become an artist, one must first abandon oneself.", "폴 고갱", "Paul Gauguin"),
    ("나는 위대한 예술가다. 그것을 알기 때문에 나는 견딜 수 있다.", "I am a great artist, and I know it. That is what lets me endure.", "폴 고갱", "Paul Gauguin"),
    ("나는 원시적인 것 속에서 진정한 아름다움을 발견했다.", "I discovered true beauty in the primitive.", "에드가 드가", "Edgar Degas"),
    ("예술은 즉흥적인 것이 아니다. 그것은 규칙과 열정의 결합이다.", "Art is not improvisation. It is the union of rules and passion.", "에드가 드가", "Edgar Degas"),
    ("나는 자연을 보이는 대로 그리지 않는다. 내가 기억하는 대로 그린다.", "I do not paint what I see in nature. I paint what I remember.", "에드가 드가", "Edgar Degas"),
    ("그림은 한 번에 완성되지 않는다. 수천 번의 붓질 끝에 완성된다.", "A painting is not completed all at once. It is finished after thousands of brushstrokes.", "에드가 드가", "Edgar Degas"),
    ("움직임 속에 진실이 있다.", "Truth lies in movement.", "에드가 드가", "Edgar Degas"),
    ("오직 관찰하는 자만이 그릴 수 있다.", "Only those who observe can paint.", "에드가 드가", "Edgar Degas"),
    ("회화는 특별한 삶의 방식이다.", "Painting is a particular way of living.", "구스타프 클림트", "Gustav Klimt"),
    ("황금은 가장 신성한 색이다.", "Gold is the most sacred color.", "구스타프 클림트", "Gustav Klimt"),
    ("나는 그림 안에 내 모든 것을 담는다.", "I pour everything I am into my paintings.", "구스타프 클림트", "Gustav Klimt"),
    ("아름다움은 꾸밈이 아니라 진실에서 나온다.", "Beauty comes not from ornamentation, but from truth.", "구스타프 클림트", "Gustav Klimt"),
    ("예술은 한 번도 완전히 설명된 적이 없다. 그것이 예술이 존재하는 이유다.", "Art has never been fully explained. That is why art exists.", "구스타프 클림트", "Gustav Klimt"),
    ("삶과 죽음은 하나의 선 위에 있다.", "Life and death rest on the same line.", "구스타프 클림트", "Gustav Klimt"),
    ("나는 나 자신을 그리지 않는다. 다른 사람들, 특히 여성들을 그린다.", "I do not paint myself. I paint others, especially women.", "카스파르 다비트 프리드리히", "Caspar David Friedrich"),
    ("예술가는 눈앞에 있는 것만 그려서는 안 된다. 내면에 보이는 것도 그려야 한다.", "An artist must not only paint what is in front of them, but also what is visible within.", "카스파르 다비트 프리드리히", "Caspar David Friedrich"),
    ("고독은 자연 속에서만 완전히 느껴진다.", "Solitude is fully felt only in nature.", "카스파르 다비트 프리드리히", "Caspar David Friedrich"),
    ("안개 속에서 진실이 드러난다.", "In the mist, truth is revealed.", "카스파르 다비트 프리드리히", "Caspar David Friedrich"),
    ("자연은 신의 언어다.", "Nature is the language of God.", "카스파르 다비트 프리드리히", "Caspar David Friedrich"),
    ("숭고함은 자연의 광대함 앞에서만 경험할 수 있다.", "The sublime can only be experienced before the vastness of nature.", "얀 반 에이크", "Jan van Eyck"),
    ("나는 할 수 있는 한 최선을 다했다.", "I have done my best, as best I could.", "얀 반 에이크", "Jan van Eyck"),
    ("세밀함 속에 신의 존재가 있다.", "In the detail, the presence of God is found.", "얀 반 에이크", "Jan van Eyck"),
    ("빛은 그림의 생명이다.", "Light is the life of a painting.", "산드로 보티첼리", "Sandro Botticelli"),
    ("아름다움은 보는 자의 마음속에 있다.", "Beauty resides in the eye of the beholder.", "산드로 보티첼리", "Sandro Botticelli"),
    ("신화 속에서 나는 인간의 진실을 찾는다.", "In mythology, I find human truth.", "산드로 보티첼리", "Sandro Botticelli"),
    ("봄처럼 아름다운 것은 무상하기 때문에 더 소중하다.", "What is as beautiful as spring is all the more precious because it is fleeting.", "산드로 보티첼리", "Sandro Botticelli"),
    ("선의 흐름 속에 감정이 담긴다.", "Emotion is carried in the flow of a line.", "엘 그레코", "El Greco"),
    ("색채는 나의 언어다.", "Color is my language.", "엘 그레코", "El Greco"),
    ("나는 신을 그린다. 그래서 나는 빛을 그린다.", "I paint God. Therefore I paint light.", "엘 그레코", "El Greco"),
    ("인간의 영혼은 하늘을 향해 뻗어 있다.", "The human soul reaches upward toward the heavens.", "엘 그레코", "El Greco"),
    ("나는 태양이 싫다. 그것은 나의 빛을 방해한다.", "I detest the sun. It interferes with my light.", "얀 베르메르", "Jan Vermeer"),
    ("빛은 그림의 영혼이다.", "Light is the soul of a painting.", "얀 베르메르", "Jan Vermeer"),
    ("일상의 순간 속에 영원이 담겨 있다.", "In the fleeting moments of daily life, eternity is contained.", "얀 베르메르", "Jan Vermeer"),
    ("창문을 통해 들어오는 빛은 신의 선물이다.", "Light entering through a window is a gift from God.", "얀 베르메르", "Jan Vermeer"),
    ("평범한 것을 비범하게 보이게 하는 것이 예술이다.", "Making the ordinary appear extraordinary — that is art.", "얀 베르메르", "Jan Vermeer"),
]

def _seed_quotes(c):
    for quote, quote_en, artist, artist_en in _QUOTES_DATA:
        c.execute("INSERT INTO artist_quotes (quote, quote_en, artist, artist_en) VALUES (?, ?, ?, ?)", (quote, quote_en, artist, artist_en))

def get_random_quote() -> dict:
    with conn() as c:
        row = c.execute("SELECT quote, quote_en, artist, artist_en FROM artist_quotes ORDER BY RANDOM() LIMIT 1").fetchone()
    return dict(row) if row else {"quote": "", "quote_en": "", "artist": "", "artist_en": ""}
