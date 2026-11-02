# TESTER-REPORT — T290 (M5 credits.html từ data_sources)

Ngày kiểm: 2026-11-01. Người kiểm: Tester (Claude Code, chỉ đọc). Không sửa code/task/status, không ghi DB, không git add/commit.
Worktree: `C:\Users\Nam Thien\.claude\worktrees\coder-t290\Dai_Tang_Kinh\daoanh`

## Kết luận tổng

**FAIL (chưa đạt để chuyển Admin xác nhận).** Kỹ thuật (đếm, test, --check) đều PASS. Hai điểm chưa đạt:
1. Điều kiện done_when "ACTIVE/REFERENCE" không áp được theo nghĩa chữ với dữ liệu DB hiện tại (cần Admin chốt quy tắc).
2. Ghi chú biên tập cứng trong `build_credits.py` (EDITORIAL_NOTES, nguồn DILA) khẳng định điều khoản "cùng giấy phép chia sẻ tương tự" trong khi DILA có `license_verified=0`. Vi phạm nguyên tắc "không khẳng định điều khoản chưa xác minh", và `--check` không bắt được lỗi này.

Admin chưa xác nhận DONE. Task vẫn ở trạng thái `testing`.

## Bảng kết quả từng mục

| # | Mục kiểm | Kết quả |
|---|---|---|
| 1 | Phạm vi thay đổi (git diff so với HEAD) | PASS, có 1 lưu ý (xem mục 1 bên dưới) |
| 2 | build_credits.py chỉ đọc DB | PASS |
| 3 | Test `tests/test_t290_credits_generator.py` (unittest + pytest) | PASS 10/10 |
| 4 | `--check` | PASS khi dùng `--api` (16 = 7 + 9). Không có DB thật nên không kiểm được với DB thật |
| 5 | Đối chiếu số nguồn, mỗi nguồn 1 mục, "chưa xác minh" | Đếm PASS; ghi "chưa xác minh" PASS; nội dung ghi chú DILA FAIL |
| 6 | done_when: credits.html liệt kê mọi nguồn ACTIVE/REFERENCE đúng giấy phép | CHƯA ĐẠT / cần Admin chốt quy tắc (xem mục 6) |

## Chi tiết bằng chứng

### 1. Phạm vi
Lệnh: `git status --short --untracked-files=all`
```
 M credits.html
 M tasks/T290-m5-credits-tu-data-sources.md
?? .opencode/agents/coder.md
?? docs/sessions/2026-11-01/T290-coder/CODER-REPORT.md
?? scripts/build_credits.py
?? tests/test_t290_credits_generator.py
```
- Tracked đổi: `credits.html`, file task T290 (diff 2 file: 130 insert, 67 delete). Task vẫn `status: testing`, không thấy coder đánh DONE.
- Lưu ý: `.opencode/agents/coder.md` là file untracked không nằm trong danh sách coder khai báo. Timestamp 17:32 cùng thời điểm với file DB placeholder. Chưa rõ coder tạo hay hệ thống sinh. Cần xác minh trước khi tích hợp.
- Chưa đọc chi tiết nội dung diff của file task (chỉ kiểm stat và status).
- Không chạm `app.py`, không chạm DB.

### 2. Chỉ đọc DB
Lệnh: grep INSERT/UPDATE/DELETE/CREATE/DROP/ALTER/REPLACE/commit trên `scripts/build_credits.py`.
- Không có câu lệnh ghi nào trong script (grep không khớp).
- Kết nối DB: `sqlite3.connect('file:...?mode=ro', uri=True)` (dòng 93-94). Truy vấn chỉ có SELECT.
- Các câu CREATE/INSERT xuất hiện trong test chỉ chạy trên DB fixture tạm trong test (`executescript` đầu dòng 49). Chưa kiểm chi tiết đường dẫn fixture có trỏ tới DB thật không; báo cáo coder nói là DB tạm.

### 3. Test
Lệnh: `python -X utf8 tests/test_t290_credits_generator.py` và `python -X utf8 -m pytest tests/test_t290_credits_generator.py -q`
```
PASS test_blocked_sources_listed_with_explanation
PASS test_check_page_fails_on_handwritten_page
PASS test_check_page_passes_on_generated_page
PASS test_cli_check_exit_codes
PASS test_load_db_counts_claims_and_authority
PASS test_load_rejects_empty_db_placeholder
PASS test_render_entries_equal_sql_rows
PASS test_select_groups_rule
PASS test_unverified_license_is_not_asserted
PASS test_verified_license_shown_from_db
10/10 PASS
pytest: 10 passed in 0.78s
```
Dòng "FAIL — Thiếu nguồn SAT" có trong output là từ test âm tính có chủ đích (test_cli_check_exit_codes), không phải lỗi.

