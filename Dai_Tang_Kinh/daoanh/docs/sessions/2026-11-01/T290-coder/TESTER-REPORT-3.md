# TESTER-REPORT-3 — T290 (M5 credits.html từ data_sources), vòng 3

Ngày kiểm: 2026-11-01. Người kiểm: Tester (Claude Code, chỉ đọc). Không sửa code/task/status, không ghi DB, không git add/commit. Không ghi vào cây chính.
Worktree: `C:\Users\Nam Thien\.claude\worktrees\coder-t290\Dai_Tang_Kinh\daoanh`
Lệnh chạy với `PYTHONDONTWRITEBYTECODE=1` / `-B` để không sinh `__pycache__` mới.

## Kết luận

**PASS các mục kỹ thuật (1–5).** Mục 6 (done_when ACTIVE/REFERENCE) vẫn CHƯA ĐẠT, chờ Admin chốt quy tắc lọc; tester không tự đánh đạt.
Task giữ `status: testing`. Không đánh DONE thay Admin.

## Bảng kết quả

| # | Mục kiểm | Kết quả |
|---|---|---|
| 1 | Sửa 5: --check bắt 4 dạng ghi chú cứng (trên bản sao tạm) | PASS (4/4 bị báo lỗi) |
| 2 | Test: unittest-style và pytest | PASS (16/16 và 16 passed) |
| 3 | `build_credits.py --check` qua API | PASS (16 nguồn, 7 đang dùng, 9 chặn) |
| 4 | Footer "lineage.db" và số test trong outcome | PASS (footer đã sửa; outcome ghi 16/16 ở vòng 3) |
| 5 | Phạm vi diff | PASS, có 2 ghi chú (xem dưới) |
| 6 | done_when: quy tắc ACTIVE/REFERENCE | CHƯA ĐẠT, chờ Admin (không tự đánh) |

## Bằng chứng chi tiết

### 1. Sửa 5 — 4 dạng ghi chú cứng (PASS)
Cách làm: copy `credits.html` sang scratchpad, chèn ngay sau `data-source-code="DILA">` (DILA có `license_verified=0`), rồi chạy `--check --out <bản sao> --api ...`. File gốc không bị sửa.

| Dạng chèn | exit | Kết quả |
|---|---|---|
| Baseline (không chèn) | 0 | PASS |
| A. `<div class="note term">Bản phái sinh phải cùng giấy phép chia sẻ tương tự.</div>` | 1 | FAIL: "Nguồn DILA: ... ghi chú ... nêu điều khoản (giấy phép, share-alike)" |
| B. `<p class="note">Theo CC BY-SA 3.0, phải ghi nguồn.</p>` | 1 | FAIL: "... nêu điều khoản (mã CC)" |
| C. `<span class="note">Theo CC BY-SA 3.0, phải ghi nguồn.</span>` | 1 | FAIL: "... nêu điều khoản (mã CC)" |
| D. `<div class="foo note">Bản phái sinh phải cùng giấy phép chia sẻ tương tự.</div>` | 1 | FAIL: "... nêu điều khoản (giấy phép, share-alike)" |

Ghi chú: test `test_check_page_flags_hardcoded_license_note_p_tag` và `..._term_class` cũng bao phủ dạng A và B.
Script kiểm tạm: `C:\Users\NAMTHI~1\AppData\Local\Temp\claude\E--Backup-2025-QuaiTieuTu-Anan-Son-phatphaponline-gradio-truyenthua-visjs-app-Dai-Tang-Kinh\9adb5cd6-c0d7-4b8f-8cc8-b665559fabe2\scratchpad\t290_variants.py`.

### 2. Test (PASS)
- `python -X utf8 tests/test_t290_credits_generator.py` → `16/16 PASS` (gồm `test_check_page_flags_hardcoded_license_note`, `_term_class`, `_p_tag`).
- `python -X utf8 -m pytest tests/test_t290_credits_generator.py -q` → `16 passed in 1.07s`.

### 3. --check qua API (PASS)
Lệnh: `python -X utf8 scripts/build_credits.py --check --out credits.html --api http://127.0.0.1:5000/daoanh/api/admin/sources/list`
Output rút gọn:
```
Dữ liệu: 16 nguồn · đang dùng 7 · chặn/chưa xác minh 9
PASS — credits.html khớp 16 dòng data_sources (mỗi nguồn đúng 1 mục).
```
exit 0. Marker trong trang: `t290:total=16 in_use=7 blocked=9 db=Source Hub API (đọc từ data_sources)`.

### 4. Footer và outcome (PASS)
- `grep "lineage.db" credits.html` → không có kết quả. Footer hiện ghi nguồn là Source Hub API, khớp dòng 132 và marker.
- Outcome (`tasks/T290-...md`) ghi: "10/10 PASS ban đầu; vòng 2 = 14/14 PASS; vòng 3 = 16/16 PASS". Số vòng 3 khớp kết quả tester (16/16). Mục "Bước 4" ghi `16/16 test PASS`.

### 5. Phạm vi diff (PASS, có 2 ghi chú)
- `git diff HEAD --name-only` (tracked): chỉ `credits.html` và `tasks/T290-m5-credits-tu-data-sources.md`. Đúng phạm vi.
- Untracked trong phạm vi: `scripts/build_credits.py`, `tests/test_t290_credits_generator.py`, `docs/sessions/2026-11-01/T290-coder/CODER-REPORT.md`, `TESTER-REPORT.md`, `TESTER-REPORT-2.md` (và file này).
- Ghi chú 1 (ngoài phạm vi, không do coder tạo): `.opencode/agents/coder.md` là untracked; coder đã nêu trong mục "Sửa sau tester". Cần loại khỏi commit.
- Ghi chú 2 (chưa xử lý từ vòng 2): thư mục `docs/sessions/2026-11-01/T290-coder/backup/` có 8 file `*.bak-*` bị `.gitignore` dòng 40 bỏ qua (`git check-ignore` xác nhận). Nếu commit bằng `git add` thông thường, backup và điểm revert sẽ không đi kèm. Cần Admin/MA quyết cách lưu.
- `__pycache__` (`scripts/`, `tests/`) đã có sẵn từ các lần chạy trước, bị ignore (`!!`), không ảnh hưởng diff.

### 6. done_when — CHƯA ĐẠT, chờ Admin (không tự đánh)
- `done_when`: "liệt kê mọi nguồn ACTIVE/REFERENCE đúng giấy phép từ DB".
- DB trong worktree là 0 byte; dữ liệu lấy qua API. Quy tắc đang dùng: `active=1 AND integration_mode<>'BLOCKED'` → 7 nguồn. Không có nguồn nào có `legal_status` = ACTIVE hoặc REFERENCE_ONLY (theo báo cáo tester lần 2).
- 6/7 nguồn đang dùng còn `license_verified=0`, nên "đúng giấy phép" chưa được xác nhận cho các nguồn này.
- Admin phải chốt quy tắc lọc, và quyết định có điền `license_spdx`/`license_verified` trong DB hay không (việc ngoài T290, không làm trong tester này).

## Việc còn lại (không do tester thực hiện)
1. Admin chốt quy tắc lọc ACTIVE/REFERENCE (done_when mục 6).
2. Quyết cách lưu backup không bị `.gitignore` bỏ qua (ghi chú 2 ở mục 5).
3. Loại `.opencode/agents/coder.md` khỏi phạm vi commit (ghi chú 1 ở mục 5).
4. Admin xác nhận DONE. Tester không đánh DONE.
