#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
T423 — Bước 2/5 "3 cây": đăng ký nguồn TTL_LOCAL + định danh người ptda: + mapping TTL → entity_hub.

Vì sao cần: TTL (Thiền sư Việt Nam) chưa phải một nguồn trong lớp định danh. Ta KHÔNG tạo
bảng persons mới mà dùng lại lớp sẵn có `entity_hub` + `entity_source_ids` (SSOT mapping).

Chế độ:
  --dry-run (MẶC ĐỊNH, chỉ đọc, mở DB qua mode=ro):
      Đề xuất 1 dòng `data_sources(TTL_LOCAL)`; danh sách ~204 thiền sư TTL chưa có DILA ID
      → `entity_hub(PERSON, canonical_label='ptda:<slug>')`; mapping mọi hồ sơ TTL (bỏ dòng alias)
      → `entity_source_ids(source='TTL_LOCAL', source_entity_id=<slug>, match_status, confidence, note)`.
      Xuất TSV + báo cáo + danh sách cần Admin duyệt vào `docs/sessions/2026-10-19/T423/`.

  --apply (CHỈ khi Admin duyệt): backup SQLite API + quick_check → INSERT data_sources + entity_hub
      + entity_source_ids → tạo UNIQUE partial index (mỗi (source, source_entity_id) tối đa 1 'accepted').

  --revert --backup <path>: lưu an toàn DB hiện tại rồi khôi phục từ backup + DROP index.

Quy tắc trạng thái (theo task T423):
  - khớp 1–1 rõ ràng (DILA ID chỉ 1 hồ sơ non-alias trỏ tới) → accepted
  - mơ hồ: 26 DILA ID bị nhiều hồ sơ non-alias trỏ tới (N:1) → candidate
  - sai đã biết BUG-038 (Lâm Tế→A032162, Mã Tổ→A038890, Hoàng Bá chưa map) → candidate + đề xuất đúng
  - chưa có DILA ID → candidate (định danh cục bộ ptda:, chờ Admin đối chiếu)

