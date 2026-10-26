#!/usr/bin/env python3
"""
T415: Audit vn_person_authority — fix DILA ID mapping (1:N slugs)

Audit bảng vn_person_authority để tìm ánh xạ slug→dila_id sai (36 trường hợp N:1 gây self-loop ở T381) và 229 slug TTL thiếu dila_id.
Task chỉ liệt kê và trình Admin, không tự sửa dila_id theo tên.

Bản ghi chép audit sẵn sàng cho Build Agent.
"""

import sqlite3
import sys
import os
from datetime import datetime

# SSOT database path (tương tự như trong etl_ttl_person_authority.py)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_PATH = os.path.join(DATA_DIR, 'lineage.db')

def get_connection():
    """Mở kết nối SQLite read-only để audit."""
    conn = sqlite3.connect(f'file:{DB_PATH}?mode=ro', uri=True)
    conn.row_factory = sqlite3.Row
    return conn
def audit_n1_mapping(conn):
    """Audit N:1 mapping (nhiều slug → 1 dila_id) trong vn_person_authority.
    
    Returns:
        list: Các case N:1, mỗi case là dict với keys: dila_id, slug_count, slugs, sample_person_ids
    """
    print("=== Audit N:1 mapping (nhiều slug → 1 dila_id) ===")
    
    cursor = conn.execute('''
        SELECT 
            dila_id,
            COUNT(*) as slug_count,
            GROUP_CONCAT(id, ", ") as slugs,
            COUNT(*) as person_count
        FROM vn_person_authority
        WHERE dila_id IS NOT NULL AND dila_id != ""
        GROUP BY dila_id
        HAVING COUNT(*) > 1
        ORDER BY COUNT(*) DESC
    ''')
    
    n1_cases = []
    for row in cursor.fetchall():
        case = {
            'dila_id': row['dila_id'],
            'slug_count': row['slug_count'],
            'slugs': row['slugs'],
            'person_count': row['person_count']
        }
        n1_cases.append(case)
        
        print(f"dila_id {row['dila_id']}: {row['slug_count']} slugs")
        print(f"  Slugs: {row['slugs']}")
    
    print(f"\nTổng số case N:1: {len(n1_cases)}")
    return n1_cases
def audit_orphan_ttl_slugs(conn):
    """Audit các slug TTL thiếu dila_id.
    
    Returns:
        list: Các orphan TTL slugs, mỗi slug là dict với keys: person_id, name_vi, name_zh, 
              teacher_edges, student_edges, dila_id_status
    """
    print("\n=== Audit orphan TTL slugs (thiếu dila_id) ===")
    
    # Lấy danh sách các slug TTL có dila_id rỗng
    cursor = conn.execute('''
        SELECT 
            vpa.id as person_id,
            vpa.name_vi,
            vpa.name_zh,
            vpa.ttl_filename
        FROM vn_person_authority vpa
        WHERE (vpa.dila_id IS NULL OR vpa.dila_id = "")
        ORDER BY vpa.id
    ''')
    
    orphan_slugs = []
    for row in cursor.fetchall():
        slug_info = {
            'person_id': row['person_id'],
            'name_vi': row['name_vi'],
            'name_zh': row['name_zh'],
            'ttl_filename': row['ttl_filename'],
            'dila_id_status': 'NULL' if row['dila_id'] is None else 'empty'
        }
        orphan_slugs.append(slug_info)
        
        print(f"Slug {row['person_id']}: tên_vi='{row['name_vi']}', tên_zh='{row['name_zh']}', ttl_filename='{row['ttl_filename']}'")
    
    print(f"\nTổng số orphan TTL slugs: {len(orphan_slugs)}")
    return orphan_slugs
def check_dila_catalog_mapping(conn):
    """Kiểm tra bảng dila_catalog_people để hiểu relationship DILA ↔ people ID.
    
    Returns:
        list: Các mapping DILA ↔ people từ dila_catalog_people
    """
    print("\n=== Kiểm tra bảng dila_catalog_people ===")
    
    try:
        cursor = conn.execute('''
            SELECT * FROM dila_catalog_people
            ORDER BY dila_id
            LIMIT 50
        ''')
        
        catalog_mappings = []
        for row in cursor.fetchall():
            mapping = dict(row)
            catalog_mappings.append(mapping)
            print(f"dila_id: {mapping.get('dila_id')}, people_id: {mapping.get('people_id')}")
        
        print(f"Tìm thấy {len(catalog_mappings)} mapping trong dila_catalog_people")
        return catalog_mappings
        
    except sqlite3.OperationalError as e:
        print(f"Bảng dila_catalog_people không tồn tại hoặc có lỗi: {e}")
        return []
