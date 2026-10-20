---
id: T377
title: "Dọn thư mục gốc daoanh: chuyển file nháp/log/backup vào _archive/2026-10-13-root-cleanup/"
status: in_progress
created: 2026-10-13
updated: 2026-10-13
owner: claude-code (phiên housekeeping 2026-10-13)
plan_approved_at: "2026-10-13 (Admin duyệt qua chat)"
dispatch: approved
done_when: >
  (1) File nháp/log/backup ở gốc daoanh/ được chuyển (không xóa) vào
  _archive/2026-10-13-root-cleanup/ kèm MANIFEST.md (tên file, lý do, đường dẫn gốc).
  (2) Không chuyển file nào được code tham chiếu, file server đang ghi, .env, config.
  (3) `python -c "import app"` vẫn chạy; `npm run guard` PASS.
  (4) Commit riêng (phần file được git theo dõi), revert được bằng `git revert <sha>`.
  (5) Admin xác nhận DONE.
revert: >
  git revert --no-edit <sha_T377> cho file được git theo dõi; file không được theo dõi:
  chuyển ngược theo MANIFEST.md (cột "đường dẫn gốc").
outcome: >
  2026-10-13: Chuyển 60 file (38 git theo dõi, 22 bị .gitignore) vào _archive/2026-10-13-root-cleanup/ +
  MANIFEST.md (đường dẫn gốc, lý do, byte, sha256). Quét tham chiếu trong code: để lại fix_all.py, fix_tabs.js,
  sync_to_vps.log (có tham chiếu), log server đang ghi hôm nay, app_local_t360.* (bằng chứng T360), file chưa chắc
  (add_tasks.py, add_route.py, list_tables.py, qa_report.json, …). `npm run guard` PASS; `import app` OK.
  File gốc 186 → 126 mục. Commit: <sha_T377> (file bị ignore chỉ khôi phục bằng MANIFEST / --restore).
  Chờ daoanh-qa + Admin.
---

# T377 — Dọn thư mục gốc daoanh

## Các bước

- [x] Liệt kê file gốc, phân loại (tracked / ignored / untracked)
- [x] Grep tham chiếu trong code cho từng ứng viên
- [x] Loại file server đang ghi (log đang mở), .env, config
- [x] Chuyển vào `_archive/2026-10-13-root-cleanup/` + MANIFEST.md
- [x] Kiểm `import app` + `npm run guard`
- [ ] Commit riêng, tiền tố `T377`
- [ ] Admin xác nhận DONE
