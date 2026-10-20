---
id: T292
title: "M5 — Script kiểm chế độ thương mại (không lộ văn bản CBETA)"
module: Attribution
priority: p1
status: blocked
created: 2026-10-10
updated: 2026-10-10
owner: claude-code
parent: docs/integration (phân tích 2026-10-10)
depends_on: [T291]
done_when: |
  Có script báo nếu HTML trả về ở chế độ thương mại chứa đoạn CBETA.
  Admin xác nhận DONE. Không tự đánh DONE.
revert: |
  Chỉ thay đổi trong task này; hoàn tác bằng sao lưu trong docs/sessions/2026-10-10/ hoặc ROLLBACK.md.
outcome: >
  2026-10-10: tạo task backlog để agent code tuần tự. Chưa bắt đầu.
---

# T292 — M5 — Script kiểm chế độ thương mại (không lộ văn bản CBETA)

## 1. Mục tiêu

Có script báo nếu HTML trả về ở chế độ thương mại chứa đoạn CBETA.

## 2. Hiện trạng (đã kiểm 2026-10-10)

Chưa có cờ chế độ thương mại. Điều khoản CBETA mâu thuẫn, chờ văn bản xác nhận.

## 3. Các bước (agent làm lần lượt)

1) Admin quyết định cờ và điều khoản áp dụng. 2) Viết script quét HTML.

## 4. Kiểm chứng

Script trả 0 đoạn CBETA ở chế độ thương mại.

## 5. Không làm trong task này

Không đưa ra tư vấn pháp lý.

## 6. Các bước

- [ ] **Bước 1 —** xác minh hiện trạng và ghi log
- [ ] **Bước 2 —** chuẩn bị (sao lưu hoặc quyết định Admin)
- [ ] **Bước 3 —** làm việc chính theo mục 3
- [ ] **Bước 4 —** kiểm chứng theo mục 4
- [ ] **Bước 5 —** Admin xác nhận DONE
