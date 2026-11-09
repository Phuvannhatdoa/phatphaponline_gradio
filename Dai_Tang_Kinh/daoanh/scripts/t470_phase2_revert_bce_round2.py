#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T470 PHASE 2 — VONG 2: tim + revert dung cac o bi mat dau TCN (BCE) do bug
extract_year cu (xem t470_phase2_apply_birth_death.py truoc fix 2026-10-26).

Doc lai revert log vong 1 (t470_phase2_birth_death_revert_log.jsonl, 12778 dong),
doi chieu voi JSON goc trong data/dila_import/extracted/<id>.json:
  - Neu chuoi JSON cho cot do (birth/death) co dau '-' ngay truoc so nam
    VA set_value (da ghi vao DB o vong 1) == abs(nam am do)
    => day la 1 trong 218 o bi bug, revert ve NULL.
  - Neu khong co dau '-' => nam CN, giu nguyen (khong dong vao 12560 o con lai).

Chi UPDATE khi gia tri hien tai trong DB con dung bang set_value da ghi
(an toan, giong co che revert cua script vong 1).

Output:
  docs/sessions/2026-10-26/t470_phase2_bce_revert_round2_log.jsonl   (moi o revert)
  docs/sessions/2026-10-26/t470_bce_years_pending_admin_decision.csv (153 person_id)

Usage:
  python -X utf8 t470_phase2_revert_bce_round2.py --dry-run   (mac dinh, khong ghi)
  python -X utf8 t470_phase2_revert_bce_round2.py --apply
"""
import sys
import io
import re
import csv
import json
import sqlite3
import pathlib
import argparse
import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

DAOANH_ROOT = pathlib.Path(
    r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh"
)
EXTRACTED_DIR = DAOANH_ROOT / "data" / "dila_import" / "extracted"
DB_PATH = DAOANH_ROOT / "data" / "lineage.db"
SESSION_DIR = DAOANH_ROOT / "docs" / "sessions" / "2026-10-26"
ROUND1_REVERT_LOG = SESSION_DIR / "t470_phase2_birth_death_revert_log.jsonl"
ROUND2_LOG = SESSION_DIR / "t470_phase2_bce_revert_round2_log.jsonl"
PENDING_CSV = SESSION_DIR / "t470_bce_years_pending_admin_decision.csv"

COL_TO_JSONKEY = {"birth_year": "birth", "death_year": "death"}


def extract_signed(range_str):
    if not range_str:
        return None
    m = re.search(r"([+-]?\d{3,4})", str(range_str))
    return int(m.group(1)) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if not ROUND1_REVERT_LOG.is_file():
        print(f"LOI: khong thay {ROUND1_REVERT_LOG}")
        sys.exit(1)

    con = sqlite3.connect(str(DB_PATH))
    cur = con.cursor()

    bce_hits = []  # (pid, col, wrong_positive_value, correct_signed_value, json_raw)
    not_bce_count = 0
    missing_json = 0

    with open(ROUND1_REVERT_LOG, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            pid, col, val = rec["id"], rec["column"], rec["set_value"]
            jpath = EXTRACTED_DIR / f"{pid}.json"
            if not jpath.is_file():
                missing_json += 1
                continue
            try:
                data = json.loads(jpath.read_text(encoding="utf-8"))
            except Exception:
                missing_json += 1
                continue
            bd = data.get("birth_death_dates") or {}
            raw = bd.get(COL_TO_JSONKEY[col])
            signed = extract_signed(raw)
            if signed is not None and signed < 0 and abs(signed) == val:
                bce_hits.append((pid, col, val, signed, raw))
            else:
                not_bce_count += 1

    print(f"Tong dong revert-log vong 1: da doc xong.")
    print(f"  O nghi la BCE (da sua dau am, abs == gia tri sai da ghi): {len(bce_hits)}")
    print(f"  O khong phai BCE (nam CN, giu nguyen): {not_bce_count}")
    print(f"  O thieu/lo JSON khi doi chieu: {missing_json}")

    person_ids = sorted(set(pid for pid, *_ in bce_hits))
    print(f"  So person_id duy nhat bi anh huong: {len(person_ids)}")

    if not args.apply:
        print("DRY-RUN — khong ghi DB, khong ghi file log/csv. Chay lai voi --apply.")
        con.close()
        return

    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    n_reverted = 0
    n_skipped_already_changed = 0
    with open(ROUND2_LOG, "a", encoding="utf-8") as logf:
        for pid, col, wrong_val, signed_val, raw in bce_hits:
            cur.execute(f"SELECT {col} FROM people WHERE id = ?", (pid,))
            r = cur.fetchone()
            current = r[0] if r else None
            if current == wrong_val:
                cur.execute(f"UPDATE people SET {col} = NULL WHERE id = ?", (pid,))
                n_reverted += 1
                logf.write(json.dumps({
                    "id": pid, "column": col,
                    "before_value_round2": wrong_val,
                    "after_value_round2": None,
                    "json_raw": raw,
                    "bce_year_pending_admin": signed_val,
                    "ts": datetime.datetime.now().isoformat(),
                }, ensure_ascii=False) + "\n")
            else:
                n_skipped_already_changed += 1
                logf.write(json.dumps({
                    "id": pid, "column": col,
                    "SKIPPED_reason": "gia tri hien tai khac gia tri da ghi o vong 1 (bi sua boi thao tac khac)",
                    "expected_wrong_value": wrong_val, "current_value": current,
                    "ts": datetime.datetime.now().isoformat(),
                }, ensure_ascii=False) + "\n")
    con.commit()

    # verify
    cur.execute("SELECT COUNT(*) FROM people")
    verify_null = 0
    for pid, col, wrong_val, signed_val, raw in bce_hits:
        cur.execute(f"SELECT {col} FROM people WHERE id = ?", (pid,))
        r = cur.fetchone()
        if r and r[0] is None:
            verify_null += 1
    print(f"Da revert: {n_reverted} o ve NULL. Bo qua (da bi doi khac): {n_skipped_already_changed}.")
    print(f"Verify lai: {verify_null}/{len(bce_hits)} o trong danh sach BCE hien la NULL.")

    # pending-admin-decision CSV: 153 person_id + gia tri JSON goc (co dau)
    with open(PENDING_CSV, "w", encoding="utf-8", newline="") as cf:
        w = csv.writer(cf)
        w.writerow(["dila_id", "column", "json_raw_value", "bce_year_signed", "db_status_after_revert"])
        for pid, col, wrong_val, signed_val, raw in bce_hits:
            w.writerow([pid, col, raw, signed_val, "NULL_pending_admin_decision"])
    print(f"Da ghi CSV pending-admin-decision: {PENDING_CSV} ({len(bce_hits)} dong, {len(person_ids)} person_id)")
    print(f"Da ghi log vong 2: {ROUND2_LOG}")

    con.close()


if __name__ == "__main__":
    main()
