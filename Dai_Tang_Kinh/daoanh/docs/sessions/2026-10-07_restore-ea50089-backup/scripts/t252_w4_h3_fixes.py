# -*- coding: utf-8 -*-
"""T252 W4 — sửa 14 dòng `place_timeline_events` mâu thuẫn (H3: 14 → 0).

Chạy áp dụng (mặc định, idempotent):
    python -X utf8 scripts/t252_w4_h3_fixes.py

Chạy hoàn nguyên (dựa manifest, trả đúng giá trị CŨ theo rowid):
    python -X utf8 scripts/t252_w4_h3_fixes.py --revert

Trước khi ghi luôn tạo backup file-level trong data/backups/, manifest JSON
trong docs/rollback/ và bảng chứng cứ TSV trong docs/evidence/.

3 nhóm sửa (mỗi dòng đều có `ly_do` + `bang_chung` trong manifest):
  A. 6 dòng midpoint THIẾU khoảng năm trong label  -> cộng ` (y0–y1年間)`
     (khoảng lấy từ DYNASTY_TABLE của dila_dynasty_range_extract.py,
      chứa year đã lưu — đúng quy ước của 838 dòng cùng nguồn đang pass).
  B. 3 dòng `source='dila_dynasty'` nhưng source_ref sai định dạng
     `·dynasty·<朝>` -> `·<朝>·midpoint` (đúng format 838 dòng cùng nguồn)
     + cộng khoảng vào label.
  C. 5 dòng year SAI so với chính note của nó -> sửa year theo.note
     (kèm year_end cho PL000000056280 vì note ghi rõ khoảng).

Không sửa gì ngoài 14 dòng này. Không xoá dòng nào.
"""
import argparse
import csv
import json
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DB = BASE / "data" / "lineage.db"
BACKUP_DIR = BASE / "data" / "backups"
MANIFEST = BASE / "docs" / "rollback" / "T252-W4-h3-fixes-manifest.json"
EVIDENCE = BASE / "docs" / "evidence" / "2026-10-06_T252_w4_fixes.tsv"

DASH = "\u2013"          # EN-dash đúng quy ước label (618–907年間)
SOURCE = "t252_w4_h3_fixes"

