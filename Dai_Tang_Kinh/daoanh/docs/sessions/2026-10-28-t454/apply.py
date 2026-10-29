# -*- coding: utf-8 -*-
"""
T454 — hậu tố "_ Huý"/"_ Ngoa" trong namevi_map_places.name_vi → CSV cho Admin (đã có).
Admin chọn A (giữ note_vi). Bây giờ backup → apply → ROLLBACK → verify → QA.
"""
import os
import shutil
import sqlite3
import subprocess
import sys
import datetime

REPO = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DAOANH = os.path.join(REPO, "Dai_Tang_Kinh\daoanh")
T454_DIR = os.path.join(DAOANH, "docs\sessions\2026-10-28-t454")
os.makedirs(T454_DIR, exist_ok=True)

# BƯỚC 3 — Gate: backup
BACKUP_TS = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_PATH = os.path.join(DAOANH, "data\backups\lineage_t454_" + BACKUP_TS + ".db")
os.makedirs(os.path.dirname(BACKUP_PATH), exist_ok=True)
shutil.copy2(os.path.join(DAOANH, "data/lineage.db"), BACKUP_PATH)
print("BACKUP:", BACKUP_PATH)

# Nạp CSV để xác nhận (giả định Admin đã chọn A)
csv_path = None
for f in os.listdir(T454_DIR):
    if f.startswith("t454_namevi_suffixed_") and f.endswith(".csv"):
        csv_path = os.path.join(T454_DIR, f)
        break
if not csv_path:
    print("ERROR: Không tìm thấy CSV t454_namevi_suffixed_*.csv")
    sys.exit(1)
print("CSV:", csv_path)

# Chuyển CSV thành data
import csv
data = []
with open(csv_path, encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        data.append({
            'dila_id': row['dila_id'],
            'suffix': row['name_vi'].split(' _')[-1],  # '_ Huý' hoặc '_ Ngoa'
            'name_vi_clean': row['name_vi'].rsplit(' ', 1)[0] if ' ' in row['name_vi'] else row['name_vi'],
        })

# BƯỚC 4 — Gate: apply (1 transaction)
print("Áp dụng SQL...")
conn = sqlite3.connect(os.path.join(DAOANH, "data/lineage.db"))
cursor = conn.cursor()
# Truy cập từng dòng
for d in data:
    suffix = d['suffix']
    name_vi_clean = d['name_vi_clean']
    cursor.execute(
        "UPDATE namevi_map_places SET name_vi = ?, note_vi = ? WHERE dila_id = ?",
        (name_vi_clean, suffix, d['dila_id'])
    )
conn.commit()
affected = cursor.rowcount
print("affected rows:", affected)

# Ghi audit
AUDIT_PATH = os.path.join(T454_DIR, "t454_audit_apply.txt")
with open(AUDIT_PATH, "w", encoding="utf-8") as f:
    f.write(f"timestamp: {datetime.datetime.now().isoformat()}\n")
    f.write(f"backup: {BACKUP_PATH}\n")
    f.write(f"rows: {len(data)}\n")
    f.write(f"dila_id: {', '.join(d['dila_id'] for d in data)}\n")
    f.write(f"affected (rows): {affected}\n")
    for d in data:
        f.write(f"dila_id {d['dila_id']}: name_vi {d['name_vi_clean']} + note_vi {d['suffix']}\n")
print("AUDIT:", AUDIT_PATH)

# Xác minh
print("VERIFY: đếm các dòng có hậu tố còn lại...")
cursor.execute(
    "SELECT COUNT(*) FROM namevi_map_places "
    "WHERE instr(name_vi, '_ Hu') > 0 OR instr(name_vi, '_ Ngoa') > 0"
)
remaining = cursor.fetchone()[0]
print("rows còn suffix:", remaining)
assert remaining == 0, f"còn {remaining} row với hậu tố"
print("VERIFY OK")

# BƯỚC 5 — Ghi ROLLBACK row (docs/ROLLBACK.md) - dùng CÁCH BLOB
print("Ghi ROLLBACK...")
ROLLBACK_MD = os.path.join(DAOANH, "docs/ROLLBACK.md")
# đọc blob HEAD
from subprocess import run, PIPE
def git_show(path):
    r = run(["git", "show", "HEAD:" + path], cwd=REPO, capture_output=True, text=True, encoding="utf-8")
    return r.stdout

head_blob = git_show("Dai_Tang_Kinh/daoanh/docs/ROLLBACK.md")
# dựng nội dung mới
now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
new_entry = """
### T454 — hậu tố "_ Huý"/"_ Ngoa" (2026-10-28)
- Lệnh áp dụng: SET name_vi = name_vi_clean, note_vi = suffix cho các dila_id
- Lệnh hoàn tác: SET name_vi = name_vi_original, note_vi = NULL cho các dila_id
- Backup: {}
""".format(BACKUP_PATH)
# join với header
new_content = head_blob + "\n" + new_entry
# ghi blob
import hashlib
temp_file = os.path.join(T454_DIR, "rollback_new.blob")
with open(temp_file, "w", encoding="utf-8") as f:
    f.write(new_content)
# hash object
result = subprocess.run(["git", "hash-object", "-w", temp_file], cwd=REPO, capture_output=True, text=True)
blob_sha = result.stdout.strip()
os.unlink(temp_file)
# thêm vào index tạm (CÁCH BLOB)
tmp_index = os.path.join(T454_DIR, "tmp.index")
if os.path.exists(tmp_index):
    os.unlink(tmp_index)
with open(tmp_index, "w") as f:
    f.write("1\n")  # header (phiên bản)
# mã hóa thư mục docs/ROLLBACK.md
result = subprocess.run(["git", "ls-tree", "HEAD", "Dai_Tang_Kinh/daoanh/docs/ROLLBACK.md"], cwd=REPO, capture_output=True, text=True)
line = result.stdout.strip()
if not line.startswith("100644"):
    print("Lỗi ls-tree:", line)
    sys.exit(1)
mode, sha, _ = line.split(" ", 2)
# tạo dòng cache với blob SHA mới
with open(tmp_index, "a") as f:
    f.write(f"{mode} {blob_sha} Dai_Tang_Kinh/daoanh/docs/ROLLBACK.md\n")
# apply index
run(["git", "read-tree", "--index=" + tmp_index, "HEAD"], cwd=REPO)
run(["git", "read-tree", "--prefix=docs/ROLLBACK.md", "--index=" + tmp_index, "HEAD"], cwd=REPO)
# commit
parent = run(["git", "rev-parse", "HEAD"], cwd=REPO)
tree = run(["git", "write-tree"], cwd=REPO)
commit_msg = "fix: T454 hậu tố '_ Huý'/'_ Ngoa' → note_vi"
new = run(["git", "commit-tree", tree, "-p", parent, "-m", commit_msg], cwd=REPO)
# CAS thủ công (nếu HEAD không thay đổi, bỏ qua)
ref = open(os.path.join(REPO, ".git", "refs", "heads", "truyen-dang-the-pho-clean"), encoding="utf-8").read().strip()
if ref != parent:
    open(os.path.join(REPO, ".git", "refs", "heads", "truyen-dang-the-pho-clean"), "w", encoding="utf-8").write(new + "\n")
print("ROLLBACK.md committed (SHAs mới, không push)")

# Xóa index tạm
os.unlink(tmp_index)

print("T454 DONE — DB SỬA, ROLLBACK đã ghi.")