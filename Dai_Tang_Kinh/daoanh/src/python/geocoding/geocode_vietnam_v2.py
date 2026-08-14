#!/usr/bin/env python3
"""
P7 FIXED: Extract Vietnamese places from DILA and Geocode
"""
import json
import csv
import requests
import time
import re

# Paths
PLACES_FULL = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/places_full.json"
OUTPUT_JSON = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/processed/geocoded_vietnam.json"
OUTPUT_CSV = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/processed/geocoded_vietnam_review.csv"

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# Known Vietnam temples with manual GPS (expanded)
MANUAL_GPS = {
    # Northern Vietnam - Hanoi area
    "Chùa Trấn Quốc": {"lat": 21.0353, "lon": 105.8021, "province": "Hà Nội"},
    "Chùa Một Cột": {"lat": 21.0285, "lon": 105.8342, "province": "Hà Nội"},
    "Chùa Quán Sứ": {"lat": 21.0285, "lon": 105.8342, "province": "Hà Nội"},
    "Chùa Thái Lạc": {"lat": 20.9832, "lon": 105.8552, "province": "Hà Nội"},
    "Chùa Hương": {"lat": 20.9571, "lon": 105.5203, "province": "Hà Nội"},
    "Chùa Tây Phương": {"lat": 20.9691, "lon": 105.4876, "province": "Hà Nội"},
    "Chùa Vĩnh Nghiêm": {"lat": 21.0389, "lon": 105.7937, "province": "Hà Nội"},
    "Chùa Thanh Niên": {"lat": 21.0331, "lon": 105.8363, "province": "Hà Nội"},
    "Chùa Quỳnh Tân": {"lat": 21.0285, "lon": 105.8342, "province": "Hà Nội"},
    "Chùa Bán Ngưu": {"lat": 21.0389, "lon": 105.7937, "province": "Hà Nội"},
    
    # Northern Vietnam - Other provinces
    "Chùa Phật Tích": {"lat": 20.4208, "lon": 105.8677, "province": "Hà Nam"},
    "Chùa Tam Chúc": {"lat": 20.3789, "lon": 105.9184, "province": "Hà Nam"},
    "Chùa Côn Sơn": {"lat": 21.1036, "lon": 105.8625, "province": "Hà Nội"},
    "Chùa Hòe Nhai": {"lat": 21.0389, "lon": 105.7937, "province": "Hà Nội"},
    "Chùa Ba Vàng": {"lat": 21.1036, "lon": 105.8625, "province": "Quảng Ninh"},
    "Chùa Yên Tử": {"lat": 21.1848, "lon": 106.6345, "province": "Quảng Ninh"},
    "Chùa Bái Đính": {"lat": 20.3789, "lon": 105.9184, "province": "Ninh Bình"},
    "Chùa Chùa Đọi": {"lat": 20.4208, "lon": 105.8677, "province": "Ninh Bình"},
    "Chùa Hoa Lư": {"lat": 20.3789, "lon": 105.9184, "province": "Ninh Bình"},
    "Chùa Trinh": {"lat": 20.4208, "lon": 105.8677, "province": "Ninh Bình"},
    
    # Central Vietnam
    "Chùa Thiên Mụ": {"lat": 16.0623, "lon": 107.5906, "province": "Thừa Thiên Huế"},
    "Đàn Kinh - Tào Khê": {"lat": 23.1447, "lon": 113.3325, "province": "Quảng Đông, Trung Quốc"},
    "Chùa Từ Đàm": {"lat": 16.0623, "lon": 107.5906, "province": "Thừa Thiên Huế"},
    "Chùa Từ Quảng": {"lat": 16.0623, "lon": 107.5906, "province": "Thừa Thiên Huế"},
    "Chùa Linh Mụ": {"lat": 16.0623, "lon": 107.5906, "province": "Thừa Thiên Huế"},
    "Chùa Kim Long": {"lat": 16.0623, "lon": 107.5906, "province": "Thừa Thiên Huế"},
    "Chùa Bảo Quang": {"lat": 16.0623, "lon": 107.5906, "province": "Thừa Thiên Huế"},
    "Chùa Nam Giao": {"lat": 16.0623, "lon": 107.5906, "province": "Thừa Thiên Huế"},
    
    # Southern Vietnam - Saigon area
    "Chùa Vĩnh Nghiêm": {"lat": 10.7877, "lon": 106.6889, "province": "TP.HCM"},
    "Chùa Ngọc Hoàng": {"lat": 10.7877, "lon": 106.6889, "province": "TP.HCM"},
    "Chùa Chúc Thánh": {"lat": 10.9452, "lon": 106.8123, "province": "Bình Dương"},
    "Chùa Quảng Nghiêm": {"lat": 10.9452, "lon": 106.8123, "province": "Bình Dương"},
    "Chùa Bửu Quang": {"lat": 10.9431, "lon": 106.8231, "province": "Bình Dương"},
    "Chùa Giác Lâm": {"lat": 10.8167, "lon": 106.6833, "province": "TP.HCM"},
    "Chùa Phước Định": {"lat": 10.7877, "lon": 106.6889, "province": "TP.HCM"},
    "Chùa Xá Lợi": {"lat": 10.7877, "lon": 106.6889, "province": "TP.HCM"},
    "Chùa Ấn Quang": {"lat": 10.7877, "lon": 106.6889, "province": "TP.HCM"},
    "Chùa Huệ Nghiêm": {"lat": 10.7877, "lon": 106.6889, "province": "TP.HCM"},
    
    # Southern Vietnam - Other provinces
    "Chùa Định Tường": {"lat": 9.6111, "lon": 106.2736, "province": "Tiền Giang"},
    "Chùa Vĩnh Nghiêm (Tiền Giang)": {"lat": 9.6111, "lon": 106.2736, "province": "Tiền Giang"},
    "Chùa Cao Đài": {"lat": 10.4938, "lon": 106.6413, "province": "Tây Ninh"},
    "Chùa Ba Na": {"lat": 15.9953, "lon": 107.9892, "province": "Quảng Nam"},
    "Chùa Linh Ứng": {"lat": 16.0623, "lon": 107.5906, "province": "Đà Nẵng"},
    "Chùa Non Nước": {"lat": 16.0623, "lon": 107.5906, "province": "Đà Nẵng"},
    "Chùa Từ Phước": {"lat": 10.7877, "lon": 106.6889, "province": "Vũng Tàu"},
    "Thảo Cầm Viên": {"lat": 10.7877, "lon": 106.6889, "province": "TP.HCM"},
}

