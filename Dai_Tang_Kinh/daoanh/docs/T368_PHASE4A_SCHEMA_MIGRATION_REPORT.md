# Audit / Schema Migration Report — T368 Phase4a Schema Migration

> Báo cáo theo template `docs/templates/audit-report.md`. Task liên quan: T368 (DONE), T368b (BLOCKED — xem mục 7).

## 1. Vị trí audit (thực tế, không đoán)

| Hạng mục | File / Schema / Endpoint thực tế |
|----------|----------------------------------|
| Data source | `data/lineage.db` (SQLite, 1.4GB, 156→160 tables) |
| FK targets kiểm tra trước migration | `vn_person_authority` (1074 rows, EXISTS), `places` (59161 rows, EXISTS) |
| Bảng mới tạo (T368) | `person_activity`, `passage_entity_mention`, `entity_merge_log`, `dharma_lineage_unified` — trước migration: MISSING cả 4 |
| Migration script | `scripts/t368_create_tables.py` |
| Rollback script | `scripts/t368_rollback.sql` |
| Verify script | `scripts/t368_verify_schema.py` |
| Test | `tests/test_t368_schema_migration.py` |

## 2. Root cause / phân loại

- **Lớp:** schema (tạo bảng mới, không phải fix bug).
- **Xác minh trước khi chạy:** cả 4 bảng mục tiêu của T368 đều MISSING trong DB thật, không có collision tên với bảng hiện có. FK targets (`vn_person_authority`, `places`) đã tồn tại và có dữ liệu → script có thể chạy an toàn, không rơi vào no-op.
- **Phát hiện quan trọng (ảnh hưởng T368b, không ảnh hưởng T368):** bảng `places` **đã tồn tại** trong DB thật với 59,161 dòng và schema khác hẳn schema "consolidated" mà task T368b mô tả (xem mục 7). Nếu chạy nguyên văn script mẫu trong T368b (`CREATE TABLE IF NOT EXISTS places (...)` với schema mới), lệnh sẽ **no-op im lặng** và task sẽ báo "done" sai sự thật — không có cột/UNIQUE constraint mới nào được tạo, không dữ liệu nào được merge. Tôi KHÔNG chạy script này.

## 3. Data/API contract trước → sau (T368)

| | Trước | Sau |
|--|-------|-----|
| `person_activity` | không tồn tại | tồn tại, 0 rows, CHECK constraint `activity_type IN ('birth','death','ordained','active_at','work')`, FK → `vn_person_authority`, `places` |
| `passage_entity_mention` | không tồn tại | tồn tại, 0 rows, FK → `vn_person_authority`, index trên `person_id` + `cbeta_passage_id` |
| `entity_merge_log` | không tồn tại | tồn tại, 0 rows |
| `dharma_lineage_unified` | không tồn tại | tồn tại, 0 rows, UNIQUE(teacher_id, student_id, source), FK → `vn_person_authority` (x2) |

Không có dữ liệu nào được insert (đúng scope — T369 sẽ import).

## 4. Files changed

- `daoanh/scripts/t368_create_tables.py` (mới) — migration idempotent, có `--dry-run`, kiểm tra FK target trước khi chạy, báo rõ no-op nếu bảng đã tồn tại.
- `daoanh/scripts/t368_rollback.sql` (mới) — DROP 4 bảng T368, không đụng `places`/`vn_person_authority`.
- `daoanh/scripts/t368_verify_schema.py` (mới) — PRAGMA table_info/index_list + test CHECK constraint thực tế bằng INSERT/rollback.
- `daoanh/tests/test_t368_schema_migration.py` (mới) — 6 test case trên DB tạm (không đụng DB thật).
- `daoanh/docs/sessions/2026-10-13/lineage_db_schema_before_t368.sql` — dump schema 302 object trước migration.
- `daoanh/docs/sessions/2026-10-13/lineage_db_backup_before_t368.db` — backup toàn bộ file DB (1.57GB) trước khi ghi.
- `daoanh/data/lineage.db` — đã ALTER (CREATE 4 TABLE + 5 INDEX). **Chưa commit git** (đúng yêu cầu "Forbidden: Do NOT commit to git" trong dispatch).

## 5. Migration / dry-run / rollback

- Dry-run: `python scripts/t368_create_tables.py --db data/lineage.db --dry-run` → in đúng 4 CREATE TABLE + 5 CREATE INDEX, không ghi DB.
- Backup: `docs/sessions/2026-10-13/lineage_db_backup_before_t368.db` (full copy) + `lineage_db_schema_before_t368.sql` (schema-only dump).
- Chạy thật: `python scripts/t368_create_tables.py --db data/lineage.db` → OK, 4/4 bảng tạo thành công.
- Revert: `python -c "import sqlite3; sqlite3.connect('data/lineage.db').executescript(open('scripts/t368_rollback.sql').read())"` hoặc restore từ file backup trên. Đã test rollback trên bản copy riêng (`docs/sessions/2026-10-13/test_rollback_copy.db`, đã xoá sau test) — xác nhận DROP đúng 4 bảng, không đụng `places`/`vn_person_authority`.

