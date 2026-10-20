# -*- coding: utf-8 -*-
"""T251 — bổ sung 6 niên hiệu thiếu vào `time_periods` (T22-LD2 era gap).

Chạy áp dụng (mặc định, idempotent):
    python -X utf8 scripts/t251_ld2_era_gap.py

Chạy hoàn nguyên (dựa manifest, xoá đúng id đã thêm):
    python -X utf8 scripts/t251_ld2_era_gap.py --revert

Trước khi ghi luôn tạo backup file-level trong data/backups/ và manifest
JSON trong docs/rollback/ — cả hai đều ghi ra cho Admin xem.
"""
import argparse
import json
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DB = BASE / "data" / "lineage.db"
BACKUP_DIR = BASE / "data" / "backups"
MANIFEST = BASE / "docs" / "rollback" / "T251-LD2-era-gap-manifest.json"

# 6 niên hiệu vắng trong LD2. Khoảng năm đã đối chiếu với lịch sử Trung Hoa.
# 59 dòng place_timeline_events tham chiếu qua source_ref; 27 dòng có year
# đều nằm trong khoảng đã khai. --revert xoá THEO id trong manifest, không
# phân biệt dòng do script này INSERT hay do nguồn khác đặt cùng tên.
ERAS = [
    # id,                zh,  VI,           start, end, era_name
    ("era_唐_垂拱",       "垂拱", "Thụy Cung", 685, 688, "唐垂拱"),
    ("era_東晉_咸和",     "咸和", "Hà Hòa",    326, 334, "東晉咸和"),
    ("era_後周_顯德",     "顯德", "Hiển Đức",  954, 959, "後周顯德"),
    ("era_唐_寶曆",       "寶曆", "Bảo Lịch",  825, 827, "唐寶曆"),
    ("era_金_大定",       "大定", "Đại Định", 1161, 1189, "金大定"),
    ("era_梁_大同",       "大同", "Đại Đồng",  535, 546, "梁大同"),
]

SOURCE = "t251_ld2_era_gap"
COLS = ("id", "period_name", "period_name_zh", "period_name_vi",
        "start_year", "end_year", "era_name", "source_origin", "created_at")


def _bang_gia(id_list):
    """Đếm + trả về các dòng hiện có của các id (dùng khi revert)."""
    if not id_list:
        return 0, []
    ph = ",".join("?" * len(id_list))
    rows = list(DB_CX.execute(
        "SELECT id, period_name_zh, start_year, end_year FROM time_periods "
        "WHERE id IN (%s)" % ph, id_list))
    return len(rows), rows


def backup():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = BACKUP_DIR / ("lineage_t251_%s.db" % ts)
    shutil.copy2(str(DB), str(dst))
    return dst


def ap_dung():
    global DB_CX
    DB_CX = sqlite3.connect(str(DB))
    now = datetime.now().isoformat()

    truoc, _ = _bang_gia([e[0] for e in ERAS])
    dst = backup()

    them, bo_qua = 0, 0
    for eid, zh, vi, s, e, en in ERAS:
        if DB_CX.execute("SELECT 1 FROM time_periods WHERE id=?", (eid,)).fetchone():
            bo_qua += 1
            continue
        DB_CX.execute(
            "INSERT INTO time_periods (%s) VALUES (?,?,?,?,?,?,?,?,?)"
            % ",".join(COLS),
            (eid, "era", zh, vi, s, e, en, SOURCE, now))
        them += 1
    DB_CX.commit()

    sau, rows = _bang_gia([e[0] for e in ERAS])
    manifest = {
        "task": "T251",
        "nguon": SOURCE,
        "thoi_gian": now,
        "backup": str(dst.relative_to(BASE)) if dst.exists() else "",
        "truoc": truoc,
        "them": them,
        "bo_qua": bo_qua,
        "sau": sau,
        "id_da_them": [e[0] for e in ERAS],
        "dong_chi_tiet": [{"id": r[0], "zh": r[1], "s": r[2], "e": r[3]}
                          for r in rows],
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    DB_CX.close()

    print("T251 ap dung xong")
    print("   backup        : %s" % manifest["backup"])
    print("   manifest      : %s" % MANIFEST.name)
    print("   truoc/sau     : %d -> %d" % (truoc, sau))
    print("   them %d, bo qua (da co) %d" % (them, bo_qua))
    if sau != len(ERAS):
        print("   CANH BAO: sau=%d khong bang %d — kiem tra lai!" % (sau, len(ERAS)))
        sys.exit(1)


def hoan_nguyen():
    global DB_CX
    if not MANIFEST.exists():
        print("Khong tim thay manifest: %s" % MANIFEST)
        sys.exit(1)
    mf = json.loads(MANIFEST.read_text(encoding="utf-8"))
    ids = mf.get("id_da_them", [])
    DB_CX = sqlite3.connect(str(DB))
    truoc, _ = _bang_gia(ids)

    xoa = 0
    for eid in ids:
        cur = DB_CX.execute("DELETE FROM time_periods WHERE id=?", (eid,))
        xoa += cur.rowcount
    DB_CX.commit()
    sau, _ = _bang_gia(ids)
    DB_CX.close()

    print("T251 hoan nguyen xong (manifest %s)" % MANIFEST.name)
    print("   truoc/sau     : %d -> %d" % (truoc, sau))
    print("   da xoa %d dong" % xoa)
    if sau != 0:
        print("   CANH BAO: van con %d dong — kiem tra lai!" % sau)
        sys.exit(1)


DB_CX = None


def main():
    p = argparse.ArgumentParser(description="T251 — bo sung 6 era thieu LD2")
    p.add_argument("--revert", action="store_true", help="hoan nguyen theo manifest")
    a = p.parse_args()
    try:
        if not DB.exists():
            print("Khong tim thay DB: %s" % DB)
            sys.exit(1)
        hoan_nguyen() if a.revert else ap_dung()
    except sqlite3.Error as ex:
        print("Loi SQLite: %s" % ex)
        sys.exit(1)
    except OSError as ex:
        print("Loi file: %s" % ex)
        sys.exit(1)


if __name__ == "__main__":
    main()
