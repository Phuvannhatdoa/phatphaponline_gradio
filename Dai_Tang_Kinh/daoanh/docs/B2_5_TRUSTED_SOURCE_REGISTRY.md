# B2.5 — Trusted Source Registry (conformance pointer)

> **T132 P6 §15** | Tạo: 2026-09-22 | Loại: conformance thin (pointer)  
> **KHÔNG duplicate nội dung** — xem file gốc bên dưới.

---

## Ánh xạ Spec B2.5 §2–§5 → Existing

| Spec | Implementation (existing) | T132 change |
|------|--------------------------|-------------|
| §2 `trusted_sources` | `data_sources` (40+ cột, 14 rows) | +7 cột additive: canonical_name/short_name/organization/origin_url/data_url/api_url/authority_roles |
| §3 usage_level | `data_sources.legal_status` (ACTIVE/REFERENCE_ONLY/BLOCKED/FROZEN) | view derived T131 P2 |
| §4 authority_role | `entity_claims.authority_role` (PRIMARY/CORROBORATING) | +`authority_roles` JSON cột |
| §5 capability | `data_sources.capabilities` (JSON, 5 nguồn đã điền) | không thay đổi |

---

## File gốc

- **Registry chính**: `docs/SOURCE_REGISTRY.md` — 14 nguồn, schema, policy thêm nguồn
- **Authority Matrix**: `docs/SOURCE_AUTHORITY_MATRIX.md` — score, tiêu chí đánh giá
- **Script build T132 P1**: `scripts/build_t132_p1_db_additive.py`
- **DB**: `data/lineage.db` → bảng `data_sources`

---

## Gaps đã vá (T132 P1)

- ✅ `canonical_name` / `short_name` / `organization` — tên chính tắc per-source (filled 14/14)
- ✅ `origin_url` / `data_url` / `api_url` — URLs đã verify từ SOURCE_AUTHORITY_MATRIX
- ✅ `authority_roles` — JSON roles per-source (IDENTITY_AUTHORITY, TEXTUAL_EVIDENCE, …)
- ✅ `entity_claims.license` / `usage_level` / `source_version` — additive NULL (REVIEW_REQUIRED)
