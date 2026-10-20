# Source Onboarding — Quy trình thêm nguồn (T77)

**Cập nhật:** 2026-08-31
**Mục đích:** Lifecycle chuẩn để một nguồn dữ liệu mới gia nhập TGS một cách nhất quán,
có đầy đủ provenance, không đụng canonical core (DILA vẫn là canonical).

> Tuân thủ: Build hard-rules, DILA = canonical, external = cross-reference, evidence có provenance.

## Vòng đời (lifecycle)

```
1. REGISTER   → 2. ADAPTER   → 3. NORMALIZE   → 4. RESOLVE   → 5. SCORE
   → 6. EVIDENCE  → 7. HITL
```

### 1. REGISTER — đăng ký nguồn
- Thêm dòng `data_sources` (source_id, source_code, source_name, source_type, license...) + các cột
  metadata T77 (source_version, adapter_version, enabled, capabilities, base_url, license flags).
- Thêm dòng `source_authority` (authority_score, precedence_order, implemented=0 cho tới khi có data thật).
- Script mẫu: `scripts/build3_source_registry_extend.py` + `scripts/build2_register_crossref_sources.py`.

### 2. ADAPTER — cung cấp adapter
- Implement `SourceAdapter` (adapters/base.py) trong `adapters/<source>/`.
- Khai báo `source_code`, `capabilities`, `adapter_version`.
- Đăng ký vào `SourceAdapterRegistry` (adapters/registry.py).
- Mẫu: `adapters/bdrc/__init__.py`.

### 3. NORMALIZE — chuẩn hoá
- `normalize(raw)` biến record thô nguồn → `ExtractedEvidence` (claim_type, subject/predicate/object,
  source_record_id, source_reference, source_url, retrieved_at).

### 4. RESOLVE — gắn canonical entity
- Dùng `entity_hub.entity_id` + `entity_source_ids` để gắn record nguồn vào canonical entity có sẵn.
- **KHÔNG tạo canonical entity mới** trừ khi entity resolution xác nhận thật sự là entity mới (≠ DILA).
- External ID chỉ lưu trong `entity_source_ids` / `entity_claims`, không ghi vào canonical.

### 5. SCORE — authority × match confidence
- SOURCE AUTHORITY (từ `source_authority`) KHÔNG tự đồng nghĩa canonical.
- Phân biệt với MATCH CONFIDENCE (cột `confidence` trong claims).
- HIGH authority + LOW match → vẫn cần human review.

### 6. EVIDENCE — ghi vào `entity_claims`
- Mỗi claim phải có provenance (source_id, source_record_id, source_reference, retrieved_at).
- Evidence mới có provenance thì mới hợp lệ.

### 7. HITL — human review (Đạo Ảnh)
- Reviewer duyệt qua Đạo Ảnh evidence panel → ghi `canonical_decision` + `en_audit_log` + `entity_hub.status='verified'`.
- External evidence KHÔNG trở thành canonical chỉ vì được xếp hạng cao.

## Checklist acceptance (test A–I cho nguồn mới)

| Test | Mô tả | Pass khi |
|---|---|---|
| A | Regression | `npm run pipeline` exit 0; B1 endpoints còn hoạt động |
| B | Register | nguồn xuất hiện trong `data_sources` + `source_authority` |
| C | Adapter dispatch | registry trả adapter đúng theo `source_code` |
| D | Evidence /api/places/<id>/claims | claim nguồn mới hiện tự động, DILA vẫn xếp đầu (authority) |
| E | Provenance | mỗi claim có source_record_id + source_reference + retrieved_at |
| F | Canonical firewall | external ID không thành canonical; entity_hub không tạo entity giả |
| G | Failure isolation | disable `enabled=0` / removal → TGS vẫn hoạt động |
| H | Version upgrade | bump source/adapter version additive, không migration phá canonical |
| I | HITL | Đạo Ảnh review được, lưu canonical_decision + audit |

## Quy tắc fail-safe

- Nguồn có connector nhưng chưa retrieve data → `CONNECTOR_ONLY`.
- Nguồn có data nhưng thiếu provenance → `PARTIAL`.
- Matching chưa phân biệt same-name/different-entity → `FAIL` (chưa vượt).
- External có thể overwrite canonical DILA → `CRITICAL FAIL`.

## Trạng thái nguồn hiện tại (2026-08-31)

| Nguồn | implemented | Status | Adapter |
|---|---|---|---|
| DILA / CBETA / MARCUS / ZQLOCAL / Wikidata | 1 | INTEGRATED | (wrap B3 GĐ2) |
| SAT/CHGIS/BDRC/FoJin/Kanripo/SC/84000/TGAZ | 0 | CONNECTOR_ONLY | BDRC có skeleton; còn lại chưa |
