T27 — Source-Neutral Entity ID — Long-term Migration
====================================================

STATUS: DEFERRED (Admin 2026-10-08) — chờ Admin quyết định migrate bây giờ hay không.

PROBLEM:
- entity.entity_id = "PL023255" (TEXT = DILA ID) — đang dùng DILA làm identity
- Hậu quả: DILA IS the identity. Bất kỳ entity nào không có DILA ID thì không thể là ZQ entity.
- BDRC-only entities (Vietnamese masters, Tibetan masters) không thể tồn tại trong hub.

MÙC TIÊU:
- entity.entity_id = INTEGER auto-increment (source-neutral, ví dụ: 10001)
- entity_source_ids dùng zq_id INTEGER thay vì TEXT entity_id
- Tất cả sources được đối xử bằng peers (DILA, BDRC, CHGIS, MARCUS, ZQLOCAL, Wikidata...)

MIGRATION PLAN (từ task file T27, Steps 1-4):
Step 1: ALTER TABLE entity ADD COLUMN zq_id INTEGER; CREATE SEQUENCE entity_seq START 10001;
UPDATE entity SET zq_id = rowid + 10000;
Step 2: ALTER TABLE entity_source_ids ADD COLUMN zq_entity_id INTEGER;
UPDATE entity_source_ids eis SET zq_entity_id = (SELECT zq_id FROM entity WHERE entity_id = eis.entity_id);
Step 3: CREATE VIEW v_entity_by_dila (backward compatibility).
Step 4: API migration — resolve_entity() function handle both old DILA IDs và new integer IDs.

DEPENDS ON: T23, T24, T25, T26 (theo task file)

ACCEPTANCE CRITERIA (từ task file):
- entity.zq_id INTEGER tồn tại và populated
- entity_source_ids dùng zq_id (không dùng text entity_id)
- Compatibility view v_entity_by_dila hoạt động
- Tất cả existing APIs vẫn chạy (test suite PASS)
- BDRC entity (không có DILA ID) có thể insert vào hub
- Backup + rollback plan verify trước migration

CURRENT STATE (db schema check):
- entity table: 167,006 rows, entity_id = TEXT (DILA IDs)
- entity_source_ids table: 167,006+ rows, có cột INTEGER (chứa source_entity_id TEXT)
- Cần migrate 167K rows sang integer ID hệ neutral

DUY KIẾM TRUNG LẬP:
- Hệ thống triều đại này có thể trùng với task khác đang develop nếu:
  + Task khác cũng migrate entity_id sang INTEGER auto-increment
  + Task khác định nghĩa cùng sequence START value (10001 hay giá trị khác)
  + Task khác define tương tự compatibility view v_entity_by_dila
- Admin cần check: nếu trùng → gộp migration plan; nếu không trùng → tiến hành riêng.

NƠI GHI CHỬ: Task file tại tasks/T27-source-neutral-entity-id.md
Đã deferred bởi Admin 2026-10-08 chờ决定何时 hợp lý khi có thời điểm phù hợp để migrate.