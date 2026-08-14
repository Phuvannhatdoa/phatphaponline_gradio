#!/usr/bin/env python3
"""
Migration V3: Nâng cấp places_pending cho DILA Place Authority Full Schema.

Changes:
1. ALTER TABLE places_pending ADD COLUMN raw_xml, district_raw, hist_country_raw
2. Backfill data from existing note column (contains TEI XML)
3. Expand dataset_sources with DILA_PLACE, DILA_PERSON, DILA_TIME, MB_GLOSSARY, CBETA, SUTTACENTRAL, EIGHTY_THOUSAND
4. Update places_pending.source_id → DILA_PLACE
5. Parse district_raw → modern country, province

Chạy:
    cd /opt/.../daoanh
    python src_python/db/migrate_places_v3.py
"""

import sqlite3
import re
import os
import sys
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, 'data', 'lineage.db')

# Chinese → Latin country mapping (from actual district data)
COUNTRY_MAP = {
    '不丹': 'Bhutan',
    '中國': 'China',
    '伊朗': 'Iran',
    '俄羅斯': 'Russia',
    '克羅埃西亞': 'Croatia',
    '加拿大': 'Canada',
    '北韓': 'North Korea',
    '南韓': 'South Korea',
    '印尼': 'Indonesia',
    '印度': 'India',
    '台灣': 'Taiwan',
    '吉爾吉斯': 'Kyrgyzstan',
    '哈薩克': 'Kazakhstan',
    '土庫曼': 'Turkmenistan',
    '塔吉克': 'Tajikistan',
    '孟加拉': 'Bangladesh',
    '寮國': 'Laos',
    '尼泊爾': 'Nepal',
    '巴基斯坦': 'Pakistan',
    '希臘': 'Greece',
    '德國': 'Germany',
    '捷克': 'Czech Republic',
    '斯里蘭卡': 'Sri Lanka',
    '新加坡': 'Singapore',
    '日本': 'Japan',
    '柬埔寨': 'Cambodia',
    '比利時': 'Belgium',
    '法國': 'France',
    '波蘭': 'Poland',
    '泰國': 'Thailand',
    '烏茲別克': 'Uzbekistan',
    '汶萊': 'Brunei',
    '緬甸': 'Myanmar',
    '美國': 'United States',
    '義大利': 'Italy',
    '英國': 'United Kingdom',
    '荷蘭': 'Netherlands',
    '菲律賓': 'Philippines',
    '蒙古': 'Mongolia',
    '越南': 'Vietnam',
    '阿富汗': 'Afghanistan',
    '馬來西亞': 'Malaysia',
}

