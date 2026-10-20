#!/usr/bin/env python3
"""
Inject Marcus Networks into lineage.db (the server's database)
"""
import json
import sqlite3
import os

EDGES_FILE = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/chinese_buddhism_sna/marcus_edges_mapped.json"
DB_PATH = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/lineage.db"

def inject_to_lineage_db():
    """Inject Marcus networks into lineage.db"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS marcus_networks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id TEXT NOT NULL,
            student_id TEXT NOT NULL,
            relation_type TEXT NOT NULL,
            teacher_label TEXT,
            student_label TEXT,
            source_data TEXT DEFAULT 'MARCUS',
            ref TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(teacher_id, student_id, relation_type)
        )
    """)
    conn.commit()
    
    with open(EDGES_FILE, encoding="utf-8") as f:
        edges = json.load(f)
    
    teacher_edges = [e for e in edges if e.get("relation_type") == "da:isTeacherOf"]
    print(f"✓ Found {len(teacher_edges):,} teacher-student edges")
    
    inserted = 0
    for e in teacher_edges:
        teacher_id = e["source"]
        student_id = e["target"]
        relation_type = e.get("relation_type", "da:isTeacherOf")
        teacher_label = e.get("source_label", "")
        student_label = e.get("target_label", "")
        ref = e.get("attrs", {}).get("e@ref", "")
        
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO marcus_networks 
                (teacher_id, student_id, relation_type, teacher_label, student_label, ref)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (teacher_id, student_id, relation_type, teacher_label, student_label, ref))
            inserted += 1
        except:
            pass
    
    conn.commit()
    print(f"✓ Inserted {inserted:,} relations into lineage.db")

def inject_conflicts_v2():
    """Inject conflicts into lineage.db"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lineage_conflicts_v2 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id TEXT NOT NULL,
            label TEXT,
            name_vi TEXT,
            conflict_type TEXT,
            dila_data TEXT,
            marcus_data TEXT,
            dila_count INTEGER,
            marcus_count INTEGER,
            is_conflict BOOLEAN DEFAULT 1,
            resolved BOOLEAN DEFAULT 0,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    
    # Load from buddhist_db.sqlite
    bddb = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/sqlite/buddhist_db.sqlite"
    conn2 = sqlite3.connect(bddb)
    cursor2 = conn2.cursor()
    
    cursor2.execute("SELECT person_id, label, name_vi, conflict_type, dila_data, marcus_data, dila_count, marcus_count FROM lineage_conflicts_v2")
    
    inserted = 0
    for row in cursor2.fetchall():
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO lineage_conflicts_v2 
                (person_id, label, name_vi, conflict_type, dila_data, marcus_data, dila_count, marcus_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, row)
            inserted += 1
        except:
            pass
    
    conn.commit()
    conn2.close()
    print(f"✓ Inserted {inserted:,} conflicts into lineage.db")

if __name__ == "__main__":
    inject_to_lineage_db()
    inject_conflicts_v2()
    print("✓ Done!")