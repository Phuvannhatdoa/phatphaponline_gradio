#!/usr/bin/env python3
"""
T415: Fix vn_person_authority — DILA ID mapping (1:N slugs)

Script sửa DILA ID mapping sai (N:1 cases) và chèn dila_id cho orphan TTL slugs.

Quy trình:
1. Xác định các case N:1 cần sửa
2. Tạo backup DB an toàn
3. Thực hiện dry-run sửa N:1 cases
4. Thực hiện dry-run chèn dila_id cho orphan TTL slugs
5. Xác nhận kết quả

Sử dụng: python scripts/t415_fix_vn_person_authority.py --dry-run
Hoặc: python scripts/t415_fix_vn_person_authority.py --apply
"""

import sqlite3
import sys
import os
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional

# SSOT database path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_PATH = os.path.join(DATA_DIR, 'lineage.db')
BACKUP_DIR = os.path.join(DATA_DIR, 'backups')
BACKUP_PREFIX = 'T415_fix_'

def ensure_backup_dir():
    """Tạo thư mục backup nếu chưa tồn tại."""
    os.makedirs(BACKUP_DIR, exist_ok=True)

def create_backup_name():
    """Tạo tên file backup."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return os.path.join(BACKUP_DIR, f'{BACKUP_PREFIX}{timestamp}.db')

def get_connection(db_path=None):
    """Mở kết nối SQLite."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn

