#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T78 — LEGAL/LICENSE FIREWALL — Migration Source Registry (additive/reversible)
================================================================================
Mục đích
--------
Thêm một lớp GOVERNANCE/SOURCE CONTROL cho TGS: phân biệt rõ Authority vs Legal
Permission. Migration này mở rộng `data_sources` (Source Registry) bằng các cột
pháp lý — nền cho máy trạng thái legal (LicenseGate) mà KHÔNG phá B1/B2.

Các cột THÊM (additive, KHÔNG drop/sửa cột hiện có):
    license_spdx              TEXT  -- mã SPDX chuẩn hóa (MIT, CC BY-SA 4.0...)
    software_license          TEXT  -- license của code/tool (software)
    data_license              TEXT  -- license của data
    corpus_license            TEXT  -- license của corpus/kinh văn
    documentation_license     TEXT  -- license tài liệu
    image_license             TEXT  -- license ảnh
    commercial_use_eventual   TEXT  -- ghi chú quyết định thương mại (rõ ràng)
    derivative_allowed        INTEGER -- 0/1 cho phép phái sinh
    sharealike_required       INTEGER -- 0/1 copyleft/share-alike
    noncommercial             INTEGER -- 0/1 phi thương mại
    noderivatives             INTEGER -- 0/1 cấm phái sinh
    license_verified          INTEGER -- 0/1 đã xác minh (không giả định)
    license_verified_at       TEXT  -- mốc xác minh
    license_verified_by       TEXT  -- ai xác minh
    license_url               TEXT  -- URL giấy phép
    terms_status              TEXT  -- under_review / audited / change_detected
    version_policy            TEXT  -- git_pin | release_pin | snapshot_ok | not_available
    integration_mode          TEXT  -- INGEST | REFERENCE_ONLY | BLOCKED
    data_license_status       TEXT  -- legal status riêng cho data (UNKNOWN/...)
    data_redistribution       INTEGER -- 0/1 data được phân phối lại
    data_commercial           INTEGER -- 0/1 data được dùng thương mại
    legal_status              TEXT  -- DISCOVERED/AUDITING/VERIFIED/APPROVED/ACTIVE/UNKNOWN/REFERENCE_ONLY/BLOCKED/FROZEN
    freeze_reason             TEXT  -- lý do nếu FROZEN
    legal_status_at_ingest    TEXT  -- snapshot legal status lúc dữ liệu đã ingest (historical)

NGUYÊN TẮC (tuân thủ Build hard-rules)
--------------------------------------
- ADDITIVE: chỉ ALTER TABLE ADD COLUMN — không đổi schema bảng khác, không đổi data.
- REVERSIBLE: backup `data/lineage_backup_t78.db`; `--undo` khôi phục backup.
- IDEMPOTENT: bỏ qua cột đã tồn tại; chạy lại an toàn.
- KHÔNG xoá/đổi dữ liệu canonical. Chỉ DATA-FIX additive cho `data_sources`
  (sửa các giá trị commercial_use/redistribution giả định -> UNKNOWN) — không đụng B1/B2.
- Historical claims KHÔNG bị xoá/freeze: chỉ gắn `legal_status_at_ingest` snapshot.

Áp dụng quyết định đã chốt (T78):
  1. Historical 447,885 claims -> giữ nguyên + snapshot legal_status_at_ingest, không freeze.
  2. Fix additive mâu thuẫn: BDRC/FoJin/CHGIS/TGAZ... commercial_use=1 (giả định) -> legal UNKNOWN.
  3. Audit 13 nguồn `data_sources` (không phải 20 theo docs kế hoạch).
  4. Version pinning per-source (`version_policy`), không hard-rule toàn hệ thống.

Cách dùng
---------
    python scripts/build3_license_firewall.py              # thêm cột + fix additive
    python scripts/build3_license_firewall.py --dry-run    # in dự kiến
    python scripts/build3_license_firewall.py --undo       # khôi phục từ backup
