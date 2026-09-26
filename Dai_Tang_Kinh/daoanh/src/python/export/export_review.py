#!/usr/bin/env python3
"""
P8: QA Review Export
Xuất places_review.csv để Admin duyệt
"""

import json
import csv

# Paths
PROCESSED_DATA = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/processed"
OUTPUT_CSV = f"{PROCESSED_DATA}/places_review.csv"
OUTPUT_JSON = f"{PROCESSED_DATA}/places_final.json"

def load_all_data():
    """Load all processed data"""
    data = {}
    
    # Load mapped places
    try:
        with open(f"{PROCESSED_DATA}/mapped_places.json", 'r', encoding='utf-8') as f:
            data['mapped'] = json.load(f)
    except:
        data['mapped'] = {'places': []}
    
    # Load enriched places
    try:
        with open(f"{PROCESSED_DATA}/enriched_places.json", 'r', encoding='utf-8') as f:
            data['enriched'] = json.load(f)
    except:
        data['enriched'] = {'places': []}
    
    # Load geocoded places
    try:
        with open(f"{PROCESSED_DATA}/geocoded_places.json", 'r', encoding='utf-8') as f:
            data['geocoded'] = json.load(f)
    except:
        data['geocoded'] = {'places': []}
    
    # Load master places (DILA)
    try:
        with open("/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/places.json", 'r', encoding='utf-8') as f:
            data['master'] = json.load(f)
    except:
        data['master'] = {'places': []}
    
    return data

def merge_all_places(data):
    """Merge all data sources into one review list"""
    places = {}
    
    # Add from geocoded (highest priority)
    for p in data.get('geocoded', {}).get('places', []):
        key = p.get('id', '') or p.get('nameVietnamese', '')
        if key:
            places[key] = {
                'id': p.get('id', ''),
                'nameVietnamese': p.get('nameVietnamese', ''),
                'nameChinese': p.get('nameChinese', ''),
                'lat': p.get('lat', ''),
                'lon': p.get('lon', ''),
                'province': p.get('province', ''),
                'description': p.get('description', ''),
                'source': p.get('source', ''),
                'status': 'geocoded'
            }
    
    # Add from enriched (if not already present)
    for p in data.get('enriched', {}).get('places', []):
        key = p.get('id', '') or p.get('nameVietnamese', '')
        if key and key not in places:
            places[key] = {
                'id': p.get('id', ''),
                'nameVietnamese': p.get('nameVietnamese', ''),
                'nameChinese': p.get('nameChinese', ''),
                'lat': p.get('lat', ''),
                'lon': p.get('lon', ''),
                'province': p.get('province', ''),
                'description': p.get('description', ''),
                'source': p.get('source', ''),
                'status': 'enriched'
            }
    
    # Add from mapped (if not already present)
    for p in data.get('mapped', {}).get('places', []):
        key = p.get('id', '') or p.get('nameVietnamese', '')
        if key and key not in places:
            places[key] = {
                'id': p.get('id', ''),
                'nameVietnamese': p.get('nameVietnamese', ''),
                'nameChinese': p.get('nameChinese', ''),
                'lat': p.get('lat', ''),
                'lon': p.get('lon', ''),
                'province': p.get('province', ''),
                'description': p.get('description', ''),
                'source': p.get('source', ''),
                'status': 'mapped'
            }
    
    # Add from master list (DILA) - for comparison
    for p in data.get('master', {}).get('places', []):
        key = p.get('id', '')
        if key and key not in places:
            places[key] = {
                'id': p.get('id', ''),
                'nameVietnamese': p.get('nameVietnamese', ''),
                'nameChinese': p.get('nameChinese', ''),
                'lat': p.get('lat', ''),
                'lon': p.get('lon', ''),
                'province': p.get('province', ''),
                'description': p.get('description', ''),
                'source': 'DILA',
                'status': 'master'
            }
    
    return places

def export_review_csv(places):
    """Export CSV for Admin review"""
    print(f"💾 Exporting review CSV to {OUTPUT_CSV}...")
    
    with open(OUTPUT_CSV, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'STT', 'ID', 'Tên_Việt', 'Tên_Hán', 'Lat', 'Lon', 
            'Province', 'Source', 'Status', 'Mô_tả', 'Ghi_chú_Admin'
        ])
        
        for i, (key, p) in enumerate(places.items(), 1):
            writer.writerow([
                i,
                p.get('id', ''),
                p.get('nameVietnamese', ''),
                p.get('nameChinese', ''),
                p.get('lat', ''),
                p.get('lon', ''),
                p.get('province', ''),
                p.get('source', ''),
                p.get('status', ''),
                p.get('description', ''),
                ''  # Admin notes
            ])
    
    print(f"✅ Exported {len(places)} places")

def export_final_json(places):
    """Export final JSON for production"""
    print(f"💾 Exporting final JSON to {OUTPUT_JSON}...")
    
    # Only include verified places with GPS
    final = [p for p in places.values() if p.get('lat') and p.get('lon')]
    
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump({'places': final}, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Exported {len(final)} verified places")

def run_qa_review():
    """Main QA review workflow"""
    print("🚀 P8: QA Review Export")
    print("=" * 50)
    
    # Load all data
    data = load_all_data()
    
    # Merge all places
    places = merge_all_places(data)
    print(f"📊 Total places: {len(places)}")
    
    # Export CSV for review
    export_review_csv(places)
    
    # Export final JSON
    export_final_json(places)
    
    # Stats
    with_gps = sum(1 for p in places.values() if p.get('lat'))
    without_gps = sum(1 for p in places.values() if not p.get('lat'))
    
    print(f"\n📊 Statistics:")
    print(f"   Tổng places: {len(places)}")
    print(f"   Có GPS: {with_gps}")
    print(f"   Chưa có GPS: {without_gps}")

if __name__ == "__main__":
    run_qa_review()
