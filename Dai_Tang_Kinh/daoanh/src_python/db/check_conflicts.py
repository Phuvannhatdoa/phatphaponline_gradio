#!/usr/bin/env python3
"""
Compare lineage between Marcus SNA and persons.json (DILA)
Log conflicts where relationships differ
"""
import json
import sqlite3
import os
from collections import defaultdict

NODES_FILE = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/chinese_buddhism_sna/marcus_nodes_mapped.json"
EDGES_FILE = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/chinese_buddhism_sna/marcus_edges_mapped.json"
DB_PATH = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/sqlite/buddhist_db.sqlite"
OUTPUT_DIR = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/chinese_buddhism_sna"

def load_data():
    with open(NODES_FILE, encoding="utf-8") as f:
        nodes = json.load(f)
    with open(EDGES_FILE, encoding="utf-8") as f:
        edges = json.load(f)
    return nodes, edges

def build_edge_lookup(edges):
    """Build lookup: node_id -> list of teachers from edges"""
    marcus_teacher_of = defaultdict(set)
    marcus_student_of = defaultdict(set)
    
    for e in edges:
        if e.get("relation_type") == "da:isTeacherOf":
            src = e["source"]
            tgt = e["target"]
            marcus_teacher_of[src].add(tgt)
            marcus_student_of[tgt].add(src)
    
    return marcus_teacher_of, marcus_student_of

def check_conflicts(nodes, marcus_teacher_of, marcus_student_of):
    """Compare Marcus edges with persons.json teacher/student"""
    
    conflicts = []
    
    for node_id, node in nodes.items():
        dila_teachers = {t["id"] for t in node.get("teacher", [])}
        dila_students = {s["id"] for s in node.get("student", [])}
        
        marcus_teachers = marcus_student_of.get(node_id, set())
        marcus_students = marcus_teacher_of.get(node_id, set())
        
        only_dila_teacher = dila_teachers - marcus_student_of.get(node_id, set())
        only_marcus_teacher = marcus_student_of.get(node_id, set()) - dila_teachers
        
        only_dila_student = dila_students - marcus_teacher_of.get(node_id, set())
        only_marcus_student = marcus_teacher_of.get(node_id, set()) - dila_students
        
        if only_dila_teacher or only_marcus_teacher or only_dila_student or only_marcus_student:
            conflicts.append({
                "node_id": node_id,
                "label": node.get("label", ""),
                "only_dila_teacher": list(only_dila_teacher),
                "only_marcus_teacher": list(only_marcus_teacher),
                "only_dila_student": list(only_dila_student),
                "only_marcus_student": list(only_marcus_student),
                "type": "lineage"
            })
    
    return conflicts

def save_conflicts(conflicts):
    """Save conflicts to JSON"""
    
    conflicts_file = os.path.join(OUTPUT_DIR, "lineage_conflicts.json")
    
    with open(conflicts_file, "w", encoding="utf-8") as f:
        json.dump(conflicts, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Saved {len(conflicts):,} conflicts to {conflicts_file}")
    return conflicts_file

def save_to_sqlite(conflicts):
    """Save conflicts to SQLite"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lineage_conflicts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT,
            label TEXT,
            source TEXT DEFAULT 'MARCUS',
            conflict_type TEXT DEFAULT 'lineage',
            only_dila_teacher TEXT,
            only_marcus_teacher TEXT,
            only_dila_student TEXT,
            only_marcus_student TEXT,
            resolved INTEGER DEFAULT 0,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    for c in conflicts:
        cursor.execute("""
            INSERT INTO lineage_conflicts (node_id, label, conflict_type, only_dila_teacher, only_marcus_teacher, only_dila_student, only_marcus_student)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            c["node_id"],
            c["label"],
            c["type"],
            json.dumps(c.get("only_dila_teacher", [])),
            json.dumps(c.get("only_marcus_teacher", [])),
            json.dumps(c.get("only_dila_student", [])),
            json.dumps(c.get("only_marcus_student", []))
        ))
    
    conn.commit()
    conn.close()
    print(f"✓ Saved {len(conflicts):,} conflicts to SQLite")

def show_sample_conflicts(conflicts):
    """Show sample conflicts"""
    print(f"\n=== Sample Conflicts ===")
    for c in conflicts[:5]:
        print(f"  {c['label']} ({c['node_id']})")
        if c.get("only_marcus_teacher"):
            print(f"    Marcus has teacher: {c['only_marcus_teacher']} (not in DILA)")
        if c.get("only_dila_teacher"):
            print(f"    DILA has teacher: {c['only_dila_teacher']} (not in Marcus)")

if __name__ == "__main__":
    nodes, edges = load_data()
    
    marcus_teacher_of, marcus_student_of = build_edge_lookup(edges)
    
    conflicts = check_conflicts(nodes, marcus_teacher_of, marcus_student_of)
    
    save_conflicts(conflicts)
    save_to_sqlite(conflicts)
    show_sample_conflicts(conflicts)
    
    total = len(nodes)
    print(f"\n=== Conflict Stats ===")
    print(f"  Total Marcus nodes: {total:,}")
    print(f"  Nodes with conflicts: {len(conflicts):,} ({100*len(conflicts)/total:.1f}%)")