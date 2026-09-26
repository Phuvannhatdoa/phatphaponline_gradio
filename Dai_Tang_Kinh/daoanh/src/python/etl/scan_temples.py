#!/usr/bin/env python3
"""
D2: Simple dictionary temple extractor
Extract temple/monastery names from dictionary text using keyword search
"""

import os
import re
import json

INPUT_DIR = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/raw/dictionaries"
OUTPUT_JSON = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/processed/dictionary_places.json"

# Temple keywords to search for
TEMPLE_KEYWORDS = [
    'chùa', 'tự', 'tịnh xá', 'thiền viện', 'viện', 'am', 'trai', 'quán', 
    'cốc', 'bảo tháp', 'tháp', 'niệm phật', 'đạo tràng', 'lam',
    'đồi', 'núi', 'hồ', 'sông', 'chùa', 'cảnh'
]

# Province patterns
PROVINCE_MAP = {
    'hồ chí minh': ('HCM', 'Hồ Chí Minh'),
    'tp.hcm': ('HCM', 'Hồ Chí Minh'),
    'sài gòn': ('HCM', 'Hồ Chí Minh'),
    'hà nội': ('HAN', 'Hà Nội'),
    'hà nội': ('HAN', 'Hà Nội'),
    'đà nẵng': ('DNG', 'Đà Nẵng'),
    'huế': ('HUE', 'Thừa Thiên Huế'),
    'thừa thiên': ('HUE', 'Thừa Thiên Huế'),
    'khánh hòa': ('KHO', 'Khánh Hòa'),
    'nha trang': ('KHO', 'Khánh Hòa'),
    'an giang': ('ANI', 'An Giang'),
    'bến tre': ('BTE', 'Bến Tre'),
    'tiền giang': ('TYN', 'Tiền Giang'),
    'vĩnh long': ('VLG', 'Vĩnh Long'),
    'cần thơ': ('CTG', 'Cần Thơ'),
    'hải phòng': ('HPG', 'Hải Phòng'),
    'quảng ninh': ('QNI', 'Quảng Ninh'),
    'quảng nam': ('QNA', 'Quảng Nam'),
    'quảng ngãi': ('QNG', 'Quảng Ngãi'),
    'bình định': ('BDI', 'Bình Định'),
    'phú yên': ('PYE', 'Phú Yên'),
    'khánh hòa': ('KHO', 'Khánh Hòa'),
    'bình thuận': ('BTH', 'Bình Thuận'),
    'đồng nai': ('DNG', 'Đồng Nai'),
    'bình dương': ('BDU', 'Bình Dương'),
    'tây ninh': ('TNI', 'Tây Ninh'),
    'lâm đồng': ('LDI', 'Lâm Đồng'),
    'đà lạt': ('LDI', 'Lâm Đồng'),
    'kon tum': ('KTM', 'Kon Tum'),
    'gia lai': ('GLA', 'Gia Lai'),
    'đắk lắk': ('DLK', 'Đắk Lắk'),
    'hà giang': ('HAG', 'Hà Giang'),
    'cao bằng': ('CAB', 'Cao Bằng'),
    'lai châu': ('LCH', 'Lai Chau'),
    'điện biên': ('DBI', 'Điện Biên'),
    'lào cai': ('LCA', 'Lào Cai'),
    'yên bái': ('YBA', 'Yên Bái'),
    'tuyên quang': ('TQU', 'Tuyên Quang'),
    'phú thọ': ('PTH', 'Phú Thọ'),
    'thái nguyên': ('TNG', 'Thái Nguyên'),
    'quảng ninh': ('QNI', 'Quảng Ninh'),
    'nam định': ('NDI', 'Nam Định'),
    'ninh bình': ('NBI', 'Ninh Bình'),
    'thanh hóa': ('THO', 'Thanh Hóa'),
    'nghệ an': ('NAN', 'Nghệ An'),
    'hà tĩnh': ('HTI', 'Hà Tĩnh'),
    'quảng bình': ('QBI', 'Quảng Bình'),
    'quảng trị': ('QTR', 'Quảng Trị'),
    'thừa thiên': ('HUE', 'Thừa Thiên Huế'),
}

def find_province(text):
    """Find province in text"""
    text_lower = text.lower()
    for key, (code, name) in PROVINCE_MAP.items():
        if key in text_lower:
            return code, name
    return None, None

def scan_texts():
    """Scan all dictionary files for temple names"""
    print("🚀 D2: Dictionary Temple Extraction")
    print("=" * 45)
    
    txt_files = [f for f in os.listdir(INPUT_DIR) if f.endswith('.txt')]
    print(f"📂 {len(txt_files)} files")
    
    temples = []
    
    for fname in txt_files:
        fpath = os.path.join(INPUT_DIR, fname)
        content = open(fpath, 'r', encoding='utf-8', errors='ignore').read()
        
        # Split into sentences/entries
        lines = re.split(r'[.\n]+', content)
        
        for line in lines:
            line = line.strip()
            if len(line) < 20:
                continue
            
            # Check if contains temple keywords
            has_temple = any(kw in line.lower() for kw in TEMPLE_KEYWORDS)
            if not has_temple:
                continue
            
            # Try to find temple name pattern (starts with Chùa/Tự/etc)
            name_match = re.search(r'([Cc]hùa|[Tt]ự|[Tt]ịnh\s+[Xx]á|[Tt]hiền\s+[Vv]iện|[Vv]iện|[Aa]m|[Tt]rai|[Qq]uán)\s+([^\.,\;\:]+)', line)
            if name_match:
                name = name_match.group(0).strip()
                name = re.sub(r'^\s+', '', name)
                
                # Find province
                prov_code, prov_name = find_province(line)
                
                temples.append({
                    'nameVi': name[:100],
                    'description': line[:500],
                    'province': prov_code,
                    'provinceName': prov_name,
                    'source': fname
                })
    
    # Dedupe
    print(f"\n🔄 Processing {len(temples)} items...")
    seen = {}
    for t in temples:
        key = t['nameVi']
        if key not in seen:
            seen[key] = t
        else:
            if len(t['description']) > len(seen[key]['description']):
                seen[key] = t
    
    result = list(seen.values())
    print(f"✅ Unique: {len(result)}")
    
    # Save
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump({'places': result, 'count': len(result)}, f, ensure_ascii=False, indent=2)
    print(f"💾 Saved to {OUTPUT_JSON}")
    
    return result

if __name__ == "__main__":
    scan_texts()