---
id: T283
title: "M0 — Xóa chuỗi key Gemini khỏi docs/ và scripts/"
module: Nền dev & an toàn
priority: p0
status: pending
created: 2026-10-10
updated: 2026-10-10
owner: claude-code
parent: docs/integration (phân tích 2026-10-10)
depends_on: []
done_when: |
  Không còn chuỗi giống key trong docs/ và scripts/.
  Admin xác nhận DONE. Không tự đánh DONE.
revert: |
  Chỉ thay đổi trong task này; hoàn tác bằng sao lưu trong docs/sessions/2026-10-10/ hoặc ROLLBACK.md.
outcome: >
  2026-10-10: tạo task backlog để agent code tuần tự. Chưa bắt đầu.
---

# T283 — M0 — Xóa chuỗi key Gemini khỏi docs/ và scripts/

## 1. Mục tiêu

Không còn chuỗi giống key trong docs/ và scripts/.

## 2. Hiện trạng (đã kiểm 2026-10-10)

18 file docs/scripts còn chuỗi kiểu AIza…. app.py đã đọc key từ môi trường (0 chuỗi cứng).

## 3. Các bước (agent làm lần lượt)

1) Liệt kê 18 file (chỉ đường dẫn, số dòng, không in giá trị). 2) Sao lưu từng file vào docs/sessions/2026-10-10/. 3) Thay bằng tham chiếu biến môi trường hoặc ghi chú. 4) Kiểm lại.

## 4. Kiểm chứng

grep -rl "AIza[0-9A-Za-z_-]\{20,\}" docs scripts → 0 file.

## 5. Không làm trong task này

Không xoay key (việc của Admin). Không in key ra log.

## 6. Các bước

- [ ] **Bước 1 —** xác minh hiện trạng và ghi log
- [ ] **Bước 2 —** chuẩn bị (sao lưu hoặc quyết định Admin)
- [ ] **Bước 3 —** làm việc chính theo mục 3
- [ ] **Bước 4 —** kiểm chứng theo mục 4
- [ ] **Bước 5 —** Admin xác nhận DONE
