#!/usr/bin/env python3
"""
Import People Data to SQLite
DILA Authority Layer - Priority 1
"""
import sqlite3
import json
import os

DATA_DIR = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data"
DB_PATH = os.path.join(DATA_DIR, "sqlite", "buddhist_db.sqlite")

def get_viet_name(names):
    """Extract Vietnamese name"""
    if not names:
        return None
    for n in names:
        if n.get('lang') in ['vi', 'viet', 'vietnamese']:
            return n.get('value')
    return None

def get_zh_name(names):
    """Extract Chinese name"""
    if not names:
        return None
    for n in names:
        if n.get('lang') in ['zho-Hant', 'zh-Hant', 'han', 'chinese']:
            return n.get('value')
    return None

def get_en_name(names):
    """Extract English name"""
    if not names:
        return None
    for n in names:
        if n.get('lang') in ['en', 'english']:
            return n.get('value')
    return None

def import_people():
    """Import people from persons.json"""
    
    # Load data
    print("📦 Loading persons.json...")
    with open(os.path.join(DATA_DIR, "persons.json"), 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    persons = data.get('persons', [])
    print(f"   Loaded {len(persons)} persons")
    
    # Connect to SQLite
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Import
    imported = 0
    errors = 0
    
    for p in persons:
        try:
            names = p.get('names', [])
            
            # Extract names
            name_zh = get_zh_name(names)
            name_vi = get_viet_name(names)
            name_en = get_en_name(names)
            
            # Parse birth/death years
            birth_year = p.get('birth_year', '')
            death_year = p.get('death_year', '')
            
            # Handle empty strings
            if birth_year and str(birth_year).isdigit():
                birth_year = int(birth_year)
            else:
                birth_year = None
                
            if death_year and str(death_year).isdigit():
                death_year = int(death_year)
            else:
                death_year = None
            
            # Get dila_id from id (starts with A)
            dila_id = p.get('id', '') if p.get('id', '').startswith('A') else None
            
            cursor.execute('''
                INSERT OR REPLACE INTO people (
                    id, name_zh, name_vi, name_en, lineage, dynasty,
                    birth_year, death_year, dila_id, wiki_url,
                    biography, sources, works
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                p.get('id'),
                name_zh,
                name_vi,
                name_en,
                p.get('dharma_lineage'),
                p.get('dynasty'),
                birth_year,
                death_year,
                dila_id,
                p.get('wiki_url'),
                p.get('biography'),
                json.dumps(p.get('sources', []), ensure_ascii=False),
                json.dumps(p.get('works', []), ensure_ascii=False)
            ))
            
            imported += 1
            
            if imported % 5000 == 0:
                print(f"   Progress: {imported}/{len(persons)}")
                
        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"   ⚠️ Error: {p.get('id')}: {e}")
    
    conn.commit()
    
    # Verify
    cursor.execute("SELECT COUNT(*) FROM people")
    count = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"✅ Imported {imported} people")
    print(f"   Total in DB: {count}")
    print(f"   Errors: {errors}")
    
    return imported

def import_places():
    """Import places from places.json"""
    
    print("📍 Loading places.json...")
    with open(os.path.join(DATA_DIR, "places.json"), 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    places = data.get('places', [])
    print(f"   Loaded {len(places)} places")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    imported = 0
    for p in places:
        try:
            lat = float(p['lat']) if p.get('lat') else None
            lng = float(p['lon']) if p.get('lon') else None
            
            cursor.execute('''
                INSERT OR REPLACE INTO places (
                    id, name_zh, name_vi, name_en, lat, lng,
                    country, province, source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                p.get('id'),
                p.get('nameChinese'),
                p.get('nameVietnamese'),
                p.get('nameEnglish'),
                lat, lng,
                p.get('country'),
                p.get('province'),
                p.get('source')
            ))
            imported += 1
            
            if imported % 2000 == 0:
                print(f"   Progress: {imported}/{len(places)}")
                
        except Exception as e:
            if imported < 5:
                print(f"   ⚠️ Error: {p.get('id')}: {e}")
    
    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM places")
    count = cursor.fetchone()[0]
    conn.close()
    
    print(f"✅ Imported {imported} places")
    print(f"   Total in DB: {count}")
    return imported

def import_networks():
    """Import networks from entity_export_enriched.json"""
    
    print("🔗 Loading entity_export_enriched.json...")
    with open(os.path.join(DATA_DIR, "..", "ontology", "json", "entity_export_enriched.json"), 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    entities = data.get('entities', [])
    print(f"   Loaded {len(entities)} entities")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    imported = 0
    sources = ['DILA', 'Marcus_SNA', 'Internal']
    
    for e in entities:
        person_id = e.get('id')
        graph_connections = e.get('graph_connections', [])
        
        for gc in graph_connections:
            try:
                relation = gc.get('relation', '')
                target_id = gc.get('target', '')
                weight = gc.get('weight', 10)
                
                cursor.execute('''
                    INSERT INTO networks (person_id, target_id, relation_type, weight, source)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    person_id,
                    target_id,
                    relation,
                    weight,
                    'DILA'
                ))
                imported += 1
                
            except Exception as e:
                if imported < 5:
                    print(f"   ⚠️ Error: {person_id}: {e}")
    
    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM networks")
    count = cursor.fetchone()[0]
    conn.close()
    
    print(f"✅ Imported {imported} network connections")
    print(f"   Total in DB: {count}")
    return imported

if __name__ == "__main__":
    print("="*50)
    print("Importing DILA Authority Layer")
    print("="*50)
    
    print("\n📌 Step 1: People")
    import_people()
    
    print("\n📌 Step 2: Places")
    import_places()
    
    print("\n📌 Step 3: Networks")
    import_networks()
    
    print("\n" + "="*50)
    print("✅ Authority Layer Complete!")
    print("="*50)