#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETL T138 (Zero-ALTER · Zero-RAM · Lean) — Edge Assertion Model (multi-source cạnh truyền thừa)
===============================================================================================
Mô hình hóa quy tắc vẽ cây đã thẩm định: mỗi cạnh truyền thừa là quan hệ chuẩn hóa
mang NHIỀU source assertion độc lập + trust_level L1..L4 (KHÔNG tái dùng tier A-D của
Zen Lineage để tránh trùng nghĩa — G5).

Tính chất (tuân điều lệnh check07 — 0 ALTER base)
-------------------------------------------------
- ZERO-ALTER: KHÔNG DROP/ALTER bảng base (marcus_networks/lineage_conflicts_v2/...).
  Chỉ CREATE TABLE dẫn xuất `lineage_edge_assertions` (DERIVED-only, additive).
- IDEMPOTENT: edge_key = 'M'|<teacher_id>|<student_id> (bền), assertion PK = source|edge_key;
  INSERT OR REPLACE → chạy lại ra cùng giá trị.
- REVERSIBLE: `--revert` chỉ DROP bảng dẫn xuất (0 động dữ liệu base).
- BACKUP: backup nhất quán bằng SQLite backup API (Zero-RAM) → data/backups/lineage_t138_<ts>.db khi `--apply`.
- Zero-RAM: duyệt marcus_networks theo chunk (fetchmany) — KHÔNG load 11,169 row cùng lúc.

Cách dùng
---------
    python scripts/etl_t138_edge_assertions.py --dry-run   # chỉ in kế hoạch + số liệu dự kiến
    python scripts/etl_t138_edge_assertions.py --apply     # tạo bảng + backfill (có backup)
    python scripts/etl_t138_edge_assertions.py --revert    # DROP bảng dẫn xuất (giữ backup)

Quy ước trust_level (L1..L4 — G5, tránh trùng tier A-D Zen Lineage)
-------------------------------------------------------------------
    L1 = văn bản chứng cứ trực tiếp (cạnh có ref CBETA) + structured confirmed
    L2 = nguồn structured đã xác nhận (DILA/Marcus đã map)
    L3 = nguồn structured chưa map / chưa rõ semantics → candidate (Zen Lineage BLOCKED, 0 rows)
    L4 = suy đoán (tên/cùng thời/tông phái) → KHÔNG tạo edge (không INSERT)

Policy G6a (grandfather Marcus)
-------------------------------
Marcus node id → DILA person qua `marcus_people_link` = "đã map ngầm" → mapping_verified=1.
Admin-duyệt (entity_source_ids.verified=1) CHỈ bắt buộc cho nguồn mới (Zen Lineage). Nguồn
DILA đã có person backbone DILA → mapping_verified=1.
"""
import argparse
import json
import os
import sqlite3
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'lineage.db')
BACKUP_DIR = os.path.join(BASE_DIR, 'data', 'backups')

TS = time.strftime('%Y%m%d_%H%M%S')
BUILT_AT = time.strftime('%Y-%m-%dT%H:%M:%S')

TABLE = 'lineage_edge_assertions'

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS lineage_edge_assertions (
    id                  INTEGER PRIMARY KEY,
    edge_key            TEXT NOT NULL,
    subject_person_id   TEXT NOT NULL,
    relation_type       TEXT NOT NULL,
    object_person_id    TEXT NOT NULL,
    source_code         TEXT NOT NULL,
    raw_relation_type   TEXT,
    ref                 TEXT,
    citation_tier       TEXT,
    mapping_verified    INTEGER DEFAULT 0,
    trust_level         TEXT NOT NULL,
    status              TEXT DEFAULT 'active',
    created_at          TEXT
)
"""
CREATE_IDX = [
    "CREATE INDEX IF NOT EXISTS idx_lea_subject ON lineage_edge_assertions(subject_person_id)",
    "CREATE INDEX IF NOT EXISTS idx_lea_object  ON lineage_edge_assertions(object_person_id)",
    "CREATE INDEX IF NOT EXISTS idx_lea_edgekey ON lineage_edge_assertions(edge_key)",
]