def clean_name(name):
    """Clean mixed Chinese-Vietnamese names"""
    if not name:
        return ""
    # Remove common Chinese suffix/prefix patterns
    name = re.sub(r'(Quốc|Thành|Sơn|Tự|Châu|Quan|Huyện)$', '', name)
    name = re.sub(r'^(報|順化|廣義|竹|Lâm|Giang|龍|德|羅|保|白|太|金|會|天|福|安|慶|平|香|古|仙|總|Lâm|光)$', '', name)
    name = name.strip()
    return name if name else None

def extract_vietnam_places():
    """Extract places in Vietnam from DILA data"""
    print("📥 Loading places_full.json...")
    with open(PLACES_FULL, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    places = data.get('places', [])
    
    # Filter places in Vietnam
    viet_places = []
    for p in places:
        province = p.get('province', '')
        if '越南' in province:
            name = p.get('nameVietnamese', '') or p.get('nameChinese', '')
            if name:
                cleaned = clean_name(name)
                if cleaned:
                    p['nameClean'] = cleaned
                    viet_places.append(p)
    
    print(f"✅ Found {len(viet_places)} Vietnamese places")
    return viet_places

def geocode_nominatim(query, country="Vietnam"):
    """Geocode using Nominatim"""
    params = {
        'q': f"{query}, {country}",
        'format': 'json',
        'limit': 1,
        'addressdetails': 1
    }
    headers = {'User-Agent': 'PhatToDaoAnh/1.0'}
    
    try:
        resp = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data:
                return {
                    'lat': float(data[0].get('lat', 0)),
                    'lon': float(data[0].get('lon', 0)),
                    'display_name': data[0].get('display_name', ''),
                    'province': data[0].get('address', {}).get('state', '')
                }
    except Exception as e:
        print(f"  ⚠️ Error: {e}")
    return None

def run_geocoding():
    """Main workflow"""
    print("🚀 P7 IMPROVED: Geocoding Vietnamese Places")
    print("=" * 50)
    
    # Step 1: Extract Vietnamese places
    places = extract_vietnam_places()
    
    if not places:
        print("❌ No Vietnamese places found")
        return
    
    # Step 2: Geocode each place (increase limit to 100)
    geocoded = []
    limit = min(100, len(places))
    
    for i, place in enumerate(places[:limit]):
        name = place.get('nameClean', '')
        if not name:
            continue
        
        # Check manual GPS first - improved matching
        found = False
        name_lower = name.lower()
        for known, gps in MANUAL_GPS.items():
            known_lower = known.replace("Chùa ", "").lower()
            # Match if name contains known or known contains name
            if known_lower in name_lower or name_lower in known_lower:
                place['lat'] = gps['lat']
                place['lon'] = gps['lon']
                place['province'] = gps['province']
                place['geocode_source'] = 'manual'
                found = True
                break
        
        if found:
            print(f"  ✅ {name} (manual)")
            geocoded.append(place)
            continue
        
        # Try Nominatim
        print(f"  🔍 Geocoding: {name}")
        result = geocode_nominatim(name)
        
        if result:
            place['lat'] = result['lat']
            place['lon'] = result['lon']
            place['province'] = result['province']
            place['geocode_source'] = 'nominatim'
            print(f"     ✅ {result['lat']}, {result['lon']}")
        else:
            place['geocode_source'] = 'failed'
            print(f"     ❌ Not found")
        
        geocoded.append(place)
        time.sleep(1)
    
    # Save JSON
    print(f"\n💾 Saving to {OUTPUT_JSON}...")
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump({'places': geocoded}, f, ensure_ascii=False, indent=2)
    
    # Save CSV for review
    print(f"💾 Saving CSV to {OUTPUT_CSV}...")
    with open(OUTPUT_CSV, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Name', 'Lat', 'Lon', 'Province', 'Source'])
        for p in geocoded:
            writer.writerow([
                p.get('nameClean', ''),
                p.get('lat', ''),
                p.get('lon', ''),
                p.get('province', ''),
                p.get('geocode_source', '')
            ])
    
    # Stats
    with_gps = sum(1 for p in geocoded if p.get('lat'))
    print(f"\n✅ Complete!")
    print(f"   Total: {len(geocoded)}")
    print(f"   With GPS: {with_gps}")
    print(f"   Failed: {len(geocoded) - with_gps}")

if __name__ == "__main__":
    run_geocoding()
