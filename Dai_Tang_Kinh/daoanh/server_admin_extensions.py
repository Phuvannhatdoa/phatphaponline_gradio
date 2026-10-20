# Admin Dashboard API Endpoints Extensions
# These endpoints are required for the admin dashboard to work

# ===================== STAGING & VERIFICATION APIs =====================

STAGING_FILE = os.path.join(DATA_DIR, 'staging.json')
VERIFICATION_FILE = os.path.join(DATA_DIR, 'verification.json')

def load_staging():
    """Load staging data"""
    if os.path.exists(STAGING_FILE):
        with open(STAGING_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"items": []}

def load_verification():
    """Load verification data"""
    if os.path.exists(VERIFICATION_FILE):
        with open(VERIFICATION_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"items": []}

@app.route('/api/admin/staging/list')
def admin_staging_list():
    """List Vietnam staging items (Local crawls)"""
    data = load_staging()
    items = data.get('items', [])
    return jsonify({
        "items": items,
        "total": len(items),
        "status": "ready"
    })

@app.route('/api/admin/verification/list')
def admin_verification_list():
    """List items needing global DILA verification"""
    data = load_verification()
    items = data.get('items', [])
    return jsonify({
        "items": items,
        "total": len(items),
        "status": "pending_global"
    })

@app.route('/api/admin/sources')
def admin_get_sources():
    """Get breakdown by source"""
    json_path = os.path.join(DATA_DIR, 'places.json')
    if not os.path.exists(json_path):
        return jsonify({"sources": []})
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    places = data.get('places', [])
    
    # Count by source
    sources = {}
    for place in places:
        source = place.get('source', 'Unknown')
        sources[source] = sources.get(source, 0) + 1
    
    return jsonify({
        "sources": [{"name": k, "count": v} for k, v in sources.items()]
    })

@app.route('/api/admin/dila-stats')
def admin_dila_stats():
    """Get DILA stats"""
    conn = get_db()
    try:
        total_people = conn.execute("SELECT COUNT(*) FROM people").fetchone()[0]
        total_places = conn.execute("SELECT COUNT(*) FROM places").fetchone()[0]
        
        # Count by dynasty
        dynasty_counts = conn.execute("""
            SELECT dynasty, COUNT(*) as cnt FROM people 
            WHERE dynasty IS NOT NULL AND dynasty != ''
            GROUP BY dynasty ORDER BY cnt DESC LIMIT 10
        """).fetchall()
        
        return jsonify({
            "total_people": total_people,
            "total_places": total_places,
            "dynasties": [{"name": r[0], "count": r[1]} for r in dynasty_counts]
        })
    finally:
        conn.close()

@app.route('/api/admin/places')
def admin_places():
    """Get places with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '')
    
    conn = get_db()
    try:
        offset = (page - 1) * per_page
        
        if search:
            query = """
                SELECT * FROM places 
                WHERE name LIKE ? OR name_vi LIKE ?
                LIMIT ? OFFSET ?
            """
            search_term = f"%{search}%"
            rows = conn.execute(query, (search_term, search_term, per_page, offset)).fetchall()
            total = conn.execute("""
                SELECT COUNT(*) FROM places 
                WHERE name LIKE ? OR name_vi LIKE ?
            """, (search_term, search_term)).fetchone()[0]
        else:
            query = "SELECT * FROM places LIMIT ? OFFSET ?"
            rows = conn.execute(query, (per_page, offset)).fetchall()
            total = conn.execute("SELECT COUNT(*) FROM places").fetchone()[0]
        
        return jsonify({
            "places": [dict(r) for r in rows],
            "total": total,
            "page": page,
            "per_page": per_page
        })
    finally:
        conn.close()

@app.route('/api/admin/places/<place_id>', methods=['PUT'])
def admin_update_place(place_id):
    """Update a place"""
    data = request.get_json()
    conn = get_db()
    try:
        conn.execute("""
            UPDATE places SET 
                name = COALESCE(?, name),
                name_vi = COALESCE(?, name_vi),
                gps_lat = COALESCE(?, gps_lat),
                gps_lng = COALESCE(?, gps_lng),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            data.get('name'),
            data.get('name_vi'),
            data.get('gps_lat'),
            data.get('gps_lng'),
            place_id
        ))
        conn.commit()
        return jsonify({"success": True, "place_id": place_id})
    finally:
        conn.close()

@app.route('/api/admin/person-stats')
def admin_person_stats():
    """Get person statistics"""
    conn = get_db()
    try:
        total = conn.execute("SELECT COUNT(*) FROM people").fetchone()[0]
        
        # Count by dynasty
        dynasty_counts = conn.execute("""
            SELECT dynasty, COUNT(*) as cnt FROM people 
            WHERE dynasty IS NOT NULL AND dynasty != ''
            GROUP BY dynasty ORDER BY cnt DESC
        """).fetchall()
        
        # Count monks vs non-monks
        is_monk = conn.execute("""
            SELECT is_monk, COUNT(*) FROM people GROUP BY is_monk
        """).fetchall()
        
        return jsonify({
            "total": total,
            "dynasties": [{"name": r[0], "count": r[1]} for r in dynasty_counts],
            "is_monk": [{"is_monk": r[0], "count": r[1]} for r in is_monk]
        })
    finally:
        conn.close()

# Enhancement for queue - load from TTL old directory
@app.route('/api/admin/queue/list')
def admin_queue_list():
    """List TTL files in old queue directory"""
    try:
        files = []
        if os.path.exists(TTL_OLD_DIR):
            for f in os.listdir(TTL_OLD_DIR):
                if f.endswith('.ttl'):
                    fpath = os.path.join(TTL_OLD_DIR, f)
                    files.append({
                        "filename": f,
                        "size": os.path.getsize(fpath),
                        "modified": os.path.getmtime(fpath)
                    })
        
        return jsonify({
            "queue": files,
            "total": len(files)
        })
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/admin/queue/', methods=['GET'])
def admin_get_ttl_file(filename):
    """Get a specific TTL file from queue"""
    filepath = os.path.join(TTL_OLD_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return jsonify({
        "filename": filename,
        "content": content
    })

# Enhanced stats endpoint  
@app.route('/api/admin/master-stats')
def admin_master_stats():
    """Get master statistics"""
    conn = get_db()
    try:
        # People stats
        total_people = conn.execute("SELECT COUNT(*) FROM people").fetchone()[0]
        
        # Places stats
        total_places = conn.execute("SELECT COUNT(*) FROM places").fetchone()[0]
        
        # Marc us network stats
        marcus_relations = conn.execute("SELECT COUNT(*) FROM marcus_networks").fetchone()[0]
        
        # Conflict stats
        unresolved_conflicts = conn.execute("SELECT COUNT(*) FROM lineage_conflicts_v2 WHERE resolved = 0").fetchone()[0]
        
        # TTL queue
        queue_count = len([f for f in os.listdir(TTL_OLD_DIR) if f.endswith('.ttl')])
        master_count = len([f for f in os.listdir(TTL_MASTER_DIR) if f.endswith('.ttl')])
        
        return jsonify({
            "people": total_people,
            "places": total_places,
            "marcus_relations": marcus_relations,
            "conflicts": unresolved_conflicts,
            "queue": queue_count,
            "resolved": master_count
        })
    finally:
        conn.close()