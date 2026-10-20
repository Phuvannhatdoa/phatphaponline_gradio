---
id: T296
title: "M3 — Gắn admin_centroid cho 33 liên kết BGIS (T31)"
module: Địa lý / GIS
priority: p2
status: blocked
created: 2026-10-10
updated: 2026-10-10
owner: claude-code
parent: docs/integration (phân tích 2026-10-10)
depends_on: [T294]
done_when: |
  33 liên kết BGIS có cờ admin_centroid, không đổi tọa độ.
  Admin xác nhận DONE. Không tự đánh DONE.
revert: |
  Chỉ thay đổi trong task này; hoàn tác bằng sao lưu trong docs/sessions/2026-10-10/ hoặc ROLLBACK.md.
outcome: >
  2026-10-10: tạo task backlog để agent code tuần tự. Chưa bắt đầu.
---

# T296 — M3 — Gắn admin_centroid cho 33 liên kết BGIS (T31)

## 1. Mục tiêu

33 liên kết BGIS có cờ admin_centroid, không đổi tọa độ.

## 2. Hiện trạng (đã kiểm 2026-10-10)

33 khớp BGIS từ T31.

## 3. Các bước (agent làm lần lượt)

1) Chọn 33 dòng theo bgis_id. 2) Đặt cờ.

## 4. Kiểm chứng

Đếm 33 dòng có cờ.

## 5. Không làm trong task này

Không nâng tâm huyện thành điểm.

## 6. Các bước

- [ ] **Bước 1 —** xác minh hiện trạng và ghi log
- [ ] **Bước 2 —** chuẩn bị (sao lưu hoặc quyết định Admin)
- [ ] **Bước 3 —** làm việc chính theo mục 3
- [ ] **Bước 4 —** kiểm chứng theo mục 4
- [ ] **Bước 5 —** Admin xác nhận DONE
