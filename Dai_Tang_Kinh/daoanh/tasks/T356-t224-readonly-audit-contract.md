---
id: T356
title: "T224 — Reproducible read-only audit contract"
module: GIS Places / Timeline / HOME
priority: high
status: in_progress
doc_status: in_progress
parent: T224
former_ids: [T355]
owner: code
created: 2026-10-11
updated: 2026-10-11
depends_on: [T224]
done_when: >
  Audit stdlib mode=ro/query_only trong một read transaction, membership một bucket/id,
  flags any/founding/dissolved tách biệt, JSON/CSV và manifest/hash tái lập, unittest fixture
  PASS, docs T224 đồng bộ lịch sử/hiện hành, dashboard sinh qua build_progress_data.py,
  root/Debug QA và trạng thái guard/dup:ids được báo trung thực.
---

# T356 — T224 audit contract, chỉ đọc DB

Admin đã duyệt build T356. Parent [T224](T224-geo-spatial-timeline-founding-phase2.md) đã xong audit G0–G2 lịch sử; G3 vẫn deferred. Không cấp lại T224/T181 hoặc sửa duplicate ID của session khác.

## Scope và cổng an toàn

- [Script](../scripts/t356_t224_readonly_audit.py): stdlib, SQLite URI mode=ro + query_only, authorizer đọc; BEGIN chỉ tạo read transaction. Không import app.py/HTTP/LLM/DDL/DML.
- SQL chỉ trả marker/flags/length và text có bound; không trả hoặc parse toàn raw_xml. Iteration fetchmany(256), một CASE A1>A2>C>B>D>E trên places_dila.id.
- A1/A2 là any-event source buckets. Founding/dissolved có flag riêng; marker chỉ là candidate, không phải date/accepted. QID syntax, tên/tọa độ không tự xác minh semantic identity hay lineage.
- Chỉ ghi report JSON/CSV/manifest vào --out-dir rõ ràng; không ghi đè file có sẵn. --dry-run không ghi output. Metadata schema/hash, timestamp/command/definition_version và historical_reference tách current_read_transaction.
- T22 sở hữu founding/era worklist; T121 sở hữu geo-enrich HITL; T230/T231 sở hữu catalog/quyền/Source Hub. Không production DB/TTL/API/raw XML/note mutation, migration/importer/NLP, không stage/commit.

## Kiểm thử / trạng thái build

[Unittest](../tests/test_t356_t224_readonly_audit.py) dùng SQLite tạm, thử write rejection chỉ trên fixture. Kết quả run, current audit và guard/dup được ghi ở [session T356](../docs/sessions/2026-10-11_T356/README.md). Triển khai/docs đã xong; 13/13 tests sau rename PASS. Debug đã kiểm script trước rename T355; root QA docs/commit còn pending. Audit cuối T356 đã PASS read-only. Không claim full pipeline.

## File liên quan / rollback

[Plan T224](../docs/Mimo-Flash/T224-geo-spatial-timeline-founding-phase2.md), ba report G2 và [Handoff T356](../docs/Handoff-2026-10-11-T356-t224-audit.md). Backup/hash input nằm trong docs/sessions/2026-10-11_T356/inputs-before.json và backups/. Rollback docs cần so hash sau, giữ thay đổi session khác; code mới revert theo commit root tạo sau QA. DB không có phần rollback vì không ghi.
