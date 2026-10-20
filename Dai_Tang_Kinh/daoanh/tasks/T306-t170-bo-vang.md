---
id: T306
title: "T170 — Admin lập bộ vàng (25 place + 25 person)"
module: Editorial / LLM Translation
priority: p1
status: blocked
created: 2026-10-10
updated: 2026-10-10
owner: claude-code
parent: docs/integration (phân tích 2026-10-10)
depends_on: []
done_when: |
  Có docs/evidence/T170_gold_set.tsv ≥50 dòng với đáp án Admin xác nhận.
  Admin xác nhận DONE. Không tự đánh DONE.
revert: |
  Chỉ thay đổi trong task này; hoàn tác bằng sao lưu trong docs/sessions/2026-10-10/ hoặc ROLLBACK.md.
outcome: >
  2026-10-10: tạo task backlog để agent code tuần tự. Chưa bắt đầu.
---

# T306 — T170 — Admin lập bộ vàng (25 place + 25 person)

## 1. Mục tiêu

Có docs/evidence/T170_gold_set.tsv ≥50 dòng với đáp án Admin xác nhận.

## 2. Hiện trạng (đã kiểm 2026-10-10)

Chưa có bộ vàng.

## 3. Các bước (agent làm lần lượt)

1) Admin lập. 2) Kiểm trùng ID.

## 4. Kiểm chứng

Đếm dòng ≥50, không trùng.

## 5. Không làm trong task này

Không tự tạo đáp án.

## 6. Các bước

- [ ] **Bước 1 —** xác minh hiện trạng và ghi log
- [ ] **Bước 2 —** chuẩn bị (sao lưu hoặc quyết định Admin)
- [ ] **Bước 3 —** làm việc chính theo mục 3
- [ ] **Bước 4 —** kiểm chứng theo mục 4
- [ ] **Bước 5 —** Admin xác nhận DONE
