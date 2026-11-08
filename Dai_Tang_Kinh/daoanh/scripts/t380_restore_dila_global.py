#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
T380 — Khôi phục số đời DILA (lineage_key='dila_global') bằng cách TÍNH LẠI từ đồ thị hiện tại.

Công thức đã xác nhận (Admin 2026-11-08): BFS trên lineage_edge_consensus với
relation_type='dharma_transmission' và consensus_status IN ('confirmed_2plus','single_source'),
gốc A002188 (Ma-ha-ca-diếp) = đời 1, đời = depth + 1.

Không dùng bản sao lưu nào làm nguồn số đời (bản 11/10 lệch 1 đời từ Hoằng Nhẫn trở đi).

Chỉ thêm dòng còn thiếu: INSERT OR IGNORE theo khóa (person_id, lineage_key). Không DROP, không UPDATE.

Modes:
  --dry-run (mặc định)  Chỉ đọc: tính, kiểm mốc, in số dòng sẽ thêm.
  --apply               Backup -> kiểm mốc (lỗi thì dừng) -> INSERT trong 1 transaction -> integrity_check.

Chạy từ thư mục daoanh/.
"""

import argparse
import os
import shutil
import sqlite3
import sys
from collections import deque, defaultdict
from datetime import datetime

DB_PATH = os.path.join('data', 'lineage.db')
BACKUP_DIR = os.path.join('data', 'backups')
ROOT = 'A002188'
LINEAGE_KEY = 'dila_global'
LINEAGE_NAME = 'Thiền Tông (DILA)'

# Mốc đã được Admin xác nhận — phải khớp trước khi ghi.
ANCHORS = {
    'A002188': 1,   # Ma-ha-ca-diếp
    'A001361': 28,  # Bồ Đề Đạt Ma
    'A003881': 29,  # Huệ Khả
    'A001601': 30,  # Tăng Xán
    'A003654': 31,  # Đạo Tín
    'A000237': 32,  # Hoằng Nhẫn
    'A001719': 33,  # Lục Tổ Huệ Năng
    'A001984': 37,  # Quy Sơn Linh Hựu
    'A003627': 38,  # Lâm Tế Nghĩa Huyền
}


def compute_generations(conn):
    edges = conn.execute(
        "SELECT teacher_id, disciple_id FROM lineage_edge_consensus "
        "WHERE relation_type='dharma_transmission' "
        "AND consensus_status IN ('confirmed_2plus','single_source')").fetchall()
    children = defaultdict(list)
    for t, d in edges:
        children[t].append(d)
    depth = {ROOT: 0}
    q = deque([ROOT])
    while q:
        x = q.popleft()
        for y in children[x]:
            if y not in depth:
                depth[y] = depth[x] + 1
                q.append(y)
    return {pid: d + 1 for pid, d in depth.items()}


def check_anchors(gens):
    bad = [(pid, want, gens.get(pid)) for pid, want in ANCHORS.items() if gens.get(pid) != want]
    return bad


def run(db, apply_changes):
    conn = sqlite3.connect(f'file:{db}?mode=ro' if not apply_changes else db, uri=not apply_changes)
    gens = compute_generations(conn)
    bad = check_anchors(gens)
    existing = set(r[0] for r in conn.execute(
        "SELECT person_id FROM person_gen_computed WHERE lineage_key=?", (LINEAGE_KEY,)))
    to_add = [(pid, g) for pid, g in gens.items() if pid not in existing]
    print(f'Đồ thị: {len(gens)} người nối được về gốc')
    print(f'Đã có {LINEAGE_KEY} trong DB: {len(existing)} người')
    print(f'Sẽ thêm: {len(to_add)} người')
    if bad:
        print('LỖI: không khớp mốc đã xác nhận:')
        for pid, want, got in bad:
            print(f'  {pid}: cần {want}, tính được {got}')
        conn.close()
        return 1
    print('Mốc đã xác nhận: khớp hết.')
    if not apply_changes:
        print('DRY-RUN: chưa ghi. Dùng --apply để ghi.')
        conn.close()
        return 0

    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup = os.path.join(BACKUP_DIR, f'lineage_pre_t380_dila_global_{stamp}.db')
    conn.close()
    print(f'[backup] {backup}')
    shutil.copy2(db, backup)

    conn = sqlite3.connect(db)
    try:
        before = conn.execute('SELECT COUNT(*) FROM person_gen_computed').fetchone()[0]
        with conn:
            conn.executemany(
                "INSERT OR IGNORE INTO person_gen_computed "
                "(person_id, lineage_key, lineage_name, gen_sect, gen_lamte, gen_thientong) "
                "VALUES (?,?,?,NULL,NULL,?)",
                [(pid, LINEAGE_KEY, LINEAGE_NAME, g) for pid, g in to_add])
        after = conn.execute('SELECT COUNT(*) FROM person_gen_computed').fetchone()[0]
        ok = conn.execute('PRAGMA integrity_check').fetchone()[0]
        print(f'person_gen_computed: {before} -> {after} (+{after - before})')
        print(f'integrity_check = {ok}')
        return 0 if ok == 'ok' else 1
    finally:
        conn.close()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_mutually_exclusive_group()
    g.add_argument('--dry-run', action='store_true')
    g.add_argument('--apply', action='store_true')
    p.add_argument('--db', default=DB_PATH)
    args = p.parse_args()
    return run(args.db, apply_changes=args.apply)


if __name__ == '__main__':
    sys.exit(main())
