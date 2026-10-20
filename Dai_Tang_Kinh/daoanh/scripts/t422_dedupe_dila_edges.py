#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T422 — Khử trùng cạnh DILA trong lineage_edge_assertions (46.006 → 23.014)
=========================================================================

Mục tiêu:
  Cây DILA đang lưu mỗi cặp thầy–trò 2 lần trong `lineage_edge_assertions`
  (46.006 dòng / 23.014 cặp). Khử trùng và chặn trùng về sau bằng UNIQUE index.

Cách hoạt động (additive, không xoá bảng):
  - Khóa trùng: (source_code, subject_person_id, object_person_id, relation_type)
  - Giữ dòng id NHỎ NHẤT trong mỗi nhóm trùng (id nhỏ nhất = bản ghi cũ nhất).
  - Nếu các dòng trong nhóm có `ref` KHÁC NHAU thì gộp lại (nối bằng "; ").
    (Đo được 2026-10-19: mọi cặp trùng DILA đều có ref=NULL y hệt nhau,
     nên nhánh gộp ref hầu như không kích hoạt — vẫn giữ cho an toàn.)
  - Xoá các dòng còn lại trong nhóm.

Sau khi khử trùng:
  - DILA   = 23.014 dòng
  - MARCUS = 11.169 dòng (không đổi — MARCUS không có trùng)
  - CREATE UNIQUE INDEX uq_lea_src_pair
      ON lineage_edge_assertions(source_code, subject_person_id,
                                 object_person_id, relation_type)

Cách dùng:
  # Bước 1 — chạy thử (KHÔNG ghi DB), xuất TSV + số đếm:
  python -X utf8 scripts/t422_dedupe_dila_edges.py --dry-run

  # Bước 2 — [CHỈ KHI ADMIN ĐÃ DUYỆT KẾT QUẢ BƯỚC 1] ghi DB thật:
  python -X utf8 scripts/t422_dedupe_dila_edges.py --apply

  # Hoàn tác (khôi phục từ backup vừa tạo):
  python -X utf8 scripts/t422_dedupe_dila_edges.py --revert --backup <duong-dan-backup>

Ràng buộc (từ tasks/T422-dila-edge-dedupe-unique.md):
  - KHÔNG xoá bảng cũ.
  - Mọi ghi DB: chạy thử trước → Admin duyệt → backup SQLite API + quick_check → ghi → kiểm lại.
  - Không tự gộp người, không tự tạo cạnh, không dùng bảng gộp / SNA làm nguồn.
  - Không deploy, không push.
"""

import argparse
import os
import sqlite3
import sys
from datetime import datetime

DB_PATH = os.path.join("data", "lineage.db")
OUT_DIR = os.path.join("docs", "sessions", "2026-10-19", "T422")
UNIQUE_INDEX_NAME = "uq_lea_src_pair"
UNIQUE_INDEX_COLS = ("source_code", "subject_person_id",
                     "object_person_id", "relation_type")


def connect_ro():
    """Mở DB ở chế độ CHỈ ĐỌC (uri mode=ro) — dùng cho --dry-run và verify."""
    uri = "file:%s?mode=ro" % DB_PATH.replace("\\", "/")
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def connect_rw():
    """Mở DB ở chế độ GHI — chỉ dùng khi --apply / --revert."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=OFF")
    return conn


