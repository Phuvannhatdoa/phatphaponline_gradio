#!/usr/bin/env python3
"""
P5: Map places - Extended dictionary matching
Raw places (Vietnamese) <-> DILA (Chinese/English/Vietnamese)
"""

import csv
import json

RAW_PLACES = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/processed/raw_vietnam_places.csv"
MASTER_LIST = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/places_full.json"
OUTPUT_CSV = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/processed/mapped_places.csv"

# Vietnamese to Chinese temple name mappings
VIETNAMESE_TO_CHINESE = {
    # General terms
    "giới đàn": "戒壇",
    "đại giới": "大戒",
    "tổ đình": "祖庭",
    "chùa": "寺",
    
    # Famous Vietnamese temples
    "báo quốc": "報國",
    "huế": "順化",
    "quảng nghiêm": "光嚴",
    "quảng đức": "光德",
    "quảng tế": "光濟",
    "quảng tâm": "光心",
    "quảng minh": "光明",
    "phước lâm": "福林",
    "phước viện": "福苑",
    "phước định": "福定",
    "thập tháp": "十塔",
    "tây thiên": "西天",
    "trúc lâm": "竹林",
    "thiền lâm": "禪林",
    "cổ pháp": "古法",
    "vĩnh nghiệm": "永驗",
    "vĩnh phúc": "永福",
    "vĩnh trì": "永池",
    "bắc môn": "北門",
    "nam môn": "南門",
    "đông môn": "東門",
    "tây môn": "西門",
    "phật tổ": "佛祖",
    "phật học": "佛學",
    "phật pháp": "佛法",
    "diệu pháp": "妙法",
    "diệu hạnh": "妙行",
    "diệu quang": "妙光",
    "diệu võng": "妙網",
    "ngọc hoàng": "玉皇",
    "ngọc phật": "玉佛",
    "kim đan": "金丹",
    "kim cang": "金剛",
    "kim liên": "金蓮",
    "thanh vân": "青雲",
    "thanh lộc": "青祿",
    "huyền viện": "玄院",
    "huyền khê": "玄溪",
    "long sơn": "龍山",
    "long viễn": "龍遠",
    "long vĩnh": "龍永",
    "long phước": "龍福",
    "linh sơn": "靈山",
    "linh quang": "靈光",
    "linh ứng": "靈應",
    "linh phong": "靈風",
    "linh viễn": "靈遠",
    "linh trì": "靈池",
    "linh xứ": "靈所",
    "từ hiếu": "慈孝",
    "từ quang": "慈光",
    "từ tâm": "慈心",
    "từ liên": "慈蓮",
    "đại giáo": "大教",
    "đại thắng": "大勝",
    "đại định": "大定",
    "đại an": "大安",
    "đại lành": "大善",
    "minh chủ": "明主",
    "minh đức": "明德",
    "minh tâm": "明心",
    "minh thanh": "明清",
    "hòa bình": "和平",
    "hòa thượng": "和上",
    "hòa an": "和安",
    "phúc định": "福定",
    "phúc an": "福安",
    "phúc lộc": "福祿",
    "phúc thọ": "福壽",
    "phúc hưng": "福興",
    "an giáo": "安教",
    "an ninh": "安寧",
    "an bình": "安平",
    "an lạc": "安樂",
    "thành công": "成功",
    "thành phát": "發達",
    "thành trì": "城池",
    "bảo giác": "保覺",
    "bảo định": "保定",
    "bảo an": "保安",
    "bảo thắng": "保勝",
    "bảo phước": "保福",
    "phổ đà": "普陀",
    "phổ chiếu": "普照",
    "phổ phong": "普風",
    "phổ minh": "普明",
    "phổ an": "普安",
    "nguyệt đình": "月亭",
    "nguyệt minh": "月明",
    "nhật minh": "日明",
    "nhật tường": "日祥",
    "trường an": "長安",
    "trường phước": "長福",
    "trường dục": "長育",
    "phong phước": "豐福",
    "phong an": "豐安",
    "phong lâm": "豐林",
    "hồng phước": "洪福",
    "hồng đức": "洪德",
    "hồng lĩnh": "洪嶺",
    "hồng viễn": "洪遠",
    "thắng lợi": "勝利",
    "thắng cảnh": "勝景",
    "thắng phước": "勝福",
    "trung an": "中安",
    "trung định": "中定",
    "trung hòa": "中和",
    "hòa hảo": "和豪",
    "hòa lợi": "和利",
    "đức phật": "佛祖",
    "đức trung": "德忠",
    "đức an": "德安",
    "đức hòa": "德和",
    "tường vân": "祥雲",
    "tường phước": "祥福",
    "tường an": "祥安",
    "tường hòa": "祥和",
    "thái bình": "太平",
    "thái an": "太安",
    "thái nhàn": "太閒",
    "thái hòa": "太和",
    "vạn phúc": "萬福",
    "vạn an": "萬安",
    "vạn hòa": "萬和",
    "vạn đức": "萬德",
    "nguyễn trung": "阮忠",
    "nguyễn phước": "阮福",
    "trần vĩnh": "陳永",
    "trần trung": "陳忠",
    "lê phước": "黎福",
    "lê trung": "黎忠",
    "võ trung": "武忠",
    "võ phước": "武福",
    "hồ trung": "胡忠",
    "hồ phước": "胡福",
    "đặng trung": "鄧忠",
    "đặng phước": "鄧福",
    "quách trung": "郭忠",
    "quách phước": "郭福",
}

