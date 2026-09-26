"""
T04 — link_marcus_glossaries.py
Tạo bảng term_glossaries từ marcus_reference (source: Marcus SNA / Bingenheimer).
marcus_reference.node_id == people.id (DILA format A...) — exact match 99%.
Không dùng fuzzy match vì node_id đã là DILA ID.
"""
import sqlite3, sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace') if hasattr(sys.stdout, 'reconfigure') else None

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'lineage.db')

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. Tạo bảng nếu chưa có
    cur.execute("""
        CREATE TABLE IF NOT EXISTS term_glossaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term TEXT NOT NULL,
            term_zh TEXT,
            term_vi TEXT,
            person_id TEXT,
            work_cbeta_id TEXT,
            source TEXT NOT NULL DEFAULT 'marcus',
            confidence TEXT DEFAULT 'exact_id',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_tg_person ON term_glossaries(person_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_tg_term ON term_glossaries(term)")

    # 2. Check nếu đã có data
    existing = cur.execute("SELECT COUNT(*) FROM term_glossaries WHERE source='marcus'").fetchone()[0]
    if existing > 0:
        print(f"[SKIP] term_glossaries đã có {existing} rows từ marcus. Dùng --force để reset.")
        if '--force' not in sys.argv:
            conn.close()
            return

        cur.execute("DELETE FROM term_glossaries WHERE source='marcus'")
        conn.commit()
        print("[RESET] Đã xóa rows cũ.")

    # 3. Populate từ marcus_reference
    # node_id format A... = DILA person ID — verify với people table
    marcus_rows = cur.execute(
        "SELECT node_id, label, label_vi FROM marcus_reference"
    ).fetchall()

    # Lấy tập hợp person IDs hợp lệ từ people table
    valid_ids = set(
        r[0] for r in cur.execute("SELECT id FROM people").fetchall()
    )

    inserted = 0
    unmatched = 0
    for (node_id, label, label_vi) in marcus_rows:
        person_id = node_id if node_id in valid_ids else None
        confidence = 'exact_id' if person_id else 'no_match'
        if person_id is None:
            unmatched += 1

        cur.execute(
            """INSERT INTO term_glossaries (term, term_zh, term_vi, person_id, source, confidence)
               VALUES (?, ?, ?, ?, 'marcus', ?)""",
            (label, label, label_vi, person_id, confidence)
        )
        inserted += 1

    conn.commit()

    # 4. Thống kê
    total = cur.execute("SELECT COUNT(*) FROM term_glossaries").fetchone()[0]
    linked = cur.execute("SELECT COUNT(*) FROM term_glossaries WHERE person_id IS NOT NULL").fetchone()[0]

    print(f"[DONE] term_glossaries:")
    print(f"  Tổng rows: {total}")
    print(f"  Đã link person_id: {linked} ({linked*100//total}%)")
    print(f"  Không match: {unmatched}")
    print()

    # 5. Kiểm tra sample
    samples = cur.execute("""
        SELECT t.term_zh, t.term_vi, t.person_id, t.confidence
        FROM term_glossaries t
        WHERE t.person_id IS NOT NULL
        LIMIT 5
    """).fetchall()
    print("Sample (term_zh | term_vi | person_id | confidence):")
    for r in samples:
        zh = (r[0] or '').encode('ascii','replace').decode()
        vi = (r[1] or '').encode('ascii','replace').decode()
        print(f"  {zh} | {vi} | {r[2]} | {r[3]}")

    conn.close()

if __name__ == '__main__':
    main()
