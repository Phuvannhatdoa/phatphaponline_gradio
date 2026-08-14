#!/usr/bin/env python3
"""
D3-D5: GPS Enrichment + ID Generation + Export temples_master.json
"""

import json
import os
import re
import requests

INPUT_JSON = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/processed/dictionary_places.json"
OUTPUT_JSON = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/processed/temples_master.json"
AMBIGUOUS_CSV = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/processed/ambiguous_report.csv"

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# Province codes (alphabetical order)
PROVINCES = [
    ('ANI', 'An Giang'), ('BDI', 'Bình Định'), ('BDU', 'Bình Dương'), ('BTE', 'Bến Tre'),
    ('BTH', 'Bình Thuận'), ('CAB', 'Cao Bằng'), ('CTG', 'Cần Thơ'), ('DNG', 'Đà Nẵng'),
    ('DNI', 'Đồng Nai'), ('DBI', 'Điện Biên'), ('DLK', 'Đắk Lắk'), ('GLA', 'Gia Lai'),
    ('HAN', 'Hà Nội'), ('HAG', 'Hà Giang'), ('HCM', 'TP.HCM'), ('HPG', 'Hải Phòng'),
    ('HTI', 'Hà Tĩnh'), ('HUE', 'Huế'), ('KHO', 'Khánh Hòa'), ('KTM', 'Kon Tum'),
    ('LCA', 'Lào Cai'), ('LCH', 'Lai Chau'), ('LDI', 'Lâm Đồng'), ('LVI', 'Long An'),
    ('MTN', 'Miền Tây'), ('NAN', 'Nghệ An'), ('NBI', 'Ninh Bình'), ('NDI', 'Nam Định'),
    ('PTH', 'Phú Thọ'), ('PYE', 'Phú Yên'), ('QBI', 'Quảng Bình'), ('QNA', 'Quảng Nam'),
    ('QNG', 'Quảng Ngãi'), ('QNI', 'Quảng Ninh'), ('QTR', 'Quảng Trị'), ('TBI', 'Thái Bình'),
    ('TCG', 'Thái Nguyên'), ('THO', 'Thanh Hóa'), ('TNI', 'Tây Ninh'), ('TQU', 'Tuyên Quang'),
    ('TYN', 'Tiền Giang'), ('VLG', 'Vĩnh Long'), ('YBA', 'Yên Bái'),
]

def normalize_name(name):
    """Remove diacritics, lowercase, replace spaces with underscore"""
    if not name:
        return "unknown"
    name = name.strip().lower()
    # Simple diacritics removal
    replacements = {
        'à':'a','á':'a','ả':'a','ã':'a','ạ':'a',
        'ă':'a','ằ':'a','ắ':'a','ẳ':'a','ẵ':'a','ặ':'a',
        'â':'a','ầ':'a','ấ':'a','ẩ':'a','ẫ':'a','ậ':'a',
        'è':'e','é':'e','ẻ':'e','ẽ':'e','ẹ':'e',
        'ê':'e','ề':'e','ế':'e','ể':'e','ễ':'e','ệ':'e',
        'ì':'i','í':'i','ỉ':'i','ĩ':'i','ị':'i',
        'ò':'o','ó':'o','ỏ':'o','õ':'o','ọ':'o',
        'ô':'o','ồ':'o','ố':'o','ổ':'o','ỗ':'o','ộ':'o',
        'ơ':'o','ờ':'o','ớ':'o','ở':'o','ỡ':'o','ợ':'o',
        'ù':'u','ú':'u','ủ':'u','ũ':'u','ụ':'u',
        'ư':'u','ừ':'u','ứ':'u','ử':'u','ữ':'u','ự':'u',
        'ỳ':'y','ý':'y','ỷ':'y','ỹ':'y','ỵ':'y',
        'đ':'d',
    }
    result = ""
    for c in name:
        result += replacements.get(c, c)
    # Replace non-alphanumeric with underscore
    result = re.sub(r'[^a-z0-9]+', '_', result)
    result = result.strip('_')
    return result[:50] if result else "unknown"

