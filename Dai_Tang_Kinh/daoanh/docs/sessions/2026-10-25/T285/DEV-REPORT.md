# DEV-REPORT — T285 M0 Hook PreToolUse chặn git ghi

- **Task:** T285 (	asks/T285-m0-hook-chan-git-ghi.md), M0
- **Developer:** OpenCode
- **Timestamp:** 2026-10-25
- **Status:** DEV_DONE (code complete, awaits @tester)

## Mục tiêu
Triển khai hook PreToolUse chặn lệnh git ghi (add/commit/reset/push --force).

## Files thay đổi
- .claude/hooks/block-git-write.ps1 (mới)
- .claude/settings.json PreToolUse (cập nhật)

## Kiểm chứng
code: Hook parse PS, settings parse JSON, thử git add bị chặn.
