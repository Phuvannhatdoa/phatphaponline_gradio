# TESTER-REPORT-4 — T290 (M5 credits.html từ data_sources), vòng 4 (Xác nhận lại)

Ngày kiểm: 2026-11-01. Người kiểm: Tester (Claude Code, chỉ đọc). Không sửa code/task/status, không ghi DB, không git add/commit. Không ghi vào cây chính.
Worktree: `C:\Users\Nam Thien\.claude\worktrees\coder-t290\Dai_Tang_Kinh\daoanh`

## Kết luận

**PASS các mục kỹ thuật (1–5).** Mục 6 (done_when ACTIVE/REFERENCE) — Admin đã chốt giữ quy tắc hiện tại (2026-11-01): `active=1 AND integration_mode<>'BLOCKED'` (7 nguồn). Trang ghi rõ "chưa xác minh giấy phép" cho 6/7 nguồn. Task giữ `status: testing`. Chờ Admin xác nhận DONE.

## Bảng kết quả

| # | Mục kiểm | Kết quả |
|---|---|---|
| 1 | Test unittest/pytest (16/16) | PASS |
| 2 | `build_credits.py --check` qua API | PASS (16 nguồn, 7 đang dùng, 9 chặn) |
| 3 | Footer đồng bộ marker, không còn "lineage.db" | PASS |
| 4 | Phạm vi diff (chỉ credits.html, task file, scripts/tests mới) | PASS (có 2 ghi chú) |
| 5 |.done_when quy tắc ACTIVE/REFERENCE | ĐÃ CHỐT BỞI ADMIN (giữ quy tắc hiện tại) |
| 6 | Sửa 1–5 từ TESTER-REPORT trước | ĐẠT HẾT |

## Bằng chứng chi tiết

### 1. Test (PASS)
- `python -X utf8 tests/test_t290_credits_generator.py` → `16/16 PASS`
- `python -X utf8 -m pytest tests/test_t290_credits_generator.py -q` → `16 passed in 1.24s`

### 2. --check qua API (PASS)
Lệnh: `python -X utf8 scripts/build_credits.py --check --out credits.html --api http://127.0.0.1:5000/daoanh/api/admin/sources/list`
Output:
```
Dữ liệu: 16 nguồn · đang dùng 7 · chặn/chưa xác minh 9
PASS — credits.html khớp 16 dòng data_sources (mỗi nguồn đúng 1 mục).
```
exit 0. Marker trong trang: `t290:total=16 in_use=7 blocked=9 db=Source Hub API (đọc từ data_sources)`.

### 3. Footer và outcome (PASS)
- `grep "lineage.db" credits.html` → không có kết quả. Footer hiện ghi: "Sinh từ bảng `data_sources` ... Nguồn dữ liệu: Source Hub API (đọc từ data_sources). Số dòng SQL = số mục trên trang = 16."
- Outcome task ghi: "vòng 3 = 16/16 PASS" — khớp kết quả tester vòng 3.

### 4. Phạm vi diff (PASS, có 2 ghi chú)
- `git diff HEAD --name-only` (tracked): chỉ `credits.html` và `tasks/T290-m5-credits-tu-data-sources.md`. Đúng phạm vi.
- Untracked trong phạm vi task: `scripts/build_credits.py`, `tests/test_t290_credits_generator.py`, `docs/sessions/2026-11-01/T290-coder/CODER-REPORT.md`, `TESTER-REPORT.md`, `TESTER-REPORT-2.md`, `TESTER-REPORT-3.md`, file này.
- Ghi chú 1: `.opencode/agents/coder.md` untracked — không phải đầu ra coder (MA sao chép). Cần loại khỏi commit.
- Ghi chú 2: thư mục `docs/sessions/2026-11-01/T290-coder/backup/` có 8 file `*.bak-*` bị `.gitignore` bỏ qua. Nếu commit bằng `git add` thông thường, backup và điểm revert sẽ không đi kèm. Cần Admin/MA quyết cách lưu.

### 5. done_when — ĐÃ CHỐT BỞI ADMIN
- Quy tắc Admin (2026-11-01): **giữ quy tắc hiện tại** = `active=1 AND integration_mode<>'BLOCKED'` (7 nguồn). Không lọc theo `legal_status` vì DB chỉ có AUDITING/UNKNOWN/INTERNAL_USE.
- 6/7 nguồn đang dùng có `license_verified=0` → trang ghi "Chưa xác minh giấy phép" (badge warn + khối `note unverified`). Đúng yêu cầu "Mục chưa xác minh giấy phép ghi rõ".
- CBETA (`license_verified=1`) → hiển thị điều khoản CC-BY-NC-SA-4.0 trong khối `note term`. Đúng.
- **Admin đã quyết định quy tắc này** — tester không tự đánh đạt, chờ Admin xác nhận DONE.

### 6. Sửa 1–5 từ TESTER-REPORT trước — ĐẠT HẾT
- Sửa 1: `EDITORIAL_NOTES` sạch (không nêu giấy phép); `LICENSE_TERM_NOTES` chỉ render khi `license_verified=1` — **XONG**.
- Sửa 2: `--check` mở rộng (`NOTE_LIKE_RE`, `note_like_blocks`) bắt 4 dạng ghi chú cứng — **XONG**, test 2 case mới PASS.
- Sửa 3: Ghi rõ quy tắc lọc trong `outcome` — **XONG**.
- Sửa 4: Chạy lại test + `--check`, ghi output — **XONG**.
- Sửa 5: Mở rộng `--check` bắt mọi thẻ có class chứa "note" (trừ `note unverified`), kèm test — **XONG** (vòng 3).

## Việc còn lại (không do tester thực hiện)
1. **Admin xác nhận DONE** (task đã đạt mọi tiêu chí kỹ thuật).
2. Quyết cách lưu backup không bị `.gitignore` bỏ qua (ghi chú 2 mục 4).
3. Loại `.opencode/agents/coder.md` khỏi phạm vi commit (ghi chú 1 mục 4).