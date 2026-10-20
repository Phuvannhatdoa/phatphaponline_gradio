# Session 2026-09-14 — T131 B2.1 REFINE: Source Governance + Compliance Gate + Adapter (map-lên-hệ-có-sẵn)

**Task:** `tasks/T131-b21-source-governance-refine.md` | **Status:** audit xong, đề xuất phê chuẩn, CHỜ implement
**Ngày:** 2026-09-14 | **Phạm vi:** scripts (registry mới) + gate/license,status (additive) + adapters/base (default methods) + tests + package.json

## Bối cảnh
Admin gửi spec B2.1 (source governance + compliance gate + extensible adapter core) yêu cầu verify. Audit thật (DB + code) → kết luận spec **không khớp logic hiện tại (~70% đã tồn tại)**:

## Audit kết quả (đã verify)
| Thành phần | Hiện trạng thật |
|---|---|
| Source Registry | `data_sources` 13 rows × 40+ cột (legal_status, data_license_status, integration_mode, license_verified=0 hết, version_policy…) — spec §4 target field gần đủ |
| Legacy | `dataset_sources` 10 rows × 8 cột (license, usage_level=GREEN/YELLOW…) — KHÔNG phải registry tương lai |
| Compliance gate | `gate/license.py` LicenseGate.checkSourcePermission (T78, commit 389f99b) — deterministic, rule-based, tách software/corpus |
| Status machine | `gate/status.py` LegalStatus: UNKNOWN/AUDITING/VERIFIED/APPROVED/ACTIVE + UNKNOWN/REFERENCE_ONLY/BLOCKED/FROZEN; KHÔNG default ACTIVE |
| Provenance | `gate/provenance.py` ProvenanceGate (bắt buộc 8 fields, chặn 'latest' pin) + `ExtractedEvidence` |
| Adapter core | `adapters/base.py` SourceAdapter (search/resolve/get_provenance/normalize/health_check/describe) + `adapters/registry.py` (data-driven dispatch, firewall) + bdrc |
| Endpoints §14 | ĐỦ 6/6 (places_pending 2070, ai_judge 2186, translate_location 7567, namevi-map-places/save 8937, transliterate 9740, search 9859) |
| Frontend badge | places.html licenseBlock (source/license/note) + admin/source_check.html + placevn.html T67 |
| Tests | test_license_firewall.py (16 temp) + test_real_data_license.py (6 real-copy) — **KHÔNG chạy trong pipeline** (`npm test`=placeholder) |

## Các GAP thật (đã liệt kê trong task Pha 1–5)
1. Gate: thêm op METADATA_READ/CONTENT_READ/CONTENT_STORE/DERIVED_DATA/EXPORT + `usage_level` + `restrictions[]` (derived).
2. Registry: +13 nguồn missing (DDBC, VRI/Tipitaka, THL, Treasury of Lives, BuddhaNexus, PTS, IDP, GRETIL, DSBC, OCBS, BGIS, MITRA, READ) → BLOCKED/chưa verify.
3. Adapter: +get_metadata/get_entity/get_evidence/get_source_version (default fallback).
4. Tests A–L (DB-copy) + `test:gov` gắn pipeline.
5. usage_level derived view cho data_sources.

## Trạng thái
- [x] Audit DB + code (bảng trên) + verify 6 endpoints + frontend badges + git (gate/adapters committed).
- [x] Task file `tasks/T131-b21-source-governance-refine.md` + tasktodo + session doc.
- [ ] P1 script registry 13→26 (idempotent) + smoke.
- [ ] P2 gate aliases + usage_level/restrictions (additive) + unit.
- [ ] P3 adapter default methods.
- [ ] P4 test_b21_governance.py (copy DB thật) + package.json test:gov.
- [ ] P5 backups + pytest run + node --check + pipeline + dashboard regen.
- [ ] Live QA :5000 (nếu App đang chạy) — chỉ verify, không đổi contract.

## Rollback
- Mọi thay đổi additive/idempotent; backup `data/lineage_backup_t131.db` + file .bak-t131. Real git index không đụng (temp-index b4_commit.py).