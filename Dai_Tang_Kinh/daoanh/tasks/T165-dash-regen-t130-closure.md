---
id: T165
title: Dashboard regen + T130 closure (docs-only, additive, 0 code, 0 DB)
module: docs · dashboard (scripts/build_progress_data.py)
priority: medium
status: done
created: 2026-09-24
updated: 2026-09-24
depends_on: T130 (CLOSED 5/5)
owner: Lee
done_when: progress_data.json được regen chứa T130 status=done + git_history có commits T130; task T130 frontmatter status=done; ROLLBACK.md có row T165; commit docs từ git toplevel visjs-app PASS.
---

# T165 — Dashboard regen + T130 closure

**Status:** done (2026-09-24) — ĐÃ XONG: frontmatter T130→done, regen progress_data.json (89 tasks, done=49), tasktodo/ROLLBACK/session log cập nhật, guard PASS, commit `874a831`. Revert tiện lợi: `git revert --no-edit 874a831`.
**Phạm vi:** `tasks/T130-phap-mach-direct-lineage.md` (frontmatter) · `tasks/T165-dash-regen-t130-closure.md` (mới) · `data/progress_data.json` (regen) · `docs/tasktodo.md` · `docs/ROLLBACK.md` · `docs/sessions/2026-09-24_t165-dash-regen-t130-closure.md`. **0 code, 0 DB, 0 API.**

## Bối cảnh
- T130 (Pháp Mạch trực hệ chain) đã **CLOSED 5/5 sessions** (commits `f07d8cb`+`f125c44`+`74ef34c`, QA browser 18/18 PASS — Session 5).
- Nhưng `data/progress_data.json` còn cũ (2026-09-23) và task `tasks/T130...md` vẫn `status: planned` → dashboard hiển thị T130 là `pending` (planned không nằm trong VALID_STATUSES→map pending). Cần đồng bộ để admin xem đúng trạng thái.

## Các bước
1. Edit `tasks/T130-phap-mach-direct-lineage.md`: frontmatter `status: planned → done`, `updated: 2026-09-13 → 2026-09-24`; body `**Status:**` khớp thực tế DONE.
2. Tạo task file này (T165).
3. Regen `data/progress_data.json`: `python -X utf8 scripts/build_progress_data.py`.
4. Update `docs/tasktodo.md` (row T165 đầu ACTIVE) + `docs/ROLLBACK.md` (row commit) + session log.
5. Commit docs từ git toplevel `visjs-app` (SSOT rule T155) — chỉ stage file của mình, không đụng file dirty pre-existing.

## Verify
- `data/progress_data.json`: chứa T130 `status=done` + `generated_at` mới (2026-09-24) + `git_history` total tăng (có commits T130 Session 1–5).
- `npm run guard` PASS (SSOT repo-root = visjs-app, không `.git/HEAD` trong daoanh).

## Files
- `tasks/T130-phap-mach-direct-lineage.md` (edit frontmatter + status body)
- `tasks/T165-dash-regen-t130-closure.md` (mới)
- `data/progress_data.json` (regen)
- `docs/tasktodo.md` (row T165)
- `docs/ROLLBACK.md` (row T165)
- `docs/sessions/2026-09-24_t165-dash-regen-t130-closure.md` (session log)

## Rollback
- Docs-only → `git revert --no-edit 874a831` (khôi phục progress_data.json cũ + frontmatter T130 cũ). 0 DB, 0 code → an toàn.