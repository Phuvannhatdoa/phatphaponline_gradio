#!/usr/bin/env python3
"""
ETL Script: Import DILA Person Authority XML to JSON
Zero-RAM: Uses iterparse (SAX-like) for streaming large XML files

Input: data/dila_import/Authority-Databases/authority_person/Buddhist_Studies_Person_Authority.xml
Output: data/persons.json
"""

import json
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Generator, Dict, List, Any
import sys

# Paths
BASE_DIR = Path("/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh")
INPUT_XML = BASE_DIR / "data/dila_import/Authority-Databases/authority_person/Buddhist_Studies_Person_Authority.xml"
OUTPUT_JSON = BASE_DIR / "data/persons.json"

# TEI namespace
NS = {'tei': 'http://tei-c.org/ns/1.0'}

def parse_person_authority_xml_streaming(xml_path: str, batch_size: int = 500) -> Generator[Dict, None, None]:
    """
    Parse DILA Person Authority XML using iterparse (Zero-RAM approach)
    """
    context = ET.iterparse(xml_path, events=('end',))
    
    for event, elem in context:
        tag = elem.tag
        if '}' in tag:
            local_name = tag.split('}')[1]
        else:
            local_name = tag
        
        if local_name == 'person':
            person_data = extract_person_data(elem)
            yield person_data
            elem.clear()
    
    if context.root is not None:
        context.root.clear()

def extract_person_data(person_elem: ET.Element) -> Dict:
    """Extract person data from TEI person element"""
    data = {
        'id': '',
        'names': [],
        'sex': '',
        'dynasty': '',
        'is_monk': False,
        'birth_year': '',
        'death_year': '',
        'birth_place': '',
        'death_place': '',
        'place_of_origin': '',
        'active_at': [],
        'occupation': '',
        'biography': '',
        'teacher': [],
        'student': [],
        'sources': [],
        'works': [],
        'dila_url': ''
    }
    
    # Define the TEI namespace
    tei_ns = 'http://tei-c.org/ns/1.0'
    ns_map = {'tei': tei_ns}
    
    # Helper function to find with or without namespace
    def find_all(parent, tag):
        # Try without namespace
        results = parent.findall(tag)
        if not results:
            # Try with namespace
            results = parent.findall(f'{{{tei_ns}}}{tag}')
        return results
    
    def find_one(parent, tag):
        result = parent.find(tag)
        if result is None:
            result = parent.find(f'{{{tei_ns}}}{tag}')
        return result
    
    # Get person ID
    data['id'] = person_elem.get('{http://www.w3.org/XML/1998/namespace}id', '')
    if not data['id']:
        data['id'] = person_elem.get('id', '')
    
    if not data['id']:
        return data
    
    # Build DILA URL
    data['dila_url'] = f"http://authority.dila.edu.tw/person/{data['id']}"
    
    # Extract names (persName elements)
    for pers_name in find_all(person_elem, 'persName'):
        name_value = pers_name.text or ''
        name_lang = pers_name.get('{http://www.w3.org/XML/1998/namespace}lang', '')
        name_type = pers_name.get('type', 'primary')
        
        if name_value:
            data['names'].append({
                'value': name_value,
                'lang': name_lang,
                'type': name_type
            })
    
    # Extract sex
    sex_elem = find_one(person_elem, 'sex')
    if sex_elem is not None:
        sex_value = sex_elem.get('value', '')
        data['sex'] = 'male' if sex_value == '1' else ('female' if sex_value == '2' else 'unknown')
    
    # Extract notes (various types)
    for note in find_all(person_elem, 'note'):
        note_type = note.get('type', '')
        note_text = (note.text or '').strip()
        
        if note_type == 'dynasty':
            data['dynasty'] = note_text
        elif note_type == 'monk':
            data['is_monk'] = note_text == '是'
        elif note_type == 'concise':
            data['biography'] = note_text
        elif note_type == 'placeOfOrigin':
            place_elem = find_one(note, 'placeName')
            if place_elem is not None:
                data['place_of_origin'] = (place_elem.text or '').strip()
                ref = find_one(place_elem, 'ref')
                if ref is not None:
                    data['birth_place_ref'] = ref.get('target', '')
        elif note_type == 'activeAt':
            if note_text:
                data['active_at'] = [p.strip() for p in note_text.split('；') if p.strip()]
        elif note_type == 'worksBy':
            if note_text:
                data['works'] = [w.strip() for w in note_text.split('\n') if w.strip()]
    
    # Extract bibliography (sources)
    for bibl in find_all(person_elem, 'bibl'):
        bibl_text = (bibl.text or '').strip()
        if bibl_text:
            data['sources'].append(bibl_text)
    
    # Extract relationships (teacher/student)
    for relation in find_all(person_elem, 'relation'):
        rel_type = relation.get('type', '')
        active = relation.get('active', '')
        
        for name_elem in find_all(relation, 'persName'):
            name = (name_elem.text or '').strip()
            if name:
                if rel_type == 'teacher':
                    data['student'].append({
                        'id': active,
                        'name': name
                    })
                elif rel_type == 'student':
                    data['teacher'].append({
                        'id': active,
                        'name': name
                    })
    
    return data