## 6. Test cases & kết quả

| Case | Input | Expected | Actual | PASS/FAIL |
|------|-------|----------|--------|-----------|
| Tạo bảng lần đầu | DB tạm có `vn_person_authority`, `places` | 4 bảng được tạo | 4 bảng tồn tại | PASS |
| Idempotent (chạy 2 lần) | gọi `create_tables()` 2 lần liên tiếp | lần 2 không lỗi, không tạo trùng | OK | PASS |
| Thiếu FK target | DB tạm không có `vn_person_authority`/`places` | migration từ chối, trả `False`, không tạo bảng nào | OK | PASS |
| CHECK constraint `activity_type` | INSERT `activity_type='invalid_type'` | `IntegrityError` | OK | PASS |
| UNIQUE constraint `dharma_lineage_unified` | INSERT trùng (teacher_id, student_id, source) | `IntegrityError` ở lần 2 | OK | PASS |
| Rollback chỉ xoá đúng scope | chạy `t368_rollback.sql` | 4 bảng T368 bị DROP, `places`/`vn_person_authority` còn nguyên | OK | PASS |
| Verify trên DB thật | `python scripts/t368_verify_schema.py --db data/lineage.db` | tất cả check PASS, 0 rows mỗi bảng | 11/11 check OK, "PASSED" | PASS |
| pytest suite | `python -X utf8 -m pytest tests/test_t368_schema_migration.py -v` | 6/6 PASS | 6 passed | PASS |

Ghi chú môi trường: máy có 2 Python khác nhau trong PATH (`python3` không có `pytest`; `python` = `C:\Python314\python.exe` có `pytest`). Dùng `python` (không phải `python3`) để chạy pytest.

## 7. Limitation / blocker còn lại — T368b KHÔNG thực hiện

**T368b (Places consolidation) bị tôi dừng lại trước khi ghi DB, không khớp với giả định trong task file:**

- Task T368b giả định cần "tạo bảng `places` hợp nhất" như thể chưa có bảng này. Thực tế `places` **đã tồn tại** (59,161 rows, cột: `id, name_zh, name_vi, name_en, location, gps_lat, gps_long, address, province, country, place_type, source_origin, confidence, created_at, updated_at`) — khác hẳn schema đề xuất trong task (`source`, `status`, `UNIQUE(name_zh, source)` không tồn tại).
- `places.id` dùng namespace ngắn (`PL000000`, 8 số) còn `places_dila.id` dùng namespace khác (`PL000000000001`, 14 số) cho **cùng một địa danh** (ví dụ 闊悉多國). Hai bảng không join được bằng `id` — cần join qua `name_zh`/`place_key`/crosswalk khác, điều task không chỉ rõ.
- `namevi_map_places` (118,296 rows, cột `dila_id` UNIQUE) map vào `places.id` dạng ngắn (xác nhận qua ví dụ `dila_id='PL000000'` khớp `places.id='PL000000'`), nhưng `places.name_vi` hiện chỉ có 2/59161 dòng non-null — nghĩa là việc merge tên Việt vào `places.name_vi` **chưa từng chạy**, đúng như task mô tả, nhưng theo quy tắc ZQ (`daoanh/CLAUDE.md`), merge này phải giữ `source≠'DILA'` cho tên Việt (vì `namevi_map_places.source` phần lớn là `auto_transliterate`/`manual`, confidence 0.5–0.7) — không được gán vào cùng cột mà không có cách phân biệt nguồn, trong khi bảng `places` hiện không có cột lưu nguồn riêng cho `name_vi`.
- Nếu chạy đúng y nguyên script mẫu trong task file (`CREATE TABLE IF NOT EXISTS places (...)`), lệnh sẽ **no-op** vì bảng đã tồn tại — không lỗi, nhưng cũng không làm gì, và nếu không kiểm tra kỹ sẽ báo "done" sai.

**Việc cần Admin/coordinator quyết định trước khi tôi code tiếp T368b:**
1. Giữ `places` hiện tại, chỉ **ALTER TABLE ADD COLUMN** (`source`, `status`) + build crosswalk `places_dila.id ↔ places.id` qua `name_zh`/`place_key`, hay
2. Tạo bảng mới tên khác (ví dụ `places_unified`) để không đụng 59K rows đang được 131+ route trong `app.py` dùng trực tiếp (rủi ro regression cao nếu đổi tên/schema bảng `places` đang live).

Tôi dừng ở đây cho T368b, chưa ghi gì vào DB cho phần places, để tránh báo cáo sai hoặc gây regression trên bảng đang được toàn bộ UI places dùng.
