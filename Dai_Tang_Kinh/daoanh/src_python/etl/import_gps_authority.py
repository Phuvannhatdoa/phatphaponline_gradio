#!/usr/bin/env python3
"""
Import GPS from DILA Place Authority - Simple Version
"""

import sqlite3
import xml.etree.ElementTree as ET
from pathlib import Path

BASE_DIR = Path("/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh")
DB_FILE = BASE_DIR / "data" / "lineage.db"
DILA_PLACE = BASE_DIR / "data" / "dila_import" / "Authority-Databases" / "authority_place" / "Buddhist_Studies_Place_Authority.xml"


def import_gps():
    print("\n📂 Parsing DILA Place Authority...")
    
    tree = ET.parse(DILA_PLACE)
    root = tree.getroot()
    for elem in root.iter():
        if elem.tag.startswith('{'):
            elem.tag = elem.tag.split('}')[1]
    
    listPlace = root.find('.//listPlace')
    places = listPlace.findall('place')
    print(f"   Found {len(places)} places")
    
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    cursor.execute("DELETE FROM places")
    conn.commit()
    
    inserted = 0
    has_gps = 0
    
    for idx, p in enumerate(places):
        place_id = p.get('key', f'PL{idx:06d}')
        
        name_zh = ''
        for pn in p.findall('placeName'):
            if pn.text:
                name_zh = pn.text[:100]
                break
        if not name_zh:
            continue
        
        lat, lng, province = None, None, ''
        
        for loc in p.findall('location'):
            geo = loc.find('geo')
            if geo is not None and geo.text:
                coords = geo.text.strip().split()
                if len(coords) >= 2:
                    lng, lat = float(coords[0]), float(coords[1])
                    has_gps += 1
        
        dist = p.find('district')
        if dist is not None and dist.text:
            province = dist.text[:100]
        
        cursor.execute("""
            INSERT INTO places (id, name_zh, gps_lat, gps_long, province)
            VALUES (?, ?, ?, ?, ?)
        """, (place_id, name_zh, lat, lng, province))
        inserted += 1
        
        if (idx + 1) % 10000 == 0:
            print(f"   {idx+1} processed (GPS: {has_gps})...")
    
    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM places")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM places WHERE gps_lat IS NOT NULL")
    with_gps = cursor.fetchone()[0]
    conn.close()
    
    print(f"\n✅ Complete: {total} places ({with_gps} with GPS)")
    return with_gps


if __name__ == "__main__":
    print("=" * 50)
    print("GPS Import")
    print("=" * 50)
    import_gps()