def convert_to_json():
    """Main function to convert XML to JSON"""
    
    print(f"📥 Input: {INPUT_XML}")
    print(f"📤 Output: {OUTPUT_JSON}")
    
    # Check input file exists
    if not INPUT_XML.exists():
        print(f"❌ Error: Input file not found: {INPUT_XML}")
        return
    
    # Get file size
    file_size_mb = INPUT_XML.stat().st_size / (1024 * 1024)
    print(f"📊 File size: {file_size_mb:.2f} MB")
    
    # Load XML file
    print("🔄 Loading XML file...")
    tree = ET.parse(INPUT_XML)
    root = tree.getroot()
    
    # Navigate to listPerson using iteration (ElementTree adds default namespace to tags)
    print("🔄 Finding person list...")
    list_person = None
    for child1 in root:
        if 'text' in child1.tag:
            for child2 in child1:
                if 'body' in child2.tag:
                    for child3 in child2:
                        if 'listPerson' in child3.tag:
                            list_person = child3
                            break
    
    if list_person is None:
        print("❌ Error: Could not find listPerson element")
        return
    
    # Extract all persons
    print("🔄 Extracting person data...")
    persons = []
    count = 0
    
    ns = 'http://tei-c.org/ns/1.0'
    ns_prefix = f'{{{ns}}}'
    
    for person_elem in list_person:
        if 'person' not in person_elem.tag:
            continue
            
        person_data = extract_person_data_v2(person_elem, ns_prefix)
        if person_data.get('id'):
            persons.append(person_data)
            count += 1
            
            if count % 1000 == 0:
                print(f"   Processed {count} persons...")
    
    print(f"✅ Total persons extracted: {count}")
    
    # Build output JSON
    output_data = {
        'persons': persons,
        'count': count,
        'metadata': {
            'source': 'DILA Authority',
            'version': '2026-03',
            'imported': '2026-04-10',
            'description': 'Buddhist Studies Person Authority Database'
        }
    }
    
    # Save to JSON
    print(f"💾 Saving to {OUTPUT_JSON}...")
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Done! Saved {count} persons to {OUTPUT_JSON}")
    
    # Print sample
    if persons:
        print("\n📋 Sample person:")
        sample = persons[0]
        print(f"   ID: {sample.get('id')}")
        print(f"   Names: {[n.get('value') for n in sample.get('names', [])[:3]]}")
        print(f"   Dynasty: {sample.get('dynasty')}")
        print(f"   Is Monk: {sample.get('is_monk')}")
        print(f"   Biography: {sample.get('biography', '')[:100]}...")

def extract_person_data_v2(person_elem: ET.Element, ns_prefix: str) -> Dict:
    """Extract person data from TEI person element - version 2 with proper namespace handling"""
    data = {
        'id': '',
        'names': [],
        'sex': '',
        'dynasty': '',
        'is_monk': False,
        'birth_year': '',
        'death_year': '',
        'birth_place': '',
        'death_place': '',
        'place_of_origin': '',
        'active_at': [],
        'occupation': '',
        'biography': '',
        'teacher': [],
        'student': [],
        'sources': [],
        'works': [],
        'dila_url': ''
    }
    
    # Get person ID
    data['id'] = person_elem.get('{http://www.w3.org/XML/1998/namespace}id', '')
    
    if not data['id']:
        return data
    
    # Build DILA URL
    data['dila_url'] = f"http://authority.dila.edu.tw/person/{data['id']}"
    
    # Extract names - using direct iteration instead of findall with namespace
    for child in person_elem:
        tag = child.tag.split('}')[1] if '}' in child.tag else child.tag
        
        if tag == 'persName':
            name_value = (child.text or '').strip()
            if name_value:
                name_lang = child.get('{http://www.w3.org/XML/1998/namespace}lang', '')
                name_type = child.get('type', 'primary')
                data['names'].append({
                    'value': name_value,
                    'lang': name_lang,
                    'type': name_type
                })
        
        elif tag == 'sex':
            sex_value = child.get('value', '')
            data['sex'] = 'male' if sex_value == '1' else ('female' if sex_value == '2' else 'unknown')
        
        elif tag == 'note':
            note_type = child.get('type', '')
            note_text = (child.text or '').strip()
            
            if note_type == 'dynasty':
                data['dynasty'] = note_text
            elif note_type == 'monk':
                data['is_monk'] = note_text == '是'
            elif note_type == 'concise':
                data['biography'] = note_text
            elif note_type == 'placeOfOrigin':
                for subchild in child:
                    subtag = subchild.tag.split('}')[1] if '}' in subchild.tag else subchild.tag
                    if subtag == 'placeName':
                        data['place_of_origin'] = (subchild.text or '').strip()
            elif note_type == 'activeAt':
                if note_text:
                    data['active_at'] = [p.strip() for p in note_text.split('；') if p.strip()]
            elif note_type == 'worksBy':
                if note_text:
                    data['works'] = [w.strip() for w in note_text.split('\n') if w.strip()]
        
        elif tag == 'listBibl':
            # Sources
            for subchild in child:
                subtag = subchild.tag.split('}')[1] if '}' in subchild.tag else subchild.tag
                if subtag == 'bibl':
                    bibl_text = (subchild.text or '').strip()
                    if bibl_text:
                        data['sources'].append(bibl_text)
        
        elif tag == 'listRelation':
            # Teacher/Student relationships
            for subchild in child:
                subtag = subchild.tag.split('}')[1] if '}' in subchild.tag else subchild.tag
                if subtag == 'relation':
                    rel_type = subchild.get('type', '')
                    active_id = subchild.get('active', '')
                    
                    # Get name from n attribute
                    name = subchild.get('n', '')
                    
                    if rel_type == 'teacher' and active_id:
                        data['student'].append({
                            'id': active_id,
                            'name': name
                        })
                    elif rel_type == 'student' and active_id:
                        data['teacher'].append({
                            'id': active_id,
                            'name': name
                        })
    
    return data

if __name__ == '__main__':
    convert_to_json()