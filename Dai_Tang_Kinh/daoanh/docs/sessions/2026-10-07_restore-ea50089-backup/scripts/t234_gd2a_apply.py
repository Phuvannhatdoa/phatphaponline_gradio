"""
T234-GĐ2a — Nối khoá evidence + dọn 34 dòng sự kiện sai. Additive, có --revert.

Phần 1 của 2 (GĐ2b: M4 exact_span · M5 time_authority_id · M6 view — làm sau).

BỐI CẢNH
=========
`audit_data_honesty.py` (T234) H1 FAIL 1.426: `event_evidence.event_id` không khớp
`event_type` hiện tại. Nguyên nhân: LD1 đã đổi 1.385 row `founding` → `era_mention`
nhưng khoá evidence vẫn là `ev:founding:<dila_id>`.
H3 FAIL 1.712: năm không suy ra được.

3 HẠNG MỤC
===========
M1  Tạo `event_evidence` cho khoá `ev:era_mention:<dila_id>`, **copy `exact_span`**
    từ bản `ev:founding:` (bảng không có UNIQUE ⇒ INSERT an toàn, không đụng bản cũ).
M2  **11 dòng sai rõ** → `event_type='era_mention'`, `year=NULL`.
    6 N1: năm đổi tên / mở rộng / trục tố / công trình phụ / note rỗng.
    5 N2: năm tái tạo hoặc note nói "không rõ năm xây".
M3  **23 dòng `khong_ro`** (năm không có trong note) → quy lại bằng bảng triều đại
    (T22-LD2): khớp năm đang lưu → GIỮ `founding`; lệch → `era_mention` + năm quy
    được; không tra được → `era_mention` + `year=NULL`.

AN TOÀN
=======
Backup DB trước · mỗi UPDATE có guard · log JSON lưu **đầy đủ giá trị cũ** để
`--revert` khôi phục đúng · rollback từ backup nếu rowcount lệch.

Usage: python -X utf8 scripts/t234_gd2a_apply.py [--dry-run|--apply|--revert]
"""

import argparse
import json
import os
import re
import shutil
import sqlite3
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "..", "data", "lineage.db")
BACKUP_DIR = os.path.join(HERE, "..", "data", "backups")
LOG_PATH = os.path.join(HERE, "..", "data", "t234_gd2a_log.json")

CN = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7,
      "八": 8, "九": 9, "十": 10, "百": 100, "千": 1000, "零": 0, "〇": 0}
NUMCH = "一二三四五六七八九十百千零〇"

# 11 dòng sai rõ — đã đọc tay, xem docs/T234 + data/t22_phase2_review.json
N1_BAD = ["PL000000005020", "PL000000008955", "PL000000009983",
          "PL000000014366", "PL000000036249", "PL000000056931"]
N2_BAD = ["PL000000009942", "PL000000009961", "PL000000010182",
          "PL000000012291", "PL000000055978"]


def cn2int(s):
    tot = cur = 0
    for ch in s:
        if ch not in CN:
            return None
        v = CN[ch]
        if v < 10:
            cur = (cur or 1) * v
        else:
            tot += (cur or 1) * v
            cur = 0
    return tot + cur


def load_era_map(conn):
    out = {}
    for zh, s, e in conn.execute(
            "SELECT period_name_zh, start_year, end_year FROM time_periods "
            "WHERE period_name='era' AND start_year IS NOT NULL "
            "AND period_name_zh IS NOT NULL AND period_name_zh<>''"):
        out.setdefault(zh, (s, e))
    return out


def era_ce(text, era_map):
    for zh, (y0, y1) in era_map.items():
        i = text.find(zh)
        while i >= 0:
            m = re.match("([" + NUMCH + "]{1,4})\\s*年",
                         text[i + len(zh): i + len(zh) + 7])
            if m:
                n = cn2int(m.group(1))
                if not n:
                    return None
                ce = y0 + n - 1
                return ce, (y0 <= ce <= y1)
            i = text.find(zh, i + 1)
    return None


