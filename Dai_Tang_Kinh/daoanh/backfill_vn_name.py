import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'lineage.db')

def backfill():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    total_nmp = cur.execute("SELECT COUNT(*) FROM namevi_map_places WHERE name_vi IS NOT NULL AND name_vi != ''").fetchone()[0]
    total_pp = cur.execute("SELECT COUNT(*) FROM places_pending").fetchone()[0]
    before = cur.execute("SELECT COUNT(*) FROM places_pending WHERE name_vi IS NOT NULL AND name_vi != ''").fetchone()[0]

    print(f"namevi_map_places with name_vi: {total_nmp}")
    print(f"places_pending total: {total_pp}")
    print(f"places_pending already has name_vi: {before}")

    cur.execute("""
        UPDATE places_pending
        SET name_vi = (
            SELECT m.name_vi FROM namevi_map_places m
            WHERE m.dila_id = places_pending.id
              AND m.name_vi IS NOT NULL AND m.name_vi != ''
            LIMIT 1
        )
        WHERE (name_vi IS NULL OR name_vi = '')
          AND id IN (SELECT dila_id FROM namevi_map_places WHERE name_vi IS NOT NULL AND name_vi != '')
    """)
    updated = cur.rowcount
    conn.commit()

    after = cur.execute("SELECT COUNT(*) FROM places_pending WHERE name_vi IS NOT NULL AND name_vi != ''").fetchone()[0]
    print(f"Backfilled: {updated} rows")
    print(f"places_pending with name_vi now: {after}")

    samples = cur.execute("""
        SELECT id, name_zh, name_vi FROM places_pending
        WHERE name_vi IS NOT NULL AND name_vi != ''
        LIMIT 5
    """).fetchall()
    print("\nSamples:")
    for s in samples:
        print(f"  {s[0]} | {s[1]} | {s[2]}")

    conn.close()

if __name__ == '__main__':
    backfill()
