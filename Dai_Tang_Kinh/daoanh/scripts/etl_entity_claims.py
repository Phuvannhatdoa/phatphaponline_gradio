"""
scripts/etl_entity_claims.py — T23 Giai đoạn 1-3: Populate entity_claims

Phase 1: COORDINATE claims từ places_dila
Phase 2: NAME claims (ZH + VI) từ places_dila + namevi_map_places  
Phase 3: ADMIN_UNIT claims từ places_dila

Run: python scripts/etl_entity_claims.py
Hoặc: python scripts/etl_entity_claims.py --phase coord|name|admin

CẢNH BẢO:
- Backup lineage.db trước khi chạy ETL
- Sử dụng INSERT OR IGNORE → không overwrite dữ liệu đã có
- Tất cả entities qua entity_source_ids JOIN → chỉ claims có DILA source entity_id
"""
import sqlite3, sys, os, time
import argparse

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'lineage.db')

# Data sources registration (match data_sources table)
SOURCE_IDS = {
    'DILA': 1,
    'BDRC': 2,
    'CBETA': 3,
    'MARCUS': 4,
    'ZQLOCAL': 5,
}

VALID_CLAIM_TYPES = {'COORDINATE', 'NAME', 'ADMIN_UNIT', 'TEXTUAL_REF', 'TEMPORAL', 'EXTERNAL_ID'}
VALID_AUTHORITY_ROLES = {'PRIMARY', 'SUPPORTING', 'SECONDARY', 'CONTRIBUTOR'}
VALID_VERIFICATION_STATUS = {'unverified', 'candidate', 'verified', 'admin_verified'}


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def ensure_claims_table(conn):
    """Ensure entity_claims table exists with correct schema."""
    # Table already exists from prior creation - just verify schema
    # Columns expected: claim_id, entity_id, source_id, claim_type, subject, predicate,
    #   object_text, source_record_id, source_reference, authority_role, confidence,
    #   verification_status, editor_note, created_at, updated_at
    cur = conn.execute("PRAGMA table_info(entity_claims)")
    cols = [r[1] for r in cur.fetchall()]
    expected = ['claim_id', 'entity_id', 'source_id', 'claim_type', 'subject', 'predicate',
                'object_text', 'source_record_id', 'source_reference', 'authority_role',
                'confidence', 'verification_status', 'editor_note', 'created_at', 'updated_at']
    if cols != expected:
        print(f"Warning: Schema mismatch. Expected {expected}, got {cols}")
    else:
        print(f"Schema OK: {len(cols)} columns")


def backup_db():
    """Create backup before ETL runs."""
    import shutil
    bak_path = DB_PATH.replace('.db', f'.bak_{time.strftime("%Y%m%d_%H%M%S")}')
    try:
        shutil.copy2(DB_PATH, bak_path)
        print(f"Backup created: {bak_path}")
    except Exception as e:
        print(f"Warning: Could not create backup: {e}")


def phase_coordinate(conn):
    """Phase 1: COORDINATE claims từ places_dila."""
    print("\n=== Phase 1: COORDINATE claims từ places_dila ===")
    
    cur = conn.execute("""
        INSERT OR IGNORE INTO entity_claims 
        (entity_id, source_id, claim_type, subject, predicate, object_text, 
         source_record_id, source_reference, confidence, authority_role)
        SELECT DISTINCT e.entity_id, s.id, 'COORDINATE', 'hasCoordinate', 'coordinates', 
            CAST(p.geo_lat AS TEXT) || ',' || CAST(p.geo_long AS TEXT), p.id, 
            p.id, 1.0, 'PRIMARY'
        FROM entity_hub e
        JOIN entity_source_ids s ON e.entity_id = s.entity_id AND s.source = 'DILA'
        JOIN places_dila p ON p.id = s.source_entity_id
        WHERE p.geo_lat IS NOT NULL AND p.geo_long IS NOT NULL
    """)
    count = cur.rowcount
    print(f"  INSERTed COORDINATE claims: {count}")
    conn.commit()


