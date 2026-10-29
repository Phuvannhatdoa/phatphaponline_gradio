# -*- coding: utf-8 -*-
"""Cập nhật Handoff: HEAD cuối + số commit cuối cùng + range revert động."""
import os, sys

BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DAO = os.path.join(BASE, "Dai_Tang_Kinh", "daoanh")
os.chdir(DAO)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

P = "docs/Handoff-2026-10-29-n4-t454-t457-batch.md"
p = os.path.join(DAO, P.replace("/", os.sep))
t = open(p, encoding="utf-8").read()

rep = [
    ("| **HEAD** | `d58ac4751020c9a2b24519729f756d1bac2c079e` |",
     "| **HEAD** | `828ae63f1172c6c7d73a901517a6144995ebc952` |"),
    ("| **Commit mới** | **9** (xem §6) |",
     "| **Commit mới** | **13** (xem §6) |"),
    ("| **Test** | `git revert` cả 9 commit: **9/9 PASS** (§5) · `dup:ids` **PASS** |",
     "| **Test** | `git revert` cả 13 commit: **A) 1 lệnh PASS** + **B) từng commit 9/9 PASS** (§5) · `dup:ids` **PASS** · `pipeline` **exit 0** |"),
    ("""```bash
cd <repo-root>   # visjs-app
git revert --no-commit 01ee030f^..d73fbc7b
# kiểm tra: git diff --stat 01ee030f^  → phải RỖNG
```""",
     """```bash
cd <repo-root>   # visjs-app
git revert --no-commit 01ee030f^..828ae63f   # ← thay SHA cuối bằng HEAD hiện tại
# kiểm tra: git diff --stat 01ee030f^  → phải RỖNG
```"""),
    ("""```
A) git revert --no-commit 01ee030f^..d73fbc7b  →  rc=0
   diff vs trang thai truoc chuoi: RONG - khop chinh xac
B) revert tung commit: 9/9 PASS
```""",
     """```
A) git revert --no-commit 01ee030f^..828ae63f  →  rc=0
   diff vs trang thai truoc chuoi: RONG - khop chinh xac
B) revert tung commit: 9/9 PASS
```

> Script tự tính HEAD động (`git rev-parse HEAD`) → dùng được sau mọi commit mới, không cần sửa SHA trong code."""),
    ("""### Commit (9)
| SHA | Nội dung | Số file |
|---|---|---|
| `d58ac475` |""",
     """### Commit (13)
| SHA | Nội dung | Số file |
|---|---|---|
| `828ae63f` | feat(T455): script apply tên người (backup + apply/revert, **CHƯA chạy**) + 12 file patch revert làm bằng chứng | 14 A |
| `2d5682bc` | docs: lệnh revert 1 dòng cho cả chuỗi + verify 2 cách | 2 M + 2 A |
| `d73fbc7b` | docs: Handoff cập nhật (9 commit, pipeline XANH) | 2 M + 1 A |
| `d58ac475` |"""),
]

for old, new in rep:
    if old not in t:
        print("!! KHONG khop:", old[:60].replace("\n", " "))
        continue
    t = t.replace(old, new, 1)

open(p, "w", encoding="utf-8", newline="").write(t)
print("Handoff updated: %d chars" % len(t))
