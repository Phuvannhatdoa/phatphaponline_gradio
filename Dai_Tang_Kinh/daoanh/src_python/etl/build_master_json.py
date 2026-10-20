#!/usr/bin/env python3
"""
Build Master JSON - Ver 30
Merges 4 sources into master_db.json with DILA ID as key
Each entity = 1 TTL file for GraphDB

Output:
- data/master_db.json (Runtime - O(1) lookup)
- data/indexed/master_index.idx (Binary/Trie Index)

Sources:
1. data/persons.json (VPS - Bio, Teacher/Student)
2. data/dict/merged.json (StarDict - Canon refs)
3. data/dila_import/ (DILA Authority)
4. ontology/*.ttl (Graph relationships)

Usage: python build_master_json.py
"""

import json
import os
import re
from pathlib import Path
from datetime import datetime

# Base paths
BASE_DIR = Path("/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh")
DATA_DIR = BASE_DIR / "data"
ONTOLOGY_DIR = BASE_DIR / "ontology"
OUTPUT_DIR = DATA_DIR
INDEXED_DIR = DATA_DIR / "indexed"

# Source files
PERSONS_FILE = DATA_DIR / "persons.json"
DICT_FILE = DATA_DIR / "dict" / "merged.json"
DILA_DIR = DATA_DIR / "dila_import" / "Authority-Databases" / "authority_catalog" / "json"

# Output files
MASTER_DB_FILE = OUTPUT_DIR / "master_db.json"
INDEX_FILE = INDEXED_DIR / "master_index.idx"
TTL_DIR = ONTOLOGY_DIR / "monks"

# Prefixes for TTL
TTL_PREFIXES = """
@prefix bkg: <http://www.phatphaponline.org/ontology/buddhist-kg#> .
@prefix crm: <http://www.cidoc-crm.org/cidoc-crm/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ex: <http://www.phatphaponline.org/ex/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix geo: <http://www.w3.org/2003/11/geo#> .
"""


