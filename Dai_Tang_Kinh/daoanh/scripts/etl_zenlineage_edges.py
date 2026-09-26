#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETL T139 (Zero-ALTER · Zero-RAM · Lean) — Zen Lineage Edge Assertions (Phase 2)
================================================================================
Chuyển transmissions Zen Lineage (đã HITL-approve mapping zen-slug → DILA person)
thành cạnh truyền thừa chuẩn hóa trong bảng DERIVED `lineage_edge_assertions`
(nguồn MARCUS: 11,169 L1/L2 · DILA: 46,006 L2 · ZENLINEAGE: L2).

Tính chất (tuân điều lệnh check07 — 0 ALTER base)
-------------------------------------------------
- ZERO-ALTER: KHÔNG DROP/ALTER bảng base. CHỈ viết vào bảng dẫn xuất
  `lineage_edge_assertions` (đã tạo từ T138) + bảng DERIVED `zenlineage_review`.
- IDEMPOTENT: cạnh ZEN = {'Z'|<teacher_slug>|<student_slug>}. Cơ chế: TRƯỚC khi insert
  xóa toàn bộ assertion source_code='ZENLINEAGE' rồi chèn lại từ zero (đảm bảo
  chạy lại ra cùng kết quả — bảng không có UNIQUE(slug pair)).
- MAPPING CHẶT: chỉ tạo edge khi CẢ 2 đầu (teacher + student) có mapping HITL-approve
  (entity_source_ids source='ZENLINEAGE' match_status='approved' verified=1).
  Nguồn mới = cần admin-duyệt (policy G6b — nguồn DILA/Marcus đã grandfather).
- REVERSIBLE: `--revert` chỉ xóa assertion source_code='ZENLINEAGE' (0 động base).
- BACKUP: backup nhất quán bằng SQLite backup API (Zero-RAM) → khi `--apply`.
- Zero-RAM: duyệt transmissions theo chunk (fetchmany) — KHÔNG load 578 row cùng lúc.
- License gate: chỉ --apply khi data_sources ZENLINEAGE.integration_mode='INGEST'
  (SSOT — tự động, không cho chạy khi BLOCKED).

Cách dùng
---------
    python scripts/etl_zenlineage_edges.py --dry-run   # chỉ in kế hoạch + số liệu dự kiến
    python scripts/etl_zenlineage_edges.py --apply     # backup + backfill zinc edge (idempotent)
    python scripts/etl_zenlineage_edges.py --revert    # xóa toàn bộ assertion ZENLINEAGE

Quy ước trust_level (G5/T138)
-----------------------------
    L2 = nguồn structured đã xác nhận (DILA/Marcus đã map) — ZENLINEAGE edges đạt L2
         khi cả 2 đầu mapping_verified=1 (approved). Chưa đủ → bỏ qua (0 INSERT).
    Không tái dụng tier A-D của Zen Lineage vào citation_tier để tránh trùng nghĩa.
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

SOURCE = 'ZENLINEAGE'
TABLE = 'lineage_edge_assertions'


def connect():
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.row_factory = sqlite3.Row
    return conn


def make_backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    dst = os.path.join(BACKUP_DIR, f'lineage_t139_edges_{TS}.db')
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


def check_license_gate(conn):
    """SSOT: chỉ cho apply khi gate đã mở INGEST (internal-only). BLOCKED → chặn."""
    row = conn.execute(
        "SELECT integration_mode, legal_status FROM data_sources WHERE source_code=?",
        (SOURCE,)).fetchone()
    if not row:
        print(f'[gate] CẢNH BÁO: không có row data_sources cho {SOURCE} — bỏ qua gate')
        return True
    mode = (row['integration_mode'] or '').upper()
    if mode in ('INGEST', 'INTERNAL'):
        print(f'[gate] PASS — integration_mode={row["integration_mode"]} '
              f'(legal_status={row["legal_status"]}) → cho phép --apply')
        return True
    print(f'[gate] BLOCK — integration_mode={row["integration_mode"]} '
          f'(không phải INGEST/INTERNAL). Chạy lại sau khi mở gate.')
    return False


def load_zen_dila_map(conn):
    """entity_source_ids ZENLINEAGE approved → {zen_slug: dila_person_id}.
    entity_id trong esi là entity_hub.entity_id; DILA person id = canonical_label."""
    m = {}
    for r in conn.execute(
            "SELECT es.source_entity_id, eh.canonical_label AS dila_id "
            "FROM entity_source_ids es "
            "JOIN entity_hub eh ON eh.entity_id = es.entity_id "
            "WHERE es.source='ZENLINEAGE' AND es.match_status='approved' AND es.verified=1"):
        if r['dila_id']:
            m[r['source_entity_id']] = r['dila_id']
    return m


