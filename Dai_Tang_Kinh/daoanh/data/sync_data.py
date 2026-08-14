import sqlite3
import xml.etree.ElementTree as ET
import os
import re

# ĐƯỜNG DẪN CHUẨN
DB_PATH = '/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/lineage.db'
XML_PATH = '/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/dila_import/Authority-Databases/authority_place/Buddhist_Studies_Place_Authority.xml'

NS = '{http://www.tei-c.org/ns/1.0}'
XML_NS = '{http://www.w3.org/XML/1998/namespace}'

COUNTRY_MAP = {
    '阿富汗': 'Afghanistan', '印度': 'India', '中國': 'China',
    '巴基斯坦': 'Pakistan', '孟加拉': 'Bangladesh', '尼泊爾': 'Nepal',
    '緬甸': 'Myanmar', '泰國': 'Thailand', '斯里蘭卡': 'Sri Lanka',
    '柬埔寨': 'Cambodia', '寮國': 'Laos', '越南': 'Vietnam',
    '印尼': 'Indonesia', '馬來西亞': 'Malaysia', '蒙古': 'Mongolia',
    '日本': 'Japan', '南韓': 'South Korea', '北韓': 'North Korea',
    '俄羅斯': 'Russia', '哈薩克': 'Kazakhstan', '吉爾吉斯': 'Kyrgyzstan',
    '塔吉克': 'Tajikistan', '土庫曼': 'Turkmenistan', '烏茲別克': 'Uzbekistan',
    '伊朗': 'Iran', '菲律賓': 'Philippines', '汶萊': 'Brunei',
    '新加坡': 'Singapore', '台灣': 'Taiwan', '不丹': 'Bhutan',
    '美國': 'United States', '加拿大': 'Canada', '英國': 'United Kingdom',
    '法國': 'France', '德國': 'Germany', '義大利': 'Italy',
    '荷蘭': 'Netherlands', '比利時': 'Belgium', '希臘': 'Greece',
    '捷克': 'Czech Republic', '波蘭': 'Poland', '克羅埃西亞': 'Croatia',
}


def get_source_id(conn):
    """Lấy source_id cho DILA_PLACE"""
    row = conn.execute("SELECT id FROM dataset_sources WHERE name = 'DILA_PLACE'").fetchone()
    return row[0] if row else 1


def get_modern_country(district_raw):
    """Parse modern country from district_raw"""
    if not district_raw:
        return ''
    first = district_raw.split('-')[0].strip().split(';')[0].strip()
    return COUNTRY_MAP.get(first, first)


def get_province(district_raw):
    """Parse province from district_raw"""
    if not district_raw:
        return ''
    parts = district_raw.split('-')
    if len(parts) >= 2:
        second = parts[1].strip()
        m = re.search(r'\(([^)]+)\)', second)
        return m.group(1) if m else second
    return ''


def extract_fields(elem):
    """Extract all fields from a TEI place element"""
    xml_id = elem.get(XML_NS + 'id', '')

    # name_zh
    name_zh = ''
    name_elem = elem.find(f'.//{NS}placeName[@{XML_NS}lang="zho-Hant"]')
    if name_elem is not None:
        name_zh = name_elem.text or ''

    # GPS
    lat, lon = None, None
    geo_elem = elem.find(f'.//{NS}geo')
    if geo_elem is not None and geo_elem.text:
        coords = geo_elem.text.strip().split()
        if len(coords) >= 2:
            try:
                lon = float(coords[0])
                lat = float(coords[1])
            except:
                pass

    # District
    district_raw = ''
    district_elem = elem.find(f'{NS}district')
    if district_elem is not None and district_elem.text:
        district_raw = district_elem.text.strip()

    # Country (historical)
    hist_country_raw = ''
    country_elem = elem.find(f'{NS}country')
    if country_elem is not None and country_elem.text:
        hist_country_raw = country_elem.text.strip()

    # Raw XML
    xml_string = ET.tostring(elem, encoding='unicode')

    # Derived fields
    country = get_modern_country(district_raw)
    province = get_province(district_raw)

    return {
        'id': xml_id,
        'name_zh': name_zh,
        'gps_lat': lat,
        'gps_long': lon,
        'district_raw': district_raw,
        'hist_country_raw': hist_country_raw,
        'country': country,
        'province': province,
        'raw_xml': xml_string,
        'note': None,  # raw_xml is canonical for TEI XML; note reserved for human descriptions
    }


def full_overhaul():
    if not os.path.exists(XML_PATH):
        return print("❌ Không tìm thấy file XML!")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    source_id = get_source_id(conn)
    print(f"🚀 ĐANG NHẬP TOÀN BỘ ĐỊA DANH DILA VÀO SQLITE...")
    print(f"   Nguồn: DILA_PLACE (source_id={source_id})")

    count = 0
    batch = []

    try:
        context = ET.iterparse(XML_PATH, events=('end',))
        for event, elem in context:
            if elem.tag.endswith('place'):
                f = extract_fields(elem)

                batch.append((
                    f['id'], f['name_zh'], f['gps_lat'], f['gps_long'],
                    f['note'], f['raw_xml'], f['district_raw'], f['hist_country_raw'],
                    f['country'], f['province'],
                    source_id
                ))
                count += 1

                if len(batch) >= 5000:
                    cursor.executemany("""
                        INSERT OR REPLACE INTO places_pending
                            (id, name_zh, gps_lat, gps_long, note, raw_xml,
                             district_raw, hist_country_raw, country, province, source_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, batch)
                    conn.commit()
                    batch = []
                    print(f"✅ Đã an vị {count} địa danh...")

                elem.clear()

        if batch:
            cursor.executemany("""
                INSERT OR REPLACE INTO places_pending
                    (id, name_zh, gps_lat, gps_long, note, raw_xml,
                     district_raw, hist_country_raw, country, province, source_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, batch)
            conn.commit()

        print("-" * 50)
        print(f"✨ ĐẠI CÔNG CÁO THÀNH!")
        print(f"📦 Tổng số địa danh đã nạp: {count}")
        print(f"🔖 Nguồn: DILA_PLACE (CC BY-SA 4.0)")
        print("-" * 50)

    except Exception as e:
        print(f"❌ Lỗi: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    full_overhaul()
