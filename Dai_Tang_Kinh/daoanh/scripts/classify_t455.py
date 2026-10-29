#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T455 — classify 794 name_vi mismatches into 3 lots (A/B/C)."""
import csv, os

ALL_CSV = r"Dai_Tang_Kinh/daoanh/docs/sessions/2026-10-22/T453/name_vi_mismatch_ALL.csv"
OUT_DIR = r"Dai_Tang_Kinh/daoanh/docs/sessions/2026-10-28-t455"
os.makedirs(OUT_DIR, exist_ok=True)

with open(ALL_CSV, encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))

lotA = []  # ZQ sai rõ - cần sửa tên
lotB = []  # alias cùng người - giữ nguyên, ghi chú alias
lotC = []  # quy tắc chính tả - sửa đúng

def is_english(s):
    s = s.strip()
    return len(s) > 0 and all(ord(c) < 128 for c in s)

def has_han(s):
    return any(0x4E00 <= ord(c) <= 0x9FFF for c in s)

for row in rows:
    name_zh_catalog = row.get('name_zh_catalog', '').strip()
    name_vi_db_ZQ = row.get('name_vi_db_ZQ', '').strip()
    name_vi_cloud = row.get('name_vi_cloud', '').strip()
    
    # Lô A: ZQ name_vi là tên Anh/Hán lạc (khác catalog rõ ràng → ZQ sai rõ, cần sửa)
    if is_english(name_vi_db_ZQ) and not is_english(name_zh_catalog):
        lotA.append(row)
        continue
    # Lô A: ZQ name_vi là Hán nhưng cách viết khác catalog (ví dụ 羗 vs 佧) → sửa ZQ
    if has_han(name_vi_db_ZQ) and has_han(name_zh_catalog) and name_vi_db_ZQ != name_zh_catalog:
        lotA.append(row)
        continue
    
    # Lô B: alias cùng người — ZQ name_vi và cloud giống nhau hoặc gần giống nhau
    if name_vi_db_ZQ and name_vi_cloud:
        zq_words = set(name_vi_db_ZQ.replace('-', ' ').replace('_', ' ').split())
        cloud_words = set(name_vi_cloud.replace('-', ' ').replace('_', ' ').split())
        common = zq_words & cloud_words
        if common and abs(len(name_vi_db_ZQ) - len(name_vi_cloud)) <= max(len(name_vi_db_ZQ), len(name_vi_cloud)) * 0.3:
            lotB.append(row)
            continue
    
    # Lô C: fallback — quy tắc chính tả / thêm Hán / sửa tên
    lotC.append(row)

# Ghi 3 file
for lot_name, lot_rows in [('A', lotA), ('B', lotB), ('C', lotC)]:
    out_path = os.path.join(OUT_DIR, f'name_vi_mismatch_{lot_name}.csv')
    with open(out_path, 'w', encoding='utf-8-sig', newline='') as f:
        if lot_rows:
            writer = csv.DictWriter(f, fieldnames=lot_rows[0].keys())
            writer.writeheader()
            writer.writerows(lot_rows)
    print(f'{lot_name}: {len(lot_rows)} dòng -> {out_path}')

print(f'LOT SUMMARY: A={len(lotA)}, B={len(lotB)}, C={len(lotC)}, total={len(rows)}')