def get_temple_type(name):
    """Determine temple type from name"""
    name_lower = name.lower()
    if 'chùa' in name_lower: return 'Chua'
    if 'tự' in name_lower: return 'Tu'
    if 'tịnh xá' in name_lower: return 'TinhXa'
    if 'thiền viện' in name_lower: return 'ThienVien'
    if 'viện' in name_lower: return 'Vien'
    if 'am' in name_lower: return 'Am'
    if 'trai' in name_lower: return 'Trai'
    if 'quán' in name_lower: return 'Quan'
    if 'cốc' in name_lower: return 'Coc'
    if 'tháp' in name_lower: return 'Thap'
    return 'Chua'

def geocode_nominatim(query, country="Vietnam"):
    """Get GPS from Nominatim"""
    params = {'q': f"{query}, {country}", 'format': 'json', 'limit': 1}
    headers = {'User-Agent': 'PhatToDaoAnh/1.0'}
    try:
        resp = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data:
                return float(data[0]['lat']), float(data[0]['lon'])
    except Exception as e:
        pass
    return None, None

def process():
    print("🚀 D3-D5: Enrichment + Export")
    print("=" * 40)
    
    # Load places
    with open(INPUT_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
    places = data['places']
    print(f"📥 Loaded {len(places)} places")
    
    # Group by province
    by_province = {}
    for p in places:
        prov = p.get('province') or 'UNKNOWN'
        if prov not in by_province:
            by_province[prov] = []
        by_province[prov].append(p)
    
    print(f"📊 {len(by_province)} provinces")
    
    # Generate IDs and enrich GPS
    results = []
    ambiguous = []
    seq_by_prov = {p[0]: 1 for p in PROVINCES}
    
    for prov_code, prov_name in PROVINCES:
        if prov_code not in by_province:
            continue
        
        prov_places = by_province[prov_code]
        seq = 1
        
        for p in prov_places[:100]:  # Limit per province for now
            name_vi = p['nameVi'][:80]
            temple_type = get_temple_type(name_vi)
            name_norm = normalize_name(name_vi)
            
            # Generate ID: pth:VN_HCM_001_Chua_Duoc_Su
            pth_id = f"pth:VN_{prov_code}_{seq:03d}_{temple_type}_{name_norm}"
            
            # Try geocoding
            lat, lon = None, None
            # Simple: use province center as fallback
            if not lat:
                # Mark as ambiguous if missing
                if len(p.get('description', '')) < 30:
                    ambiguous.append([pth_id, name_vi, prov_name, "Missing location"])
            
            results.append({
                'id': pth_id,
                'nameVi': name_vi,
                'nameAlt': name_vi.replace('chùa ', '').replace('Chùa ', ''),
                'type': temple_type,
                'province': prov_code,
                'provinceName': prov_name,
                'lat': lat or "",
                'lon': lon or "",
                'description': p.get('description', '')[:300],
                'sources': [p.get('source', '')],
                'status': 'pending' if not lat else 'verified',
                'sameAs': []
            })
            
            seq += 1
    
    print(f"✅ Generated {len(results)} temples")
    print(f"⚠️ Ambiguous: {len(ambiguous)}")
    
    # Save main JSON
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump({
            'temples': results,
            'count': len(results),
            'metadata': {
                'source': 'StarDict Dictionaries',
                'id_format': 'pth:VN_{PROVINCE}_{SEQ:03d}_{TYPE}_{NAME}'
            }
        }, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Saved to {OUTPUT_JSON}")
    
    # Save ambiguous CSV
    import csv
    with open(AMBIGUOUS_CSV, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Name', 'Province', 'Issue'])
        for a in ambiguous[:500]:
            writer.writerow(a)
    
    print(f"💾 Saved ambiguous to {AMBIGUOUS_CSV}")
    
    return results

if __name__ == "__main__":
    process()