---
id: T510
title: "Gắn LicenseGate cho 3 script UPDATE entity_claims còn lại (tách từ T287)"
module: Data Governance / License Gate
priority: p0
status: pending
created: 2026-11-01
updated: 2026-11-01
owner: unassigned
parent: tasks/T287-m1-noi-gate-etl-con-lai.md
depends_on: [T287]
former_ids: []
done_when: |
  3 script sau gọi LicenseGate trước khi ghi entity_claims (hoặc được Admin xác nhận không còn dùng):
  scripts/t33_fix_entity_claims_source_id.py (UPDATE source_id),
  scripts/t83_bootstrap_review.py (UPDATE verification_status, reviewed_by),
  scripts/build2_add_evidence_provenance_columns.py (UPDATE source_url, retrieved_at).
  scripts/etl_t100_batch4.py chỉ ALTER TABLE (DDL, không ghi row) — không cần gate, ghi rõ trong outcome.
  Admin xác nhận DONE. Không tự đánh DONE.
revert: |
  Chỉ thay đổi trong task này; hoàn tác bằng sao lưu trong docs/sessions/2026-11-01/T510-coder/backup/ (*.bak-before-coder).
outcome: >
  2026-11-01: tạo từ T287 theo quyết định Admin (tách task). Chưa bắt đầu.
---

# T510 — Gắn LicenseGate cho 3 script UPDATE entity_claims

## 1. Mục tiêu

Mỗi script UPDATE entity_claims trong danh sách trên gọi LicenseGate trước khi ghi, theo mẫu `wire_evidence_into_entity_claims.py` đã làm trong T287.

## 2. Hiện trạng (tester T287, 2026-11-01)

- t33: UPDATE `source_id`, chưa có gate.
- t83: UPDATE `verification_status`, `reviewed_by`, chưa có gate.
- build2: UPDATE `source_url`, `retrieved_at`, chưa có gate.
- etl_t100_batch4: ALTER TABLE thêm cột, không ghi row.

## 3. Các bước

1) Kiểm từng script còn được chạy hay không (grep tham chiếu, ghi log). Script không còn dùng: ghi rõ trong outcome, Admin xác nhận trước khi bỏ qua.
2) Với script còn dùng: thêm gate theo mẫu T287, chạy TRƯỚC khối UPDATE; từ chối thì ghi en_audit_log và thoát mã 2.
3) Kiểm: py_compile/ast.parse; test từ chối nguồn BLOCKED có dòng audit; dry-run không ghi audit.

## 4. Kiểm chứng

ast.parse từng file; script kiểm chứng với DB tạm (không đụng data/lineage.db).

## 5. Không làm trong task này

Không đổi schema. Không chạy ETL thật. Không ghi DB thật. Không commit.

## 6. Các bước

- [ ] **Bước 1 —** kiểm script còn dùng hay không, ghi log
- [ ] **Bước 2 —** gắn gate cho các script còn dùng
- [ ] **Bước 3 —** kiểm chứng theo mục 4
- [ ] **Bước 4 —** Admin xác nhận DONE
