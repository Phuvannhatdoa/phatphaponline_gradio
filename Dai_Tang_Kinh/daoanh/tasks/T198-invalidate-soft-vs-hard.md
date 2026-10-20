---
id: T198
title: "T178/T169 hành vi DELETE trong invalidate_cache_all_semantic — risk mất audit trail, cần phân biệt soft vs hard invalidate"
module: Engine / Cache Invalidation
priority: high
status: done
done_at: "2026-10-09"
done_by: "Admin xác nhận"
undone_reason: "invalidate_cache_for_rule và invalidate_cache_all_semantic dùng DELETE (hard) nên mất audit trail, trong khi endpoint admin dùng UPDATE status='invalidated' (soft). Hai hàm cùng mục đích nhưng hành vi khác nhau; chưa chốt sẽ theo hướng nào. (đã lỗi thời, xem mục 5 và 7)"
undone_until: "Khi Admin chốt soft-vs-hard. Nếu chọn soft: ~10 dòng code + test hồi quy thì đóng được ngay."
undone_action: "ADMIN quyết: giữ soft (đề xuất — xoá cứng khó truy vết lỗi dịch) hay thêm migration/flag cho hard purge."
owner: claudecode
depends_on: [T169]
created: 2026-09-30
updated: 2026-09-30
designed_by: claudecode
handoff_to: Admin
plan_approved_at: "chờ Admin duyệt (đã được yêu cầu mở task riêng)"
done_when: |
  [ĐÃ LỖI THỜI kể từ mục 5 (Admin quyết 2026-10-08): invalidate_cache_for_rule/
  invalidate_cache_all_semantic đã đổi DELETE (hard) → UPDATE status='invalidated' (soft),
  mô tả DELETE dưới đây chỉ còn giá trị lịch sử, KHÔNG phản ánh code hiện tại.]
  docs/DB_Schema.md + docs/Mimo-Flash/T165-spec (hoặc T169) bổ sung matrix invalidate: 
    - admin endpoint `POST /daoanh/api/admin/translate/invalidate` (rv=ALL/rule_code/ids) dùng UPDATE `status='invalidated'` (soft)
    - `invalidate_cache_for_rule(conn, rule_code)` [trước 2026-10-08 dùng DELETE (hard); từ 2026-10-08 đã đổi sang UPDATE status='invalidated' (soft) — xem mục 5]
    - `invalidate_cache_all_semantic(conn)` [trước 2026-10-08 dùng DELETE (hard); từ 2026-10-08 đã đổi sang UPDATE status='invalidated' (soft) — xem mục 5]
  code-comment rõ ràng (docs-only nếu chưa sửa code, hoặc thêm doc comment) + SESSION.md + tasktodo; 0 DB; guard/lint/test PASS.
  Phần docs/DB_Schema.md / docs/Mimo-Flash/T169-* (matrix invalidate, mục 3 Deliverables)
  CHƯA làm — ngoài phạm vi các lần sửa code đã thực hiện (xem mục 5, mục 6).
risk: |
  `DELETE FROM translation_cache WHERE ...` xóa vĩnh viễn bản dịch đã cache, không giữ `status='invalidated'`, khác contract A4 (soft). 
  Có thể phá audit trail (report_count, approved_by, last_error context) và khó rollback.
  Cần Admin quyết định giữ soft-invalidate cho "semantic-wide" hoặc thêm migration/flag (hard purge vs soft). (đã lỗi thời, xem mục 5 và 7)
---

# T198 — Phân biệt soft vs hard invalidate (docs-first)

## 1. Thực trạng (verify 2026-09-30)
- `style_constitution.py:445-467`:
  - `invalidate_cache_for_rule`: `DELETE FROM translation_cache WHERE source_hash IN (...) OR source_text LIKE ?` (hard) — không set `status='invalidated'`
  - `invalidate_cache_all_semantic`: `DELETE FROM translation_cache WHERE selected_rule_codes IS NOT NULL` (hard)
- `app.py:18350` (endpoint invalidate ALL): `UPDATE translation_cache SET status='invalidated', ... WHERE 1=1` (soft) — giữ row, có audit
  [ĐÃ ĐÍNH CHÍNH 2026-10-08 (xem mục 5): mô tả ban đầu ở đây ghi nhầm có cột
  `invalidated_at/invalidated_by/invalidated_reason` — schema `translation_cache` thực tế
  KHÔNG có 3 cột này (đã kiểm `PRAGMA table_info`), chỉ có `status`/`updated_at`.]
- T165/T169 mô tả "invalidate" nói chung, chưa phân biệt 2 nhánh này.

## 2. Mục tiêu
Thêm matrix rõ ràng (contract) vào docs, tránh hiểu lầm A4 (T197 §8 P2). **Không sửa code** trong task này trừ comment/doc.

