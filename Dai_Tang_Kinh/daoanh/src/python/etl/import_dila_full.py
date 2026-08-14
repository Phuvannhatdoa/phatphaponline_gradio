#!/usr/bin/env python3
"""
Import full DILA Authority - Fixed Vietnamese translation
"""

import xml.etree.ElementTree as ET
import json

DILA_XML = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/dila_temp/Buddhist_Studies_Place_Authority.xml"
OUTPUT_JSON = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/places_full.json"

def han_viet_convert(text):
    if not text: return ""
    
    # Direct replacements (full phrase first)
    phrases = {
        "闊悉多國": "Khost",
        "興都庫什山": "Hindu Kush",
        "印度": "Ấn Độ",
        "中國": "Trung Quốc",
        "日本": "Nhật Bản",
        "越南": "Việt Nam",
        "泰國": "Thái Lan",
        "北京": "Bắc Kinh",
        "上海": "Thượng Hải",
        "長安": "Trường An",
        "洛陽": "Lạc Dương",
        "少林寺": "Thiếu Lâm Tự",
        "靈山": "Linh Sơn",
        "普陀山": "Phổ Đà Sơn",
        "普陀": "Phổ Đà",
        "五台山": "Ngũ Đài Sơn",
        "峨眉山": "Nga Mi Sơn",
        "九華山": "Cửu Hoa Sơn",
        "天台山": "Thiên Đài Sơn",
        "廬山": "Lư Sơn",
        "金山寺": "Kim Sơn Tự",
        "靈隱寺": "Linh Ẩn Tự",
    }
    
    # Check full phrase match
    for zh, vi in phrases.items():
        if text == zh:
            return vi
    
    # Character-by-character for common suffixes
    result = text
    suffixes = [
        ("國", "Quốc"), ("省", "Tỉnh"), ("市", "Thành"), ("縣", "Huyện"),
        ("山", "Sơn"), ("江", "Giang"), ("河", "Hà"), ("湖", "Hồ"),
        ("海", "Hải"), ("州", "Châu"), ("府", "Phủ"), ("寺", "Tự"),
        ("院", "Viện"), ("堂", "Đường"), ("庵", "Am"), ("觀", "Quan"),
        ("塔", "Tháp"), ("林", "Lâm"), ("園", "Viên"), ("洞", "Động"),
    ]
    
    for zh, vi in suffixes:
        result = result.replace(zh, vi)
    
    return result if result != text else ""

print("📥 Parsing DILA Authority...")
tree = ET.parse(DILA_XML)
root = tree.getroot()
ns = root.tag.split('}')[0].strip('{') if '}' in root.tag else ''

places = []
for i, place in enumerate(root.findall(f'.//{{{ns}}}place')):
    place_id = place.get('{http://www.w3.org/XML/1998/namespace}id')
    if not place_id: continue
    
    name_zh = ""
    name_en = ""
    lat = ""
    lon = ""
    province = ""
    
    for child in place:
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        
        if tag == 'placeName':
            text = child.text or ""
            if text:
                if not name_zh and '\u4e00' <= text[0] <= '\u9fff':
                    name_zh = text
                elif not name_en:
                    name_en = text
        elif tag == 'latitude':
            lat = child.text or ""
        elif tag == 'longitude':
            lon = child.text or ""
        elif tag == 'district':
            province = child.text or ""
    
    name_vi = han_viet_convert(name_zh)
    
    places.append({
        'id': place_id,
        'nameChinese': name_zh,
        'nameVietnamese': name_vi,
        'nameEnglish': name_en,
        'lat': lat,
        'lon': lon,
        'province': province,
        'source': 'DILA'
    })

print(f"✅ Total: {len(places)} places")

with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
    json.dump({'places': places, 'count': len(places)}, f, ensure_ascii=False, indent=2)

print(f"💾 Saved: {OUTPUT_JSON}")

print("\n📊 Sample with Vietnamese names:")
for p in places[:15]:
    if p['nameChinese']:
        print(f"  {p['id']}: {p['nameChinese']} → {p['nameVietnamese']} | {p['lat']},{p['lon']}")
