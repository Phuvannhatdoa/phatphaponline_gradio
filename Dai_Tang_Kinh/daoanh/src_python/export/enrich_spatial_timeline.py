#!/usr/bin/env python3
"""
Enrich Spatial Timeline - Optimized version với index lookup
"""
import json
import os

DATA_DIR = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data"
OUTPUT_DIR = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/ontology/json"

def load_places():
    """Load places.json - build name index"""
    places_file = os.path.join(DATA_DIR, "places.json")
    with open(places_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    places = data.get('places', [])
    
    # Build index by Chinese name
    name_index = {}
    for p in places:
        cn = p.get('nameChinese', '').strip()
        if cn and p.get('lat'):
            name_index[cn] = {
                'lat': float(p['lat']),
                'lng': float(p['lon']),
                'name': cn
            }
    
    print(f"📍 Loaded {len(places)} places, indexed {len(name_index)} with GPS")
    return name_index

def load_entity_export():
    """Load entity_export.json"""
    export_file = os.path.join(OUTPUT_DIR, "entity_export.json")
    with open(export_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    print("🔄 Building place index...")
    place_index = load_places()
    
    print("📦 Loading entity_export.json...")
    data = load_entity_export()
    entities = data.get('entities', [])
    print(f"   Loaded {len(entities)} entities")
    
    # Enrich
    GPS_count = 0
    for entity in entities:
        if not entity.get('spatial_timeline'):
            continue
        
        timeline = entity['spatial_timeline']
        for event in timeline:
            loc = event.get('location', {})
            place_name = loc.get('name', '').strip()
            
            # Direct lookup
            if place_name in place_index:
                gps = place_index[place_name]
                event['location'] = {
                    "name": gps['name'],
                    "lat": gps['lat'],
                    "lng": gps['lng']
                }
                GPS_count += 1
            else:
                # Try partial match
                for cn, gps in place_index.items():
                    if place_name in cn or cn in place_name:
                        event['location'] = {
                            "name": gps['name'],
                            "lat": gps['lat'],
                            "lng": gps['lng']
                        }
                        GPS_count += 1
                        break
    
    print(f"✅ GPS enriched: {GPS_count} locations")
    
    # Save
    output_file = os.path.join(OUTPUT_DIR, "entity_export_enriched.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Saved to: {output_file}")
    
    # Sample
    for e in entities:
        if e.get('spatial_timeline'):
            tl = e['spatial_timeline'][0]
            loc = tl.get('location', {})
            if loc.get('lat'):
                print(f"\n📋 Sample:")
                print(f"   {e.get('id')}: {e.get('name')}")
                print(f"   → {loc.get('name')}: {loc.get('lat')}, {loc.get('lng')}")
                break

if __name__ == "__main__":
    main()
