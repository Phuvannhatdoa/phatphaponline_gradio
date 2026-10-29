# -*- coding: utf-8 -*-
"""Cập nhật Handoff tổng: 9 commit, pipeline XANH, revert 9/9 PASS."""
import os, sys

BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DAO = os.path.join(BASE, "Dai_Tang_Kinh", "daoanh")
os.chdir(DAO)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

P = "docs/Handoff-2026-10-29-n4-t454-t457-batch.md"
p = os.path.join(DAO, P.replace("/", os.sep))
t = open(p, encoding="utf-8").read()
nl = "\r\n" if "\r\n" in t else "\n"

rep = [
    # §1 bảng đọc nhanh
    ("| **HEAD** | `873e7dcc9d7e60cb7d88bad60b6ceea937519aaa` |",
     "| **HEAD** | `d58ac4751020c9a2b24519729f756d1bac2c079e` |"),
    ("| **Commit mới** | 7 (xem §6) |",
     "| **Commit mới** | **9** (xem §6) |"),
    ("| **Pipeline** | Chưa chạy lại sau chuỗi này (cổng đỏ cũ vẫn vậy — xem §8) |",
     "| **Pipeline** | ✅ **XANH — exit 0** (`npm run pipeline`, 1.804 dòng log) |"),
    ("| **Test** | `git revert` cả 7 commit: **7/7 PASS** (§5) |",
     "| **Test** | `git revert` cả 9 commit: **9/9 PASS** (§5) · `dup:ids` **PASS** |"),

    # §2 phát hiện quan trọng
    ("""### Phát hiện quan trọng nhất
- **`LIKE '%_ Huý%'` là BẪY**: `_` trong SQL LIKE là wildcard 1 ký tự → trả về 2 dòng giả ("Ải Ngoan Trại", "Ải Ngoan Sỡ"). Phải dùng `LIKE '%\\_ Huý%' ESCAPE '\\'`. Script `scripts/t454_verify_state.py` đã xử lý.
- **3 file log bị UTF-16** do PowerShell redirect (`>` mặc định UTF-16LE) → git coi là **binary** → `git revert`/`git apply` fail. Đã commit `873e7dcc` chuyển sang UTF-8.""",
     """### Phát hiện quan trọng nhất
- 🎉 **`npm run pipeline` đã XANH (exit 0)** — 4 cổng đỏ trước phiên này đều đã gỡ: `audit:honesty` (ratchet 7/7) · `test:t200` (canonical A001984) · `audit:t166` (migration additive) · `test:gov` (18/18). Bằng chứng: `docs/sessions/2026-10-28-commit/pipeline.log`.
- **`LIKE '%_ Huý%'` là BẪY**: `_` trong SQL LIKE là wildcard 1 ký tự → trả về 2 dòng giả ("Ải Ngoan Trại", "Ải Ngoan Sỡ"). Phải dùng `LIKE '%\\_ Huý%' ESCAPE '\\'`. Script `scripts/t454_verify_state.py` đã xử lý.
- **3 file log bị UTF-16** do PowerShell redirect (`>` mặc định UTF-16LE) → git coi là **binary** → `git revert`/`git apply` fail. Đã commit `873e7dcc` chuyển sang UTF-8.
- **`git revert --no-commit` GHI VÀO WORKTREE** — dùng để "verify" đã xoá 24 file thật. Verify revert phải dùng **worktree cô lập** (`git worktree add --detach`). Chi tiết §7.2."""),

    # §5.1 lệnh revert
    ("""```bash
cd <repo-root>   # visjs-app
git revert --no-commit 873e7dcc   # fix UTF-16 logs -> UTF-8
git revert --no-commit 32e1d2d7   # tasktodo markers T454-T457
git revert --no-commit 8242fbd1   # ROLLBACK backup path fix
git revert --no-commit 38ffb5f4   # T456 status + ROLLBACK rows
git revert --no-commit a5d2ec25   # T455 - phan loai 794 dong
git revert --no-commit 2686da0a   # T457 - import DILA bio nexus
git revert --no-commit 01ee030f   # T454 - lam sach hau to
# kiểm tra: git diff --stat 01ee030f^  → phải RỖNG
```

**Kết quả verify**: sau cả 7 lệnh, `git diff --stat 01ee030f^` = **rỗng** ⇒ trạng thái khớp chính xác trạng thái trước chuỗi N4.""",
     """```bash
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

> ⚠️ **Revert theo thứ tự NGƯỢC** (mới → cũ) là bắt buộc. Revert từng commit riêng lẻ sẽ **conflict** vì các commit sau sửa cùng file (vd `873e7dcc` sửa file log của `2686da0a`/`a5d2ec25`; `8242fbd1` sửa `ROLLBACK.md` của `38ffb5f4`). Đã kiểm chứng bằng `scripts/verify_revert_seq.py` (worktree cô lập)."""),

    # §5.3 script verify
    ("""```bash
python -X utf8 Dai_Tang_Kinh/daoanh/scripts/verify_revert_worktree.py  # revert từng commit trong worktree cô lập
python -X utf8 Dai_Tang_Kinh/daoanh/scripts/verify_revert_seq.py       # revert theo thứ tự ngược
```""",
     """```bash
# AN TOÀN — chạy trong worktree cô lập, KHÔNG đụng worktree chính
python -X utf8 Dai_Tang_Kinh/daoanh/scripts/verify_revert_seq.py       # revert ngược thứ tự (9/9 PASS)
python -X utf8 Dai_Tang_Kinh/daoanh/scripts/verify_revert_worktree.py  # revert từng commit riêng lẻ (4/7 — 3 conflict, xem §5.1)
python -X utf8 Dai_Tang_Kinh/daoanh/scripts/verify_revert_safe.py      # git apply --check --cached (không ghi gì)
```

> ⛔ **KHÔNG chạy `git revert --no-commit` trong worktree chính để "test"** — nó **ghi thật** vào worktree (đã xoá 24 file, xem §7.2)."""),

    # §6 commit table
    ("""### Commit (7)
| SHA | Nội dung | Số file |
|---|---|---|
| `873e7dcc` | fix: 3 file log UTF-16 → UTF-8 (git binary patch) | 3 M |""",
     """### Commit (9)
| SHA | Nội dung | Số file |
|---|---|---|
| `d58ac475` | docs: pipeline log (1.804 dòng) + `known-failing-gates.md` cập nhật + 17 script helper | 18 (1 M + 17 A) |
| `bdcf4fa4` | docs: Handoff tổng chuỗi N4 (10 mục §15) | 1 A |
| `873e7dcc` | fix: 3 file log UTF-16 → UTF-8 (git binary patch) | 3 M |"""),

    # §8 cổng đỏ
    ("""### Cổng đỏ còn lại (theo `docs/known-failing-gates.md`)
- `audit:honesty:strict` — 5/7 FAIL (H1 41 / H2 96 / H3 969 / H4 745 / H5 55) — đã có **ratchet** chặn vi phạm mới (`997565ae`)
- `test:translation` — dừng ở `test:t200` (đã gỡ bằng `9d8a1e0c`)
- `audit:t166` — DB thiếu 4 cột `translation_cache`/`translation_rules` + index `idx_tc_identity` (migration đã apply ở `989ccfc4` — cần verify lại vì DB đã đổi)
- `test:gov` — đã gỡ ở `b71a68b0`""",
     """### Cổng đỏ — **đã gỡ hết khỏi pipeline** (đo 2026-10-29, `npm run pipeline` exit 0)
| Cổng | Trước | Sau | Commit gỡ |
|---|---|---|---|
| `audit:honesty` | đỏ (5/7 FAIL) | ✅ PASS (ratchet) 7/7 — không vi phạm MỚI | `997565ae` |
| `test:translation` → `test:t200` | đỏ (1/25 FAIL) | ✅ PASS 25/25 | `9d8a1e0c` |
| `audit:t166` | đỏ (thiếu 4 cột + index) | ✅ PASS — schema đủ, app guard đầy đủ | `989ccfc4` |
| `test:gov` | đỏ | ✅ PASS 18/18 | `b71a68b0` |
| `dup:ids` | đỏ (T432/T433/T434 trùng) | ✅ PASS — không có ID trùng thật | `f2958353` |

### Cổng CỨNG còn đỏ (không nằm trong pipeline mặc định)
- `audit:honesty:strict` — 5/7 FAIL (H1 41 / H2 96 / H3 969 / H4 745 / H5 55). Chỉ bật khi phát hành / đánh giá dữ liệu (`npm run audit:honesty:strict`). Tiêu chí gỡ: strict exit 0 **hoặc** Admin ký policy ngưỡng từng H."""),

    # §9 lệnh kiểm tra
    ("""# 5. Verify revert 7/7 (KHÔNG ghi worktree chính)
python -X utf8 Dai_Tang_Kinh/daoanh/scripts/verify_revert_seq.py

# 6. Task ID trùng (phải PASS)
npm run dup:ids
```""",
     """# 5. Verify revert 9/9 (KHÔNG ghi worktree chính)
python -X utf8 Dai_Tang_Kinh/daoanh/scripts/verify_revert_seq.py

# 6. Task ID trùng (phải PASS)
npm.cmd run dup:ids

# 7. Pipeline (phải exit 0)
npm.cmd run pipeline
```

> ⚠️ Dùng **`npm.cmd`** (không phải `npm`) — shim `npm` của PowerShell hỏng, in ra rỗng."""),

    # §7 sai lầm thêm
    ("""| 9 | Commit dựa trên `expect = "A\\t"+path` | So sánh fail khi file đã track → `M` | So sánh theo **tên file** (`split("\\t",1)[1]`), không theo status letter |""",
     """| 9 | Commit dựa trên `expect = "A\\t"+path` | So sánh fail khi file đã track → `M` | So sánh theo **tên file** (`split("\\t",1)[1]`), không theo status letter |
| 10 | `npm run dup:ids` FAIL vì thư mục `docs/sessions/2026-10-28-commit/blobs/` chứa bản sao task file | Cổng đỏ (false) | Không lưu bản sao file task trong `docs/`; staging blob đặt ngoài repo hoặc xoá sau khi commit |
| 11 | `npm run <script>` in ra rỗng | Tưởng script không chạy | Shim `npm` của PowerShell hỏng → dùng **`npm.cmd`** |
| 12 | `npm run pipeline > log 2>&1` (PowerShell) | Log ra **UTF-16** → git binary | Dùng `scripts/run_pipeline_log.py` (subprocess + ghi UTF-8) |"""),
]

for old, new in rep:
    if old not in t:
        print("!! KHONG khop:", old[:70].replace("\n", " "))
        continue
    t = t.replace(old, new, 1)

open(p, "w", encoding="utf-8", newline="").write(t)
print("Handoff updated: %d chars" % len(t))
print("co '9/9 PASS':", "9/9 PASS" in t)
print("co 'XANH':", "XANH" in t)
