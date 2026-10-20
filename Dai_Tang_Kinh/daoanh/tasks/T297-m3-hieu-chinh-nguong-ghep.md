---
id: T297
title: "M3 — Hiệu chỉnh ngưỡng ghép trên ≥200 cặp gán nhãn tay"
module: Địa lý / GIS
priority: p2
status: blocked
created: 2026-10-10
updated: 2026-10-10
owner: claude-code
parent: docs/integration (phân tích 2026-10-10)
depends_on: [T295]
done_when: |
  Ngưỡng 2/10/25 km và điểm 0,5+0,3+0,2 được kiểm trên mẫu thật.
  Admin xác nhận DONE. Không tự đánh DONE.
revert: |
  Chỉ thay đổi trong task này; hoàn tác bằng sao lưu trong docs/sessions/2026-10-10/ hoặc ROLLBACK.md.
outcome: >
  2026-10-10: tạo task backlog để agent code tuần tự. Chưa bắt đầu.
---

# T297 — M3 — Hiệu chỉnh ngưỡng ghép trên ≥200 cặp gán nhãn tay

## 1. Mục tiêu

Ngưỡng 2/10/25 km và điểm 0,5+0,3+0,2 được kiểm trên mẫu thật.

## 2. Hiện trạng (đã kiểm 2026-10-10)

Ngưỡng hiện là giả định. Cần Admin gán nhãn ≥200 cặp.

## 3. Các bước (agent làm lần lượt)

1) Admin gán nhãn. 2) Chạy khớp thử. 3) Ghi báo cáo độ chính xác và độ phủ.

## 4. Kiểm chứng

Báo cáo có độ chính xác và độ phủ.

## 5. Không làm trong task này

Không tự động liên kết trên 25 km.

## 6. Các bước

- [ ] **Bước 1 —** xác minh hiện trạng và ghi log
- [ ] **Bước 2 —** chuẩn bị (sao lưu hoặc quyết định Admin)
- [ ] **Bước 3 —** làm việc chính theo mục 3
- [ ] **Bước 4 —** kiểm chứng theo mục 4
- [ ] **Bước 5 —** Admin xác nhận DONE
