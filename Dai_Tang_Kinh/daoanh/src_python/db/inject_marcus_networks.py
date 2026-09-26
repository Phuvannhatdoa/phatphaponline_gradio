#!/usr/bin/env python3
"""
Inject Marcus Networks into SQLite
Creates marcus_networks table and imports 33,976 teacher-student relations from GEXF
"""
import json
import sqlite3
import os
from datetime import datetime

EDGES_FILE = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/chinese_buddhism_sna/marcus_edges_mapped.json"
DB_PATH = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/sqlite/buddhist_db.sqlite"

def create_table(conn):
    """Create marcus_networks table"""
    cursor = conn.cursor()
    
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
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_marcus_teacher ON marcus_networks(teacher_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_marcus_student ON marcus_networks(student_id)")
    
    conn.commit()
    print("✓ Created marcus_networks table")

def inject_data(conn):
    """Inject edges from Marcus GEXF"""
    with open(EDGES_FILE, encoding="utf-8") as f:
        edges = json.load(f)
    
    cursor = conn.cursor()
    
    teacher_edges = [e for e in edges if e.get("relation_type") == "da:isTeacherOf"]
    print(f"✓ Found {len(teacher_edges):,} teacher-student edges")
    
    inserted = 0
    skipped = 0
    
    for e in teacher_edges:
        teacher_id = e["source"]      # A000005 (鑑堂一)
        student_id = e["target"]    # A000668 (明滿)
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
        except Exception as err:
            skipped += 1
            print(f"  Skipped {teacher_id}->{student_id}: {err}")
    
    conn.commit()
    print(f"✓ Inserted {inserted:,} relations")
    print(f"  Skipped: {skipped:,}")

def show_stats(conn):
    """Show statistics"""
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM marcus_networks")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT teacher_id) FROM marcus_networks")
    teachers = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT student_id) FROM marcus_networks")
    students = cursor.fetchone()[0]
    
    print(f"\n=== Marcus Networks Stats ===")
    print(f"  Total relations: {total:,}")
    print(f"  Unique teachers: {teachers:,}")
    print(f"  Unique students: {students:,}")

def show_sample(conn):
    """Show sample data"""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT teacher_id, teacher_label, student_id, student_label, ref
        FROM marcus_networks
        LIMIT 5
    """)
    
    print(f"\n=== Sample Relations ===")
    for row in cursor.fetchall():
        tid, tlabel, sid, slabel, ref = row
        print(f"  {tlabel} ({tid}) → {slabel} ({sid})")
        if ref:
            print(f"    Ref: {ref[:60]}...")

if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    
    create_table(conn)
    inject_data(conn)
    show_stats(conn)
    show_sample(conn)
    
    conn.close()
    print("\n✓ Marcus Networks injection complete!")