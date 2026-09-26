"""
migrate_name_vi_norm.py
Thêm và populate cột name_vi_norm trong places_pending (diacritics-free Vietnamese name).

Chạy: python scripts/migrate_name_vi_norm.py
Có thể chạy lại (idempotent).
"""

import sqlite3
import os
import unicodedata
import re
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'lineage.db')


def normalize_text(s):
    if not s:
        return ''
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = s.replace('đ', 'd').replace('Đ', 'd')
    return re.sub(r'\s+', ' ', s).lower().strip()


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")


def main():
    log(f"Migrating name_vi_norm in {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")

    cols = [r[1] for r in conn.execute("PRAGMA table_info(places_pending)").fetchall()]
    if 'name_vi_norm' not in cols:
        log("Adding name_vi_norm column...")
        conn.execute("ALTER TABLE places_pending ADD COLUMN name_vi_norm TEXT")
        conn.commit()

    pending = conn.execute(
        "SELECT COUNT(*) FROM places_pending WHERE name_vi IS NOT NULL AND name_vi != '' AND (name_vi_norm IS NULL OR name_vi_norm = '')"
    ).fetchone()[0]
    log(f"Rows to migrate: {pending}")
    if pending == 0:
        log("Nothing to migrate.")
        conn.close()
        return

    # Cursor-based: track last rowid to avoid OFFSET drift
    last_rowid = 0
    batch_size = 5000
    total = 0
    cur = conn.cursor()
    while True:
        rows = conn.execute(
            "SELECT rowid, name_vi FROM places_pending WHERE rowid > ? AND name_vi IS NOT NULL AND name_vi != '' AND (name_vi_norm IS NULL OR name_vi_norm = '') ORDER BY rowid LIMIT ?",
            (last_rowid, batch_size)
        ).fetchall()
        if not rows:
            break
        for r in rows:
            norm = normalize_text(r['name_vi'])
            if norm:
                cur.execute("UPDATE places_pending SET name_vi_norm = ? WHERE rowid = ?", (norm, r['rowid']))
            last_rowid = r['rowid']
        conn.commit()
        total += len(rows)
        log(f"  Migrated {total} rows (last rowid: {last_rowid})...")

    log(f"Done! Total migrated: {total}")

    total_all = conn.execute("SELECT COUNT(*) FROM places_pending").fetchone()[0]
    total_norm = conn.execute("SELECT COUNT(*) FROM places_pending WHERE name_vi_norm IS NOT NULL AND name_vi_norm != ''").fetchone()[0]
    log(f"Total places_pending: {total_all}, with name_vi_norm: {total_norm}")

    conn.close()


if __name__ == '__main__':
    main()
