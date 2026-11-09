---
id: T287
title: "M1 — Nối LicenseGate vào 2 script ghi entity_claims còn lại"
module: Data Governance / License Gate
priority: p0
status: coding
created: 2026-10-10
updated: 2026-10-10
owner: claude-code
parent: docs/integration (phân tích 2026-10-10)
depends_on: [T231]
done_when: |
  Mọi script ghi entity_claims gọi LicenseGate trước khi ghi.
  Admin xác nhận DONE. Không tự đánh DONE.
revert: |
  Chỉ thay đổi trong task này; hoàn tác bằng sao lưu trong docs/sessions/2026-10-10/ hoặc ROLLBACK.md.
outcome: >
  2026-10-10: tạo task backlog để agent code tuần tự. Chưa bắt đầu.
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

- [ ] **Bước 1 —** xác minh hiện trạng và ghi log
- [ ] **Bước 2 —** chuẩn bị (sao lưu hoặc quyết định Admin)
- [ ] **Bước 3 —** làm việc chính theo mục 3
- [ ] **Bước 4 —** kiểm chứng theo mục 4
- [ ] **Bước 5 —** Admin xác nhận DONE
