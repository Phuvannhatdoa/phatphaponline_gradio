# -*- coding: utf-8 -*-
"""T455 — kiểm tra quy ước viết tên trong people.name_vi + dựng đề xuất 260 dòng (dry-run)."""
import csv, os, re, sqlite3, sys, collections

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DB = os.path.join(BASE, "Dai_Tang_Kinh", "daoanh", "data", "lineage.db")
D = os.path.join(BASE, "Dai_Tang_Kinh", "daoanh", "docs", "sessions", "2026-10-28-t455")
OUT = os.path.join(BASE, "Dai_Tang_Kinh", "daoanh", "docs", "sessions", "2026-10-30-t455-apply")

conn = sqlite3.connect("file:" + DB + "?mode=ro", uri=True)

# ---- 1. quy ước viết tên hiện hành ----
print("=== quy ước viết tên trong people.name_vi (48.673 dòng) ===")
with_hyphen = 0
with_han = 0
lower_word = 0
total = 0
samples = []
for (nv,) in conn.execute("SELECT name_vi FROM people WHERE name_vi IS NOT NULL AND name_vi <> ''"):
    total += 1
    if "-" in nv:
        with_hyphen += 1
    if any(0x4E00 <= ord(c) <= 0x9FFF for c in nv):
        with_han += 1
    words = [w for w in re.split(r"[\s\-]+", nv) if w]
    if any(w and w[0].islower() and w[0].isalpha() for w in words):
        lower_word += 1
        if len(samples) < 6:
            samples.append(nv)
print("   có dấu gạch nối '-'      : %d (%.1f%%)" % (with_hyphen, with_hyphen / total * 100))
print("   còn chữ Hán              : %d (%.1f%%)" % (with_han, with_han / total * 100))
print("   có từ viết thường (a-z)  : %d (%.1f%%)" % (lower_word, lower_word / total * 100))
print("   ví dụ viết thường:", samples)
conn.close()

# ---- 2. dựng đề xuất ----
def to_title(s):
    """Chuẩn hoá: bỏ gạch nối, Title Case mỗi từ, giữ dấu thanh."""
    s = s.replace("-", " ").replace("–", " ").replace("—", " ").replace("_", " ")
    s = re.sub(r"\s+", " ", s).strip()
    out = []
    for w in s.split(" "):
        if not w:
            continue
        out.append(w[0].upper() + w[1:])
    return " ".join(out)


def has_han(s):
    return any(0x4E00 <= ord(c) <= 0x9FFF for c in s)


os.makedirs(OUT, exist_ok=True)
rows_out = []
summary = collections.Counter()

for lot in ["A", "C"]:
    with open(os.path.join(D, "name_vi_mismatch_%s.csv" % lot), encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            pid = r["person_id"]
            zq = r["name_vi_db_ZQ"].strip()
            cloud = r["name_vi_cloud"].strip()
            new = to_title(cloud)
            action = "updated"
            reason = ""
            if lot == "A":
                if has_han(new):
                    action = "skip"
                    reason = "Cloud van con chu Han — can tra tu dien"
                elif new == to_title(zq):
                    action = "unchanged"
                    reason = "Cloud chung thu tu ZQ (chi khac dau gach noi) — giu nguyen"
            rows_out.append({
                "lot": lot,
                "person_id": pid,
                "name_zh_catalog": r["name_zh_catalog"],
                "name_vi_old_ZQ": zq,
                "name_vi_new": new,
                "action": action,
                "reason": reason,
                "so_lan": r["so_lan"],
            })
            summary[(lot, action)] += 1

# lô B: ghi chú alias, KHÔNG sửa
with open(os.path.join(D, "name_vi_mismatch_B.csv"), encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        rows_out.append({
            "lot": "B",
            "person_id": r["person_id"],
            "name_zh_catalog": r["name_zh_catalog"],
            "name_vi_old_ZQ": r["name_vi_db_ZQ"].strip(),
            "name_vi_new": to_title(r["name_vi_cloud"].strip()),
            "action": "kept_alias",
            "reason": "alias - da doi chieu, giu theo ZQ (khac quy uoc doc ca tu)",
            "so_lan": r["so_lan"],
        })
        summary[("B", "kept_alias")] += 1

path = os.path.join(OUT, "t455_proposal_planA.csv")
with open(path, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
    w.writeheader()
    w.writerows(rows_out)

print()
print("=== đề xuất (phương án A) ===")
for k in sorted(summary):
    print("   lô %s / %-10s : %d" % (k[0], k[1], summary[k]))
print("   tổng dòng đề xuất:", len(rows_out))
print("   file:", path)

print()
print("=== các dòng KHÔNG sửa được (cần tra tay) ===")
for r in rows_out:
    if r["action"] in ("skip", "unchanged"):
        print("   [%s] %-9s Hán=%-12s ZQ=%-20s Cloud=%-20s %s" % (
            r["lot"], r["person_id"], r["name_zh_catalog"][:12],
            r["name_vi_old_ZQ"][:20], r["name_vi_new"][:20], r["reason"]))
