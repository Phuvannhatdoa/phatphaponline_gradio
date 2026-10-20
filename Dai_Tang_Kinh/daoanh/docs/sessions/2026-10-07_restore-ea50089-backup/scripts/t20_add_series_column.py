"""T20 — Thêm column series vào cbeta_catalog_vn và mark X-series rows.

Sau khi chạy:
- Mọi row T-series Đại Chính Tạng có series='T'
- Các row X-series (cbeta_ref LIKE 'X%') có series='X'
- JOIN queries trong api_places_cbeta phải filter AND (series='T' OR series IS NULL)
  để tránh nhầm sh_number giữa 2 hệ đánh số độc lập.
"""
import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = 'daoanh/data/lineage.db'


def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Check existing columns
    c.execute("PRAGMA table_info(cbeta_catalog_vn)")
    existing = [row[1] for row in c.fetchall()]
    print(f"Existing columns ({len(existing)}): {existing}")

    # Add series column if not present
    if 'series' not in existing:
        c.execute("ALTER TABLE cbeta_catalog_vn ADD COLUMN series TEXT DEFAULT 'T'")
        print("Added 'series' column (DEFAULT 'T')")
    else:
        print("'series' column already exists — skipping ALTER TABLE")

    # Ensure all non-null rows have 'T' (covers rows where DEFAULT didn't apply)
    c.execute("UPDATE cbeta_catalog_vn SET series='T' WHERE series IS NULL")
    print(f"Set series='T' for {c.rowcount} previously-null rows")

    # Mark X-series rows by cbeta_ref prefix
    c.execute("UPDATE cbeta_catalog_vn SET series='X' WHERE cbeta_ref LIKE 'X%'")
    x_count = c.rowcount
    print(f"Marked {x_count} rows as series='X'")

    conn.commit()

    # Verify
    c.execute("SELECT series, COUNT(*) as cnt FROM cbeta_catalog_vn GROUP BY series ORDER BY series")
    print("Distribution after migration:")
    for row in c.fetchall():
        print(f"  series={row[0]!r}: {row[1]} rows")

    # Show X-series rows
    if x_count > 0:
        print("X-series rows:")
        c.execute("SELECT sh_number, cbeta_ref, title_zh, title_vi FROM cbeta_catalog_vn WHERE series='X'")
        for row in c.fetchall():
            print(f"  sh={row[0]} cbeta_ref={row[1]} zh={row[2][:40]} vi={row[3]}")

    conn.close()


if __name__ == '__main__':
    main()
