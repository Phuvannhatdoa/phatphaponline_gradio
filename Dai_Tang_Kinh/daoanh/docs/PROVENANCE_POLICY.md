# PROVENANCE POLICY — TGS (T78)

> **Ngày:** 2026-08-31 · **Áp dụng cho:** mọi Evidence ingest MỚI vào TGS.
> **Nguyên tắc:** KHÔNG tạo Canonical Fact từ Evidence thiếu provenance. "REFERENCE ≠ COPY".

## 1. Trường bắt buộc cho mỗi Evidence (ProvenanceGate)
Mỗi Evidence ingest vào TGS phải có:
- `source_id` — từ Source Registry
- `source_uri` — URL/nguồn cụ thể
- `source_version` — version nguồn
- `retrieved_at` — mốc lấy dữ liệu (ISO)
- `content_hash` — hash nội dung (sha256:...)
- `license_status` — legal status tại thời điểm ingest
- `transformation` — bước biến đổi (normalize/parse/...)
- `evidence_type` — loại (TEXT_EVIDENCE / NETWORK_EVIDENCE / EXTERNAL_ID / ...)

Thiếu 1 trong các trường → **REJECT** ingestion. (Kiểm tra qua `gate/provenance.py`.)

## 2. Version pinning (per-source, `version_policy`)
- `git_pin` — phải có `commit_sha` cụ thể.
- `release_pin` — phải có `release_version` cụ thể (không phải "latest").
- `snapshot_ok` — chấp nhận snapshot có ngày/hash.
- `not_available` — nguồn không có git/release rõ ràng.
- **"latest" / "main" / "master" / "head"** KHÔNG được dùng làm provenance duy nhất.

## 3. Pipeline giữ nguồn gốc
```
RAW SOURCE → NORMALIZED SOURCE → DERIVED EVIDENCE → CANONICAL ENTITY
```
- KHÔNG sửa RAW SOURCE.
- KHÔNG biến dữ liệu đã normalize thành "original".
- Mọi transformation ghi nhận (đã có ở vai trong entity_claims).

## 4. Historical data (bảo vệ B1/B2)
- 447,885 claims đã ingest giữ nguyên; gắn `legal_status_at_ingest` snapshot ("LEGACY").
- Không tự xoá/freeze historical evidence.
- Gate mới chỉ áp cho data MỚI + flag cảnh báo cho historical có legal chưa rõ.

## 5. Kiểm chứng
- `tests/test_license_firewall.py::test_07_missing_provenance` → REJECT khi thiếu.
- `test_08_missing_version_requires_pin` → REJECT khi policy đòi pin mà thiếu commit/release.
- `test_real_data_license.py` → kiểm tra evidence/canonical không mất ID trên DB thật (copy).
