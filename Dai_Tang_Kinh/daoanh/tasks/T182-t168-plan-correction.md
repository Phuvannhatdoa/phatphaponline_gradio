---
id: T182
title: "T168 PLAN correction — sửa số liệu stale + tham chiếu nguồn sai (docs-only)"
module: Editorial / LLM Translation
priority: high
status: done
owner: claudecode
depends_on: [T165, T166, T167]
created: 2026-09-27
updated: 2026-09-27
done_at: "2026-09-27 (docs edit xong + tasktodo/ROLLBACK/session + dashboard regen; chờ commit 2-pass hash-fill)"
plan_approved_at: "2026-09-27 (Admin: 'Đồng ý build, hãy lưu logs, gitcommit và update các thông tin...' — phê chuẩn đề xuất sửa T168 PLAN)"
done_when: |
  (S1) Tham chiếu nguồn `admin/app.py (18.865 dòng)` trong T168 PLAN audited:
       file KHÔNG tồn tại → thay bằng `app.py` + ghi chú rõ.
  (S2) A1 rule_type "chỉ 4 giá trị (86/8/2/1)" → cập nhật 7 giá trị thật
       (terminology 90 · style 10 · forbidden 6 · gate 3 · provenance 1 · structure 1 · grammar 1 = 112).
  (S3) P0-2 "RULE-% = 0 row" → 15 row thật (T167 seeded).
  (S4) A1 "96 active + 1 dismissed" → active 110 (+1 active/is_active=0) · dismissed 1 · pending 0.
  (S5) A1 cache "1.761 (auto 1.752)" → 1.799 (auto 1.790 · draft 2 · edited 6 · invalidated 1).
  (S6) A1 "_t73_call_gemini bỏ usage, 0 retry" → đã có retry/backoff 429 (T178 gap 13).
  (S7) A1 "tests/ chỉ 4 file" → 11 file test thật.
  (S8) Line refs drift → `_t73_rules_version`=16916 · `_t73_source_hash`=16923 ·
       `_glossary_resolver`=16958 · `_t73_call_gemini`=17083 · worker `validate_unit`=212.
  Banner snapshot 2026-09-25 + frontmatter status pending → superseded.
  tasktodo + ROLLBACK + session + dashboard regen + commit 2-pass hash-fill.
  Revert tiện: 1 lệnh `git revert --no-edit 13b0ca59df55e719735698e49428462906e4f7d2` (docs-only, 0 code/0 DB).
---

# T182 — T168 PLAN correction (docs-only)

## Bối cảnh

`docs/Mimo-Flash/T168-rule-resolver-context-compiler-PLAN.md` ghi ngày 2026-09-25, được absorb
vào T165/T166, nhưng khi T167/T177/T178/T179 thay đổi DB & code, các số liệu A1/P0-2 trong plan
KHÔNG được cập nhật → trở thành "PLAN lịch sử mang số liệu thời điểm 2026-09-25" trong khi
frontmatter vẫn `status: pending` + Phase 5/7/8 chưa tick (mơ hồ: đã absorb chưa, còn sống không).

Audit read-only (2026-09-27) phát hiện 8 điểm lệch (S1–S8).

## Việc cần làm (đã Admin phê chuẩn)

1. **S1 (bắt buộc, P0):** Audit scope + A1 line 61 dùng `admin/app.py (18.865 dòng)` và
   `admin/app.py:18193` — file **KHÔNG tồn tại** (`Test-Path = False`; chính
   `tasks/T168-t165-spec-v2-review-accepted.md` đã xác nhận "18865 là ảo giác").
   → Thay bằng `app.py` (21.054 dòng) + ghi chú rõ `admin/app.py` không tồn tại.

2. **S2–S8:** cập nhật A1 theo DB/code thật 2026-09-27 (chi tiết trong done_when).

3. **Banner snapshot** đầu file: "Snapshot 2026-09-25 — đã evolve theo T167/T177/T178/T179;
   bảng thật xem tasks/T168-t165-spec-v2-review-accepted + tasktodo T178/T179".

4. **Frontmatter** `status: pending` → `superseded` (plan đã absorb T165/T166, Phase 1–4 build xong;
   Phase 5/7/8 đã làm qua T166/T178/T179).

## Verify

- py_compile docs không áp dụng (docs-only); chạy `npm run guard` + kiểm tra frontmatter parse.
- `scripts/build_progress_data.py` regen dashboard → `data/progress_data.json` có entry T182.
- `npm run pipeline` PASS (các test Python không chạm plan).

## Revert

- **1 lệnh:** `git revert --no-edit 13b0ca59df55e719735698e49428462906e4f7d2` (docs-only) — khôi phục T168 PLAN cũ vì
  nội dung cũ chưa bị xóa (edit additive), tasktodo/ROLLBACK/session back về trước.
- Cấm `cp *.bak`, cấm `reset --hard`.