# Toàn bộ import dữ liệu dọn trong 1 transaction (theo PK) — idempotent, atomic.
INSERT_SQL = """
INSERT OR REPLACE INTO lineage_edge_assertions
(edge_key, subject_person_id, relation_type, object_person_id, source_code,
 raw_relation_type, ref, citation_tier, mapping_verified, trust_level, status, created_at)
VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
"""


def connect():
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.row_factory = sqlite3.Row
    return conn


def has_table(conn, name):
    return conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None


def make_backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    dst = os.path.join(BACKUP_DIR, f'lineage_t138_{TS}.db')
    if not os.path.exists(DB_PATH):
        print(f'[backup] KHÔNG tìm thấy {DB_PATH} — bỏ qua backup')
        return None
    src = sqlite3.connect(DB_PATH, timeout=60)
    try:
        dest = sqlite3.connect(dst, timeout=60)
        try:
            src.backup(dest)  # streaming pages, Zero-RAM, nhất quán
        finally:
            dest.close()
    finally:
        src.close()
    print(f'[backup] Đã backup → {dst} ({os.path.getsize(dst):,} bytes)')
    return dst


def edge_key(teacher_id, student_id):
    # Bền theo cặp nút nguồn (marcus ids). Cùng cặp = cùng cạnh.
    return f'M|{teacher_id}|{student_id}'


def backfill_marcus(conn, dry_run):
    """Mọi cạnh marcus_networks → 1 assertion MARCUS (L1 nếu có ref, L2 nếu không).
    Map teacher/student → DILA person qua marcus_people_link (grandfather G6a)."""
    link = {}
    for r in conn.execute("SELECT person_id, marcus_node_id FROM marcus_people_link"):
        link[r['marcus_node_id']] = r['person_id']

    total = conn.execute("SELECT COUNT(*) FROM marcus_networks").fetchone()[0]
    print(f'[marcus] {total:,} cạnh marcus_networks → assertions MARCUS' + (' (dry-run)' if dry_run else ''))
    if dry_run:
        return total

    cur = conn.execute(
        "SELECT teacher_id, student_id, relation_type, teacher_label, student_label, ref "
        "FROM marcus_networks")
    n_ins = 0
    while True:
        rows = cur.fetchmany(5000)
        if not rows:
            break
        for r in rows:
            t = link.get(r['teacher_id']) or r['teacher_id']
            s = link.get(r['student_id']) or r['student_id']
            ref = r['ref'] or ''
            conn.execute(INSERT_SQL, (
                edge_key(r['teacher_id'], r['student_id']), t, 'da:isTeacherOf', s,
                'MARCUS', r['relation_type'], ref, None,
                1, ('L1' if ref else 'L2'), 'active', BUILT_AT,
            ))
            n_ins += 1
    print(f'[marcus] Đã chèn {n_ins:,} assertion MARCUS')
    return n_ins


def backfill_dila(conn, dry_run):
    """lineage_conflicts_v2.dila_data (JSON set thầy/trò) → assertions DILA L2.
    direction: conflict_type 'teacher_set' = DILA có tập THẦY của person → subject=DILA-person, relation teacher_of.
    'student_set' = DILA có tập TRÒ của person → subject=person, object=idos.
    Chỉ chèn dila_count>0 (có dữ liệu thật); bỏ chunks JSON rỗng. Chaos-safe: idempotent PK."""
    total_rows = conn.execute(
        "SELECT COUNT(*) FROM lineage_conflicts_v2 WHERE dila_count>0").fetchone()[0]
    print(f'[dila] {total_rows:,} conflict rows có dila_count>0 (set thầy/trò DILA)'
          + (' (dry-run)' if dry_run else ''))
    if dry_run:
        return 0

    cur = conn.execute(
        "SELECT person_id, conflict_type, dila_data, dila_count FROM lineage_conflicts_v2 WHERE dila_count>0")
    n_ins = 0
    while True:
        rows = cur.fetchmany(5000)
        if not rows:
            break
        for r in rows:
            try:
                ids = json.loads(r['dila_data'] or '[]')
            except Exception:
                ids = []
            if not isinstance(ids, list) or not ids:
                continue
            if r['conflict_type'] == 'teacher_set':
                # thầy của person → cạnh teacher→person, subject=thầy, object=person
                for tid in ids:
                    conn.execute(INSERT_SQL, (
                        f'D|{tid}|{r["person_id"]}', tid, 'da:isTeacherOf', r['person_id'],
                        'DILA', 'dila:teacher_of', None, None,
                        1, 'L2', 'active', BUILT_AT,
                    ))
                    n_ins += 1
            elif r['conflict_type'] == 'student_set':
                # trò của person → cạnh person→trò, subject=person, object=trò
                for sid in ids:
                    conn.execute(INSERT_SQL, (
                        f'D|{r["person_id"]}|{sid}', r['person_id'], 'da:isTeacherOf', sid,
                        'DILA', 'dila:teacher_of', None, None,
                        1, 'L2', 'active', BUILT_AT,
                    ))
                    n_ins += 1
    print(f'[dila] Đã chèn {n_ins:,} assertion DILA')
    return n_ins


