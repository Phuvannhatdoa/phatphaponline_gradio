---
id: T286
title: "M0 — Rà và tạo nháp .claude/rules, skills/onboard-source, agents/source-reviewer"
module: Nền dev & an toàn
priority: p2
status: blocked
created: 2026-10-10
updated: 2026-10-10
owner: claude-code
parent: docs/integration (phân tích 2026-10-10)
depends_on: [T285]
done_when: |
  Có rule theo paths cho adapters/** và gate/**, skill onboard-source, subagent source-reviewer chỉ đọc.
  Admin xác nhận DONE. Không tự đánh DONE.
revert: |
  Chỉ thay đổi trong task này; hoàn tác bằng sao lưu trong docs/sessions/2026-10-10/ hoặc ROLLBACK.md.
outcome: >
  2026-10-10: tạo task backlog để agent code tuần tự. Chưa bắt đầu.
---

# T286 — M0 — Rà và tạo nháp .claude/rules, skills/onboard-source, agents/source-reviewer

## 1. Mục tiêu

Có rule theo paths cho adapters/** và gate/**, skill onboard-source, subagent source-reviewer chỉ đọc.

## 2. Hiện trạng (đã kiểm 2026-10-10)

daoanh/.claude/ chỉ có launch.json và settings.json. Agents/skills nằm ở ../.claude/ (cần kiểm).

## 3. Các bước (agent làm lần lượt)

1) Admin xác nhận nơi đặt. 2) Tạo nháp. 3) Thử subagent chỉ đọc.

## 4. Kiểm chứng

Subagent chạy được, không có quyền ghi.

## 5. Không làm trong task này

Không tự kích hoạt skill onboard-source.

## 6. Các bước

- [ ] **Bước 1 —** xác minh hiện trạng và ghi log
- [ ] **Bước 2 —** chuẩn bị (sao lưu hoặc quyết định Admin)
- [ ] **Bước 3 —** làm việc chính theo mục 3
- [ ] **Bước 4 —** kiểm chứng theo mục 4
- [ ] **Bước 5 —** Admin xác nhận DONE
