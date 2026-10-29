# -*- coding: utf-8 -*-
"""
T454 apply: sửa namevi_map_places.name_vi (xóa hậu tố "_ Huý"/"_ Ngoa") → note_vi.
Dựa trên CSV docs/sessions/2026-10-28-t454/t454_namevi_suffixed_*.csv
do Admin chọn A (chuyển sang note_vi).
"""
import os
import sqlite3
import datetime
import csv
import shutil

DAOANH = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh"
T454_DIR = os.path.join(DAOANH, "docs/sessions/2026-10-28-t454")
os.makedirs(T454_DIR, exist_ok=True)

# Nạp CSV
csv_path = None
for f in os.listdir(T454_DIR):
    if f.startswith("t454_namevi_suffixed_") and f.endswith(".csv"):
        csv_path = os.path.join(T454_DIR, f)
        break
if not csv_path:
    print("Lỗi: Không tìm thấy CSV t454_namevi_suffixed_*.csv")
    exit(1)

data = []
with open(csv_path, encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        name_vi = row['name_vi']
        if ' _' in name_vi:
            suffix = name_vi.split(' _')[-1]
        else:
            suffix = ''
        name_vi_clean = name_vi.rsplit(' ', 1)[0] if ' ' in name_vi else name_vi
        data.append({
            'dila_id': row['dila_id'],
            'suffix': suffix,
            'name_vi_clean': name_vi_clean,
        })
print("Dòng cần sửa:", len(data))
for d in data:
    print(f"  {d['dila_id']}: '{d['name_vi_clean']}' + note_vi '{d['suffix']}'")

# Backup
BACKUP_TS = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_PATH = os.path.join(DAOANH, "data/backups/lineage_t454_" + BACKUP_TS + ".db")
os.makedirs(os.path.dirname(BACKUP_PATH), exist_ok=True)
shutil.copy2(os.path.join(DAOANH, "data/lineage.db"), BACKUP_PATH)
print("BACKUP:", BACKUP_PATH)

# Apply UPDATE
print("Đang cập nhật namevi_map_places...")
conn = sqlite3.connect(os.path.join(DAOANH, "data/lineage.db"))
cursor = conn.cursor()
for d in data:
    cursor.execute(
        "UPDATE namevi_map_places SET name_vi = ?, note_vi = ? WHERE dila_id = ?",
        (d['name_vi_clean'], d['suffix'], d['dila_id'])
    )
conn.commit()
affected = cursor.rowcount
print("affected rows:", affected)

# Verify
print("Verifying...")
cursor.execute(
    "SELECT COUNT(*) FROM namevi_map_places "
    "WHERE instr(name_vi, '_ Hu') > 0 OR instr(name_vi, '_ Ngoa') > 0"
)
remaining = cursor.fetchone()[0]
print("rows còn suffix:", remaining)
if remaining > 0:
    print("Xác minh lỗi: vẫn còn suffix!")
    exit(1)
print("T454 apply DONE. Backup:", BACKUP_PATH)

# Append ghi chú ROLLBACK
ROLLBACK_PATH = os.path.join(DAOANH, "docs/ROLLBACK.md")
now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
with open(ROLLBACK_PATH, "a", encoding="utf-8") as f:
    f.write(f"\n### T454 — hậu tố '_ Huý'/'_ Ngoa' ({now})\n")
    f.write(f"- Thao tác: UPDATE namevi_map_places SET name_vi = <không hậu tố>, note_vi = '<suffix>'\n")
    f.write(f"- Hoàn tác: Dùng backup DB và đặt lại note_vi = NULL + nối suffix vào name_vi\n")
    f.write(f"- Backup: {BACKUP_PATH}\n")
    f.write(f"- Dila_id xử lý: {', '.join(d['dila_id'] for d in data)}\n")
print("Đã ghi ghi chú ROLLBACK.md.")

conn.close()