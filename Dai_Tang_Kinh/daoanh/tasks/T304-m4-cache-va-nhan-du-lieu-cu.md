---
id: T304
title: "M4 — Cache 24 giờ và nhãn dữ liệu cũ"
module: Đối chiếu kinh điển
priority: p3
status: blocked
created: 2026-10-10
updated: 2026-10-10
owner: claude-code
parent: docs/integration (phân tích 2026-10-10)
depends_on: [T303]
done_when: |
  Khi nguồn ngoài không trả lời, vẫn hiện dữ liệu đã lưu và nhãn cũ.
  Admin xác nhận DONE. Không tự đánh DONE.
revert: |
  Chỉ thay đổi trong task này; hoàn tác bằng sao lưu trong docs/sessions/2026-10-10/ hoặc ROLLBACK.md.
outcome: >
  2026-10-10: tạo task backlog để agent code tuần tự. Chưa bắt đầu.
---

# T304 — M4 — Cache 24 giờ và nhãn dữ liệu cũ

## 1. Mục tiêu

Khi nguồn ngoài không trả lời, vẫn hiện dữ liệu đã lưu và nhãn cũ.

## 2. Hiện trạng (đã kiểm 2026-10-10)

Chưa có.

## 3. Các bước (agent làm lần lượt)

1) Cache theo nguồn. 2) Nhãn cũ.

## 4. Kiểm chứng

Tắt mạng thử: tab vẫn hiện dữ liệu cũ.

## 5. Không làm trong task này

Không gọi nguồn ngoài khi cache còn hạn.

## 6. Các bước

- [ ] **Bước 1 —** xác minh hiện trạng và ghi log
- [ ] **Bước 2 —** chuẩn bị (sao lưu hoặc quyết định Admin)
- [ ] **Bước 3 —** làm việc chính theo mục 3
- [ ] **Bước 4 —** kiểm chứng theo mục 4
- [ ] **Bước 5 —** Admin xác nhận DONE
