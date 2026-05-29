#!/usr/bin/env python3
"""
One-time migration: move existing journal_{user_id}.json files → SQLite.
Run once:  python backend/scripts/migrate_journals.py

Safe to run multiple times — skips entries already in the DB (by user+date).
After confirming everything works, you can delete the .json files.
"""
import sys, json, re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.database import conn, init_db, save_journal_entry


def migrate():
    init_db()

    json_files = list(PROJECT_ROOT.glob("journal_*.json"))
    if not json_files:
        print("No journal_*.json files found - nothing to migrate.")
        return

    total_migrated = 0
    total_skipped  = 0

    for jf in json_files:
        match = re.search(r"journal_(\d+)\.json", jf.name)
        if not match:
            continue
        user_id = int(match.group(1))

        # Verify user exists
        with conn() as c:
            user = c.execute("SELECT id FROM users WHERE id=?", (user_id,)).fetchone()
        if not user:
            print(f"  Skipping {jf.name} — user {user_id} not in DB")
            continue

        try:
            entries = json.loads(jf.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  Error reading {jf.name}: {e}")
            continue

        migrated = 0
        skipped  = 0
        for entry in entries:
            date = entry.get("date", "")
            if not date:
                continue
            # Skip if already migrated
            with conn() as c:
                exists = c.execute(
                    "SELECT id FROM journal_entries WHERE user_id=? AND date=?",
                    (user_id, date),
                ).fetchone()
            if exists:
                skipped += 1
                continue
            try:
                save_journal_entry(user_id, entry)
                migrated += 1
            except Exception as e:
                print(f"    Error saving entry {date}: {e}")

        print(f"  {jf.name} → {migrated} migrated, {skipped} already existed")
        total_migrated += migrated
        total_skipped  += skipped

    print(f"\nDone — total {total_migrated} entries migrated, {total_skipped} skipped.")
    if total_migrated > 0:
        print("Tip: confirm the app works, then delete the .json files:")
        for jf in json_files:
            print(f"  del {jf}")


if __name__ == "__main__":
    migrate()
