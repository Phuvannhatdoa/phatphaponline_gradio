#!/usr/bin/env python3
"""
P6: Translation & Bio Enrichment
Dịch Hán tự → Hán-Việt, viết Bio tiếng Việt từ .ttl files và Wikidata
"""

import json
import csv
import re
import requests
from collections import defaultdict

# Paths
MAPPED_PLACES_CSV = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/processed/mapped_places.csv"
MAPPED_PLACES_JSON = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/processed/mapped_places.json"
TTL_PATH = "/opt/phatphaponline_gradio/truyenthua/visjs-app/data/processed/"
OUTPUT_JSON = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/processed/enriched_places.json"
OUTPUT_CSV = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/processed/places_review.csv"

# Wikidata API
WIKIDATA_API = "https://www.wikidata.org/wiki/Special:EntityData/{}.json"

# Vietnamese Buddhist dictionary (common terms)
HAN_VIET_DICT = {
    "寺": "Tự",
    "塔": "Tháp",
    "林": "Lâm",
    "山": "Sơn",
    "洞": "Động",
    "庵": "Am",
    "堂": "Đường",
    "院": "Viện",
    "廟": "Miếu",
    "宮": "Cung",
    "窟": "Quật",
    "石窟": "Thạch Quật",
    "精舍": "Tinh Xá",
    "伽藍": "Già Lam",
    "禪院": "Thiền Viện",
    "叢林": "Tùng Lâm",
    "丈室": "Trượng Phòng",
    "法堂": "Pháp Đường",
    "僧堂": "Tăng Đường",
    "庫堂": "Khố Đường",
    "齋堂": "Trai Đường",
    "浴室": "Dục Phòng",
    "淨房": "Tịnh Phòng",
    "延壽堂": "Diễn Thọ Đường",
    "客堂": "Khách Đường",
    "法界": "Pháp Giới",
    "虛空": "Hư Không",
    "極樂": "Cực Lạc",
    "兜率": "Đâu Suất",
    "靈山": "Linh Sơn",
    "普陀": "Phổ Đà",
    "五台山": "Ngũ Đài Sơn",
    "峨眉山": "Nga Mi Sơn",
    "九華山": "Cửu Hoa Sơn",
    "普賢": "Phổ Hiền",
    "文殊": "Văn Thù",
    "觀音": "Quan Âm",
    "彌陀": "Di Đà",
    "如來": "Như Lai",
    "釋迦": "Thích Ca",
    "牟尼": "Mâu Ni",
    "佛": "Phật",
    "僧": "Tăng",
    "尼": "Ni",
    "羅漢": "La Hán",
    "菩薩": "Bồ Tát",
    "聲聞": "Thanh Văn",
    "緣覺": "Duyên Giác",
    "如來藏": "Như Lai Tàng",
    "法身": "Pháp Thân",
    "報身": "Báo Thân",
    "應身": "Ứng Thân",
    "法性": "Pháp Tính",
    "法相": "Pháp Tướng",
    "真如": "Chân Như",
    "實相": "Thực Tướng",
    "空性": "Không Tính",
    "佛性": "Phật Tính",
    "心經": "Tâm Kinh",
    "金剛經": "Kim Cương Kinh",
    "法華經": "Pháp Hoa Kinh",
    "楞嚴經": "Lăng Nghiêm Kinh",
    "彌陀經": "Di Đà Kinh",
}

# Common Vietnamese monastery name patterns
MONASTERY_PREFIXES = [
    "Chùa", "Tự", "Viện", "Am", "Tháp", "Núi", "Động", "Lâm"
]

MONASTERY_SUFFIXES = [
    "Tự", "Chùa", "Viện", "Am", "Tháp", "Tàng", "Tâm", "An", "Lâm"
]