### 4. --check
Lệnh: `python -X utf8 scripts/build_credits.py --api http://127.0.0.1:5000/daoanh/api/admin/sources/list --check --out credits.html` (chỉ GET)
```
Dữ liệu: 16 nguồn · đang dùng 7 · chặn/chưa xác minh 9
PASS — credits.html khớp 16 dòng data_sources (mỗi nguồn đúng 1 mục).
exit=0
```
- Lệnh `--check` không tham số: exit 2, báo "không tìm thấy lineage.db thật". Đây là hành vi đã ghi trong báo cáo coder, vì `data/lineage.db` là file 0 byte.
- Không kiểm được với DB thật do không có DB thật trong worktree.

### 5. Đối chiếu số và nội dung trang
Dữ liệu API (16 dòng, GET):
- ACTIVE/nonblocked (7): DILA, CBETA, MARCUS, ZQLOCAL, Wikidata, ZENLINEAGE, TTL_LOCAL. Khớp với báo cáo coder.
- Blocked/inactive (9): BDRC, SAT, CHGIS, FoJin, Kanripo, SuttaCentral, 84000, TGAZ, DILA_CATALOG. Khớp.
- Lưu ý: trong DB, các `legal_status` là AUDITING, UNKNOWN, INTERNAL_USE. Không có giá trị ACTIVE hay REFERENCE_ONLY.

Trên credits.html (grep):
- 7 `class="source-card"` + 9 `<li data-source-code>` = 16. Mỗi `data-source-code` xuất hiện đúng 1 lần.
- Có marker `<!-- t290:total=16 in_use=7 blocked=9 ... -->`.
- Có 6/7 nguồn đang dùng ghi "chưa xác minh" (DILA, MARCUS, ZQLOCAL, Wikidata, ZENLINEAGE, TTL_LOCAL). CBETA có `license_verified=1`, `CC-BY-NC-SA-4.0`.
- Không còn chuỗi "CC BY-SA 3.0" cũ. Đây là điểm tốt.

**FAIL — ghi chú biên tập khẳng định điều khoản chưa xác minh:**
- `EDITORIAL_NOTES['DILA']` được render thành: "Bản phái sinh phân phối ra ngoài phải cùng giấy phép chia sẻ tương tự". Đây là một điều khoản (share-alike) được viết cứng, không lấy từ DB, cho nguồn có `license_verified=0`.
- Điều này trái với docstring của script ("Điều khoản hiển thị trên trang luôn lấy từ DB") và với yêu cầu "không tự khẳng định điều khoản" của QA T290.
- `--check` chỉ kiểm sự có mặt của chuỗi "chưa xác minh", không kiểm nội dung ghi chú, nên lỗi này không bị phát hiện.
- Ghi chú CBETA ("chỉ dùng phi thương mại") cũng là điều khoản cứng, nhưng DB có `license_verified=1` với CC-BY-NC-SA, nên tạm chấp nhận.
- Lỗi nhỏ: footer ghi cứng "Sinh từ data_sources trong lineage.db", trong khi marker ghi `db=Source Hub API`. Dòng TTL_LOCAL còn để nguyên backtick `local_dump` trong HTML.

### 6. done_when
Yêu cầu: "credits.html liệt kê mọi nguồn ACTIVE/REFERENCE đúng giấy phép từ DB."
- Nghĩa chữ: không có nguồn nào trong DB có `legal_status` = ACTIVE hoặc REFERENCE_ONLY. Nếu áp đúng chữ thì danh sách rỗng, không thể đánh giá đạt/không đạt theo cách đó.
- Cách hiểu của coder (active=1 và integration_mode≠BLOCKED): trang liệt kê đủ 7 nguồn. Cách hiểu này hợp lý, nhưng không phải điều task viết.
- "Đúng giấy phép": 6/7 nguồn đang dùng chưa có giấy phép xác minh trong DB, nên trang không thể nêu giấy phép đúng. Coder đã nêu rõ việc này cần Admin quyết.
- Kết luận: **chưa đạt, cần Admin chốt quy tắc lọc (ACTIVE/REFERENCE là cột nào, giá trị nào) và điền `license_spdx`/`license_verified` nếu muốn trang nêu điều khoản.**

## Đề xuất cho coder (không tự sửa)
1. Bỏ hoặc sửa ghi chú DILA trong `EDITORIAL_NOTES` để không khẳng định share-alike khi `license_verified=0`. Bổ sung kiểm trong `--check` để bắt các điều khoản cứng cho nguồn chưa xác minh.
2. Làm rõ trong task: "ACTIVE/REFERENCE" tương ứng cột nào và giá trị nào.
3. Xác minh nguồn của `.opencode/agents/coder.md` (untracked, ngoài phạm vi khai báo).
4. Đồng bộ footer (nguồn dữ liệu) với marker.

Không đánh DONE. Quyết định hoàn tất thuộc về Admin.
