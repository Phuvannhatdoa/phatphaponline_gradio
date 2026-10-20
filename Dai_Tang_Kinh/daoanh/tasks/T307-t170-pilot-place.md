---
id: T307
title: "T170 — Pilot 25 place (sau T287, T305, T306, có phê chuẩn Admin)"
module: Editorial / LLM Translation
priority: p1
status: blocked
created: 2026-10-10
updated: 2026-10-10
owner: claude-code
parent: docs/integration (phân tích 2026-10-10)
depends_on: [T287,T305,T306]
done_when: |
  Chạy --pilot 25 cho place; kết quả vào place_groq_audit; Admin duyệt.
  Admin xác nhận DONE. Không tự đánh DONE.
revert: |
  Chỉ thay đổi trong task này; hoàn tác bằng sao lưu trong docs/sessions/2026-10-10/ hoặc ROLLBACK.md.
outcome: >
  2026-10-10: tạo task backlog để agent code tuần tự. Chưa bắt đầu.
---

# T307 — T170 — Pilot 25 place (sau T287, T305, T306, có phê chuẩn Admin)

## 1. Mục tiêu

Chạy --pilot 25 cho place; kết quả vào place_groq_audit; Admin duyệt.

## 2. Hiện trạng (đã kiểm 2026-10-10)

Bảng place_groq_audit có sẵn, 0 dòng. Lần chạy thật cần phê chuẩn.

## 3. Các bước (agent làm lần lượt)

1) Sao lưu. 2) --validate-only. 3) --pilot 25. 4) Admin duyệt mẫu.

## 4. Kiểm chứng

Đối soát SQL theo SPEC §8.

## 5. Không làm trong task này

Không chạy production.

## 6. Các bước

- [ ] **Bước 1 —** xác minh hiện trạng và ghi log
- [ ] **Bước 2 —** chuẩn bị (sao lưu hoặc quyết định Admin)
- [ ] **Bước 3 —** làm việc chính theo mục 3
- [ ] **Bước 4 —** kiểm chứng theo mục 4
- [ ] **Bước 5 —** Admin xác nhận DONE
