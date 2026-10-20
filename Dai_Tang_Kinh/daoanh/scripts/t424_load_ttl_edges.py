#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
T424 — Bước 3/5 "3 cây": nạp đầy đủ cạnh TTL → lineage_edge_assertions (source_code=TTL).

Vì sao cần: cạnh TTL hiện nằm riêng ở `dharma_lineage_ttl_vn` (784 cạnh) và bảng cạnh chung
`lineage_edge_assertions` CHỈ có DILA + MARCUS (xem `lea by source`). T185 (`etl_ttl_full_import.py`)
từng nạp 1378 cạnh TTL (2026-09-28) nhưng đã mất khi DB được khôi phục (2026-10-07). T424 nạp lại
TỪ FILE TTL trực tiếp, định danh qua crosswalk T423 (`entity_source_ids` source='TTL_LOCAL') —
KHÔNG dùng khớp tên như T185.

Chế độ:
  --dry-run (MẶC ĐỊNH, chỉ đọc, mode=ro):
      Parse mọi `data/ttl/*.ttl` (bỏ `0-template.ttl`), rút cạnh teacher→student từ
      `bkg:hasTeacher` / `bkg:hasDisciple`; đổi slug → canonical_id (DILA ID hoặc `ptda:<slug>`)
      qua `entity_source_ids` của T423. Xuất TSV + báo cáo vào `docs/sessions/2026-10-19/T424/`:
      số cạnh, đầu accepted/candidate/chưa-map, self-loop, đảo chiều, trùng. KHÔNG ghi DB.

  --apply (CHỈ khi Admin duyệt): backup SQLite + quick_check → INSERT OR IGNORE vào
      `lineage_edge_assertions(source_code='TTL')` cho cạnh 2 đầu ĐÃ map (accepted hoặc candidate).
      mapping_verified=1 nếu cả 2 đầu accepted, ngược lại 0. Cạnh có đầu chưa map → KHÔNG nạp (báo).

  --revert --backup <path>: lưu an toàn DB hiện tại rồi khôi phục từ backup.

