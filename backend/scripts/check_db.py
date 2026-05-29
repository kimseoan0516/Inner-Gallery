#!/usr/bin/env python3
"""
Quick DB health check.
Run:  python backend/scripts/check_db.py
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.database import conn, init_db

def main():
    init_db()
    with conn() as c:
        tables = [r[0] for r in c.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()]

        print("=== Inner Gallery DB ===\n")
        for table in tables:
            count = c.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"  {table:<20} {count:>6} rows")

        print()
        # Sample artist names
        artists = c.execute(
            "SELECT name, name_ko, genre FROM artists ORDER BY name LIMIT 8"
        ).fetchall()
        if artists:
            print("Sample artists:")
            for a in artists:
                ko = f" ({a['name_ko']})" if a['name_ko'] else ""
                print(f"  {a['name']}{ko}  -  {a['genre']}")
        else:
            print("No artists yet. Run:  python backend/scripts/import_artists.py")

if __name__ == "__main__":
    main()
