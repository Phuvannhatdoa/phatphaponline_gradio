---
id: T290
title: "M5 — Sinh credits.html từ data_sources"
module: Attribution
priority: p1
status: done
created: 2026-10-10
updated: 2026-11-01
owner: claude-code
parent: docs/integration (phân tích 2026-10-10)
depends_on: [T283]
done_when: |
  credits.html liệt kê mọi nguồn ACTIVE/REFERENCE đúng giấy phép từ DB.
  Quy tắc lọc đã chốt (Admin 2026-11-01): giữ quy tắc hiện tại = active=1 AND integration_mode<>'BLOCKED' (7 nguồn). Mục chưa xác minh giấy phép ghi rõ.
  Admin xác nhận DONE. Không tự đánh DONE.
revert: |
  Chỉ thay đổi trong task này; hoàn tác bằng sao lưu trong docs/sessions/2026-10-10/ hoặc ROLLBACK.md.
outcome: >
  2026-10-10: tạo task backlog để agent code tuần tự. Chưa bắt đầu.
  2026-11-01 (coder): XONG phần code, chờ tester.
  Thêm `scripts/build_credits.py` (CHỈ ĐỌC DB): sinh credits.html từ `data_sources`
  (source_code/source_name/organization/legal_status/integration_mode/license_spdx/
  data_license/license_verified/origin_url/license_url/active) + claims đếm từ
  `entity_claims` + `source_authority.authority_score`. Nhóm "đang dùng" =
  `active=1 AND integration_mode<>'BLOCKED'`; còn lại vào mục "chặn/chưa xác minh"
  (nguồn bị chặn vẫn hiện dòng giải thích, không lỗi — theo M5). `--check` kiểm
  marker total/in_use/blocked + mỗi nguồn đúng 1 mục + giấy phép chưa xác minh phải
  ghi rõ "chưa xác minh". Thêm `tests/test_t290_credits_generator.py` (DB fixture
  tạm, không đụng DB thật): 10/10 PASS ban đầu; vòng 2 = 14/14 PASS; vòng 3 = 16/16 PASS.
  Sinh lại `credits.html`: 16 nguồn trong data_sources → 7 đang dùng (DILA, CBETA,
  MARCUS, ZQLOCAL, Wikidata, ZENLINEAGE, TTL_LOCAL), 9 chặn/chưa xác minh; `--check`
  PASS. Nguồn dữ liệu để sinh: DB thật KHÔNG có trong worktree (data/lineage.db =
  0 byte) → dùng `--api http://127.0.0.1:5000/daoanh/api/admin/sources/list` (GET
  chỉ-đọc trên app đang chạy, đọc trực tiếp bảng data_sources). Không ghi DB, không
  sửa giấy phép. CẦN ADMIN QUYẾT: 6/7 nguồn đang dùng có `license_verified=0` nên
  trang ghi "Chưa xác minh giấy phép" thay vì nêu điều khoản (bản cũ ghi tay
  CC BY-SA 3.0 cho DILA…) — muốn trang nêu điều khoản thì phải điền `license_spdx` +
  `license_verified` trong DB (việc của task khác, T290 không được ghi DB).
  Lưu ý kiểm thử: /daoanh/credits.html KHÔNG có route trong app.py:5000 (404 là bình
  thường); trang là file tĩnh, phục vụ bởi nginx/`local_gateway.py` (port 8080).
  Backup bản cũ: docs/sessions/2026-11-01/T290-coder/backup/credits.html.bak-before-coder

  2026-11-01 (coder, vòng 2 — sửa theo TESTER-REPORT):
  Sửa 1 — XONG: `scripts/build_credits.py` tách ghi chú làm 2 tầng. `EDITORIAL_NOTES`
  chỉ mô tả vai trò/ngữ cảnh, không còn câu nào nêu giấy phép/bản quyền/share-alike.
  Điều khoản chuyển sang `LICENSE_TERM_NOTES` và chỉ render khi `license_verified=1`.
  DILA (`license_verified=0`) hết câu "cùng giấy phép chia sẻ tương tự";
  CBETA (verified=1) vẫn hiện điều khoản phi thương mại.
  Sửa 2 — XONG: thêm `find_license_claims()` (8 mẫu: giấy phép, license, bản quyền,
  copyright, thương mại, share-alike/chia sẻ tương tự, mã CC, public domain) +
  `card_segment()`/`NOTE_BLOCK_RE`. `--check` soi khối `<div class="note">` của mọi
  nguồn `license_verified=0` và FAIL nếu thấy điều khoản (bỏ qua khối cảnh báo
  "note unverified"). Thêm 4 test: `test_unverified_source_shows_no_license_term_note`,
  `test_verified_source_shows_license_term_note`, `test_editorial_notes_have_no_license_terms`,
  `test_check_page_flags_hardcoded_license_note` (test cuối: chèn ghi chú cứng vào thẻ DILA
  → `--check` báo lỗi, chứng minh bắt được đúng lỗi tester nêu).
  Sửa 3 — XONG (ghi rõ, KHÔNG đổi quy tắc): "đang dùng" = `active=1 AND
  integration_mode<>'BLOCKED'` (gồm cả `local_dump`, `REFERENCE_ONLY`); còn lại
  (`active=0` hoặc `BLOCKED`) → mục "chặn/chưa xác minh". Không lọc theo `legal_status`
  vì DB chỉ có AUDITING/UNKNOWN/INTERNAL_USE (không có ACTIVE/REFERENCE_ONLY). Nếu Admin
  chốt cột khác: chỉ sửa `select_groups()` (1 hàm) — đếm, render, `--check` tự theo.
  Sửa 4 — XONG, output:
  · `python -X utf8 tests/test_t290_credits_generator.py` → 14/14 PASS
  · `python -X utf8 -m pytest tests/test_t290_credits_generator.py -q` → 14 passed in 2.32s
  · `python -X utf8 scripts/build_credits.py --api http://127.0.0.1:5000/daoanh/api/admin/sources/list --out credits.html`
    → "Đã sinh credits.html: 16 nguồn · đang dùng 7 · chặn/chưa xác minh 9"
  · thêm `--check` → "PASS — credits.html khớp 16 dòng data_sources (mỗi nguồn đúng 1 mục)." exit=0
  · kiểm lại trang: "chia sẻ tương tự" = 0 lần; `class="note term"` = 1 (chỉ CBETA, verified=1).
  CHƯA SỬA (ngoài danh sách Sửa 1–4, để MA/Admin quyết):
  (a) footer đã đồng bộ với marker (vòng 3); (b) ghi chú TTL_LOCAL: đã bỏ 2 dấu
  backtick hiển thị thô, nội dung giữ nguyên ("nạp cục bộ local_dump");
  (c) `.opencode/agents/coder.md` vẫn untracked, vẫn không rõ nguồn gốc (không phải đầu
  ra của coder — MA sao chép vào worktree);
  (d) 6/7 nguồn đang dùng vẫn `license_verified=0` → trang ghi "Chưa xác minh giấy phép"
  thay vì nêu điều khoản; muốn nêu điều khoản phải điền `license_spdx` + `license_verified`
  trong DB (task khác — T290 không ghi DB); (e) quy tắc lọc ACTIVE/REFERENCE còn chờ Admin chốt.
  Backup vòng 2: docs/sessions/2026-11-01/T290-coder/backup/{build_credits.py,test_t290_credits_generator.py,credits.html}.bak-before-coder-fix1

  2026-11-01 (coder, vòng 3 — sửa theo TESTER-REPORT-2):
  Sửa 5 — XONG: mở rộng `--check` để bắt ghi chú cứng nêu giấy phép ở mọi dạng
  (`<div class="note term">`, `<p class="note">`, mọi thẻ có class chứa "note", trừ
  khối cảnh báo `note unverified`). Thêm `NOTE_LIKE_RE` + `note_like_blocks()` và 2 test
  (`test_check_page_flags_hardcoded_license_note_term_class`,
  `test_check_page_flags_hardcoded_license_note_p_tag`). Test tổng 14 → 16 PASS.
  Footer: bỏ câu cứng "Sinh từ data_sources trong lineage.db" (thay bằng "Sinh từ bảng
  data_sources"), đồng bộ với marker `db=Source Hub API`.
  Vòng 3 output:
  · `python -X utf8 tests/test_t290_credits_generator.py` → 16/16 PASS
  · `python -X utf8 -m pytest tests/test_t290_credits_generator.py -q` → 16 passed in 1.31s
  · `python -X utf8 scripts/build_credits.py --api ... --out credits.html` → 16 nguồn · 7 · 9
  · `--check` → PASS, exit=0.
  CHƯA SỬA (ngoài danh sách, để MA/Admin quyết):
  (a) footer nay đã đồng bộ nguồn dữ liệu với marker (đã sửa vòng 3);
  (b) ghi chú TTL_LOCAL giữ nội dung "nạp cục bộ local_dump" (đã bỏ backtick hiển thị thô);
  (c) `.opencode/agents/coder.md` vẫn untracked (MA sao chép);
  (d) 6/7 nguồn đang dùng vẫn `license_verified=0`;
  (e) quy tắc lọc ACTIVE/REFERENCE còn chờ Admin chốt.
  Backup vòng 3: docs/sessions/2026-11-01/T290-coder/backup/{build_credits.py,test_t290_credits_generator.py,credits.html}.bak-before-coder-fix2
---

# T290 — M5 — Sinh credits.html từ data_sources

## 1. Mục tiêu

credits.html liệt kê mọi nguồn ACTIVE/REFERENCE đúng giấy phép từ DB.

## 2. Hiện trạng (đã kiểm 2026-10-10)

credits.html ở gốc daoanh/ đã có, chưa đối chiếu đủ nguồn.

## 3. Các bước (agent làm lần lượt)

1) So danh sách trang với data_sources. 2) Sinh nội dung từ DB (không gõ tay). 3) Kiểm.

