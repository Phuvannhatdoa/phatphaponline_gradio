---
id: T166
title: Dashboard hygiene batch — đồng bộ frontmatter 9 task stale + regen progress_data.json (docs-only, 0 code, 0 DB)
module: docs · dashboard (scripts/build_progress_data.py)
priority: medium
status: done
created: 2026-09-24
updated: 2026-09-24
depends_on: T165 (dashboard regen convention)
owner: Lee
done_when: 9 task file frontmatter khớp thực tế docs/tasktodo.md (T131/T137/T138/T110/T52/T97b/T125/T126 → done; T139 → in_progress); 4 file không-frontmatter (T97b/T125/T126/T139) được thêm frontmatter YAML để parse chuẩn; progress_data.json regen (89 tasks, done=57); tasktodo/ROLLBACK/session log cập nhật; commit docs từ git toplevel visjs-app PASS.
---

# T166 — Dashboard hygiene batch (frontmatter stale sync)

**Status:** done (2026-09-24) — ĐÃ XONG: 9 frontmatter đồng bộ, regen progress_data.json (89 tasks · done=57 · in_progress=17 · pending=13 · git 460 commits), tasktodo/ROLLBACK/session log cập nhật, guard PASS, commit `14412bf`. Revert tiện lợi: `git revert --no-edit 14412bf`.
**Phạm vi:** 9 file `tasks/*.md` (frontmatter edits) · `tasks/T166-dashboard-hygiene-batch.md` (mới) · `data/progress_data.json` (regen) · `docs/tasktodo.md` · `docs/ROLLBACK.md` · `docs/sessions/2026-09-24_t166-dashboard-hygiene-batch.md`. **0 code, 0 DB, 0 API.**

## Bối cảnh
Phát hiện từ cross-check (2026-09-24): dashboard `progress_data.json` đếm sai loạt task vì **frontmatter file task tụt sau thực tế** `docs/tasktodo.md`. Hệ quả: 8 task đã DONE bị hiển thị pending/in_progress, 1 task in_progress bị hiện pending. Cần đồng bộ để admin xem đúng trạng thái trước khi chốt backlog.

## Các bước
1. **5 file có frontmatter** → sửa `status` theo thực tế docs/tasktodo.md:
   - `tasks/T131-b21-source-governance-refine.md`: `in_progress → done` (`c686636` build additive committed, tasktodo:31, updated 2026-09-18)
   - `tasks/T137-zen-lineage-integration-audit.md`: `in_progress → done` (AUDIT-ONLY, tasktodo:37)
   - `tasks/T138-zen-lineage-render-policy.md`: `in_progress → done` (DONE + LIVE, tasktodo:36)
   - `tasks/T110-glossary-vietnamese-pipeline.md`: `pending → done` (T05 closure, tasktodo:210)
   - `tasks/T52-doi-chieu-tam-tang.md`: `pending → done` (T52a–e, tasktodo:161, updated 2026-09-11)
2. **4 file KHÔNG có frontmatter YAML** (bắt đầu `# T...`) → parse_frontmatter script trả rỗng → default `pending`. **Thêm frontmatter YAML đầy đủ** để dashboard parse đúng:
   - `tasks/T97b-place-tu-si-timeline-events.md`: `status: done` (tasktodo:13, `ed03c86`)
   - `tasks/T125-qa-tab-safe-fallback.md`: `status: done` (tasktodo:157)
   - `tasks/T126-qa-backend-real.md`: `status: done` (tasktodo:156)
   - `tasks/T139-zen-lineage-gateway.md`: `status: in_progress` (Phase 2 completion, chờ HITL — tasktodo:35)
3. Regen `data/progress_data.json`: `python -X utf8 scripts/build_progress_data.py`.
4. Update `docs/tasktodo.md` (row T166 đầu ACTIVE) + `docs/ROLLBACK.md` (row commit) + session log.
5. Commit docs từ git toplevel `visjs-app` (SSOT rule T155) — chỉ stage file của mình, không đụng file dirty pre-existing.

## Verify
- `data/progress_data.json`: T131/T137/T138/T110/T52/T97b/T125/T126 = `done`, T139 = `in_progress`, `generated_at` mới (2026-09-24), `task_meta`: done=57 · in_progress=17 · pending=13 · total=89.
- `npm run guard` PASS (SSOT repo-root = visjs-app, không `.git/HEAD` trong daoanh).

## Files
- `tasks/T131-b21-source-governance-refine.md` (frontmatter)
- `tasks/T137-zen-lineage-integration-audit.md` (frontmatter)
- `tasks/T138-zen-lineage-render-policy.md` (frontmatter)
- `tasks/T110-glossary-vietnamese-pipeline.md` (frontmatter)
- `tasks/T52-doi-chieu-tam-tang.md` (frontmatter)
- `tasks/T97b-place-tu-si-timeline-events.md` (thêm frontmatter YAML)
- `tasks/T125-qa-tab-safe-fallback.md` (thêm frontmatter YAML)
- `tasks/T126-qa-backend-real.md` (thêm frontmatter YAML)
- `tasks/T139-zen-lineage-gateway.md` (thêm frontmatter YAML)
- `tasks/T166-dashboard-hygiene-batch.md` (mới)
- `data/progress_data.json` (regen)
- `docs/tasktodo.md` (row T166)
- `docs/ROLLBACK.md` (row T166)
- `docs/sessions/2026-09-24_t166-dashboard-hygiene-batch.md` (session log)

## Rollback
- Docs-only → `git revert --no-edit 14412bf` (khôi phục frontmatter cũ + progress_data.json cũ). 0 DB, 0 code → an toàn. KHÔNG ảnh hưởng T164 (task riêng, 0 xung đột — T164 đã commit `77dec5e` từ 2026-09-23).