def estimate(conn, zen_map):
    """Đếm transmissions khả dụng: total / có map 1 đầu / đủ 2 đầu."""
    total = conn.execute(
        "SELECT COUNT(*) FROM source_staging WHERE source_code=? AND row_type='transmission'",
        (SOURCE,)).fetchone()[0]
    cur = conn.execute(
        "SELECT teacher_slug, student_slug FROM source_staging "
        "WHERE source_code=? AND row_type='transmission'", (SOURCE,))
    has_teacher = has_both = 0
    while True:
        rows = cur.fetchmany(5000)
        if not rows:
            break
        for r in rows:
            t = r['teacher_slug'] in zen_map
            s = r['student_slug'] in zen_map
            if t:
                has_teacher += 1
            if t and s:
                has_both += 1
    return total, has_teacher, has_both


def backfill(conn, zen_map, dry_run):
    total, has_teacher, has_both = estimate(conn, zen_map)
    if not dry_run:
        # RESET — idempotent: xóa toàn bộ assertion ZEN cũ rồi chèn lại
        conn.execute("DELETE FROM lineage_edge_assertions WHERE source_code=?", (SOURCE,))
    print(f'[zen] transmissions={total} · map-tối-thiểu-1-đầu={has_teacher} · '
          f'cạnh tạo được (đủ 2 đầu)={has_both}' + (' (dry-run)' if dry_run else ''))
    if dry_run:
        return 0
    cur = conn.execute(
        "SELECT source_entity_id, teacher_slug, student_slug, tier, extra_json "
        "FROM source_staging WHERE source_code=? AND row_type='transmission'", (SOURCE,))
    n = 0
    while True:
        rows = cur.fetchmany(5000)
        if not rows:
            break
        for r in rows:
            t = zen_map.get(r['teacher_slug'])
            s = zen_map.get(r['student_slug'])
            if not (t and s):
                continue
            try:
                extra = json.loads(r['extra_json'] or '{}')
            except Exception:
                extra = {}
            conn.execute(
                "INSERT INTO lineage_edge_assertions "
                "(edge_key, subject_person_id, relation_type, object_person_id, source_code, "
                " raw_relation_type, ref, citation_tier, mapping_verified, trust_level, status, created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (f'Z|{r["teacher_slug"]}|{r["student_slug"]}', t, 'da:isTeacherOf', s,
                 SOURCE, extra.get('tr_type') or 'primary', None, None,
                 1, 'L2', 'active', BUILT_AT))
            n += 1
    print(f'[zen] Đã chèn {n} assertion ZENLINEAGE (L2, mapping_verified=1)')
    return n


def apply():
    if not os.path.exists(DB_PATH):
        print(f'[lỗi] Không tìm thấy DB {DB_PATH}'); sys.exit(1)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    conn = connect()
    try:
        if not check_license_gate(conn):
            print('[gate] Hủy bỏ --apply.'); sys.exit(1)
        make_backup()
        zen_map = load_zen_dila_map(conn)
        print(f'[map] {len(zen_map)} zen-slug đã HITL-approve → DILA person')
        if not zen_map:
            print('[map] CHƯA có mapping nào được duyệt — không tạo edge. '
                  'Vào admin/zenlineage_review.html để Approve trước.')
            return
        backfill(conn, zen_map, dry_run=False)
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


def dry_run():
    if not os.path.exists(DB_PATH):
        print(f'[lỗi] Không tìm thấy DB {DB_PATH}'); sys.exit(1)
    conn = connect()
    try:
        print(f'[plan] DB: {DB_PATH}')
        print('[plan] Sẽ backup → data/backups/lineage_t139_edges_<ts>.db')
        if not check_license_gate(conn):
            print('[plan] Gate đang BLOCKED — --apply sẽ bị chặn.')
        zen_map = load_zen_dila_map(conn)
        print(f'[plan] {len(zen_map)} zen-slug đã approve (entity_source_ids verified=1)')
        backfill(conn, zen_map, dry_run=True)
        print('[plan] REVERT → DELETE lineage_edge_assertions WHERE source_code=ZENLINEAGE')
    finally:
        conn.close()


def revert():
    conn = connect()
    try:
        cur = conn.execute("DELETE FROM lineage_edge_assertions WHERE source_code=?", (SOURCE,))
        conn.commit()
        print(f'[revert] Đã xóa {cur.rowcount} assertion ZENLINEAGE (0 động bảng base)')
    except Exception as e:
        conn.rollback()
        print(f'[lỗi] {e}'); sys.exit(1)
    finally:
        conn.close()


def main():
    ap = argparse.ArgumentParser(description='ETL T139 — Zen Lineage Edge Assertions')
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--dry-run', action='store_true')
    g.add_argument('--apply', action='store_true')
    g.add_argument('--revert', action='store_true')
    args = ap.parse_args()
    if args.dry_run:
        dry_run()
    elif args.apply:
        apply()
    else:
        revert()


if __name__ == '__main__':
    main()