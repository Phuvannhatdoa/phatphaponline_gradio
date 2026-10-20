"""
T24 - ZQLOCAL Content Layer: tao bang zqlocal_content va migrate du lieu
tu namevi_map_places (ten Viet do ZQ tu-phien-am, khong phai DILA cung cap).

Idempotent: dung CREATE TABLE IF NOT EXISTS + INSERT OR IGNORE (UNIQUE constraint
tren entity_id+content_type) nen chay lai nhieu lan an toan.

Chi dung nguon namevi_map_places (da hieu ro schema, 100% join duoc voi entity qua dila_id).
KHONG dong vao entity_claims trong script nay - xem ghi chu trong
tasks/T24-zqlocal-content-layer.md ve bug source_id phat hien trong etl_entity_claims.py.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'lineage.db')

GENERATED_BY_MAP = {
    'auto_transliterate': 'auto_transliterate',
    'manual': 'editor',
    'auto_generated': 'auto_transliterate',
    'rag_auto': 'auto_transliterate',
}
CONFIDENCE_MAP = {
    'auto_transliterate': 0.5,
    'manual': 0.8,
    'auto_generated': 0.5,
    'rag_auto': 0.5,
}


def ensure_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS zqlocal_content (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_id     TEXT NOT NULL,
            content_type  TEXT NOT NULL,
            content       TEXT NOT NULL,
            confidence    REAL DEFAULT 0.8,
            generated_by  TEXT,
            reviewed_by   TEXT,
            reviewed_at   TEXT,
            created_at    TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(entity_id, content_type)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_zqlocal_entity ON zqlocal_content(entity_id)")
    conn.commit()


def migrate(conn):
    rows = conn.execute("""
        SELECT n.dila_id, n.name_vi, n.source, n.vn_name_status, e.entity_id
        FROM namevi_map_places n
        JOIN entity e ON e.dila_id = n.dila_id
        WHERE n.name_vi IS NOT NULL AND n.name_vi != ''
    """).fetchall()

    inserted = 0
    skipped_no_map = 0
    for dila_id, name_vi, source, vn_name_status, entity_id in rows:
        generated_by = GENERATED_BY_MAP.get(source)
        confidence = CONFIDENCE_MAP.get(source)
        if generated_by is None:
            skipped_no_map += 1
            continue
        if vn_name_status == 'reviewed':
            confidence = max(confidence, 0.9)
        cur = conn.execute("""
            INSERT OR IGNORE INTO zqlocal_content
                (entity_id, content_type, content, confidence, generated_by)
            VALUES (?, 'VI_NAME', ?, ?, ?)
        """, (entity_id, name_vi, confidence, generated_by))
        inserted += cur.rowcount
    conn.commit()
    return inserted, skipped_no_map, len(rows)


def main():
    conn = sqlite3.connect(DB_PATH)
    ensure_table(conn)
    inserted, skipped, total = migrate(conn)
    count = conn.execute("SELECT COUNT(*) FROM zqlocal_content").fetchone()[0]
    by_gen = conn.execute("""
        SELECT generated_by, COUNT(*) FROM zqlocal_content GROUP BY generated_by
    """).fetchall()
    print(f"[OK] zqlocal_content table ready.")
    print(f"  Source rows (namevi_map_places JOIN entity): {total}")
    print(f"  Newly inserted this run: {inserted}")
    print(f"  Skipped (unmapped source value): {skipped}")
    print(f"  Total zqlocal_content rows now: {count}")
    print(f"  By generated_by: {by_gen}")
    conn.close()


if __name__ == '__main__':
    main()