## 3. Deliverables
1. `docs/db_schema.md` — thêm mục "Cache Invalidation Strategy" (soft vs hard)
2. `docs/Mimo-Flash/T169-t165-engine-build.md` (hoặc thêm note) — cập nhật đoạn nói về invalidate (nêu lý do semantic-wide có thể hard)
3. Thêm § vào `docs/sessions/2026-09-26_t177_directive_v2_absorb.md` hoặc session mới T198
4. `tasks/T198-*.md`, `docs/tasktodo.md`, dashboard (nếu cần)

## 4. Không làm
Code behavior change. Chỉ document contract. Admin quyết định behavior change (nếu cần) riêng.

## 5. Admin quyết (2026-10-08) — phương án (a) XÓA MỀM

Admin chốt: `invalidate_cache_for_rule` và `invalidate_cache_all_semantic` đổi từ DELETE (hard)
sang UPDATE `status='invalidated'` (soft), khớp hành vi endpoint admin (`app.py` các dòng
19874, 20083, 21387/21393 — đều dùng `UPDATE ... SET status='invalidated', updated_at=...`).
Lưu ý: schema `translation_cache` thực tế KHÔNG có cột `invalidated_at/invalidated_by/invalidated_reason`
(đã kiểm bằng `PRAGMA table_info`) — chỉ có `status`, `updated_at`; audit trail giữ qua
`report_count`/`approved_by` sẵn có, không cần cột mới (đúng ràng buộc "không đổi schema").

**File đã đổi:**
- `style_constitution.py` (dòng ~445-474): `invalidate_cache_for_rule` và
  `invalidate_cache_all_semantic` — DELETE → `UPDATE translation_cache SET status='invalidated',
  updated_at=datetime('now') WHERE ... AND status != 'invalidated'`. Thêm điều kiện
  `status != 'invalidated'` để rowcount chỉ đếm row thực sự đổi trạng thái (idempotent).
- `tests/test_t165_style_constitution.py`: sửa `test_invalidate_no_null_delete_4` (assert
  COUNT không đổi = 2, row match có `status='invalidated'`, row NULL legacy giữ `status='auto'`)
  + thêm test mới `test_invalidate_soft_idempotent_t198` (gọi 2 lần, lần 2 rowcount=0,
  report_count/approved_by không mất).

**Backup trước khi sửa:**
- `docs/sessions/2026-10-08/style_constitution.py.bak-before-T198`
- `docs/sessions/2026-10-08/test_t165_style_constitution.py.bak-before-T198`

**Lệnh đã chạy:**
- `python -m py_compile style_constitution.py` → OK
- `python -m py_compile tests/test_t165_style_constitution.py` → OK
- `python -m pytest tests/test_t165_style_constitution.py -q` → 12 passed

**Chưa làm (ngoài phạm vi lệnh admin lần này):** chưa cập nhật `docs/db_schema.md` /
`docs/Mimo-Flash/T169-...` matrix invalidate theo mục 3 (Deliverables) — phần đó là
docs-only, không nằm trong phạm vi "đổi DELETE→UPDATE" được giao lần này. KHÔNG đổi
`status`/đánh DONE trong frontmatter theo đúng yêu cầu.

## 6. QA phát hiện lỗi UNIQUE sau mục 5 — Admin chốt phương án (a) GHI ĐÈ (2026-10-08, lượt 2)

QA xác nhận bug mới phát sinh từ chính thay đổi ở mục 5: sau khi một dòng
`translation_cache` bị soft-invalidate (`status='invalidated'`, còn giữ khóa
UNIQUE(source_hash, source_type)), `write_cache()` (3 nhánh INSERT ở khoảng dòng
775, 791/798 cũ → nay ~776/806/818 tuỳ nhánh migrate) vẫn dùng `INSERT` thường để
ghi bản dịch mới cho CÙNG (source_hash, source_type) ⇒ `sqlite3.IntegrityError:
UNIQUE constraint failed`. Đây là hệ quả trực tiếp của việc đổi DELETE→UPDATE ở
mục 5 (trước đó dòng bị xoá hẳn nên không còn giữ khóa, không bao giờ đụng UNIQUE).

Admin chốt tiếp phương án (a) **GHI ĐÈ** (không đổi schema, không thêm cột):
`write_cache()` dùng `INSERT ... ON CONFLICT(source_hash, source_type) DO UPDATE
SET <cột nội dung/status/updated_at> WHERE translation_cache.status='invalidated'`
cho cả 4 nhánh (P8.2 / T166 identity / T165 constitution / pre-migration legacy).
Khi dòng conflict KHÔNG phải invalidated (ví dụ đang 'auto') thì `WHERE` sai →
SQLite coi như DO NOTHING, không raise lỗi, không đổi gì (ngoài phạm vi sửa lần
này — hành vi cũ giữa 2 dòng active cùng khóa chưa từng xảy ra trong thực tế, đã
kiểm `data/lineage.db` không có duplicate (source_hash, source_type)).

