---
id: T387
title: "Backup DB bằng SQLite backup API; sync VPS upload tên mới + kiểm + swap nguyên tử"
status: pending
created: 2026-10-13
updated: 2026-10-13
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

- [ ] Sao lưu các script sẽ sửa
- [ ] Viết `db_safe_backup.py` + test trên DB tạm WAL
- [ ] Chuyển backup_db_daily.py sang helper
- [ ] Chuyển 6 script còn lại; thêm cờ an toàn cho restore
- [ ] Viết lại bước 2 + 3 của sync_to_vps.ps1 (upload tên mới, kiểm, swap, restart có điều kiện)
- [ ] Commit riêng `T387: …`
- [ ] daoanh-qa kiểm độc lập
- [ ] Admin xác nhận DONE