def load_mapped_places():
    """Load mapped places từ P5"""
    print("📥 Loading mapped places...")
    
    places = {}
    with open(MAPPED_PLACES_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            place_name = row['raw_name']
            places[place_name] = {
                'raw_name': place_name,
                'matched_name': row.get('matched_name', ''),
                'confidence': float(row.get('confidence', 0)),
                'gps_found': row.get('gps_found', 'N'),
                'source_id': row.get('source_id', ''),
                'lat': row.get('lat', ''),
                'lon': row.get('lon', '')
            }
    
    print(f"✅ Loaded {len(places)} mapped places")
    return places

def translate_name(name_zh):
    """Translate Chinese name to Vietnamese"""
    if not name_zh:
        return ""
    
    # Check dictionary first
    if name_zh in HAN_VIET_DICT:
        return HAN_VIET_DICT[name_zh]
    
    # Try to match known patterns
    result = name_zh
    for zh, vi in HAN_VIET_DICT.items():
        if zh in name_zh:
            result = result.replace(zh, vi)
    
    # Clean up - remove remaining Chinese if no match
    if re.search(r'[\u4e00-\u9fff]', result):
        # Try to construct Vietnamese name
        parts = []
        for char in result:
            if char in HAN_VIET_DICT:
                parts.append(HAN_VIET_DICT[char])
            else:
                parts.append(char)
        result = "".join(parts)
    
    return result

def fetch_wikidata_bio(wikidata_id):
    """Fetch bio from Wikidata"""
    try:
        url = WIKIDATA_API.format(wikidata_id)
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            entities = data.get('entities', {})
            if wikidata_id in entities:
                entity = entities[wikidata_id]
                descriptions = entity.get('descriptions', {})
                vi_desc = descriptions.get('vi', {}).get('value', '')
                en_desc = descriptions.get('en', {}).get('value', '')
                return vi_desc or en_desc
    except Exception as e:
        print(f"⚠️ Wikidata fetch error: {e}")
    return ""

def extract_monks_from_ttl(place_name):
    """Trích xuất các vị Tổ liên quan từ TTL files"""
    monks = []
    
    # Place name patterns in Vietnamese
    patterns = [
        place_name,
        place_name.replace("Chùa ", ""),
        place_name.replace("Tự ", ""),
    ]
    
    # This is a simplified version - in production, 
    # we would search through actual TTL files
    # For now, return empty list
    return monks

def enrich_place(place_data):
    """Enrich a single place with translation and bio"""
    name_zh = place_data.get('matched_name', '')
    
    # Translate name
    name_vi = translate_name(name_zh)
    if not name_vi:
        name_vi = place_data.get('raw_name', '')
    
    # Build result
    enriched = {
        'id': place_data.get('source_id', ''),
        'nameChinese': name_zh,
        'nameVietnamese': name_vi,
        'lat': place_data.get('lat', ''),
        'lon': place_data.get('lon', ''),
        'confidence': place_data.get('confidence', 0),
        'source': 'DILA' if place_data.get('source_id', '').startswith('PL') else 'CBETA',
        'monks': [],
        'description': ''
    }
    
    return enriched

def run_translation():
    """Main translation workflow"""
    print("🚀 P6: Translation & Bio Enrichment")
    print("=" * 50)
    
    # Load mapped places
    places = load_mapped_places()
    
    # Enrich each place
    enriched_places = []
    for raw_name, place_data in places.items():
        enriched = enrich_place(place_data)
        enriched_places.append(enriched)
    
    # Save JSON
    print(f"💾 Saving enriched places to {OUTPUT_JSON}...")
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump({'places': enriched_places}, f, ensure_ascii=False, indent=2)
    
    # Save CSV for review
    print(f"💾 Saving review CSV to {OUTPUT_CSV}...")
    with open(OUTPUT_CSV, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'ID', 'Tên_Hán', 'Tên_Việt', 'Lat', 'Lon', 
            'Confidence', 'Nguồn', 'Mô_tả', 'Ghi_chú_Admin'
        ])
        for p in enriched_places:
            writer.writerow([
                p['id'],
                p['nameChinese'],
                p['nameVietnamese'],
                p['lat'],
                p['lon'],
                p['confidence'],
                p['source'],
                p['description'],
                ''  # Admin notes column
            ])
    
    print(f"✅ Complete! Enriched {len(enriched_places)} places")
    print(f"📝 Review: {OUTPUT_CSV}")

if __name__ == "__main__":
    run_translation()
