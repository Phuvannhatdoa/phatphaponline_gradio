#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
T425 — Bước 4/5 "3 cây": thêm cột relation_kind / source_edge_ref / mapping_ok
vào lineage_edge_assertions + tạo 4 VIEW (DILA, Marcus, TTL, chồng cây) + so sánh với consensus.

Chế độ:
  --dry-run (MẶC ĐỊNH): chỉ báo cáo DDL sẽ chạy, không sửa DB.
  --apply (CHỈ khi Admin duyệt): backup SQLite + quick_check → ALTER TABLE ADD COLUMN (additive)
       + CREATE VIEW.
  --revert --backup <path>: khôi phục DB từ backup (VIEW tự mất, cột additive giữ nguyên).

Lưu ý: cột `mapping_ok` = `mapping_verified` (đồng bộ); `source_edge_ref` = `ref` (đồng bộ);
       `relation_kind` mặc định 'unknown' (T414 sẽ điền sau).
"""

import argparse
import datetime as _dt
import os
import sqlite3
import sys

DB_DEFAULT = os.path.join("data", "lineage.db")
BACKUP_ROOT = os.path.join("data", "backups")
OUT_DIR = os.path.join("docs", "sessions", "2026-10-19", "T425")

COL_RELATION_KIND = "relation_kind"
COL_SOURCE_EDGE_REF = "source_edge_ref"
COL_MAPPING_OK = "mapping_ok"

VIEW_DILA = "v_tree_dila"
VIEW_MARCUS = "v_tree_marcus"
VIEW_TTL = "v_tree_ttl"
VIEW_OVERLAY = "v_tree_overlay"

DDL_ADD_COLUMNS = [
    f'ALTER TABLE lineage_edge_assertions ADD COLUMN {COL_RELATION_KIND} TEXT DEFAULT "unknown"',
    f'ALTER TABLE lineage_edge_assertions ADD COLUMN {COL_SOURCE_EDGE_REF} TEXT',
    f'ALTER TABLE lineage_edge_assertions ADD COLUMN {COL_MAPPING_OK} INTEGER DEFAULT 0',
]

DDL_SYNC_MAPPING_OK = (
    f'UPDATE lineage_edge_assertions SET {COL_MAPPING_OK} = mapping_verified, '
    f'{COL_SOURCE_EDGE_REF} = ref'
)

DDL_VIEWS = [
    f"""
CREATE VIEW IF NOT EXISTS {VIEW_DILA} AS
SELECT
  id, edge_key, subject_person_id, relation_type, object_person_id,
  source_code, raw_relation_type, ref, citation_tier, mapping_verified,
  trust_level, status, created_at,
  {COL_RELATION_KIND}, {COL_SOURCE_EDGE_REF}, {COL_MAPPING_OK}
FROM lineage_edge_assertions
WHERE source_code = 'DILA' AND status = 'active'
""",
    f"""
CREATE VIEW IF NOT EXISTS {VIEW_MARCUS} AS
SELECT
  id, edge_key, subject_person_id, relation_type, object_person_id,
  source_code, raw_relation_type, ref, citation_tier, mapping_verified,
  trust_level, status, created_at,
  {COL_RELATION_KIND}, {COL_SOURCE_EDGE_REF}, {COL_MAPPING_OK}
FROM lineage_edge_assertions
WHERE source_code = 'MARCUS' AND status = 'active'
""",
    f"""
CREATE VIEW IF NOT EXISTS {VIEW_TTL} AS
SELECT
  id, edge_key, subject_person_id, relation_type, object_person_id,
  source_code, raw_relation_type, ref, citation_tier, mapping_verified,
  trust_level, status, created_at,
  {COL_RELATION_KIND}, {COL_SOURCE_EDGE_REF}, {COL_MAPPING_OK}
FROM lineage_edge_assertions
WHERE source_code = 'TTL' AND status = 'active'
""",
    f"""
