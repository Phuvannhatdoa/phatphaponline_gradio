# TESTER-REPORT-2 — T290 (M5 credits.html từ data_sources), vòng 2

Ngày kiểm: 2026-11-01. Người kiểm: Tester (Claude Code, chỉ đọc). Không sửa code/task/status, không ghi DB, không git add/commit.
Worktree: `C:\Users\Nam Thien\.claude\worktrees\coder-t290\Dai_Tang_Kinh\daoanh`

## Kết luận

**FAIL (chưa đạt).** Mục 1, 3, 4 PASS. Mục 2 FAIL một phần: `--check` chỉ bắt ghi chú cứng dạng `<div class="note">`, bỏ lọt hai dạng khác đã thử. Mục 5 (quy tắc ACTIVE/REFERENCE) là điểm chờ Admin, tester không tự đánh đạt. Task giữ `status: testing`, không đánh DONE.

## Bảng kết quả

| # | Mục kiểm | Kết quả |
|---|---|---|
| 1 | Sửa 1: bỏ điều khoản cứng DILA trong EDITORIAL_NOTES | PASS |
| 2 | Sửa 2: --check báo lỗi ghi chú cứng nêu giấy phép cho nguồn license_verified=0, có test | FAIL (một phần, xem dưới) |
| 3 | Sửa 3: ghi rõ cách lọc trong outcome, không đổi quy tắc | PASS (select_groups không đổi so với bản fix1) |
| 4 | Sửa 4: chạy lại test và --check, ghi output | PASS |
| 5 | Khớp credits.html: mỗi nguồn 1 mục, "chưa xác minh", không điều khoản cứng DILA | PASS (mục khớp); phần ACTIVE/REFERENCE chờ Admin |
| 6 | Phạm vi diff | PASS, có 2 lưu ý (xem mục Phạm vi) |
| 7 | done_when: ACTIVE/REFERENCE | CHƯA ĐẠT, chờ Admin chốt (không tự đánh) |

## Chi tiết bằng chứng

### Sửa 1 — PASS
- `scripts/build_credits.py` dòng 60–73: `EDITORIAL_NOTES` không còn từ khóa giấy phép. Điều khoản tách sang `LICENSE_TERM_NOTES` (dòng 78–82), chỉ render khi `license_verified=1` (dòng 287–291).
- `credits.html`: `grep -c "chia sẻ tương tự"` = 0; `grep -c 'class="note term"'` = 1 (chỉ CBETA, verified=1).
- Thẻ DILA hiện: badge "Chưa xác minh giấy phép", note mô tả vai trò, và khối "Giấy phép chưa xác minh trong DB (license_verified=0)".
- Test `test_editorial_notes_have_no_license_terms`, `test_unverified_source_shows_no_license_term_note`: PASS.

### Sửa 2 — FAIL (một phần)
- Mã kiểm: `scripts/build_credits.py` dòng 97–98 `NOTE_BLOCK_RE = <div class="note">(.*?)</div>`. `check_page` (dòng 446–462) chỉ soi các khối này.
- Thử nghiệm tester (chèn vào thẻ DILA trong credits.html hiện tại, không ghi file, chỉ chạy `check_page` trên chuỗi trong bộ nhớ, bản gốc baseline = []):
  - A. `<div class="note term">Bản phái sinh phải cùng giấy phép chia sẻ tương tự.</div>` → kết quả `[]` (KHÔNG bị bắt).
  - B. `<p class="note">Theo CC BY-SA 3.0, phải ghi nguồn.</p>` → kết quả `[]` (KHÔNG bị bắt).
  - Chỉ dạng `<div class="note">` (test `test_check_page_flags_hardcoded_license_note`) mới bị bắt.
- Yêu cầu tester lần 1: "--check báo lỗi nếu ghi chú cứng nêu giấy phép cho nguồn license_verified=0". Hiện chưa đủ: một ghi chú cứng dùng class khác hoặc thẻ khác vẫn lọt.
- Gợi ý sửa (không tự sửa): soi toàn bộ đoạn thẻ (`card_segment`) trừ khối `class="note unverified"` và khối cảnh báo chuẩn, thay vì chỉ `<div class="note">`; thêm test cho dạng A và B.

### Sửa 3 — PASS
- Outcome ghi rõ: "đang dùng" = `active=1 AND integration_mode<>'BLOCKED'`, và lý do không lọc theo `legal_status`.
- So sánh `select_groups()` với `docs/sessions/2026-11-01/T290-coder/backup/build_credits.py.bak-before-coder-fix1`: giống hệt, không đổi quy tắc.

### Sửa 4 — PASS
- `python -X utf8 tests/test_t290_credits_generator.py` → `14/14 PASS` (cả 14 test, gồm 4 test mới).
- `python -X utf8 -m pytest tests/test_t290_credits_generator.py -q` → `14 passed in 0.86s`.
- `python -X utf8 scripts/build_credits.py --check --out credits.html --api http://127.0.0.1:5000/daoanh/api/admin/sources/list` → `Dữ liệu: 16 nguồn · đang dùng 7 · chặn/chưa xác minh 9` / `PASS — credits.html khớp 16 dòng data_sources (mỗi nguồn đúng 1 mục).` exit 0.
- `--check` không kèm `--api` hoặc `--db` báo `LỖI: không tìm thấy lineage.db thật` (đúng, vì DB trong worktree là 0 byte).
- Lưu ý: 14 test chỉ là một cách kiểm; outcome vẫn ghi `10/10 PASS` ở mục "Bước 4" của task (dòng bị sót khi cập nhật, cần sửa cho khớp 14/14).

