#!/usr/bin/env python3
"""
Automated Label Resolver & TTL Generator
The Muscle: Auto-enrich skeleton TTL files from SQLite

Features:
- Skeleton Scanner: Scan /data/ttl/old for .ttl skeletons
- Deep Enrichment: Bio, SNA, GIS, Works from SQLite
- Conflict Handling: PENDING/RESOLVED logic
- Knowledge Injection: Build complete TTL
- Multi-Format Export: TTL + JSON
"""

import sqlite3
import re
import os
from pathlib import Path
from datetime import datetime

BASE_DIR = Path("/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh")
DB_FILE = BASE_DIR / "data" / "lineage.db"
TTL_OLD = BASE_DIR / "data" / "ttl" / "old"
TTL_OUT = BASE_DIR / "ontology" / "ttl" / "monks"
JSON_OUT = BASE_DIR / "ontology" / "json" / "monks"

TTL_OLD.mkdir(parents=True, exist_ok=True)
TTL_OUT.mkdir(parents=True, exist_ok=True)
JSON_OUT.mkdir(parents=True, exist_ok=True)


def scan_skeletons():
    """Quét thư mục ttl/old tìm .ttl skeleton files"""
    print("\n📂 Scanning skeleton TTL files...")
    
    if not TTL_OLD.exists():
        print(f"   ⚠️ Directory not found: {TTL_OLD}")
        return []
    
    files = list(TTL_OLD.glob("*.ttl"))
    print(f"   Found {len(files)} skeleton TTL files")
    return files


def extract_dila_id(ttl_content):
    """Trích xuất da:dilaId từ TTL content"""
    patterns = [
        r'da:(\w+)\s+a\s+bkg:Monk',
        r'da:(\w+)\s+a\s+foaf:Person',
        r'<ex:monk/([^>]+)>\s+a\s+bkg:Monk',
        r':(\w+)\s+a\s+bkg:Monk',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, ttl_content)
        if match:
            aid = match.group(1)
            if 'monk/' in aid:
                aid = aid.replace('monk/', '')
            return f"A{aid}" if not aid.startswith('A') else aid
    
    return None


