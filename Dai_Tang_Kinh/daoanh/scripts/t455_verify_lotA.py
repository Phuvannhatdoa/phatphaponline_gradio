# -*- coding: utf-8 -*-
"""T455 — kiểm chứng từng chữ cho lô A (đề xuất sửa) + tra tay 2 dòng đặc biệt."""
import csv, os, re, sqlite3, sys, unicodedata

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DB = os.path.join(BASE, "Dai_Tang_Kinh", "daoanh", "data", "lineage.db")
OUT = os.path.join(BASE, "Dai_Tang_Kinh", "daoanh", "docs", "sessions", "2026-10-30-t455-apply")
PROP = os.path.join(OUT, "t455_proposal_planA.csv")

conn = sqlite3.connect("file:" + DB + "?mode=ro", uri=True)
cm = {}
for ch, reading, poly, cand in conn.execute("SELECT char, reading, is_polyphonic, candidates FROM hanviet_char_map"):
    cm[ch] = (reading, poly, cand or "")
ovr = {c: v for c, v in conn.execute("SELECT char, hanviet FROM custom_hanviet_override")}
fb = {c: v for c, v in conn.execute("SELECT ch, hv FROM hanviet_fallback")}


def nd(s):
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if not unicodedata.combining(c)).lower().replace(" ", "")


cmn = {nd(k): v[0] for k, v in cm.items()}
ovrn = {nd(k): v for k, v in ovr.items()}
fbn = {nd(k): v for k, v in fb.items()}

print("=== tra chữ đặc biệt ===")
for ch in ["頙", "璹", "橖", "鸖", "蜞", "溈", "僼", "晙", "頙", "哌", "玘", "旲", "涑"]:
    k = nd(ch)
    src = "charmap" if k in cmn else ("override" if k in ovrn else ("fallback" if k in fbn else "KHÔNG CÓ"))
    val = cmn.get(k, ovrn.get(k, fbn.get(k, "-")))
    poly = cm.get(ch, ("", 0, ""))[1] if ch in cm else ""
    print("   %s -> %-10s (%s%s)" % (ch, val, src, ", đa âm" if poly else ""))

print()
print("=== kiểm chứng 22 dòng lô A sẽ sửa: chữ Hán -> charmap vs tên mới (Cloud) ===")
with open(PROP, encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))
flag = []
for r in rows:
    if r["lot"] != "A" or r["action"] != "updated":
        continue
    han = r["name_zh_catalog"]
    new = r["name_vi_new"]
    newtok = [nd(t) for t in re.split(r"[\s\-]+", new) if t]
    notes = []
    for ch in han:
        k = nd(ch)
        if not k:
            continue
        reading = cmn.get(k) or ovrn.get(k) or fbn.get(k)
        if not reading:
            notes.append("%s: KHÔNG có trong bảng đọc" % ch)
            continue
        rk = nd(reading)
        if not any(rk == nt or rk in nt for nt in newtok):
            notes.append("%s: charmap='%s' KHÔNG thấy trong '%s'" % (ch, reading, new))
    if notes:
        flag.append((r, notes))
        print("  ⚠ %-9s %-10s -> %-22s | %s" % (r["person_id"], han[:10], new[:22], "; ".join(notes)))
    else:
        print("  ✓ %-9s %-10s -> %-22s | mọi chữ khớp bảng đọc" % (r["person_id"], han[:10], new[:22]))

print()
print("số dòng cần người xem lại:", len(flag))
conn.close()
