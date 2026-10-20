#!/usr/bin/env python3
"""
Khởi tạo bảng dataset_sources và cập nhật các bảng chính với cột source_id.

Đây là lớp Metadata Hàn Lâm (Academic Provenance Layer) cho toàn bộ Database.
Mục tiêu: Mọi bản ghi trong hệ thống đều có thể giải trình được nguồn gốc,
license và mức độ sử dụng (GREEN/YELLOW/RED).

Hệ thống phân cấp an toàn:
- GREEN: CC0 — có thể tự do xuất bản ra cộng đồng
- YELLOW: CC BY-SA 4.0 — cần ghi công khi hiển thị
- RED: Nội bộ — chỉ dùng trong admin

Chạy script:
    cd /opt/.../daoanh
    python src_python/db/init_dataset_sources.py
"""

import sqlite3
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, 'data', 'lineage.db')

SEED_SOURCES = [
    {
        'name': 'DILA_Authority',
        'source_type': 'authority',
        'origin_url': 'https://authority.dila.edu.tw/',
        'license': 'CC BY-SA 4.0',
        'usage_level': 'YELLOW',
        'attribution_text': 'Dữ liệu được cung cấp bởi DILA Authority (CBETA, 佛學規範資料庫) theo giấy phép CC BY-SA 4.0.',
        'notes': 'Nguồn chính thức về địa danh và nhân vật Phật giáo từ Đại Tạng Kinh.'
    },
    {
        'name': 'Marcus_fojin',
        'source_type': 'glossary',
        'origin_url': 'https://github.com/marcusbingenheimer/',
        'license': 'CC0',
        'usage_level': 'GREEN',
        'attribution_text': 'Dữ liệu tham chiếu từ công trình nghiên cứu của Marcus Bingenheimer (CC0).',
        'notes': 'Dữ liệu học thuật về địa danh Phật giáo, đối chiếu từ nhiều nguồn Đại Tạng Kinh.'
    },
    {
        'name': 'DILA_PLACE',
        'source_type': 'authority',
        'origin_url': 'https://authority.dila.edu.tw/place/',
        'license': 'CC BY-SA 4.0',
        'usage_level': 'YELLOW',
        'attribution_text': 'Dữ liệu địa danh từ Buddhist Place Authority Database, DILA, CC BY-SA 4.0.',
        'notes': 'Buddhist Place Authority Database — địa danh Phật giáo từ Đại Tạng Kinh.'
    },
    {
        'name': 'DILA_PERSON',
        'source_type': 'authority',
        'origin_url': 'https://authority.dila.edu.tw/person/',
        'license': 'CC BY-SA 4.0',
        'usage_level': 'YELLOW',
        'attribution_text': 'Dữ liệu nhân vật từ Buddhist Person Authority Database, DILA, CC BY-SA 4.0.',
        'notes': 'Buddhist Person Authority Database — nhân vật Phật giáo lịch sử.'
    },
    {
        'name': 'DILA_TIME',
        'source_type': 'authority',
        'origin_url': 'https://authority.dila.edu.tw/time/',
        'license': 'CC BY-SA 4.0',
        'usage_level': 'YELLOW',
        'attribution_text': 'Dữ liệu niên đại từ DDBC Time Authority Database, DILA, CC BY-SA 4.0.',
        'notes': 'DDBC Time Authority Database — niên đại và thời kỳ lịch sử Phật giáo.'
    },
    {
        'name': 'MB_GLOSSARY',
        'source_type': 'glossary',
        'origin_url': 'https://github.com/mbingenheimer/buddhist_studies_glossaries',
        'license': 'CC0',
        'usage_level': 'GREEN',
        'attribution_text': 'Từ điển thuật ngữ Phật học từ buddhist_studies_glossaries (Marcus Bingenheimer), CC0 1.0 Universal.',
        'notes': 'Buddhist studies glossaries — thuật ngữ đa ngôn ngữ Phật học.'
    },
    {
        'name': 'CBETA',
        'source_type': 'canon',
        'origin_url': 'https://cbeta.org/',
        'license': 'CC BY-SA 4.0',
        'usage_level': 'YELLOW',
        'attribution_text': 'Tham chiếu kinh văn từ CBETA (Chinese Buddhist Electronic Text Association), CC BY-SA 4.0.',
        'notes': 'Chỉ lưu metadata/tham chiếu, không import toàn bộ corpus.'
    },
    {
        'name': 'SUTTACENTRAL',
        'source_type': 'canon',
        'origin_url': 'https://suttacentral.net/',
        'license': 'CC BY-NC-SA 4.0',
        'usage_level': 'YELLOW',
        'attribution_text': 'Tham chiếu kinh văn từ SuttaCentral, CC BY-NC-SA 4.0.',
        'notes': 'Chỉ lưu metadata/tham chiếu, không import toàn bộ corpus.'
    },
    {
        'name': 'EIGHTY_THOUSAND',
        'source_type': 'canon',
        'origin_url': 'https://84000.co/',
        'license': 'CC BY-NC-SA 4.0',
        'usage_level': 'YELLOW',
        'attribution_text': 'Tham chiếu kinh văn từ 84000: Translating the Words of the Buddha, CC BY-NC-SA 4.0.',
        'notes': 'Chỉ lưu metadata/tham chiếu, không import toàn bộ corpus.'
    },
]

