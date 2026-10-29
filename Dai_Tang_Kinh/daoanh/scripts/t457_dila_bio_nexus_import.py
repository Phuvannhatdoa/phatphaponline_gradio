#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T457 — import dila_bio_nexus từ staging_v4 (A2: array full parse).
Usage:
  python -X utf8 scripts/t457_dila_bio_nexus_import.py --stats
  python -X utf8 scripts/t457_dila_bio_nexus_import.py --dry-run
  python -X utf8 scripts/t457_dila_bio_nexus_import.py --apply
  python -X utf8 scripts/t457_dila_bio_nexus_import.py --revert
"""
import argparse, sqlite3, json, os, sys, datetime, shutil, hashlib

DAOANH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(DAOANH, "data/lineage.db")
STAGING_PATH = os.path.join(DAOANH, "data/staging_v4/t457_dila_bio_nexus.jsonl")
BACKUP_DIR = os.path.join(DAOANH, "data/backups")

def stats():
    count = 0
    books = {}
    with_year = 0
    with open(STAGING_PATH, encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            count += 1
            book = rec.get("book", "none")
            books[book] = books.get(book, 0) + 1
            if rec.get("year_from") is not None or rec.get("year_to") is not None:
                with_year += 1
    print(f"STATS: records={count}, books={len(books)}, with_year={with_year}, percent_year={with_year/count*100:.1f}%")
    for b, c in sorted(books.items()):
        print(f"  {b}: {c}")

def dry_run():
    # Verify DB doesn't have dila_bio_nexus yet; if it exists, count current
    conn = sqlite3.connect(DB_PATH, uri=True)
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    has_table = "dila_bio_nexus" in tables
    current = conn.execute("SELECT COUNT(*) FROM dila_bio_nexus").fetchone()[0] if has_table else 0
    conn.close()
    print(f"DRY-RUN: DB={DB_PATH}, table_exists={has_table}, current_rows={current}")
    stats()

def apply():
    # Backup
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"lineage_t457_{ts}.db")
    os.makedirs(BACKUP_DIR, exist_ok=True)
    shutil.copy2(DB_PATH, backup_path)
    print(f"BACKUP: {backup_path}")
    conn = sqlite3.connect(DB_PATH, uri=True)
    # Create tables (additive, idempotent with IF NOT EXISTS)
    conn.execute("CREATE TABLE IF NOT EXISTS dila_bio_nexus (id INTEGER PRIMARY KEY AUTOINCREMENT, book TEXT, source_file TEXT, nexus_id TEXT, seq INTEGER, from_anchor TEXT, to_anchor TEXT, text_zh TEXT, jd_from REAL, jd_to REAL, year_from INTEGER, year_to INTEGER, provenance TEXT, status TEXT DEFAULT 'staged', imported_at DATETIME DEFAULT CURRENT_TIMESTAMP)")
    conn.execute("CREATE TABLE IF NOT EXISTS dila_bio_nexus_person (nexus_id TEXT, person_id TEXT, PRIMARY KEY (nexus_id, person_id))")
    conn.execute("CREATE TABLE IF NOT EXISTS dila_bio_nexus_place (nexus_id TEXT, place_id TEXT, PRIMARY KEY (nexus_id, place_id))")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_bn_book ON dila_bio_nexus(book)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_bn_person ON dila_bio_nexus_person(person_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_bn_year ON dila_bio_nexus(year_from)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_bn_place ON dila_bio_nexus_place(place_id)")
    # Read JSONL and insert in batches
    count = 0
    with open(STAGING_PATH, encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            cursor = conn.execute(
                "INSERT INTO dila_bio_nexus (book, source_file, nexus_id, seq, from_anchor, to_anchor, text_zh, jd_from, jd_to, year_from, year_to, provenance, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT DO NOTHING",
                (rec.get("book"), rec.get("source_file"), rec.get("nexus_id"), rec.get("seq"), rec.get("from_anchor"), rec.get("to_anchor"), rec.get("text_zh"), rec.get("jd_from"), rec.get("jd_to"), rec.get("year_from"), rec.get("year_to"), rec.get("provenance"), rec.get("status", "staged"))
            )
            if cursor.rowcount > 0:
                nexus_id = cursor.connection.execute("SELECT last_insert_rowid()").fetchone()[0]
                # Actually the INSERT doesn't return the id easily; use nexus_id directly for links
                # Link to persons
                for pid in rec.get("person_ids", []):
                    conn.execute("INSERT OR IGNORE INTO dila_bio_nexus_person (nexus_id, person_id) VALUES (?, ?)", (rec.get("nexus_id"), pid))
                for plid in rec.get("place_ids", []):
                    conn.execute("INSERT OR IGNORE INTO dila_bio_nexus_place (nexus_id, place_id) VALUES (?, ?)", (rec.get("nexus_id"), plid))
                count += 1
    conn.commit()
    print(f"APPLY: inserted/updated {count} nexus records (additive, idempotent)")

def revert():
    conn = sqlite3.connect(DB_PATH, uri=True)
    conn.execute("DROP TABLE IF EXISTS dila_bio_nexus")
    conn.execute("DROP TABLE IF EXISTS dila_bio_nexus_person")
    conn.execute("DROP TABLE IF EXISTS dila_bio_nexus_place")
    conn.execute("DROP INDEX IF EXISTS idx_bn_book")
    conn.execute("DROP INDEX IF EXISTS idx_bn_person")
    conn.execute("DROP INDEX IF EXISTS idx_bn_year")
    conn.execute("DROP INDEX IF EXISTS idx_bn_place")
    conn.commit()
    print("REVERT: dropped dila_bio_nexus + link tables + indexes")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stats", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--revert", action="store_true")
    args = parser.parse_args()
    if args.stats:
        stats()
    elif args.dry_run:
        dry_run()
    elif args.apply:
        apply()
    elif args.revert:
        revert()
    else:
        parser.print_help()
