
## T166 — identity schema migration (2026-10-28)

| Migration | Lệnh revert | Backup | Ngày |
|---|---|---|---|
| T166 identity migration | `python -X utf8 scripts/t166_identity_migrate.py --revert` (DROP 4 cột + index `idx_tc_identity`; dữ liệu cũ KHÔNG mất) | `Dai_Tang_Kinh/daoanh/data/backups/lineage_t166_20261028_112541.db` | 2026-10-28 |

- Lệnh apply: `python -X utf8 scripts/t166_identity_migrate.py --apply` (ADD `translation_cache.identity_status`, `translation_cache.identity_issues`, `translation_cache.identity_lock_hash`, `translation_rules.identity_lock_policy` DEFAULT `'P-PARTIAL'`, CREATE INDEX `idx_tc_identity`).
- Lệnh revert: `python -X utf8 scripts/t166_identity_migrate.py --revert`.
- Đường dẫn backup: `Dai_Tang_Kinh/daoanh/data/backups/lineage_t166_20261028_112541.db`.
- Ghi chú: additive, không mất dữ liệu cũ. Số dòng `translation_cache` (1771) và `translation_rules` (140) bằng nhau trước/sau apply. Cột mới ở các dòng cũ là NULL (legacy).
