"""
T44 — gợi ý duyệt cho nhóm exact_year KHÔNG trùng tu (596 dòng).
CHỈ ĐỌC DB (mode=ro). Ghi file TSV gợi ý để Admin xem. Không ghi DB.
Chạy: python -X utf8 scripts/t44_suggest_exact.py
"""
import csv, re, sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "docs" / "evidence" / "2026-10-09_T44_candidates.tsv"
OUT = ROOT / "docs" / "evidence" / "2026-10-10_T44_exact_suggestions.tsv"
DB = ROOT / "data" / "lineage.db"

FOUND = re.compile(r"(建|創|創建|立|所立|置|造|始建|興建|開創|敕建|請建)")
NOT_FOUND = re.compile(r"(碑|石刻|碑文|摩崖|撰|題|改|更名|賜額|為功徳院|功德院|重修|重建|復建|修|移|遷|廟|觀|道士)")
MUST_BUDDHIST = re.compile(r"(寺|院|庵|菴|禪|蘭若|精舍|刹|寺廟)")

def classify(note, year, era):
    n = note or ""
    # Ghi chú có năm/niên hiệu và động từ thành lập trong cùng câu
    clauses = re.split(r"[。；;，,、]", n)
    hit = [c for c in clauses if era and era in c and FOUND.search(c)]
    if not hit:
        return "CẦN XEM", "không thấy động từ thành lập gần niên hiệu"
    if any(NOT_FOUND.search(c) for c in hit):
        return "CẦN XEM", "có từ khóa khác (trùng tu/bia/đổi tên/đạo quán) gần niên hiệu"
    return "ĐỀ XUẤT DUYỆT", "có động từ thành lập gần niên hiệu, không có từ khóa khác"

def main():
    rows = [r for r in csv.DictReader(open(SRC, encoding="utf-8"), delimiter="\t")
            if r["method"] == "exact_year" and r["has_renovation_flag"] == "N"]
    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    out = []
    for i, r in enumerate(rows, 1):
        note = con.execute("select note from places_dila where id=?", (r["dila_id"],)).fetchone()
        note = note[0] if note else ""
        sug, why = classify(note, r["year"], r["era_name"])
        out.append({**r, "goi_y": sug, "ly_do": why, "admin_quyet_dinh": "", "admin_ghi_chu": ""})
        if i % 100 == 0:
            print(f"... {i}/{len(rows)}", flush=True)
    con.close()
    cols = list(out[0].keys())
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter="\t")
        w.writeheader(); w.writerows(out)
    from collections import Counter
    print("Tổng:", len(out), Counter(o["goi_y"] for o in out))
    print("Ghi:", OUT)

if __name__ == "__main__":
    main()