DATASET_SOURCES = [
    {
        'name': 'DILA_PLACE',
        'source_type': 'authority',
        'origin_url': 'https://authority.dila.edu.tw/place/',
        'license': 'CC BY-SA 4.0',
        'usage_level': 'YELLOW',
        'attribution_text': 'Dữ liệu địa danh từ Buddhist Place Authority Database, Dharma Drum Institute of Liberal Arts (DILA), CC BY-SA 4.0.',
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


def parse_country_from_district(district_raw):
    """Parse modern country from district_raw (e.g., '阿富汗-巴爾赫省(Balkh)-Khulm' → 'Afghanistan')"""
    if not district_raw:
        return ''
    # Take first segment before '-'
    first = district_raw.split('-')[0].strip()
    # Handle semicolons (multiple countries)
    first = first.split(';')[0].strip()
    return COUNTRY_MAP.get(first, first)


def parse_province_from_district(district_raw):
    """Parse province from district_raw (e.g., '阿富汗-巴爾赫省(Balkh)-Khulm' → 'Balkh')"""
    if not district_raw:
        return ''
    parts = district_raw.split('-')
    if len(parts) >= 2:
        second = parts[1].strip()
        # Extract English name from parentheses if present
        m = re.search(r'\(([^)]+)\)', second)
        if m:
            return m.group(1)
        return second
    return ''


def extract_from_xml(note_text):
    """Extract district_raw, hist_country_raw from TEI XML string"""
    if not note_text:
        return '', '', ''
    
    # district
    m = re.search(r'<ns0:district>(.*?)</ns0:district>', note_text, re.DOTALL)
    district_raw = m.group(1).strip() if m else ''
    
    # country (historical)
    m = re.search(r'<ns0:country>(.*?)</ns0:country>', note_text, re.DOTALL)
    hist_country_raw = m.group(1).strip() if m else ''
    
    return district_raw, hist_country_raw


def migrate():
    print('=' * 60)
    print('  🚀 MIGRATION V3: Nâng cấp places_pending cho DILA Full Schema')
    print('=' * 60)
    print(f'\n📂 Database: {DB_PATH}')
    
    if not os.path.exists(DB_PATH):
        print(f'❌ Không tìm thấy database: {DB_PATH}')
        sys.exit(1)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    t0 = time.time()
    
    try:
        # ===== STEP 1: ALTER TABLE =====
        print('\n[1/5] Thêm cột mới vào places_pending...')
        alter_commands = [
            ('ALTER TABLE places_pending ADD COLUMN raw_xml TEXT', 'raw_xml'),
            ('ALTER TABLE places_pending ADD COLUMN district_raw TEXT', 'district_raw'),
            ('ALTER TABLE places_pending ADD COLUMN hist_country_raw TEXT', 'hist_country_raw'),
        ]
        for sql, col in alter_commands:
            try:
                conn.execute(sql)
                conn.commit()
                print(f'  ✅ Đã thêm cột {col}')
            except sqlite3.OperationalError as e:
                if 'duplicate column' in str(e).lower() or 'already exists' in str(e).lower():
                    print(f'  ⏭️  Cột {col} đã tồn tại')
                else:
                    raise e
        
        # ===== STEP 2: Copy note → raw_xml =====
        print('\n[2/5] Sao chép note → raw_xml...')
        total = conn.execute('SELECT COUNT(*) FROM places_pending WHERE note IS NOT NULL').fetchone()[0]
        conn.execute("UPDATE places_pending SET raw_xml = note WHERE raw_xml IS NULL AND note IS NOT NULL")
        conn.commit()
        print(f'  ✅ Đã sao chép {total} bản ghi (note → raw_xml)')
        
        # ===== STEP 3: Backfill district_raw, hist_country_raw =====
        print('\n[3/5] Phân tích XML để trích xuất district_raw, hist_country_raw...')
        rows = conn.execute(
            "SELECT id, note FROM places_pending WHERE note IS NOT NULL AND (district_raw IS NULL OR hist_country_raw IS NULL)"
        ).fetchall()
        total_rows = len(rows)
        print(f'  📊 Cần xử lý: {total_rows} bản ghi')
        
        batch = []
        updated = 0
        for i, row in enumerate(rows):
            district_raw, hist_country_raw = extract_from_xml(row['note'])
            country = parse_country_from_district(district_raw)
            province = parse_province_from_district(district_raw)
            batch.append((district_raw, hist_country_raw, country, province, row['id']))
            
            if len(batch) >= 1000:
                conn.executemany(
                    "UPDATE places_pending SET district_raw = ?, hist_country_raw = ?, country = ?, province = ? WHERE id = ?",
                    batch
                )
                conn.commit()
                updated += len(batch)
                batch = []
                print(f'  ⏳ {updated}/{total_rows}...')
        
        if batch:
            conn.executemany(
                "UPDATE places_pending SET district_raw = ?, hist_country_raw = ?, country = ?, province = ? WHERE id = ?",
                batch
            )
            conn.commit()
            updated += len(batch)
        
        print(f'  ✅ Đã cập nhật {updated}/{total_rows} bản ghi')
        
        # ===== STEP 4: Expand dataset_sources =====
        print('\n[4/5] Mở rộng dataset_sources...')
        existing = {r['name'] for r in conn.execute('SELECT name FROM dataset_sources').fetchall()}
        
        for src in DATASET_SOURCES:
            if src['name'] not in existing:
                conn.execute("""
                    INSERT INTO dataset_sources (name, source_type, origin_url, license, usage_level, attribution_text, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (src['name'], src['source_type'], src['origin_url'], src['license'],
                      src['usage_level'], src['attribution_text'], src['notes']))
                print(f'  ✅ Đã thêm: {src["name"]} ({src["license"]}, {src["usage_level"]})')
            else:
                print(f'  ⏭️  Đã tồn tại: {src["name"]}')
        conn.commit()
        
        # Get DILA_PLACE id and update source_id
        dila_place = conn.execute("SELECT id FROM dataset_sources WHERE name = 'DILA_PLACE'").fetchone()
        if dila_place:
            dila_place_id = dila_place[0]
            conn.execute("UPDATE places_pending SET source_id = ? WHERE source_id IS NULL OR source_id != ?", (dila_place_id, dila_place_id))
            conn.commit()
            print(f'  ✅ Đã cập nhật source_id = {dila_place_id} (DILA_PLACE) cho places_pending')
        
        # ===== STEP 5: Verify =====
        print('\n[5/5] Xác minh kết quả...')
        
        # Check PL000000000014
        row = conn.execute("""
            SELECT id, name_zh, country, province, gps_lat, gps_long,
                   district_raw, hist_country_raw,
                   LENGTH(raw_xml) as raw_len, LENGTH(note) as note_len,
                   source_id
            FROM places_pending WHERE id = 'PL000000000014'
        """).fetchone()
        
        if row:
            print(f'\n  📝 Mẫu: PL000000000014 (土火羅)')
            print(f'     country:       {row["country"]}')
            print(f'     province:      {row["province"]}')
            print(f'     gps_lat:       {row["gps_lat"]}')
            print(f'     gps_long:      {row["gps_long"]}')
            print(f'     district_raw:  {row["district_raw"]}')
            print(f'     hist_country_raw: {row["hist_country_raw"]}')
            print(f'     raw_xml len:   {row["raw_len"]}')
            print(f'     note len:      {row["note_len"]}')
            print(f'     source_id:     {row["source_id"]}')
        
        # Stats
        stats = conn.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN raw_xml IS NOT NULL THEN 1 ELSE 0 END) as has_raw,
                SUM(CASE WHEN district_raw IS NOT NULL AND district_raw != '' THEN 1 ELSE 0 END) as has_district,
                SUM(CASE WHEN hist_country_raw IS NOT NULL AND hist_country_raw != '' THEN 1 ELSE 0 END) as has_country,
                SUM(CASE WHEN country IS NOT NULL AND country != '' THEN 1 ELSE 0 END) as has_modern_country,
                SUM(CASE WHEN province IS NOT NULL AND province != '' THEN 1 ELSE 0 END) as has_province
            FROM places_pending
        """).fetchone()
        
        print(f'\n  📊 Thống kê places_pending:')
        print(f'     Tổng số:              {stats["total"]}')
        print(f'     Có raw_xml:           {stats["has_raw"]}')
        print(f'     Có district_raw:      {stats["has_district"]}')
        print(f'     Có hist_country_raw:  {stats["has_country"]}')
        print(f'     Có country (hiện đại): {stats["has_modern_country"]}')
        print(f'     Có province:          {stats["has_province"]}')
        
        elapsed = time.time() - t0
        print(f'\n  ⏱️  Thời gian: {elapsed:.1f}s')
        print(f'\n{"=" * 60}')
        print(f'  🎉 MIGRATION V3 HOÀN TẤT!')
        print(f'{"=" * 60}')
        
    except Exception as e:
        print(f'\n❌ LỖI: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    migrate()
