#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T470 PHASE 2 — ghi birth_year/death_year còn thiếu vào people.

CHỈ ghi (UPDATE) cột đang NULL. KHÔNG bao giờ ghi đè cột đã có giá trị.
KHÔNG tạo dòng mới (không INSERT) — chỉ UPDATE trên id đã tồn tại trong
bảng `people`. 817 dila_id không có trong `people` bị loại trừ tuyệt đối,
kể cả khi JSON có birth_death_dates.

Nguồn danh sách ứng viên: docs/sessions/2026-10-26/dila_json_reconcile.csv
  (field == 'birth_death_dates' và classification == 'DB_THIEU'), nhưng
  KHÔNG tin thẳng nhãn hàng đó — nhãn DB_THIEU ở mức dòng có thể gộp cả
  trường hợp 1 năm thiếu + 1 năm khác giá trị (xem dila_json_reconcile_dryrun.py
  classify_birth_death: ưu tiên "missing" trước "mismatch"). Script này tính
  lại độc lập theo từng cột (birth_year / death_year) từ JSON gốc + DB hiện
  tại, chỉ set cột nào JSON có giá trị VÀ DB đang NULL cho đúng cột đó.

Chạy theo lô (mặc định 1000 dòng ghi/lô), verify lại bằng SELECT sau mỗi lô.
Ghi revert-log (jsonl) để --revert đặt lại NULL đúng các ô đã ghi (idempotent,
chỉ revert ô mà giá trị hiện tại còn khớp giá trị đã ghi — không đụng nếu ô
đó bị sửa bởi thao tác khác sau này).

Usage:
  python -X utf8 scripts/t470_phase2_apply_birth_death.py --apply
  python -X utf8 scripts/t470_phase2_apply_birth_death.py --dry-run   (mac dinh)
  python -X utf8 scripts/t470_phase2_apply_birth_death.py --revert
