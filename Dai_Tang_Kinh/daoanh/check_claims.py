import sqlite3

conn = sqlite3.connect('data/lineage.db')

# Check if entity_claims exists
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='entity_claims'").fetchone()
print(f'entity_claims exists: {tables is not None}')

# Try creating via individual executes
try:
    conn.execute('''CREATE TABLE IF NOT EXISTS entity_claims 
        (claim_id INTEGER PRIMARY KEY AUTOINCREMENT, 
        entity_id INTEGER NOT NULL, 
        source_id INTEGER NOT NULL, 
        claim_type TEXT NOT NULL, 
        subject TEXT, 
        predicate TEXT, 
        object_text TEXT, 
        source_record_id TEXT, 
        source_reference TEXT, 
        authority_role TEXT DEFAULT "supporting", 
        confidence REAL DEFAULT 1.0, 
        verification_status TEXT DEFAULT "unverified", 
        editor_note TEXT, 
        created_at TEXT DEFAULT datetime("now"), 
        updated_at TEXT DEFAULT datetime("now"), 
        UNIQUE(entity_id, source_id, claim_type, source_record_id))''')
    print('Table created via individual execute')
except Exception as e:
    print(f'Error: {e}')

# Try the simpler approach - just check if column exists
cur = conn.execute('PRAGMA table_info(entity_claims)')
cols = [r[1] for r in cur.fetchall()]
print(f'Columns: {cols}')

conn.close()