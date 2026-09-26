#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETL T100 Batch 4 (P2-MASTER) — schema additive cho khối GIÁO LÝ phân đôi
==========================================================================
Làm TRƯỚC khi sửa app.py/places.html để route mới có bảng để đọc.

Tính chất
---------
- ADDITIVE: chỉ CREATE TABLE (bảng mới) + ALTER TABLE ADD COLUMN (cột mới).
  KHÔNG đổi/drop cột cũ, KHÔNG đụng dữ liệu existing entity_claims (447,885 rows).
- IDEMPOTENT: chạy lại nhiều lần không lỗi/nhân đôi (guard PRAGMA + upsert ON CONFLICT).
- REVERSIBLE: `--revert` chỉ DROP bảng mới + DROP 3 cột vừa thêm + restore seed, có backup.
- BACKUP: tự copy `data/lineage.db` → `data/backups/lineage_b4_<timestamp>.db` khi `--apply`.

Cách dùng
---------
    python scripts/etl_t100_batch4.py --dry-run   # chỉ in kế hoạch, không đổi DB
    python scripts/etl_t100_batch4.py --apply     # CREATE + ALTER + seed (có backup)
    python scripts/etl_t100_batch4.py --revert    # DROP bảng mới + 3 cột mới (giữ backup)

Output schema
-------------
1) `pali_cbeta_map`         (sh TEXT PK, pali_title, sc_uid, pts_sutta, note)
   — rút hardcode `_PALI_REF_MAP` (app.py:14122) ra bảng; consumer `api_cbeta_compare`.
2) `doctrine_concept`       (id PK, name_vi, name_zh, pth_uri, definition_vi,
                             related_entities, assertion_level, updated_at)
   — whitelist KHÁI NIỆM GIÁO LÝ (R2: không trộn glossary 248K; THEMATIC badge).
