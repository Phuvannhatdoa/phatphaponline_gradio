# Session: 2026-09-15 T139 — Zen Lineage Gateway (Source Registry + Staging ETL)

## Mục tiêu
Triển khai Gateway cho Zen Lineage theo T137 audit (CONDITIONAL GO, import BLOCKED
chờ license): (1) Phase 0 — đăng ký nguồn trong `data_sources`/`source_authority`
đúng T131/T132, (2) Phase 2 — ETL staging an toàn license-gated, dry-run verify
counts, không ingest production.

## Kết quả thật

| Chỉ số | Giá trị |
|---|---|
| `POST /daoanh/api/admin/source-add` | ✓ http 200 → `data_sources` source_id=14 `ZENLINEAGE`: BLOCKED/AUDITING/license_verified=0 |
| SQL additive (Phase 0) | ✓ `source_version='ec8357ed'` + `source_authority` ZENLINEAGE score=50 order=13 implemented=0 + en_audit_log 2 dòng |
| `scripts/etl_zenlineage_stage.py` (mới) | ✓ py_compile OK; `--dry-run` PASS; `--apply` BỊ CHẶN (gate = data_sources.integration_mode); `--revert` no-op an toàn |
| Dry-run validate counts | ✓ **556 masters / 578 transmissions / 25 schools / 8,684 citations / 206 sources — 5/5 khớp audit** |
| Staging SQL (DB-in-memory) | ✓ 556 master + 578 transmission; tier A194/B342/C25/D17 khớp §5 audit |
| Input channel | ✓ ưu tiên `%TEMP%\opencode\zenlineage_t137\zen.db` (T137 dựng @ec8357ed) — không cần npm/network |
| `docs/ZEN_LINEAGE_INTEGRATION_AUDIT_V1.md` §14 | ✓ ghi trạng thái T139 + gate mở license |
| `tasks/T139-zen-lineage-gateway.md` (mới) | ✓ plan/verify/rollback |
| `docs/tasktodo.md` | T139 ACTIVE top |
| `docs/ROLLBACK.md` | row T139 commit hash |

## Files changed
- `scripts/etl_zenlineage_stage.py` (mới)
- `docs/ZEN_LINEAGE_INTEGRATION_AUDIT_V1.md` (§14, sửa §14 sau §13)
- `tasks/T139-zen-lineage-gateway.md` (mới)
- `docs/tasktodo.md` (T139 ACTIVE)
- `docs/ROLLBACK.md` (row T139)
- `data/progress_data.json` (dashboard regen)

## Design decision
- **License gate = SSOT** đọc từ `data_sources.integration_mode` mỗi lần `--apply`
  (không hardcode trong script): admin chỉ cần flip 1 dòng DB, không sửa code.
- Zen Lineage **cùng chiều teacher→student với Marcus** → khi license mở + ứng dụng sẽ
  corroborate L2 tự nhiên (khác DILA — ngược chiều, luôn direction_mismatch).
- `source_authority` ZENLINEAGE implemented=0 từ đầu → badge/score chỉ hiển thị khi
  thực sự ingest (Không được tự nhận quyền hạn trước HITL).

## Rollback
- Phase 0 DB: DELETE data_sources + source_authority ZENLINEAGE (+ en_audit_log).
- Phase 2: `git revert 74a5741` · DB (nếu đã apply): `python scripts/etl_zenlineage_stage.py --revert`.

## Ghi chú
- Static export `public/api/masters.json` (465 masters) là publish-subset KHÔNG đủ cho
  dry-run counts (thiếu tier) — script ưu tiên zen.db đầy đủ; kênh tĩnh chỉ fallback.
- `--apply` hiện CHẶN đúng; mở license: `UPDATE data_sources SET integration_mode='INGEST' WHERE source_code='ZENLINEAGE'`.
- Next (chờ admin): quyết định license → `--apply` → HITL M3/M4 → assertions ZENLINEAGE.