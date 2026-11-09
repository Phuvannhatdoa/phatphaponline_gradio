"""T500 — W1, phương án 2 (Admin chọn 2026-10-31): sửa các dòng volume_files KHÔNG trùng theo XML.

Phạm vi:
  - Chỉ 3 work X0714, L1557, GA0037.
  - Chỉ những cặp (work, quyển) KHÔNG nằm trong volume_files_conflicts.csv (5 quyển trùng giữ theo API).
  - Đề xuất lấy từ volume_files_fix_proposal.csv (đã do t500_fix_volume_files_dryrun.py tạo).

Mặc định chỉ kiểm (không ghi DB). Chạy ghi DB phải có --apply.
Trước khi ghi: sao lưu lineage.db. Ghi trong một transaction; rollback nếu số dòng khớp không đúng
hoặc kiểm sau ghi không đạt.
"""
import argparse
import csv
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "lineage.db"
BACKUP_DIR = ROOT / "data" / "backups"
OUT = ROOT / "docs" / "sessions" / "2026-10-31" / "cbeta-volumes"
PROPOSAL = OUT / "volume_files_fix_proposal.csv"
CONFLICTS = OUT / "volume_files_conflicts.csv"
WORKS = {"X0714", "L1557", "GA0037"}
EXPECTED_ROWS = 64
EXPECTED_TOTAL = 21513


def load_rows():
    with open(CONFLICTS, encoding="utf-8", newline="") as f:
        held = {(r["work_id"], int(r["juan_no"])) for r in csv.DictReader(f)}
    with open(PROPOSAL, encoding="utf-8", newline="") as f:
        rows = [
            r for r in csv.DictReader(f)
            if r["work_id"] in WORKS and (r["work_id"], int(r["juan_no"])) not in held
        ]
    return rows


def main():
    ap = argparse.ArgumentParser(description="T500 W1 phương án 2 (mặc định chỉ kiểm)")
    ap.add_argument("--apply", action="store_true", help="sao lưu rồi ghi DB")
    a = ap.parse_args()

    rows = load_rows()
    print(f"Dòng đề xuất sửa (3 work, trừ 5 quyển trùng): {len(rows)}")
    if len(rows) != EXPECTED_ROWS:
        print(f"Số dòng {len(rows)} khác kỳ vọng {EXPECTED_ROWS}. Dừng.")
        return 1

    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    try:
        stale = []
        for r in rows:
            cur = con.execute(
                "SELECT file_id FROM volume_files WHERE work_id=? AND juan_no=?",
                (r["work_id"], int(r["juan_no"]))).fetchone()
            if cur is None or cur[0] != r["file_hien_tai"]:
                stale.append((r["work_id"], r["juan_no"], cur))
    finally:
        con.close()
    if stale:
        print(f"{len(stale)} dòng không còn khớp file hiện tại, dừng để kiểm tra:", stale[:5])
        return 1
    print("Kiểm trước ghi: 64/64 dòng khớp file hiện tại.")
    if not a.apply:
        print("Chưa ghi DB. Thêm --apply để sao lưu và ghi.")
        return 0

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = BACKUP_DIR / f"lineage_pre_t500_w1_{stamp}.db"
    shutil.copy2(DB, backup)
    print("Đã sao lưu:", backup)

    con = sqlite3.connect(DB)
    try:
        con.execute("BEGIN")
        updated = 0
        for r in rows:
            cur = con.execute(
                "UPDATE volume_files SET file_id = ? "
                "WHERE work_id = ? AND juan_no = ? AND file_id = ?",
                (r["file_de_xuat"], r["work_id"], int(r["juan_no"]), r["file_hien_tai"]))
            updated += cur.rowcount
        if updated != len(rows):
            con.rollback()
            print(f"Số dòng cập nhật {updated} khác đề xuất {len(rows)}, đã rollback.")
            return 1
        total = con.execute("SELECT COUNT(*) FROM volume_files").fetchone()[0]
        wv = con.execute("SELECT COUNT(*) FROM work_volumes").fetchone()[0]
        if total != EXPECTED_TOTAL or wv != EXPECTED_TOTAL:
            con.rollback()
            print(f"Kiểm sau ghi không khớp (volume_files={total}, work_volumes={wv}), đã rollback.")
            return 1
        con.commit()
        print(f"Đã cập nhật {updated} dòng. Commit.")
    except Exception as exc:
        con.rollback()
        print("Lỗi, đã rollback:", exc)
        return 1
    finally:
        con.close()
    print("Backup để khôi phục nếu cần:", backup)
    return 0


if __name__ == "__main__":
    sys.exit(main())
