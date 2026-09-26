# LICENSE FIREWALL AUDIT (T78 — Phase 1 Inspect)

> **Ngày:** 2026-08-31 · **Module:** Source Governance Layer (TGS/PTDA)
> **Mục đích:** Audit toàn bộ repo TRƯỚC khi code — xác định ingestion paths, registry,
> provenance, license hiện có, và các điểm nguy cơ bypass license.

---

## A. Architecture hiện tại
- **Main Server** `app.py` (:5000) — mọi business logic + API + phục vụ `admin/` và `dashboard/`.
- **Auth Gateway** `server.py` (:5001) — chỉ login (không liên quan license).
- **2 tầng dữ liệu:**
  - **B1 (Build 1):** identity_hub / canonical mapping / authority ranking / canonical_decision / en_audit_log / conflicts — "người quyết định canonical dựa trên xếp hạng nguồn".
  - **B2 (Build 2):** entity_claims (447,885) / entity_source_ids (182,715) / evidence đa-nguồn (DILA/CBETA/MARCUS/ZQLOCAL/Wikidata) / Evidence Graph / Đạo Ảnh mapping.
- **Source Registry:** `data_sources` (13 nguồn) + `dataset_sources` (10, `usage_level` GREEN/YELLOW).
- **Adapter layer (T77):** `adapters/{base,registry}.py` — data-driven, dispatch theo `data_sources`.

## B. B1 components
- `entity_hub` (167,006), `entity_claims`, `entity_source_ids`, `canonical_decision` (2),
  `en_audit_log` (2), `conflicts` (0), `source_authority` ranking (T68), `resolve_canonical` (T68).

## C. B2 components
- Đa-nguồn evidence: DILA 293,177 / CBETA 13,933 / MARCUS 22,332 / ZQLOCAL 118,295 / Wikidata 148 claims.
- PROVENANCE wire (T69): entity_claims gắn source_id/authority_role/confidence/verification_status.
- B2 Real Data Acceptance (T76) verdict PARTIAL.

## D. Existing source registry
- `data_sources` (13 rows) — có `source_id, source_code, source_name, source_type, authority_scope,
  license_note, active, created_at` + T77 metadata (source_version, adapter_version, capabilities,
  enabled, license_note→legal hint, attribution_required, redistribution_allowed, commercial_use, api_terms).
- `dataset_sources` (10) — `usage_level` (GREEN/YELLOW), `license`, `attribution_text`.

## E. Existing provenance
- `entity_claims.*` — source_id + authority_role + confidence + verification_status.
- `entity_source_ids.*` — match_status, confidence, verified, verification_note, source_url.
- CHƯA có: content_hash / commit_sha / retrieved_at bắt buộc trên mọi claims (chỉ có ở wire tầng T69).

## F. Existing license handling
- Chỉ ghi chú `license_note` (free-text) + `dataset_sources.usage_level`.
- **KHÔNG có:** legal_status machine, license_verified flag, SPDX, commercial/redistribution xác minh,
  software vs corpus tách bạch, freeze. → Đây là GAP chính T78 xử lý.

## G. All ingestion paths
1. `SOURCE → downloader/harvester → parser → database (entity_claims/entity_source_ids)`
   (DILA, CBETA, MARCUS, ZQLOCAL, Wikidata — B2 wire).
2. `SOURCE → API (adapter/route) → normalize → database` (các `/daoanh/api/*`, T77 adapter path).
3. `SOURCE → ETL script (scripts/*.py) → database` (T31 BGIS, T34-T38 cross-ref, T64b).
4. `SOURCE → Evidence Graph / canonical` (resolve_canonical, entity_claims).
5. `RAG/vector` — CHƯA có (không phải hiểm họa hiện tại).

## H. Các điểm nguy cơ bypass license
- **KHÔNG có LicenseGate ở bất kỳ path nào** — bất kỳ ETL/API/script nào cũng có thể INSERT claims trực tiếp.
- `data_sources.commercial_use/redistribution_allowed` mặc định (T77) = 1 cho nhiều nguồn chưa xác minh
  (BDRC id2 commercial=1 dù active=0; FoJin/CHGIS/TGAZ/SAT commercial=1 giả định) → **nguy cơ giả định quyền**.
- `license_note` là free-text, không chuẩn hóa SPDX, không gắn `license_verified`.
- Authority (`source_authority`) hiện độc lập với legal — nhưng KHÔNG có cơ chế chặn ingest khi legal chưa rõ.
- **Historical claims đã ingest** (447,885) — cần chính sách (giữ + snapshot, không freeze).

## I. Những phần CẦN sửa (T78)
- Thêm cột legal vào `data_sources` (SPDX, software/data/corpus license, verified, terms_status,
  version_policy, integration_mode, legal_status, freeze_reason, legal_status_at_ingest, repository_url).
- Tạo `gate/` (LicenseGate + ProvenanceGate + status machine + analyzer).
- Hook gate vào `adapters/registry.dispatch` (không bypass).
- Routes `source-check` + `source-add` + page `source_check.html` + menu.
- Data-fix additive (BDRC/FoJin/CHGIS/TGAZ... → UNKNOWN).

## J. Những phần KHÔNG được sửa (bảo vệ B1/B2)
- `entity_hub`, `entity_claims`, `entity_source_ids`, `places`, `people` — KHÔNG đổi ID/dữ liệu.
- `source_authority` ranking hiện tại — chỉ ghi chú, không đổi giá trị.
- `resolve_canonical` / canonical ID architecture — giữ nguyên.
- `dataset_sources` rows hiện có — không xoá.
- `app.py` routes hiện có (chỉ ADD 2 route), `server.py`, `search.js`, `thientong.py`.
- File phiên song song (translation_*, T73/T75, submodule dila_import, agents/README).