def phase_names(conn):
    """Phase 2: NAME claims (ZH + VI) từ places_dila + namevi_map_places."""
    print("\n=== Phase 2: NAME claims từ places_dila + namevi_map_places ===")
    
    # Phase 2a: NAME_ZH claims từ places_dila
    cur_a = conn.execute("""
        INSERT OR IGNORE INTO entity_claims 
        (entity_id, source_id, claim_type, subject, predicate, object_text, 
         source_record_id, confidence, authority_role)
        SELECT DISTINCT e.entity_id, s.id, 'NAME', 'canonicalNameZh', p.name_zh, p.name_zh, 
            p.id, 0.95, 'PRIMARY'
        FROM entity_hub e
        JOIN entity_source_ids s ON e.entity_id = s.entity_id AND s.source = 'DILA'
        JOIN places_dila p ON p.id = s.source_entity_id
        WHERE p.name_zh IS NOT NULL AND p.name_zh != ''
    """)
    count_a = cur_a.rowcount
    print(f"  INSERTed NAME_ZH claims (from places_dila): {count_a}")
    
    # Phase 2b: NAME_VI claims từ namevi_map_places
    cur_b = conn.execute("""
        INSERT OR IGNORE INTO entity_claims 
        (entity_id, source_id, claim_type, subject, predicate, object_text, 
         source_record_id, confidence, authority_role)
        SELECT DISTINCT e.entity_id, s.id, 'NAME', 'vietnameseName', nv.name_vi, nv.name_vi, 
            nv.dila_id, 0.85, 'PRIMARY'
        FROM entity_hub e
        JOIN entity_source_ids s ON e.entity_id = s.entity_id AND s.source = 'DILA'
        JOIN namevi_map_places nv ON nv.dila_id = s.source_entity_id
        WHERE nv.name_vi IS NOT NULL AND nv.name_vi != ''
    """)
    count_b = cur_b.rowcount
    print(f"  INSERTed NAME_VI claims (from namevi_map_places): {count_b}")
    
    conn.commit()


def phase_admin_unit(conn):
    """Phase 3: ADMIN_UNIT claims từ places_dila.district."""
    print("\n=== Phase 3: ADMIN_UNIT claims từ places_dila ===")
    
    cur = conn.execute("""
        INSERT OR IGNORE INTO entity_claims 
        (entity_id, source_id, claim_type, subject, predicate, object_text, 
         source_record_id, confidence, authority_role)
        SELECT DISTINCT e.entity_id, s.id, 'ADMIN_UNIT', 'hasAdministrativeUnit', p.district, 
            p.district, p.id, 0.8, 'PRIMARY'
        FROM entity_hub e
        JOIN entity_source_ids s ON e.entity_id = s.entity_id AND s.source = 'DILA'
        JOIN places_dila p ON p.id = s.source_entity_id
        WHERE p.district IS NOT NULL AND p.district != ''
    """)
    count = cur.rowcount
    print(f"  INSERTed ADMIN_UNIT claims: {count}")
    conn.commit()


def main():
    parser = argparse.ArgumentParser(description='T23 ETL: Populate entity_claims')
    parser.add_argument('--phase', choices=['coord', 'name', 'admin', 'all'],
                        default='all', help='Chạy phase cụ thể')
    parser.add_argument('--backup', action='store_true',
                        help='Tạo backup DB trước khi chạy')
    args = parser.parse_args()
    
    # Backup nếu được yêu cầu
    if args.backup:
        backup_db()
    
    conn = get_db()
    
    # Ensure table exists (no-op if already exists)
    ensure_claims_table(conn)
    
    if args.phase == 'all':
        phase_coordinate(conn)
        phase_names(conn)
        phase_admin_unit(conn)
        print("\n=== Tổng kết ===")
        total = conn.execute("SELECT COUNT(*) FROM entity_claims").fetchone()[0]
        print(f"  Tổng entity_claims rows: {total}")
    elif args.phase == 'coord':
        phase_coordinate(conn)
    elif args.phase == 'name':
        phase_names(conn)
    elif args.phase == 'admin':
        phase_admin_unit(conn)
    
    conn.close()
    print("\nETL completed.")


if __name__ == '__main__':
    main()