"""
T16 Nexus Events ETL
Tạo bảng nexus_events từ place_person_bibl (confidence >= 0.7, person_id IS NOT NULL).
Nguồn: Cao Tăng Truyện (唐/宋/梁/明高僧傳) parse từ CBETA với DILA entity links.
"""
import sqlite3, sys, datetime
sys.stdout.reconfigure(encoding='utf-8')

DB = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\lineage.db"
conn = sqlite3.connect(DB)

# Tạo bảng nexus_events
conn.executescript("""
CREATE TABLE IF NOT EXISTS nexus_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    passage_id TEXT,
    person_dila_id TEXT,
    place_dila_id TEXT,
    event_year INTEGER,
    event_label TEXT,
    source_book TEXT,
    confidence REAL DEFAULT 0.7,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_ne_place  ON nexus_events(place_dila_id);
CREATE INDEX IF NOT EXISTS idx_ne_person ON nexus_events(person_dila_id);
CREATE INDEX IF NOT EXISTS idx_ne_conf   ON nexus_events(confidence);
""")
conn.commit()
print("nexus_events table created/verified.")

# Xóa data cũ (idempotent re-run)
conn.execute("DELETE FROM nexus_events WHERE passage_id LIKE 'ppb:%'")
conn.commit()

# ETL từ place_person_bibl
rows = conn.execute("""
    SELECT id, place_id, person_id, person_name_raw, cbeta_ref, source_book, confidence
    FROM place_person_bibl
    WHERE person_id IS NOT NULL
      AND person_id LIKE 'A%'
      AND confidence >= 0.7
""").fetchall()

print(f"place_person_bibl source rows: {len(rows)}")

insert_data = []
for r in rows:
    ppb_id, place_id, person_id, name_raw, cbeta_ref, source_book, conf = r
    insert_data.append((
        f'ppb:{ppb_id}',
        person_id,
        place_id,
        None,              # event_year — không có trong place_person_bibl
        name_raw,          # event_label = person name raw
        source_book,
        conf,
        datetime.datetime.now().isoformat()
    ))

conn.executemany("""
    INSERT INTO nexus_events (passage_id, person_dila_id, place_dila_id, event_year, event_label, source_book, confidence, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", insert_data)
conn.commit()

total = conn.execute("SELECT COUNT(*) FROM nexus_events").fetchone()[0]
place_cnt = conn.execute("SELECT COUNT(DISTINCT place_dila_id) FROM nexus_events").fetchone()[0]
person_cnt = conn.execute("SELECT COUNT(DISTINCT person_dila_id) FROM nexus_events").fetchone()[0]
print(f"nexus_events populated: {total} rows | {place_cnt} places | {person_cnt} persons")

# Sample Thiếu Lâm Tự
sample = conn.execute("""
    SELECT ne.person_dila_id, ne.event_label, ne.source_book, ne.confidence,
           p.name_vi, p.name_zh
    FROM nexus_events ne
    LEFT JOIN people p ON p.id = ne.person_dila_id
    WHERE ne.place_dila_id = 'PL000000023255'
    LIMIT 5
""").fetchall()
print(f"\nSample Thiếu Lâm Tự ({len(sample)} rows shown):")
for r in sample:
    print(f"  {r[0]}({r[1]}) | {r[4] or r[5]} | {r[2]} | conf={r[3]}")

conn.close()
print("\nDONE.")