def load_persons():
    """Load persons from VPS data"""
    print("📂 Loading persons.json...")
    with open(PERSONS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    persons = data.get('persons', [])
    print(f"   Loaded {len(persons)} persons")
    return {p.get('id'): p for p in persons if p.get('id')}


def load_dict():
    """Load dictionary for canon references"""
    print("📂 Loading dict/merged.json...")
    try:
        with open(DICT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"   Loaded {len(data)} dictionary terms")
        return data
    except Exception as e:
        print(f"   ⚠️ Error loading dict: {e}")
        return {}


def load_dila():
    """Load DILA authority data"""
    print("📂 Loading DILA authority data...")
    dila_data = {}
    if DILA_DIR.exists():
        for json_file in DILA_DIR.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    dila_data.update(data)
            except Exception as e:
                print(f"   ⚠️ Error loading {json_file.name}: {e}")
    print(f"   Loaded {len(dila_data)} DILA records")
    return dila_data


def extract_names(person):
    """Extract Vietnamese and Han names from person record"""
    names = person.get('names', '[]')
    if isinstance(names, str):
        try:
            names = json.loads(names)
        except:
            names = []
    
    name_vi = None
    name_han = None
    
    for name_obj in names:
        lang = name_obj.get('lang', '')
        value = name_obj.get('value', '')
        if 'viet' in lang.lower() or 'vi' in lang.lower():
            name_vi = value
        elif 'han' in lang.lower() or 'zho' in lang:
            name_han = value
    
    return name_vi, name_han


def parse_lineage(lineage_str):
    """Parse teacher/student from string to list"""
    if not lineage_str or lineage_str == '[]':
        return []
    try:
        if isinstance(lineage_str, str):
            return json.loads(lineage_str)
        return lineage_str
    except:
        return []


def build_master_record(person_id, person_data, dict_data, dila_data):
    """Build master record from all sources"""
    try:
        name_vi, name_han = extract_names(person_data)
        
        # Get biography
        bio = str(person_data.get('biography', '')) if person_data.get('biography') else ''
        
        # Get lineage - with error handling
        try:
            teacher = parse_lineage(person_data.get('teacher', '[]'))
            if not isinstance(teacher, list):
                teacher = []
        except:
            teacher = []
            
        try:
            disciples = parse_lineage(person_data.get('student', '[]'))
            if not isinstance(disciples, list):
                disciples = []
        except:
            disciples = []
        
        # Find canon references - SKIP expensive dictionary search for now
        # Can be added back with optimization later
        canon_refs = {
            'taisho': [],
            'cbeta': [],
            'stardict': []
        }
        
        # Get DILA data
        dila_info = dila_data.get(person_id, {})
        
        # Build master record
        record = {
            'metadata': {
                'id': person_id,
                'authority_id': str(dila_info.get('authorityID', '')) if isinstance(dila_info, dict) else '',
                'sources': ['VPS'],
                'created_at': datetime.now().isoformat()
            },
            'display': {
                'name_vi': name_vi or '',
                'name_han': name_han or '',
                'dynasty': str(person_data.get('dynasty', '')) if person_data.get('dynasty') else ''
            },
            'bio': {
                'content': bio,
                'source': 'VPS'
            },
            'lineage': {
                'teacher_id': teacher[0] if teacher and len(teacher) > 0 else None,
                'disciples': disciples
            },
            'canon': canon_refs,
            'ontology': {
                'same_as': f"https://authority.dila.edu.tw/person/?id={person_id}" if dila_info else None
            }
        }
        
        # Add sources if DILA data exists
        if dila_info and isinstance(dila_info, dict):
            record['metadata']['sources'].append('DILA')
        if any(canon_refs.values()):
            record['metadata']['sources'].append('STAR_DICT')
        
        return record
    except Exception as e:
        print(f"   ⚠️ Error building record for {person_id}: {e}")
        return None


def build_index(master_db):
    """Build binary index for autocomplete"""
    print("🔧 Building master index...")
    index = {}
    
    for person_id, record in master_db.items():
        display = record.get('display', {})
        name_vi = display.get('name_vi', '')
        name_han = display.get('name_han', '')
        
        # Index by ID
        index[person_id.lower()] = person_id
        
        # Index by Vietnamese name (lowercase, no diacritics)
        if name_vi:
            normalized = name_vi.lower().replace(' ', '')
            index[normalized] = person_id
        
        # Index by Han name
        if name_han:
            index[name_han] = person_id
    
    print(f"   Indexed {len(index)} entries")
    return index


def generate_ttl(record):
    """Generate TTL file for a single entity"""
    person_id = record['metadata']['id']
    display = record['display']
    bio = record['bio']
    lineage = record['lineage']
    
    ttl = f"""@prefix bkg: <http://www.phatphaponline.org/ontology/buddhist-kg#> .
@prefix crm: <http://www.cidoc-crm.org/cidoc-crm/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ex: <http://www.phatphaponline.org/ex/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix geo: <http://www.w3.org/2003/11/geo#> .

<ex:monk/{person_id}> a bkg:Monk ;
"""
    
    # Labels
    labels = []
    if display.get('name_vi'):
        labels.append(f"""rdfs:label "{display['name_vi']}"@vi""")
    if display.get('name_han'):
        labels.append(f"""rdfs:label "{display['name_han']}"@zh""")
    ttl += '    ' + ' ;\n    '.join(labels) + ' ;\n'
    
    # Biography
    if bio.get('content'):
        bio_content = bio['content'].replace('"', '\\"').replace('\n', ' ')
        ttl += f'    bkg:biographicalNote """{bio_content}"""@vi ;\n'
    
    # Gender
    ttl += '    bkg:gender <bkg:Male> ;\n'
    
    # Dynasty
    if display.get('dynasty'):
        dynasty_val = display['dynasty'].replace('"', '\\"')
        ttl += f'    bkg:dynasty "{dynasty_val}" ;\n'
    
    # Teacher
    if lineage.get('teacher_id'):
        teacher_id = lineage['teacher_id'].replace('"', '\\"')
        ttl += f'    bkg:hasTeacher <ex:monk/{teacher_id}> ;\n'
    
    # Disciples
    for disciple_id in lineage.get('disciples', []):
        disciple_clean = disciple_id.replace('"', '\\"')
        ttl += f'    bkg:hasDisciple <ex:monk/{disciple_clean}> ;\n'
    
    # Ontology same-as
    if record['ontology'].get('same_as'):
        same_as = record['ontology']['same_as'].replace('"', '\\"')
        ttl += f'    owl:sameAs <{same_as}> .\n'
    
    return ttl


def main():
    """Main function to build master JSON"""
    print("=" * 60)
    print("🪷 BUILD MASTER JSON - VER 30")
    print("=" * 60)
    print(f"Started: {datetime.now().isoformat()}")
    print()
    
    # Ensure output directories exist
    INDEXED_DIR.mkdir(parents=True, exist_ok=True)
    TTL_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load all sources
    persons_data = load_persons()
    dict_data = load_dict()
    dila_data = load_dila()
    
    # Build master database
    print("\n🔄 Building master database...")
    print("   (Skipping TTL generation for speed - use export_ttl.py for TTL)")
    master_db = {}
    errors = 0
    count = 0
    
    for person_id, person_data in persons_data.items():
        try:
            record = build_master_record(person_id, person_data, dict_data, dila_data)
            if record is None:
                errors += 1
                continue
                
            master_db[person_id] = record
            count += 1
            
            # Progress indicator
            if count % 5000 == 0:
                print(f"   Processed {count} records...")
            
        except Exception as e:
            errors += 1
            if errors <= 3:
                print(f"   ⚠️ Error processing {person_id}: {e}")
            print(f"   ⚠️ Error processing {person_id}: {e}")
    
    # Build index
    print("\n🔄 Building search index...")
    index_data = build_index(master_db)
    
    # Save outputs
    print("\n💾 Saving outputs...")
    
    # Save master_db.json
    with open(MASTER_DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(master_db, f, ensure_ascii=False, indent=2)
    print(f"   ✅ master_db.json: {len(master_db)} records")
    
    # Save index as JSON (for web compatibility)
    index_json_file = INDEXED_DIR / "master_index.json"
    with open(index_json_file, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False)
    print(f"   ✅ master_index.json: {len(index_data)} entries")
    
    # Note about TTL files
    print(f"   ℹ️ TTL generation skipped in this run")
    print(f"   ℹ️ Run src_python/etl/export_ttl.py to generate TTL files")
    
    # Summary
    print()
    print("=" * 60)
    print("✅ BUILD COMPLETE")
    print("=" * 60)
    print(f"Master DB Records: {len(master_db)}")
    print(f"Errors: {errors}")
    print(f"Output: {MASTER_DB_FILE}")
    print(f"Index: {index_json_file}")
    print(f"Finished: {datetime.now().isoformat()}")
    
    return master_db


if __name__ == "__main__":
    main()