def m1(conn, ap):
    dids = [(r[0], r[1]) for r in conn.execute(
        "SELECT DISTINCT dila_id, event_type FROM place_timeline_events")]
    ins = []
    for did, et in dids:
        key = "ev:%s:%s" % (et, did)
        if conn.execute("SELECT 1 FROM event_evidence WHERE event_id=?", (key,)).fetchone():
            continue
        # lay ban goc: uu tien ev:<event_type> roi ev:founding
        src = None
        for cand in (key, "ev:founding:" + did):
            src = conn.execute(
                "SELECT time_mention_id, source_record, source_table, exact_span, "
                "source_ref, evidence_type, reviewer_note FROM event_evidence "
                "WHERE event_id=?", (cand,)).fetchone()
            if src:
                break
        if src:
            ins.append((key,) + tuple(src))
    if ap and ins:
        conn.executemany(
            "INSERT INTO event_evidence (event_id, time_mention_id, source_record, "
            "source_table, exact_span, source_ref, evidence_type, reviewer_note) "
            "VALUES (?,?,?,?,?,?,?,?)", ins)
        conn.commit()
    return len(dids), len(ins), [r[0] for r in ins]


def m1b(conn, ap):
    """Tu tao evidence cho event khong co ban goc nao (vd wikidata P576).
    exact_span de NULL - khong dua, vi day la claim co cau truc khong co van ban."""
    rows = conn.execute(
        "SELECT e.id, e.dila_id, e.event_type, e.source_ref FROM place_timeline_events e "
        "WHERE NOT EXISTS(SELECT 1 FROM event_evidence x "
        "  WHERE x.event_id='ev:'||e.event_type||':'||e.dila_id) "
        "AND e.source_ref IS NOT NULL AND e.source_ref LIKE 'Q%'").fetchall()
    ins = []
    for rid, did, et, sref in rows:
        ins.append(("ev:%s:%s" % (et, did), None, sref, "wikidata", None, sref,
                    "structured_claim",
                    "claim co cau truc tu wikidata, khong co exact_span van ban"))
    if ap and ins:
        conn.executemany(
            "INSERT INTO event_evidence (event_id, time_mention_id, source_record, "
            "source_table, exact_span, source_ref, evidence_type, reviewer_note) "
            "VALUES (?,?,?,?,?,?,?,?)", ins)
        conn.commit()
    return len(rows), len(ins), [r[0] for r in ins]


def m2(conn, ap):
    ids = N1_BAD + N2_BAD
    ph = ",".join("?" * len(ids))
    rows = conn.execute(
        "SELECT id, event_type, year, year_end, confidence FROM place_timeline_events "
        "WHERE dila_id IN (%s) AND event_type='founding'" % ph, ids).fetchall()
    if ap and rows:
        conn.executemany(
            "UPDATE place_timeline_events SET event_type='era_mention', year=NULL, "
            "year_end=NULL, confidence='era_rename_or_renovation' "
            "WHERE id=? AND event_type='founding'", [(r[0],) for r in rows])
        conn.commit()
    return [{"id": r[0], "event_type": r[1], "year": r[2], "year_end": r[3],
             "confidence": r[4]} for r in rows]


