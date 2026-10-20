"""
Phase 3.3: Kiem tra tinh ven toan (integrity) cua cac file DB backup
bang PRAGMA quick_check, truoc khi archive off-repo.

Cach dung:
    python daoanh/scripts/verify_db_backups.py [file1] [file2] ...

Neu khong truyen argument, script se tu kiem tra 2 file mac dinh cua Phase 3.3:
    - daoanh/docs/sessions/2026-10-14/lineage.db.backup_t381_etl_20261014_084125
    - daoanh/docs/sessions/2026-10-14/lineage.db.before_t381_revised

Script chi DOC (read-only connect), khong ghi/sua file DB.
"""

import sqlite3
import sys
import os

DEFAULT_FILES = [
    "daoanh/docs/sessions/2026-10-14/lineage.db.backup_t381_etl_20261014_084125",
    "daoanh/docs/sessions/2026-10-14/lineage.db.before_t381_revised",
]


def quick_check(path):
    """Chay PRAGMA quick_check tren 1 file DB, tra ve (ok: bool, detail: list)."""
    if not os.path.exists(path):
        return False, ["FILE KHONG TON TAI: {}".format(path)]

    size_mb = os.path.getsize(path) / (1024 * 1024)

    try:
        # Mo read-only de khong vo tinh tao file moi / ghi WAL
        uri = "file:{}?mode=ro".format(path.replace("\\", "/"))
        conn = sqlite3.connect(uri, uri=True)
        cursor = conn.cursor()
        cursor.execute("PRAGMA quick_check;")
        result = cursor.fetchall()
        conn.close()

        flat = [row[0] for row in result]
        ok = len(flat) == 1 and flat[0] == "ok"
        return ok, flat, size_mb
    except sqlite3.Error as e:
        return False, ["LOI SQLITE: {}".format(e)], size_mb


def main():
    files = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT_FILES

    print("=" * 70)
    print("PHASE 3.3 - PRAGMA quick_check tren cac file DB backup")
    print("=" * 70)

    summary = []
    for f in files:
        print("\n--- Kiem tra: {} ---".format(f))
        outcome = quick_check(f)
        if len(outcome) == 3:
            ok, detail, size_mb = outcome
        else:
            ok, detail = outcome
            size_mb = None

        status = "OK" if ok else "CORRUPT"
        if size_mb is not None:
            print("Kich thuoc: {:.1f} MB".format(size_mb))
        print("Ket qua quick_check: {}".format(detail))
        print("=> {}".format(status))
        summary.append((f, status, detail))

    print("\n" + "=" * 70)
    print("TONG KET")
    print("=" * 70)
    for f, status, detail in summary:
        print("- {} : {}".format(os.path.basename(f), status))
        if status != "OK":
            print("  Chi tiet: {}".format(detail))


if __name__ == "__main__":
    main()
