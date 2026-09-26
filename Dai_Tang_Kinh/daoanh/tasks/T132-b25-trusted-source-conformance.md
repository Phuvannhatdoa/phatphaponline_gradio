---
id: T132
title: B2.5 REFINE: Trusted Source Registry + Legal/Capability Contract
priority: high
status: done
owner: AI Engineer (build) · Lee Tổng (phê chuẩn)
module: Governance
created: 2026-09-14
updated: 2026-09-22
depends_on: T131
---
# T132 — B2.5 REFINE: Trusted Source Registry + Legal/Capability Contract (conformance map-lên-hệ-có-sẵn)

---

## 1. Context (AO — audit thật 2026-09-14, build mode sau khi phê chuẩn)

Spec "B2.5 TRUSTED SOURCE REGISTRY + LEGAL/CAPABILITY CONTRACT" được admin gửi verify.
**Verdict: ~75–80% ĐÃ TỒN TẠI** trong Build 3 (T70/T74/T76/T77/T78/T82 + docs). Implement literal sẽ tự vi phạm §0/§15 ("KHÔNG duplicate") bằng cách tạo `trusted_sources` table + adapter interface + 5 docs TRÙNG LẶP. Phê chuẩn chuyển thành **B2.5-REFINE additive** (giống T131): **KHÔNG tạo bảng mới, KHÔNG duplicate docs, KHÔNG sửa schema đang chạy ngoài cột additive null-safe**.

### Ánh xạ §16 (B1 component → existing → reuse → gap → change) — trích yếu
| Spec | Existing (verified) | Gap | Change |
|---|---|---|---|
| §2 `trusted_sources` | `data_sources` 13 rows × 40+ cột + `source_authority` 13 rows (score/precedence/implemented) | thiếu canonical_name/short_name/organization/origin_url/data_url/api_url/authority_roles | +7 cột additive (NULL-safe) — KHÔNG bảng mới |
| §3 usage_level | dataset_sources.usage_level (GREEN/YELLOW) + legal_status chain (≈RED=BLOCKED/FROZEN) | chưa ở data_sources | dùng view derived (T131 P2) |
| §4 authority role | entity_claims.authority_role (PRIMARY 447k CORROBORATING 148…), authority_scope, score | chưa role-list per-source | `authority_roles` JSON cột |
| §5 capability | data_sources.capabilities JSON ✓ (DILA/CBETA/MARCUS/Wikidata/ZQLOCAL có, 8 nguồn khác []) | ts taxonomy tên khác | ko cần |
| §6 adapter | adapters/base.py SourceAdapter (search/resolve/get_provenance/normalize/health_check/describe) + ExtractedEvidence | thiếu get_metadata/lookup_entity/get_evidence/get_identifier/get_license/get_version + license/usage_level/source_version | T131 P3 + default methods + 3 field |
| §7 evidence graph | **entity_claims 447,885** ≈ 1:1 §7 (claim_id/entity_id/source_id/source_record_id/claim_type/subject/predicate/object_text/source_reference/source_url/confidence/retrieved_at/verification_status/assertion_level/authority_role) | thiếu license, usage_level, source_version per-claim | +3 cột additive |
| §8 authority | source_authority score + authority_role; evidence đối nghịch giữ nguyên (5 sắc claims) | fn corroboration optional | optional |
| §9 conflict | `conflicts`(0) + `conflict_pending`(0, đúng schema §9) + lineage_conflicts_v2(40,327) | chưa dùng cho places (PL…) | recorder + seed nhỏ |
| §10 pipeline 21+ | SOURCE_ONBOARDING.md + admin/source_check.html (thêm→AUDITING) | — | — |
| §11 firewall | gate/license.py + status.py (can_ingest/can_reference, DEFAULT DENY, CODE≠DATA) | can_display/can_quote chưa tên | wrapper additive (T131) |
| §12 versioning | source_version/version_policy/last_sync/last_verified + ProvenanceGate pin | per-evidence version | = gap §7 |
| §15 docs | 4/5 ĐÃ CÓ (SOURCE_REGISTRY.md, SOURCE_INTEGRATION_POLICY+ARCHITECTURE.md, LICENSE_FIREWALL.md, PROVENANCE_POLICY.md, SOURCE_AUTHORITY_MATRIX.md, BUILD1_AUDIT.md) | **CHỈ EVIDENCE_GRAPH_CONTRACT.md thiếu** | 1 doc mới + 4 conformance thin |

## 2. Pha (additive, tuân thủ §15 "không tạo trùng")

