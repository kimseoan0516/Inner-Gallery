#!/usr/bin/env python3
"""
Import artist data from the Kaggle dataset CSV into the artists table.
Run once:  python backend/scripts/import_artists.py
Re-running is safe — skips artists already in the DB.
"""
import sys, csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.database import conn, init_db

# Korean name mapping (add more as needed)
KO_NAMES = {
    "Vincent van Gogh":       "빈센트 반 고흐",
    "Claude Monet":           "클로드 모네",
    "Pablo Picasso":          "파블로 피카소",
    "Leonardo da Vinci":      "레오나르도 다 빈치",
    "Michelangelo":           "미켈란젤로",
    "Rembrandt":              "렘브란트",
    "Salvador Dali":          "살바도르 달리",
    "Frida Kahlo":            "프리다 칼로",
    "Gustav Klimt":           "구스타프 클림트",
    "Edvard Munch":           "에드바르 뭉크",
    "Pierre-Auguste Renoir":  "피에르 오귀스트 르누아르",
    "Edgar Degas":            "에드가 드가",
    "Paul Cezanne":           "폴 세잔",
    "Henri Matisse":          "앙리 마티스",
    "Albrecht Dürer":         "알브레히트 뒤러",
    "Sandro Botticelli":      "산드로 보티첼리",
    "Caravaggio":             "카라바조",
    "Jan van Eyck":           "얀 반 에이크",
    "Peter Paul Rubens":      "피터 폴 루벤스",
    "Francisco Goya":         "프란시스코 고야",
    "Diego Velazquez":        "디에고 벨라스케스",
    "El Greco":               "엘 그레코",
    "Giotto di Bondone":      "조토 디 본도네",
    "Marc Chagall":           "마르크 샤갈",
    "Pieter Bruegel":         "피터르 브뤼헐",
    "Andy Warhol":            "앤디 워홀",
    "Paul Gauguin":           "폴 고갱",
    "Georges Seurat":         "조르주 쇠라",
    "Henri de Toulouse-Lautrec": "앙리 드 툴루즈 로트렉",
    "Camille Pissarro":       "카미유 피사로",
    "Alfred Sisley":          "알프레드 시슬리",
    "Eugene Delacroix":       "외젠 들라크루아",
    "Edouard Manet":          "에두아르 마네",
    "Diego Rivera":           "디에고 리베라",
    "Frida Kahlo":            "프리다 칼로",
    "Kazimir Malevich":       "카지미르 말레비치",
    "Wassily Kandinsky":      "바실리 칸딘스키",
    "Paul Klee":              "파울 클레",
    "Joan Miro":              "호안 미로",
    "Rene Magritte":          "르네 마그리트",
    "Giorgio de Chirico":     "조르조 데 키리코",
    "Amedeo Modigliani":      "아메데오 모딜리아니",
    "Gustav Klimt":           "구스타프 클림트",
    "Egon Schiele":           "에곤 실레",
    "Hieronymus Bosch":       "히에로니무스 보스",
    "Jan Vermeer":            "얀 페르메이르",
    "Johannes Vermeer":       "요하네스 페르메이르",
    "Raphael":                "라파엘로",
    "Titian":                 "티치아노",
}


def find_csv() -> Path | None:
    """Search for artists.csv in artwork_sources or artwork_index."""
    search_dirs = [
        PROJECT_ROOT / "backend" / "artwork_sources",
        PROJECT_ROOT / "backend" / "artwork_index" / "_images",
    ]
    for d in search_dirs:
        for f in d.rglob("*.csv"):
            return f
    return None


def import_artists(csv_path: Path):
    init_db()

    inserted = 0
    skipped  = 0

    with open(csv_path, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("name") or "").strip()
            if not name:
                continue
            name_ko        = KO_NAMES.get(name, "")
            nationality    = (row.get("nationality")  or "").strip()
            years          = (row.get("years")        or "").strip()
            genre          = (row.get("genre")        or "").strip()
            bio            = (row.get("bio")          or "")[:500].strip()
            wikipedia      = (row.get("wikipedia")    or "").strip()
            painting_count = int(row.get("paintings") or 0)

            with conn() as c:
                existing = c.execute(
                    "SELECT id FROM artists WHERE LOWER(name) = LOWER(?)", (name,)
                ).fetchone()

                if existing:
                    # Update Korean name if we have it and it's missing
                    if name_ko:
                        c.execute(
                            "UPDATE artists SET name_ko=? WHERE id=? AND name_ko=''",
                            (name_ko, existing["id"]),
                        )
                    skipped += 1
                else:
                    c.execute("""
                        INSERT INTO artists
                            (name, name_ko, nationality, years, genre, bio, wikipedia, painting_count)
                        VALUES (?,?,?,?,?,?,?,?)
                    """, (name, name_ko, nationality, years, genre, bio, wikipedia, painting_count))
                    inserted += 1

    print(f"Done - inserted {inserted} artists, skipped {skipped} duplicates.")


def main():
    csv_path = find_csv()
    if not csv_path:
        print("artists.csv not found.")
        print("Make sure the zip has been extracted via build_index.py first.")
        sys.exit(1)
    print(f"Importing from: {csv_path}")
    import_artists(csv_path)


if __name__ == "__main__":
    main()
