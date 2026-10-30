# -*- coding: utf-8 -*-
"""Kiểm tra chữ đa âm (polyphonic) trong lô B — nguyên nhân gốc lý do charmap không phân định được."""
import sqlite3, os, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DB = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\lineage.db"
conn = sqlite3.connect("file:" + DB + "?mode=ro", uri=True)

CHARS = ["樹", "畏", "著", "頂", "般", "若", "錩", "閻", "崛", "那", "空", "昰", "竑", "玘", "顗", "沖", "虚", "虛", "讕", "摩"]
print("char | reading | polyphonic | candidates")
print("-" * 78)
for ch in CHARS:
    r = conn.execute(
        "SELECT reading, is_polyphonic, candidates FROM hanviet_char_map WHERE char = ?", (ch,)
    ).fetchone()
    if r:
        print("  %s  | %-8s | %-5s | %s" % (ch, r[0], r[1], (r[2] or "")[:40]))
    else:
        r2 = conn.execute("SELECT hv FROM hanviet_fallback WHERE ch = ?", (ch,)).fetchone()
        r3 = conn.execute("SELECT hanviet FROM custom_hanviet_override WHERE char = ?", (ch,)).fetchone()
        print("  %s  | KHÔNG có trong hanviet_char_map | fallback=%s | override=%s" % (
            ch, r2[0] if r2 else "-", r3[0] if r3 else "-"))

n_poly = conn.execute("SELECT COUNT(*) FROM hanviet_char_map WHERE is_polyphonic = 1").fetchone()[0]
n_tot = conn.execute("SELECT COUNT(*) FROM hanviet_char_map").fetchone()[0]
print("\nhanviet_char_map: %d chữ, trong đó %d đa âm (%.1f%%)" % (n_tot, n_poly, n_poly / n_tot * 100))
conn.close()