**File đã đổi (lượt 2):**
- `style_constitution.py` (`write_cache`, 4 nhánh INSERT ~dòng 775-915 sau khi thêm
  comment): mỗi nhánh thêm `ON CONFLICT(source_hash, source_type) DO UPDATE SET ...
  WHERE translation_cache.status='invalidated'`. `SET` chỉ liệt kê các cột nội dung
  bản dịch (source_text/translated_text/model_id/rules_version/constitution_hash/
  selected_rule_codes/glossary_hash/identity_*/entity_evidence/alignment_method/
  entity_assertion_status/entity_types_covered tuỳ nhánh) + `status` + `updated_at`.
  KHÔNG đưa `report_count`/`approved_by`/`approved_at`/`created_at` vào `SET` ⇒ các
  cột audit cũ giữ nguyên qua lần ghi đè, đúng yêu cầu Admin.
- `tests/test_t165_style_constitution.py`: thêm `_mkdb_unique_cache()` (schema có
  `UNIQUE(source_hash, source_type)` khớp DB thật — KHÔNG sửa `_mkdb()` chung vì
  `test_lookup_dual_key` cố ý chèn 2 dòng cùng khóa, thiếu UNIQUE) + 3 test:
  `test_write_cache_overwrite_invalidated_row_t198` (a), `test_write_cache_overwrite_
  invalidated_row_idempotent_t198` (b), `test_write_cache_insert_unchanged_no_
  invalidated_row_t198` (c). Đồng thời thêm `UNIQUE(source_hash, source_type)` vào
  bảng tạm của `test_pre_migration_guards_16` (khớp thực tế: UNIQUE có từ lúc tạo
  bảng, độc lập với các cột thêm sau qua migration) — nếu không thêm, nhánh legacy
  mới (`ON CONFLICT(...)`) sẽ lỗi `OperationalError: ON CONFLICT clause does not
  match any PRIMARY KEY or UNIQUE constraint` trên bảng test thiếu constraint đó.

**Backup trước khi sửa (lượt 2):**
- `docs/sessions/2026-10-08/style_constitution.py.bak-before-T198-overwrite`
- `docs/sessions/2026-10-08/test_t165_style_constitution.py.bak-before-T198-overwrite`
- `docs/sessions/2026-10-08/T198-invalidate-soft-vs-hard.md.bak-before-T198-overwrite`

**Lệnh đã chạy (lượt 2):**
- `python -m py_compile style_constitution.py` → OK
- `python -m py_compile tests/test_t165_style_constitution.py` → OK
- `python -m pytest tests/test_t165_style_constitution.py -q` → 15 passed

**Chưa làm (lượt 2):** chưa cập nhật `docs/db_schema.md` / matrix invalidate (mục 3
Deliverables, ngoài phạm vi). KHÔNG đổi `status`/đánh DONE trong frontmatter.

## 7. Lượt sửa 2 và 3 (2026-10-09)

- **Lỗi QA lượt 2 đã sửa:** (1) 4 file test thiếu `UNIQUE(source_hash, source_type)` đã
  thêm ràng buộc khớp DB thật; (2) `translation_id` lấy bằng `SELECT` theo khóa thay vì
  `lastrowid`; (3) khi không ghi (DO NOTHING) trả `replaced=False` kèm id dòng hiện có.
  Chính sách không ghi đè dòng active đã cũ KHÔNG đổi.
- **File đã đổi:** `style_constitution.py` (`write_cache`), `tests/test_t165_style_constitution.py`,
  `tests/test_t179_phase8.py`, `tests/test_t165_phase8_pilot_gate.py`,
  `tests/test_t165_phase8_alignment_persistence.py`, `tests/test_t178_gap_d3.py`.
- **Backup:** `docs/sessions/2026-10-09/*.bak-before-T198-fix2` (6 file).
- **Kết quả:** `test_t165_style_constitution` 15 passed; 4 file hồi quy 52 passed.
- **Chưa làm:** chạy toàn bộ `tests/` (`test_t169_classify_diff.py` gọi `sys.exit` ở cấp
  module làm lỗi collect, không do T198); endpoint dịch thật trên `app.py` chưa chạy
  end-to-end (cấm gọi API); SQLite trên VPS chưa kiểm (local 3.50.4).
- **Rủi ro ghi nhận:** `write_cache` cần `conn.row_factory = sqlite3.Row`;
  `scripts/t50_passage_vi_backfill.py` nhánh `except` dùng `INSERT OR REPLACE` (xóa cứng,
  ngoài phạm vi T198, nên là follow-up nếu Admin muốn).

Admin xác nhận DONE ngày 2026-10-09. Các điểm chưa làm vẫn ghi ở trên (toàn bộ tests/, endpoint thật, SQLite trên VPS, follow-up t50_passage_vi_backfill.py) là việc riêng, không chặn DONE.