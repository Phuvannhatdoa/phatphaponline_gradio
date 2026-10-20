# Session 2026-09-14 — T132 B2.5 REFINE: Trusted Source Registry + Legal/Capability Contract (conformance)

**Task:** `tasks/T132-b25-trusted-source-conformance.md` | **Status:** audit xong, đề xuất phê chuẩn, PLANNED (phụ thuộc T131)
**Ngày:** 2026-09-14 | **Phạm vi:** data_sources +7 cột additive · entity_claims +3 cột · gate helpers · adapters/base · conflict_recorder · docs conformance + EVIDENCE_GRAPH_CONTRACT.md · tests §13 A–J

## Bối cảnh
Admin gửi spec B2.5 (Trusted Source Registry + Legal/Capability Contract) yêu cầu verify. Verdict: **~75–80% đã tồn tại** — implement literal tạo `trusted_sources` + adapter mới + 5 docs = tự duplicate (§0/§15). Chuyển thành conformance map-lên-hệ-có-sẵn.

## Audit kết quả (verified 2026-09-14)
| Spec | Existing thật |
|---|---|
| §2 registry | `data_sources` 13 rows × 40+ cột + `source_authority` 13 rows (authority_score/precedence_order/implemented): DILA 100, CBETA 80, SAT 75, MARCUS 60, ZQLOCAL 50, CHGIS 58, FoJin 40, Wikidata 25… |
| §3 usage_level | dataset_sources.usage_level GREEN/YELLOW; legal_status chain (≈RED=BLOCKED/FROZEN) |
| §4 authority role | entity_claims.authority_role (PRIMARY 447k, CORROBORATING 148); data_sources.authority_scope; THIẾU role-list per-source |
| §5 capability | data_sources.capabilities JSON (DILA=["search","resolve","coordinate"], CBETA=["search","text_evidence"], MARCUS=["search","network_evidence"], ZQLOCAL=["local","name_vi"], Wikidata=["search","external_id"]; 8 nguồn khác []) |
| §6 adapter | adapters/base.py SourceAdapter (search/resolve/get_provenance/normalize/health_check/describe) + ExtractedEvidence (≥9 field) |
| §7 evidence | entity_claims 447,885: claim_id/entity_id/source_id/claim_type/subject/predicate/object_text/source_record_id/source_reference/source_url/confidence/retrieved_at/verification_status/assertion_level/authority_role — THIẾU license/usage_level/source_version |
| §8 authority | source_authority score + entity_claims.authority_role; evidence đối nghịch KHÔNG overwrite (DILA-CBETA-MARCUS-ZQLOCAL mỗi source là bản ghi riêng) |
| §9 conflict | `conflicts`(0) + `conflict_pending`(0) schema §9 đúng (entity_ref/field/value_a/b/source_a/b/authority_a/b/status/resolved_*) + lineage_conflicts_v2 (40,327, person) |
| §10 pipeline | SOURCE_ONBOARDING.md + admin/source_check.html (thêm→AUDITING) |
| §11 firewall | gate/license.py LicenseGate + status.py LegalStatus (can_ingest/can_reference, DEFAULT DENY, CODE≠DATA) |
| §12 versioning | data_sources.source_version/version_policy/last_sync/last_verified + ProvenanceGate pin (chặn 'latest') |
| §15 docs | CÓ sẵn: SOURCE_REGISTRY.md, SOURCE_INTEGRATION_POLICY/ARCHITECTURE.md, LICENSE_FIREWALL.md(+AUDIT/TEST_REPORT), PROVENANCE_POLICY.md, SOURCE_AUTHORITY_MATRIX.md, BUILD1_AUDIT.md, build1_frozen_contract.md — chỉ EVIDENCE_GRAPH_CONTRACT.md thiếu |

## Kế hoạch (task T132: 8 pha)
P1 +7 cột additive data_sources + backfill đã-verify (không bịa) → P2 gate can_display/can_quote (sau T131) → P3 adapter lookup_entity/get_identifier/get_license + ExtractedEvidence +3 field → P4 entity_claims +3 cột + EVIDENCE_GRAPH_CONTRACT.md → P5 conflict_recorder + seed nhỏ places needs_review → P6 4 doc conformance THIN → P7 tests §13 A–J (5P/5Pl/5T/3Time thật) → P8 backups/docs/dashboard. KHÔNG: trusted_sources mới, fake data, ALTER destructive, duplicate docs, sửa canonical/DILA IDs/endpoints/frontend.

## Trạng thái
- [x] Audit DB + code (bảng trên) + verify source_authority, entity_claims, conflict tables, capabilities.
- [x] Task file + tasktodo T132 + session doc.
- [ ] P1–P8 (sau T131).

## Rollback
- Additive/null-safe; chạy migration trên DB copy trước; backup `data/lineage_backup_t132.db` + file .bak-t132. Real git index không đụng (temp-index b4_commit.py).