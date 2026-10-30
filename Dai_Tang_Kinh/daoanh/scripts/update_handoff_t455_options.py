# -*- coding: utf-8 -*-
"""Cập nhật Handoff-2026-10-29: thêm phần T455 (3 phương án) + Admin xác nhận DONE T453/T454/T457."""
import os, re, sys

BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
os.chdir(BASE)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = os.path.join(BASE, "Dai_Tang_Kinh", "daoanh", "docs", "Handoff-2026-10-29-n4-t454-t457-batch.md")

t = open(P, encoding="utf-8").read()

# 1) §2 — 3 việc Admin: cập nhật trạng thái 2 & 3 đã OK
old = """### 3 việc Admin cần làm ngay
| # | Việc | Cần gì |
|---|---|---|
| 1 | **Duyệt lô T455** (A=24 sửa tên / B=534 giữ + ghi alias / C=236 sửa chính tả) | Mẫu 20 dòng/lô trong `docs/sessions/2026-10-28-t455/name_vi_mismatch_{A,B,C}.csv` + Q3b (thứ tự lô) + Q3c (duyệt bảng lịch sử `people_name_vi_history` không) |
| 2 | **Xác nhận DONE** T454 + T457 (mình đã ghi task file là `status: done`) | Admin xác nhận thì giữ nguyên; muốn đổi thì báo, mình sửa lại |
| 3 | **Xác nhận T453 DONE** (đã nạp đủ 5.747 bộ từ 2026-10-26, vẫn ghi "chờ Admin xác nhận") | Task file `tasks/T453-dila-catalog-a-import-vi.md` |"""
new = """### 3 việc Admin cần làm ngay
| # | Việc | Cần gì | Trạng thái |
|---|---|---|---|
| 1 | **Chọn phương án T455** (A / B / C) | Báo cáo đầy đủ: `docs/reports/T455-analysis-794-mismatch.md` — 3 phương án kèm số đo đo được | ⏳ **CHỜ** |
| 2 | **Xác nhận DONE** T454 + T457 | Admin xác nhận thì giữ nguyên; muốn đổi thì báo, mình sửa lại | ✅ **OK (2026-10-30)** — đã ghi vào task file + tasktodo |
| 3 | **Xác nhận T453 DONE** (đã nạp đủ 5.747 bộ từ 2026-10-26) | Task file `tasks/T453-dila-catalog-a-import-vi.md` | ✅ **OK (2026-10-30)** — task file đã `status: done`; marker tasktodo đã đổi sang DONE |"""
assert old in t, "khong khop §2 3 viec"
t = t.replace(old, new, 1)

# 2) thêm mục T455 3 phuong an vao §3
old3 = """### T456 — autocomplete ô Search HOME
Chưa bắt đầu. Phụ thuộc `depends_on: [T453, T416, T450]`. Thứ tự N4: T454 ✅ → T457 ✅ → T455 (đang) → T456."""
new3 = """### T455 — 3 phương án để Admin chọn (2026-10-30, đã có bằng chứng đo được)

Báo cáo đầy đủ: **`docs/reports/T455-analysis-794-mismatch.md`**

| Lô | Số | Bản chất | Tự quyết được? |
|---|---|---|---|
| **A** | 24 | ZQ hỏng rõ: để tên Anh (`Amoghavajra`) hoặc để nguyên chữ Hán hiến (`昰 竑 玘 霰 丏 讕` — không có trong `hanviet_char_map`) → 17/24 còn sót Hán | ✅ tra từ điển |
| **B** | 534 | **Không phải lỗi kỹ thuật** mà là khác *quy ước đọc cả từ*: ZQ đọc theo nghĩa chữ (`Long Thụ`, `Bàn Nhược`, `Vô Trứ`) vs Cloud theo cách gọi quen thuộc VN (`Long Thọ`, `Bát Nhã`, `Vô Trước`). 478/534 sai ≤ 1 từ · 64/534 chỉ khác gạch nối · **0/534** sót Hán | ⚠️ **không** — charmap không phân định được (269 ZQ / 314 Cloud / 113 hòa) |
| **C** | 236 | ZQ thiếu/sai 1 chữ, hay thiếu tiền tố tôn kính `釋` (Thích) → charmap dự án xác nhận **Cloud 188/236 (80 %)** | ✅ có bằng chứng máy |

- **(A) Khuyến nghị** — sửa **260 dòng** (lô A 24 + lô C 236), giữ 534 dòng lô B và ghi chú alias. Lô B mở task riêng, làm dần theo `so_lan`.
- **(B)** — sửa cả **794** theo Cloud. Đồng bộ hết nhưng Cloud cũng có lỗi riêng (`實叉難陀` → "Thật" thay vì "Thực") và là bản dịch unreviewed.
- **(C)** — sửa lô A + C theo Cloud, lô B tra từ điển theo lô `so_lan` (ưu tiên ~50 người xuất hiện ≥ 20 lần). Chính xác nhất nhưng chậm.

Script đo: `scripts/t455_examples.py` · `scripts/t455_diff_analysis.py` · `scripts/t455_charmap_check.py` · `scripts/t455_polyphonic_check.py`

### T456 — autocomplete ô Search HOME
Chưa bắt đầu. Phụ thuộc `depends_on: [T453, T416, T450]`. Thứ tự N4: T454 ✅ → T457 ✅ → T455 (chờ chọn phương án) → T456."""
assert old3 in t, "khong khop §3 T456"
t = t.replace(old3, new3, 1)

# 3) them canh bao trong §4 ve staging blob
old4 = """### 4.5 Đường dẫn"""
new4 = """### 4.5 Staging blob KHÔNG được đặt trong `docs/`
- Đặt bản sao file task trong `docs/sessions/<ngày>/blobs/` ⇒ `npm run dup:ids` **FAIL** (quét `docs/**/*.md`, thấy 2 file cùng `id:`).
- Đã xảy ra 2 lần. Cách đúng: staging blob để **ngoài repo** (`%TEMP%`) hoặc **xoá ngay sau khi commit**.
- Kiểm tra trước khi commit: `npm.cmd run dup:ids`.

### 4.6 Đường dẫn"""
assert old4 in t, "khong khop §4.5"
t = t.replace(old4, new4, 1)

open(P, "w", encoding="utf-8", newline="").write(t)
print("Handoff updated: %d chars" % len(t))
print("co '3 phuong an':", "3 phương án" in t)
print("co 'OK (2026-10-30)':", "OK (2026-10-30)" in t)
