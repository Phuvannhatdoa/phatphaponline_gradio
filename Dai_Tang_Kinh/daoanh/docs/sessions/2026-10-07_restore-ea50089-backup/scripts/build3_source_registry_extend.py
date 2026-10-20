#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T77 — Build 3 (G1): Mở rộng Source Registry — thêm cột metadata cho `data_sources`
====================================================================================
Mục đích
--------
Mở rộng `data_sources` (Source Registry) bằng các cột metadata additive để hỗ trợ
nghiệp vụ source management trong tương lai (versioning, sync, license, capabilities)
— phục vụ mục tiêu "READY FOR FUTURE SOURCE INTEGRATION".

Các cột THÊM (additive, KHÔNG drop/sửa cột hiện có):
    source_version      TEXT  -- version hiện tại của nguồn dữ liệu
    adapter_version     TEXT  -- version của adapter tích hợp nguồn
    schema_version      TEXT  -- version schema dữ liệu nguồn
    last_sync           TEXT  -- mốc thời gian đồng bộ cuối
    last_verified       TEXT  -- mốc thời gian xác minh cuối
    enabled             INTEGER -- 0/1 (tách khỏi `active` — for graceful disable)
    health              TEXT  -- trạng thái health (ok/degraded/unknown)
    capabilities        TEXT  -- JSON [] khả năng nguồn (fetch/search/resolve/...)
    base_url            TEXT  -- base endpoint nguồn
    attribution_required INTEGER -- 0/1 có cần ghi công?
    redistribution_allowed INTEGER -- 0/1 có được phân phối lại?
    commercial_use      INTEGER -- 0/1 có được dùng thương mại?
    api_terms           TEXT  -- mô tả/điều khoản API

NGUYÊN TẮC (tuân thủ Build hard-rules)
--------------------------------------
- ADDITIVE: chỉ ALTER TABLE ADD COLUMN — không đổi schema bảng khác, không đổi data.
- REVERSIBLE: trước mỗi ALTER tạo backup `data/lineage_backup_t77.db`; `--undo` khôi phục backup.
- IDEMPOTENT: bỏ qua cột đã tồn tại; chạy lại an toàn.
- KHÔNG drop cột, KHÔNG đổi `source_id`, KHÔNG đụng canonical/entity.
- Backfill: không over-write — chỉ gán giá trị mặc định cho cột mới (cho dòng hiện có).

Cách dùng
---------
    python scripts/build3_source_registry_extend.py              # thêm cột + backfill
    python scripts/build3_source_registry_extend.py --dry-run    # in ra dự kiến
    python scripts/build3_source_registry_extend.py --undo       # khôi phục từ backup

Kiểm chứng
----------
    PRAGMA table_info(data_sources);
