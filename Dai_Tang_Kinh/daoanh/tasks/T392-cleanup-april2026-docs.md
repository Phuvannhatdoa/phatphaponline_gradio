id: T392
title: "Dọn 8 file tài liệu tháng 4/2026 → Backup-Old/"
status: in_progress
date: 2026-10-14
updated: 2026-10-15
tags: [cleanup, docs, apr-2026, reversible]
---

# T392 — Dọn 8 file tài liệu tháng 4/2026 → Backup-Old/

## Mục tiêu
Dọn 8 file `.md` gốc tại `Dai_Tang_Kinh/daoanh/` có ngày nội dung **tháng 4/2026** (tháng đầu tiên của dự án Đạo Ảnh) đã được hợp nhất vào `docs/DEV_HISTORY.md`. Move vào `visjs-app/Backup-Old/2026-10-14/` với manifest + restore script. Không xoá vĩnh viễn.

## Phạm vi
8 file .md (ngày nội dung 2026-04-10 → 04-14):
- `DILA_Structure_Report.md` (04-10)
- `FEATURE_PLAN.md` (04-10/12)
- `QA2.md` (04-12)
- `QA_REPORT_V2.md` (04-12)
- `TASK_LOG_QA1.md` (04-12)
- `TASK_LOG.md` (04-13)
- `SYSTEM_MAP.md` (04-14)
- `Timeline Tich Hop.md` (04-14)

Tổng: 8 file, 61.470 byte.

**Không đụng:** 4 file DB 5.80 GiB (tháng 10), 39 file rác T377 (tháng 8), 23 script, mọi log, `session.md` (tháng 10), 3 file tháng 5.

## Tiêu chí "vô dụng" (4/4 đạt)
1. Nội dung đã hợp nhất vào `docs/DEV_HISTORY.md:262` (liệt kê tên từng file)
2. `git grep` = 0 hit trong `app.py server.py api_*.py scripts/ tests/ package.json *.bat *.sh`
3. Không route Flask; `build_progress_data.py` chỉ quét `DOCS_DIR = docs`
4. Không link `](../X.md)` nào bị đứt

## Deliverables
- Script: `scripts/t391_backup_old.py` (--dry-run/--apply/--restore, hash guard)
- Manifest: `Backup-Old/2026-10-14/MANIFEST-2026-10-14.md` + `manifest-2026-10-14.json`
- Commit: `049804a` (chore(T392): dọn 8 file tài liệu tháng 4/2026 → Backup-Old (0 DB, reversible))
- Verify: guard PASS · route 363 · dup:ids FAIL 1 (T274, pre-existing) · progress_data.json không đổi
- Restore test: QA2.md restored → sha256 match → move back OK

## Restore
- `git revert --no-edit 049804a` (tracked files)
- `python -X utf8 Dai_Tang_Kinh/daoanh/scripts/t391_backup_old.py --restore <path>` (hash guard)

## Verify
- `guard` PASS
- route count = 363
- `dup:ids` FAIL 1 (T274, pre-existing)
- `data/progress_data.json` không đổi
- Restore test: QA2.md restored → sha256 match → move back OK

## Cảnh báo
- Move 60 KB, giải phóng 0 byte.
- `Backup-Old/` gitignored — 8 file tracked an toàn (git revert), file untracked chỉ trên đĩa.
- `SYSTEM_MAP.md` tái sinh nếu chạy `datafusion.py`.
- `.git` 3.9 GB (history có DB) → task riêng `T392`.
- T274 duplicate ID vẫn FAIL `dup:ids` (pre-existing).

## Files
- `scripts/t391_backup_old.py`
- `Backup-Old/2026-10-14/MANIFEST-2026-10-14.md`
- `Backup-Old/2026-10-14/manifest-2026-10-14.json`
- `docs/tasktodo.md` (+T392 block)
- `docs/ROLLBACK.md` (+T392 row)
- `docs/Handoff-2026-10-14-T392-cleanup-april2026.md`
- `tasks/T392-cleanup-april2026-docs.md` (this file)

## Commit
`049804a` — `chore(T392): dọn 8 file tài liệu tháng 4/2026 → Backup-Old (0 DB, reversible)`

## Revert
`git revert --no-edit 049804a` · hoặc `scripts/t391_backup_old.py --restore <path>`

## Ghi chú 2026-10-15 (revert điều phối, Decision 4)
Status trả về `in_progress`. File này trước đó mang `former_ids: [T391]` — đã xoá vì T392 (dọn 8 file tài
liệu tháng 4/2026) và T391 (thêm npm lint script đa nền tảng) là hai task khác nhau, không phải một task
đổi tên; gộp `former_ids` gây nhầm lẫn khi tra cứu. Giữ `in_progress` chờ xác nhận lại độc lập.