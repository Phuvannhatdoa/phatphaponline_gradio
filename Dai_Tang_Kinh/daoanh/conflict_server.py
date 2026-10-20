#!/usr/bin/conflict_server.py
"""
Conflict API Server - Lightweight Flask server for Marcus conflicts
"""
import os
import sqlite3
import json
from flask import Flask, jsonify, request
from datetime import datetime

app = Flask(__name__)

DB_PATH = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/lineage.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/conflicts')
def api_conflicts():
    """Get unresolved conflicts"""
    conn = get_db()
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        conflict_type = request.args.get('type', None)
        
        query = "SELECT * FROM lineage_conflicts_v2 WHERE resolved = 0"
        params = []
        
        if conflict_type:
            query += " AND conflict_type = ?"
            params.append(conflict_type)
        
        query += " ORDER BY id LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        rows = conn.execute(query, params).fetchall()
        
        return jsonify({
            'conflicts': [dict(row) for row in rows],
            'count': len(rows)
        })
    finally:
        conn.close()

@app.route('/api/marcus_network/<person_id>')
def api_marcus_network(person_id):
    """Get Marcus network for person"""
    conn = get_db()
    try:
        teachers = conn.execute("""
            SELECT teacher_id, teacher_label, ref
            FROM marcus_networks
            WHERE student_id = ?
        """, (person_id,)).fetchall()
        
        students = conn.execute("""
            SELECT student_id, student_label, ref
            FROM marcus_networks
            WHERE teacher_id = ?
        """, (person_id,)).fetchall()
        
        return jsonify({
            'person_id': person_id,
            'teachers': [dict(t) for t in teachers],
            'students': [dict(s) for s in students],
            'teacher_count': len(teachers),
            'student_count': len(students)
        })
    finally:
        conn.close()

@app.route('/api/resolve_conflict', methods=['POST'])
def api_resolve_conflict():
    """Resolve a conflict"""
    data = request.get_json()
    conflict_id = data.get('conflict_id')
    notes = data.get('notes', '')
    resolution = data.get('resolution', 'use_dila')
    
    conn = get_db()
    try:
        conn.execute("""
            UPDATE lineage_conflicts_v2
            SET resolved = 1, notes = ?
            WHERE id = ?
        """, (f"{notes} | Resolution: {resolution}", conflict_id))
        conn.commit()
        
        return jsonify({
            'status': 'ok',
            'conflict_id': conflict_id,
            'resolution': resolution
        })
    finally:
        conn.close()

@app.route('/api/marcus_stats')
def api_marcus_stats():
    """Get Marcus statistics"""
    conn = get_db()
    try:
        total = conn.execute("SELECT COUNT(*) FROM marcus_networks").fetchone()[0]
        teachers = conn.execute("SELECT COUNT(DISTINCT teacher_id) FROM marcus_networks").fetchone()[0]
        students = conn.execute("SELECT COUNT(DISTINCT student_id) FROM marcus_networks").fetchone()[0]
        
        conflicts = conn.execute("SELECT COUNT(*) FROM lineage_conflicts_v2 WHERE resolved = 0").fetchone()[0]
        
        return jsonify({
            'relations': total,
            'teachers': teachers,
            'students': students,
            'conflicts': conflicts
        })
    finally:
        conn.close()

@app.route('/api/health')
def api_health():
    return jsonify({'status': 'ok', 'time': datetime.now().isoformat()})

if __name__ == '__main__':
    print("Conflict API running on port 5002")
    app.run(host='0.0.0.0', port=5002, debug=False)