Ràng buộc: không xoá bảng cũ; không gộp người; không tạo cạnh; mỗi ghi DB phải backup trước.
Không git-track gì trong script này.
"""

import argparse
import datetime as _dt
import os
import sqlite3
import sys

# ---------------------------------------------------------------------------
# Hằng số cấu hình
# ---------------------------------------------------------------------------
DB_DEFAULT = os.path.join("data", "lineage.db")
BACKUP_ROOT = os.path.join("data", "backups")
OUT_DIR = os.path.join("docs", "sessions", "2026-10-19", "T423")

SRC_CODE = "TTL_LOCAL"
SRC_NAME = "TTL Thiền Sư Việt Nam (bản địa)"
SRC_TYPE = "lineage_authority"
ENTITY_HUB_STATUS = "active"
PARTIAL_INDEX = "uq_esi_source_srcid_accepted"

# BUG-038: mapping sai đã biết → (dila_id_hiện_tại, dila_id_đề_xuất, ghi_chú)
BUG038 = {
    "lam_te_nghia_huyen": ("A032162", "A003627",
                           "BUG-038: A032162 là 義玄 triều Joseon (Triều Tiên), không phải Lâm Tế Nghĩa Huyền nhà Đường"),
    "ma_to_dao_nhat": ("A038890", "A003623",
                       "BUG-038: A038890 là 道一/みちかず (Nhật), không phải Mã Tổ Đạo Nhất 馬祖道一"),
    "hoang_ba_hy_van": ("", "A000490",
                        "BUG-038: chưa nối DILA; tên hiện 'Hơi Vận' sai, nên là Hoàng Bá Hy Vận (希運)"),
}

# Độ tin cậy gợi ý theo nhóm
CONF_ACCEPTED = 0.99
CONF_N1 = 0.50
CONF_BUG038 = 0.30
CONF_LOCAL = 0.30


def now_stamp():
    return _dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def open_ro(db_path):
    """Mở DB CHỈ ĐỌC (URI mode=ro) — dùng cho --dry-run."""
    return sqlite3.connect("file:{}?mode=ro".format(db_path.replace("\\", "/")), uri=True)


# ---------------------------------------------------------------------------
# Phân tích & phân loại
# ---------------------------------------------------------------------------
def classify(conn):
    """Trả về dict kết quả phân loại. CHỈ chạy SELECT."""
    cur = conn.cursor()

    # N:1 trên các hồ sơ NON-alias: dila_id bị > 1 slug non-alias trỏ tới
    n1 = {}
    for dila_id, n, ids in cur.execute(
        """SELECT dila_id, COUNT(*), GROUP_CONCAT(id, '|')
           FROM vn_person_authority
           WHERE id NOT LIKE 'alias_%' AND dila_id IS NOT NULL AND dila_id <> ''
           GROUP BY dila_id HAVING COUNT(*) > 1"""
    ):
        n1[dila_id] = ids.split("|")

    # Bảng tra dila_id -> entity_id (qua entity_source_ids nguồn DILA)
    dila2ent = {}
    for dila_id, ent in cur.execute(
        """SELECT source_entity_id, MIN(entity_id) FROM entity_source_ids
           WHERE source = 'DILA' GROUP BY source_entity_id"""
    ):
        dila2ent[dila_id] = ent

    # Id lớn nhất hiện có trong entity_hub (để cấp id cho entity ptda: mới)
    max_ent = cur.execute("SELECT COALESCE(MAX(entity_id), 0) FROM entity_hub").fetchone()[0]

    rows = list(cur.execute(
        """SELECT id, name_vi, name_zh, dila_id, status, entity_type, ttl_filename
           FROM vn_person_authority
           WHERE id NOT LIKE 'alias_%'
           ORDER BY id"""
    ))

    new_local = []      # (slug, name_vi) cần tạo entity_hub ptda:
    mappings = []       # dict mỗi hồ sơ TTL -> entity_source_ids
    next_ent = max_ent + 1

    for slug, name_vi, name_zh, dila_id, status, etype, ttl_fn in rows:
        has_dila = bool(dila_id and dila_id.strip())
        note_parts = []
        if slug in BUG038:
            cur_dila, suggest, why = BUG038[slug]
            match_status, conf = "candidate", CONF_BUG038
            note_parts.append(why)
            note_parts.append("đề xuất dila_id = {}".format(suggest or "(cần Admin xác định)"))
            note_parts.append("chờ Admin")
            if has_dila:
                ent = dila2ent.get(dila_id)
            else:
                ent = next_ent
                new_local.append((slug, name_vi))
                next_ent += 1
                note_parts.append("định danh cục bộ ptda:{}".format(slug))
        elif not has_dila:
            match_status, conf = "candidate", CONF_LOCAL
            ent = next_ent
            new_local.append((slug, name_vi))
            next_ent += 1
            note_parts.append("chưa có DILA ID — định danh cục bộ ptda:{}; chờ Admin đối chiếu".format(slug))
        elif dila_id in n1:
            match_status, conf = "candidate", CONF_N1
            ent = dila2ent.get(dila_id)
            note_parts.append("N:1 — dila_id {} dùng chung bởi {} hồ sơ non-alias: {}".format(
                dila_id, len(n1[dila_id]), "|".join(n1[dila_id])))
        else:
            match_status, conf = "accepted", CONF_ACCEPTED
            ent = dila2ent.get(dila_id)
            note_parts.append("khớp 1–1 rõ ràng (DILA ID {} chỉ 1 hồ sơ non-alias)".format(dila_id))

        if ent is None:
            # Không tra được entity đích — hạ xuống candidate và đánh dấu để Admin xem
            match_status, conf = "candidate", min(conf, CONF_LOCAL)
            note_parts.append("KHÔNG tra được entity_id cho dila_id={} (cần rà)".format(dila_id))

        mappings.append({
            "slug": slug,
            "name_vi": name_vi,
            "name_zh": name_zh,
            "dila_id": dila_id or "",
            "entity_id": ent,
            "match_status": match_status,
            "confidence": conf,
            "verification_note": "; ".join(note_parts),
            "ttl_filename": ttl_fn or "",
        })

    # Danh sách xung đột alias (chỉ báo cáo, KHÔNG nạp)
    alias_conflicts = list(cur.execute(
        """SELECT id, dila_id, name_vi FROM vn_person_authority
           WHERE id LIKE 'alias_%' ORDER BY id"""
    ))

    # Đối chiếu 5 dòng ttl_mapping verified
    ttm = list(cur.execute("SELECT ttl_filename, name_vi, dila_id, status FROM ttl_mapping"))

    return {
        "n1": n1,
        "dila2ent": dila2ent,
        "max_ent": max_ent,
        "rows": rows,
        "new_local": new_local,
        "mappings": mappings,
        "alias_conflicts": alias_conflicts,
        "ttl_mapping": ttm,
    }


def summarize(res):
    maps = res["mappings"]
    by = {}
    for m in maps:
        by.setdefault(m["match_status"], []).append(m)
    return {
        "total_non_alias": len(maps),
        "accepted": len(by.get("accepted", [])),
        "candidate": len(by.get("candidate", [])),
        "new_local": len(res["new_local"]),
        "n1_dila_ids": len(res["n1"]),
        "bug038": sum(1 for m in maps if m["slug"] in BUG038),
        "alias_rows": len(res["alias_conflicts"]),
    }


# ---------------------------------------------------------------------------
# Xuất báo cáo (dry-run)
# ---------------------------------------------------------------------------
def write_reports(res, db_path):
    os.makedirs(OUT_DIR, exist_ok=True)
    s = summarize(res)

    # 1) TSV mapping đầy đủ
    p_map = os.path.join(OUT_DIR, "t423_entity_source_ids.tsv")
    with open(p_map, "w", encoding="utf-8-sig", newline="") as f:
        f.write("slug\tname_vi\tname_zh\tdila_id\tentity_id\tmatch_status\tconfidence\tverification_note\tttl_filename\n")
        for m in res["mappings"]:
            f.write("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(
                m["slug"], m["name_vi"] or "", m["name_zh"] or "", m["dila_id"],
                m["entity_id"], m["match_status"], m["confidence"],
                m["verification_note"], m["ttl_filename"]))

    # 2) TSV entity_hub mới (ptda:)
    p_hub = os.path.join(OUT_DIR, "t423_entity_hub_new.tsv")
    with open(p_hub, "w", encoding="utf-8-sig", newline="") as f:
        f.write("entity_id\tentity_type\tcanonical_label\tname_vi\n")
        base = res["max_ent"]
        for i, (slug, name_vi) in enumerate(res["new_local"]):
            f.write("{}\tPERSON\tptda:{}\t{}\n".format(base + 1 + i, slug, name_vi or ""))

    # 3) TSV xung đột alias (chỉ báo cáo)
    p_al = os.path.join(OUT_DIR, "t423_alias_conflicts.tsv")
    with open(p_al, "w", encoding="utf-8-sig", newline="") as f:
        f.write("alias_slug\tdila_id\tname_vi\n")
        for a, d, nv in res["alias_conflicts"]:
            f.write("{}\t{}\t{}\n".format(a, d or "", nv or ""))

    # 4) Báo cáo tổng hợp
    p_rep = os.path.join(OUT_DIR, "t423_dry_run_report.txt")
    with open(p_rep, "w", encoding="utf-8") as f:
        f.write("T423 DRY-RUN — {} — db={}\n".format(_dt.datetime.now().isoformat(timespec="seconds"), db_path))
        f.write("=" * 70 + "\n")
        f.write("Đề xuất data_sources: source_code={} name='{}' type={}\n".format(SRC_CODE, SRC_NAME, SRC_TYPE))
        f.write("entity_id lớn nhất hiện tại: {}  → cấp mới từ {}\n".format(res["max_ent"], res["max_ent"] + 1))
        f.write("-" * 70 + "\n")
        for k, v in s.items():
            f.write("  {:<20}: {}\n".format(k, v))
        f.write("-" * 70 + "\n")
        f.write("N:1 (dila_id bị nhiều hồ sơ non-alias trỏ) — {} nhóm:\n".format(len(res["n1"])))
        for d, ids in sorted(res["n1"].items()):
            f.write("  {} x{}: {}\n".format(d, len(ids), "|".join(ids)))
        f.write("-" * 70 + "\n")
        f.write("BUG-038 (candidate + đề xuất):\n")
        for m in res["mappings"]:
            if m["slug"] in BUG038:
                f.write("  {}\t{}\t{}\n".format(m["slug"], m["entity_id"], m["verification_note"]))
        f.write("-" * 70 + "\n")
        f.write("Đối chiếu ttl_mapping ({} dòng):\n".format(len(res["ttl_mapping"])))
        for fn, nv, did, st in res["ttl_mapping"]:
            f.write("  {} | {} | {} | {}\n".format(fn, nv, did, st))
        f.write("=" * 70 + "\n")
        f.write("GHI CHÚ: đây là CHẠY THỬ, KHÔNG ghi DB. Chờ Admin duyệt mới --apply.\n")

    return [p_map, p_hub, p_al, p_rep], s


# ---------------------------------------------------------------------------
# Ghi DB (--apply)
# ---------------------------------------------------------------------------
def apply_db(db_path, res):
    s = summarize(res)
    ts = now_stamp()
    bdir = os.path.join(BACKUP_ROOT, "T423_" + ts)
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
        cur.execute("BEGIN")
        # (1) data_sources
        cur.execute(
            """INSERT INTO data_sources(source_code, source_name, source_type, active, created_at,
                                       canonical_name, short_name, integration_mode)
               VALUES (?,?,?,1,?,?,?,?)""",
            (SRC_CODE, SRC_NAME, SRC_TYPE, _dt.datetime.now().isoformat(timespec="seconds"),
             SRC_NAME, SRC_CODE, "local_dump"))
        now = _dt.datetime.now().isoformat(timespec="seconds")
        # (2) entity_hub ptda: (cấp id từ max_ent+1)
        base = res["max_ent"]
        cur.executemany(
            """INSERT INTO entity_hub(entity_id, entity_type, canonical_label, status, created_at, updated_at)
               VALUES (?,?,?,?,?,?)""",
            [(base + 1 + i, "PERSON", "ptda:" + slug, ENTITY_HUB_STATUS, now, now)
             for i, (slug, _nv) in enumerate(res["new_local"])])
        # (3) entity_source_ids (source=TTL_LOCAL)
        cur.executemany(
            """INSERT INTO entity_source_ids(entity_id, source, source_entity_id, source_label,
                                             match_status, confidence, verified, verification_note,
                                             created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            [(m["entity_id"], SRC_CODE, m["slug"], m["name_vi"], m["match_status"],
              m["confidence"], 0, m["verification_note"], now, now) for m in res["mappings"]])
        # (4) UNIQUE partial index
        cur.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS {} ON entity_source_ids(source, source_entity_id) "
            "WHERE match_status = 'accepted'".format(PARTIAL_INDEX))
        conn.commit()
    except Exception:
        conn.rollback()
        conn.close()
        raise
    conn.close()
    print("[apply] xong: data_sources+1, entity_hub+{}, entity_source_ids+{} (accepted={})".format(
        s["new_local"], s["total_non_alias"], s["accepted"]))
    print("[backup] giữ cho revert: {}".format(bdest))
    return bdest


