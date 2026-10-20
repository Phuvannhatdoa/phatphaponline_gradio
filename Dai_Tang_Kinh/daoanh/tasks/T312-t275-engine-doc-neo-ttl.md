---
id: T312
title: "T275 — Engine đọc neo TTL trước (bước 6)"
module: Lineage / Generation
priority: p1
status: blocked
created: 2026-10-10
updated: 2026-10-10
owner: claude-code
parent: docs/integration (phân tích 2026-10-10)
depends_on: [T309]
done_when: |
  generation_engine_v2 ưu tiên neo TTL; BFS DILA chỉ khi không có neo.
  Admin xác nhận DONE. Không tự đánh DONE.
revert: |
  Chỉ thay đổi trong task này; hoàn tác bằng sao lưu trong docs/sessions/2026-10-10/ hoặc ROLLBACK.md.
outcome: >
  2026-10-10: tạo task backlog để agent code tuần tự. Chưa bắt đầu.
---

# T312 — T275 — Engine đọc neo TTL trước (bước 6)

## 1. Mục tiêu

generation_engine_v2 ưu tiên neo TTL; BFS DILA chỉ khi không có neo.

## 2. Hiện trạng (đã kiểm 2026-10-10)

Engine chưa đổi. Lâm Tế đời 30 vẫn unreachable/incomplete.

## 3. Các bước (agent làm lần lượt)

1) Admin duyệt thay đổi engine. 2) Backup. 3) Sửa parents(). 4) Chạy test số đời.

## 4. Kiểm chứng

Lâm Tế: Nghĩa Huyền 38, Phương Hội 45 khớp TTL.

## 5. Không làm trong task này

Không đổi số của tông khác mà không kiểm.

## 6. Các bước

- [ ] **Bước 1 —** xác minh hiện trạng và ghi log
- [ ] **Bước 2 —** chuẩn bị (sao lưu hoặc quyết định Admin)
- [ ] **Bước 3 —** làm việc chính theo mục 3
- [ ] **Bước 4 —** kiểm chứng theo mục 4
- [ ] **Bước 5 —** Admin xác nhận DONE