# (dila_id, source_ref GỐC, {cot: gia_tri_moi}, ly_do, bang_chung)
FIXES = [
    # ---- A. midpoint thiếu khoảng năm trong label (6) ----
    ("PL000000000353", "PL000000000353\u00b7\u5143\u672b\u660e\u521d\u00b7midpoint",
     {"label_zh": "\u5ef6\u58fd ~\u5143\u672b\u660e\u521d (1271%s1368\u5e74\u9593)" % DASH},
     "midpoint khong hien khoang (W4a)",
     "year=1368 = cuoi trieu Nguyen; DYNASTY_TABLE['\u5143']=(1271,1368)"),
    ("PL000000005412", "PL000000005412\u00b7\u660e\u672b\u6e05\u521d\u00b7midpoint",
     {"label_zh": "萬緣庵 ~\u660e\u672b\u6e05\u521d (1368%s1644\u5e74\u9593)" % DASH},
     "midpoint khong hien khoang (W4a)",
     "year=1644 = cuoi trieu Minh; DYNASTY_TABLE['\u660e']=(1368,1644)"),
    ("PL000000018578", "PL000000018578\u00b7\u660e\u672b\u6e05\u521d\u00b7midpoint",
     {"label_zh": "\u5927\u68b5\u5bfa ~\u660e\u672b\u6e05\u521d (1368%s1644\u5e74\u9593)" % DASH},
     "midpoint khong hien khoang (W4a)",
     "year=1644 = cuoi trieu Minh; DYNASTY_TABLE['\u660e']=(1368,1644)"),
    ("PL000000034323", "PL000000034323\u00b7\u660e\u672b\u6e05\u521d\u00b7midpoint",
     {"label_zh": "\u91d1\u5e36\u5bfa ~\u660e\u672b\u6e05\u521d (1368%s1644\u5e74\u9593)" % DASH},
     "midpoint khong hien khoang (W4a)",
     "year=1644 = cuoi trieu Minh; DYNASTY_TABLE['\u660e']=(1368,1644)"),
    ("PL000000036172", "PL000000036172\u00b7\u660e\u672b\u6e05\u521d\u00b7midpoint",
     {"label_zh": "\u606f\u5fc3\u6240 ~\u660e\u672b\u6e05\u521d (1368%s1644\u5e74\u9593)" % DASH},
     "midpoint khong hien khoang (W4a)",
     "year=1644 = cuoi trieu Minh; DYNASTY_TABLE['\u660e']=(1368,1644)"),
    ("PL000000056538", "PL000000056538\u00b7\u660e\u672b\u6e05\u521d\u00b7midpoint",
     {"label_zh": "\u5929\u57ce\u5bfa ~\u660e\u672b\u6e05\u521d (1368%s1644\u5e74\u9593)" % DASH},
     "midpoint khong hien khoang (W4a)",
     "year=1644 = cuoi trieu Minh; DYNASTY_TABLE['\u660e']=(1368,1644)"),

    # ---- B. source_ref sai format + label thieu khoang (3) ----
    ("PL000000000286", "PL000000000286\u00b7dynasty\u00b7\u5510",
     {"source_ref": "PL000000000286\u00b7\u5510\u00b7midpoint",
      "label_zh": "\u59cb\u5efa\u65bc\u5510\u671d\uff0c稱聚瑟寺 (618%s907\u5e74\u9593)" % DASH},
     "source_ref dung 'dynasty' thay vi 'midpoint' + label thieu khoang (W4b)",
     "source='dila_dynasty', year=762 = trung diem 唐 (618,907); 838 dong cung "
     "nguon dung format <dila_id>·<trieu>·midpoint"),
    ("PL000000005410", "PL000000005410\u00b7dynasty\u00b7\u660e",
     {"source_ref": "PL000000005410\u00b7\u660e\u00b7midpoint",
      "label_zh": "寺周山巒起伏，明初創建 (1368%s1644\u5e74\u9593)" % DASH},
     "source_ref dung 'dynasty' thay vi 'midpoint' + label thieu khoang (W4b)",
     "source='dila_dynasty', year=1506 = trung diem 明 (1368,1644)"),
    ("PL000000055761", "PL000000055761\u00b7dynasty\u00b7\u5143",
     {"source_ref": "PL000000055761\u00b7\u5143\u00b7midpoint",
      "label_zh": "\u59cb\u5efa\u4e8e\u5143\u4ee3 (1271%s1368\u5e74\u9593)" % DASH},
     "source_ref dung 'dynasty' thay vi 'midpoint' + label thieu khoang (W4b)",
     "source='dila_dynasty', year=1319 = trung diem 元 (1271,1368)"),

    # ---- C. year mâu thuẫn với CHÍNH note (5) ----
    ("PL000000056280", "PL000000056280\u00b7dynasty\u00b7\u5510",
     {"year": 766, "year_end": 779},
     "year=762 (trung diem 唐) mâu thuân voi khoang note ghi (W4c)",
     "note: '\u5275\u5efa\u65bc\u5510\u4ee3\u5927\u66c6\uff08766-779\uff09\u5e74\u9593' "
     "-> 762 ngoai khoang 766-779; year=766, year_end=779 (quy uoc "
     "era_name_midpoint trong bang)"),
    ("PL000000023803", "PL000000023803\u00b7note\u00b7regex",
     {"year": 911},
     "year=902 khong phai ket qua cua '天復十一年' (W4c)",
     "note: '\u5efa\u65bc\u5468\u5929\u5fa9\u5341\u4e00\u5e74'; 唐天復 901-904 -> "
     "901+11-1 = 911 (vuot khoang, nguon ghi vay — W1a rule(b) trung year)"),
    ("PL000000057764", "PL000000057764\u00b7note\u00b7regex",
     {"year": 1399},
     "year=1372 khong phai ket qua cua '洪武三十二年' (W4c)",
     "note: '\u570b\u671d\u6d2a\u6b66\u4e09\u5341\u4e8c\u5e74'; \u6d2a\u6b66 1368-1398 -> "
     "1368+32-1 = 1399 (vuot khoang, nguon ghi vay — W1a rule(b) trung year)"),
    ("PL000000058034", "PL000000058034\u00b7note\u00b7regex",
     {"year": 324},
     "year=691 la suy ra tu 唐永昌 trong khi note ghi 晉 (W4c)",
     "note: '\u664b\u6c38\u660c\u4e09\u5e74\u5efa'; 東晉永昌 322-323 -> 322+3-1 = 324. "
     "691 = 689+2 (唐永昌 689-690) nhung note KHONG ghi 唐"),
    ("PL000000054389", "PL000000054389\u00b7note\u00b7regex",
     {"year": 1967},
     "year=1922 khong khop note (W4c)",
     "note: '\u6c11\u570b\u4e94\u5341\u516d\u5e74\uff081967\uff09\uff0c\u7531\u661f\u9708"
     "\u5927\u5e2b\u958b\u5c71\u5275\u5efa' -> 1912+56-1 = 1967; note tu ghi 1967"),
]

COLS = ("label_zh", "source_ref", "year", "year_end")
DB_CX = None


def _tim(row_key):
    """Tra ve (rowid, dict gia_tri_hien_tai) cho 1 dong; dung lai neu khong dung 1."""
    did, sref = row_key
    rows = DB_CX.execute(
        "SELECT id, label_zh, source_ref, year, year_end FROM place_timeline_events "
        "WHERE dila_id=? AND source_ref=?", (did, sref)).fetchall()
    if len(rows) != 1:
        print("   LOI: tim thay %d dong cho %s / %s — dung lai." % (len(rows), did, sref))
        DB_CX.close()
        sys.exit(1)
    r = rows[0]
    return r[0], {"label_zh": r[1], "source_ref": r[2], "year": r[3], "year_end": r[4]}


