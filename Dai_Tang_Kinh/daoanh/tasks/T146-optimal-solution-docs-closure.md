---
id: T146
title: "Optimal Solution Docs Closure — Quy trình Governance chuẩn hoá (docs-only, 0 code, 0 DB)"
module: daoanh
priority: high
status: done
created: 2026-09-16
updated: 2026-09-16
done_when:
  - "[x] Ghi nhận phê chuẩn Admin cho đề xuất tối ưu 4 trụ (workflow rule / git additive / ROLLBACK SSOT / HITL)"
  - "[x] Tạo task T146 — số tiếp theo SSOT (real max tasks/ = T145)"
  - "[x] Session md + tasktodo + ROLLBACK row (placeholder → hash-fill 2-pass)"
  - "[x] Dashboard regen `scripts/build_progress_data.py` → progress_data.json"
  - "[x] 0 code, 0 API, 0 Schema, 0 DB — docs-only"
---

# T146 — Optimal Solution Docs Closure (Governance chuẩn hoá)

## Bối cảnh

Admin phê chuẩn đề xuất "Giải pháp tối ưu" cho dự án Đạo Ảnh (Truyền Thừa) — hoá thạch thành **quy trình governance chuẩn** để mọi phiên sau (T147+) không lặp lại lỗi cấu trúc: mojibake trong git log, đánh hash tay, commit trùng/no-op, phạm vi dirty.

## Giải pháp tối ưu — 4 trụ (đã phê chuẩn)

1. **Workflow Rule (bắt buộc trước Review):** chạy `npm run pipeline` (lint → test → e2e) TRƯỚC khi xin Admin review. Admin chỉ review khi "All tests passed". Không ngoại lệ.
2. **Git additive + append-only:** 0 `reset`, 0 DB ALTER, mọi thay đổi additive; rollback = `git revert` (giữ lịch sử). Docs closure commit riêng, tách khỏi commit code.
3. **ROLLBACK.md = SSOT:** mỗi hành động là 1 row `| Date | Hash | Nội dung |`; hash luôn lấy thật từ `git rev-parse <sha>` — KHÔNG gõ tay hash. Placeholder → hash-fill 2-pass (commit row placeholder → commit xong lấy real hash → hash-fill).
4. **HITL (Human-In-The-Loop):** mọi quyết định phạm vi/kiến trúc/browser-verify do Admin; agent báo cáo trung thực (fallback khi thiếu dữ liệu, không bịa).

## Quy trình chuẩn hoá cho session (đã áp dụng)

- **SSOT count task:** `Get-ChildItem tasks/T###.md` → real max filename = T145 → T146 là số kế tiếp (KHÔNG đọc T### lẫn trong body/ROLLBACK/quotes để tránh false-positive).
- **Dashboard regen:** `python scripts/build_progress_data.py` → `data/progress_data.json` (0 ALTER, idempotent, additive).
- **Commit ngữ cảnh:** thread-safe, ASCII subject, 0 MOJIBAKE — chỉ `docs/*.md`, `tasks/T146*.md`, `data/progress_data.json`.

## Scope

- ✅ Docs: `docs/tasktodo.md`, `docs/ROLLBACK.md`, `docs/sessions/2026-09-16_t146-optimal-solution-docs-closure.md`
- ✅ Task: `tasks/T146-optimal-solution-docs-closure.md`
- ✅ Data regen: `data/progress_data.json`
- ❌ Code: NONE · ❌ API: NONE · ❌ Schema/DB: NONE

## Commit + Revert

- Commit: xem `docs/ROLLBACK.md` (row T146 — docs-only).
- Revert: `git revert --no-edit <T146_docs_sha>` (0 code, 0 DB → revert an toàn).
