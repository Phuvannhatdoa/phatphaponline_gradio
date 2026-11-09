"""T500 — dry-run sửa volume_files theo mốc quyển trong XML CBETA cục bộ (chỉ đọc, không ghi DB).

Quy tắc (đã Admin duyệt 2026-10-31, mục 1):
  - Với mỗi (work_id, juan_no), tìm file XML có <milestone unit="juan" n="NNN"> tương ứng.
  - Nếu chỉ có MỘT file cho cặp đó và khác file_id hiện tại: đề xuất sửa.
  - Nếu cùng (work_id, juan_no) xuất hiện ở NHIỀU file: không tự sửa, ghi vào conflicts (Admin quyết,
    mục 2). Không đoán.
  - Quyển không có mốc trong XML cục bộ: giữ nguyên, không đề xuất.

Đầu ra (docs/sessions/2026-10-31/cbeta-volumes/):
  volume_files_fix_proposal.csv   work_id, juan_no, file_hien_tai, file_de_xuat
  volume_files_conflicts.csv      work_id, juan_no, cac_file_xml
  volume_files_fix_summary.json   số liệu tổng hợp
"""
import collections
import csv
import json
import pathlib
import re
import sqlite3
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
XML = ROOT / "data" / "cbeta" / "xml-p5-full"
DB = ROOT / "data" / "lineage.db"
OUT = ROOT / "docs" / "sessions" / "2026-10-31" / "cbeta-volumes"

MILESTONE = re.compile(r"<milestone\b[^>]*>")
FILE_STEM = re.compile(r"^([A-Z]+)[0-9]+[a-z]?n(.+)$")


def build_index():
    """(work_id, juan_no) -> set(file_stem). Đọc từng dòng, không nạp cả file vào RAM."""
    idx = collections.defaultdict(set)
    for f in XML.rglob("*.xml"):
        if "schema" in f.parts:
            continue
        m = FILE_STEM.match(f.stem)
        if not m:
            continue
        work = m.group(1) + m.group(2)
        with open(f, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if "juan" not in line:
                    continue
                for tag in MILESTONE.findall(line):
                    if 'unit="juan"' not in tag:
                        continue
                    n = re.search(r'\bn="(\d+)"', tag)
                    if n:
                        idx[(work, int(n.group(1)))].add(f.stem)
    return idx


def main():
    uri = DB.resolve().as_uri() + "?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    rows = con.execute("SELECT work_id, juan_no, file_id FROM volume_files").fetchall()
    con.close()

    print("Đang quét XML cục bộ (có thể vài phút)...", flush=True)
    idx = build_index()

    proposals, conflicts = [], []
    same = missing = 0
    for work, juan, current in rows:
        found = idx.get((work, juan))
        if not found:
            missing += 1
            continue
        if len(found) > 1:
            conflicts.append([work, juan, "|".join(sorted(found))])
            continue
        (proposed,) = found
        if proposed == current:
            same += 1
        else:
            proposals.append([work, juan, current, proposed])

    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "volume_files_fix_proposal.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["work_id", "juan_no", "file_hien_tai", "file_de_xuat"])
        w.writerows(proposals)
    with open(OUT / "volume_files_conflicts.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["work_id", "juan_no", "cac_file_xml"])
        w.writerows(conflicts)

    summary = {
        "rows_total": len(rows),
        "da_dung": same,
        "de_xuat_sua": len(proposals),
        "works_de_xuat_sua": len({r[0] for r in proposals}),
        "xung_dot": len(conflicts),
        "works_xung_dot": sorted({r[0] for r in conflicts}),
        "khong_co_moc_xml": missing,
    }
    (OUT / "volume_files_fix_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