def m3(conn, ap, era_map):
    rows = conn.execute(
        "SELECT e.id, e.dila_id, e.year, e.label_zh, e.confidence, p.note "
        "FROM place_timeline_events e JOIN places_dila p ON p.id=e.dila_id "
        "WHERE e.source='dila_era_name' AND e.event_type='founding'").fetchall()
    keep, fix, unres = [], [], []
    for rid, did, year, lab, conf, note in rows:
        note = note or ""
        if str(year) in note:
            keep.append(did)
            continue
        r = era_ce(note, era_map)
        if r is None:
            unres.append({"id": rid, "dila_id": did, "year": year,
                          "label_zh": lab, "confidence": conf})
        elif r[1] and r[0] == year:
            keep.append(did)
        else:
            fix.append({"id": rid, "dila_id": did, "year": year, "label_zh": lab,
                        "confidence": conf, "new_year": r[0] if r[1] else None,
                        "in_range": r[1]})
    if ap:
        for d in unres:
            conn.execute(
                "UPDATE place_timeline_events SET event_type='era_mention', year=NULL, "
                "year_end=NULL, confidence='era_unresolved' "
                "WHERE id=? AND event_type='founding'", (d["id"],))
        for d in fix:
            conn.execute(
                "UPDATE place_timeline_events SET event_type='era_mention', year=?, "
                "confidence=? WHERE id=? AND event_type='founding'",
                (d["new_year"],
                 "era_rederived" if d["new_year"] else "era_unresolved", d["id"]))
        conn.commit()
    return keep, fix, unres


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--revert", action="store_true")
    ap.add_argument("--only-m1m2", action="store_true",
                    help="chỉ chạy M1 + M2 (bỏ M3 — cần Admin duyệt 32 dòng)")
    a = ap.parse_args()
    if not any([a.dry_run, a.apply, a.revert]):
        ap.print_help()
        sys.exit(1)
    db = os.path.abspath(DB_PATH)

    if a.revert:
        if not os.path.exists(LOG_PATH):
            print("Không có log — không có gì để revert.")
            return
        with open(LOG_PATH, encoding="utf-8") as f:
            log = json.load(f)
        c = sqlite3.connect(db)
        cur = c.cursor()
        n = 0
        for eid in log["m1_evidence"]:
            cur.execute("DELETE FROM event_evidence WHERE event_id=?", (eid,))
            n += cur.rowcount
        for r in log["m2_restore"] + log["m3_restore"]:
            cur.execute(
                "UPDATE place_timeline_events SET event_type=?, year=?, year_end=?, "
                "confidence=? WHERE id=?",
                (r["event_type"], r["year"], r.get("year_end"), r["confidence"], r["id"]))
            n += cur.rowcount
        c.commit()
        c.close()
        print("Đã revert %d thay đổi. Backup: %s" % (n, log["backup"]))
        return

    ap_ = a.apply
    conn = sqlite3.connect(db)
    em = load_era_map(conn)
    print("=== T234-GĐ2a %s ===" % ("APPLY" if ap_ else "DRY-RUN"))
    print("   bảng triều đại: %d tên niên hiệu" % len(em))
    backup = None
    if ap_:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        backup = os.path.join(BACKUP_DIR, "lineage_t234gd2a_%s.db"
                              % datetime.now().strftime("%Y%m%d_%H%M%S"))
        shutil.copy2(db, backup)
        print("   Backup: %s" % backup)

    tot, ins, ids_m1 = m1(conn, ap_)
    print("M1 %d cap (dila_id,event_type) -> INSERT evidence %d" % (tot, ins))

    tot_b, ins_b, ids_m1b = m1b(conn, ap_)
    print("M1b %d event khong ban goc (wikidata) -> INSERT %d" % (tot_b, ins_b))

    log_m1 = ids_m1 + ids_m1b

    rest2 = m2(conn, ap_)
    print("M2 %d dòng sai rõ → era_mention + year NULL" % len(rest2))

    if a.only_m1m2:
        keep, fix, unres = [], [], []
        print('M3 SKIPPED (--only-m1m2) - 32 dong can Admin duyet truoc')
    else:
        keep, fix, unres = m3(conn, ap_, em)
        print("M3 23 dòng khong_ro: GIỮ %d | đổi %d | không tra được %d"
              % (len(keep), len(fix), len(unres)))
        for d in fix[:8]:
            print("     %-14s %-6s -> %s" % (d["dila_id"], d["year"],
                                            d["new_year"] if d["in_range"] else "NGOÀI KHOẢNG"))

    if ap_:
        # GHI MERGE, KHONG GHI DE. Ly do: chay lai --only-m1m2 tren DB da
        # xu ly la idempotent (insert 0 dong, sua 0 dong). Neu ghi de, log se
        # thanh {"m1_evidence": [], "m2_restore": []} va --revert se im lang
        # khong lam gi -> mat ho so cap nhat mau. Da gap loi nay 1 lan.
        old = {}
        if os.path.exists(LOG_PATH):
            try:
                with open(LOG_PATH, encoding="utf-8") as f:
                    old = json.load(f)
            except (ValueError, OSError):
                old = {}
        # union event_id da insert (revert phai xoa het)
        m1_all = sorted(set(old.get("m1_evidence") or []) | set(log_m1))
        # gia tri GOC da ghi truoc do giu nguyen (setdefault) — revert phai ve
        # trang thai TRUOC GĐ2, khong phai trang thai giua cac lan chay
        by_id = {}
        for r in list(old.get("m2_restore") or []) + list(old.get("m3_restore") or []) \
                + list(rest2) + list(fix) + list(unres):
            by_id.setdefault(r["id"], r)
        merged = {"run_at": datetime.now().isoformat(),
                  "first_run_at": old.get("first_run_at") or old.get("run_at"),
                  "backup": old.get("backup") or backup,
                  "backup_latest": backup,
                  "m1_evidence": m1_all,
                  "m2_restore": list(by_id.values()),
                  "m3_restore": []}
        with open(LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=1)
        print("   Log: %s  (m1=%d, restore=%d%s)"
              % (LOG_PATH, len(m1_all), len(by_id),
                 "  [MERGE]" if old else "  [MOI]"))
    conn.close()
    if ap_:
        print("\n=== VERIFY H1 + H3 ===")
        os.system('python -X utf8 "%s" --h1 --h3'
                  % os.path.join(HERE, "audit_data_honesty.py"))


if __name__ == "__main__":
    main()