"""

import sys
import io
import os
import re
import csv
import json
import sqlite3
import pathlib
import argparse
import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

HERE = pathlib.Path(__file__).resolve().parent
DAOANH_ROOT = HERE.parent
EXTRACTED_DIR = DAOANH_ROOT / "data" / "dila_import" / "extracted"
DB_PATH = DAOANH_ROOT / "data" / "lineage.db"
SESSION_DIR = DAOANH_ROOT / "docs" / "sessions" / "2026-10-26"
CSV_PATH = SESSION_DIR / "dila_json_reconcile.csv"
REVERT_LOG = SESSION_DIR / "t470_phase2_birth_death_revert_log.jsonl"
APPLY_LOG = SESSION_DIR / "t470_phase2_birth_death_apply.log"

BATCH_SIZE = 1000


def extract_year(range_str):
    """'+1631-01-01 ~ +1631-12-31' -> 1631 ; '-0200-01-01 ~ -0200-12-31' -> -200.
    BUG DA SUA (2026-10-26, vong 2): regex cu (\\d{3,4}) khong bat dau '-' nen
    nam TCN (Truoc Cong Nguyen) bi ghi thanh so duong sai. Gio bat ca dau +/-
    ngay truoc chuoi so."""
    if not range_str:
        return None
    m = re.search(r"([+-]?\d{3,4})", str(range_str))
    return int(m.group(1)) if m else None


def log(msg, fh=None):
    print(msg)
    if fh:
        fh.write(msg + "\n")


def load_candidates():
    """Trả về list dila_id duy nhất có field=birth_death_dates, DB_THIEU, không
    phải 1 trong 817 ID thiếu khỏi people (lọc ở main bằng people_ids)."""
    ids = []
    with open(CSV_PATH, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if len(row) < 3:
                continue
            pid, field, cls = row[0], row[1], row[2]
            if field == "birth_death_dates" and cls == "DB_THIEU":
                ids.append(pid)
    return ids


def compute_updates(con, candidate_ids):
    cur = con.cursor()
    cur.execute("SELECT id, birth_year, death_year FROM people")
    people = {r[0]: (r[1], r[2]) for r in cur.fetchall()}

    updates = []  # (pid, column, new_value)
    skipped_not_in_people = 0
    skipped_no_null_target = 0

    for pid in candidate_ids:
        if pid not in people:
            skipped_not_in_people += 1
            continue
        db_b, db_d = people[pid]
        jpath = EXTRACTED_DIR / f"{pid}.json"
        if not jpath.is_file():
            continue
        try:
            data = json.loads(jpath.read_text(encoding="utf-8"))
        except Exception:
            continue
        bd = data.get("birth_death_dates") or {}
        jb = extract_year(bd.get("birth"))
        jd = extract_year(bd.get("death"))

        did_any = False
        if jb is not None and db_b is None:
            updates.append((pid, "birth_year", jb))
            did_any = True
        if jd is not None and db_d is None:
            updates.append((pid, "death_year", jd))
            did_any = True
        if not did_any:
            skipped_no_null_target += 1

    return updates, skipped_not_in_people, skipped_no_null_target


def apply_updates(con, updates, log_fh, revert_fh):
    cur = con.cursor()
    total = len(updates)
    done = 0
    for i in range(0, total, BATCH_SIZE):
        batch = updates[i:i + BATCH_SIZE]
        for pid, col, val in batch:
            cur.execute(
                f"UPDATE people SET {col} = ? WHERE id = ? AND {col} IS NULL",
                (val, pid),
            )
            revert_fh.write(json.dumps({
                "id": pid, "column": col, "set_value": val,
                "old_value": None, "ts": datetime.datetime.now().isoformat(),
            }, ensure_ascii=False) + "\n")
        con.commit()
        done += len(batch)

        # verify: sample-count rows in this batch that now match expected value
        ok = 0
        for pid, col, val in batch:
            cur.execute(f"SELECT {col} FROM people WHERE id = ?", (pid,))
            r = cur.fetchone()
            if r and r[0] == val:
                ok += 1
        log(f"  lo {i // BATCH_SIZE + 1}: ghi {len(batch)} dong, verify OK {ok}/{len(batch)}", log_fh)
        if ok != len(batch):
            log("  CANH BAO: verify khong khop 100% trong lo nay!", log_fh)
    return done


def do_revert(con, log_fh):
    if not REVERT_LOG.is_file():
        log("Khong co revert-log, khong co gi de revert.", log_fh)
        return
    cur = con.cursor()
    n = 0
    with open(REVERT_LOG, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            pid, col, val = rec["id"], rec["column"], rec["set_value"]
            # Chi revert ve NULL neu gia tri hien tai con dung bang gia tri da ghi
            # (khong dung khi co thao tac khac sua lai sau do).
            cur.execute(f"SELECT {col} FROM people WHERE id = ?", (pid,))
            r = cur.fetchone()
            if r and r[0] == val:
                cur.execute(f"UPDATE people SET {col} = NULL WHERE id = ?", (pid,))
                n += 1
    con.commit()
    log(f"Da revert {n} o ve NULL.", log_fh)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--revert", action="store_true")
    args = ap.parse_args()

    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    with open(APPLY_LOG, "a", encoding="utf-8") as log_fh:
        log(f"=== t470_phase2_apply_birth_death.py — {datetime.datetime.now().isoformat()} "
            f"mode={'apply' if args.apply else ('revert' if args.revert else 'dry-run')} ===", log_fh)

        con = sqlite3.connect(str(DB_PATH))

        if args.revert:
            do_revert(con, log_fh)
            con.close()
            return

        candidate_ids = load_candidates()
        candidate_ids = sorted(set(candidate_ids))
        log(f"Ung vien tu CSV (field=birth_death_dates, DB_THIEU): {len(candidate_ids)} dila_id", log_fh)

        updates, skip_not_people, skip_no_null = compute_updates(con, candidate_ids)
        log(f"Tinh lai doc lap theo cot: can ghi {len(updates)} o "
            f"(loai {skip_not_people} khong co trong people, "
            f"{skip_no_null} khong co cot NULL tuong ung de ghi)", log_fh)

        by_col = {}
        for _, col, _ in updates:
            by_col[col] = by_col.get(col, 0) + 1
        log(f"  Theo cot: {by_col}", log_fh)

        if not args.apply:
            log("DRY-RUN — khong ghi gi. Chay lai voi --apply de ghi thuc su.", log_fh)
            con.close()
            return

        with open(REVERT_LOG, "a", encoding="utf-8") as revert_fh:
            done = apply_updates(con, updates, log_fh, revert_fh)
        log(f"HOAN TAT: da ghi {done} o vao people.birth_year/death_year.", log_fh)
        con.close()


if __name__ == "__main__":
    main()
