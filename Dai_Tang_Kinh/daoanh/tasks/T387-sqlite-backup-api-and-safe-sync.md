---
id: T387
title: "Backup DB bằng SQLite backup API; sync VPS upload tên mới + kiểm + swap nguyên tử"
status: done
created: 2026-10-13
updated: 2026-10-25
owner: code (Hermes giao)
parent: T382
module: Hạ tầng / Docs
priority: high
depends_on: []
dispatch: approved
plan_approved_at: "2026-10-13 (Admin phê chuẩn đề xuất ARCHITECTURE-REVIEW-2026-10-13-VERIFY.md, bước 4)"
done_when: >
  (1) Có helper dùng chung `scripts/db_safe_backup.py` (`backup_to(path)` dùng `sqlite3.Connection.backup()`, sau đó
  `PRAGMA quick_check` trên bản sao, ghi sha256 + kích thước vào file `.manifest.json` cạnh bản sao).
  (2) `scripts/backup_db_daily.py` dùng helper này thay `shutil.copy2` (ưu tiên vì chạy mỗi ngày).
  (3) Các script copy/restore DB thô (`etl_entity_claims.py:86`, `cbeta_build_text_passages.py:191`, `bgis_spatial_join.py:264`,
  `build3_license_firewall.py:156,235`, `build3_source_registry_extend.py:121,199`) chuyển sang helper; restore bằng copy đè
  DB chỉ cho phép khi có cờ `--i-know-server-is-stopped`.
  (4) `sync_to_vps.ps1`: tạo bản sao bằng backup API (không đọc file live) → upload tên `lineage.db.incoming-<ts>` → trên VPS
  kiểm sha256 + `quick_check` → `mv` nguyên tử thay `lineage.db` → restart CHỈ khi các bước trên thành công → health check API.
  Upload thất bại ⇒ không restart.
  (5) Test helper trên DB tạm (WAL mode, có ghi dở) ⇒ bản sao toàn vẹn. Không chạy sync thật, không SSH.
  (6) Commit riêng tiền tố T387; Admin xác nhận DONE.
revert: >
  git revert --no-edit <sha_T387>. Bản sao các script sửa vào docs/sessions/<ngày>/*.bak-before-T387.
outcome: >
  2026-10-13: tạo task, chưa làm.
  2026-10-25: đã hoàn tất code (chưa commit, chờ QA + Admin DONE).
  (1) scripts/db_safe_backup.py: backup_to() + verify_backup() (header + PRAGMA quick_check) +
  restore_from() có cổng --i-know-server-is-stopped (từ chối copy đè, xoá -wal/-shm sau restore) +
  prune_old_backups() sửa regex ngày (bản cũ không bao giờ khớp) + CLI exit code 0/1.
  (2) backup_db_daily.py: dùng helper; SỬA BUG đường dẫn (trước đây truyền tên file thay vì
  $BACKUPS_DIR/… nên luôn báo "Backup file not created" và exit 1).
  (3) 6 script: build3_source_registry_extend.py + build3_license_firewall.py (--undo gọi
  restore_from, thêm cờ; sửa dry-run cũ ghi đè lên chính bản backup), etl_entity_claims.py,
  cbeta_build_text_passages.py, bgis_spatial_join.py (fallback copy chỉ khi có cờ),
  backup_db_daily.py.
  (4) sync_to_vps.ps1: snapshot bằng backup API → upload lineage.db.incoming-<ts> → verify
  sha256 + quick_check trên VPS → mv nguyên tử → restart CHỈ khi swap OK → health check
  /api/health; upload/verify fail ⇒ không restart, xoá file .incoming.
  (5) tests/test_t387_db_safe_backup.py: 10 test (WAL chưa checkpoint vẫn đủ dòng, verify,
  manifest, prune, restore từ chối/cho phép) — 10 passed. Không chạy sync thật, không SSH.
  2026-10-25: CHƯA commit (chờ Admin).
---

# T387 — Backup/sync SQLite an toàn

## Mục tiêu

DB chạy WAL (`PRAGMA journal_mode = wal`). Copy file thô có thể thiếu dữ liệu trong `-wal`; `sync_to_vps.ps1` dùng
`sftp put -a` ghi thẳng lên `lineage.db` production đang chạy và restart kể cả khi upload thất bại.
Bằng chứng: `docs/reports/ARCHITECTURE-REVIEW-2026-10-13-VERIFY.md` (P0-4, P1-4, C4).

## Phạm vi

Được sửa: các script liệt kê ở done_when, `sync_to_vps.ps1`, tạo `scripts/db_safe_backup.py` + `tests/test_t387_db_safe_backup.py`.
Cấm: chạy backup/restore trên `data/lineage.db` thật (trừ đọc), chạy sync, SSH VPS, deploy, push.

## Các bước

- [x] Sao lưu các script sẽ sửa (git có sẵn; chưa commit nên revert bằng `git checkout --`)
- [x] Viết `db_safe_backup.py` + test trên DB tạm WAL
- [x] Chuyển backup_db_daily.py sang helper
- [x] Chuyển 6 script còn lại; thêm cờ an toàn cho restore
- [x] Viết lại bước 2 + 3 của sync_to_vps.ps1 (upload tên mới, kiểm, swap, restart có điều kiện)
- [x] Commit riêng `T387: …` (Admin xác nhận DONE 2026-10-25; đã commit 2026-10-26 — xem `git log --grep T387`. Route UI `/daoanh/api/admin/backup` trong app.py là file chung nhiều phiên — chưa commit, nộp riêng khi khoá lô UI.)
- [x] daoanh-qa kiểm độc lập (DEV-REPORT: docs/sessions/2026-10-25/T387/DEV-REPORT.md)
- [x] Admin xác nhận DONE (2026-10-25)
