# SOURCE INTEGRATION POLICY — TGS (T78)

> **Ngày:** 2026-08-31 · **Định nghĩa** quy trình tích hợp nguồn mới (Source 21, 22, ... N)
> KHÔNG rebuild B1/B2, KHÔNG hard-code if/else per-source.

## 1. Ingestion Firewall (mọi path đều qua)
```
SOURCE
  ↓
SOURCE REGISTRY (data_sources)
  ↓
LICENSE GATE (checkSourcePermission)
  ↓
PROVENANCE GATE (bắt buộc provenance)
  ↓
QUALITY / AUTHORITY
  ↓
SOURCE GATE (legal_status)
  ↓
INGEST
```
**Không có ingestion path bypass.** `adapters/registry.dispatch` gọi LicenseGate trước khi trả adapter.

## 2. Quy trình thêm Source 21+
| Bước | Việc | Ai |
|------|------|----|
| 1 | Tạo registry entry (INSERT `data_sources` hoặc Legal Check form) | Admin |
| 2 | Adapter nếu cần (đăng ký trong `adapters/`) | Dev |
| 3 | License audit (Legal Check / xác minh SPDX) | Admin + Hệ thống |
| 4 | Provenance audit (đảm bảo version pinning) | Hệ thống |
| 5 | Source Gate (legal_status=AUDITING) | Hệ thống |
| 6 | Approval (admin bật ACTIVE) | Admin |

## 3. Legal Check (Add Source by form)
`admin/source_check.html`:
1. Nhập **Tên nguồn + Repo URL** (public, không token).
2. Hệ thống: fetch LICENSE/README → **rule-based SPDX** → LicenseGate từng operation.
3. Report 3 phần: **A** đánh giá license · **B** kết luận pháp lý · **C** notes tích hợp + provenance draft.
4. Nếu license không cho ingest nhưng repo phù hợp → **REFERENCE_ONLY nội bộ, phi thương mại** + notes đề nghị.
5. Admin bấm **XÁC NHẬN THÊM** → `source-add` → `legal_status=AUDITING` (KHÔNG tự ACTIVE) + audit log.
6. Dashboard card tự xuất hiện.

## 4. Reference-Only / Internal Review (chính sách notes)
- Source chưa đủ quyền ingest nhưng có giá trị học thuật → dùng **REFERENCE_ONLY**:
  lưu metadata để trích dẫn/truy nguyên trong phạm vi quyền cho phép, **KHÔNG copy corpus vào Canonical**.
- Chế độ **thuần nội bộ, phi thương mại**, mục đích học thuật/đối chiếu cá nhân.
- Notes mặc định có sẵn (admin chỉnh/duyệt):
  * Chỉ dùng đối chiếu/trích dẫn nội bộ; không nhúng bản gốc vào đầu ra công khai;
    không tự publish/redistribute; khi tác giả cấp quyền → team xác nhận sau → nâng ACTIVE.
- "Reference ≠ Copy": không copy corpus chỉ vì thuận tiện.

## 5. Freeze khi license/termp đổi
- Change-detector so `content_hash`/`license_verified_at`/`terms_status`/`repository_url`.
- Phát hiện đổi → `legal_status=FROZEN`, chặn ingest mới, KHÔNG xoá historical.
- Admin review rồi mới tiếp tục.

## 6. Boundary (không sửa)
- KHÔNG sửa `entity_hub/entity_claims/entity_source_ids/places/people` ID/dữ liệu.
- KHÔNG đổi `source_authority` ranking.
- KHÔNG rewrite B1/B2. Chỉ ADD tầng Governance.
