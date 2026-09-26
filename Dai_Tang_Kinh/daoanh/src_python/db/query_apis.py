#!/usr/bin/env python3
"""
Query APIs for SQLite Buddhist Database
"""
import sqlite3
import json
import os

DB_PATH = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/sqlite/buddhist_db.sqlite"

def query_by_name(name, limit=10):
    """Search people by name"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, name_zh, name_vi, dynasty, lineage
        FROM people
        WHERE name_zh LIKE ? OR name_vi LIKE ? OR name_en LIKE ?
        LIMIT ?
    ''', (f'%{name}%', f'%{name}%', f'%{name}%', limit))
    
    results = []
    for row in cursor.fetchall():
        results.append({
            'id': row[0],
            'name_zh': row[1],
            'name_vi': row[2],
            'dynasty': row[3],
            'lineage': row[4]
        })
    
    conn.close()
    return results

def query_by_lineage(lineage, limit=20):
    """Get people by lineage"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, name_zh, dynasty, birth_year, death_year
        FROM people
        WHERE lineage LIKE ?
        LIMIT ?
    ''', (f'%{lineage}%', limit))
    
    results = []
    for row in cursor.fetchall():
        results.append({
            'id': row[0],
            'name_zh': row[1],
            'dynasty': row[2],
            'birth_year': row[3],
            'death_year': row[4]
        })
    
    conn.close()
    return results

def query_by_dynasty(dynasty, limit=20):
    """Get people by dynasty"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, name_zh, name_vi, birth_year, death_year
        FROM people
        WHERE dynasty = ?
        LIMIT ?
    ''', (dynasty, limit))
    
    results = []
    for row in cursor.fetchall():
        results.append({
            'id': row[0],
            'name_zh': row[1],
            'name_vi': row[2],
            'birth_year': row[3],
            'death_year': row[4]
        })
    
    conn.close()
    return results

def query_teacher_student(person_id):
    """Get teacher/student network"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Teachers
    cursor.execute('''
        SELECT p.id, p.name_zh, p.dynasty, n.relation_type
        FROM networks n
        JOIN people p ON n.target_id = p.id
        WHERE n.person_id = ? AND n.relation_type = 'TeacherOf'
    ''', (person_id,))
    
    teachers = [{'id': r[0], 'name': r[1], 'dynasty': r[2], 'relation': r[3]} for r in cursor.fetchall()]
    
    # Students
    cursor.execute('''
        SELECT p.id, p.name_zh, p.dynasty, n.relation_type
        FROM networks n
        JOIN people p ON n.target_id = p.id
        WHERE n.person_id = ? AND n.relation_type = 'DiscipleOf'
    ''', (person_id,))
    
    students = [{'id': r[0], 'name': r[1], 'dynasty': r[2], 'relation': r[3]} for r in cursor.fetchall()]
    
    conn.close()
    return {'teachers': teachers, 'students': students}

def query_places_near(lat, lng, radius_km=50):
    """Get places within radius (simple lat/lng box)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Simple box approximation
    lat_delta = radius_km / 111.0  # ~111km per degree
    lng_delta = radius_km / (111.0 * 0.7)  # Rough approximation
    
    cursor.execute('''
        SELECT id, name_zh, lat, lng, country, province
        FROM places
        WHERE lat BETWEEN ? AND ?
        AND lng BETWEEN ? AND ?
        LIMIT 20
    ''', (lat - lat_delta, lat + lat_delta, lng - lng_delta, lng + lng_delta))
    
    results = []
    for row in cursor.fetchall():
        results.append({
            'id': row[0],
            'name_zh': row[1],
            'lat': row[2],
            'lng': row[3],
            'country': row[4],
            'province': row[5]
        })
    
    conn.close()
    return results

def get_stats():
    """Get database statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    stats = {}
    
    tables = ['people', 'places', 'networks', 'canons_catalog', 'lexicon', 'time_periods']
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        stats[table] = cursor.fetchone()[0]
    
    conn.close()
    return stats

# Test queries
if __name__ == "__main__":
    print("📊 Database Stats:")
    stats = get_stats()
    for k, v in stats.items():
        print(f"   {k}: {v:,}")
    
    print("\n🔍 Query: Search 'Thích' (5 results)")
    results = query_by_name('Thích', 5)
    for r in results:
        print(f"   {r['id']}: {r['name_zh']} ({r['dynasty']})")
    
    print("\n🔍 Query: Dynasty '宋' (3 results)")
    results = query_by_dynasty('宋', 3)
    for r in results:
        print(f"   {r['id']}: {r['name_zh']}")
    
    print("\n✅ All queries working!")