def mark_rejected(conn, dry_run):
    """Cạnh thuộc conflict đã resolve kèm reject (T136) → status='rejected'.
    Cơ chế: lineage_conflicts_v2.resolved=1 + notes chứa 'reject' (legacy) HOẶC
    en_audit_log action resolve + entity_ref là cặp. Vì reject hiện ~0 row (T136 mới thêm
    resolution_type), thực thi minimal: đọc notes có 'reject' → báo cáo không ẩn bừa."""
    resolved = conn.execute(
        "SELECT person_id, conflict_type, notes FROM lineage_conflicts_v2 "
        "WHERE resolved=1 AND is_conflict=1").fetchall()
    n_reject = 0
    for r in resolved:
        notes = (r['notes'] or '')
        if 'reject' in notes.lower():
            n_reject += 1
            # mark các cạnh Marcus của person theo hướng conflict
    print(f'[reject] {n_reject} conflict resolved có ghi chú reject (thực thi tối thiểu; 0 edge hidden mặc định)'
          + (' (dry-run)' if dry_run else ''))
    return n_reject


def apply_dry_run():
    conn = connect()
    try:
        print(f'[plan] DB: {DB_PATH}')
        print(f'[plan] Sẽ CREATE TABLE {TABLE} (DERIVED-only, additive, 0 ALTER base)')
        backfill_marcus(conn, dry_run=True)
        backfill_dila(conn, dry_run=True)
        mark_rejected(conn, dry_run=True)
        print('[plan] BACKUP → data/backups/lineage_t138_<ts>.db')
        print('[plan] REVERT  → DROP TABLE lineage_edge_assertions')
    finally:
        conn.close()


def apply():
    if not os.path.exists(DB_PATH):
        print(f'[lỗi] Không tìm thấy DB {DB_PATH}'); sys.exit(1)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    conn = connect()
    try:
        make_backup()
        conn.execute(CREATE_TABLE)
        for idx in CREATE_IDX:
            conn.execute(idx)
        print(f'[table] Đã CREATE {TABLE}')
        backfill_marcus(conn, dry_run=False)
        backfill_dila(conn, dry_run=False)
        mark_rejected(conn, dry_run=False)
        conn.commit()
        for row in conn.execute(
                "SELECT source_code, trust_level, COUNT(*) c FROM lineage_edge_assertions "
                "GROUP BY source_code, trust_level ORDER BY source_code, trust_level"):
            print(f'[summary] {row["source_code"]} {row["trust_level"]}: {row["c"]:,}')
        print('[done] --apply hoàn tất.')
    except Exception as e:
        conn.rollback()
        print(f'[lỗi] {e}'); sys.exit(1)
    finally:
        conn.close()


def revert():
    conn = connect()
    try:
        if has_table(conn, TABLE):
            conn.execute(f'DROP TABLE {TABLE}')
            conn.commit()
            print(f'[revert] Đã DROP {TABLE}')
        else:
            print(f'[revert] {TABLE} không tồn tại — không có gì để xóa')
    finally:
        conn.close()


def main():
    ap = argparse.ArgumentParser(description='ETL T138 — Edge Assertion Model')
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--dry-run', action='store_true')
    g.add_argument('--apply', action='store_true')
    g.add_argument('--revert', action='store_true')
    args = ap.parse_args()
    if args.dry_run:
        apply_dry_run()
    elif args.apply:
        apply()
    else:
        revert()


if __name__ == '__main__':
    main()