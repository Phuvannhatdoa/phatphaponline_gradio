"""
T234-GD2b/M5 — Noi 96 dong `time_authority_id='reign_era_dict'` placeholder
sang `time_periods.id` THAT (bang trieu dai/era cua T22-LD2, 216 dong).

VAN DE
======
`time_mentions.time_authority_id` co 96 row tro toi placeholder `'reign_era_dict'`
— mot chuoi GIA DINH, khong phai khoa. Ket qua: UI khong hien duoc nguon,
gate H2 FAIL.

`raw_time_zh` VAN CON day du: vi du `明洪熙元年` = trieu dai `明` + nien hieu
`洪熙` + `元年`. => hoàn toàn khoi phuc duoc.

QUY TAC HON TRONG
=================
1. Chi gan khi xac dinh DUY NHAT 1 `time_periods.id` (khop ca trieu dai).
2. Niên hiệu trùng tên giữa nhiều triều đại mà không có tiền tố triều đại
   (vd đứng một mình `大安`) ⇒ **để NULL**, KHÔNG đoán.
3. Không tạo id giả (bản nháp cũ dựng `era:<zh>` sai — đã bỏ).

Usage: python -X utf8 scripts/t234_gd2b_h2_authority.py [--dry-run|--apply|--revert]
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
LOG_PATH = os.path.join(HERE, "..", "data", "t234_gd2b_log.json")

PLACEHOLDER = "reign_era_dict"
YEAR_RE = re.compile("(\\d{1,4})\\s*年|元年|元年|初年")


def load_periods(conn):
    """id -> dict, cho cac dong LD2 co start_year (authoritative)."""
    out = {}
    for pid, pname, zh, y0, y1 in conn.execute(
            "SELECT id, period_name, period_name_zh, start_year, end_year "
            "FROM time_periods WHERE source_origin='t22_ld2_historical' "
            "AND start_year IS NOT NULL AND period_name IN ('era','dynasty')"):
        out[pid] = {"name": pname, "zh": zh, "y0": y0, "y1": y1}
    return out


def resolve(raw, periods, year=None):
    """raw_time_zh -> (time_periods.id | None, ly_do)

    CHI DUNG VAN BAN. KHONG dung `normalized_start` de loai era:
    nam do chinh T97 tinh, ma T97 dang co bug (GĐ3: LIKE '%era%' + rows[0]).
    Dung no lam bang chung => vong tron, da gay ra gan sai nhu
    `後周顯德元年 -> era_南漢_乾和`. Nam chi dung de DOI CHIEU sau khi
    da gan id tu van ban.
    """
    s = YEAR_RE.sub("", raw or "").strip()
    if not s:
        return None, "rong"
    # 1) era: ten nien hieu la duoi chuoi (uu tien dai nhat)
    eras = [p for p in periods.values() if p["name"] == "era" and s.endswith(p["zh"])]
    if not eras:
        return None, "khong tim thay ten nien hieu"
    if len(eras) > 1:
        return None, "trung ten nien hieu (%d) - can tien to trieu dai" % len(eras)
    era = eras[0]
    # 1b) ten niên hiệu DUY NHẤT trong LD2 => không cần tiền tố triều đại vẫn
    #     loại được (vd 乾隆/永初/紹興 chỉ có 1 triều đại). Vẫn là VĂN BẢN.
    same_name = [pid for pid, p in periods.items()
                 if p["name"] == "era" and p["zh"] == era["zh"]]
    if len(same_name) == 1:
        return same_name[0], "ten niên hiệu duy nhất trong LD2"
    # 2) tên trùng => bắt buộc phải có tiền tố triều đại để loại
    prefix = s[:len(s) - len(era["zh"])]
    if not prefix:
        return None, "khong co tien to trieu dai - khong loai duoc"
    # 2) trieu dai: khop tien to voi danh sach trieu dai LD2 (uien toi dai nhat)
    dyns = [p for p in periods.values() if p["name"] == "dynasty" and prefix.endswith(p["zh"])]
    if not dyns:
        return None, "khong khop ten trieu dai"
    dyn = max(dyns, key=lambda p: len(p["zh"]))
    # 3) era phai thuoc ve trieu dai do khong?
    same = [p for p in eras if p["y0"] == era["y0"] and p["y1"] == era["y1"]]
    if not same:
        return None, "ky tuong khong nhat quan"
    for pid, p in periods.items():
        if p["name"] == "era" and p["zh"] == era["zh"] and \
           abs(p["y0"] - era["y0"]) < 3 and p["y0"] >= dyn["y0"] and p["y0"] <= dyn["y1"]:
            return pid, "khop"
    return None, "khong tim thay id khop ca trieu dai"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--revert", action="store_true")
    a = ap.parse_args()
    if not any([a.dry_run, a.apply, a.revert]):
        ap.print_help()
        sys.exit(1)
    db = os.path.abspath(DB_PATH)

    if a.revert:
        if not os.path.exists(LOG_PATH):
            print("Khong co log.")
            return
        log = json.load(open(LOG_PATH, encoding="utf-8"))
        c = sqlite3.connect(db)
        before = c.total_changes
        for mid, old in log["restore"]:
            if isinstance(mid, (list, tuple)):
                mid = mid[0]          # log ghi (tuple5, PLACEHOLDER)
            c.execute("UPDATE time_mentions SET time_authority_id=? WHERE mention_id=?",
                      (old, mid))
        n = c.total_changes - before
        c.commit()
        c.close()
        print("Da revert %d dong. Backup: %s" % (n, log["backup"]))
        return

    conn = sqlite3.connect(db)
    periods = load_periods(conn)
    rows = conn.execute(
        "SELECT mention_id, raw_time_zh, normalized_start, time_authority_id "
        "FROM time_mentions "
        "WHERE time_authority_id=?", (PLACEHOLDER,)).fetchall()
    print("=== T234-GD2b/M5 %s ===" % ("APPLY" if a.apply else "DRY-RUN"))
    print("   LD2 periods: %d | placeholder rows: %d" % (len(periods), len(rows)))

    set_ok, set_null, why = [], [], {}
    for mid, raw, nstart, old in rows:
        pid, reason = resolve(raw, periods, nstart)
        if pid:
            set_ok.append((mid, pid, raw, reason, nstart))
        else:
            set_null.append((mid, raw, reason))
            why[reason] = why.get(reason, 0) + 1

    print("   GAN ID THAT : %d" % len(set_ok))
    print("   DE NULL     : %d" % len(set_null))
    for k, v in sorted(why.items(), key=lambda x: -x[1]):
        print("      - %-45s %d" % (k, v))
    for mid, pid, raw, rsn, year in set_ok[:12]:
        p = periods.get(pid, {})
        tag = ""
        if year is not None and p.get("y0") is not None and p.get("y1") is not None:
            tag = ("DOI CHIEU OK" if p["y0"] <= year <= p["y1"]
                   else "!! TUONG CONG: nam %d ngoai [%s,%s]" % (year, p["y0"], p["y1"]))
        print("      OK   %-16s -> %-18s [%s] %s" % (raw, pid, rsn, tag))
    for mid, raw, reason in set_null[:8]:
        print("      NULL %-14s (%s)" % (raw, reason))

    backup = None
    if a.apply:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        backup = os.path.join(BACKUP_DIR, "lineage_t234gd2b_%s.db"
                              % datetime.now().strftime("%Y%m%d_%H%M%S"))
        shutil.copy2(db, backup)
        conn.executemany("UPDATE time_mentions SET time_authority_id=? WHERE mention_id=?",
                         [(pid, mid) for mid, pid, _, _, _ in set_ok])
        conn.executemany("UPDATE time_mentions SET time_authority_id=NULL WHERE mention_id=?",
                         [(mid,) for mid, _, _ in set_null])
        conn.commit()
        json.dump({"run_at": datetime.now().isoformat(), "backup": backup,
                   "restore": [(m, PLACEHOLDER) for m in set_ok + set_null]},
                  open(LOG_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("   Backup: %s" % backup)
        print("   Log:    %s" % LOG_PATH)
    conn.close()


if __name__ == "__main__":
    main()