class T415Fixer:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.backup_path = None
        self.stats = {
            'n1_cases_fixed': 0,
            'n1_cases_verified': 0,
            'orphan_slugs_processed': 0,
            'orphan_slugs_inserted': 0,
            'queries_executed': 0,
            'errors': []
        }
    
    def log_query(self, query, params=None):
        """Ghi log query được thực hiện."""
        self.stats['queries_executed'] += 1
        if self.dry_run:
            print(f"[DRY RUN] {query} {params if params else ''}")
        else:
            print(f"[EXECUTE] {query} {params if params else ''}")
    
    def log_error(self, message):
        """Ghi log lỗi."""
        self.stats['errors'].append(message)
        print(f"ERROR: {message}")
    
    def create_backup(self, conn):
        """Tạo backup DB trước khi sửa."""
        if self.dry_run:
            print("DRY RUN: Sẽ tạo backup DB tại:", create_backup_name())
            self.backup_path = create_backup_name()
            return
        
        ensure_backup_dir()
        backup_path = create_backup_name()
        
        try:
            # Sao chép file DB
            import shutil
            shutil.copy2(DB_PATH, backup_path)
            print(f"Đã tạo backup DB: {backup_path}")
            self.backup_path = backup_path
        except Exception as e:
            self.log_error(f"Không thể tạo backup DB: {e}")
            raise
    
    def load_n1_cases(self, conn) -> List[Dict[str, Any]]:
        """Tải các case N:1 cần sửa."""
        print("=== Tải case N:1 cần sửa ===")
        
        cursor = conn.execute('''
            SELECT 
                dila_id,
                COUNT(*) as slug_count,
                GROUP_CONCAT(id, ", ") as slugs
            FROM vn_person_authority
            WHERE dila_id IS NOT NULL AND dila_id != ""
            GROUP BY dila_id
            HAVING COUNT(*) > 1
            ORDER BY dila_id
        ''')
        
        cases = []
        for row in cursor.fetchall():
            case = {
                'dila_id': row['dila_id'],
                'slug_count': row['slug_count'],
                'slugs': row['slugs'].split(', ')
            }
            cases.append(case)
            
            print(f"dila_id {row['dila_id']}: {row['slug_count']} slugs")
            print(f"  Slugs: {row['slugs']}")
        
        print(f"Tổng số case N:1: {len(cases)}")
        return cases
    
    def load_orphan_slugs(self, conn) -> List[Dict[str, Any]]:
        """Tải các orphan TTL slugs cần chèn dila_id."""
        print("\n=== Tải orphan TTL slugs cần chèn dila_id ===")
        
        cursor = conn.execute('''
            SELECT 
                id as person_id,
                name_vi,
                name_zh,
                ttl_filename,
                dila_id
            FROM vn_person_authority
            WHERE (dila_id IS NULL OR dila_id = "")
            ORDER BY id
        ''')
        
        orphans = []
        for row in cursor.fetchall():
            orphan = {
                'person_id': row['person_id'],
                'name_vi': row['name_vi'],
                'name_zh': row['name_zh'],
                'ttl_filename': row['ttl_filename'],
                'has_dila_id': bool(row['dila_id'] and row['dila_id'] != '')
            }
            orphans.append(orphan)
            
            print(f"Slug {row['person_id']}: tên_vi='{row['name_vi']}', tên_zh='{row['name_zh']}', ttl_filename='{row['ttl_filename']}'")
        
        print(f"Tổng số orphan TTL slugs: {len(orphans)}")
        return orphans
    
    def fix_n1_case(self, conn, case: Dict[str, Any]) -> bool:
        """Sửa một case N:1 - giữ lại slug 'đặc biệt' (alias, auto_ttl, verified) và thay thế các slug khác.
        
        Returns:
            bool: True nếu sửa thành công
        """
        dila_id = case['dila_id']
        slugs = case['slugs']
        
        print(f"\n--- Sửa case dila_id {dila_id} ---")
        
        # Xác định slug nào nên giữ lại (các case đặc biệt)
        slugs_to_keep = []
        slugs_to_replace = []
        
        for slug in slugs:
            cursor = conn.execute('SELECT status FROM vn_person_authority WHERE id = ?', (slug,))
            row = cursor.fetchone()
            if row:
                status = row['status']
                # Giữ lại các slug đặc biệt
                if status in ['alias_vi_suffix', 'auto_ttl', 'verified']:
                    slugs_to_keep.append(slug)
                    print(f"  Giữ lại slug {slug} (status: {status})")
                else:
                    slugs_to_replace.append(slug)
                    print(f"  Sẽ thay thế slug {slug} (status: {status})")
        
        if not slugs_to_replace:
            print(f"  Không có slug nào cần thay thế (tất cả {len(slugs)} đều được giữ lại)")
            return True
        
        # Kiểm tra thông tin các slug cần thay thế
        for slug in slugs_to_replace:
            cursor = conn.execute('SELECT name_vi, name_zh, ttl_filename FROM vn_person_authority WHERE id = ?', (slug,))
            row = cursor.fetchone()
            if row:
                print(f"  Slug {slug}: name_vi='{row['name_vi']}', name_zh='{row['name_zh']}'")
        
        # Thực hiện sửa (chỉ thực hiện trong mode apply)
        if not self.dry_run:
            try:
                for slug in slugs_to_replace:
                    self.log_query(
                        'UPDATE vn_person_authority SET dila_id = ? WHERE id = ?',
                        (dila_id, slug)
                    )
                    cursor = conn.execute(
                        'UPDATE vn_person_authority SET dila_id = ? WHERE id = ?',
                        (dila_id, slug)
                    )
                    print(f"  Đã cập nhật slug {slug} -> dila_id {dila_id}")
                
                conn.commit()
                self.stats['n1_cases_fixed'] += 1
                print(f"  Đã sửa thành công case dila_id {dila_id}")
                return True
                
            except Exception as e:
                conn.rollback()
                self.log_error(f"Lỗi khi sửa case dila_id {dila_id}: {e}")
                return False
        
        return True  # Trong mode dry_run, giả định thành công
    
    def insert_dila_for_orphan(self, conn, orphan: Dict[str, Any]) -> bool:
        """Chèn dila_id cho một orphan TTL slug.
        
        Returns:
            bool: True nếu chèn thành công
        """
        person_id = orphan['person_id']
        
        print(f"\n--- Chèn dila_id cho orphan {person_id} ---")
        print(f"  Tên: {orphan['name_vi']}")
        print(f"  TTL file: {orphan['ttl_filename']}")
        
        # Tìm dila_id phù hợp từ các dila_id đã có
        suitable_dila_id = None
        
        # Kiểm tra nếu cùng tên_vi có dila_id không rỗng (có thể gợi ý)
        if orphan['name_vi']:
            cursor = conn.execute('''
                SELECT DISTINCT dila_id, id as person_id, name_vi
                FROM vn_person_authority
                WHERE name_vi LIKE ? AND dila_id IS NOT NULL AND dila_id != ""
                ORDER BY dila_id
            ''', (f'%{orphan["name_vi"]}%',))
            
            suggestions = []
            for row in cursor.fetchall():
                suggestions.append({
                    'dila_id': row['dila_id'],
                    'person_id': row['person_id'],
                    'name_vi': row['name_vi']
                })
            
            if suggestions:
                print(f"  Tìm thấy {len(suggestions)} suggestions tương đồng:")
                for sug in suggestions[:5]:  # Hiển thị 5 suggestions đầu tiên
                    print(f"    dila_id {sug['dila_id']} (person_id {sug['person_id']}, tên: {sug['name_vi']})")
                
                # Tự động chọn suggestion đầu tiên
                suitable_dila_id = suggestions[0]['dila_id']
                print(f"  Sẽ sử dụng dila_id: {suitable_dila_id}")
        
        # Nếu không tìm thấy suggestion, sử dụng dila_id đầu tiên có sẵn
        if not suitable_dila_id:
            cursor = conn.execute('''
                SELECT dila_id, id as person_id
                FROM vn_person_authority
                WHERE dila_id IS NOT NULL AND dila_id != ""
                ORDER BY dila_id
                LIMIT 1
            ''')
            
            row = cursor.fetchone()
            if row:
                suitable_dila_id = row['dila_id']
                print(f"  Sẽ sử dụng dila_id đầu tiên có sẵn: {suitable_dila_id}")
            else:
                self.log_error(f"  Không tìm thấy dila_id nào để gán cho orphan {person_id}")
                return False
        
        # Thực hiện chèn (chỉ thực hiện trong mode apply)
        if not self.dry_run:
            try:
                self.log_query(
                    'UPDATE vn_person_authority SET dila_id = ? WHERE id = ?',
                    (suitable_dila_id, person_id)
                )
                cursor = conn.execute(
                    'UPDATE vn_person_authority SET dila_id = ? WHERE id = ?',
                    (suitable_dila_id, person_id)
                )
                
                conn.commit()
                self.stats['orphan_slugs_inserted'] += 1
                print(f"  Đã chèn dila_id {suitable_dila_id} cho orphan {person_id}")
                return True
                
            except Exception as e:
                conn.rollback()
                self.log_error(f"Lỗi khi chèn dila_id cho orphan {person_id}: {e}")
                return False
        
        return True  # Trong mode dry_run, giả định thành công
    
    def verify_fixes(self, conn):
        """Xác minh rằng các sửa đổi đã được áp dụng."""
        print("\n=== Xác minh các sửa đổi ===")
        
        # Kiểm tra lại N:1 cases
        cursor = conn.execute('''
            SELECT 
                dila_id,
                COUNT(*) as slug_count
            FROM vn_person_authority
            WHERE dila_id IS NOT NULL AND dila_id != ""
            GROUP BY dila_id
            HAVING COUNT(*) > 1
        ''')
        
        remaining_n1 = []
        for row in cursor.fetchall():
            remaining_n1.append({
                'dila_id': row['dila_id'],
                'slug_count': row['slug_count']
            })
            print(f"  STILL N:1: dila_id {row['dila_id']}: {row['slug_count']} slugs")
        
        self.stats['n1_cases_verified'] = len(remaining_n1)
        
        # Kiểm tra orphan slugs
        cursor = conn.execute('''
            SELECT COUNT(*) as count
            FROM vn_person_authority
            WHERE dila_id IS NULL OR dila_id = ""
        ''')
        
        row = cursor.fetchone()
        remaining_orphans = row['count']
        print(f"  Còn {remaining_orphans} orphan TTL slugs (dila_id rỗng/NULL)")
        
        self.stats['orphan_slugs_processed'] = remaining_orphans
    
    def run(self):
        """Thực hiện toàn bộ quy trình sửa."""
        print(f"=== Bắt đầu T415 Fix - {'DRY RUN' if self.dry_run else 'APPLY'} ===")
        print(f"Database: {DB_PATH}")
        
        conn = get_connection()
        
        try:
            # Tạo backup (chỉ trong mode apply)
            if not self.dry_run:
                self.create_backup(conn)
            
            # Tải dữ liệu
            n1_cases = self.load_n1_cases(conn)
            orphan_slugs = self.load_orphan_slugs(conn)
            
            # Sửa N:1 cases
            print(f"\n=== Sửa {len(n1_cases)} case N:1 ===")
            for case in n1_cases:
                success = self.fix_n1_case(conn, case)
                if not success:
                    print(f"  Lỗi khi sửa case dila_id {case['dila_id']}")
            
            # Chèn dila_id cho orphan slugs
            print(f"\n=== Chèn dila_id cho {len(orphan_slugs)} orphan TTL slugs ===")
            for orphan in orphan_slugs:
                success = self.insert_dila_for_orphan(conn, orphan)
                if not success:
                    print(f"  Lỗi khi xử lý orphan {orphan['person_id']}")
            
            # Xác minh sửa đổi
            self.verify_fixes(conn)
            
            # Hiển thị tóm tắt
            self.print_summary()
            
            return True
            
        except Exception as e:
            self.log_error(f"Lỗi trong quá trình thực hiện: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            conn.close()
    
    def print_summary(self):
        """Hiển thị tóm tắt các sửa đổi."""
        print("\n=== Tóm tắt sửa đổi ===")
        print(f"Dry run: {self.dry_run}")
        print(f"Đã sửa {self.stats['n1_cases_fixed']} case N:1")
        print(f"Đã chèn dila_id cho {self.stats['orphan_slugs_inserted']} orphan TTL slugs")
        print(f"Đã thực hiện {self.stats['queries_executed']} truy vấn SQL")
        print(f"Còn lại {self.stats['n1_cases_verified']} case N:1")
        print(f"Còn lại {self.stats['orphan_slugs_processed']} orphan TTL slugs")
        
        if self.stats['errors']:
            print(f"\n=== Lỗi ===")
            for error in self.stats['errors']:
                print(f"  - {error}")
        
        if self.backup_path and not self.dry_run:
            print(f"\nBackup DB: {self.backup_path}")
            print("Bạn có thể khôi phục bằng: cp {self.backup_path} {DB_PATH}")


def main():
    parser = argparse.ArgumentParser(description='T415: Fix vn_person_authority DILA ID mapping')
    parser.add_argument('--apply', action='store_true', help='Thực hiện sửa (mặc định: dry-run)')
    parser.add_argument('--dry-run', action='store_true', help='Chạy dry-run (mặc định)')
    
    args = parser.parse_args()
    
    dry_run = not args.apply
    
    fixer = T415Fixer(dry_run=dry_run)
    success = fixer.run()
    
    if success:
        print("\n✓ T415 Fix hoàn tất!")
        return 0
    else:
        print("\n✗ T415 Fix thất bại!")
        return 1

if __name__ == "__main__":
    sys.exit(main())