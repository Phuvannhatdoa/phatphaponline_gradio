# Source Integration Contract (conformance pointer)

> **T132 P6 §15** | Tạo: 2026-09-22 | Loại: conformance thin (pointer)  
> Spec §10 Source Onboarding + §6 Adapter Contract.

---

## File gốc (đừng duplicate)

- **Policy**: `docs/SOURCE_INTEGRATION_POLICY.md`
- **Architecture**: `docs/SOURCE_INTEGRATION_ARCHITECTURE.md`
- **Adapter base**: `adapters/base.py` — `SourceAdapter` + `ExtractedEvidence`
- **Adapter registry**: `adapters/registry.py` — `SourceAdapterRegistry`
- **License gate**: `gate/license.py` — `LicenseGate.checkSourcePermission`
- **Admin UI thêm nguồn**: `POST /daoanh/api/admin/source-add` (app.py)

---

## Quy trình onboard nguồn mới (§10)

1. Thêm row vào `data_sources` (`integration_mode='BLOCKED'`, `license_verified=0`)
2. Admin review pháp lý → update `legal_status`, `data_license`
3. Khi approved: `integration_mode='INGEST'`, chạy ETL riêng
4. Audit log: `en_audit_log` (action='source_onboard')

---

## Adapter contract (§6, T132 P3)

`SourceAdapter` methods (bắt buộc override):
- `search(query)` → `List[ExtractedEvidence]`
- `resolve(record_id)` → `Optional[ExtractedEvidence]`
- `get_provenance(ev)` → `Dict`

Optional defaults (T132 P3):
- `lookup_entity(record_id)` → resolve alias
- `get_identifier(record_id)` → source-specific ID
- `get_license()` → license dict

`ExtractedEvidence` fields (T132 P3 additions):
- `license`, `license_status`, `source_version` — default None (REVIEW_REQUIRED)