"""
import argparse
import os
import shutil
import sqlite3
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = r'data/lineage.db'
BACKUP_PATH = r'data/lineage_backup_t78.db'

# (cột, kiểu, default, mô tả)
NEW_COLUMNS = [
    ('license_spdx', 'TEXT', None, 'mã SPDX chuẩn hóa (MIT, CC BY-SA 4.0...)'),
    ('software_license', 'TEXT', None, 'license của code/tool (software)'),
    ('data_license', 'TEXT', None, 'license của data'),
    ('corpus_license', 'TEXT', None, 'license của corpus/kinh văn'),
    ('documentation_license', 'TEXT', None, 'license tài liệu'),
    ('image_license', 'TEXT', None, 'license ảnh'),
    ('derivative_allowed', 'INTEGER', 0, '0/1 cho phép phái sinh'),
    ('sharealike_required', 'INTEGER', 0, '0/1 copyleft/share-alike'),
    ('noncommercial', 'INTEGER', 0, '0/1 phi thương mại'),
    ('noderivatives', 'INTEGER', 0, '0/1 cấm phái sinh'),
    ('license_verified', 'INTEGER', 0, '0/1 đã xác minh (không giả định)'),
    ('license_verified_at', 'TEXT', None, 'mốc xác minh (ISO)'),
    ('license_verified_by', 'TEXT', None, 'ai xác minh'),
    ('license_url', 'TEXT', None, 'URL giấy phép'),
    ('terms_status', 'TEXT', 'under_review', 'under_review/audited/change_detected'),
    ('version_policy', 'TEXT', 'not_available', 'git_pin|release_pin|snapshot_ok|not_available'),
    ('integration_mode', 'TEXT', 'BLOCKED', 'INGEST|REFERENCE_ONLY|BLOCKED'),
    ('data_license_status', 'TEXT', 'UNKNOWN', 'legal status riêng cho data'),
    ('data_redistribution', 'INTEGER', 0, '0/1 data được phân phối lại'),
    ('data_commercial', 'INTEGER', 0, '0/1 data được dùng thương mại'),
    ('legal_status', 'TEXT', 'AUDITING', 'DISCOVERED/AUDITING/VERIFIED/APPROVED/ACTIVE/UNKNOWN/REFERENCE_ONLY/BLOCKED/FROZEN'),
    ('freeze_reason', 'TEXT', None, 'lý do nếu FROZEN'),
    ('legal_status_at_ingest', 'TEXT', None, 'snapshot legal status lúc ingest (historical)'),
    ('repository_url', 'TEXT', None, 'URL repo nguồn (GitHub...)'),
    ('updated_at', 'TEXT', None, 'mốc cập nhật source (ISO)'),
]

# METADATA_LOOKUP: source_code -> {cột: giá trị} — metadata pháp lý ĐÃ XÁC MINH cho từng nguồn
# (chỉ gán khi đã xác minh; giá trị UNKNOWN/None = chưa rõ, KHÔNG giả định)
LEGAL_METADATA = {
    'DILA': {'license_note_hint': None},
}

# FIX giả định sai: các nguồn hiện có commercial_use/redistribution = 1 nhưng chưa xác minh
# -> chuyển data_license_status = UNKNOWN (KHÔNG tự cho là được phân phối/thương mại).
# Lưu ý: KHÔNG sửa commercial_use/redistribution_allowed cũ (giữ B1/B2 không đổi);
# chỉ gán cột MỚI data_commercial/data_redistribution/data_license_status rõ ràng.
FIX_UNKNOWN = [
    # (source_code, version_policy, data_license_status, data_redistribution, data_commercial, ghi chú)
    ('BDRC',       'not_available', 'UNKNOWN', 0, 0, 'legal chưa xác minh; active=0 (T18 skip)'),
    ('FoJin',      'not_available', 'UNKNOWN', 0, 0, 'license corpus chưa xác minh — không giả định'),
    ('CHGIS',      'snapshot_ok',   'UNKNOWN', 0, 0, 'GIS Harvard — redistribution cần xác minh'),
    ('TGAZ',       'snapshot_ok',   'UNKNOWN', 0, 0, 'GIS Harvard Gazetteer — cần xác minh'),
    ('SAT',        'snapshot_ok',   'AUDITING', 0, 0, 'SAT Daizokyo — license CC BY 4.0 cần xác minh corpus'),
    ('Kanripo',    'release_pin',   'AUDITING', 0, 0, 'Kanripo CC BY-SA 4.0 — cần xác minh phạm vi'),
    ('SuttaCentral','release_pin',  'AUDITING', 0, 0, 'CC BY-NC-SA 4.0 — phi thương mại (noncommercial)'),
    ('84000',      'release_pin',   'AUDITING', 0, 0, 'CC BY-NC-SA 4.0 — phi thương mại (noncommercial)'),
]

# Các nguồn đã ingest (historical) — gắn legal_status_at_ingest snapshot + data legal status
INGESTED_SOURCES = {
    'DILA':    {'legal_status': 'AUDITING', 'data_license_status': 'AUDITING',
                'data_redistribution': 0, 'data_commercial': 0,
                'license_note_status': 'CC BY-SA 4.0 (cần xác minh phạm vi)',
                'integration_mode': 'INGEST', 'legal_status_at_ingest': 'LEGACY'},
    'CBETA':   {'legal_status': 'AUDITING', 'data_license_status': 'AUDITING',
                'data_redistribution': 1, 'data_commercial': 1,
                'integration_mode': 'INGEST', 'legal_status_at_ingest': 'LEGACY'},
    'MARCUS':  {'legal_status': 'AUDITING', 'data_license_status': 'AUDITING',
                'data_redistribution': 0, 'data_commercial': 0,
                'integration_mode': 'INGEST', 'legal_status_at_ingest': 'LEGACY'},
    'ZQLOCAL': {'legal_status': 'AUDITING', 'data_license_status': 'AUDITING',
                'data_redistribution': 1, 'data_commercial': 1,
                'integration_mode': 'INGEST', 'legal_status_at_ingest': 'LEGACY'},
    'Wikidata':{'legal_status': 'AUDITING', 'data_license_status': 'AUDITING',
                'data_redistribution': 1, 'data_commercial': 1,
                'integration_mode': 'INGEST', 'legal_status_at_ingest': 'LEGACY'},
}


def connect():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def columns(conn, table):
    return [d[1] for d in conn.execute(f'PRAGMA table_info({table})')]


def backup():
    if os.path.exists(BACKUP_PATH):
        os.remove(BACKUP_PATH)
    shutil.copy2(DB_PATH, BACKUP_PATH)
    return BACKUP_PATH


def do_apply(conn, dry_run):
    print('=== [T78] LEGAL/LICENSE FIREWALL — mở rộng Source Registry (additive/reversible) ===')
    existing = columns(conn, 'data_sources')
    missing = [(c, t, d) for c, t, d, _ in NEW_COLUMNS if c not in existing]

    if not dry_run and missing:
        bk = backup()
        print(f'  [~] backup đã tạo: {bk}')
    elif dry_run and missing:
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

    if dry_run:
        print('\n  [dry-run] data-fix additive sẽ được mô tả bên dưới (không thực thi).')

    # Data-fix additive: gắn legal metadata/status cho nguồn đã ingest (historical) —
    # KHÔNG xoá/freeze; chỉ gán cột mới + legal_status_at_ingest snapshot.
    if not dry_run:
        conn.execute('UPDATE data_sources SET license_verified = 0, terms_status = \'under_review\'')
        for code, vals in INGESTED_SOURCES.items():
            conn.execute(
                '''UPDATE data_sources SET
                     legal_status = ?, data_license_status = ?,
                     data_redistribution = ?, data_commercial = ?,
                     integration_mode = ?, legal_status_at_ingest = ?
                   WHERE source_code = ?''',
                (vals['legal_status'], vals['data_license_status'],
                 vals['data_redistribution'], vals['data_commercial'],
                 vals['integration_mode'], vals['legal_status_at_ingest'], code))
        print(f'  [+] gán legal snapshot cho {len(INGESTED_SOURCES)} nguồn đã ingest (historical, không freeze).')

        for code, vp, dls, dr, dc, note in FIX_UNKNOWN:
            conn.execute(
                '''UPDATE data_sources SET
                     version_policy = ?, data_license_status = ?,
                     data_redistribution = ?, data_commercial = ?,
                     legal_status = 'UNKNOWN', integration_mode = 'BLOCKED'
                   WHERE source_code = ?''',
                (vp, dls, dr, dc, code))
        print(f'  [+] data-fix {len(FIX_UNKNOWN)} nguồn chưa xác minh -> legal_status=UNKNOWN (BLOCKED ingest mới), không giả định.')
        conn.commit()

    print('\n--- data_sources sau T78 (legal status) ---')
    if 'legal_status' in columns(conn, 'data_sources'):
        for r in conn.execute("SELECT source_code, legal_status, data_license_status, data_redistribution, data_commercial, integration_mode, legal_status_at_ingest FROM data_sources ORDER BY source_id"):
            print(f"    {r['source_code']:<14} legal={str(r['legal_status']):<12} data={str(r['data_license_status']):<10} "
                  f"dk={r['data_redistribution']} cm={r['data_commercial']} mode={str(r['integration_mode']):<14} at_ingest={r['legal_status_at_ingest']}")
    return 0


def do_undo(conn, dry_run):
    print('=== [T78] UNDO — khôi phục từ backup ===')
    if not os.path.exists(BACKUP_PATH):
        print('  [error] không tìm thấy backup, không thể undo.')
        return 1
    if dry_run:
        print(f'  [dry-run] sẽ khôi phục DB từ {BACKUP_PATH}')
        return 0
    conn.close()
    shutil.copy2(BACKUP_PATH, DB_PATH)
    print(f'  [~] đã khôi phục DB từ {BACKUP_PATH} — trả về trạng thái trước T78.')
    return 0


def run(dry_run=False, undo=False):
    if undo:
        return do_undo(connect(), dry_run)
    return do_apply(connect(), dry_run)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='T78 — LEGAL/LICENSE FIREWALL (data_sources)')
    ap.add_argument('--dry-run', action='store_true', help='chỉ in ra, không thay đổi')
    ap.add_argument('--undo', action='store_true', help='khôi phục từ backup (revert)')
    args = ap.parse_args()
    sys.exit(run(dry_run=args.dry_run, undo=args.undo))
