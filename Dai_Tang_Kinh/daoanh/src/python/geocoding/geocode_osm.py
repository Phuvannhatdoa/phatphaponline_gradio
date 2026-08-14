#!/usr/bin/env python3
"""
B: Geocoding Vietnamese places using OSM Nominatim
"""

import requests
import json
import time
import csv
import os

INPUT_CSV = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/processed/mapped_places.csv"
OUTPUT_JSON = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/processed/geocoded_vietnam.json"

def geocode_osm(place_name, country="Vietnam"):
    """Geocode using OSM Nominatim"""
    try:
        # Add Vietnam context
        search_name = f"{place_name}, {country}"
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": search_name,
            "format": "json",
            "limit": 1,
            "addressdetails": 1
        }
        headers = {"User-Agent": "PhatToDaoAnh/1.0"}
        
        r = requests.get(url, params=params, headers=headers, timeout=10)
        data = r.json()
        
        if data:
            return {
                "lat": data[0].get("lat"),
                "lon": data[0].get("lon"),
                "display_name": data[0].get("display_name"),
                "type": data[0].get("type")
            }
    except Exception as e:
        pass
    return None

def main():
    print("🔍 Geocoding Vietnamese places via OSM...")
    
    # Load mapped places
    places = []
    with open(INPUT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('matched_name'):
                places.append({
                    'raw_name': row['raw_name'],
                    'matched_name': row['matched_name'],
                    'lat': row.get('lat', ''),
                    'lon': row.get('lon', ''),
                    'frequency': int(row.get('frequency', 0))
                })
    
    print(f"📥 Loaded {len(places)} places")
    
    # Geocode those without GPS
    geocoded = []
    for i, p in enumerate(places):
        if not p['lat'] or not p['lon']:
            print(f"   Geocoding: {p['matched_name']}")
            result = geocode_osm(p['matched_name'])
            
            if result:
                p['lat'] = result['lat']
                p['lon'] = result['lon']
                print(f"      → {result['lat']},{result['lon']}")
            else:
                print(f"      → Not found")
            
            time.sleep(1)  # Rate limit
        
        geocoded.append(p)
        
        if (i + 1) % 10 == 0:
            print(f"   Processed {i+1}/{len(places)}")
    
    # Save
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(geocoded, f, ensure_ascii=False, indent=2)
    
    # Stats
    with_gps = [p for p in geocoded if p.get('lat') and p.get('lon')]
    print(f"\n✅ Complete!")
    print(f"   Total: {len(geocoded)}")
    print(f"   With GPS: {len(with_gps)}")
    print(f"   Saved to: {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
