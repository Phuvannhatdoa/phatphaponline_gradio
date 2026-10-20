# EVIDENCE_GRAPH_CONTRACT.md

> **T132 P4 §7 §12** — Hợp đồng schema Evidence Graph (`entity_claims`)  
> **Ngày tạo:** 2026-09-22 | **Trạng thái:** CANONICAL

---

## 1. Mục đích

File này ánh xạ các trường của bảng `entity_claims` sang spec §7 (Evidence Graph) và §12 (Versioning), mô tả quy tắc không overwrite, cách truy ngược nguồn, và policy backfill.

---

## 2. Ánh xạ entity_claims ↔ Spec §7

| Cột DB | Spec §7 | Ghi chú |
|--------|---------|---------|
| `claim_id` | evidence_id | UUID / hash tự sinh |
| `entity_id` | subject | canonical ID (PL…, A…) |
| `source_id` | source | FK → data_sources.source_id |
| `source_record_id` | provenance.record_id | ID gốc trong nguồn (vd DILA place ID) |
| `claim_type` | predicate_type | EXTERNAL_ID / NAME / GEOGRAPHY / TEXTUAL / TIME / … |
| `subject` | subject_alt | thường = entity_id |
| `predicate` | predicate | tên trường (name_zh, coordinates, …) |
| `object_text` | object | giá trị thực tế |
| `source_reference` | citation | ref cụ thể trong nguồn (CBETA sigla, page) |
| `source_url` | source_url | URL tham chiếu nguồn |
| `confidence` | confidence | 0.0–1.0 |
| `retrieved_at` | provenance.timestamp | ISO-8601 thời điểm lấy |
| `verification_status` | status | unverified / verified / disputed / needs_review |
| `assertion_level` | level | claim / assertion / canonical |
| `authority_role` | source_role | PRIMARY / CORROBORATING |
| `license` *(T132 P1)* | license | SPDX/key license của evidence (NULL = REVIEW_REQUIRED) |
| `usage_level` *(T132 P1)* | usage_level | GREEN / YELLOW / RED / REVIEW_REQUIRED |
| `source_version` *(T132 P1)* | provenance.version | version nguồn lúc lấy evidence |

---

## 3. Quy tắc KHÔNG overwrite (§12)

1. **Mỗi source → 1 row riêng**: Nếu DILA và MARCUS cùng có giá trị `name_zh` cho một entity → 2 rows, KHÔNG gộp.
2. **verification_status chỉ tăng**: unverified → verified / disputed / needs_review (không lùi).
3. **license/usage_level backfill**: chỉ SET khi `data_sources.license_verified=1` cho nguồn đó — hiện tất cả = NULL (REVIEW_REQUIRED) vì license_verified=0.
4. **Không tự xóa**: nếu evidence lỗi thời → đổi `verification_status='disputed'` + ghi `notes`.

---

## 4. Policy backfill T132 (hiện tại)

```sql
-- Hiện tại: license_verified=0 cho tất cả nguồn → license/usage_level = NULL
SELECT source_id, source_code, license_verified FROM data_sources;
-- Khi admin xác nhận 1 nguồn (vd DILA license CC-BY-NC-SA):
--   UPDATE data_sources SET license_verified=1, data_license='CC-BY-NC-SA' WHERE source_code='DILA';
--   UPDATE entity_claims SET license='CC-BY-NC-SA', usage_level='YELLOW' WHERE source_id=1 AND license IS NULL;
```

---

## 5. Truy ngược evidence (§12 versioning)

```python
# Từ entity_id → list evidence với provenance đầy đủ:
SELECT ec.*, ds.source_code, ds.source_version, ds.last_verified
FROM entity_claims ec
JOIN data_sources ds ON ds.source_id = ec.source_id
WHERE ec.entity_id = ?
ORDER BY ec.confidence DESC, ec.verification_status DESC;
```

Trường `source_version` trong `entity_claims` (T132 P1) = version tại thời điểm lấy evidence. So sánh với `data_sources.source_version` để phát hiện staleness.

---

## 6. Xem thêm

- `data_sources` schema: `docs/SOURCE_REGISTRY.md`
- License policy: `docs/LICENSE_FIREWALL.md`
- Source authority matrix: `docs/SOURCE_AUTHORITY_MATRIX.md`
- Conflict engine: `docs/CONFLICT_ENGINE_SPEC.md`
- T132 task: `tasks/T132-b25-trusted-source-conformance.md`