### P1 — Registry fields (spec §2, §4, §5)
- Script `scripts/build_t132_registry_fields.py` (idempotent, INSERT-safe):
  - ALTER TABLE data_sources ADD COLUMN nếu chưa có (NULL safe): `canonical_name`, `short_name`, `organization`, `origin_url`, `data_url`, `api_url`, `authority_roles` (TEXT JSON).
  - Backfill DILA/CBETA/SAT/MARCUS/ZQLOCAL/Wikidata/BDRC/CHGIS/FoJin/Kanripo/SuttaCentral/84000/TGAZ với dữ liệu **đã verify trong docs SOURCE_REGISTRY/SOURCE_AUTHORITY_MATRIX** (base_url→api_url/data_url, organization đã biết) — KHÔNG bịa; các field không chắc chắn để NULL.
  - `authority_roles` JSON theo §4 (DILA=IDENTITY_AUTHORITY,PLACE_AUTHORITY,PERSON_AUTHORITY,TIME_AUTHORITY,CATALOG_AUTHORITY; CBETA=TEXTUAL_EVIDENCE; MARCUS=SECONDARY_REFERENCE,LEXICON; CHGIS/GEOGRAPHIC+HISTORICAL; Wikidata=INTEROPERABILITY,SECONDARY_REFERENCE; voilà từ docs có sẵn — ghi chú nguồn trong note).
- 0 destructive; 13 dòng cũ giữ nguyên.

### P2 — Policy helpers (spec §11) — sau T131
- `gate/license.py`: thêm `can_display(source_id)` (=metadata/citation check) + `can_quote(source_id)` (=derived-data check) làm wrapper gọi checkSourcePermission — additive. KHÔNG hard-code tên nguồn.

### P3 — Adapter + normalized object (spec §6)
- `adapters/base.py` (kéo theo T131 P3): thêm `lookup_entity(record_id)` (=resolve alias), `get_identifier(record_id)` (trả source-specific id), `get_license()` (đọc từ data_sources qua source_id) — default fallback, không phá bdrc.
- `ExtractedEvidence`: thêm field `license`, `license_status`, `source_version` (Optional, default None) — to_dict tự cập nhật.

### P4 — Evidence contract (spec §7, §12)
- Script `scripts/build_t132_evidence_license_columns.py` (idempotent):
  - ALTER TABLE entity_claims ADD COLUMN (NULL-safe): `license`, `usage_level`, `source_version`.
  - **KHÔNG backfill đại trà tự đoán**; chỉ backfill deterministic qua join data_sources khi source duy nhất + legal đã verify (hiện license_verified=0 hết → để NULL = REVIEW_REQUIRED, đúng §5). Ghi chú trong doc.
- Tạo **`docs/EVIDENCE_GRAPH_CONTRACT.md`** (doc MỚI thật): map entity_claims ↔ §7 fields, quy tắc không overwrite, versioning, cách truy ngược → source.

### P5 — Conflict recorder cho places (spec §9)
- Module `gate/conflict_recorder.py` (additive): `record_conflict(entity_ref, field, value_a, value_b, source_a, source_b)` → INSERT OR IGNORE into `conflict_pending` (đã có đúng schema). Deterministic, human-in-loop qua `status/resolved_*`.
- Seed NHỎ data thật: sample từ `namevi_map_places.needs_review=1` (place mapping chờ duyệt thật hiện có) — ghi nguồn; KHÔNG fake. Số lượng giới hạn (VD 20) + note.
- Lineage conflicts giữ nguyên lineage_conflicts_v2 (không đụng).

### P6 — Docs conformance (spec §15)
- Tạo 4 doc THIN (pointer ↔ existing, không duplicate nội dung):
  - `docs/B2_5_TRUSTED_SOURCE_REGISTRY.md` → trỏ SOURCE_REGISTRY.md + data_sources.
  - `docs/B1_ALREADY_EXISTS.md` → trỏ BUILD1_AUDIT.md + build1_frozen_contract.md + build1_inventory.md.
  - `docs/SOURCE_INTEGRATION_CONTRACT.md` → trỏ SOURCE_INTEGRATION_POLICY.md + SOURCE_INTEGRATION_ARCHITECTURE.md.
  - `docs/LICENSE_POLICY.md` → trỏ LICENSE_FIREWALL.md + LICENSE_FIREWALL_AUDIT.md.
  - Mỗi doc ghi rõ: bảng ánh xạ spec § ↔ file hiện hữu + gaps đã vá (P1–P5).

