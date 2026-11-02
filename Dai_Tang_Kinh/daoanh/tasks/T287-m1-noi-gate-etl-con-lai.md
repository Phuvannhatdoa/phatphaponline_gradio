---
id: T287
title: "M1 — Nối LicenseGate vào 2 script ghi entity_claims còn lại"
module: Data Governance / License Gate
priority: p0
status: done
created: 2026-10-10
updated: 2026-11-01
owner: claude-code
parent: docs/integration (phân tích 2026-10-10)
depends_on: [T231]
done_when: |
  2 script ghi entity_claims (wire_evidence_into_entity_claims.py, etl_t109_provenance.py) gọi LicenseGate trước khi ghi.
  Phần 3 script còn lại tách sang T510 (Admin quyết 2026-11-01).
  Admin xác nhận DONE. Không tự đánh DONE.
revert: |
  Chỉ thay đổi trong task này; hoàn tác bằng sao lưu trong docs/sessions/2026-10-10/ hoặc ROLLBACK.md.
outcome: >
  2026-11-01 (coder): Đã nối LicenseGate vào 2 script.
  (1) Hiện trạng kiểm lại: scripts/etl_t109_provenance.py KHÔNG INSERT entity_claims
  (chỉ ghi 2 bảng dẫn xuất entity_claims_audit + events_provenance); script thật sự
  INSERT entity_claims còn lại là scripts/wire_evidence_into_entity_claims.py.
  (2) wire_evidence_into_entity_claims.py: thêm _gate_check + _gate_audit_refusal
  (nguồn CBETA=3, MARCUS=4, Wikidata tra data_sources), chạy TRƯỚC khối xoá/ghi;
  khối DELETE idempotent được dời xuống ngay trước INSERT để không mất dữ liệu cũ
  nếu gate từ chối; bị từ chối -> raise PermissionError + exit 2.
  (3) etl_t109_provenance.py: thêm gate_preflight(conn, dry_run) với op DERIVE cho
  mọi source_id có trong entity_claims + DILA (events_provenance gán cứng DILA);
  chạy trước khi tạo bảng/backfill; từ chối -> ghi en_audit_log + SystemExit(2).
  (4) Nhánh từ chối: 1 dòng en_audit_log (action=license_gate_block, entity_ref=source:<id>,
  field_name=<bảng đích>, verification_status=blocked, editor=tên script,
  evidence_sources=JSON gate/op/status). --dry-run không chặn và KHÔNG ghi audit.
  (5) Kiểm chứng: py_compile + ast.parse 2 file OK; pytest tests/test_license_firewall.py
  16 passed; script kiểm chứng riêng với DB tạm
  docs/sessions/2026-11-01/T287-coder/verify_t287.py -> PASS (nguồn BLOCKED bị từ chối +
  đúng 1 dòng audit; dry-run 0 dòng audit).
  Còn mở: mẫu etl_entity_claims.py là fail-open khi import gate lỗi (WARN rồi bỏ qua) —
  T287 giữ đúng mẫu này; nếu MA muốn fail-closed thì cần task riêng đổi cả 3 script.
  Không đổi schema, không chạy ETL thật, không commit.
---

# T287 — M1 — Nối LicenseGate vào 2 script ghi entity_claims còn lại

## 1. Mục tiêu

Mọi script ghi entity_claims gọi LicenseGate trước khi ghi.

## 2. Hiện trạng (đã kiểm 2026-10-10)

scripts/etl_t109_provenance.py và scripts/wire_evidence_into_entity_claims.py chưa có gate (kiểm bằng grep, có thể bỏ sót).

## 3. Các bước (agent làm lần lượt)

1) Xác định script nào thật sự INSERT entity_claims. 2) Theo mẫu scripts/etl_entity_claims.py (dòng 26–29). 3) Nhánh từ chối ghi en_audit_log.

## 4. Kiểm chứng

py_compile từng file; thử nguồn BLOCKED bị từ chối với dòng audit.

## 5. Không làm trong task này

Không đổi schema. Không chạy ETL thật.

## 6. Các bước

- [x] **Bước 1 —** xác minh hiện trạng và ghi log
- [x] **Bước 2 —** chuẩn bị (sao lưu hoặc quyết định Admin)
- [x] **Bước 3 —** làm việc chính theo mục 3
- [x] **Bước 4 —** kiểm chứng theo mục 4
- [ ] **Bước 5 —** Admin xác nhận DONE
