"""
T454: đo lại name_vi_map_places có hậu tố "_ Huý"/"_ Ngoa".

Xử lý CSV cho Admin (Chọn A: giữ note_vi, hoặc B: xoá hậu tố khỏi name_vi).
"""
import sqlite3
import csv
import os

con = sqlite3.connect('data/lineage.db', uri=True)
rows = con.execute(
    "SELECT dila_id, name_vi, name_zh, note_vi, source, created_at "
    "FROM namevi_map_places "
    "WHERE instr(name_vi, '_ Hu') > 0 OR instr(name_vi, '_ Ngoa') > 0"
).fetchall()
print("Số dòng có hậu tố:", len(rows))

# Tạo CSV cho Admin
import datetime
label = 't454_namevi_suffixed_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + '.csv'
path = os.path.join('docs/sessions/2026-10-28-t454/', label)
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['dila_id', 'name_vi', 'name_zh', 'note_vi', 'source', 'created_at'])
    for r in rows:
        w.writerow(r)
print('CSV created:', path)

for r in rows:
    print(dict(zip(['dila_id', 'name_vi', 'name_zh', 'note_vi', 'source', 'created_at'], r)))