### P7 — Tests (spec §13, A–J) — sau T131
- `tests/test_b25_authority_contract.py` (DB-copy thật, 0 fake):
  - Chọn real data: 5 Person (A001xxx), 5 Place (PL…), 5 Text (cbeta_ref), 3 Time — từ entities thật có sẵn.
  - Case A DILA-only / B DILA+Marcus / C DILA+CHGIS(nếu adapter) / D conflicting evidence (dùng lineage_conflicts_v2 hay entity_claims 2 source) / E missing license (license_verified=0 → không GREEN) / F unknown source (chặn) / G duplicate source record / H same entity diff labels (namevi_map_places) / I source unavailable (adapter health unknown) / J source version changed.
  - Assert: RED không vào payload; YELLOW không thành canonical; evidence không overwrite (2 bản ghi riêng); conflict ghi vào conflict_pending.
- package.json: T131 đã thêm `test:gov` → include test_b25.

### P8 — Backups + docs + dashboard
- Snapshot: `[System.IO.File]::Copy` gate/license.py, gate/base.py, adapters/base.py, app.py → `docs/sessions/*.bak-t132-...`; DB: `data/lineage_backup_t132.db`. Chạy migration trên DB temp copy trước khi áp DB thật (nếu có thể) + smoke.
- Session doc `docs/sessions/2026-09-14_t132-b25-trusted-source-conformance.md`; tasktodo; `python -X utf8 scripts/build_progress_data.py`.
- Chỉ commit qua temp-index khi user yêu cầu.

## 3. Non-goals (KHÔNG làm)
- KHÔNG tạo `trusted_sources` table (data_sources là registry).
- KHÔNG sửa legal engine core / Fusion / entity_hub / DILA IDs / canonical.
- KHÔNG sửa dataset_sources legacy; KHÔNG rewrite placevn.html/places.html layout; KHÔNG đổi endpoints.
- KHÔNG mock/fake; KHÔNG assign license từ "public GitHub"; KHÔNG backfill license tự đoán.
- KHÔNG duplicate 4 docs đã tồn tại (chỉ conformance thin).

## 4. Acceptance (spec §14 checklist immune)
- B1 không phá ✓; dataset_sources nguyên ✓; DILA/Marcus provenance trả đúng (ai_judge test) ✓; license không overwrite ✓ (test K-style); code/data license phân biệt ✓ (đã có 4 cột license); RED chặn production (test E/I + gate) ✓(sau T131); YELLOW không tự canonical ✓; evidence nhiều nguồn không overwrite ✓ (entity_claims giữ riêng); conflict lưu riêng ✓ (conflict_pending); source 21 thêm không sửa core ✓; adapter contract ✓; source version lưu ✓ (data_sources + entity_claims mới); provenance truy ngược ✓; placevn.html/API/GraphDB không regression (node --check + e2e + endpoint smoke); tester PASS (pipeline).

## 5. Risks
- ALTER TABLE trên DB thật — chạy trước trên COPY temp (script hỗ trợ `--copy`), rồi thật. Idempotent, NULL-safe, 0 backfill dữ liệu.
- pytest chưa có trong npm env — kiểm tra trước; fallback unittest runner.
- e2e:runtime EPERM pre-existing — ghi nhận trong report.
- Overlap T131 (gate/adapters): T132 status=planned, implement SAU T131 hoặc gộp chung 1 đợt integration.

## 6. Rollback
- Mọi thay đổi additive; revert = xóa cột mới (nếu cần) hoặc restore backup; conflict_pending seed có thể DELETE nguồn seed (ghi rõ ids). Real git index không đụng (temp-index).

## 7. Closure 2026-09-22 (bổ sung late)
- **P5 seed THẬT đã ghi**: `conflict_pending` 0 → **20 rows** từ `namevi_map_places.needs_review=1` (18,165 ứng viên, chọn 20 deterministic đầu theo id; provenance đầy đủ trong cột `notes` — ADD COLUMN TEXT additive; nguồn value_a = DILA name_zh, value_b = ZQLOCAL auto-transliterate chờ duyệt; **0 fake**). Script: `scripts/seed_t132_conflict_pending.py` (`--stats / --apply [--limit] / --revert`, idempotent — vòng đời revert→re-apply 20→0→20 đã validate).
- **P8 backups (pre-seed)**: 4 `.bak-t132-20260922` (gate/license, gate/status, adapters/base, app) trong `docs/sessions/` + `data/lineage_backup_t132.db` 1,372MB (sqlite online backup, gitignored local).
- **Pipeline 2026-09-22**: guard/lint/test/uat(3-3)/compliance(7-2 pre-existing metric)/gov(**17-17**)/e2e ✅; `e2e:runtime` ❌ EPERM chỉ do lock `.last-run.json` (môi trường, pre-existing).
- Commits: `7832f26` (P2-P8 core) · `e4b2664` (docs addendum) · 3 commit riêng cho seed/P8/closure (revert riêng từng pha).
- Chú thích: `app.py` guard `__main__` thuộc `a1c0c16 fix: BUG-023` (agent khác) — không phải T132.