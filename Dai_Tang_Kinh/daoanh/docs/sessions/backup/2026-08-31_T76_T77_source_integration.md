# Session — T76 B2 Real Data Acceptance + T77 Source Registry/Adapter (2026-08-31)

**Admin phê chuẩn:** ĐỒNG Ý BUILD kế hoạch T76 + T77.
**Các quyết định khóa:**
1. **1a** — Conflict test chỉ dựa trên data thật, KHÔNG seed; nếu 0 case thật → PARTIAL + lý do.
2. **Bỏ TEST_TRUSTED_SOURCE_X** khỏi acceptance (spec cấm mock; để Build 4+ tùy chọn).
3. **G1 (T77) làm sau T76** — cô lập checksum before/after.
4. **Thêm checksum** integrity trước/sau.
5. Chỉ commit file T76/T77 (per-file add, không `add -A` — tránh cuốn thay đổi phiên khác).

---

## T76 — B2 Real Data Acceptance Test

**Verdict: PARTIAL** (10/13 PASS, 3 PARTIAL, 0 CRITICAL FAIL, regression PASS).

Key real-data findings:
- DB thật `data/lineage.db`: entity_hub=167,006; entity_claims=447,885; entity_source_ids=182,715; conflict_pending=0.
- 5 source ingested (DILA 293,177 / ZQLOCAL 118,295 / MARCUS 22,332 / CBETA 13,933 / Wikidata 148); 8 CONNECTOR_ONLY (implemented=0).
- Canonical Identity PASS: 0 canonical PLACE ngoài prefix `PL0`; DILA giữ canonical.
- Provenance PARTIAL: CBETA/MARCUS/Wikidata 100% ref+retrieved; DILA retrieved=0 (293,177); ZQLOCAL ref=0 (118,295).
- Matching PARTIAL: geo_cross_ref=181, name_vi_map_places=0 (thin).
- Conflict PARTIAL: conflict_pending=0 — không seed, không case thật.
- E2E PASS: `GET /daoanh/api/places/PL000000023255/claims` HTTP 200, resolved=181597, 38 claims, DILA trước.
- Integrity PASS: `data/t76_checksum_before.json` vs `after.json` IDENTICAL (chỉ khác timestamp) — read-only, 0 thay đổi DB.
- Regression PASS: lint/test/e2e exit 0 (lint = ESM get_format:185 false-positive).

**Reports:**
- `docs/T76_B2_REAL_DATA_ENVIRONMENT_REPORT.md`
- `docs/T76_B2_REAL_DATA_ACCEPTANCE_REPORT.md`
- `docs/T76_B2_FAILURES_AND_REMEDIATION.md`
- `data/t76_checksum_before.json`, `data/t76_checksum_after.json`

---

## T77 — Source Registry metadata + Adapter skeleton

Done (G1, build mode additively):
1. **`scripts/build3_source_registry_extend.py`** — ALTER `data_sources` +13 cột (`source_version`, `adapter_version`, `schema_version`, `last_sync`, `last_verified`, `enabled`, `health`, `capabilities`, `base_url`, `attribution_required`, `redistribution_allowed`, `commercial_use`, `api_terms`) + backfill 5 nguồn + backup `data/lineage_backup_t77.db`. Verified: idempotent, undo path OK, live API still HTTP 200 (38 claims).
2. **`adapters/base.py`** — `SourceAdapter` (ABC) + `ExtractedEvidence` (provenance chuẩn) + `to_json`.
3. **`adapters/registry.py`** — `SourceAdapterRegistry` data-driven (load từ `data_sources.capabilities`, dispatch theo source_code).
4. **`adapters/__init__.py`** — package doc.
5. **`adapters/bdrc/__init__.py`** — adapter mẫu (BDRC, health=`conector_only`).
6. Smoke test pass: registry 13 nguồn, BDRC has_adapter=True, SAT dispatch raises KeyError.
7. Docs: `docs/BUILD1_AUDIT.md`, `docs/SOURCE_INTEGRATION_ARCHITECTURE.md`, `docs/SOURCE_ONBOARDING.md`.

**Rollback:**
- DB ALTER: `python scripts/build3_source_registry_extend.py --undo` (restore `lineage_backup_t77.db`).
- Adapter/docs/tasks: git revert (atomic commit riêng, không đụng file phiên khác).

---

## File tạo/sửa (chỉ T76/T77)

**Tạo:** tasks/T76-*, tasks/T77-*, docs/T76_*.md (3), docs/BUILD1_AUDIT.md, docs/SOURCE_INTEGRATION_ARCHITECTURE.md, docs/SOURCE_ONBOARDING.md, scripts/build3_source_registry_extend.py, adapters/base.py, adapters/registry.py, adapters/__init__.py, adapters/bdrc/__init__.py, docs/sessions/2026-08-31_T76_T77_source_integration.md
**Sửa:** docs/tasktodo.md, docs/progress.md, docs/roadmap.md, dashboard/dashboard_process.html (banner ĐỒNG Ý BUILD)
**Data (git-ignored, evidence):** data/lineage.db (ALTER T77), data/t76_checksum_*.json, data/lineage_backup_t77.db

## Next

- Build 3/G2 (Build 4+): de-lock-in `entity_unified`, `_name_vi_evidence`, `geo_cross_ref`→`entity_external_ref`, gộp routes clone, wrap harvester vào adapter, skeleton TEST_TRUSTED_SOURCE_X (tùy chọn).
- Hoàn thiện Provenance DILA/ZQLOCAL + Matching + Conflict khi data thật đủ.