def find_duplicate_groups(conn):
    """
    Trả về danh sách nhóm trùng theo khóa (source_code, subject, object, relation_type).

    Mỗi phần tử là dict:
      {source_code, subject_person_id, object_person_id, relation_type,
       count, keep_id, delete_ids, refs, n_refs}
    """
    q = """
        SELECT source_code, subject_person_id, object_person_id, relation_type,
               COUNT(*) AS cnt,
               MIN(id)  AS keep_id,
               GROUP_CONCAT(COALESCE(ref, '')) AS ref_blob
        FROM lineage_edge_assertions
        GROUP BY source_code, subject_person_id, object_person_id, relation_type
        HAVING cnt > 1
        ORDER BY source_code, subject_person_id, object_person_id
    """
    groups = []
    for r in conn.execute(q):
        keep_id = r["keep_id"]
        # Lấy danh sách id cần xoá (mọi id trong nhóm trừ keep_id)
        del_rows = conn.execute("""
            SELECT id, ref FROM lineage_edge_assertions
            WHERE source_code=? AND subject_person_id=? AND object_person_id=? AND relation_type=?
              AND id != ?
            ORDER BY id
        """, (r["source_code"], r["subject_person_id"], r["object_person_id"],
              r["relation_type"], keep_id)).fetchall()
        delete_ids = [d["id"] for d in del_rows]
        # Gộp ref: ref của dòng giữ + ref của các dòng sắp xoá (bỏ None/rỗng, bỏ trùng)
        refs = []
        keep_ref = conn.execute(
            "SELECT ref FROM lineage_edge_assertions WHERE id=?", (keep_id,)
        ).fetchone()["ref"]
        if keep_ref:
            refs.append(keep_ref)
        for d in del_rows:
            if d["ref"] and d["ref"] not in refs:
                refs.append(d["ref"])
        groups.append({
            "source_code": r["source_code"],
            "subject_person_id": r["subject_person_id"],
            "object_person_id": r["object_person_id"],
            "relation_type": r["relation_type"],
            "count": r["cnt"],
            "keep_id": keep_id,
            "delete_ids": delete_ids,
            "refs": refs,
            "n_refs": len(refs),
        })
    return groups


def summarise(conn):
    """Đếm tổng quan trước/sau."""
    per_src_rows = {}
    for r in conn.execute("SELECT source_code, COUNT(*) AS n FROM lineage_edge_assertions GROUP BY source_code"):
        per_src_rows[r["source_code"]] = r["n"]
    per_src_pairs = {}
    for r in conn.execute("""
        SELECT source_code, COUNT(*) AS n FROM (
            SELECT DISTINCT source_code, subject_person_id, object_person_id, relation_type
            FROM lineage_edge_assertions)
        GROUP BY source_code"""):
        per_src_pairs[r["source_code"]] = r["n"]
    total = conn.execute("SELECT COUNT(*) FROM lineage_edge_assertions").fetchone()[0]
    return {"rows": per_src_rows, "pairs": per_src_pairs, "total": total}


def ensure_out_dir():
    os.makedirs(OUT_DIR, exist_ok=True)


