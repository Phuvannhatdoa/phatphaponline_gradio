"""T35 — Seed sat_crossref table từ cbeta_catalog_vn (T-series only).

Mỗi row tương ứng 1 kinh T-series Đại Chính Tạng.
SAT URL pattern: https://21dzk.l.u-tokyo.ac.jp/SAT/T{num:04d}.html
"""
import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = 'daoanh/data/lineage.db'
SAT_BASE = 'https://21dzk.l.u-tokyo.ac.jp/SAT'


def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Create table
    c.execute("""
        CREATE TABLE IF NOT EXISTS sat_crossref (
            cbeta_sigla  TEXT PRIMARY KEY,
            sat_url      TEXT,
            has_unique   INTEGER DEFAULT 0,
            created_at   TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("sat_crossref table ready")

    # Fetch T-series rows (exclude explicit X-series by cbeta_ref)
    c.execute("""
        SELECT sh_number
        FROM cbeta_catalog_vn
        WHERE sh_number IS NOT NULL
          AND (cbeta_ref IS NULL OR cbeta_ref NOT LIKE 'X%')
        ORDER BY CAST(sh_number AS INTEGER)
    """)
    rows = c.fetchall()
    print(f"T-series candidates: {len(rows)}")

    inserted = 0
    skipped = 0
    for (sh_number,) in rows:
        try:
            num = int(sh_number)
        except (ValueError, TypeError):
            skipped += 1
            continue
        sigla = f"T{num:04d}"
        url = f"{SAT_BASE}/{sigla}.html"
        c.execute(
            "INSERT OR IGNORE INTO sat_crossref(cbeta_sigla, sat_url) VALUES(?, ?)",
            (sigla, url)
        )
        if c.rowcount:
            inserted += 1

    conn.commit()
    print(f"Inserted: {inserted} | Skipped (non-numeric sh_number): {skipped}")
    c.execute("SELECT COUNT(*) FROM sat_crossref")
    total = c.fetchone()[0]
    print(f"Total sat_crossref rows: {total}")

    # Sample output
    c.execute("SELECT cbeta_sigla, sat_url FROM sat_crossref ORDER BY cbeta_sigla LIMIT 5")
    print("Sample rows:")
    for row in c.fetchall():
        print(f"  {row[0]} -> {row[1]}")

    conn.close()
    return total


if __name__ == '__main__':
    total = main()
    if total >= 500:
        print(f"\nT35 acceptance criterion met: {total} >= 500 rows")
    else:
        print(f"\nWARNING: Only {total} rows — below 500 threshold")
