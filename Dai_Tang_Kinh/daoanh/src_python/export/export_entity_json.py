#!/usr/bin/env python3
"""
Export Entity JSON - Chuyển đổi persons.json thành Final JSON Schema cho GIS/Deepsearch
Output: entity_export.json theo chuẩn Final JSON Schema
"""
import json
import os
from datetime import datetime

DATA_DIR = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data"
OUTPUT_DIR = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/ontology/json"

def load_persons():
    """Load persons.json data"""
    persons_file = os.path.join(DATA_DIR, "persons.json")
    with open(persons_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('persons', [])

def get_viet_name(names):
    """Extract Vietnamese name from names array"""
    if not names:
        return None
    for n in names:
        if n.get('lang') in ['vi', 'viet', 'vietnamese']:
            return n.get('value')
    # Fallback to first Chinese name
    if names:
        return names[0].get('value')
    return None

def get_han_name(names):
    """Extract Han name from names array"""
    if not names:
        return None
    for n in names:
        if n.get('lang') in ['zho-Hant', 'zh-Hant', 'han', 'chinese']:
            return n.get('value')
    return None

def build_authority_links(person):
    """Build authority_links from person data"""
    links = {}
    
    # DILA link
    if person.get('dila_url'):
        dila_id = person.get('id', '')
        if dila_id.startswith('A'):
            links['dila'] = dila_id
    
    # Wiki link (if available in sources or external)
    if person.get('wiki_url'):
        links['wiki'] = person.get('wiki_url')
    
    return links if links else None

def build_spatial_timeline(person):
    """Build spatial_timeline from active_at and events"""
    timeline = []
    
    # Extract from active_at (places where person was active)
    active_at = person.get('active_at', [])
    if active_at:
        for i, place in enumerate(active_at):
            timeline.append({
                "event": f"Hoạt động tại {place}",
                "year": None,
                "location": {
                    "name": place,
                    "lat": None,
                    "lng": None
                }
            })
    
    return timeline if timeline else None

def build_graph_connections(person):
    """Build graph_connections with teacher/student relationships"""
    connections = []
    
    # Teacher connection - handle both string and object format
    teachers = person.get('teacher', [])
    for t in teachers:
        if isinstance(t, str):
            target_id = t
        elif isinstance(t, dict):
            target_id = t.get('id', '')
        else:
            continue
        if target_id:
            connections.append({
                "target": target_id,
                "relation": "TeacherOf",
                "weight": 10
            })
    
    # Student connections - handle both string and object format
    students = person.get('student', [])
    for s in students:
        if isinstance(s, str):
            target_id = s
        elif isinstance(s, dict):
            target_id = s.get('id', '')
        else:
            continue
        if target_id:
            connections.append({
                "target": target_id,
                "relation": "DiscipleOf",
                "weight": 10
            })
    
    return connections if connections else None

def convert_person(person):
    """Convert single person to entity schema"""
    names = person.get('names', [])
    viet_name = get_viet_name(names)
    han_name = get_han_name(names)
    
    entity = {
        "id": person.get('id', ''),
        "name": viet_name or han_name or "Unknown",
        "lineage": person.get('dharma_lineage', None),
        "authority_links": build_authority_links(person),
        "han_name": han_name,
        "dynasty": person.get('dynasty', None),
        "birth_year": person.get('birth_year', None),
        "death_year": person.get('death_year', None),
        "biography": person.get('biography', None),
        "sources": person.get('sources', []),
        "works": person.get('works', []),
    }
    
    # Add optional fields
    spatial = build_spatial_timeline(person)
    if spatial:
        entity['spatial_timeline'] = spatial
    
    graph = build_graph_connections(person)
    if graph:
        entity['graph_connections'] = graph
    
    return entity

def export_entity_json():
    """Main export function"""
    print("📦 Loading persons.json...")
    persons = load_persons()
    print(f"   Loaded {len(persons)} persons")
    
    # Convert all persons
    entities = []
    for p in persons:
        try:
            entity = convert_person(p)
            entities.append(entity)
        except Exception as e:
            print(f"   ⚠️ Error converting {p.get('id', 'unknown')}: {e}")
    
    # Build final output
    output = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "agent_version": "Refiner-v1.2",
            "total_entities": len(entities)
        },
        "entities": entities
    }
    
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Write output
    output_file = os.path.join(OUTPUT_DIR, "entity_export.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Exported to: {output_file}")
    print(f"   Total entities: {len(entities)}")
    
    # Print sample
    if entities:
        sample = entities[0]
        print(f"\n📋 Sample entity:")
        print(f"   ID: {sample.get('id')}")
        print(f"   Name: {sample.get('name')}")
        print(f"   Has authority_links: {'authority_links' in sample}")
        print(f"   Has spatial_timeline: {'spatial_timeline' in sample}")
        print(f"   Has graph_connections: {'graph_connections' in sample}")
    
    return output

if __name__ == "__main__":
    export_entity_json()