def cmd_dry_run():
    """Chạy thử: liệt kê nhóm trùng, xuất TSV + số đếm. KHÔNG ghi DB."""
    print("=" * 68)
    print("T422 — DRY RUN (chỉ đọc, KHÔNG ghi DB)")
    print("=" * 68)

    conn = connect_ro()
    before = summarise(conn)
    groups = find_duplicate_groups(conn)
    conn.close()

    print("\n[TRƯỚC KHỬ TRÙNG]")
    for s in sorted(before["rows"]):
        print("  %-10s rows=%-6d distinct_pairs=%d" %
              (s, before["rows"][s], before["pairs"].get(s, 0)))
    print("  %-10s rows=%d" % ("TOTAL", before["total"]))

    # Phân tích theo nguồn
    by_src = {}
    total_delete = 0
    for g in groups:
        by_src.setdefault(g["source_code"], {"groups": 0, "rows": 0, "delete": 0})
        by_src[g["source_code"]]["groups"] += 1
        by_src[g["source_code"]]["rows"] += g["count"]
        by_src[g["source_code"]]["delete"] += len(g["delete_ids"])
        total_delete += len(g["delete_ids"])

    print("\n[NHÓM TRÙNG THEO NGUỒN]")
    for s in sorted(by_src):
        d = by_src[s]
        print("  %-10s groups=%-6d rows_involved=%-6d will_delete=%d" %
              (s, d["groups"], d["rows"], d["delete"]))

    # Số nhóm có ref khác nhau (cần gộp)
    need_merge = [g for g in groups if g["n_refs"] > 1]
    print("\n[NHÓM CẦN GỘP ref — khác ref trong cùng nhóm]")
    print("  %d nhóm" % len(need_merge))
    if need_merge:
        for g in need_merge[:10]:
            print("    %s->%s refs=%s" %
                  (g["subject_person_id"], g["object_person_id"], g["refs"]))

    # Dự kiến sau khi khử trùng
    print("\n[DỰ KIẾN SAU KHỬ TRÙNG]")
    for s in sorted(before["rows"]):
        will_delete = by_src.get(s, {}).get("delete", 0)
        print("  %-10s rows %d -> %d  (xoá %d)" %
              (s, before["rows"][s], before["rows"][s] - will_delete, will_delete))

    # Kiểm tra điều kiện tạo UNIQUE index có khả thi không
    print("\n[KIỂM TRA UNIQUE INDEX — %s]" % UNIQUE_INDEX_NAME)
    print("  Khóa: (%s)" % ", ".join(UNIQUE_INDEX_COLS))
    feasible = all(g["n_refs"] == 1 or True for g in groups)  # luôn khả thi sau dedupe
    print("  Sau dedupe: mỗi (source, pair, rel) chỉ còn 1 dòng -> UNIQUE khả thi.")
    print("  Đã tồn tại index? (sẽ kiểm lại khi --apply)")

    # Xuất TSV
    ensure_out_dir()
    tsv_path = os.path.join(OUT_DIR, "t422_duplicate_groups.tsv")
    with open(tsv_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("source_code\tsubject_person_id\tobject_person_id\trelation_type\t"
                "count\tkeep_id\tdelete_ids\tn_refs\tmerged_ref\n")
        for g in groups:
            f.write("%s\t%s\t%s\t%s\t%d\t%d\t%s\t%d\t%s\n" % (
                g["source_code"], g["subject_person_id"], g["object_person_id"],
                g["relation_type"], g["count"], g["keep_id"],
                ",".join(str(i) for i in g["delete_ids"]),
                g["n_refs"], ";".join(g["refs"])))
    print("\n[ĐÃ XUẤT] %s  (%d nhóm trùng)" % (tsv_path, len(groups)))

    # Xuất báo cáo text
    rpt_path = os.path.join(OUT_DIR, "t422_dry_run_report.txt")
    with open(rpt_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("T422 DRY RUN — %s\n" % datetime.now().isoformat(timespec="seconds"))
        f.write("=" * 60 + "\n\n")
        f.write("TRUOC:\n")
        for s in sorted(before["rows"]):
            f.write("  %-10s rows=%-6d pairs=%d\n" %
                    (s, before["rows"][s], before["pairs"].get(s, 0)))
        f.write("  TOTAL rows=%d\n\n" % before["total"])
        f.write("NHOM TRUNG:\n")
        for s in sorted(by_src):
            d = by_src[s]
            f.write("  %-10s groups=%-6d rows=%-6d delete=%d\n" %
                    (s, d["groups"], d["rows"], d["delete"]))
        f.write("\nSAU DEDUPE (du kien):\n")
        for s in sorted(before["rows"]):
            will_delete = by_src.get(s, {}).get("delete", 0)
            f.write("  %-10s rows %d -> %d\n" %
                    (s, before["rows"][s], before["rows"][s] - will_delete))
        f.write("\nCan gop ref: %d nhom\n" % len(need_merge))
        f.write("Tong so dong se xoa: %d\n" % total_delete)
    print("[ĐÃ XUẤT] %s" % rpt_path)

    print("\n" + "=" * 68)
    print("DRY RUN HOÀN TẤT — không ghi DB. Dùng --apply sau khi Admin duyệt.")
    print("=" * 68)
    return 0


def cmd_apply(backup_dir=None):
    """
    Ghi DB thật: backup → quick_check → DELETE trùng → CREATE UNIQUE INDEX → verify.
    CHỈ CHẠY KHI ADMIN ĐÃ DUYỆT KẾT QUẢ DRY RUN.
    """
    print("=" * 68)
    print("T422 — APPLY (GHI DB THẬT)")
    print("=" * 68)
    if not os.path.exists(DB_PATH):
        print("[LỖI] Không tìm thấy DB: %s" % DB_PATH)
        return 1

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    if backup_dir is None:
        backup_dir = os.path.join("data", "backups", "T422_%s" % ts)
    os.makedirs(backup_dir, exist_ok=True)
    backup_path = os.path.join(backup_dir, "lineage.db")

    print("\n[BƯỚC 1] Backup SQLite (dùng SQLite backup API, an toàn khi DB đang mở)...")
    src = sqlite3.connect(DB_PATH)
    dst = sqlite3.connect(backup_path)
    with dst:
        src.backup(dst)
    dst.close()
    src.close()
    bk_size = os.path.getsize(backup_path)
    print("  -> %s  (%.1f MB)" % (backup_path, bk_size / (1024 * 1024)))

    print("\n[BƯỚC 2] PRAGMA quick_check trên backup...")
    bconn = sqlite3.connect(backup_path)
    qc = bconn.execute("PRAGMA quick_check;").fetchall()
    bconn.close()
    qc_ok = all(row[0] == "ok" for row in qc)
    print("  -> %s" % ("OK" if qc_ok else qc))
    if not qc_ok:
        print("[DỪNG] Backup không đạt quick_check. Không tiếp tục.")
        return 1

    print("\n[BƯỚC 3] Đếm + phân tích nhóm trùng TRƯỚC khi xoá...")
    conn = connect_rw()
    before = summarise(conn)
    groups = find_duplicate_groups(conn)
    total_delete = sum(len(g["delete_ids"]) for g in groups)
    print("  Trước: %s" % {k: before["rows"][k] for k in sorted(before["rows"])})
    print("  Nhóm trùng: %d nhóm, sẽ xoá %d dòng" % (len(groups), total_delete))

    print("\n[BƯỚC 4] Xoá dòng trùng (giữ id nhỏ nhất trong mỗi nhóm)...")
    cur = conn.cursor()
    deleted = 0
    merged_ref = 0
    try:
        conn.execute("BEGIN")
        for g in groups:
            # Gộp ref nếu cần (nếu dòng giữ có ref NULL mà dòng sắp xoá có ref)
            if g["n_refs"] > 1:
                merged_ref += 1
                cur.execute(
                    "UPDATE lineage_edge_assertions SET ref=? WHERE id=?",
                    (";".join(g["refs"]), g["keep_id"]))
            # Xoá các dòng thừa
            if g["delete_ids"]:
                placeholders = ",".join("?" for _ in g["delete_ids"])
                cur.execute(
                    "DELETE FROM lineage_edge_assertions WHERE id IN (%s)" % placeholders,
                    g["delete_ids"])
                deleted += cur.rowcount
        conn.commit()
    except Exception as e:
        conn.rollback()
        print("[LỖI] rollback. Không ghi gì: %s" % e)
        conn.close()
        return 1

    print("  -> đã xoá %d dòng; đã gộp ref cho %d nhóm" % (deleted, merged_ref))

    print("\n[BƯỚC 5] Tạo UNIQUE index %s..." % UNIQUE_INDEX_NAME)
    try:
        conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS %s
            ON lineage_edge_assertions(%s)
        """ % (UNIQUE_INDEX_NAME, ", ".join(UNIQUE_INDEX_COLS)))
        conn.commit()
        print("  -> OK")
    except Exception as e:
        conn.rollback()
        print("[LỖI] tạo index thất bại: %s" % e)
        print("  Dữ liệu đã khử trùng vẫn nằm trong DB. Dùng backup để hoàn tác nếu cần.")
        conn.close()
        return 1

    print("\n[BƯỚC 6] VERIFY sau khi ghi...")
    after = summarise(conn)
    idx_ok = True
    for r in conn.execute("PRAGMA index_list(lineage_edge_assertions)"):
        if r["name"] == UNIQUE_INDEX_NAME:
            print("  Index %s: unique=%s origin=%s" % (r["name"], r["unique"], r["origin"]))
            for c in conn.execute("PRAGMA index_info(%s)" % UNIQUE_INDEX_NAME):
                print("      col: %s" % c["name"])
    print("\n  SAU:")
    for s in sorted(after["rows"]):
        print("    %-10s rows=%-6d pairs=%d" % (s, after["rows"][s], after["pairs"].get(s, 0)))
    print("    %-10s rows=%d" % ("TOTAL", after["total"]))

    # Kiểm tra còn trùng không
    still = conn.execute("""
        SELECT COUNT(*) FROM (
            SELECT 1 FROM lineage_edge_assertions
            GROUP BY source_code, subject_person_id, object_person_id, relation_type
            HAVING COUNT(*) > 1)
    """).fetchone()[0]
    print("\n  Nhóm trùng còn lại: %d  (mong đợi 0)" % still)

    # Kiểm tra MARCUS không đổi
    marcus_ok = after["rows"].get("MARCUS") == before["rows"].get("MARCUS")
    dila_ok = after["rows"].get("DILA") == before["pairs"].get("DILA")
    print("  MARCUS không đổi: %s (%d)" % (marcus_ok, after["rows"].get("MARCUS")))
    print("  DILA = distinct pairs: %s (%d)" % (dila_ok, after["rows"].get("DILA")))

    # Ghi manifest
    manifest_path = os.path.join(backup_dir, "t422_apply_manifest.txt")
    with open(manifest_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("T422 APPLY — %s\n" % datetime.now().isoformat(timespec="seconds"))
        f.write("DB: %s\n" % DB_PATH)
        f.write("Backup: %s (%.1f MB)\n" % (backup_path, bk_size / (1024 * 1024)))
        f.write("quick_check: %s\n" % ("ok" if qc_ok else qc))
        f.write("Truoc: %s\n" % before["rows"])
        f.write("Sau:   %s\n" % after["rows"])
        f.write("Nhom trung: %d, xoa %d dong, gop ref %d nhom\n" %
                (len(groups), deleted, merged_ref))
        f.write("Con trung sau: %d\n" % still)
        f.write("Index: %s (UNIQUE on %s)\n" % (UNIQUE_INDEX_NAME, ", ".join(UNIQUE_INDEX_COLS)))
    print("\n[ĐÃ GHI] %s" % manifest_path)

    conn.close()

    print("\n" + "=" * 68)
    print("APPLY HOÀN TẤT.")
    print("  Hoàn tác: python -X utf8 scripts/t422_dedupe_dila_edges.py --revert --backup %s" % backup_dir)
    print("=" * 68)
    return 0


def cmd_revert(backup_path):
    """Hoàn tác: khôi phục DB từ backup và DROP unique index."""
    print("=" * 68)
    print("T422 — REVERT (khôi phục từ backup)")
    print("=" * 68)
    if not os.path.exists(backup_path):
        print("[LỖI] Không tìm thấy backup: %s" % backup_path)
        return 1
    print("  Backup: %s" % backup_path)
    # Kiểm backup nhanh
    bconn = sqlite3.connect(backup_path)
    qc = bconn.execute("PRAGMA quick_check;").fetchall()
    bconn.close()
    if not all(row[0] == "ok" for row in qc):
        print("[DỪNG] Backup không đạt quick_check: %s" % qc)
        return 1
    print("  quick_check: OK")

    # Sao lưu DB hiện tại trước khi ghi đè (phòng h)
    safety_dir = os.path.join("data", "backups",
                              "T422_revert_safety_%s" % datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(safety_dir, exist_ok=True)
    safety_path = os.path.join(safety_dir, "lineage.db")
    src = sqlite3.connect(DB_PATH)
    dst = sqlite3.connect(safety_path)
    with dst:
        src.backup(dst)
    dst.close(); src.close()
    print("  Đã lưu DB hiện tại (phòng h): %s" % safety_path)

    # Ghi đè DB từ backup
    src = sqlite3.connect(backup_path)
    dst = sqlite3.connect(DB_PATH)
    with dst:
        src.backup(dst)
    dst.close(); src.close()
    print("  Đã khôi phục DB từ backup.")

    # DROP unique index (nếu tồn tại)
    conn = connect_rw()
    conn.execute("DROP INDEX IF EXISTS %s" % UNIQUE_INDEX_NAME)
    conn.commit()
    conn.close()
    print("  Đã DROP index %s (nếu có)." % UNIQUE_INDEX_NAME)
    print("\nREVERT HOÀN TẤT.")
    return 0


def main():
    ap = argparse.ArgumentParser(description="T422 — khử trùng cạnh DILA")
    ap.add_argument("--dry-run", action="store_true",
                    help="Chỉ đọc, xuất TSV + số đếm, KHÔNG ghi DB")
    ap.add_argument("--apply", action="store_true",
                    help="GHI DB: backup + DELETE trùng + CREATE UNIQUE INDEX")
    ap.add_argument("--revert", action="store_true",
                    help="Hoàn tác từ backup")
    ap.add_argument("--backup", type=str, default=None,
                    help="Thư mục backup (dùng cho --revert: trỏ tới file lineage.db trong đó)")
    args = ap.parse_args()

    if args.dry_run:
        return cmd_dry_run()
    if args.apply:
        return cmd_apply(args.backup)
    if args.revert:
        if not args.backup:
            print("[LỖI] --revert cần --backup <duong-dan-file-lineage.db>")
            return 1
        return cmd_revert(args.backup)

    ap.print_help()
    print("\n[LỖI] Phải chọn --dry-run, --apply hoặc --revert.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