Ràng buộc: không xoá bảng cũ; không gộp người; không tự tạo/sửa cạnh; mỗi ghi DB backup trước.
Ghi chú: nguồn `TTL` (theo task + T185 + rebuild consensus) vs registry `TTL_LOCAL` (T423) — xem
báo cáo mục CẢNH BÁO.
"""

import argparse
import datetime as _dt
import glob
import os
import re
import sqlite3
import sys

from rdflib import Graph, URIRef

# ---------------------------------------------------------------------------
# Hằng số
# ---------------------------------------------------------------------------
DB_DEFAULT = os.path.join("data", "lineage.db")
TTL_DIR = os.path.join("data", "ttl")
TEMPLATE_FILE = "0-template.ttl"
BACKUP_ROOT = os.path.join("data", "backups")
OUT_DIR = os.path.join("docs", "sessions", "2026-10-19", "T424")

BKG = "http://www.phatphaponline.org/ontology/buddhist-kg#"
HAS_TEACHER = URIRef(BKG + "hasTeacher")
HAS_DISCIPLE = URIRef(BKG + "hasDisciple")

SRC_CODE = "TTL"
REL_TYPE = "da:isTeacherOf"
TRUST_LEVEL = "L2"          # theo tiền lệ T185
TSV_HEADER = ("teacher_slug\tstudent_slug\tteacher_canonical\tstudent_canonical\t"
              "teacher_status\tstudent_status\tmapping_verified\tref\n")


def now_stamp():
    return _dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def open_ro(db_path):
    return sqlite3.connect("file:{}?mode=ro".format(db_path.replace("\\", "/")), uri=True)


def local_slug(uri):
    """<ex:monk/<slug>> → slug (không phụ thuộc tiền tố ex:)."""
    m = re.search(r"monk/([^>/#]+)$", str(uri))
    return m.group(1) if m else str(uri)


# ---------------------------------------------------------------------------
# Parse TTL → cạnh
# ---------------------------------------------------------------------------
def parse_edges():
    """Trả về (edges, selfloops, reverse_raw, n_files_ok, n_files_fail, fail_list).

    edges: dict (teacher_slug, student_slug) -> ref (tên file TTL gốc)
    selfloops: set (slug, slug, ref)
    """
    edges = {}
    selfloops = set()
    ok = fail = 0
    fail_list = []
    files = sorted(f for f in glob.glob(os.path.join(TTL_DIR, "*.ttl"))
                   if os.path.basename(f) != TEMPLATE_FILE and os.path.isfile(f))
    for fpath in files:
        ref = os.path.basename(fpath)
        try:
            g = Graph()
            g.parse(fpath, format="turtle")
        except Exception as ex:
            fail += 1
            fail_list.append((ref, str(ex)))
            continue
        ok += 1
        for s, _p, o in g.triples((None, HAS_TEACHER, None)):
            t, st = local_slug(o), local_slug(s)          # object = thầy, subject = trò
            if t == st:
                selfloops.add((t, st, ref))
            else:
                edges.setdefault((t, st), ref)
        for s, _p, o in g.triples((None, HAS_DISCIPLE, None)):
            t, st = local_slug(s), local_slug(o)          # subject = thầy, object = trò
            if t == st:
                selfloops.add((t, st, ref))
            else:
                edges.setdefault((t, st), ref)
    return edges, selfloops, ok, fail, fail_list


# ---------------------------------------------------------------------------
# Crosswalk T423: slug → entity_id → canonical (DILA ID hoặc ptda:)
# ---------------------------------------------------------------------------
def build_crosswalk(conn):
    cur = conn.cursor()
    slug2ent = {}
    slug2status = {}
    for slug, ent, ms in cur.execute(
            "SELECT source_entity_id, entity_id, match_status "
            "FROM entity_source_ids WHERE source='TTL_LOCAL'"):
        slug2ent[slug] = ent
        slug2status[slug] = ms
    ent2dila = {}
    for ent, dila in cur.execute(
            "SELECT entity_id, MIN(source_entity_id) FROM entity_source_ids "
            "WHERE source='DILA' GROUP BY entity_id"):
        ent2dila[ent] = dila

    def resolve(slug):
        if slug not in slug2ent:
            return None, None, "unmapped"
        ent = slug2ent[slug]
        canon = ent2dila.get(ent) or ("ptda:" + slug)
        return canon, ent, slug2status.get(slug, "?")

    return resolve, len(slug2ent)


# ---------------------------------------------------------------------------
# Phân loại
# ---------------------------------------------------------------------------
def classify(edges, selfloops, resolve):
    rows = []                      # mỗi cạnh (slug_space)
    unmapped_slugs = set()
    for (t, s), ref in sorted(edges.items()):
        tc, te, ts = resolve(t)
        sc, se, ss = resolve(s)
        if tc is None:
            unmapped_slugs.add(t)
        if sc is None:
            unmapped_slugs.add(s)
        rows.append({
            "t_slug": t, "s_slug": s, "t_canon": tc or "", "s_canon": sc or "",
            "t_status": ts, "s_status": ss, "ref": ref,
            "t_ent": te, "s_ent": se,
        })

    # Cạnh ĐỀ XUẤT nạp: cả 2 đầu đã map (accepted hoặc candidate)
    insertable = [r for r in rows if r["t_canon"] and r["s_canon"]]

    # Sụp canonical: nhiều slug-pair → 1 canonical-pair (do N:1) → dedupe + self-loop canonical
    canon_pairs = {}
    canon_selfloop = []
    for r in insertable:
        key = (r["t_canon"], r["s_canon"])
        if r["t_canon"] == r["s_canon"]:
            canon_selfloop.append(r)
            continue
        canon_pairs.setdefault(key, r)

    # Đảo chiều (theo canonical, trên tập đã dedupe)
    reverse = []
    for (a, b) in sorted(canon_pairs):
        if (b, a) in canon_pairs:
            reverse.append((a, b))

    return rows, insertable, canon_pairs, canon_selfloop, reverse, unmapped_slugs


def summarize(rows, insertable, canon_pairs, canon_selfloop, reverse, unmapped_slugs, selfloops):
    combos = {}
    for r in insertable:
        k = "{} / {}".format(r["t_status"], r["s_status"])
        combos[k] = combos.get(k, 0) + 1
    both_accepted = sum(1 for r in insertable
                        if r["t_status"] == "accepted" and r["s_status"] == "accepted")
    return {
        "edges_distinct_slug": len(rows),
        "selfloop_ttl": len(selfloops),
        "insertable_both_mapped": len(insertable),
        "insertable_dedupe_canonical": len(canon_pairs),
        "canonical_selfloop_after_collapse": len(canon_selfloop),
        "both_accepted": both_accepted,
        "reverse_pairs": len(reverse) // 2,
        "slugs_unmapped": len(unmapped_slugs),
        "edges_skipped_unmapped": len(rows) - len(insertable),
        "endpoint_combos": combos,
    }


# ---------------------------------------------------------------------------
# Báo cáo
# ---------------------------------------------------------------------------
def write_reports(rows, insertable, canon_pairs, canon_selfloop, reverse,
                  unmapped_slugs, selfloops, ok, fail, fail_list, n_xwalk, s, db_path):
    os.makedirs(OUT_DIR, exist_ok=True)
    files = []

    # 1) tất cả cạnh slug-space
    p1 = os.path.join(OUT_DIR, "t424_edges.tsv")
    with open(p1, "w", encoding="utf-8-sig", newline="") as f:
        f.write(TSV_HEADER)
        for r in rows:
            mv = 1 if (r["t_status"] == "accepted" and r["s_status"] == "accepted") else 0
            f.write("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(
                r["t_slug"], r["s_slug"], r["t_canon"], r["s_canon"],
                r["t_status"], r["s_status"], mv, r["ref"]))
    files.append(p1)

    # 2) self-loop (slug)
    p2 = os.path.join(OUT_DIR, "t424_selfloops.tsv")
    with open(p2, "w", encoding="utf-8-sig", newline="") as f:
        f.write("slug\tref\n")
        for slug, _st, ref in sorted(selfloops):
            f.write("{}\t{}\n".format(slug, ref))
    files.append(p2)

    # 3) đảo chiều (canonical) — mỗi cặp 1 dòng
    p3 = os.path.join(OUT_DIR, "t424_reverse_pairs.tsv")
    with open(p3, "w", encoding="utf-8-sig", newline="") as f:
        f.write("canon_a\tcanon_b\tref_a_b\tref_b_a\n")
        seen = set()
        for (a, b) in sorted(reverse):
            if (b, a) in seen:
                continue
            seen.add((a, b))
            ra = canon_pairs[(a, b)]["ref"]
            rb = canon_pairs[(b, a)]["ref"]
            f.write("{}\t{}\t{}\t{}\n".format(a, b, ra, rb))
    files.append(p3)

    # 4) slug chưa map
    p4 = os.path.join(OUT_DIR, "t424_unmapped_slugs.tsv")
    with open(p4, "w", encoding="utf-8-sig", newline="") as f:
        f.write("slug\n")
        for slug in sorted(unmapped_slugs):
            f.write(slug + "\n")
    files.append(p4)

    # 5) báo cáo tổng hợp
    p5 = os.path.join(OUT_DIR, "t424_report.txt")
    with open(p5, "w", encoding="utf-8") as f:
        f.write("T424 DRY-RUN — {} — db={}\n".format(
            _dt.datetime.now().isoformat(timespec="seconds"), db_path))
        f.write("=" * 74 + "\n")
        f.write("Parse TTL: {} file OK | {} file lỗi (bỏ '{}')\n".format(ok, fail, TEMPLATE_FILE))
        for ref, err in fail_list:
            f.write("    [lỗi parse] {}: {}\n".format(ref, err))
        f.write("Crosswalk T423 (entity_source_ids source='TTL_LOCAL'): {} slug\n".format(n_xwalk))
        f.write("-" * 74 + "\n")
        for k, v in s.items():
            if k == "endpoint_combos":
                f.write("  {:<34}: {}\n".format(k, ""))
                for kk, vv in sorted(v.items(), key=lambda x: -x[1]):
                    f.write("      {:<28} {}\n".format(kk, vv))
            else:
                f.write("  {:<34}: {}\n".format(k, v))
        f.write("-" * 74 + "\n")
        f.write("Self-loop (slug, theo file TTL): {}\n".format(len(selfloops)))
        f.write("Self-loop SAU KHI sụp canonical (N:1): {}\n".format(len(canon_selfloop)))
        for r in canon_selfloop[:20]:
            f.write("    {} → {}\n".format(r["t_slug"], r["t_canon"]))
        f.write("-" * 74 + "\n")
        f.write("Đảo chiều (canonical) — {} cặp:\n".format(s["reverse_pairs"]))
        seen = set()
        for (a, b) in sorted(reverse):
            if (b, a) in seen:
                continue
            seen.add((a, b))
            f.write("    {} ⇄ {}\n".format(a, b))
        f.write("-" * 74 + "\n")
        f.write("Slug chưa map ({}): {}\n".format(
            len(unmapped_slugs), ", ".join(sorted(unmapped_slugs)[:40])
            + (" …" if len(unmapped_slugs) > 40 else "")))
        f.write("=" * 74 + "\n")
        f.write("CẢNH BÁO (cần Admin quyết):\n")
        f.write("  1. source_code: task/T185/rebuild-consensus dùng 'TTL'; T423 lại đăng ký\n")
        f.write("     data_sources='TTL_LOCAL'. Bản này dùng '{}'. Nếu chọn 'TTL_LOCAL' thì\n".format(SRC_CODE))
        f.write("     phải sửa cả rebuild consensus (đang đọc source_code='TTL').\n")
        f.write("  2. 66 slug TTL chưa có hồ sơ định danh → cạnh có đầu này BỊ BỎ (không nạp).\n")
        f.write("  3. Cạnh candidate: nạp kèm mapping_verified=0 (T425 thêm cột mapping_ok).\n")
        f.write("  4. trust_level='{}' (theo tiền lệ T185).\n".format(TRUST_LEVEL))
        f.write("  5. Đảo chiều / self-loop canonical: KHÔNG tự sửa, chỉ báo (danh sách trên).\n")
        f.write("={0:^74}\n".format(" CHẠY THỬ — KHÔNG GHI DB. Chờ Admin duyệt mới --apply. "))
    files.append(p5)
    return files


# ---------------------------------------------------------------------------
# Ghi DB
# ---------------------------------------------------------------------------
def apply_db(db_path, insertable, canon_pairs):
    ts = now_stamp()
    bdir = os.path.join(BACKUP_ROOT, "T424_" + ts)
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

    now = _dt.datetime.now().isoformat(timespec="seconds")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(MAX(id),0) FROM lineage_edge_assertions")
    id_before = cur.fetchone()[0]
    n_ins = 0
    try:
        cur.execute("BEGIN")
        for (a, b), r in sorted(canon_pairs.items()):
            mv = 1 if (r["t_status"] == "accepted" and r["s_status"] == "accepted") else 0
            cur.execute(
                """INSERT OR IGNORE INTO lineage_edge_assertions
                   (edge_key, subject_person_id, relation_type, object_person_id,
                    source_code, raw_relation_type, ref, mapping_verified, trust_level,
                    status, created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                ("{}|{}|{}".format(SRC_CODE, a, b), a, REL_TYPE, b,
                 SRC_CODE, REL_TYPE, r["ref"], mv, TRUST_LEVEL, "active", now))
            n_ins += cur.rowcount
        conn.commit()
    except Exception:
        conn.rollback()
        conn.close()
        raise
    cur.execute("SELECT COALESCE(MAX(id),0) FROM lineage_edge_assertions")
    id_after = cur.fetchone()[0]
    total = cur.execute(
        "SELECT COUNT(*) FROM lineage_edge_assertions WHERE source_code=?",
        (SRC_CODE,)).fetchone()[0]
    conn.close()

    with open(os.path.join(bdir, "t424_apply_manifest.txt"), "w", encoding="utf-8") as f:
        f.write("T424 APPLY {}\n".format(now))
        f.write("backup={}\n".format(bdest))
        f.write("rows_inserted={}  id_range={}..{}\n".format(n_ins, id_before + 1, id_after))
        f.write("source_code_total={}\n".format(total))
        f.write("REVERT: python -X utf8 scripts/t424_load_ttl_edges.py --revert --backup {}\n".format(bdest))
    print("[apply] +{} dòng | id {}..{} | tổng source_code={}: {}".format(
        n_ins, id_before + 1, id_after, SRC_CODE, total))
    print("[backup] giữ cho revert: {}".format(bdest))
    return bdest


