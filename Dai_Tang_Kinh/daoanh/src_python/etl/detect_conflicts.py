#!/usr/bin/env python3
"""
Conflict Detection: DILA vs Marcus Lineage
Only insert into conflicts table when DILA_set != Marcus_set

Usage: python detect_conflicts.py
"""

import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime

BASE_DIR = Path("/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh")
DB_FILE = BASE_DIR / "data" / "lineage.db"

# Marcus SNA files
MARCUS_NODES_FILE = BASE_DIR / "data" / "chinese_buddhism_sna" / "marcus_nodes_mapped.json"
MARCUS_EDGES_FILE = BASE_DIR / "data" / "chinese_buddhism_sna" / "marcus_edges_mapped.json"


def load_persons_data():
    """Load persons.json for DILA data"""
    persons_file = BASE_DIR / "data" / "persons.json"
    if persons_file.exists():
        with open(persons_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def detect_conflicts():
    """Detect conflicts between DILA and Marcus lineage data"""
    print("=" * 60)
    print("🔍 CONFLICT DETECTION: DILA vs Marcus")
    print("=" * 60)
    
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    
    # Load DILA data
    print("\n📋 Loading DILA persons...")
    persons = load_persons_data()
    print(f"   Loaded {len(persons)} DILA persons")
    
    # Load Marcus data
    marcus_nodes = []
    if MARCUS_NODES_FILE.exists():
        with open(MARCUS_NODES_FILE, 'r', encoding='utf-8') as f:
            marcus_nodes = json.load(f)
    print(f"   Loaded {len(marcus_nodes)} Marcus nodes")
    
    # Build DILA teacher/student maps
    print("\n🔨 Building DILA lineage map...")
    dila_teachers = {}
    dila_students = {}
    
    for pid, data in persons.items():
        if not isinstance(data, dict):
            continue
        
        # Teachers
        teachers = data.get('teacher', [])
        if isinstance(teachers, str) and teachers:
            try:
                teachers = json.loads(teachers)
            except:
                teachers = []
        if isinstance(teachers, list) and teachers:
            dila_teachers[pid] = [t.get('id', '') for t in teachers if t.get('id')]
        
        # Students  
        students = data.get('student', [])
        if isinstance(students, str) and students:
            try:
                students = json.loads(students)
            except:
                students = []
        if isinstance(students, list) and students:
            dila_students[pid] = [s.get('id', '') for s in students if s.get('id')]
    
    print(f"   DILA teachers: {len(dila_teachers)}")
    print(f"   DILA students: {len(dila_students)}")
    
    # Build Marcus teacher/student maps
    print("\n🔨 Building Marcus lineage map...")
    marcus_teachers = {}
    marcus_students = {}
    
    if MARCUS_EDGES_FILE.exists():
        with open(MARCUS_EDGES_FILE, 'r', encoding='utf-8') as f:
            marcus_edges = json.load(f)
        
        for edge in marcus_edges:
            source = edge.get('source', '')
            target = edge.get('target', '')
            rel_type = edge.get('relation', '')
            
            if rel_type in ['teacher of', 'disciple of', 'directed']:
                if source not in marcus_teachers:
                    marcus_teachers[source] = []
                marcus_teachers[source].append(target)
            
            if source not in marcus_students:
                marcus_students[source] = []
            marcus_students[source].append(target)
    
    print(f"   Marcus teachers: {len(marcus_teachers)}")
    print(f"   Marcus students: {len(marcus_students)}")
    
    # Detect conflicts
    print("\n🔍 Detecting conflicts...")
    conflicts = []
    processed = 0
    
    # Process only first 1000 for demo (will do full run later)
    for monk_id, dila_t in dila_teachers.items():
        if processed >= 1000:
            break
        processed += 1
        
        marcus_t = marcus_teachers.get(monk_id, [])
        
        # Convert to sets for comparison
        dila_set = set(dila_t)
        marcus_set = set(marcus_t)
        
        # Only insert if there's a difference
        if dila_set != marcus_set:
            node_data = None
            for node in marcus_nodes[:10]:
                if node.get('id') == monk_id:
                    node_data = node
                    break
            
            name = node_data.get('label', '') if node_data else ''
            
            conflicts.append({
                'monk_id': monk_id,
                'monk_name': name,
                'conflict_type': 'lineage_teachers',
                'only_dila_teachers': json.dumps(list(dila_set - marcus_set)),
                'only_marcus_teachers': json.dumps(list(marcus_set - dila_set)),
                'dila_count': len(dila_set),
                'marcus_count': len(marcus_set),
                'status': 'pending'
            })
        
        # Also check students
        dila_s = dila_students.get(monk_id, [])
        marcus_s = marcus_students.get(monk_id, [])
        
        dila_set_s = set(dila_s)
        marcus_set_s = set(marcus_s)
        
        if dila_set_s != marcus_set_s:
            node_data = None
            for node in marcus_nodes[:10]:
                if node.get('id') == monk_id:
                    node_data = node
                    break
            
            name = node_data.get('label', '') if node_data else ''
            
            conflicts.append({
                'monk_id': monk_id,
                'monk_name': name,
                'conflict_type': 'lineage_students',
                'only_dila_students': json.dumps(list(dila_set_s - marcus_set_s)),
                'only_marcus_students': json.dumps(list(marcus_set_s - dila_set_s)),
                'dila_count': len(dila_set_s),
                'marcus_count': len(marcus_set_s),
                'status': 'pending'
            })
    
    # Insert conflicts (batching for performance)
    print(f"\n💾 Inserting {len(conflicts)} conflicts...")
    
    batch_size = 500
    for i in range(0, len(conflicts), batch_size):
        batch = conflicts[i:i+batch_size]
        
        cursor.executemany("""
            INSERT INTO conflicts (
                monk_id, monk_name, conflict_type, 
                only_dila_teachers, only_marcus_teachers,
                only_dila_students, only_marcus_students,
                dila_count, marcus_count, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            (
                c['monk_id'], c['monk_name'], c['conflict_type'],
                c.get('only_dila_teachers', ''), c.get('only_marcus_teachers', ''),
                c.get('only_dila_students', ''), c.get('only_marcus_students', ''),
                c['dila_count'], c['marcus_count'], c['status']
            ) for c in batch
        ])
        
        conn.commit()
        print(f"   Inserted batch {i//batch_size + 1}: {len(batch)} records")
    
    # Summary
    cursor.execute("SELECT COUNT(*) FROM conflicts WHERE status='pending'")
    pending = cursor.fetchone()[0]
    
    print("\n" + "=" * 60)
    print("✅ CONFLICT DETECTION COMPLETE")
    print("=" * 60)
    print(f"   Total conflicts: {len(conflicts)}")
    print(f"   Pending: {pending}")
    print(f"   Database: {DB_FILE}")
    
    conn.close()
    
    return len(conflicts)


if __name__ == "__main__":
    detect_conflicts()