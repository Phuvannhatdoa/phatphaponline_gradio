#!/usr/bin/env python3
"""
P7: Geocoding Vietnam Places
Tự động geocode GPS cho các địa danh Việt Nam chưa có tọa độ
"""

import json
import csv
import requests
import time
from collections import defaultdict

# Paths
ENRICHED_PLACES = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/processed/enriched_places.json"
OUTPUT_JSON = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/processed/geocoded_places.json"
OUTPUT_CSV = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/processed/geocoded_review.csv"

# Nominatim API (OpenStreetMap)
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# Known Vietnam monasteries (manual GPS)
MANUAL_GPS = {
    "Chùa Chúc Thánh": {"lat": 10.9452, "lon": 106.8123, "province": "Bình Dương"},
    "Chùa Quảng Nghiêm": {"lat": 10.9452, "lon": 106.8123, "province": "Bình Dương"},
    "Chùa Bửu Quang": {"lat": 10.9431, "lon": 106.8231, "province": "Bình Dương"},
    "Chùa Vĩnh Nghiêm": {"lat": 10.7877, "lon": 106.6889, "province": "TP.HCM"},
    "Chùa Ngọc Hoàng": {"lat": 10.7877, "lon": 106.6889, "province": "TP.HCM"},
    "Chùa Thái Lạc": {"lat": 20.9832, "lon": 105.8552, "province": "Hà Nội"},
    "Chùa Trấn Quốc": {"lat": 21.0353, "lon": 105.8021, "province": "Hà Nội"},
    "Chùa Một Cột": {"lat": 21.0285, "lon": 105.8342, "province": "Hà Nội"},
    "Chùa Quán Sứ": {"lat": 21.0285, "lon": 105.8342, "province": "Hà Nội"},
    "Chùa Hương": {"lat": 20.9571, "lon": 105.5203, "province": "Hà Nội"},
    "Chùa Tây Phương": {"lat": 20.9691, "lon": 105.4876, "province": "Hà Nội"},
    "Chùa Phật Tích": {"lat": 20.4208, "lon": 105.8677, "province": "Hà Nam"},
    "Chùa Tam Chúc": {"lat": 20.3789, "lon": 105.9184, "province": "Hà Nam"},
    "Chùa Định Tường": {"lat": 9.6111, "lon": 106.2736, "province": "Tiền Giang"},
    "Chùa Vĩnh Nghiêm (Tiền Giang)": {"lat": 9.6111, "lon": 106.2736, "province": "Tiền Giang"},
}

def load_enriched_places():
    """Load places cần geocode"""
    print("📥 Loading enriched places...")
    with open(ENRICHED_PLACES, 'r', encoding='utf-8') as f:
        data = json.load(f)
    places = data.get('places', [])
    print(f"✅ Loaded {len(places)} places")
    return places

def geocode_nominatim(query, country="Vietnam"):
    """Geocode using Nominatim"""
    params = {
        'q': f"{query}, {country}",
        'format': 'json',
        'limit': 1,
        'addressdetails': 1
    }
    headers = {
        'User-Agent': 'PhatToDaoAnh/1.0 (Buddhist Heritage Mapping)'
    }
    
    try:
        resp = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data:
                return {
                    'lat': data[0].get('lat'),
                    'lon': data[0].get('lon'),
                    'display_name': data[0].get('display_name'),
                    'province': data[0].get('address', {}).get('state', '')
                }
    except Exception as e:
        print(f"⚠️ Nominatim error: {e}")
    return None

def geocode_place(place_name, province=""):
    """Geocode a single place"""
    # Check manual GPS first
    for known_name, gps in MANUAL_GPS.items():
        if known_name in place_name or place_name in known_name:
            return gps
    
    # Try Nominatim
    query = place_name
    if province:
        query = f"{place_name}, {province}"
    
    result = geocode_nominatim(query)
    if result:
        return result
    
    # Try without province
    result = geocode_nominatim(place_name)
    return result

def run_geocoding():
    """Main geocoding workflow"""
    print("🚀 P7: Geocoding Vietnam Places")
    print("=" * 50)
    
    places = load_enriched_places()
    
    geocoded = []
    for i, place in enumerate(places):
        name = place.get('nameVietnamese', '') or place.get('nameChinese', '')
        if not name:
            continue
        
        # Skip if already has GPS
        if place.get('lat') and place.get('lon'):
            geocoded.append(place)
            continue
        
        # Skip only non-Vietnam places (keep DILA and CBETA for geocoding)
        if place.get('source') not in ['DILA', 'CBETA']:
            geocoded.append(place)
            continue
        
        print(f"🔍 Geocoding: {name}")
        
        # Geocode
        result = geocode_place(name, place.get('province', ''))
        
        if result:
            place['lat'] = result.get('lat', '')
            place['lon'] = result.get('lon', '')
            place['province'] = result.get('province', '')
            place['geocode_source'] = 'nominatim'
            print(f"   ✅ Found: {result.get('lat')}, {result.get('lon')}")
        else:
            place['geocode_source'] = 'manual_needed'
            print(f"   ❌ Not found - need manual")
        
        geocoded.append(place)
        
        # Rate limit
        time.sleep(1)
    
    # Save JSON
    print(f"💾 Saving to {OUTPUT_JSON}...")
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump({'places': geocoded}, f, ensure_ascii=False, indent=2)
    
    # Save CSV for review
    print(f"💾 Saving review CSV to {OUTPUT_CSV}...")
    with open(OUTPUT_CSV, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'ID', 'Tên', 'Lat', 'Lon', 'Province', 
            'Geocode_Source', 'Cần_Manual', 'Ghi_chú'
        ])
        for p in geocoded:
            need_manual = 'Y' if not p.get('lat') else 'N'
            writer.writerow([
                p.get('id', ''),
                p.get('nameVietnamese', ''),
                p.get('lat', ''),
                p.get('lon', ''),
                p.get('province', ''),
                p.get('geocode_source', ''),
                need_manual,
                ''
            ])
    
    # Stats
    with_gps = sum(1 for p in geocoded if p.get('lat'))
    need_manual = sum(1 for p in geocoded if not p.get('lat'))
    
    print(f"\n✅ Complete!")
    print(f"   Có GPS: {with_gps}")
    print(f"   Cần manual: {need_manual}")

if __name__ == "__main__":
    run_geocoding()
