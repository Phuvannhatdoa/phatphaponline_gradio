#!/usr/bin/env python3
"""
Deep Conflict Analysis - Compare DILA vs Marcus lineage data
Creates lineage_conflicts_v2 table with full comparison data
"""
import json
import sqlite3
import os
from collections import defaultdict

DB_PATH = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/sqlite/buddhist_db.sqlite"
PERSONS_FILE = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/persons.json"
OUTPUT_DIR = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/chinese_buddhism_sna"

def load_persons():
    """Load persons.json for DILA data"""
    with open(PERSONS_FILE, encoding="utf-8") as f:
        raw = json.load(f)
    return {p["id"]: p for p in raw.get("persons", [])}

def get_marcus_teachers(conn):
    """Get all teacher relationships from Marcus networks"""
    cursor = conn.cursor()
    cursor.execute("SELECT student_id, teacher_id FROM marcus_networks")
    
    marcus_teachers = defaultdict(list)
    for student_id, teacher_id in cursor.fetchall():
        marcus_teachers[student_id].append(teacher_id)
    
    return marcus_teachers

def get_marcus_students(conn):
    """Get all student relationships from Marcus networks"""
    cursor = conn.cursor()
    cursor.execute("SELECT teacher_id, student_id FROM marcus_networks")
    
    marcus_students = defaultdict(list)
    for teacher_id, student_id in cursor.fetchall():
        marcus_students[teacher_id].append(student_id)
    
    return marcus_students

def create_table(conn):
    """Create lineage_conflicts_v2 table"""
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
    print("✓ Created lineage_conflicts_v2 table")

def analyze_conflicts(conn, persons, marcus_teachers, marcus_students):
    """Compare DILA vs Marcus lineage data"""
    cursor = conn.cursor()
    
    conflicts = []
    total_checked = 0
    
    for person_id, person in persons.items():
        total_checked += 1
        
        dila_teachers = [t["id"] for t in person.get("teacher", [])]
        dila_students = [s["id"] for s in person.get("student", [])]
        
        marcus_tchr = marcus_teachers.get(person_id, [])
        marcus_std = marcus_students.get(person_id, [])
        
        set_dila_t = set(dila_teachers)
        set_marcus_t = set(marcus_tchr)
        
        set_dila_s = set(dila_students)
        set_marcus_s = set(marcus_std)
        
        name_zh = ""
        name_vi = ""
        for nm in person.get("names", []):
            if nm.get("type") == "primary":
                name_zh = nm.get("value", "")
            if nm.get("lang") == "vie":
                name_vi = nm.get("value", "")
        
        if not name_vi:
            for nm in person.get("names", []):
                if nm.get("lang") in ("zho-Hant", "zho-Hans"):
                    name_vi = nm.get("value", "")
                    break
        
        if set_dila_t != set_marcus_t:
            conflicts.append({
                "person_id": person_id,
                "label": name_zh,
                "name_vi": name_vi,
                "conflict_type": "teacher_set",
                "dila_data": json.dumps(sorted(set_dila_t)),
                "marcus_data": json.dumps(sorted(set_marcus_t)),
                "dila_count": len(set_dila_t),
                "marcus_count": len(set_marcus_t)
            })
        
        if set_dila_s != set_marcus_s:
            conflicts.append({
                "person_id": person_id,
                "label": name_zh,
                "name_vi": name_vi,
                "conflict_type": "student_set",
                "dila_data": json.dumps(sorted(set_dila_s)),
                "marcus_data": json.dumps(sorted(set_marcus_s)),
                "dila_count": len(set_dila_s),
                "marcus_count": len(set_marcus_s)
            })
        
        if total_checked % 5000 == 0:
            print(f"  Checked {total_checked:,} persons...")
    
    print(f"✓ Analyzed {total_checked:,} persons")
    return conflicts

def insert_conflicts(conn, conflicts):
    """Insert conflicts into SQLite"""
    cursor = conn.cursor()
    
    inserted = 0
    for c in conflicts:
        cursor.execute("""
            INSERT INTO lineage_conflicts_v2 
            (person_id, label, name_vi, conflict_type, dila_data, marcus_data, dila_count, marcus_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            c["person_id"],
            c["label"],
            c["name_vi"],
            c["conflict_type"],
            c["dila_data"],
            c["marcus_data"],
            c["dila_count"],
            c["marcus_count"]
        ))
        inserted += 1
    
    conn.commit()
    print(f"✓ Inserted {inserted:,} conflicts")

def save_json(conflicts):
    """Save conflicts to JSON"""
    conflicts_file = os.path.join(OUTPUT_DIR, "lineage_conflicts_v2.json")
    
    with open(conflicts_file, "w", encoding="utf-8") as f:
        json.dump(conflicts, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Saved to {conflicts_file}")

def show_stats(conn):
    """Show statistics"""
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM lineage_conflicts_v2")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM lineage_conflicts_v2 WHERE conflict_type='teacher_set'")
    teacher_conflicts = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM lineage_conflicts_v2 WHERE conflict_type='student_set'")
    student_conflicts = cursor.fetchone()[0]
    
    print(f"\n=== Conflict Stats ===")
    print(f"  Total conflicts: {total:,}")
    print(f"  Teacher set conflicts: {teacher_conflicts:,}")
    print(f"  Student set conflicts: {student_conflicts:,}")

def show_sample(conn):
    """Show sample conflicts"""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT person_id, label, name_vi, conflict_type, dila_data, marcus_data
        FROM lineage_conflicts_v2
        WHERE conflict_type='teacher_set'
        LIMIT 3
    """)
    
    print(f"\n=== Sample Teacher Conflicts ===")
    for row in cursor.fetchall():
        pid, label, name_vi, ctype, dila, marcus = row
        dila_ids = json.loads(dila) if dila else []
        marcus_ids = json.loads(marcus) if marcus else []
        print(f"  {label} ({pid}) - {name_vi}")
        print(f"    DILA teachers: {dila_ids[:3]}...")
        print(f"    Marcus teachers: {marcus_ids[:3]}...")

if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    
    print("Loading DILA persons...")
    persons = load_persons()
    
    print("Loading Marcus network data...")
    marcus_teachers = get_marcus_teachers(conn)
    marcus_students = get_marcus_students(conn)
    
    create_table(conn)
    
    print("Analyzing conflicts...")
    conflicts = analyze_conflicts(conn, persons, marcus_teachers, marcus_students)
    
    insert_conflicts(conn, conflicts)
    save_json(conflicts)
    show_stats(conn)
    show_sample(conn)
    
    conn.close()
    print("\n✓ Deep conflict analysis complete!")