---
id: T78
title: "Legal/License Firewall + Legal Check (Add Source) — P0-3"
module: Source Governance Layer (TGS)
priority: high
status: done
depends_on: [T77]
created: 2026-08-31
updated: 2026-08-31
completed: 2026-08-31
done_when: >
  Hệ thống có một lớp GOVERNANCE/SOURCE CONTROL phía trước ingestion: LicenseGate +
  ProvenanceGate + máy trạng thái legal (no DEFAULT=ACTIVE), tách Authority khỏi Legal,
  REFERENCE_ONLY cho source chưa đủ quyền ingest, version pinning per-source, freeze
  khi license đổi. Admin có menu "Legal Check Nguồn" (điền tên+URL repo -> hệ thống tự
  check theo rules -> report + notes tích hợp -> admin xác nhận thêm, legal_status=AUDITING,
  không tự ACTIVE). B1/B2 không bị phá (migration additive + undo + backup).
---

# T78 — Legal/License Firewall + Legal Check (Add Source)

## Mục tiêu
Thêm lớp **LEGAL/LICENSE FIREWALL** cho TGS: không ingest source chỉ vì public trên GitHub;
không suy luận license software = license corpus; source chưa xác minh không vào Canonical;
không phá B1/B2; cho phép Source 21+ mà không rebuild. Admin dùng **Legal Check** để đánh giá
+ thêm nguồn mới bằng form (no-code).

## Quyết định đã chốt (11)
1. Historical 447,885 claims -> **giữ nguyên + snapshot legal_status_at_ingest, không freeze**, chỉ flag.
2. Fix additive mâu thuẫn data (BDRC/FoJin/CHGIS/TGAZ commercial_use giả định -> legal UNKNOWN).
3. Audit **13 nguồn `data_sources`** (KHÔNG 20 theo docs kế hoạch).
4. Version pinning **per-source** (`version_policy`), không hard-rule toàn hệ thống.
5. Add-source: **public-only, không token**.
6. Phân tích license: **rule-based SPDX** (LLM check độc lập riêng từng repo trước khi gửi link).
7. Menu: **sidebar Hệ thống**.
8. Trang: `admin/source_check.html`.
9. Không tự APPROVED — mọi trường hợp **legal_status = AUDITING**, admin tự bật ACTIVE.
10. **Notes mặc định có sẵn** (admin chỉnh được).
11. Reference-Only / Internal Review Notes khi license không cho ingest.

## Kiến trúc (ADD layer trước ingestion — không đụng B1/B2)
```
SOURCE → SOURCE REGISTRY (data_sources) → LICENSE GATE → PROVENANCE GATE
      → QUALITY/AUTHORITY → SOURCE GATE → INGEST
```

## Các file tạo/sửa
- **Create:** `scripts/build3_license_firewall.py` (migration additive + undo), `gate/{__init__,status,license,provenance,analyzer}.py`, `admin/source_check.html`, `tests/test_license_firewall.py` (16 tests), `tests/test_real_data_license.py`.
- **Edit:** `app.py` (2 routes: source-check, source-add), `admin/index.html` (menu), `adapters/registry.py` (dispatch qua gate), `docs/*` (Tasktodo/progress/roadmap/trusted-sources), `dashboard/dashboard_process.html`.
- **Docs:** `docs/LICENSE_FIREWALL_AUDIT.md`, `LICENSE_FIREWALL.md`, `SOURCE_REGISTRY.md`, `PROVENANCE_POLICY.md`, `SOURCE_INTEGRATION_POLICY.md`, `LICENSE_FIREWALL_TEST_REPORT.md`.

## Verify
- Tests: `python -m pytest tests/test_license_firewall.py tests/test_real_data_license.py` (23 passed).
- B1/B2 regression: entity_hub=167,006 / entity_claims=447,885 / entity_source_ids=182,715 — IDENTICAL trước/sau.
- Đạo Ảnh ID mở: `GET /daoanh/api/places/PL000000023255/claims` → HTTP 200.
- Migration reversible: backup `data/lineage_backup_t78.db` + `data/lineage_backup_t78_pristine.db`.
- Dashboard card T78 tự xuất hiện qua `tasks/T78-license-firewall.md`.
