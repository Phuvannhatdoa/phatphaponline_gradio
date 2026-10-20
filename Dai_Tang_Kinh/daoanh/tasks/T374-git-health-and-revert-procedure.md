---
id: T374
title: "Kiểm tra sức khỏe git + quy trình chuẩn hoàn tác một bản sửa (revert one fix)"
status: in_progress
created: 2026-10-13
updated: 2026-10-13
owner: claude-code (phiên housekeeping 2026-10-13)
plan_approved_at: "2026-10-13 (Admin duyệt qua chat)"
dispatch: approved
done_when: >
  (1) docs/sessions/2026-10-13/git-health.md ghi HEAD, nhánh, số dòng git status, số staged
  deletion, worktree, rác object — có lệnh đo kèm theo.
  (2) docs/process/REVERT_ONE_FIX.md mô tả quy trình: một commit cho một việc, stage theo
  đường dẫn tường minh, kiểm `git diff --cached`, hoàn tác bằng `git revert <sha>`.
  (3) AGENTS.md và CLAUDE.md chỉ được NỐI THÊM một mục ngắn trỏ tới tài liệu trên.
  (4) Admin xác nhận DONE.
revert: >
  git revert --no-edit <sha_T374> (docs-only, 0 code, 0 DB). SHA ghi ở mục outcome.
outcome: >
  2026-10-13: Đo git (HEAD 89cea47 lúc đo, master, 23 dòng status, 0 staged — anomaly "mass staged deletion"
  trong CLAUDE.md hiện không còn; 10 file rác tmp_obj_* trong .git/objects; 2 worktree phụ; 1 stash).
  Viết docs/sessions/2026-10-13/git-health.md + docs/process/REVERT_ONE_FIX.md; nối mục §19 vào AGENTS.md
  và mục ngắn vào CLAUDE.md (bản sao: docs/sessions/2026-10-13/housekeeping/*.bak-before-T374).
  Commit: <sha_T374> (phiên không có quyền `git add` → commit qua
  docs/sessions/2026-10-13/housekeeping/commit_plan.sh). Chờ daoanh-qa + Admin.
---

# T374 — Git health + quy trình "revert one fix"

Thuộc lô housekeeping 2026-10-13 (T374–T378). Bàn giao: `docs/Handoff-2026-10-13-housekeeping.md`.

## Các bước

- [x] Đo trạng thái git từ repo root `visjs-app` (HEAD, nhánh, `git status --short`, staged, worktree, `count-objects`)
- [x] Ghi `docs/sessions/2026-10-13/git-health.md`
- [x] Viết `docs/process/REVERT_ONE_FIX.md`
- [x] Nối mục ngắn vào cuối `AGENTS.md` và `CLAUDE.md` (không sửa phần khác)
- [ ] Commit riêng, tiền tố `T374`
- [ ] Admin xác nhận DONE