def analyze_specific_cases(n1_cases, catalog_mappings):
    """Phân tích các case N:1 cụ thể để xác định vấn đề.
    
    Returns:
        dict: Phân tích chi tiết các case N:1
    """
    print("\n=== Phân tích chi tiết các case N:1 ===")
    
    analysis = {}
    for case in n1_cases:
        dila_id = case['dila_id']
        slugs = case['slugs'].split(', ')
        
        print(f"\nPhân tích dila_id {dila_id} ({len(slugs)} slugs):")
        
        for slug in slugs:
            # Lấy thông tin đầy đủ của từng person
            cursor = conn.execute('''
                SELECT * FROM vn_person_authority 
                WHERE id = ?
            ''', (slug,))
            person_data = cursor.fetchone()
            
            if person_data:
                print(f"  - Slug {slug}:")
                print(f"    name_vi: {person_data['name_vi']}")
                print(f"    name_zh: {person_data['name_zh']}")
                print(f"    dila_id: {person_data['dila_id']}")
                print(f"    status: {person_data['status']}")
                print(f"    ttl_filename: {person_data['ttl_filename']}")
        
        analysis[dila_id] = {
            'slugs': slugs,
            'slug_count': case['slug_count']
        }
    
    return analysis
def main():
    """Hàm chính để thực hiện audit T415."""
    print(f"Bắt đầu T415 Audit - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Database: {DB_PATH}")
    print(f"Working directory: {os.getcwd()}")
    
    conn = get_connection()
    
    try:
        # Kiểm tra schema
        print("\n=== Kiểm tra schema bảng vn_person_authority ===")
        cursor = conn.execute('PRAGMA table_info(vn_person_authority)')
        schema = [row['name'] for row in cursor.fetchall()]
        print(f"Các cột: {schema}")
        
        # Audit N:1 mapping
        n1_cases = audit_n1_mapping(conn)
        
        # Audit orphan TTL slugs  
        orphan_slugs = audit_orphan_ttl_slugs(conn)
        
        # Kiểm tra bảng dila_catalog_people
        catalog_mappings = check_dila_catalog_mapping(conn)
        
        # Phân tích chi tiết các case
        analysis = analyze_specific_cases(n1_cases, catalog_mappings)
        
        # Xuất báo cáo audit
        print("\n=== Xuất báo cáo audit ===")
        output_file = f"docs/sessions/{datetime.now().strftime('%Y-%m-%d')}_T415_audit_report.txt"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# T415 Audit Report - vn_person_authority DILA ID Mapping\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"## Tóm tắt\n")
            f.write(f"- Tổng số case N:1: {len(n1_cases)}\n")
            f.write(f"- Tổng số orphan TTL slugs: {len(orphan_slugs)}\n")
            f.write(f"- Số mapping trong dila_catalog_people: {len(catalog_mappings)}\n\n")
            
            f.write(f"## Chi tiết các case N:1\n")
            for dila_id, info in analysis.items():
                f.write(f"### dila_id: {dila_id}\n")
                f.write(f"- Số slug: {info['slug_count']}\n")
                f.write(f"- Các slug: {', '.join(info['slugs'])}\n\n")
        
        print(f"Đã ghi báo cáo audit vào: {output_file}")
        
        # Trả về kết quả để Build Agent có thể sử dụng
        return {
            'n1_cases': n1_cases,
            'orphan_slugs': orphan_slugs,
            'catalog_mappings': catalog_mappings,
            'analysis': analysis,
            'report_file': output_file
        }
        
    finally:
        conn.close()
if __name__ == "__main__":
    try:
        result = main()
        print("\n✓ T415 Audit hoàn tất thành công!")
        print(f"- Phát hiện {len(result['n1_cases'])} case N:1")
        print(f"- Phát hiện {len(result['orphan_slugs'])} orphan TTL slugs")
        print(f"- Báo cáo đã được ghi: {result['report_file']}")
        
    except Exception as e:
        print(f"\n✗ Lỗi trong T415 Audit: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)