def revert_db(db_path, backup):
    if not backup or not os.path.exists(backup):
        raise SystemExit("--revert cần --backup <path tồn tại>")
    ts = now_stamp()
    sdir = os.path.join(BACKUP_ROOT, "T423_revert_safety_" + ts)
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
    try:
        c = sqlite3.connect(db_path)
        c.execute("DROP INDEX IF EXISTS {}".format(PARTIAL_INDEX))
        c.commit()
        c.close()
    except Exception as e:
        print("[revert] cảnh báo DROP INDEX: {}".format(e))
    print("[revert] đã khôi phục từ {}".format(backup))


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="T423 — đăng ký TTL_LOCAL + mapping TTL (dry-run/apply/revert)")
    ap.add_argument("--dry-run", action="store_true", help="chỉ đọc, xuất đề xuất (mặc định)")
    ap.add_argument("--apply", action="store_true", help="GHI DB (chỉ khi Admin duyệt)")
    ap.add_argument("--revert", action="store_true", help="khôi phục DB từ backup")
    ap.add_argument("--backup", default="", help="đường dẫn backup cho --revert")
    ap.add_argument("--db", default=DB_DEFAULT, help="đường dẫn lineage.db")
    args = ap.parse_args()

    if args.revert:
        revert_db(args.db, args.backup)
        return
    if args.apply:
        res = classify(open_ro(args.db))
        apply_db(args.db, res)
        return

    # mặc định: dry-run
    res = classify(open_ro(args.db))
    files, s = write_reports(res, args.db)
    print("T423 DRY-RUN — CHỈ ĐỌC, không ghi DB")
    for k, v in s.items():
        print("  {:<20}: {}".format(k, v))
    print("Xuất:")
    for p in files:
        print("  " + p)


if __name__ == "__main__":
    main()
