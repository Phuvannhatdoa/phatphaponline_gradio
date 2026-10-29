#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""1) Gỡ 2 khối T454/T457 trùng (do tôi append thủ công) khỏi worktree ROLLBACK.md.
2) Chuẩn bị blob ROLLBACK.md từ HEAD + backup path chính xác của T454.
KHÔNG đụng WIP của session khác (T482/T470/T449/T379/T474/T447/T477/Tiến Độ Dịch).
"""
import os, subprocess, sys

BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
os.chdir(BASE)
RB = "Dai_Tang_Kinh/daoanh/docs/ROLLBACK.md"
WT = os.path.join(BASE, RB.replace("/", os.sep))

# ---- 1) gỡ khối trùng trong worktree ----
with open(WT, encoding="utf-8") as f:
    wt = f.read()

dup_a = """
### T454 — cleanup suffix (2026-10-28)
- Apply: UPDATE namevi_map_places SET name_vi = ... WHERE so_vi = ... (5 dòng)
- Backup: data/backups/lineage_t454_*.db
- Revert: UPDATE namevi_map_places SET name_vi = '<cu>' WHERE id IN (...))
"""
dup_b = """
### T457 — DILA Bio Nexus import A2 (2026-10-29)
- Apply: INSERT INTO dila_bio_nexus (+ link tables dila_bio_nexus_person/place, 21.740 dòng)
- Backup: data/backups/lineage_t457_20261029_094901.db
- Revert: DROP TABLE dila_bio_nexus; DROP TABLE dila_bio_nexus_person; DROP TABLE dila_bio_nexus_place;
  DROP INDEX idx_bn_book; DROP INDEX idx_bn_person; DROP INDEX idx_bn_year; DROP INDEX idx_bn_place;
"""
removed = 0
for dup in (dup_a, dup_b):
    if dup in wt:
        wt = wt.replace(dup, "\n")
        removed += 1
        print("removed duplicate block:", dup.strip().split("\n")[0][:70])
with open(WT, "w", encoding="utf-8", newline="") as f:
    f.write(wt)
print("worktree ROLLBACK.md: removed %d duplicate block(s), now %d chars" % (removed, len(wt)))

# ---- 2) blob HEAD + backup path chính xác ----
head = subprocess.run(["git", "show", "HEAD:" + RB], capture_output=True, cwd=BASE).stdout.decode("utf-8")
old = "`data/backups/lineage_t454_20261028_*.db` (sqlite copy, tạo TRƯỚC `--apply`)"
new = "`data/backups/lineage_t454_20261028_201150.db` (sqlite copy, tạo TRƯỚC `--apply`; 5 dila_id: PL000000013217, PL000000042180, PL000000042255, PL000000042305, PL000000055653)"
assert old in head, "không tìm thấy dòng backup T454 trong HEAD"
head = head.replace(old, new, 1)
out = os.path.join(BASE, "Dai_Tang_Kinh", "daoanh", "docs", "sessions", "2026-10-28-commit", "blobs", RB.replace("/", "__"))
with open(out, "w", encoding="utf-8", newline="") as f:
    f.write(head)
print("prepared new ROLLBACK.md blob (%d chars) -> %s" % (len(head), out))