"""
import argparse
import os
import shutil
import sqlite3
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = r'data/lineage.db'
BACKUP_PATH = r'data/lineage_backup_t77.db'

# (cột, kiểu, default, mô tả)
NEW_COLUMNS = [
    ('source_version', 'TEXT', '1.0', 'version hiện tại của nguồn dữ liệu'),
    ('adapter_version', 'TEXT', None, 'version adapter tích hợp nguồn'),
    ('schema_version', 'TEXT', None, 'version schema dữ liệu nguồn'),
    ('last_sync', 'TEXT', None, 'mốc đồng bộ cuối (ISO)'),
    ('last_verified', 'TEXT', None, 'mốc xác minh cuối (ISO)'),
    ('enabled', 'INTEGER', 1, '0/1 — tách khỏi active, cho disable có kiểm soát'),
    ('health', 'TEXT', 'unknown', 'ok/degraded/unknown'),
    ('capabilities', 'TEXT', '[]', 'JSON [] khả năng nguồn'),
    ('base_url', 'TEXT', None, 'base endpoint nguồn'),
    ('attribution_required', 'INTEGER', 0, '0/1 cần ghi công?'),
    ('redistribution_allowed', 'INTEGER', 1, '0/1 được phân phối lại?'),
    ('commercial_use', 'INTEGER', 1, '0/1 được dùng thương mại?'),
    ('api_terms', 'TEXT', None, 'điều khoản API'),
]

# Giá trị cho từng source hiện có (backfill — chỉ cột mới, không đổi dữ liệu cũ)
# source_code -> {cột: giá trị}
BACKFILL = {
    'DILA': {'source_version': '2026.03', 'adapter_version': '0.1', 'schema_version': 'dila-v1',
             'base_url': 'https://authority.dila.edu.tw', 'attribution_required': 1,
             'redistribution_allowed': 0, 'commercial_use': 0, 'api_terms': 'DILA Authority API — non-commercial',
             'capabilities': '["search", "resolve", "coordinate"]'},
    'CBETA': {'source_version': 'T50', 'adapter_version': '0.1', 'schema_version': 'cbeta-txt',
              'base_url': 'https://www.cbeta.org', 'attribution_required': 1,
              'redistribution_allowed': 1, 'commercial_use': 1,
              'capabilities': '["search", "text_evidence"]'},
    'MARCUS': {'source_version': '2026', 'adapter_version': '0.1', 'schema_version': 'marcus-net',
               'base_url': 'http://marcus.ctg.byu.edu', 'attribution_required': 1,
               'redistribution_allowed': 0, 'commercial_use': 0,
               'capabilities': '["search", "network_evidence"]'},
    'ZQLOCAL': {'source_version': '2024', 'adapter_version': '0.1', 'schema_version': 'zq-local',
                'base_url': None, 'attribution_required': 0, 'redistribution_allowed': 1,
                'commercial_use': 1, 'capabilities': '["local", "name_vi"]'},
    'Wikidata': {'source_version': 'Q', 'adapter_version': '0.1', 'schema_version': 'wikidata-entity',
                 'base_url': 'https://www.wikidata.org', 'attribution_required': 1,
                 'redistribution_allowed': 1, 'commercial_use': 1,
                 'capabilities': '["search", "external_id"]'},
}


def connect():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def columns(conn, table):
    return [d[1] for d in conn.execute(f'PRAGMA table_info({table})')]


def run(dry_run=False, undo=False):
    conn = connect()
    try:
        return do_undo(conn, dry_run) if undo else do_apply(conn, dry_run)
    finally:
        conn.close()


def backup():
    """Tạo backup trước khi ALTER — nền cho --undo."""
    if os.path.exists(BACKUP_PATH):
        os.remove(BACKUP_PATH)
    shutil.copy2(DB_PATH, BACKUP_PATH)
    return BACKUP_PATH


def do_apply(conn, dry_run):
    print('=== [T77] Mở rộng Source Registry (data_sources) — additive/reversible ===')
    existing = columns(conn, 'data_sources')
    missing = [(c, t, d) for c, t, d, _ in NEW_COLUMNS if c not in existing]
    if not missing:
        print('  [ok] data_sources đã có đủ mọi cột T77 — không thay đổi (idempotent).')
        return 0

    if not dry_run:
        bk = backup()
        print(f'  [~] backup đã tạo: {bk}')
    else:
        print('  [dry-run] (sẽ tạo backup trước khi ALTER)')

    for col, ctype, default, desc in NEW_COLUMNS:
        if col in existing:
            print(f'  [ok] cột {col} đã có — bỏ qua.')
            continue
        if dry_run:
            print(f'  [dry-run] sẽ ALTER ADD COLUMN {col} {ctype} (mặc định {default})')
            continue
        ddl = f'ALTER TABLE data_sources ADD COLUMN {col} {ctype}'
        if default is not None:
            if isinstance(default, str):
                ddl += f" DEFAULT '{default}'"
            else:
                ddl += f' DEFAULT {default}'
        conn.execute(ddl)
        conn.commit()
        print(f'  [+] đã thêm cột {col} {ctype}')

    # Backfill chỉ cột mới cho các source đã biết (không đổi dữ liệu cũ)
    if not dry_run:
        for code, vals in BACKFILL.items():
            sets = []
            args = []
            colmap = dict((d[0], d[1]) for d in NEW_COLUMNS)
            for col, val in vals.items():
                if col in colmap:
                    sets.append(f'{col} = ?')
                    args.append(val)
            if sets:
                args.append(code)
                conn.execute(f'UPDATE data_sources SET {", ".join(sets)} WHERE source_code = ?', args)
        conn.commit()
        print(f'  [+] backfill metadata cho {len(BACKFILL)} nguồn đã biết.')

    print('\n--- data_sources sau T77 ---')
    cur_cols = columns(conn, 'data_sources')
    sel = 'source_code' if 'source_code' in cur_cols else None
    for r in conn.execute("SELECT * FROM data_sources ORDER BY source_id"):
        code = r['source_code']
        extra = ''
        if 'source_version' in cur_cols:
            extra += f" ver={r['source_version']}"
        if 'adapter_version' in cur_cols:
            extra += f" adapter={r['adapter_version']}"
        if 'capabilities' in cur_cols:
            extra += f" cap={r['capabilities']}"
        if 'enabled' in cur_cols:
            extra += f" enabled={r['enabled']}"
        print(f'    {code:<14}{extra}')
    return 0


def do_undo(conn, dry_run):
    print('=== [T77] UNDO — khôi phục từ backup ===')
    if not os.path.exists(BACKUP_PATH):
        print('  [error] không tìm thấy backup, không thể undo.')
        return 1
    if dry_run:
        print(f'  [dry-run] sẽ khôi phục DB từ {BACKUP_PATH}')
        return 0
    conn.close()
    shutil.copy2(BACKUP_PATH, DB_PATH)
    print(f'  [~] đã khôi phục DB từ {BACKUP_PATH} — trả về trạng thái trước T77.')
    return 0


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='T77 — Mở rộng Source Registry (data_sources)')
    ap.add_argument('--dry-run', action='store_true', help='chỉ in ra, không thay đổi')
    ap.add_argument('--undo', action='store_true', help='khôi phục từ backup (revert)')
    args = ap.parse_args()
    sys.exit(run(dry_run=args.dry_run, undo=args.undo))
