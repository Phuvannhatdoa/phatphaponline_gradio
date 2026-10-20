# LICENSE FIREWALL — TGS/PTDA (T78)

> **Ngày:** 2026-08-31 · **Layer:** Source Governance / Source Control (ADD trước ingestion)
> **Nguyên tắc cốt lõi:** PUBLIC ≠ FREE · GITHUB PUBLIC ≠ LICENSE · SOFTWARE ≠ CORPUS ·
> AUTHORITY ≠ INGEST PERMISSION · REFERENCE ≠ COPY · SOURCE ≠ CANONICAL

---

## 1. Mục đích
Thêm một tầng GOVERNANCE phía trước ingestion để:
1. Không ingest source chỉ vì public trên GitHub.
2. Không suy ra license corpus từ license software.
3. Không cho source chưa xác minh license vào Canonical DB.
4. Không phá B1/B2 (đã build).
5. Cho phép Source 21, 22... mà không rebuild.
6. Mọi evidence truy nguyên về source + version + provenance.
7. Tách rõ: Academic Authority / Legal Permission / Technical Quality / Provenance.

## 2. Kiến trúc (ADD layer)
```
RAW SOURCE
  ↓
SOURCE REGISTRY (data_sources — mở rộng cột legal)
  ↓
LICENSE GATE   → checkSourcePermission(source_id, operation)
  ↓
PROVENANCE GATE → bắt buộc provenance khi ingest mới
  ↓
QUALITY / AUTHORITY (đã có, KHÔNG đụng ranking)
  ↓
SOURCE GATE     → legal_status machine
  ↓
INGEST (B1/B2 giữ nguyên; historical claims giữ + snapshot)
```

## 3. Máy trạng thái legal (status machine)
Chuỗi tích lũy phê duyệt: **DISCOVERED → AUDITING → VERIFIED → APPROVED → ACTIVE**
Trạng thái giới hạn: **UNKNOWN / REFERENCE_ONLY / BLOCKED / FROZEN**

| Status | INGEST data mới? | Ghi chú |
|--------|------------------|---------|
| DISCOVERED / AUDITING / VERIFIED | ❌ | đang xác minh |
| APPROVED | ⏸ | đủ pháp lý nhưng chưa active |
| ACTIVE | ✅ | được ingest theo policy |
| UNKNOWN | ❌ | chưa rõ — KHÔNG INGEST |
| BLOCKED | ❌ | cấm |
| FROZEN | ❌ (giữ historical) | license/terms đổi, đang review |
| REFERENCE_ONLY | ✅ chỉ citation | không copy corpus vào Canonical |

> **KHÔNG có DEFAULT = ACTIVE.** Source mới → AUDITING, admin tự bật ACTIVE.

## 4. LicenseGate
`checkSourcePermission(source_id, operation)` → `{allowed, status, reason, license, source_id, checked_at}`.
Operations: `READ_METADATA / DOWNLOAD / STORE_RAW / TRANSFORM / DERIVE / INGEST / REDISTRIBUTE / COMMERCIAL_USE`.
Kết quả không phải boolean đơn thuần. Phân biệt operation cần DATA vs chỉ SOFTWARE.

## 5. ProvenanceGate
Mỗi Evidence ingest mới bắt buộc: `source_id, source_uri, source_version, retrieved_at,
content_hash, license_status, transformation, evidence_type` (+ commit_sha HOẶC release_version
nếu policy đòi pin). Thiếu → REJECT. "latest" không được dùng làm provenance duy nhất.

## 6. Software ≠ Corpus
MIT repo không khiến corpus APPROVED. LicenseGate tách: software op cho phép, corpus op (INGEST/
REDISTRIBUTE/COMMERCIAL) chặn nếu `data_license_status` chưa verify.

## 7. Authority ≠ Legal
`authority_score` không bao giờ để approve legal. DILA/CBETA authority cao vẫn AUDITING cho tới khi
admin xác minh license → ACTIVE.

## 8. Reference-Only / Internal Review
Source phù hợp kỹ thuật nhưng license chưa cho ingest → **REFERENCE_ONLY nội bộ, phi thương mại**:
lưu metadata trích dẫn/truy nguyên, KHÔNG copy corpus vào Canonical, kèm **notes tích hợp** mặc định
(admin chỉnh/duyệt). Khi tác giả cấp quyền → team xác nhận sau → nâng ACTIVE.

## 9. Freeze khi license đổi
Change-detector so `content_hash`/`license_verified_at`/`terms_status` → phát hiện đổi → `FROZEN`,
chặn ingest mới, KHÔNG xoá historical. Admin review 1 lần.

## 10. Files
- **Create:** `scripts/build3_license_firewall.py`; `gate/{__init__,status,license,provenance,analyzer}.py`; `admin/source_check.html`; `tests/test_license_firewall.py`, `tests/test_real_data_license.py`.
- **Edit:** `app.py` (2 routes), `admin/index.html` (menu), `adapters/registry.py` (dispatch qua gate).
- **Docs:** `LICENSE_FIREWALL_AUDIT.md`, `SOURCE_REGISTRY.md`, `PROVENANCE_POLICY.md`, `SOURCE_INTEGRATION_POLICY.md`, `LICENSE_FIREWALL_TEST_REPORT.md`.