def revert_db(db_path, backup):
    if not backup or not os.path.exists(backup):
        raise SystemExit("--revert cần --backup <path tồn tại>")
    ts = now_stamp()
    sdir = os.path.join(BACKUP_ROOT, "T424_revert_safety_" + ts)
    os.makedirs(sdir, exist_ok=True)
    safety = os.path.join(sdir, "lineage.db")
    src = sqlite3.connect(db_path)
    dst = sqlite3.connect(safety)
    with dst:
        src.backup(dst)
    dst.close()
    src.close()
    print("[revert] đã lưu an toàn DB hiện tại: {}".format(safety))
    b = sqlite3.connect(backup)
    d = sqlite3.connect(db_path)
    with d:
        b.backup(d)
    d.close()
    b.close()
    print("[revert] đã khôi phục từ {}".format(backup))


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="T424 — nạp cạnh TTL vào lineage_edge_assertions")
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
    resolve, n_xwalk = build_crosswalk(conn)
    conn.close()

    edges, selfloops, ok, fail, fail_list = parse_edges()
    rows, insertable, canon_pairs, canon_selfloop, reverse, unmapped = classify(
        edges, selfloops, resolve)
    s = summarize(rows, insertable, canon_pairs, canon_selfloop, reverse, unmapped, selfloops)

    if args.apply:
        apply_db(args.db, insertable, canon_pairs)
        return

    files = write_reports(rows, insertable, canon_pairs, canon_selfloop, reverse,
                          unmapped, selfloops, ok, fail, fail_list, n_xwalk, s, args.db)
    print("T424 DRY-RUN — CHỈ ĐỌC, không ghi DB")
    for k, v in s.items():
        if k == "endpoint_combos":
            print("  {:<34}:".format(k))
            for kk, vv in sorted(v.items(), key=lambda x: -x[1]):
                print("      {:<28} {}".format(kk, vv))
        else:
            print("  {:<34}: {}".format(k, v))
    print("Xuất:")
    for p in files:
        print("  " + p)


if __name__ == "__main__":
    main()