ALTER_TABLES = [
    ("ALTER TABLE places_pending ADD COLUMN source_id INTEGER REFERENCES dataset_sources(id)", "places_pending"),
    ("ALTER TABLE places_dila ADD COLUMN source_id INTEGER REFERENCES dataset_sources(id)", "places_dila"),
    ("ALTER TABLE namevi_map_places ADD COLUMN source_id INTEGER REFERENCES dataset_sources(id)", "namevi_map_places"),
    ("ALTER TABLE people ADD COLUMN source_id INTEGER REFERENCES dataset_sources(id)", "people"),
]


def migrate():
    print(f"[MIGRATION] Đường dẫn DB: {DB_PATH}")
    if not os.path.exists(DB_PATH):
        print(f"[LỖI] Không tìm thấy database tại: {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Tạo bảng dataset_sources
    print("\n[1/3] Tạo bảng dataset_sources...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dataset_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            source_type TEXT,
            origin_url TEXT,
            license TEXT,
            usage_level TEXT CHECK(usage_level IN ('GREEN', 'YELLOW', 'RED')) DEFAULT 'YELLOW',
            attribution_text TEXT,
            notes TEXT
        )
    """)
    conn.commit()
    print("  ✅ Bảng dataset_sources đã sẵn sàng.")

    # 2. Seed dữ liệu
    print("\n[2/3] Seed dữ liệu nguồn...")
    existing = cursor.execute("SELECT name FROM dataset_sources").fetchall()
    existing_names = {row[0] for row in existing}

    for src in SEED_SOURCES:
        if src['name'] not in existing_names:
            cursor.execute("""
                INSERT INTO dataset_sources (name, source_type, origin_url, license, usage_level, attribution_text, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (src['name'], src['source_type'], src['origin_url'], src['license'],
                  src['usage_level'], src['attribution_text'], src['notes']))
            print(f"  ✅ Đã thêm: {src['name']} ({src['license']}, {src['usage_level']})")
        else:
            print(f"  ⏭️  Đã tồn tại: {src['name']}")
    conn.commit()

    # 3. Thêm cột source_id vào các bảng chính
    print("\n[3/3] Thêm cột source_id vào các bảng chính...")
    for alter_sql, table_name in ALTER_TABLES:
        try:
            cursor.execute(alter_sql)
            conn.commit()
            print(f"  ✅ Đã thêm source_id vào bảng {table_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                print(f"  ⏭️  Cột source_id đã tồn tại trong bảng {table_name}")
            else:
                print(f"  ⚠️  Lỗi khi thêm vào {table_name}: {e}")

    # 4. Cập nhật source_id mặc định cho các bảng dựa trên logic hiện tại
    print("\n[Bonus] Cập nhật source_id mặc định...")
    dila_place = cursor.execute("SELECT id FROM dataset_sources WHERE name = 'DILA_PLACE'").fetchone()
    dila_auth = cursor.execute("SELECT id FROM dataset_sources WHERE name = 'DILA_Authority'").fetchone()
    marcus = cursor.execute("SELECT id FROM dataset_sources WHERE name = 'Marcus_fojin'").fetchone()

    dila_place_id = dila_place[0] if dila_place else (dila_auth[0] if dila_auth else 1)
    marcus_id = marcus[0] if marcus else None

    # places_pending: DILA_PLACE
    cursor.execute("UPDATE places_pending SET source_id = ? WHERE source_id IS NULL", (dila_place_id,))
    print(f"  ✅ places_pending: gán source_id={dila_place_id} (DILA_PLACE)")
    # places_dila: DILA_PLACE
    cursor.execute("UPDATE places_dila SET source_id = ? WHERE source_id IS NULL", (dila_place_id,))
    print(f"  ✅ places_dila: gán source_id={dila_place_id} (DILA_PLACE)")
    # people: DILA_PERSON
    dila_person = cursor.execute("SELECT id FROM dataset_sources WHERE name = 'DILA_PERSON'").fetchone()
    if dila_person:
        cursor.execute("UPDATE people SET source_id = ? WHERE source_id IS NULL", (dila_person[0],))
        print(f"  ✅ people: gán source_id={dila_person[0]} (DILA_PERSON)")

    if marcus_id:
        cursor.execute("UPDATE namevi_map_places SET source_id = ? WHERE source_id IS NULL", (marcus_id,))
        print(f"  ✅ namevi_map_places: gán source_id={marcus_id} (Marcus_fojin)")

    conn.commit()
    conn.close()

    print("\n" + "=" * 60)
    print("  🎉 MIGRATION HOÀN TẤT!")
    print("  Lớp Metadata Hàn Lâm (dataset_sources) đã được niêm phong.")
    print("=" * 60)
    print("\nCác nguồn dữ liệu hiện có:")
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT id, name, license, usage_level FROM dataset_sources").fetchall()
    for r in rows:
        print(f"  [{r[0]}] {r[1]} — {r[2]} ({r[3]})")
    conn.close()


if __name__ == '__main__':
    migrate()
