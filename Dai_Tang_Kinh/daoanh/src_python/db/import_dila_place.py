#!/usr/bin/env python3
"""Import DILA Place - FULL DATA VERSION with all XML fields"""

import sqlite3
import xml.etree.ElementTree as ET
import re

DB_FILE = '/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/lineage.db'
XML_FILE = '/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/dila_import/Authority-Databases/authority_place/Buddhist_Studies_Place_Authority.xml'

NS = '{http://www.tei-c.org/ns/1.0}'
XML_NS_ID = '{http://www.w3.org/XML/1998/namespace}'

def extract_geo(geo_text):
    """Extract lat/long from geo text like '67.868089 36.555275'"""
    if not geo_text:
        return None, None
    parts = geo_text.strip().split()
    if len(parts) >= 2:
        try:
            return float(parts[0]), float(parts[1])
        except:
            return None, None
    return None, None

def get_all_names(place):
    """Extract all placeName elements with their languages"""
    names = {
        'primary': '',
        'zh': '',
        'en': '',
        'san': '',
        'jpn': '',
        'peo': '',
        'other': []
    }
    
    name_els = place.findall(f'{NS}placeName')
    for name_el in name_els:
        lang = name_el.attrib.get(f'{XML_NS_ID}lang', '')
        txt = name_el.text.strip() if name_el.text else ''
        name_type = name_el.attrib.get('type', '')
        
        # Skip empty
        if not txt:
            continue
            
        # Primary name (no type attribute, or first one)
        if not name_type and not names['primary']:
            names['primary'] = txt
        
        # By language
        if 'zho-Hant' in lang or 'Chinese' in lang:
            names['zh'] = txt
        elif 'eng' in lang:
            names['en'] = txt
        elif 'san' in lang:
            names['san'] = txt
        elif 'jpn' in lang:
            names['jpn'] = txt
        elif 'peo' in lang:
            names['peo'] = txt
        else:
            names['other'].append(f"{lang}:{txt}")
    
    return names

def get_location_info(place):
    """Extract location element info"""
    location_el = place.find(f'{NS}location')
    if location_el is None:
        return '', None, None, ''
    
    # Get geo coordinates
    geo_el = location_el.find(f'{NS}geo')
    geo_text = geo_el.text if geo_el is not None and geo_el.text else ''
    geo_long, geo_lat = extract_geo(geo_text)
    
    # Get place reference
    place_ref = location_el.find(f'{NS}place')
    place_key = place_ref.attrib.get('key', '') if place_ref is not None else ''
    place_text = place_ref.text if place_ref is not None and place_ref.text else ''
    
    # Full location XML as text
    location_xml = ET.tostring(location_el, encoding='unicode')
    
    return location_xml, geo_lat, geo_long, place_key

def get_notes(place):
    """Extract all note elements"""
    note_els = place.findall(f'{NS}note')
    note_text = ''
    note_category = ''
    
    for note_el in note_els:
        txt = note_el.text if note_el.text else ''
        note_type = note_el.attrib.get('type', '')
        
        if note_type == 'category':
            note_category = txt
        else:
            note_text += txt + ' '
    
    return note_text.strip(), note_category

def get_listbibl(place):
    """Extract listBibl references"""
    listbibl_el = place.find(f'{NS}listBibl')
    if listbibl_el is None:
        return ''
    
    bibl_els = listbibl_el.findall(f'{NS}bibl')
    bibls = []
    for bibl_el in bibl_els:
        txt = bibl_el.text if bibl_el.text else ''
        if txt:
            bibls.append(txt.strip())
    
    return '; '.join(bibls)

def get_district(place):
    """Extract district info"""
    district_el = place.find(f'{NS}district')
    if district_el is None:
        return ''
    return district_el.text.strip() if district_el.text else ''

def main():
    print(f"Loading: {XML_FILE}")
    tree = ET.parse(XML_FILE)
    root = tree.getroot()
    
    body = root.find(f'{NS}text/{NS}body')
    list_place = body.find(f'{NS}listPlace') if body is not None else None
    places = list_place.findall(f'{NS}place') if list_place is not None else []
    total = len(places)
    print(f"Found {total} places")
    
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA journal_mode=WAL")
    
    # DROP and recreate with FULL schema
    conn.execute("DROP TABLE IF EXISTS places_dila")
    conn.execute("""
        CREATE TABLE places_dila (
            id TEXT PRIMARY KEY,
            name TEXT,
            name_zh TEXT,
            name_en TEXT,
            name_san TEXT,
            name_jpn TEXT,
            name_peo TEXT,
            name_other TEXT,
            location_xml TEXT,
            geo_lat REAL,
            geo_long REAL,
            place_key TEXT,
            district TEXT,
            note TEXT,
            note_category TEXT,
            listbibl TEXT,
            raw_xml TEXT
        )
    """)
    conn.commit()
    
    inserted = 0
    errors = 0
    
    for i, place in enumerate(places):
        try:
            # Get id
            pid = place.attrib.get(f'{XML_NS_ID}id')
            if not pid:
                errors += 1
                continue
            
            # Get all names
            names = get_all_names(place)
            
            # Get location info
            location_xml, geo_lat, geo_long, place_key = get_location_info(place)
            
            # Get district
            district = get_district(place)
            
            # Get notes
            note_text, note_category = get_notes(place)
            
            # Get listBibl
            listbibl = get_listbibl(place)
            
            # Get raw XML (full place element)
            raw_xml = ET.tostring(place, encoding='unicode')
            
            # Insert
            conn.execute("""
                INSERT INTO places_dila 
                (id, name, name_zh, name_en, name_san, name_jpn, name_peo, name_other,
                 location_xml, geo_lat, geo_long, place_key, district, note, note_category, listbibl, raw_xml)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pid,
                names['primary'],
                names['zh'],
                names['en'],
                names['san'],
                names['jpn'],
                names['peo'],
                '; '.join(names['other']),
                location_xml,
                geo_lat,
                geo_long,
                place_key,
                district,
                note_text,
                note_category,
                listbibl,
                raw_xml
            ))
            
            inserted += 1
            
            if (i + 1) % 10000 == 0:
                conn.commit()
                print(f"  {i+1}/{total}... (inserted: {inserted})")
                
        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"Error at {i} (id={pid}): {e}")
            pass
    
    conn.commit()
    
    # Final count
    count = conn.execute("SELECT COUNT(*) FROM places_dila").fetchone()[0]
    print(f"✅ Done! Inserted {count} places into places_dila (errors: {errors})")
    
    # Show sample
    print("\nSample data (first 3 rows):")
    rows = conn.execute("SELECT id, name, name_zh, name_en, district, note_category FROM places_dila LIMIT 3").fetchall()
    for row in rows:
        print(f"  {row[0]}: {row[1]} (zh={row[2]}, en={row[3]}, district={row[4]}, cat={row[5]})")
    
    conn.close()

if __name__ == '__main__':
    main()
