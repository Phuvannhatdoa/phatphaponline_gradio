"""T500 — Áp dụng schema additive và nạp dòng quyển từ kết quả dry-run.

Mặc định chỉ kiểm tra và in số liệu (không ghi DB).
Chạy ghi DB phải có cờ --apply. Trước khi ghi, script sao lưu lineage.db.

Nguồn: docs/sessions/2026-10-29/cbeta-volumes/work_volumes_dryrun.csv và alias_dryrun.csv
(kết quả dry-run, không gọi lại API).
Không sửa bảng cũ. Mọi thay đổi nằm trong một transaction.
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
OUT = ROOT / "docs" / "sessions" / "2026-10-29" / "cbeta-volumes"
SCHEMA = ROOT / "scripts" / "t500_work_volumes_schema.sql"
VOL_CSV = OUT / "work_volumes_dryrun.csv"
ALIAS_CSV = OUT / "alias_dryrun.csv"
TABLES = ["work_volumes", "volume_files", "work_alias"]


def count(con, table):
    try:
        return con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    except sqlite3.OperationalError:
        return None


def snapshot_counts(con):
    out = {t: count(con, t) for t in TABLES}
    out["dila_catalog_works"] = count(con, "dila_catalog_works")
    out["sum_juans"] = con.execute(
        "SELECT COALESCE(SUM(juans),0) FROM dila_catalog_works").fetchone()[0]
    return out


def read_volumes():
    with open(VOL_CSV, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def read_aliases():
    seen = set()
    rows = []
    with open(ALIAS_CSV, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            key = (r["work_id_db"], r["alt_code"])
            # Bỏ cặp tự trỏ chính nó (work_id == alt_code): không mang thông tin alias (T500, 2026-10-31).
            if key[0] == key[1] or key in seen:
                continue
            seen.add(key)
            rows.append((r["work_id_db"], r["alt_code"], "alt tương đương (T500 dry-run)"))
    return rows


def backup_db():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = BACKUP_DIR / f"lineage_pre_t500_{stamp}.db"
    shutil.copy2(DB, dest)
    return dest


def main():
    ap = argparse.ArgumentParser(description="T500 — nạp schema quyển (mặc định chỉ kiểm)")
    ap.add_argument("--apply", action="store_true", help="ghi DB sau khi sao lưu")
    a = ap.parse_args()

    vols = read_volumes()
    aliases = read_aliases()
    print(f"Dòng quyển từ dry-run: {len(vols)}")
    print(f"Dòng alias (sau khử trùng): {len(aliases)}")

    uri = DB.resolve().as_uri() + "?mode=ro"
    ro = sqlite3.connect(uri, uri=True)
    before = snapshot_counts(ro)
    ro.close()
    print("Trước:", before)

    if not a.apply:
        print("Chưa ghi DB. Thêm --apply để sao lưu và ghi.")
        return 0

    if any(before[t] not in (None, 0) for t in TABLES):
        print("Bảng đã có dữ liệu, dừng để tránh nạp trùng:", before)
        return 1

    backup = backup_db()
    print("Đã sao lưu:", backup)

    con = sqlite3.connect(DB)
    try:
        con.execute("PRAGMA foreign_keys = ON")
        con.execute("BEGIN")
        for stmt in SCHEMA.read_text(encoding="utf-8").split(";"):
            body = "\n".join(l for l in stmt.splitlines() if not l.strip().startswith("--")).strip()
            if body and body.upper() not in ("BEGIN", "COMMIT"):
                con.execute(body)
        con.executemany(
            "INSERT INTO work_volumes (work_id, juan_no, cbeta_node_n, juan_source, source_snapshot) "
            "VALUES (?, ?, ?, ?, ?)",
            [(r["work_id"], int(r["juan_no"]), r["cbeta_node_n"], r["juan_source"], r["source_snapshot"])
             for r in vols])
        con.executemany(
            "INSERT INTO volume_files (work_id, juan_no, file_id) VALUES (?, ?, ?)",
            [(r["work_id"], int(r["juan_no"]), r["file_id"]) for r in vols])
        con.executemany(
            "INSERT INTO work_alias (work_id, alt_work_id, note) VALUES (?, ?, ?)", aliases)
        after = snapshot_counts(con)
        expected_ok = (after["work_volumes"] == len(vols)
                       and after["volume_files"] == len(vols)
                       and after["work_alias"] == len(aliases)
                       and after["dila_catalog_works"] == before["dila_catalog_works"]
                       and after["sum_juans"] == before["sum_juans"])
        if not expected_ok:
            con.rollback()
            print("Kiểm sau ghi không khớp, đã rollback:", after)
            return 1
        con.commit()
    except Exception as exc:
        con.rollback()
        print("Lỗi, đã rollback:", exc)
        return 1
    finally:
        con.close()

    ro = sqlite3.connect(uri, uri=True)
    final = snapshot_counts(ro)
    ro.close()
    print("Sau:", final)
    print("Backup để khôi phục nếu cần:", backup)
    return 0


if __name__ == "__main__":
    sys.exit(main())