CREATE VIEW IF NOT EXISTS {VIEW_OVERLAY} AS
SELECT
  subject_person_id AS teacher_id,
  object_person_id AS disciple_id,
  relation_type,
  COUNT(*) AS n_sources,
  GROUP_CONCAT(source_code, ',') AS sources,
  MAX(CASE WHEN {COL_RELATION_KIND} = 'noi_phap' THEN 3
           WHEN {COL_RELATION_KIND} = 'khac' THEN 2
           ELSE 1 END) AS kind_rank,
  MAX(CASE
        WHEN {COL_RELATION_KIND} = 'noi_phap' THEN 'noi_phap'
        WHEN {COL_RELATION_KIND} = 'khac' THEN 'khac'
        ELSE 'unknown' END) AS relation_kind_strongest
FROM lineage_edge_assertions
WHERE status = 'active' AND {COL_MAPPING_OK} = 1
GROUP BY subject_person_id, object_person_id, relation_type
""",
]

DROP_VIEWS = [
    f"DROP VIEW IF EXISTS {VIEW_OVERLAY}",
    f"DROP VIEW IF EXISTS {VIEW_TTL}",
    f"DROP VIEW IF EXISTS {VIEW_MARCUS}",
    f"DROP VIEW IF EXISTS {VIEW_DILA}",
]


def now_stamp():
    return _dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def open_ro(db_path):
    return sqlite3.connect("file:{}?mode=ro".format(db_path.replace("\\", "/")), uri=True)


def check_columns(conn):
    """Kiểm tra cột đã có chưa."""
    cols = [r[1] for r in conn.execute('PRAGMA table_info(lineage_edge_assertions)')]
    return {c: c in cols for c in [COL_RELATION_KIND, COL_SOURCE_EDGE_REF, COL_MAPPING_OK]}


def check_views(conn):
    """Kiểm tra view đã có chưa."""
    existing = set()
    for r in conn.execute("SELECT name FROM sqlite_master WHERE type='view' AND name LIKE 'v_tree_%'"):
        existing.add(r[0])
    return {v: v in existing for v in [VIEW_DILA, VIEW_MARCUS, VIEW_TTL, VIEW_OVERLAY]}


def dry_run(conn):
    has_cols = check_columns(conn)
    has_views = check_views(conn)

    # Stats
    total = conn.execute("SELECT COUNT(*) FROM lineage_edge_assertions WHERE status='active'").fetchone()[0]
    by_src = conn.execute(
        "SELECT source_code, COUNT(*) FROM lineage_edge_assertions WHERE status='active' GROUP BY 1"
    ).fetchall()
    mv = conn.execute(
        "SELECT mapping_verified, COUNT(*) FROM lineage_edge_assertions WHERE status='active' GROUP BY 1"
    ).fetchall()

    print("=== T425 DRY-RUN ===")
    print(f"Tổng cạnh active: {total:,}")
    print("Theo nguồn:")
    for src, cnt in by_src:
        print(f"  {src}: {cnt:,}")
    print("mapping_verified:")
    for mv_val, cnt in mv:
        print(f"  {mv_val}: {cnt:,}")
    print()
    print("Cột sẽ thêm:")
    for c, exists in has_cols.items():
        print(f"  {c}: {'ĐÃ CÓ' if exists else 'CHƯA CÓ'}")
    print()
    print("VIEW sẽ tạo:")
    for v, exists in has_views.items():
        print(f"  {v}: {'ĐÃ CÓ' if exists else 'CHƯA CÓ'}")
    print()
    print("DDL (thứ tự):")
    for ddl in DDL_ADD_COLUMNS:
        print(f"  {ddl}")
    print(f"  {DDL_SYNC_MAPPING_OK}")
    for ddl in DDL_VIEWS:
        print(f"  {ddl.strip()[:100]}...")
    print()
    return has_cols, has_views


def compare_overlay_consensus(conn):
    """So sánh overlay logic (tính trực tiếp) với lineage_edge_consensus."""
    # Overlay logic: GROUP BY teacher, disciple WHERE mapping_verified=1
    ov_sql = """
        SELECT
          subject_person_id AS teacher_id,
          object_person_id AS disciple_id,
          COUNT(*) AS n_sources,
          GROUP_CONCAT(source_code, ',') AS sources
        FROM lineage_edge_assertions
        WHERE status = 'active' AND mapping_verified = 1
        GROUP BY subject_person_id, object_person_id
    """

    ov = conn.execute("SELECT COUNT(*) FROM (" + ov_sql + ")").fetchone()[0]

    cons = conn.execute("""
        SELECT COUNT(*) FROM lineage_edge_consensus
    """).fetchone()[0]

    q1 = "SELECT COUNT(*) FROM (" + ov_sql + ") ov LEFT JOIN lineage_edge_consensus ec ON ec.teacher_id = ov.teacher_id AND ec.disciple_id = ov.disciple_id WHERE ec.id IS NULL"
    in_ov_not_cons = conn.execute(q1).fetchone()[0]

    q2 = "SELECT COUNT(*) FROM lineage_edge_consensus ec LEFT JOIN (" + ov_sql + ") ov ON ov.teacher_id = ec.teacher_id AND ov.disciple_id = ec.disciple_id WHERE ov.teacher_id IS NULL"
    in_cons_not_ov = conn.execute(q2).fetchone()[0]

    q3 = """SELECT ec.teacher_id, ec.disciple_id, ec.dila_asserted, ec.marcus_asserted, ec.ttl_asserted, ec.lineage_asserted, ec.agreeing_source_count, ec.consensus_status, ec.source_badge FROM lineage_edge_consensus ec LEFT JOIN (""" + ov_sql + """) ov ON ov.teacher_id = ec.teacher_id AND ov.disciple_id = ec.disciple_id WHERE ov.teacher_id IS NULL LIMIT 50"""
    diff = conn.execute(q3).fetchall()

    q4 = """SELECT ov.teacher_id, ov.disciple_id, ov.n_sources, ov.sources FROM (""" + ov_sql + """) ov LEFT JOIN lineage_edge_consensus ec ON ec.teacher_id = ov.teacher_id AND ec.disciple_id = ec.disciple_id WHERE ec.id IS NULL LIMIT 50"""
    diff_rev = conn.execute(q4).fetchall()

    print("=== SO SÁNH overlay (tính trực tiếp) vs lineage_edge_consensus ===")
    print(f"  overlay total: {ov:,}")
    print(f"  consensus total: {cons:,}")
    print(f"  trong overlay KHÔNG có trong consensus: {in_ov_not_cons:,}")
    print(f"  trong consensus KHÔNG có trong overlay: {in_cons_not_ov:,}")
    print()
    if diff:
        print("  Cạnh consensus KHÔNG có trong overlay (mẫu 50):")
        for r in diff:
            print(f"    {r[0]}->{r[1]}  dila={r[2]} marcus={r[3]} ttl={r[4]} lineage={r[5]}  agree={r[6]} status={r[7]} badge={r[8]}")
    if diff_rev:
        print("  Cạnh overlay KHÔNG có trong consensus (mẫu 50):")
        for r in diff_rev:
            print(f"    {r[0]}->{r[1]}  n_sources={r[2]} sources={r[3]}")

    return {
        "ov_total": ov,
        "cons_total": cons,
        "ov_not_cons": in_ov_not_cons,
        "cons_not_ov": in_cons_not_ov,
        "diff_cons_not_ov": diff,
        "diff_ov_not_cons": diff_rev,
    }


def apply_db(db_path):
    ts = now_stamp()
    bdir = os.path.join(BACKUP_ROOT, "T425_" + ts)
    os.makedirs(bdir, exist_ok=True)
    bdest = os.path.join(bdir, "lineage.db")

    src = sqlite3.connect(db_path)
    dst = sqlite3.connect(bdest)
    with dst:
        src.backup(dst)
    dst.close()
    qc = src.execute("PRAGMA quick_check").fetchone()[0]
    src.close()
    print("[backup] {} (quick_check={})".format(bdest, qc))
    if qc != "ok":
        raise SystemExit("quick_check FAIL — dừng, không ghi DB.")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        # 1. Thêm cột
        for ddl in DDL_ADD_COLUMNS:
            print("[DDL]", ddl)
            cur.execute(ddl)
        # 2. Đồng bộ mapping_ok + source_edge_ref
        print("[SYNC]", DDL_SYNC_MAPPING_OK)
        cur.execute(DDL_SYNC_MAPPING_OK)
        print(f"  Updated {cur.rowcount} rows")
        # 3. Tạo VIEW
        for ddl in DDL_VIEWS:
            cur.execute(ddl)
        conn.commit()
    except Exception:
        conn.rollback()
        conn.close()
        raise
    conn.close()

    # Verify
    conn = open_ro(db_path)
    has_cols = check_columns(conn)
    has_views = check_views(conn)
    conn.close()

    print("[apply] xong — verify:")
    for c, ok in has_cols.items():
        print(f"  {c}: {'OK' if ok else 'THẤT BẠI'}")
    for v, ok in has_views.items():
        print(f"  {v}: {'OK' if ok else 'THẤT BẠI'}")
    print("[backup] giữ cho revert:", bdest)
    return bdest


def revert_db(db_path, backup):
    if not backup or not os.path.exists(backup):
        raise SystemExit("--revert cần --backup <path tồn tại>")
    ts = now_stamp()
    sdir = os.path.join(BACKUP_ROOT, "T425_revert_safety_" + ts)
    os.makedirs(sdir, exist_ok=True)
    safety = os.path.join(sdir, "lineage.db")
    src = sqlite3.connect(db_path)
    dst = sqlite3.connect(safety)
    with dst:
        src.backup(dst)
    dst.close()
    src.close()
    print("[revert] đã lưu an toàn DB hiện tại:", safety)
    b = sqlite3.connect(backup)
    d = sqlite3.connect(db_path)
    with d:
        b.backup(d)
    d.close()
    b.close()
    print("[revert] đã khôi phục từ", backup)


def write_report(conn, has_cols, has_views, cmp):
    os.makedirs(OUT_DIR, exist_ok=True)
    p = os.path.join(OUT_DIR, "t425_report.txt")
    with open(p, "w", encoding="utf-8") as f:
        f.write("T425 DRY-RUN — {} — db={}\n".format(
            _dt.datetime.now().isoformat(timespec="seconds"), DB_DEFAULT))
        f.write("=" * 70 + "\n")
        f.write("Cột sẽ thêm:\n")
        for c, e in has_cols.items():
            f.write(f"  {c}: {'ĐÃ CÓ' if e else 'CHƯA CÓ'}\n")
        f.write("VIEW sẽ tạo:\n")
        for v, e in has_views.items():
            f.write(f"  {v}: {'ĐÃ CÓ' if e else 'CHƯA CÓ'}\n")
        f.write("-" * 70 + "\n")
        f.write("DDL:\n")
        for ddl in DDL_ADD_COLUMNS:
            f.write(f"  {ddl}\n")
        f.write(f"  {DDL_SYNC_MAPPING_OK}\n")
        f.write("-" * 70 + "\n")
        f.write("So sánh overlay vs consensus:\n")
        f.write(f"  overlay total: {cmp['ov_total']:,}\n")
        f.write(f"  consensus total: {cmp['cons_total']:,}\n")
        f.write(f"  overlay không trong consensus: {cmp['ov_not_cons']:,}\n")
        f.write(f"  consensus không trong overlay: {cmp['cons_not_ov']:,}\n")
        f.write("=" * 70 + "\n")
        f.write("CHẠY THỬ — KHÔNG GHI DB. Chờ Admin duyệt mới --apply.\n")
    print("Xuất:", p)
    return p


def main():
    ap = argparse.ArgumentParser(description="T425 — thêm cột + VIEW cây (dry-run/apply/revert)")
    ap.add_argument("--dry-run", action="store_true", help="chỉ đọc, xuất báo cáo (mặc định)")
    ap.add_argument("--apply", action="store_true", help="GHI DB (chỉ khi Admin duyệt)")
    ap.add_argument("--revert", action="store_true", help="khôi phục DB từ backup")
    ap.add_argument("--backup", default="", help="đường dẫn backup cho --revert")
    ap.add_argument("--db", default=DB_DEFAULT, help="đường dẫn lineage.db")
    args = ap.parse_args()

    if args.revert:
        revert_db(args.db, args.backup)
        return

    conn = open_ro(args.db)
    has_cols, has_views = dry_run(conn)
    cmp = compare_overlay_consensus(conn)
    conn.close()

    if args.apply:
        apply_db(args.db)
        return

    write_report(conn, has_cols, has_views, cmp)
    print("T425 DRY-RUN — CHỈ ĐỌC, không ghi DB")


if __name__ == "__main__":
    main()