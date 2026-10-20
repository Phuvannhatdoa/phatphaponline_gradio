# License Policy (conformance pointer)

> **T132 P6 §15** | Tạo: 2026-09-22 | Loại: conformance thin (pointer)  
> Spec §11 License Firewall + §12 Versioning.

---

## File gốc (đừng duplicate)

- **Firewall**: `docs/LICENSE_FIREWALL.md`
- **Audit**: `docs/LICENSE_FIREWALL_AUDIT.md`
- **Gate code**: `gate/license.py` — `LicenseGate`
- **Gate status**: `gate/status.py` — `LegalStatus`, `default_allows`

---

## Tóm tắt policy §11

| Operation | Yêu cầu |
|-----------|---------|
| READ_METADATA | `legal_status` không BLOCKED/UNKNOWN/FROZEN |
| DERIVE / TRANSFORM | `data_license_status` hợp lệ |
| INGEST | `can_ingest()` = ACTIVE + INGEST mode |
| REDISTRIBUTE | `data_redistribution=1` |
| COMMERCIAL_USE | `data_commercial=1` |

## T132 P2 additions (§11 wrappers)

```python
gate = LicenseGate(db_path)
gate.can_display(source_id)   # → checkSourcePermission('READ_METADATA')
gate.can_quote(source_id)     # → checkSourcePermission('DERIVE')
```

---

## Versioning §12

Trường `source_version` trong `entity_claims` (T132 P1) = snapshot version lúc lấy.  
So sánh với `data_sources.source_version` → phát hiện staleness.  
Xem chi tiết: `docs/EVIDENCE_GRAPH_CONTRACT.md §5`.
