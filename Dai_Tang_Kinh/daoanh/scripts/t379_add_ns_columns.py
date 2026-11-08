#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
T379 (rebuild-gen-tables follow-up) — Phương án A (Admin duyệt 2026-11-07):
thêm cột teacher_ns / disciple_ns (TEXT DEFAULT 'DILA') vào lineage_edge_consensus.

Additive thuần — KHÔNG rebuild bảng, KHÔNG UPDATE dòng cũ, KHÔNG DELETE.
Thiết kế đầy đủ: docs/design/T379-lineage-edge-consensus-ns-design.md §1-§2.

Khác biệt so với design doc (ghi rõ theo lệnh chốt cuối của Admin qua chat,
ưu tiên hơn bản doc): tên index UNIQUE là `idx_lec_ns_key` (không phải
`uq_lec_ns_key`), thứ tự cột (teacher_ns, disciple_ns, teacher_id,
disciple_id, relation_type) — không phải (teacher_ns, teacher_id,
disciple_ns, disciple_id, relation_type) như doc §1/§2 đề xuất. Giữ nguyên
UNIQUE constraint cũ (sqlite_autoindex trên teacher_id/disciple_id/
relation_type) song song, không rebuild bảng — đúng cả 2 bản (doc + lệnh
Admin) đồng ý điểm này.

Modes:
  --dry-run (MẶC ĐỊNH)  Chỉ đọc, in số liệu trước/DDL sẽ chạy, không ghi DB.
  --apply               Backup (shutil.copy2) -> ALTER TABLE ADD COLUMN x2
                         -> CREATE UNIQUE INDEX + 2 INDEX phụ, trong 1
                         transaction. PRAGMA quick_check sau commit.
  --revert              Additive rollback: DROP INDEX x3 + ALTER TABLE
                         DROP COLUMN x2 (SQLite >= 3.35). Từ chối nếu phát
                         hiện có dòng ns != 'DILA' (dữ liệu TTL_LOCAL thật đã
                         được insert bằng cột này) — khi đó phải restore từ
                         file backup, không DROP COLUMN (xem design doc §6
                         mục 5).

Phạm vi migration này (Bước 7, ràng buộc cứng từ Admin):
  - KHÔNG insert cạnh TTL_LOCAL mới nào.
  - Không đổi logic tính đời tự động.
  - Không đụng cây chính — chỉ chạy trong worktree.