## 4. Kiểm chứng

Số nguồn trên trang = số dòng SQL.

## 5. Không làm trong task này

Không đổi giấy phép trong DB.

## 6. Các bước

- [x] **Bước 1 —** xác minh hiện trạng và ghi log
- [x] **Bước 2 —** chuẩn bị (sao lưu `docs/sessions/2026-11-01/T290-coder/backup/credits.html.bak-before-coder`)
- [x] **Bước 3 —** làm việc chính theo mục 3 (`scripts/build_credits.py` sinh trang từ `data_sources`; `credits.html` đã sinh lại)
- [x] **Bước 4 —** kiểm chứng theo mục 4 (`--check` PASS: 16 mục = 16 dòng; 16/16 test PASS)
- [ ] **Bước 5 —** Admin xác nhận DONE

## 7. Sửa sau tester (2026-11-01, tester FAIL — chờ coder sửa)

Nguồn: `docs/sessions/2026-11-01/T290-coder/TESTER-REPORT.md` (trong worktree này).

- [x] **Sửa 1 —** Bỏ điều khoản cứng của DILA trong `EDITORIAL_NOTES` (`scripts/build_credits.py`). Nếu nguồn có `license_verified=0` thì ghi "chưa xác minh giấy phép", không nêu "cùng giấy phép chia sẻ tương tự".
- [x] **Sửa 2 —** (đạt) Thêm vào `--check`: báo lỗi nếu có ghi chú cứng nêu giấy phép cho nguồn đang `license_verified=0`. Thêm test tương ứng vào `tests/test_t290_credits_generator.py`.
- [x] **Sửa 3 —** Ghi rõ trong `outcome` cách lọc "ACTIVE/REFERENCE" đang dùng (`active=1 AND integration_mode<>'BLOCKED'`). KHÔNG đổi quy tắc lọc: quy tắc này chờ Admin chốt.
- [x] **Sửa 4 —** Chạy lại test và `--check`, ghi output vào outcome. Đổi lại thành `status: testing` khi xong.
- [x] **Sửa 5 (tester lần 2) —** (đạt) Mở rộng `--check` để bắt cả `<div class="note term">` và `<p class="note">` (mọi thẻ có class chứa `note`, trừ `note unverified`), kèm test cho từng dạng. Chạy lại test (16/16 PASS) và `--check` (PASS).

Ngoài phạm vi, không làm: `.opencode/agents/coder.md` là file untracked do MA sao chép vào worktree, không phải đầu ra của coder.
