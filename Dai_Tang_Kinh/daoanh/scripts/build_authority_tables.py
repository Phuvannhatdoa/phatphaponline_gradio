#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_authority_tables.py — T68a: tạo 2 bảng additive cho Source Authority Matrix + Conflict Detection.

Bảng mới (chỉ THÊM, không sửa bảng nguồn — reversible bằng DROP):
  1. source_authority — matrix xếp hạng nguồn (cấu hình, KHÔNG hardcode trong code).
  2. conflict_pending  — bảng phát hiện xung đột địa danh (place-aware).

Idempotent: CREATE TABLE IF NOT EXISTS + seed bằng INSERT OR IGNORE (an toàn chạy nhiều lần).

LƯU Ý: KHÔNG dùng wal_checkpoint/backup trong script (bài học T58).
"""
import os
import sys
import sqlite3

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'lineage.db')

SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS source_authority (
        source_code TEXT PRIMARY KEY,      -- 'DILA','CBETA','SAT','MARCUS','CHGIS','BDRC','FoJin','Wikidata','ZQLOCAL'
        source_id INTEGER,                 -- FK tham chiếu data_sources.source_id (NULL nếu chưa có trong data_sources)
        authority_score INTEGER,           -- điểm xếp hạng nguồn (cao = đáng tin hơn)
        precedence_order INTEGER,          -- thứ tự ưu tiên khi điểm bằng nhau (nhỏ = ưu tiên hơn)
        implemented INTEGER DEFAULT 0,     -- 1 = nguồn đã có dữ liệu trong DB; 0 = chưa implement (khớp T70 governance)
        note TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS conflict_pending (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_ref TEXT,                   -- 'PL…' (DILA ID dạng raw trong DB)
        field TEXT,                        -- 'name_vi' | 'gps_lat' | 'gps_long' | ...
        value_a TEXT, value_b TEXT,        -- 2 giá trị xung đột
        source_a TEXT, source_b TEXT,      -- tên nguồn tương ứng
        authority_a INTEGER, authority_b INTEGER,  -- điểm nguồn tương ứng
        status TEXT DEFAULT 'pending',     -- pending|resolved|accepted
        resolved_choice TEXT,
        resolved_by TEXT,
        resolved_at TEXT
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_conflict_pending_entity ON conflict_pending (entity_ref, status)",
    "CREATE INDEX IF NOT EXISTS idx_conflict_pending_status ON conflict_pending (status)",
]

# Matrix xếp hạng nguồn mục tiêu (có nguồn gốc, không giấu — admin có thể chỉnh qua cấu hình).
# implemented=1 cho nguồn đã thực sự đổ dữ liệu vào DB; 0 cho nguồn chờ T70/T69.
SEED = [
    # (source_code, source_id, authority_score, precedence_order, implemented, note)
    ('DILA',      1, 100, 1, 1, 'DILA Authority — nguồn chính thức địa danh Phật giáo (Đại Tạng Kinh)'),
    ('CBETA',     3,  80, 2, 1, 'CBETA Buddhist Canon — tham chiếu kinh văn'),
    ('SAT',    None,  75, 3, 0, 'SAT Daizōkyō Text Database — chưa implement (T70 governance)'),
    ('MARCUS',    4,  60, 4, 1, 'Marcus Glossary/Nets (Bingenheimer) — học thuật CC0'),
    ('CHGIS',  None,  58, 5, 0, 'China Historical GIS — chưa implement (T70 governance)'),
    ('BDRC',      2,  40, 6, 0, 'Buddhist Digital Resource Center — nguồn chưa active'),
    ('FoJin',  None,  40, 7, 0, 'FoJin (佛典) — chưa implement (T70 governance)'),
    ('Wikidata',None,  25, 8, 0, 'Wikidata — chỉ tham khảo ngoài, không phải nguồn chính'),
    ('ZQLOCAL',   5,  50, 0, 1, 'ZQ Local Data — dữ liệu Việt nội bộ (tên Việt do admin duyệt)'),
]


def main():
    if not os.path.isfile(DB_PATH):
        print(f"[ERR] Không tìm thấy DB: {DB_PATH}")
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    try:
        for stmt in SCHEMA:
            conn.execute(stmt)
        # Seed matrix — INSERT OR IGNORE (giữ nguyên nếu admin đã chỉnh)
        for row in SEED:
            conn.execute("""
                INSERT OR IGNORE INTO source_authority
                    (source_code, source_id, authority_score, precedence_order, implemented, note)
                VALUES (?, ?, ?, ?, ?, ?)
            """, row)
        # Với nguồn đã có trong data_sources, đồng bộ source_id nếu đang NULL
        conn.execute("""
            UPDATE source_authority
            SET source_id = (SELECT ds.source_id FROM data_sources ds WHERE ds.source_code = source_authority.source_code)
            WHERE source_id IS NULL AND EXISTS (SELECT 1 FROM data_sources ds WHERE ds.source_code = source_authority.source_code)
        """)
        conn.commit()
        # Verify
        for t in ('source_authority', 'conflict_pending'):
            n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info({t})")]
            print(f"  [OK] bảng {t}: rows={n} cols={cols}")
        print("--- source_authority seed ---")
        for r in conn.execute("SELECT source_code, source_id, authority_score, precedence_order, implemented FROM source_authority ORDER BY authority_score DESC"):
            print(f"    {r[0]:<10} source_id={r[1]} score={r[2]:<3} order={r[3]} implemented={r[4]}")
    finally:
        conn.close()
    print("[OK] T68a hoàn tất — 2 bảng + matrix đã sẵn sàng.")


if __name__ == '__main__':
    main()