def query_bio(dila_id):
    """Lấy bio từ SQLite people"""
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT name_vi, name_zh, sect, dynasty, bio
        FROM people WHERE id = ? OR name_vi LIKE ? OR name_zh LIKE ?
    """, (dila_id, f"%{dila_id}%", f"%{dila_id}%"))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'name_vi': row[0] or '',
            'name_zh': row[1] or '',
            'sect': row[2] or '',
            'dynasty': row[3] or '',
            'short_bio': row[4] or ''
        }
    return {}


def query_sna(dila_id):
    """Lấy quan hệ thầy trò từ SQLite networks"""
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT related_id, relation_type, source_origin
        FROM networks WHERE monk_id = ?
    """, (dila_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    teachers = []
    disciples = []
    
    for related_id, relation_type, origin in rows:
        if relation_type == 'hasTeacher':
            teachers.append({'id': related_id, 'origin': origin})
        elif relation_type == 'hasDisciple':
            disciples.append({'id': related_id, 'origin': origin})
    
    return {'teachers': teachers, 'disciples': disciples}


def query_gis(dila_id):
    """Lấy tọa độ từ SQLite places"""
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT name_vi, province, gps_lat, gps_long
        FROM places WHERE id LIKE ?
    """, (f"%{dila_id}%",))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'name_vi': row[0] or '',
            'province': row[1] or '',
            'lat': row[2],
            'lng': row[3]
        }
    return {}


def query_conflicts(dila_id):
    """Tra cứu conflicts"""
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, status, admin_choice
        FROM conflicts WHERE monk_id = ?
    """, (dila_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'conflict_id': row[0],
            'status': row[1],
            'admin_choice': row[2]
        }
    return None


def build_enriched_ttl(skeleton, bio, sna, gis, conflicts):
    """Build enriched TTL with all data"""
    dila_id = extract_dila_id(skeleton)
    if not dila_id:
        return None
    
    lines = [
        f"# Enriched TTL for {dila_id}",
        f"# Generated: {datetime.now().isoformat()}",
        "",
    ]
    
    # Conflict handling
    if conflicts and conflicts['status'] == 'PENDING':
        lines.append(f"# [CONFLICT ALERT] Conflict ID: {conflicts['conflict_id']}")
        lines.append(f"# Status: PENDING - Data merged from multiple sources")
        lines.append("")
    
    # Core data
    lines.append(f"da:{dila_id} a bkg:Monk ;")
    
    if bio.get('name_vi'):
        lines.append(f'    skos:prefLabel "{bio["name_vi"]}"@vi ;')
    
    if bio.get('name_zh'):
        lines.append(f'    rdfs:label "{bio["name_zh"]}"@zh-Hans ;')
    
    if bio.get('sect'):
        lines.append(f'    bkg:sect "{bio["sect"]}" ;')
    
    if bio.get('lineage'):
        lines.append(f'    bkg:lineage "{bio["lineage"]}" ;')
    
    if bio.get('dynasty'):
        lines.append(f'    bkg:dynasty "{bio["dynasty"]}" ;')
    
    if bio.get('short_bio'):
        lines.append(f'    bkg:biographicalNote "{bio["short_bio"]}"@vi ;')
    
    # Teachers
    for t in sna.get('teachers', []):
        if t['id']:
            lines.append(f'    da:hasTeacher <#{t["id"]}> ;')
    
    # Disciples
    for d in sna.get('disciples', []):
        if d['id']:
            lines.append(f'    da:hasDisciple <#{d["id"]}> ;')
    
    # GIS
    if gis.get('lat') and gis.get('lng'):
        lines.append(f'    geo:lat {gis["lat"]} ;')
        lines.append(f'    geo:long {gis["lng"]} ;')
        if gis.get('province'):
            lines.append(f'    bkg:province "{gis["province"]}" ;')
    
    lines.append('    .')
    
    return '\n'.join(lines)


def build_json(dila_id, bio, sna, gis):
    """Build flat JSON for GIS"""
    return {
        'id': dila_id,
        'name_vi': bio.get('name_vi', ''),
        'name_zh': bio.get('name_zh', ''),
        'sect': bio.get('sect', ''),
        'lineage': bio.get('lineage', ''),
        'dynasty': bio.get('dynasty', ''),
        'short_bio': bio.get('short_bio', ''),
        'teachers': [t['id'] for t in sna.get('teachers', [])],
        'disciples': [d['id'] for d in sna.get('disciples', [])],
        'lat': gis.get('lat'),
        'lng': gis.get('lng'),
        'province': gis.get('province', '')
    }


def process_skeletons():
    """Main enrichment pipeline"""
    print("=" * 60)
    print("🚀 Automated Label Resolver & TTL Generator")
    print("=" * 60)
    
    files = scan_skeletons()
    
    enriched = 0
    conflicts = 0
    
    for filepath in files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                skeleton = f.read()
        except:
            continue
        
        dila_id = extract_dila_id(skeleton)
        if not dila_id:
            continue
        
        bio = query_bio(dila_id)
        sna = query_sna(dila_id)
        gis = query_gis(dila_id)
        conflict_data = query_conflicts(dila_id)
        
        if conflict_data:
            conflicts += 1
        
        ttl_content = build_enriched_ttl(skeleton, bio, sna, gis, conflict_data)
        
        if ttl_content:
            out_ttl = TTL_OUT / filepath.name
            with open(out_ttl, 'w', encoding='utf-8') as f:
                f.write(ttl_content)
            
            json_data = build_json(dila_id, bio, sna, gis)
            out_json = JSON_OUT / f"{dila_id}.json"
            
            import json
            with open(out_json, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            enriched += 1
    
    print(f"\n📊 Enrichment Complete:")
    print(f"   Enriched: {enriched} TTL files")
    print(f"   Conflicts: {conflicts}")
    print(f"   Output TTL: {TTL_OUT}")
    print(f"   Output JSON: {JSON_OUT}")
    
    return enriched


if __name__ == "__main__":
    process_skeletons()
    
    print("\n✅ TTL Enrichment Complete")