3) `entity_claims` + cột    assertion_level / reviewed_by / reviewed_at (additive).
"""
import argparse
import os
import shutil
import sqlite3
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'lineage.db')
BACKUP_DIR = os.path.join(BASE_DIR, 'data', 'backups')

# ── dữ liệu seed 1: rút từ _PALI_REF_MAP (app.py:14122-14129) — key = forms['sh'] zfill(4)
PALI_REF_SEED = [
    ('0251', 'Prajñāpāramitā Hṛdaya', '', '', 'Tâm Kinh — không có tương đương Pali Nikāya trực tiếp; tham chiếu Bát Nhã Hán tạng (đoạn) + Pali tương tự AN 9.14 (cấu trúc tụng niệm)'),
    ('0235', 'Vajracchedikā Prajñāpāramitā', '', '', 'Kim Cang Kinh — không có tương đương Pali Nikāya trực tiếp; gần nhất về đề tài: AN 7.64 (Vajraupama)'),
    ('0262', 'Saddhammapuṇḍarīka', '', '', 'Pháp Hoa Kinh — không có tương đương Pali trực tiếp'),
    ('0209', 'Satipaṭṭhāna Sutta', 'mn10', 'MN 10', 'Kinh Niệm Xứ — song song trực tiếp Pali MN 10'),
    ('0222', 'Mahāsatipaṭṭhāna Sutta', 'dn22', 'DN 22', 'Kinh Đại Niệm Xứ — song song Pali DN 22'),
    ('0221', 'Mahāsatipaṭṭhāna / DN 22 (song)', '', '', ''),
]

# ── dữ liệu seed 2: whitelist KHÁI NIỆM GIÁO LÝ core (THEMATIC) — R2: không hút glossary
DOCTRINE_SEED = [
    ('Tứ Diệu Đế', '四聖諦', 'pth:tu-dieu-de',
     'Bốn chân lý: Khổ, Tập, Diệt, Đạo — nền tảng giáo lý nguyên thủy.',
     'Bát Chính Đạo, Duyệt khổ, Niết Bàn', 'THEMATIC'),
    ('Bát Chính Đạo', '八正道', 'pth:bat-chinh-dao',
     'Tám chi phần con đường diệt khổ: Chánh kiến, Chánh tư duy, Chánh ngữ, Chánh nghiệp, Chánh mạng, Chánh tinh tấn, Chánh niệm, Chánh định.',
     'Tứ Diệu Đế, Thiền định', 'THEMATIC'),
    ('Duyên Khởi', '緣起', 'pth:duyen-khoi',
     'Mọi hiện tượng sinh khởi tùy thuộc nhân duyên — chuỗi 12 chi phần.',
     'Vô Ngã, Vô Thường', 'THEMATIC'),
    ('Ngũ Uẩn', '五蘊', 'pth:ngu-uan',
     'Năm nhóm cấu thành con người: Sắc, Thọ, Tưởng, Hành, Thức.',
     'Vô Ngã, Sắc Không', 'THEMATIC'),
    ('Vô Ngã', '無我', 'pth:vo-nga',
     'Không có bản ngã thường hằng — quán chiếu qua Ngũ Uẩn.',
     'Duyên Khởi, Ngũ Uẩn', 'THEMATIC'),
    ('Vô Thường', '無常', 'pth:vo-thuong',
     'Mọi pháp hữu vi đều biến đổi, không tồn tại mãi.',
     'Vô Ngã, Khổ', 'THEMATIC'),
    ('Niết Bàn', '涅槃', 'pth:niet-ban',
     'Diệt tận khổ đau và tham ái — mục tiêu giải thoát cuối cùng.',
     'Tứ Diệu Đế, Khổ', 'THEMATIC'),
    ('Nghiệp', '業', 'pth:nghiep',
     'Hành động có chủ tâm tạo quả tương ứng — luật nhân quả đạo đức.',
     'Luân Hồi, Nhân Quả', 'THEMATIC'),
    ('Luân Hồi', '輪迴', 'pth:luan-hoi',
     'Vòng sinh tử lặp lại do nghiệp và vô minh dẫn dắt.',
     'Nghiệp, Giải Thoát', 'THEMATIC'),
    ('Tánh Không', '性空', 'pth:tanh-khong',
     'Bát Nhã — các pháp không có tự tánh cố định; liên hệ Bát Nhã tâm kinh.',
     'Bát Nhã, Huyền Trang', 'THEMATIC'),
    ('Bồ Đề Tâm', '菩提心', 'pth:bo-de-tam',
     'Nguyện cầu giác ngộ vì lợi ích chúng sinh — nền tảng Đại thừa.',
     'Bồ Tát Đạo, Từ Bi', 'THEMATIC'),
    ('Từ Bi', '慈悲', 'pth:tu-bi',
     'Nguyện đem vui, cứu khổ cho chúng sinh — hạnh Bồ Tát.',
     'Bồ Đề Tâm, Bồ Tát Đạo', 'THEMATIC'),
]


def connect():
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.row_factory = sqlite3.Row
    return conn


def has_table(conn, name):
    r = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone()
    return r is not None


def has_column(conn, table, col):
    return col in {r[1] for r in conn.execute(f'PRAGMA table_info({table})')}


def make_backup(dry_run):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = time.strftime('%Y%m%d_%H%M%S')
    dst = os.path.join(BACKUP_DIR, f'lineage_b4_{ts}.db')
    if dry_run:
        print(f'[backup][dry-run] Sẽ copy {DB_PATH} → {dst}')
        return None
    if not os.path.exists(DB_PATH):
        print(f'[backup] KHÔNG tìm thấy {DB_PATH} — bỏ qua backup')
        return None
    shutil.copy2(DB_PATH, dst)
    print(f'[backup] Đã backup → {dst} ({os.path.getsize(dst):,} bytes)')
    return dst


def create_pali_cbeta_map(conn, dry_run):
    if has_table(conn, 'pali_cbeta_map'):
        print('[pali_cbeta_map] bảng đã có — bỏ qua create (idempotent).')
    else:
        if dry_run:
            print('[pali_cbeta_map][dry-run] Sẽ CREATE TABLE pali_cbeta_map (sh PK, pali_title, sc_uid, pts_sutta, note)')
        else:
            conn.execute("""
                CREATE TABLE pali_cbeta_map (
                    sh TEXT PRIMARY KEY,
                    pali_title TEXT,
                    sc_uid TEXT,
                    pts_sutta TEXT,
                    note TEXT
                )
            """)
            print('[pali_cbeta_map] Đã CREATE TABLE.')

    n = conn.execute("SELECT COUNT(*) FROM pali_cbeta_map").fetchone()[0] if has_table(conn, 'pali_cbeta_map') else 0
    if dry_run:
        print(f'[pali_cbeta_map][dry-run] Sẽ upsert {len(PALI_REF_SEED)} record (hiện có {n}).')
        return
    if not has_table(conn, 'pali_cbeta_map'):
        return
    # upsert idempotent — chạy lại không nhân đôi
    conn.executemany(
        "INSERT INTO pali_cbeta_map (sh, pali_title, sc_uid, pts_sutta, note) VALUES (?,?,?,?,?) "
        "ON CONFLICT(sh) DO UPDATE SET pali_title=excluded.pali_title, sc_uid=excluded.sc_uid, "
        "pts_sutta=excluded.pts_sutta, note=excluded.note",
        PALI_REF_SEED)
    conn.commit()
    print(f'[pali_cbeta_map] Upsert xong {len(PALI_REF_SEED)} record (tổng {conn.execute("SELECT COUNT(*) FROM pali_cbeta_map").fetchone()[0]}).')


def create_doctrine_concept(conn, dry_run):
    if has_table(conn, 'doctrine_concept'):
        print('[doctrine_concept] bảng đã có — bỏ qua create (idempotent).')
    else:
        if dry_run:
            print('[doctrine_concept][dry-run] Sẽ CREATE TABLE doctrine_concept (id PK, name_vi, name_zh, pth_uri, definition_vi, related_entities, assertion_level, updated_at)')
        else:
            conn.execute("""
                CREATE TABLE doctrine_concept (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name_vi TEXT,
                    name_zh TEXT,
                    pth_uri TEXT UNIQUE,
                    definition_vi TEXT,
                    related_entities TEXT,
                    assertion_level TEXT DEFAULT 'THEMATIC',
                    updated_at TEXT
                )
            """)
            print('[doctrine_concept] Đã CREATE TABLE.')

    n = conn.execute("SELECT COUNT(*) FROM doctrine_concept").fetchone()[0] if has_table(conn, 'doctrine_concept') else 0
    if dry_run:
        print(f'[doctrine_concept][dry-run] Sẽ upsert {len(DOCTRINE_SEED)} khái niệm (hiện có {n}).')
        return
    if not has_table(conn, 'doctrine_concept'):
        return
    ts = time.strftime('%Y-%m-%dT%H:%M:%S')
    conn.executemany(
        "INSERT INTO doctrine_concept (name_vi, name_zh, pth_uri, definition_vi, related_entities, assertion_level, updated_at) "
        "VALUES (?,?,?,?,?,?,?) "
        "ON CONFLICT(pth_uri) DO UPDATE SET name_vi=excluded.name_vi, name_zh=excluded.name_zh, "
        "definition_vi=excluded.definition_vi, related_entities=excluded.related_entities, updated_at=excluded.updated_at",
        [(*row, ts) for row in DOCTRINE_SEED])
    conn.commit()
    print(f'[doctrine_concept] Upsert xong {len(DOCTRINE_SEED)} khái niệm (tổng {conn.execute("SELECT COUNT(*) FROM doctrine_concept").fetchone()[0]}).')


def add_entity_claims_columns(conn, dry_run):
    NEW_COLS = [
        ('assertion_level', 'TEXT'),
        ('reviewed_by', 'TEXT'),
        ('reviewed_at', 'TEXT'),
    ]
    changed = False
    cols_now = {r[1] for r in conn.execute('PRAGMA table_info(entity_claims)')}
    for name, typ in NEW_COLS:
        if name in cols_now:
            print(f'[entity_claims] cột {name} đã có — bỏ qua (idempotent).')
        elif dry_run:
            print(f'[entity_claims][dry-run] Sẽ ALTER TABLE ADD COLUMN {name} {typ}')
        else:
            conn.execute(f"ALTER TABLE entity_claims ADD COLUMN {name} {typ}")
            conn.commit()
            print(f'[entity_claims] Đã ADD COLUMN {name} {typ}')
            changed = True
    return changed


def revert(conn, dry_run):
    """--revert: DROP 2 bảng mới + 3 cột mới (guarded). Không động bảng cũ khác."""
    dropped = []
    for tbl in ('pali_cbeta_map', 'doctrine_concept'):
        if has_table(conn, tbl):
            if dry_run:
                print(f'[revert][dry-run] Sẽ DROP TABLE {tbl}')
            else:
                conn.execute(f'DROP TABLE {tbl}')
                dropped.append(tbl)
        else:
            print(f'[revert] {tbl} không tồn tại — bỏ qua.')
    if not dry_run and dropped:
        conn.commit()

    cols = ['assertion_level', 'reviewed_by', 'reviewed_at']
    for name in cols:
        if has_column(conn, 'entity_claims', name):
            if dry_run:
                print(f'[revert][dry-run] Sẽ DROP COLUMN entity_claims.{name}')
            else:
                conn.execute(f'ALTER TABLE entity_claims DROP COLUMN {name}')
                dropped.append(f'entity_claims.{name}')
        else:
            print(f'[revert] entity_claims.{name} không tồn tại — bỏ qua.')
    if not dry_run and any('entity_claims.' in d for d in dropped):
        conn.commit()
    if dry_run:
        print('[revert][dry-run] Xong (mô phỏng).')
    else:
        print(f'[revert] Đã xoá: {", ".join(dropped) if dropped else "không có gì"}.')


def verify(conn):
    print('\n[verify] Kiểm tra schema sau ETL:')
    for tbl in ('pali_cbeta_map', 'doctrine_concept'):
        if has_table(conn, tbl):
            cols = [r[1] for r in conn.execute(f'PRAGMA table_info({tbl})')]
            rows = conn.execute(f'SELECT COUNT(*) FROM {tbl}').fetchone()[0]
            print(f'  {tbl}: {rows:,} rows · cols={cols}')
        else:
            print(f'  {tbl}: KHÔNG tồn tại')
    cols = [r[1] for r in conn.execute('PRAGMA table_info(entity_claims)')]
    print(f'  entity_claims: cols={cols}')
    new_cols = [c for c in ('assertion_level', 'reviewed_by', 'reviewed_at') if c in cols]
    print(f'  entity_claims có {len(new_cols)} cột P2-MASTER mới: {new_cols}')
    n = conn.execute('SELECT COUNT(*) FROM entity_claims').fetchone()[0]
    print(f'  entity_claims total rows: {n:,} (KHÔNG thay đổi nếu idempotent chạy lại)')


def main():
    ap = argparse.ArgumentParser(description='T100 Batch 4 P2-MASTER — schema additive GIÁO LÝ phân đôi')
    ap.add_argument('--dry-run', action='store_true', help='chỉ in kế hoạch, không đổi DB')
    ap.add_argument('--apply', action='store_true', help='CREATE + ALTER + seed (mặc định nếu không có cờ khác)')
    ap.add_argument('--revert', action='store_true', help='DROP bảng mới + 3 cột mới')
    args = ap.parse_args()

    dry_run = args.dry_run
    revert_mode = args.revert
    apply_mode = args.apply or (not dry_run and not revert_mode)

    print(f'[ETL] T100 Batch 4 P2-MASTER — DB: {DB_PATH}')
    print(f'[ETL] mode: {"revert" if revert_mode else ("dry-run" if dry_run else "apply")}')

    if not os.path.exists(DB_PATH):
        print(f'[ETL] LỖI: không tìm thấy DB {DB_PATH}')
        sys.exit(1)

    if not dry_run and not revert_mode:
        make_backup(args.dry_run)

    conn = connect()
    try:
        if revert_mode:
            revert(conn, dry_run)
        else:
            create_pali_cbeta_map(conn, dry_run)
            create_doctrine_concept(conn, dry_run)
            add_entity_claims_columns(conn, dry_run)
            if dry_run:
                print('[ETL][dry-run] KHÔNG đổi gì — mô phỏng xong.')
        verify(conn)
    finally:
        conn.close()


if __name__ == '__main__':
    main()