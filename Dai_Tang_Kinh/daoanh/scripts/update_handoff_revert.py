# -*- coding: utf-8 -*-
"""Cập nhật Handoff: lệnh revert 1 dòng cho Admin + trạng thái revert 9/9 (2 cách)."""
import os, sys

BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DAO = os.path.join(BASE, "Dai_Tang_Kinh", "daoanh")
os.chdir(DAO)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

P = "docs/Handoff-2026-10-29-n4-t454-t457-batch.md"
p = os.path.join(DAO, P.replace("/", os.sep))
t = open(p, encoding="utf-8").read()

old = """### 5.1 Revert 1 commit (độc lập)
Chuỗi N4 có 7 commit. Revert **ngược thứ tự** để sạch (đã verify 7/7 PASS):

```bash
cd <repo-root>   # visjs-app
git revert --no-commit d58ac475   # pipeline log + known-failing-gates
git revert --no-commit bdcf4fa4   # handoff tong chuoi N4
git revert --no-commit 873e7dcc   # fix UTF-16 logs -> UTF-8
git revert --no-commit 32e1d2d7   # tasktodo markers T454-T457
git revert --no-commit 8242fbd1   # ROLLBACK backup path fix
git revert --no-commit 38ffb5f4   # T456 status + ROLLBACK rows
git revert --no-commit a5d2ec25   # T455 - phan loai 794 dong
git revert --no-commit 2686da0a   # T457 - import DILA bio nexus
git revert --no-commit 01ee030f   # T454 - lam sach hau to
# kiểm tra: git diff --stat 01ee030f^  → phải RỖNG
```

**Kết quả verify (2026-10-29)**: sau cả **9** lệnh, `git diff --stat 01ee030f^` = **rỗng** ⇒ trạng thái khớp **chính xác** trạng thái trước chuỗi N4. Mỗi bước đều báo `REVERT OK`.

> ⚠️ **Revert theo thứ tự NGƯỢC** (mới → cũ) là bắt buộc. Revert từng commit riêng lẻ sẽ **conflict** vì các commit sau sửa cùng file (vd `873e7dcc` sửa file log của `2686da0a`/`a5d2ec25`; `8242fbd1` sửa `ROLLBACK.md` của `38ffb5f4`). Đã kiểm chứng bằng `scripts/verify_revert_seq.py` (worktree cô lập)."""

new = """### 5.1 ⭐ Revert CẢ CHUỖI — 1 LỆNH (khuyến nghị)

```bash
cd <repo-root>   # visjs-app
git revert --no-commit 01ee030f^..d73fbc7b
# kiểm tra: git diff --stat 01ee030f^  → phải RỖNG
```

**Đã kiểm chứng 2026-10-29**: `rc=0`, `git diff --stat 01ee030f^` = **RỖNG** ⇒ trạng thái sau revert khớp **chính xác** trạng thái trước chuỗi N4. Không cần xử lý conflict thủ công.

### 5.2 Revert từng commit (ngược thứ tự) — 9/9 PASS

```bash
git revert --no-commit d58ac475   # pipeline log + known-failing-gates
git revert --no-commit bdcf4fa4   # handoff tong chuoi N4
git revert --no-commit 873e7dcc   # fix UTF-16 logs -> UTF-8
git revert --no-commit 32e1d2d7   # tasktodo markers T454-T457
git revert --no-commit 8242fbd1   # ROLLBACK backup path fix
git revert --no-commit 38ffb5f4   # T456 status + ROLLBACK rows
git revert --no-commit a5d2ec25   # T455 - phan loai 794 dong
git revert --no-commit 2686da0a   # T457 - import DILA bio nexus
git revert --no-commit 01ee030f   # T454 - lam sach hau to
```

**Kết quả verify (2026-10-29)**: **9/9 PASS** (script tự gỡ conflict modify/delete cho 2 commit docs-only cuối).

> ⚠️ **Revert theo thứ tự NGƯỢC** (mới → cũ) là bắt buộc khi revert từng commit. Revert từng commit **đồng thời** sẽ conflict vì các commit sau sửa cùng file (`873e7dcc` sửa file log của `2686da0a`/`a5d2ec25`; `8242fbd1` sửa `ROLLBACK.md` của `38ffb5f4`; `d73fbc7b` sửa `verify_revert_seq.py` của `d58ac475`). Dùng **cách 5.1** (1 lệnh) là sạch nhất.
>
> Conflict modify/delete khi revert 1 commit: file bị commit đó ADD nhưng commit sau đã sửa → ý định revert là **xoá** file đó → `git rm --ignore-unmatch <path>` rồi `git add -A`."""

assert old in t, "khong khop §5.1"
t = t.replace(old, new, 1)

# đánh lại số mục 5.2 -> 5.3, 5.3 -> 5.4
t = t.replace("### 5.2 Revert code + DB cho từng task", "### 5.3 Revert code + DB cho từng task", 1)
t = t.replace("### 5.3 Script verify (không ghi worktree)", "### 5.4 Script verify (không ghi worktree)", 1)

old2 = """```bash
# AN TOÀN — chạy trong worktree cô lập, KHÔNG đụng worktree chính
python -X utf8 Dai_Tang_Kinh/daoanh/scripts/verify_revert_seq.py       # revert ngược thứ tự (9/9 PASS)
python -X utf8 Dai_Tang_Kinh/daoanh/scripts/verify_revert_worktree.py  # revert từng commit riêng lẻ (4/7 — 3 conflict, xem §5.1)
python -X utf8 Dai_Tang_Kinh/daoanh/scripts/verify_revert_safe.py      # git apply --check --cached (không ghi gì)
```"""
new2 = """```bash
# AN TOÀN — chạy trong worktree cô lập, KHÔNG đụng worktree chính
python -X utf8 Dai_Tang_Kinh/daoanh/scripts/verify_revert_seq.py       # A) range 1 lệnh PASS  +  B) từng commit 9/9 PASS
python -X utf8 Dai_Tang_Kinh/daoanh/scripts/verify_revert_worktree.py  # revert từng commit riêng lẻ (không auto-gỡ conflict)
python -X utf8 Dai_Tang_Kinh/daoanh/scripts/verify_revert_safe.py      # git apply --check --cached (không ghi gì)
```

Kết quả `verify_revert_seq.py` (2026-10-29):
```
A) git revert --no-commit 01ee030f^..d73fbc7b  →  rc=0
   diff vs trang thai truoc chuoi: RONG - khop chinh xac
B) revert tung commit: 9/9 PASS
```"""
assert old2 in t, "khong khop §5.4"
t = t.replace(old2, new2, 1)

# §2 thêm mục revert 1 lệnh
old3 = """### 3 việc Admin cần làm ngay"""
new3 = """### ⭐ Revert cả chuỗi N4 — 1 lệnh (đã kiểm chứng)
```bash
git revert --no-commit 01ee030f^..d73fbc7b
```
→ `rc=0`, `git diff --stat 01ee030f^` = **RỖNG** (khớp chính xác trạng thái trước N4).

### 3 việc Admin cần làm ngay"""
assert old3 in t, "khong khop §2"
t = t.replace(old3, new3, 1)

open(p, "w", encoding="utf-8", newline="").write(t)
print("Handoff updated: %d chars" % len(t))
print("co '1 LỆNH':", "1 LỆNH" in t)
print("co '9/9 PASS':", "9/9 PASS" in t)
