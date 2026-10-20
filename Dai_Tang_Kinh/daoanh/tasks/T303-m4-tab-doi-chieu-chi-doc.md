---
id: T303
title: "M4 — Tab Đối chiếu đọc từ bảng có sẵn (chỉ đọc)"
module: Đối chiếu kinh điển
priority: p2
status: blocked
created: 2026-10-10
updated: 2026-10-10
owner: claude-code
parent: docs/integration (phân tích 2026-10-10)
depends_on: [T302]
done_when: |
  Tab hiển thị song song từ sat_crossref (2.913), toh_cbeta_crossref (10), kanripo_catalog (101), có nhãn mức Link/Metadata.
  Admin xác nhận DONE. Không tự đánh DONE.
revert: |
  Chỉ thay đổi trong task này; hoàn tác bằng sao lưu trong docs/sessions/2026-10-10/ hoặc ROLLBACK.md.
outcome: >
  2026-10-10: tạo task backlog để agent code tuần tự. Chưa bắt đầu.
---

# T303 — M4 — Tab Đối chiếu đọc từ bảng có sẵn (chỉ đọc)

## 1. Mục tiêu

Tab hiển thị song song từ sat_crossref (2.913), toh_cbeta_crossref (10), kanripo_catalog (101), có nhãn mức Link/Metadata.

## 2. Hiện trạng (đã kiểm 2026-10-10)

Các bảng đã có dữ liệu; chưa có tab.

## 3. Các bước (agent làm lần lượt)

1) API đọc bảng. 2) Tab trong trang đọc kinh. 3) Trạng thái rỗng nói rõ.

## 4. Kiểm chứng

Chụp màn hình có ít nhất 1 dòng song song đúng.

## 5. Không làm trong task này

Không hiển thị văn bản nguồn có giấy phép hạn chế.

## 6. Các bước

- [ ] **Bước 1 —** xác minh hiện trạng và ghi log
- [ ] **Bước 2 —** chuẩn bị (sao lưu hoặc quyết định Admin)
- [ ] **Bước 3 —** làm việc chính theo mục 3
- [ ] **Bước 4 —** kiểm chứng theo mục 4
- [ ] **Bước 5 —** Admin xác nhận DONE
