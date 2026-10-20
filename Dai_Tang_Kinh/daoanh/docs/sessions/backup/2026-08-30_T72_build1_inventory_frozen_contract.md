# T72 — Build 1 Inventory + Frozen Contract (docs)

**Ngày:** 2026-08-30
**Trạng thái:** ✅ DONE (docs-only, reversible)
**Mục đích:** Chốt nền tảng cho Build 2 theo directive + hiện trạng repo: xác nhận tầng canonical entity / source identity **đã IMPLEMENTED (T23 Identity Hub)**, nên Build 2 = reuse+extend T67→T70, KHÔNG xây lại identity.

## Việc đã làm (đã verify)
- Verified hiện trạng DB/SQL:
  - `entity_hub` (167,006) — canonical entity: entity_id INT surrogate, entity_type, canonical_label='PL…', status.
  - `entity` (167,006) — dila_id, entity_id TEXT, aliases.
  - `entity_source_ids` (167,009) — source identity mapping (0 verified, match_status=candidate).
  - `entity_claims` (411,472) — 177,445 NAME / 175,441 COORDINATE / 58,586 ADMIN_UNIT; authority_role='PRIMARY' 100%; unverified 100%.
  - `canonical_decision` + `en_audit_log` — provenance, T67 done (commit a5bb07f).
  - OpenSearch / Fuseki / GraphDB: **KHÔNG có trong app daoanh** (0 refs) — search dùng SQLite FTS5. Ghi trung thực.
  - 61 route `/daoanh/api/admin/*`, 57 route `/api/*`.
- Tạo 2 tài liệu theo convention repo:
  - `docs/build1_inventory.md` — bảng Capability → file/API/table/status (chỉ ghi đã verify).
  - `docs/build1_frozen_contract.md` — BUILD 1 FROZEN: được phép consume/extend/add; không duplicate/replace/parallel identity/mapping/admin.
- Tạo task file `tasks/T72-build1-frozen-contract-inventory.md`.
- Cập nhật `docs/tasktodo.md` (T72 done) + regenerated `data/progress_data.json` (dashboard: 77 task, done=44).

## Kết luận Build 2
- **Canonical Entity + Source Identity Mapping đã IMPLEMENTED** → Build 2 KHÔNG build lại identity.
- Gap thật Build 2: **T68** (source_authority + conflict_pending + resolve_canonical) → **T69** (wire evidence đa-nguồn) → **T70** (governance).

## File thay đổi
- `docs/build1_inventory.md` (new)
- `docs/build1_frozen_contract.md` (new)
- `tasks/T72-build1-frozen-contract-inventory.md` (new)
- `docs/tasktodo.md`
- `data/progress_data.json`

## Revert
Docs-only — `git revert` commit này hoặc `git rm` 2 file; không đụng code/DB.
