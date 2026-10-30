# -*- coding: utf-8 -*-
"""T455 — đối chiếu 3 lô với bảng đọc Hán-Việt chuẩn của dự án (hanviet_char_map).

Đây là "chuẩn thứ 3": không phải ZQ, không phải Cloud, mà là bảng tra Hán→Việt
do dự án tự xây (custom_hanviet_override > HAN_VIET_CHAR > hanviet_fallback).
"""
import csv, os, re, sqlite3, sys, unicodedata

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DAO = os.path.join(BASE, "Dai_Tang_Kinh", "daoanh")
DB = os.path.join(DAO, "data", "lineage.db")
D = os.path.join(DAO, "docs", "sessions", "2026-10-28-t455")

conn = sqlite3.connect("file:" + DB + "?mode=ro", uri=True)
tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
print("bảng charmap có trong DB:", [t for t in tables if "hanviet" in t.lower() or "charmap" in t.lower()])

charmap = {}
if "hanviet_char_map" in tables:
    charmap = {ch: hv for ch, hv in conn.execute("SELECT char, reading FROM hanviet_char_map")}
    print("hanviet_char_map:", len(charmap), "chữ")
elif "custom_hanviet_override" in tables:
    charmap = {ch: hv for ch, hv in conn.execute("SELECT char, hanviet FROM custom_hanviet_override")}
    print("custom_hanviet_override:", len(charmap), "chữ")
conn.close()

# bỏ dấu để so khớp mềm
def nd(s):
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if not unicodedata.combining(c)).lower().replace(" ", "")

cm = {nd(k): v for k, v in charmap.items()}

def read_han_viet(han):
    """Đọc Hán->Việt theo charmap; trả về (chuỗi, số chữ đọc được/tổng)."""
    out, ok, total = [], 0, 0
    for ch in han:
        if not ch.strip():
            continue
        total += 1
        v = cm.get(nd(ch))
        if v:
            out.append(v); ok += 1
        else:
            out.append(ch)
    return " ".join(out), ok, total

def tokens(s):
    s = re.sub(r"[-–—_]", " ", s)
    return [t for t in re.split(r"\s+", s.strip().lower()) if t]

def match_ratio(a, b):
    """Tỉ lệ khớp theo từ (không phân biệt dấu thanh)."""
    ta, tb = tokens(nd(a)), tokens(nd(b))
    if not ta or not tb:
        return 0.0
    common = 0
    for x in ta:
        if x in tb:
            common += 1
    return common / max(len(ta), len(tb))

for lot in ["A", "B", "C"]:
    p = os.path.join(D, "name_vi_mismatch_%s.csv" % lot)
    with open(p, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    zq_wins = cloud_wins = tie = unreadable = 0
    charmap_support_zq = charmap_support_cloud = 0
    samples = []
    for r in rows:
        han = r["name_zh_catalog"]
        zq, cloud = r["name_vi_db_ZQ"], r["name_vi_cloud"]
        hv, ok, total = read_han_viet(han)
        if total == 0 or ok / total < 0.5:
            unreadable += 1
            continue
        sz, sc = match_ratio(hv, zq), match_ratio(hv, cloud)
        if abs(sz - sc) < 0.01:
            tie += 1
            if sz > 0.7:
                charmap_support_zq += 1; charmap_support_cloud += 1
        elif sz > sc:
            charmap_support_zq += 1
            if len(samples) < 6 and sz - sc > 0.3:
                samples.append(("ZQ", r["person_id"], han, zq, cloud, hv))
        else:
            charmap_support_cloud += 1
            if len(samples) < 6 and sc - sz > 0.3:
                samples.append(("CLOUD", r["person_id"], han, zq, cloud, hv))
    print()
    print("=" * 78)
    print("LÔ %s (%d dòng) — charmap đọc được %d, không đọc được %d" % (lot, len(rows), len(rows) - unreadable, unreadable))
    print("  charmap nghiêng về ZQ   : %d" % charmap_support_zq)
    print("  charmap nghiêng về Cloud : %d" % charmap_support_cloud)
    print("  hòa nhau (không phân định) : %d" % tie)
    for s in samples:
        print("   %-6s %-9s Hán=%-10s ZQ=%-20s Cloud=%-20s charmap=%s" % (s[0], s[1], s[2][:10], s[3][:20], s[4][:20], s[5][:26]))
