# -*- coding: utf-8 -*-
"""T252 W3 — bổ sung 19 niên hiệu thiếu vào `time_periods` (H3: 43 → 14).

Chạy áp dụng (mặc định, idempotent):
    python -X utf8 scripts/t252_w3_era_gap.py

Chạy hoàn nguyên (dựa manifest, xoá đúng id đã thêm):
    python -X utf8 scripts/t252_w3_era_gap.py --revert

Trước khi ghi luôn tạo backup file-level trong data/backups/ và manifest
JSON trong docs/rollback/ — cả hai đều ghi ra cho Admin xem.

NGUỒN KHOẢNG NĂM (không đoán, có kiểm chứng):
  1. zh.wikipedia.org/wiki/中國年號列表 — bản lưu 2026-10-06 (bằng chứng:
     docs/sessions/2026-10-06_T252-w1-w3-w4.md §2 + manifest `nguon`).
  2. Corpus nội bộ: note/label của chính place_timeline_events có ghi
     `天監（502-519）` … (xem manifest `kiem_chung_corpus`).
  3. Đối chiếu thòng lặp với triều đại trong DYNASTY_TABLE của
     scripts/dila_dynasty_range_extract.py (mọi niên hiệu đều nằm gọn
     trong khoảng triều đại tương ứng).
Additive-only: KHÔNG UPDATE/DELETE dòng cũ, KHÔNG sửa `dyn_民국`.
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
MANIFEST = BASE / "docs" / "rollback" / "T252-W3-era-gap-manifest.json"

URL_WIKI = "https://zh.wikipedia.org/wiki/中國年號列表"

# id, zh, VI, start, end, era_name, nguồn kiểm chứng
ERAS = [
    ("era_梁_天監",     "天監", "Thiên Giám",  502,  519, "梁天監",
     "wiki + corpus: note '梁天監中（502-519）' (PL000000012045)"),
    ("era_梁_普通",     "普通", "Phổ Thông",   520,  527, "梁普通", "wiki"),
    ("era_梁_大通",     "大通", "Đại Thông",  527,  529, "梁大通", "wiki"),
    ("era_梁_承聖",     "承聖", "Thừa Thánh", 552,  555, "梁承聖", "wiki"),
    ("era_齊_永明",     "永明", "Vĩnh Minh",  483,  493, "齊永明",
     "wiki + corpus: '永明（483-493）'"),
    ("era_宋_昇明",     "昇明", "Thăng Minh", 477,  479, "宋昇明", "wiki"),
    ("era_東晉_義熙",   "義熙", "Nghĩa Hy",   405,  418, "東晉義熙", "wiki"),
    ("era_唐_乾寧",     "乾寧", "Càn Ninh",   894,  898, "唐乾寧", "wiki"),
    ("era_唐_景龍",     "景龍", "Cảnh Long",  707,  710, "唐景龍", "wiki"),
    ("era_唐_永泰",     "永泰", "Vĩnh Thái",  765,  766, "唐永泰", "wiki"),
    ("era_唐_儀鳳",     "儀鳳", "Nghi Phụng", 676,  679, "唐儀鳳", "wiki"),
    ("era_唐_長安",     "長安", "Trường An",  701,  704, "唐長安", "wiki"),
    ("era_唐_神龍",     "神龍", "Thần Long",  705,  707, "唐神龍", "wiki"),
    ("era_南唐_保大",   "保大", "Bảo Đại",    943,  957, "南唐保大", "wiki"),
    ("era_宋_咸淳",     "咸淳", "Hàm Thuần", 1265, 1274, "宋咸淳",
     "wiki + corpus: '咸淳（1265-1274）'"),
    ("era_前秦_建元",   "建元", "Kiến Nguyên", 365,  385, "前秦建元",
     "wiki (kiểu tự '秦苻堅建元十八年' = PL000000058689)"),
    ("era_唐_大順",     "大順", "Đại Thuận",  890,  891, "唐大順", "wiki"),
    ("era_東晉_永昌",   "永昌", "Vĩnh Xương",  322,  323, "東晉永昌", "wiki"),
    ("era_民國",        "民國", "Dân Quốc",  1912, 1949, "民國",
     "wiki ('民國元年（1912）…民國38年（1949）') + dyn_民國 1912-1949 + "
     "DYNASTY_TABLE['民國'] = (1912, 1949)"),
]

SOURCE = "t252_w3_era_gap"
COLS = ("id", "period_name", "period_name_zh", "period_name_vi",
        "start_year", "end_year", "era_name", "source_origin", "created_at")

DB_CX = None


def _bang_gia(id_list):
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
    dst = BACKUP_DIR / ("lineage_t252w3_%s.db" % ts)
    shutil.copy2(str(DB), str(dst))
    return dst


def ap_dung(dry=False):
    global DB_CX
    DB_CX = sqlite3.connect(str(DB))
    now = datetime.now().isoformat()

    ids = [e[0] for e in ERAS]
    truoc, _ = _bang_gia(ids)

    # Canh bao neu id da ton tai nhung thieu start_year (khong vao duoc era_map)
    lech = []
    for eid, zh, vi, s, e, en, _src in ERAS:
        row = DB_CX.execute(
            "SELECT start_year FROM time_periods WHERE id=?", (eid,)).fetchone()
        if row and row[0] is None:
            lech.append(eid)
    if lech:
        print("CANH BAO: id da co nhung start_year NULL: %s" % ", ".join(lech))
        print("   -> khong vao duoc era_map; dung lai de Admin quyet.")
        DB_CX.close()
        sys.exit(1)

    if dry:
        print("[DRY RUN] se them %d era (truoc da co %d):"
              % (len([e for e in ERAS
                      if not DB_CX.execute("SELECT 1 FROM time_periods WHERE id=?",
                                           (e[0],)).fetchone()]), truoc))
        for eid, zh, vi, s, e, en, src in ERAS:
            print("   %-18s %-4s %d-%d  %s" % (eid, zh, s, e, src))
        DB_CX.close()
        return

    dst = backup()

    them, bo_qua = 0, 0
    for eid, zh, vi, s, e, en, _src in ERAS:
        if DB_CX.execute("SELECT 1 FROM time_periods WHERE id=?", (eid,)).fetchone():
            bo_qua += 1
            continue
        DB_CX.execute(
            "INSERT INTO time_periods (%s) VALUES (?,?,?,?,?,?,?,?,?)"
            % ",".join(COLS),
            (eid, "era", zh, vi, s, e, en, SOURCE, now))
        them += 1
    DB_CX.commit()

    sau, rows = _bang_gia(ids)
    manifest = {
        "task": "T252",
        "giai_doan": "W3",
        "nguon": SOURCE,
        "nguon_khoang_nam": {
            "chinh": URL_WIKI,
            "ngay_luu": "2026-10-06",
            "corpus": "note/label trong place_timeline_events",
            "doi_chieu": "moi nien hieu nam gon trong khoang trieu dai "
                         "tuong ung (scripts/dila_dynasty_range_extract.py)",
        },
        "thoi_gian": now,
        "backup": str(dst.relative_to(BASE)) if dst.exists() else "",
        "truoc": truoc,
        "them": them,
        "bo_qua": bo_qua,
        "sau": sau,
        "id_da_them": ids,
        "dong_chi_tiet": [
            {"id": eid, "zh": zh, "vi": vi, "s": s, "e": e, "era_name": en,
             "nguon": src}
            for eid, zh, vi, s, e, en, src in ERAS],
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    DB_CX.close()

    print("T252 W3 ap dung xong")
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

    print("T252 W3 hoan nguyen xong (manifest %s)" % MANIFEST.name)
    print("   truoc/sau     : %d -> %d" % (truoc, sau))
    print("   da xoa %d dong" % xoa)
    if sau != 0:
        print("   CANH BAO: van con %d dong — kiem tra lai!" % sau)
        sys.exit(1)


def main():
    p = argparse.ArgumentParser(description="T252 W3 — bo sung 19 nien hieu thieu")
    p.add_argument("--revert", action="store_true", help="hoan nguyen theo manifest")
    p.add_argument("--dry-run", action="store_true", help="in ra, khong ghi")
    a = p.parse_args()
    try:
        if not DB.exists():
            print("Khong tim thay DB: %s" % DB)
            sys.exit(1)
        if a.revert:
            hoan_nguyen()
        else:
            ap_dung(dry=a.dry_run)
    except sqlite3.Error as ex:
        print("Loi SQLite: %s" % ex)
        sys.exit(1)
    except OSError as ex:
        print("Loi file: %s" % ex)
        sys.exit(1)


if __name__ == "__main__":
    main()
