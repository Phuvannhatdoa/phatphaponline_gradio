"""T500 — sửa volume_files theo mốc quyển XML cục bộ (Admin duyệt 2026-10-31, mục 1).

Mặc định chỉ kiểm (không ghi DB). Chạy ghi DB phải có --apply.
Nguồn: docs/sessions/2026-10-31/cbeta-volumes/volume_files_fix_proposal.csv (kết quả t500_fix_volume_files_dryrun.py).

Loại khỏi đợt này: 3 work có xung đột (GA0037, L1557, X0714) — chờ Admin quyết quy tắc chọn file (mục 2).
Trước khi ghi: sao lưu lineage.db. Ghi trong một transaction; rollback nếu số dòng cập nhật không khớp
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
HOLD_WORKS = {"GA0037", "L1557", "X0714"}


def read_proposal():
    with open(PROPOSAL, encoding="utf-8", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["work_id"] not in HOLD_WORKS]
    return rows


def main():
    ap = argparse.ArgumentParser(description="T500 — sửa volume_files theo XML (mặc định chỉ kiểm)")
    ap.add_argument("--apply", action="store_true", help="sao lưu rồi ghi DB")
    a = ap.parse_args()

    rows = read_proposal()
    print(f"Dòng đề xuất sửa (trừ 3 work đang giữ): {len(rows)}")
    works = {r["work_id"] for r in rows}
    print(f"Số work: {len(works)}")
    if not a.apply:
        print("Chưa ghi DB. Thêm --apply để sao lưu và ghi.")
        return 0

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = BACKUP_DIR / f"lineage_pre_t500_volfiles_{stamp}.db"
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
        if total != 21513 or wv != 21513:
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
