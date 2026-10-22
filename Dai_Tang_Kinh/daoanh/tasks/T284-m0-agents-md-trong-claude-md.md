---
id: T284
title: "M0 — Thêm @AGENTS.md vào CLAUDE.md"
module: Nền dev & an toàn
priority: p0
status: done
created: 2026-10-10
updated: 2026-10-21
owner: claude-code
parent: docs/integration (phân tích 2026-10-10)
depends_on: [T283]
done_when: |
  CLAUDE.md dưới 200 dòng, nhập AGENTS.md, giữ mọi quy tắc cũ.
  Admin xác nhận DONE. Không tự đánh DONE.
revert: |
  Chỉ thay đổi trong task này; hoàn tác bằng sao lưu trong docs/sessions/2026-10-10/ hoặc ROLLBACK.md.
outcome: >
  2026-10-10: tạo task backlog để agent code tuần tự. Chưa bắt đầu.
---

# T284 — M0 — Thêm @AGENTS.md vào CLAUDE.md

## 1. Mục tiêu

CLAUDE.md dưới 200 dòng, nhập AGENTS.md, giữ mọi quy tắc cũ.

## 2. Hiện trạng (đã kiểm 2026-10-10)

CLAUDE.md 98 dòng, không có @AGENTS.md.

## 3. Các bước (agent làm lần lượt)

1) Sao lưu CLAUDE.md. 2) Thêm dòng @AGENTS.md ở đầu. 3) Đối chiếu từng quy tắc cũ còn đủ (ZQ source_id=5, backup, quyền, VPS).

## 4. Kiểm chứng

wc -l CLAUDE.md < 200; grep "@AGENTS.md" CLAUDE.md có kết quả.

## 5. Không làm trong task này

Không xóa quy tắc cũ.

## 6. Các bước

- [ ] **Bước 1 —** xác minh hiện trạng và ghi log
- [ ] **Bước 2 —** chuẩn bị (sao lưu hoặc quyết định Admin)
- [ ] **Bước 3 —** làm việc chính theo mục 3
- [ ] **Bước 4 —** kiểm chứng theo mục 4
- [ ] **Bước 5 —** Admin xác nhận DONE
