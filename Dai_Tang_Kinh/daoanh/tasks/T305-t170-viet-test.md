---
id: T305
title: "T170 — Viết tests/ cho pipeline (SPEC §6, R1–R8)"
module: Editorial / LLM Translation
priority: p1
status: blocked
created: 2026-10-10
updated: 2026-10-10
owner: claude-code
parent: docs/integration (phân tích 2026-10-10)
depends_on: [T306]
done_when: |
  Ba file test T170 PASS 100%.
  Admin xác nhận DONE. Không tự đánh DONE.
revert: |
  Chỉ thay đổi trong task này; hoàn tác bằng sao lưu trong docs/sessions/2026-10-10/ hoặc ROLLBACK.md.
outcome: >
  2026-10-10: tạo task backlog để agent code tuần tự. Chưa bắt đầu.
---

# T305 — T170 — Viết tests/ cho pipeline (SPEC §6, R1–R8)

## 1. Mục tiêu

Ba file test T170 PASS 100%.

## 2. Hiện trạng (đã kiểm 2026-10-10)

tests/ chưa có file test T170. Script T170 đã có.

## 3. Các bước (agent làm lần lượt)

1) Viết test theo SPEC. 2) Dùng DB tạm (T170_DB). 3) Test R3: 惠明 ≠ 慧明.

## 4. Kiểm chứng

pytest tests/test_dila_verifier_v3.py tests/test_dila_person_verifier.py tests/test_t170_redteam.py → 100% PASS.

## 5. Không làm trong task này

Không gọi API Groq trong test.

## 6. Các bước

- [ ] **Bước 1 —** xác minh hiện trạng và ghi log
- [ ] **Bước 2 —** chuẩn bị (sao lưu hoặc quyết định Admin)
- [ ] **Bước 3 —** làm việc chính theo mục 3
- [ ] **Bước 4 —** kiểm chứng theo mục 4
- [ ] **Bước 5 —** Admin xác nhận DONE
