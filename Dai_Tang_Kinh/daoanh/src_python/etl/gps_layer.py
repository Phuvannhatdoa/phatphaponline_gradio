#!/usr/bin/env python3
"""
GPS Layer Integration
Link entity names (Chùa) → GPS coordinates from DILA Place Authority
"""

import sqlite3
import json
import re
from pathlib import Path

BASE_DIR = Path("/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh")
DB_FILE = BASE_DIR / "data" / "lineage.db"
DILA_PLACE = BASE_DIR / "data" / "dila_import" / "Authority-Databases" / "authority_place" / "Buddhist_Studies_Place_Authority.xml"
OUTPUT_GPS = BASE_DIR / "data" / "indexed" / "gps_places.json"


def extract_gps_from_xml(xml_file):
    """Parse DILA Place Authority XML to get GPS coordinates"""
    print("\n📂 Parsing DILA Place Authority XML...")
    
    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except Exception as e:
        print(f"   ⚠️ Error: {e}")
        return {}
    
    # Remove namespace
    for elem in root.iter():
        if elem.tag.startswith('{'):
            elem.tag = elem.tag.split('}')[1]
    
    gps_data = {}
    
    listPlace = root.find('.//listPlace')
    if listPlace is None:
        print("   ⚠️ No listPlace found")
        return {}
    
    places = listPlace.findall('place')[:15000]  # Limit for performance
    
    for place in places:
        place_key = place.get('key', '')
        
        geo_lat = None
        geo_long = None
        location = ""
        name_zh = ""
        province = ""
        
        # Get placeName (Chinese)
        for pn in place.findall('placeName'):
            if pn.text:
                name_zh = pn.text
                break
        
        # Get location with geo inside
        for loc in place.findall('location'):
            geo = loc.find('geo')
            if geo is not None and geo.text:
                coords = geo.text.strip().split()
                if len(coords) >= 2:
                    try:
                        geo_long = float(coords[0])
                        geo_lat = float(coords[1])
                    except:
                        pass
            
            # Get place inside location (for matching)
            pl = loc.find('place')
            if pl is not None and pl.text:
                location = pl.text
        
        # Get district/province
        district = place.find('district')
        if district is not None and district.text:
            province = district.text
        
        if geo_lat and geo_long and name_zh:
            gps_data[name_zh] = {
                'lat': geo_lat,
                'lng': geo_long,
                'province': province,
                'location': location,
                'name_zh': name_zh
            }
    
    print(f"   ✅ Found {len(gps_data)} places with GPS")
    return gps_data


def link_entities_to_gps():
    """Link lexicon entities (Chùa) with GPS coordinates"""
    print("\n🔗 Linking entities to GPS...")
    
    gps_data = extract_gps_from_xml(DILA_PLACE)
    
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT term, definition, entity_type
        FROM lexicon
        WHERE entity_type = 'ĐỊA DANH'
        AND (term LIKE '%Chùa%' OR term LIKE '%Tự%' OR term LIKE '%Viện%')
        LIMIT 1000
    """)
    entities = cursor.fetchall()
    
    linked = []
    for term, definition, entity_type in entities:
        term_simple = term.replace('Chùa ', '').replace('Tự ', '').replace('Viện ', '').strip()
        
        matched_gps = None
        for place_key, gps in gps_data.items():
            if place_key in term or term in place_key:
                matched_gps = gps
                break
        
        if not matched_gps:
            for place_key, gps in gps_data.items():
                if gps.get('location') and term_simple.lower() in gps.get('location', '').lower():
                    matched_gps = gps
                    break
        
        if matched_gps:
            linked.append({
                'term': term,
                'entity_type': entity_type,
                'lat': matched_gps['lat'],
                'lng': matched_gps['lng'],
                'province': matched_gps.get('province', ''),
                'place_key': matched_gps.get('place_key', '')
            })
    
    conn.close()
    
    OUTPUT_GPS.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_GPS, 'w', encoding='utf-8') as f:
        json.dump(linked, f, ensure_ascii=False, indent=2)
    
    print(f"   ✅ Linked {len(linked)} entities with GPS")
    return linked


def create_map_data():
    """Create GeoJSON for map visualization"""
    linked = link_entities_to_gps()
    
    features = []
    for item in linked:
        if item.get('lat') and item.get('lng'):
            features.append({
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [item['lng'], item['lat']]
                },
                'properties': {
                    'name': item['term'],
                    'province': item.get('province', ''),
                    'place_key': item.get('place_key', '')
                }
            })
    
    geojson = {
        'type': 'FeatureCollection',
        'features': features
    }
    
    geojson_file = BASE_DIR / "data" / "indexed" / "places.geojson"
    with open(geojson_file, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)
    
    print(f"   ✅ GeoJSON: {len(features)} points")
    return geojson


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 GPS Layer Integration")
    print("=" * 60)
    
    linked = link_entities_to_gps()
    geojson = create_map_data()
    
    print(f"\n📊 GPS Layer Stats:")
    print(f"   Total linked: {len(linked)}")
    print(f"   Output: {OUTPUT_GPS}")
    print(f"   GeoJSON: places.geojson")
    
    print("\n✅ GPS Layer Complete")