#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build 2 — Phase D: Đăng ký các nguồn Cross-Reference vào authority matrix
==========================================================================
Mục đích
--------
Nâng `source_authority` lên "matrix nguồn đầy đủ" bằng cách THÊM (additive) các nguồn
cross-reference còn thiếu theo queue của TGS Build 2 Phase D:
    SAT -> Kanripo -> SuttaCentral/VRI -> 84000 Toh -> CHGIS/TGAZ

Cụ thể:
1. Thêm dòng `data_sources` cho mọi nguồn trong matrix mà CHƯA có (SAT, CHGIS, FoJin,
   Kanripo, SuttaCentral, 84000, TGAZ) — để panel Evidence (Phase C) có thể hiển thị
   đầy đủ tên/type/license khi claim trỏ tới nguồn.
2. Thêm dòng `source_authority` cho các nguồn cross-ref MỚI (Kanripo, SuttaCentral,
   84000, TGAZ) với `implemented=0` (chưa có pipeline/data thật).
3. Đồng bộ `source_authority.source_id` từ `data_sources` (giống T68) nếu đang NULL.

NGUYÊN TẮC (tuân thủ Build 2 hard-rules)
-----------------------------------------
- ADDITIVE: chỉ THÊM dòng, KHÔNG sửa/xóa bảng nguồn, không đổi score dòng hiện có.
- IDEMPOTENT: INSERT OR IGNORE / UPDATE chỉ khi NULL — chạy lại không nhân đôi.
- REVERSIBLE: --undo xóa đúng các dòng build này thêm (dùng source_code bất biến).
- `implemented=0` — KHÔNG coi nguồn là đã tích hợp cho tới khi có pipeline + data thật.
- KHÔNG dùng wal_checkpoint/backup (bài học T58).

Cách dùng
---------
    python scripts/build2_register_crossref_sources.py              # đăng ký nếu chưa có
    python scripts/build2_register_crossref_sources.py --dry-run    # in ra sẽ làm gì
    python scripts/build2_register_crossref_sources.py --undo       # xóa các dòng build này thêm

Kiểm chứng
----------
    SELECT source_code, source_id, authority_score, precedence_order, implemented
    FROM source_authority ORDER BY precedence_order;
