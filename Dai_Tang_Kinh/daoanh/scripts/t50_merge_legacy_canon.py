"""
t50_merge_legacy_canon.py — T50b: Merge buddhist_db.sqlite canon_mapping
=========================================================================
Import 2,698 canon_mapping rows from orphaned buddhist_db.sqlite (34 MB)
into lineage.db as legacy_canon_mapping table.

Usage:
    python scripts/t50_merge_legacy_canon.py           # full run
    python scripts/t50_merge_legacy_canon.py --dry-run  # preview only
"""
import sqlite3, os, sys, argparse, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
DB_PATH = 'data/lineage.db'
LEGACY_DB = 'data/sqlite/buddhist_db.sqlite'


def main():
    parser = argparse.ArgumentParser(description='T50b: Merge legacy canon mapping')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    if not os.path.exists(LEGACY_DB):
        print(f"❌ Legacy DB not found: {LEGACY_DB}")
        return

    legacy_conn = sqlite3.connect(LEGACY_DB)
    legacy_conn.row_factory = sqlite3.Row

    # Check what tables exist in legacy DB
    tables = [r[0] for r in legacy_conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()]
    print(f"Legacy DB tables: {tables}")

    # Check canon_mapping schema and count
    if 'canon_mapping' not in tables:
        print("❌ canon_mapping table not found in legacy DB")
        legacy_conn.close()
        return

    cols = [r[1] for r in legacy_conn.execute("PRAGMA table_info(canon_mapping)").fetchall()]
    count = legacy_conn.execute("SELECT COUNT(*) FROM canon_mapping").fetchone()[0]
    print(f"canon_mapping: {count} rows, columns: {cols}")

    # Sample data
    sample = legacy_conn.execute("SELECT * FROM canon_mapping LIMIT 3").fetchall()
    print("\nSample rows:")
    for row in sample:
        print(f"  {dict(row)}")

    if args.dry_run:
        print(f"\n[DRY RUN] Would merge {count} rows into lineage.db")
        legacy_conn.close()
        return

    # Create target table
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS legacy_canon_mapping (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            work_id TEXT NOT NULL,
            canon_source TEXT NOT NULL,
            title TEXT,
            author_dila_id TEXT,
            year INTEGER,
            volume TEXT,
            page TEXT,
            source_legacy TEXT DEFAULT 'buddhist_db.sqlite',
            imported_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(work_id, canon_source)
        )
    """)

    # Merge data
    inserted = 0
    for row in legacy_conn.execute("SELECT * FROM canon_mapping").fetchall():
        d = dict(row)
        try:
            conn.execute("""
                INSERT OR IGNORE INTO legacy_canon_mapping
                (work_id, canon_source, title, author_dila_id, year, volume, page)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                d.get('work_id', ''), d.get('canon_source', ''),
                d.get('title', ''), d.get('author_dila_id'),
                d.get('year'), d.get('volume'), d.get('page')
            ))
            inserted += 1
        except Exception as e:
            print(f"  Error: {e}")

    conn.commit()
    legacy_conn.close()

    # Verify
    target_count = conn.execute("SELECT COUNT(*) FROM legacy_canon_mapping").fetchone()[0]
    print(f"\n✅ Merged: {inserted} rows inserted, {target_count} total in legacy_canon_mapping")
    print(f"   Source: {count} rows from buddhist_db.sqlite")
    if target_count == count:
        print("   ✓ Row counts match — no data loss")
    else:
        print(f"   ⚠ Row count mismatch: {target_count} vs {count}")

    conn.close()


if __name__ == '__main__':
    main()