def normalize(s):
    if not s:
        return ""
    return s.lower().strip()

def main():
    print("📥 Loading master list...")
    with open(MASTER_LIST, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    master_places = data.get('places', [])
    print(f"✅ Loaded {len(master_places)} master places")
    
    # Build index from DILA
    master_index = {}
    for mp in master_places:
        for key in ['nameVietnamese', 'nameChinese', 'nameEnglish']:
            val = mp.get(key, '')
            if val:
                master_index[normalize(val)] = mp
    
    # Add Vietnamese->Chinese dictionary
    matched_count = 0
    for vi, zh in VIETNAMESE_TO_CHINESE.items():
        if zh in master_index:
            master_index[vi] = master_index[zh]
            matched_count += 1
    
    print(f"📊 Dictionary matched: {matched_count}")
    print(f"📥 Loading raw places...")
    
    raw_places = {}
    with open(RAW_PLACES, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            place_name = row['place_name_raw']
            if place_name not in raw_places:
                raw_places[place_name] = {
                    'frequency': int(row['frequency']),
                    'monks': []
                }
            raw_places[place_name]['monks'].append({
                'name': row['mentioned_in_monk'],
                'uri': row['source_monk_uri']
            })
    
    print(f"✅ Loaded {len(raw_places)} unique raw places")
    
    mapped = []
    unmapped = []
    
    for raw_name, data in raw_places.items():
        match = None
        score = 0
        raw_norm = normalize(raw_name)
        
        # Dictionary lookup
        if raw_norm in master_index:
            match = master_index[raw_norm]
            score = 1.0
        else:
            # Partial match for multi-word names
            for key, mp in master_index.items():
                if len(key) >= 3 and key in raw_norm:
                    match = mp
                    score = 0.7
                    break
                if len(raw_norm) >= 3 and raw_norm in key:
                    match = mp
                    score = 0.7
                    break
        
        if match:
            mapped.append({
                'raw_name': raw_name,
                'matched_name': match.get('nameVietnamese') or match.get('nameChinese') or match.get('nameEnglish', ''),
                'matched_id': match.get('id', ''),
                'confidence': round(score, 2),
                'gps_found': bool(match.get('lat') and match.get('lon')),
                'lat': match.get('lat', ''),
                'lon': match.get('lon', ''),
                'frequency': data['frequency'],
                'source': match.get('source', ''),
            })
        else:
            unmapped.append({
                'raw_name': raw_name,
                'frequency': data['frequency'],
                'confidence': 0,
            })
    
    mapped.sort(key=lambda x: -x['frequency'])
    unmapped.sort(key=lambda x: -x['frequency'])
    
    with open(OUTPUT_CSV, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'raw_name', 'matched_name', 'matched_id', 'confidence', 
            'gps_found', 'lat', 'lon', 'frequency', 'source'
        ])
        writer.writeheader()
        writer.writerows(mapped)
    
    print(f"✅ Mapped: {len(mapped)} places")
    print(f"❌ Unmapped: {len(unmapped)} places")
    
    print("\n📊 Top mapped:")
    for p in mapped[:20]:
        print(f"  {p['raw_name']} → {p['matched_name']} ({p['confidence']:.0%})")
    
    print("\n📊 Top unmapped:")
    for p in unmapped[:20]:
        print(f"  {p['raw_name']} ({p['frequency']} lần)")

if __name__ == "__main__":
    main()
