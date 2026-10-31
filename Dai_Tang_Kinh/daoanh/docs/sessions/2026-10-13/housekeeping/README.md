# Session 2026-10-13 — Housekeeping T374–T378

Phiên Claude Code (Remote Control từ dự án PPOL), Admin duyệt 5 việc qua chat. Bàn giao chi tiết:
[`docs/Handoff-2026-10-13-housekeeping.md`](../../../Handoff-2026-10-13-housekeeping.md).

## Mô tả ngắn

| Task | Việc | Trạng thái file | Commit |
|---|---|---|---|
| (đăng ký) | 5 task file + 5 dòng tasktodo | xong | `<sha_REG>` |
| T374 | git health + `docs/process/REVERT_ONE_FIX.md` + mục trỏ AGENTS/CLAUDE | xong, **phần AGENTS/CLAUDE mất do sự cố — chạy lại bằng reapply** | `<sha_T374>` |
| T375 | 8/9 ID trùng: 13 bản cũ → `_archive/2026-10-13-dup-ids/` | xong (T274 chờ Admin) | `<sha_T375>` |
| T376 | 74 mục DONE → `docs/archive/tasktodo-done-2026.md` | xong, **tasktodo.md mất do sự cố — chạy lại bằng reapply** | `a4397c2a` + `45b2b5ec` |
| T377 | 60 file gốc → `_archive/2026-10-13-root-cleanup/` | xong | `<sha_T377>` |
| T378 | 5 route zenlineage → `api_zenlineage.py` | xong, **app.py mất do sự cố — chạy lại bằng reapply** | `<sha_T378>` |

## Sự cố 12:57–13:00

Phiên khác chuyển worktree dùng chung sang nhánh orphan `data-authority-lightweight` (7f4e654) ⇒ mọi file tracked
của master biến khỏi đĩa. Xem Handoff mục 4.

## File trong thư mục này

| File | Vai trò |
|---|---|
| `commit_plan.sh` | Commit từng mục (pathspec, kiểm staged, tự điền SHA) — chạy sau khi khôi phục + reapply |
| `reapply_after_restore.py` | Áp dụng lại T374/T376/T378 + bỏ bản trùng T375/T377 sau `checkout master` (idempotent) |
| `t375_archive_dup_ids.py`, `t377_root_cleanup.py`, `t378_extract_zenlineage.py` | Script từng mục (có `--restore` với T375/T377) |
| `*.bak-before-T37x` | Bản sao trước khi sửa |
| `dup-ids-*.log`, `build_progress_*.log`, `progress_counts_*.txt`, `t376-*.log`, `t377-apply.log`, `t378-*` | Bằng chứng trước/sau |
| `final-*.log` | guard / dup:ids / build / npm test cuối phiên (trước sự cố) |

## Cách chạy / kiểm

```bash
# từ daoanh/ (sau khi worktree về master)
python -X utf8 docs/sessions/2026-10-13/housekeeping/reapply_after_restore.py --check
python -X utf8 docs/sessions/2026-10-13/housekeeping/reapply_after_restore.py --apply
npm run guard && npm run dup:ids; python -X utf8 scripts/build_progress_data.py
# từ visjs-app/
bash Dai_Tang_Kinh/daoanh/docs/sessions/2026-10-13/housekeeping/commit_plan.sh
```