### Mục 5 — khớp credits.html (PASS, có ghi chú)
- Bảng API (`GET /daoanh/api/admin/sources/list`, chỉ đọc) so với credits.html: 16 nguồn, mỗi `data-source-code` đúng 1 lần (16 mã: 84000, BDRC, CBETA, CHGIS, DILA, DILA_CATALOG, FoJin, Kanripo, MARCUS, SAT, SuttaCentral, TGAZ, TTL_LOCAL, Wikidata, ZENLINEAGE, ZQLOCAL).
- Đang dùng (7): DILA, CBETA, MARCUS, ZQLOCAL, Wikidata, ZENLINEAGE, TTL_LOCAL. Khớp rule.
- Chưa xác minh (license_verified=0) trong nhóm đang dùng: 6 nguồn (DILA, MARCUS, ZQLOCAL, Wikidata, ZENLINEAGE, TTL_LOCAL). Tất cả ghi "Chưa xác minh giấy phép". CBETA (verified=1) ghi `CC-BY-NC-SA-4.0`.
- Marker: `<!-- t290:total=16 in_use=7 blocked=9 ... -->`, khớp.
- Lưu ý còn lại (không thuộc 1–4, coder đã tự nêu là "chưa sửa"): footer dòng 130 ghi "Sinh từ data_sources trong lineage.db" trong khi dòng 132 và marker ghi nguồn là "Source Hub API". Mâu thuẫn nhỏ, cần sửa hoặc để Admin quyết.

### Mục 7 — done_when (CHƯA ĐẠT, chờ Admin)
- `done_when`: "liệt kê mọi nguồn ACTIVE/REFERENCE đúng giấy phép".
- Trong DB hiện có: legal_status = UNKNOWN 8, AUDITING 7, INTERNAL_USE 1; integration_mode = BLOCKED 9, INGEST 6, local_dump 1. KHÔNG có giá trị ACTIVE hay REFERENCE_ONLY trong `legal_status`.
- Quy tắc coder đang dùng (`active=1 AND integration_mode<>'BLOCKED'`) cho 7 nguồn "đang dùng". Nếu Admin muốn lọc theo cột khác, chỉ cần sửa `select_groups()`.
- Tester không đánh đạt điều kiện này. Admin phải chốt quy tắc lọc trước khi xác nhận DONE.

## Phạm vi diff (git status / git diff HEAD, chỉ đọc)

- Tracked đổi: `credits.html`, `tasks/T290-m5-credits-tu-data-sources.md`. Đúng phạm vi.
- Untracked, phần việc của coder: `scripts/build_credits.py`, `tests/test_t290_credits_generator.py`, `docs/sessions/2026-11-01/T290-coder/CODER-REPORT.md`, `docs/sessions/2026-11-01/T290-coder/TESTER-REPORT.md`, `docs/sessions/2026-11-01/T290-coder/TESTER-REPORT-2.md` (file này).
- Untracked ngoài phạm vi: `.opencode/agents/coder.md` (MA sao chép, coder không tạo; tester lần 1 đã nêu).
- Lưu ý 1: thư mục backup `docs/sessions/2026-11-01/T290-coder/backup/` bị `.gitignore` dòng 40 (`*.bak-*`) bỏ qua. Nếu commit theo `git add` thông thường, các bản sao lưu sẽ KHÔNG đi kèm, và lệnh revert trong task mất điểm tựa. Cần Admin/MA quyết cách lưu backup.
- Lưu ý 2: lần chạy test và --check của tester tạo `scripts/__pycache__/` và `tests/__pycache__/`. Đây là thư mục bị ignore (`!!`), không ảnh hưởng diff, nhưng đã được tạo bởi tester.
- Không có thay đổi nào trong DB; không có thay đổi giấy phép.

## Việc còn lại cho coder (không tự sửa ở đây)

1. Mở rộng `check_page` để bắt ghi chú cứng nêu giấy phép ở mọi dạng (`class` khác, thẻ `<p>`), và thêm test cho dạng A và B nêu ở trên.
2. Sửa dòng "10/10 PASS" trong mục Bước 4 của task thành số đúng (14/14).
3. Đồng bộ footer "lineage.db" với nguồn thực tế (Source Hub API) hoặc ghi rõ lý do.
4. Quyết định cách lưu backup không bị `.gitignore` bỏ qua (xem Lưu ý 1).

## Việc chờ Admin

- Chốt quy tắc lọc "ACTIVE/REFERENCE" (done_when mục 5).
- Điền `license_spdx` + `license_verified` trong DB nếu muốn trang nêu điều khoản cho 6 nguồn đang dùng chưa xác minh (việc khác task, T290 không ghi DB).
- Xác nhận DONE. Tester không đánh DONE thay Admin.