"""

import argparse
import os
import shutil
import sqlite3
import sys
from datetime import datetime

DB_PATH = os.path.join('data', 'lineage.db')
BACKUP_DIR = os.path.join('data', 'backups')
TABLE = 'lineage_edge_consensus'

CHECK_TABLES = [
    'lineage_edge_consensus',
    'passage',
    'vn_person_relations',
    'dharma_pair_sources',
    'ai_person_name',
]

DDL_ADD_TEACHER_NS = (
    f"ALTER TABLE {TABLE} ADD COLUMN teacher_ns TEXT DEFAULT 'DILA'"
)
DDL_ADD_DISCIPLE_NS = (
    f"ALTER TABLE {TABLE} ADD COLUMN disciple_ns TEXT DEFAULT 'DILA'"
)
# Tên + thứ tự cột theo lệnh chốt cuối của Admin qua chat (xem docstring đầu file).
DDL_UNIQUE_INDEX = (
    f"CREATE UNIQUE INDEX IF NOT EXISTS idx_lec_ns_key "
    f"ON {TABLE}(teacher_ns, disciple_ns, teacher_id, disciple_id, relation_type)"
)
DDL_IDX_TEACHER_NS = (
    f"CREATE INDEX IF NOT EXISTS idx_lec_teacher_ns ON {TABLE}(teacher_ns, teacher_id)"
)
DDL_IDX_DISCIPLE_NS = (
    f"CREATE INDEX IF NOT EXISTS idx_lec_disciple_ns ON {TABLE}(disciple_ns, disciple_id)"
)

DDL_ALL = [DDL_ADD_TEACHER_NS, DDL_ADD_DISCIPLE_NS, DDL_UNIQUE_INDEX,
           DDL_IDX_TEACHER_NS, DDL_IDX_DISCIPLE_NS]


def now_stamp():
    return datetime.now().strftime('%Y%m%d_%H%M%S')


def open_ro(db_path):
    return sqlite3.connect('file:{}?mode=ro'.format(db_path.replace('\\', '/')), uri=True)


def table_counts(conn):
    out = {}
    for t in CHECK_TABLES:
        out[t] = conn.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
    return out


def has_ns_columns(conn):
    cols = [r[1] for r in conn.execute(f'PRAGMA table_info({TABLE})')]
    return 'teacher_ns' in cols and 'disciple_ns' in cols


def has_ns_index(conn):
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name=? AND name=?",
        (TABLE, 'idx_lec_ns_key')
    ).fetchone()
    return bool(rows)


def dry_run(db_path):
    conn = open_ro(db_path)
    try:
        before = table_counts(conn)
        cols_exist = has_ns_columns(conn)
        idx_exists = has_ns_index(conn)
        print('=== T379 ns-columns DRY-RUN (chỉ đọc, không ghi DB) ===')
        print(f'DB: {db_path}')
        print()
        print('Số dòng hiện tại (kỳ vọng Bước 2):')
        for t, n in before.items():
            print(f'  {t}: {n}')
        print()
        print(f'Cột teacher_ns/disciple_ns đã tồn tại: {cols_exist}')
        print(f'Index idx_lec_ns_key đã tồn tại: {idx_exists}')
        print()
        if cols_exist:
            dila_both = conn.execute(
                f"SELECT COUNT(*) FROM {TABLE} WHERE teacher_ns='DILA' AND disciple_ns='DILA'"
            ).fetchone()[0]
            non_dila = conn.execute(
                f"SELECT COUNT(*) FROM {TABLE} WHERE teacher_ns!='DILA' OR disciple_ns!='DILA'"
            ).fetchone()[0]
            print(f'  teacher_ns=DILA AND disciple_ns=DILA: {dila_both}')
            print(f'  teacher_ns!=DILA OR disciple_ns!=DILA: {non_dila}')
            print()
        print('DDL sẽ chạy khi --apply:')
        for ddl in DDL_ALL:
            print(f'  {ddl}')
        print()
        print('KHÔNG có bước UPDATE — 23411 dòng cũ nhận teacher_ns/disciple_ns=\'DILA\'')
        print('qua ALTER TABLE ... DEFAULT, không UPDATE riêng (rủi ro ghi sai = 0).')
        return before
    finally:
        conn.close()


def apply_db(db_path):
    if not os.path.exists(db_path):
        raise SystemExit(f'Không tìm thấy DB: {db_path}')

    before_conn = open_ro(db_path)
    before = table_counts(before_conn)
    before_conn.close()

    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = now_stamp()
    backup_path = os.path.join(BACKUP_DIR, f'lineage_pre_ns_{ts}.db')
    shutil.copy2(db_path, backup_path)
    print(f'[backup] {backup_path}')

    bconn = sqlite3.connect(backup_path)
    bqc = bconn.execute('PRAGMA quick_check').fetchone()[0]
    bconn.close()
    print(f'[backup] quick_check={bqc}')
    if bqc != 'ok':
        raise SystemExit('Backup quick_check KHÔNG ok — dừng, không ghi DB.')

    conn = sqlite3.connect(db_path)
    try:
        conn.execute('BEGIN')
        cols_exist = has_ns_columns(conn)
        if cols_exist:
            print(f'[skip] cột teacher_ns/disciple_ns đã tồn tại — bỏ qua 2 lệnh ADD COLUMN.')
        else:
            for ddl in (DDL_ADD_TEACHER_NS, DDL_ADD_DISCIPLE_NS):
                print('[DDL]', ddl)
                conn.execute(ddl)
        for ddl in (DDL_UNIQUE_INDEX, DDL_IDX_TEACHER_NS, DDL_IDX_DISCIPLE_NS):
            print('[DDL]', ddl)
            conn.execute(ddl)

        after = table_counts(conn)
        print()
        print('Kiểm tra số dòng SAU migration (phải khớp TRƯỚC — additive thuần):')
        mismatch = False
        for t in CHECK_TABLES:
            ok = after[t] == before[t]
            print(f'  {t}: before={before[t]} after={after[t]} {"OK" if ok else "MISMATCH"}')
            if not ok:
                mismatch = True

        dila_both = conn.execute(
            f"SELECT COUNT(*) FROM {TABLE} WHERE teacher_ns='DILA' AND disciple_ns='DILA'"
        ).fetchone()[0]
        non_dila = conn.execute(
            f"SELECT COUNT(*) FROM {TABLE} WHERE teacher_ns!='DILA' OR disciple_ns!='DILA'"
        ).fetchone()[0]
        print(f'  teacher_ns=DILA AND disciple_ns=DILA: {dila_both} (kỳ vọng = {before[TABLE]})')
        print(f'  teacher_ns!=DILA OR disciple_ns!=DILA: {non_dila} (kỳ vọng = 0)')
        if dila_both != before[TABLE] or non_dila != 0:
            mismatch = True

        if mismatch:
            print('MISMATCH phát hiện — ROLLBACK, giữ backup, không commit.')
            conn.rollback()
            conn.close()
            raise SystemExit(1)

        conn.commit()
    except SystemExit:
        raise
    except Exception:
        conn.rollback()
        conn.close()
        raise
    finally:
        if conn.in_transaction:
            conn.rollback()

    qc = conn.execute('PRAGMA integrity_check').fetchone()[0]
    print(f'PRAGMA integrity_check: {qc}')
    conn.close()
    if qc != 'ok':
        print('CẢNH BÁO: integrity_check KHÔNG ok sau commit — báo Admin ngay, '
              f'KHÔNG tự sửa thêm. Backup còn tại: {backup_path}')
        sys.exit(1)

    print()
    print('[apply] Hoàn tất. Backup giữ cho revert:', backup_path)
    return backup_path


def revert_additive(db_path):
    """DROP INDEX + DROP COLUMN — chỉ an toàn khi KHÔNG có dòng ns != 'DILA'."""
    conn = sqlite3.connect(db_path)
    try:
        if not has_ns_columns(conn):
            print('Cột teacher_ns/disciple_ns không tồn tại — không có gì để revert.')
            return
        non_dila = conn.execute(
            f"SELECT COUNT(*) FROM {TABLE} WHERE teacher_ns!='DILA' OR disciple_ns!='DILA'"
        ).fetchone()[0]
        if non_dila > 0:
            raise SystemExit(
                f'TỪ CHỐI revert additive: có {non_dila} dòng ns != DILA (dữ liệu '
                'TTL_LOCAL thật). DROP COLUMN sẽ làm mất khả năng phân biệt nguồn '
                'của các dòng này. Phải restore từ file backup toàn bộ thay vì chạy '
                '--revert (xem design doc §6 mục 5).'
            )
        conn.execute('BEGIN')
        for ddl in ('DROP INDEX IF EXISTS idx_lec_disciple_ns',
                    'DROP INDEX IF EXISTS idx_lec_teacher_ns',
                    'DROP INDEX IF EXISTS idx_lec_ns_key',
                    f'ALTER TABLE {TABLE} DROP COLUMN disciple_ns',
                    f'ALTER TABLE {TABLE} DROP COLUMN teacher_ns'):
            print('[DDL]', ddl)
            conn.execute(ddl)
        conn.commit()
        qc = conn.execute('PRAGMA integrity_check').fetchone()[0]
        print(f'PRAGMA integrity_check: {qc}')
    except SystemExit:
        conn.rollback()
        raise
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dry-run', action='store_true', help='chỉ đọc (mặc định)')
    ap.add_argument('--apply', action='store_true', help='GHI DB thật (có backup tự động)')
    ap.add_argument('--revert', action='store_true',
                     help='DROP cột/index đã thêm (additive rollback) — từ chối nếu đã có dữ liệu TTL_LOCAL')
    ap.add_argument('--db', default=DB_PATH, help='đường dẫn lineage.db')
    args = ap.parse_args()

    if args.revert:
        revert_additive(args.db)
        return

    if args.apply:
        apply_db(args.db)
        return

    dry_run(args.db)
    print()
    print('T379 ns-columns DRY-RUN — CHỈ ĐỌC, không ghi DB. Dùng --apply để ghi.')


if __name__ == '__main__':
    main()
