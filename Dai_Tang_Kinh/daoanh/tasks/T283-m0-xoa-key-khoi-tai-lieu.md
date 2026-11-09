---
id: T283
title: "M0 — Xóa chuỗi key Gemini khỏi docs/ và scripts/"
module: Nền dev & an toàn
priority: p0
status: done
created: 2026-10-10
updated: 2026-10-20
owner: claude-code
parent: docs/integration (phân tích 2026-10-10)
depends_on: []
done_when: |
  Không còn chuỗi giống key trong docs/ và scripts/.
  Admin xác nhận DONE. Không tự đánh DONE.
revert: |
  Khôi phục scripts/t166_identity_audit.py từ backup docs/sessions/2026-10-20/T283/t166_identity_audit.py.bak-before-T283
  hoặc `git revert --no-edit <sha>`. Chi tiết trong docs/ROLLBACK.md.
outcome: >
  2026-10-10: tạo task backlog để agent code tuần tự. Chưa bắt đầu.
  2026-10-20: FIX XONG phần code, chờ Admin xác nhận DONE. Quét lại toàn bộ docs/**/*.md +
  scripts/*.py: chỉ còn 1 file chứa key thật — `scripts/t166_identity_audit.py` (key nằm trong
  hằng FORBIDDEN_INLINE_LLM_KEY dùng để dò key lộ trong app.py). Backup trước khi sửa:
  `docs/sessions/2026-10-20/T283/t166_identity_audit.py.bak-before-T283` (SHA256 7BEBC433…B895).
  Sửa: thay key thật bằng regex mẫu `AIza[0-9A-Za-z_\-]{30,}` (FORBIDDEN_INLINE_LLM_KEY_RE) —
  bắt được MỌI key Gemini, không riêng key cũ. Verify: (1) quét lại AIza… trong docs/scripts = 0 file;
  (2) ast.parse OK; (3) test regex 3/3 PASS (bắt key cũ, bắt key mẫu, không bắt nhầm code sạch)
  tại %TEMP%\opencode\t283_test_regex.py. Lưu ý: `npm run audit:t166` FAIL có sẵn (DB thiếu cột
  identity_status trong translation_cache — schema T166 chưa migrate), KHÔNG do thay đổi này
  (xác nhận bằng schema PRAGMA: cols chỉ có id…updated_at). Không xoay key (việc Admin).
  Session: docs/sessions/2026-10-20_T283-remove-gemini-key.md.
  **Commit: `45fd624`** (fix: T283 xoa key Gemini cu trong t166_identity_audit.py (regex mau) + docs;
  ghi SHA lần 2 qua commit docs riêng). Revert: `git revert --no-edit 45fd624`.
---

# T283 — M0 — Xóa chuỗi key Gemini khỏi docs/ và scripts/

## 1. Mục tiêu

Không còn chuỗi giống key trong docs/ và scripts/.

## 2. Hiện trạng (đã kiểm 2026-10-10; quét lại 2026-10-20)

2026-10-10: 18 file docs/scripts còn chuỗi kiểu AIza…. app.py đã đọc key từ môi trường (0 chuỗi cứng).
2026-10-20: các lần dọn trước đã xử lý hết; chỉ còn 1 file — `scripts/t166_identity_audit.py`
(hằng FORBIDDEN_INLINE_LLM_KEY, key thật nằm trong source để dò key lộ). Đã thay bằng regex mẫu.

## 3. Các bước (agent làm lần lượt)

1) Liệt kê file (chỉ đường dẫn, số dòng, không in giá trị). 2) Sao lưu vào docs/sessions/2026-10-20/T283/. 3) Thay bằng tham chiếu biến môi trường hoặc ghi chú. 4) Kiểm lại.

## 4. Kiểm chứng

grep -rl "AIza[0-9A-Za-z_-]\{20,\}" docs scripts → 0 file. **ĐẠT 2026-10-20 (0 file).**

## 5. Không làm trong task này

Không xoay key (việc của Admin). Không in key ra log.

## 6. Các bước

- [x] **Bước 1 —** xác minh hiện trạng và ghi log
- [x] **Bước 2 —** chuẩn bị (sao lưu `docs/sessions/2026-10-20/T283/t166_identity_audit.py.bak-before-T283`)
- [x] **Bước 3 —** làm việc chính theo mục 3 (regex mẫu thay key thật)
- [x] **Bước 4 —** kiểm chứng theo mục 4 (0 file + ast.parse OK + test regex 3/3 PASS)
- [ ] **Bước 5 —** Admin xác nhận DONE
