# -*- coding: utf-8 -*-
"""Phân tích chính xác: trong mỗi lô, khác biệt thực chất là gì?"""
import csv, os, re, sys, unicodedata

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
D = os.path.join(BASE, "Dai_Tang_Kinh", "daoanh", "docs", "sessions", "2026-10-28-t455")


def norm(s):
    """Bỏ dấu gạch nối + space + khác biệt case, giữ dấu thanh."""
    s = s.replace("-", " ").replace("–", " ").replace("—", " ")
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


def no_diacritic(s):
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if not unicodedata.combining(c))


for lot in ["A", "B", "C"]:
    p = os.path.join(D, "name_vi_mismatch_%s.csv" % lot)
    with open(p, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    same_after_norm = sum(1 for r in rows if norm(r["name_vi_db_ZQ"]) == norm(r["name_vi_cloud"]))
    same_after_nodiac = sum(1 for r in rows
                            if no_diacritic(norm(r["name_vi_db_ZQ"])) == no_diacritic(norm(r["name_vi_cloud"])))
    identical = sum(1 for r in rows if r["name_vi_db_ZQ"] == r["name_vi_cloud"])
    has_han = sum(1 for r in rows if any(0x4E00 <= ord(c) <= 0x9FFF for c in r["name_vi_db_ZQ"]))
    # khác biệt ở cấp độ từ
    one_word_diff = 0
    for r in rows:
        a, b = norm(r["name_vi_db_ZQ"]).split(), norm(r["name_vi_cloud"]).split()
        if len(a) == len(b):
            d = sum(1 for x, y in zip(a, b) if x != y)
            if d <= 1:
                one_word_diff += 1
    print("LÔ %s (%d dòng):" % (lot, len(rows)))
    print("   ZQ == Cloud (giống hệt)              : %d" % identical)
    print("   giống sau khi bỏ gạch nối/space        : %d" % same_after_norm)
    print("   giống sau khi bỏ gạch + bỏ dấu thanh   : %d" % same_after_nodiac)
    print("   khác nhau ≤1 TỪ (sai 1 chữ)           : %d" % one_word_diff)
    print("   còn chữ Hán trong name_vi               : %d" % has_han)
    print()

# Lô B: đếm dạng khác biệt cụ thể
p = os.path.join(D, "name_vi_mismatch_B.csv")
with open(p, encoding="utf-8-sig") as f:
    b_rows = list(csv.DictReader(f))
only_hyphen = sum(1 for r in b_rows if norm(r["name_vi_db_ZQ"]) == norm(r["name_vi_cloud"]))
diff_word = []
for r in b_rows:
    a, b = norm(r["name_vi_db_ZQ"]).split(), norm(r["name_vi_cloud"]).split()
    if a != b:
        diff_word.append((r["person_id"], r["name_zh_catalog"], r["name_vi_db_ZQ"], r["name_vi_cloud"], r["so_lan"]))
print("LÔ B — chi tiết %d dòng còn khác sau khi bỏ gạch nối:" % len(diff_word))
for x in diff_word[:20]:
    print("   %-9s %-9s ZQ=%-20s Cloud=%-20s x%s" % (x[0], x[1][:9], x[2][:20], x[3][:20], x[4]))
print("   ... (tổng %d)" % len(diff_word))