"""
import argparse
import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = r'data/lineage.db'

# Các nguồn cross-reference sẽ thêm vào `data_sources` (chỉ những nguồn CHƯA có).
# (source_id gán thủ công theo thứ tự tiếp sau MAX=6; ko autoincrement)
DATA_SOURCES = [
    # source_id, source_code, source_name, source_type, authority_scope, license_note, active
    (7,  'SAT',          'SAT Daizōkyō Text Database',            'crossref', 'han corpus',        'CC BY 4.0',  1),
    (8,  'CHGIS',        'China Historical GIS (Harvard)',        'gis',      'admin boundaries',  'Harvard',    1),
    (9,  'FoJin',        'FoJin 佛典',                             'crossref', 'han corpus',        'unknown',    1),
    (10, 'Kanripo',      'Kanripo Digital Archive of Buddhist Studies', 'crossref', 'han variants',  'CC BY-SA 4.0', 1),
    (11, 'SuttaCentral', 'SuttaCentral (Pali Canon)',             'crossref', 'pali canon',       'CC BY-NC-SA 4.0', 1),
    (12, '84000',        '84000 Translating the Words of the Buddha', 'crossref', 'tibetan canon', 'CC BY-NC-SA 4.0', 1),
    (13, 'TGAZ',         'TGAZ Harvard China Historical GIS Gazetteer', 'gis', 'historical gazetteer', 'Harvard', 1),
]

# Các dòng `source_authority` MỚI (implemented=0) cho nguồn cross-ref chưa có trong matrix.
# (source_code, authority_score, precedence_order, implemented, note)
AUTHORITY_ADD = [
    ('Kanripo',      70,  9, 0, 'Kanripo — Hán Tạng critical editions/variants; chưa implement (T34 GĐ B)'),
    ('TGAZ',         55, 10, 0, 'TGAZ Harvard Gazetteer API — chưa implement (phụ thuộc T21)'),
    ('SuttaCentral', 50, 11, 0, 'SuttaCentral — Pali Canon (thay VRI); chưa implement (T34 GĐ C)'),
    ('84000',        45, 12, 0, '84000 — Tibetan Canon Toh; chưa implement (T34 GĐ D)'),
]

# Các nguồn đã có trong `source_authority` (implemented=0) cần thêm dòng `data_sources`
# để nối source_id (SAT, CHGIS, FoJin đã có matrix nhưng chưa có data_sources).
AUTHORITY_LINK_ONLY = ['SAT', 'CHGIS', 'FoJin']


def connect():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def run(dry_run=False, undo=False):
    conn = connect()
    try:
        ds_cols = [d[1] for d in conn.execute('PRAGMA table_info(data_sources)')]
        sa_cols = [d[1] for d in conn.execute('PRAGMA table_info(source_authority)')]
        need = {'source_id', 'source_code', 'source_name', 'source_type', 'authority_scope',
                'license_note', 'active'}
        if not need.issubset(set(ds_cols)):
            print(f'[D] LỖI: data_sources thiếu cột {need - set(ds_cols)} — không đúng schema. Không làm gì.')
            return 1
        sa_need = {'source_code', 'source_id', 'authority_score', 'precedence_order', 'implemented', 'note'}
        if not sa_need.issubset(set(sa_cols)):
            print(f'[D] LỖI: source_authority thiếu cột {sa_need - set(sa_cols)} — không đúng schema.')
            return 1

        if undo:
            return do_undo(conn, dry_run)

        return do_apply(conn, dry_run)
    finally:
        conn.close()


def do_apply(conn, dry_run):
    print('=== [D] Đăng ký nguồn cross-reference (implemented=0 / additive / idempotent) ===')

    # 1) Thêm dòng data_sources cho mọi nguồn còn thiếu
    for sid, code, name, stype, scope, lic, active in DATA_SOURCES:
        exists = conn.execute('SELECT source_id FROM data_sources WHERE source_code=?', (code,)).fetchone()
        if exists:
            print(f'  [D][ok] data_sources đã có {code} (source_id={exists["source_id"]}) — bỏ qua (idempotent)')
            continue
        if dry_run:
            print(f'  [D][dry-run] sẽ thêm data_sources: source_id={sid}, code={code}, name={name}')
            continue
        conn.execute(
            'INSERT OR IGNORE INTO data_sources '
            '(source_id, source_code, source_name, source_type, authority_scope, license_note, active) '
            'VALUES (?,?,?,?,?,?,?)',
            (sid, code, name, stype, scope, lic, active),
        )
        conn.commit()
        print(f'  [D][+] đã thêm data_sources: source_id={sid}, code={code}')

    # 2) Thêm dòng source_authority MỚI (implemented=0)
    for code, score, order, imp, note in AUTHORITY_ADD:
        exists = conn.execute('SELECT precedence_order FROM source_authority WHERE source_code=?', (code,)).fetchone()
        if exists:
            print(f'  [D][ok] source_authority đã có {code} (order={exists["precedence_order"]}) — bỏ qua (idempotent)')
            continue
        if dry_run:
            print(f'  [D][dry-run] sẽ thêm source_authority: {code}, score={score}, order={order}, implemented={imp}')
            continue
        conn.execute(
            'INSERT OR IGNORE INTO source_authority '
            '(source_code, source_id, authority_score, precedence_order, implemented, note) '
            'VALUES (?,?,?,?,?,?)',
            (code, None, score, order, imp, note),
        )
        conn.commit()
        print(f'  [D][+] đã thêm source_authority: {code} (score={score}, order={order}, implemented=0)')

    # 3) Đồng bộ source_id từ data_sources nếu đang NULL (giống T68)
    if not dry_run:
        conn.execute("""
            UPDATE source_authority
            SET source_id = (SELECT ds.source_id FROM data_sources ds WHERE ds.source_code = source_authority.source_code)
            WHERE source_id IS NULL
              AND EXISTS (SELECT 1 FROM data_sources ds WHERE ds.source_code = source_authority.source_code)
        """)
        conn.commit()
        print('  [D][+] đã đồng bộ source_id cho các matrix-row có data_sources tương ứng.')

    print('--- source_authority tổng hợp (Phase D sau khi đăng ký) ---')
    for r in conn.execute("SELECT source_code, source_id, authority_score, precedence_order, implemented "
                          "FROM source_authority ORDER BY precedence_order"):
        print(f'    {r[0]:<14} source_id={r[1]} score={r[2]:<3} order={r[3]} implemented={r[4]}')
    return 0


def do_undo(conn, dry_run):
    print('=== [D] UNDO — gỡ các dòng build Phase D đã thêm ===')
    # Xóa data_sources các nguồn do build này thêm (chỉ nếu chúng chưa có trước Phase D — source_id>=7 do build này đặt)
    for sid, code, name, stype, scope, lic, active in DATA_SOURCES:
        row = conn.execute('SELECT source_id FROM data_sources WHERE source_code=?', (code,)).fetchone()
        if row and row['source_id'] == sid:
            if dry_run:
                print(f'  [D][dry-run] sẽ xóa data_sources: source_id={sid}, code={code}')
            else:
                conn.execute('DELETE FROM data_sources WHERE source_id=?', (sid,))
                conn.commit()
                print(f'  [D][-] đã xóa data_sources: source_id={sid}, code={code}')
        else:
            print(f'  [D][ok] data_sources {code} (source_id={row["source_id"] if row else None}) ≠ {sid} — không xóa (an toàn)')

    # Xóa các dòng source_authority mới thêm (implemented cho nguồn cross-ref mới)
    for code, score, order, imp, note in AUTHORITY_ADD:
        row = conn.execute('SELECT precedence_order FROM source_authority WHERE source_code=?', (code,)).fetchone()
        if row and row['precedence_order'] == order:
            if dry_run:
                print(f'  [D][dry-run] sẽ xóa source_authority: {code}')
            else:
                conn.execute('DELETE FROM source_authority WHERE source_code=?', (code,))
                conn.commit()
                print(f'  [D][-] đã xóa source_authority: {code}')
        else:
            print(f'  [D][ok] source_authority {code} order={row["precedence_order"] if row else None} ≠ {order} — không xóa (an toàn)')
    # Reset source_id về NULL cho các nguồn link-only (SAT/CHGIS/FoJin) — vốn NULL trước Phase D.
    # Khi data_sources rows bị xóa, không để source_authority trỏ tới dòng không còn tồn tại.
    for code in AUTHORITY_LINK_ONLY:
        row = conn.execute('SELECT source_id FROM source_authority WHERE source_code=?', (code,)).fetchone()
        if row and row['source_id'] is not None:
            if dry_run:
                print(f'  [D][dry-run] sẽ reset source_authority.{code}.source_id → NULL')
            else:
                conn.execute("UPDATE source_authority SET source_id = NULL WHERE source_code = ?", (code,))
                conn.commit()
                print(f'  [D][-] đã reset source_authority.{code}.source_id → NULL')
        else:
            print(f'  [D][ok] source_authority.{code}.source_id đã NULL — không đổi (an toàn)')
    print('[D] UNDO xong — đã trả về trạng thái trước Phase D (các dòng do build này thêm).')
    return 0


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Đăng ký nguồn cross-ref vào authority matrix (Phase D)')
    ap.add_argument('--dry-run', action='store_true', help='chỉ in ra, không thay đổi DB')
    ap.add_argument('--undo', action='store_true', help='gỡ các dòng build Phase D đã thêm (revert)')
    args = ap.parse_args()
    sys.exit(run(dry_run=args.dry_run, undo=args.undo))