def backup():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = BACKUP_DIR / ("lineage_t252w4_%s.db" % ts)
    shutil.copy2(str(DB), str(dst))
    return dst


def ap_dung(dry=False):
    global DB_CX
    DB_CX = sqlite3.connect(str(DB))
    now = datetime.now().isoformat()

    if dry:
        print("[DRY RUN] %d sua doi:" % len(FIXES))
        for did, sref, changes, ly_do, bc in FIXES:
            rowid, cur = _tim((did, sref))
            for cot, moi in changes.items():
                cu = cur.get(cot)
                trang_thai = "da dung" if cu == moi else "%r -> %r" % (cu, moi)
                print("   rowid=%-6s %-18s %-11s %s" % (rowid, did, cot, trang_thai))
        DB_CX.close()
        return

    dst = backup()
    them, bo_qua = [], []
    rows_out = []

    for did, sref, changes, ly_do, bc in FIXES:
        rowid, cur = _tim((did, sref))
        thay = {cot: (cur.get(cot), moi) for cot, moi in changes.items()
                if cur.get(cot) != moi}
        if not thay:
            bo_qua.append(did)
            continue
        sets = ", ".join("%s=?" % cot for cot in thay)
        DB_CX.execute("UPDATE place_timeline_events SET %s WHERE id=?" % sets,
                      [v[1] for v in thay.values()] + [rowid])
        them.append(did)
        rows_out.append({
            "rowid": rowid, "dila_id": did, "source_ref": sref,
            "ly_do": ly_do, "bang_chung": bc,
            "cu_moi": " | ".join("%s: %r -> %r" % (k, v[0], v[1])
                                 for k, v in thay.items()),
        })
    DB_CX.commit()

    manifest = {
        "task": "T252",
        "giai_doan": "W4",
        "nguon": SOURCE,
        "thoi_gian": now,
        "backup": str(dst.relative_to(BASE)) if dst.exists() else "",
        "da_sua": them,
        "bo_qua": bo_qua,
        "so_dong": len(them),
        "chi_tiet": [
            {"rowid": r["rowid"], "dila_id": r["dila_id"],
             "source_ref": r["source_ref"], "cu_moi": r["cu_moi"],
             "ly_do": r["ly_do"], "bang_chung": r["bang_chung"]}
            for r in rows_out],
        "revert": "python -X utf8 scripts/t252_w4_h3_fixes.py --revert "
                  "(tra gia tri CUA theo rowid, xem chi_tiet[].cu_moi)",
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                        encoding="utf-8")

    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    with open(EVIDENCE, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["rowid", "dila_id", "cu_moi", "ly_do", "bang_chung"])
        for r in rows_out:
            w.writerow([r["rowid"], r["dila_id"], r["cu_moi"], r["ly_do"],
                        r["bang_chung"]])
    DB_CX.close()

    print("T252 W4 ap dung xong")
    print("   backup        : %s" % manifest["backup"])
    print("   manifest      : %s" % MANIFEST.name)
    print("   evidence      : %s" % EVIDENCE.name)
    print("   da sua %d, bo qua (da dung) %d" % (len(them), len(bo_qua)))
    if len(them) + len(bo_qua) != len(FIXES):
        print("   CANH BAO: tong khong bang %d — kiem tra lai!" % len(FIXES))
        sys.exit(1)


def hoan_nguyen():
    global DB_CX
    if not MANIFEST.exists():
        print("Khong tim thay manifest: %s" % MANIFEST)
        sys.exit(1)
    mf = json.loads(MANIFEST.read_text(encoding="utf-8"))
    DB_CX = sqlite3.connect(str(DB))
    # Dung backup (khong doc manifest dang text) de tra dung gia tri CUA theo rowid
    backup_rel = mf.get("backup", "")
    if not backup_rel or not (BASE / backup_rel).exists():
        print("Khong tim thay backup: %s" % backup_rel)
        DB_CX.close()
        sys.exit(1)
    src = sqlite3.connect(str(BASE / backup_rel))
    dem = 0
    for r in mf.get("chi_tiet", []):
        rowid = r["rowid"]
        cu = src.execute(
            "SELECT label_zh, source_ref, year, year_end FROM place_timeline_events "
            "WHERE id=?", (rowid,)).fetchone()
        if cu is None:
            print("   LOI: rowid %s khong co trong backup" % rowid)
            continue
        DB_CX.execute("UPDATE place_timeline_events SET label_zh=?, source_ref=?, "
                      "year=?, year_end=? WHERE id=?",
                      (cu[0], cu[1], cu[2], cu[3], rowid))
        dem += 1
    DB_CX.commit()
    src.close()
    DB_CX.close()
    print("T252 W4 hoan nguyen xong (manifest %s)" % MANIFEST.name)
    print("   da tra lai %d dong (lay gia tri cu tu backup %s)" % (dem, backup_rel))
    if dem != len(mf.get("chi_tiet", [])):
        print("   CANH BAO: so dong khong khop manifest!")
        sys.exit(1)


def main():
    p = argparse.ArgumentParser(description="T252 W4 — sua 14 dong mâu thuẫn H3")
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
