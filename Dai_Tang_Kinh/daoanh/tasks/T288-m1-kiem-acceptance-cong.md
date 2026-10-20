---
id: T288
title: "M1 — Kiểm acceptance cổng: BLOCKED bị từ chối, LEGACY không đổi"
module: Data Governance / License Gate
priority: p0
status: pending
created: 2026-10-10
updated: 2026-10-10
owner: claude-code
parent: docs/integration (phân tích 2026-10-10)
depends_on: [T287]
done_when: |
  Chứng minh cổng hoạt động: nguồn BLOCKED bị chặn, 5 nguồn LEGACY giữ nguyên số claims.
  Admin xác nhận DONE. Không tự đánh DONE.
revert: |
  Chỉ thay đổi trong task này; hoàn tác bằng sao lưu trong docs/sessions/2026-10-10/ hoặc ROLLBACK.md.
outcome: >
  2026-10-10: tạo task backlog để agent code tuần tự. Chưa bắt đầu.
---

# T288 — M1 — Kiểm acceptance cổng: BLOCKED bị từ chối, LEGACY không đổi

## 1. Mục tiêu

Chứng minh cổng hoạt động: nguồn BLOCKED bị chặn, 5 nguồn LEGACY giữ nguyên số claims.

## 2. Hiện trạng (đã kiểm 2026-10-10)

Đếm claims theo source_id hiện có (DILA 293.177, ZQLOCAL 118.295, MARCUS 22.332, CBETA 13.933, Wikidata 148).

## 3. Các bước (agent làm lần lượt)

1) Đếm trước. 2) Chạy dry-run các ETL đã nối. 3) Đếm sau, so sánh.

## 4. Kiểm chứng

Số claims trước = sau; có dòng audit cho nguồn bị chặn.

## 5. Không làm trong task này

Không nạp nguồn mới.

## 6. Các bước

- [ ] **Bước 1 —** xác minh hiện trạng và ghi log
- [ ] **Bước 2 —** chuẩn bị (sao lưu hoặc quyết định Admin)
- [ ] **Bước 3 —** làm việc chính theo mục 3
- [ ] **Bước 4 —** kiểm chứng theo mục 4
- [ ] **Bước 5 —** Admin xác nhận DONE
