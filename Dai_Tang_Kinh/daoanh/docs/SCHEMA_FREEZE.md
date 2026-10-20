# SCHEMA FREEZE — Khóa Sổ Schema & Data-Lock

> **Trạng thái:** ✅ DONE (2026-09-11) · **Task:** T82 (Schema Freeze + Data Lock) · **Read-only, additive, 0 ALTER**
> **Phiên bản schema (build hash):** `a8336fb4` — revert = `git revert a8336fb4`

---

## 1. Mục đích

Tài liệu chính thức "khóa sổ" trước release: ghi nhận trạng thái **toàn bộ schema** `data/lineage.db`
(137 tables + 4 views), phân lớp freeze, checksum baseline, và **expected-change registry**
(bảng được phép thay đổi qua luồng HITL — admin review). Dùng để phát hiện regress + bàn giao "vô não".

## 2. Tổng quan Schema (2026-09-11)

**DB:** `data/lineage.db` · 664MB · **137 tables + 4 views**

| Layer | Ý nghĩa | Số bảng | Quy tắc |
|-------|---------|--------:|---------|
| **RAW** | Dữ liệu gốc bất biến (DILA/Marcus/DDBC) | 5 | Đóng băng tuyệt đối — chỉ đọc, ETL dẫn xuất ra nơi khác |
| **CORE** | Bảng trung tâm (entity, places, people, claims) | 15 | Đóng băng — chỉ đổi qua task có revert + checksum lại |
| **MAPPING** | Bảng ánh xạ / liên kết trung gian | 70 | Đóng băng — thêm row qua ETL additive, 0 ALTER |
| **DERIVED** | Bảng dẫn xuất (glossary_vi, *_audit, *_clusters...) | 44 | Tự do sinh mới qua ETL additive + revert script |
| **AUDIT** | Log ghi chép (en_audit_log, text_reading_log) | 2 | Ghi append-only, không đổi lịch sử |
| **VIEW** | SQL view adapter | 4 | Đóng băng — đổi phải qua migration có review |

### 4 Views
`v_assertions` · `v_entity_places` · `v_events_full` · `v_place_cbeta_vn`

## 3. Bảng Trọng Yếu (CORE + RAW) — snapshot 2026-09-11

| bảng | layer | rows | ghi chú |
|------|-------|-----:|---------|
| `entity_claims` | CORE | 447,885 | Assertion layer (T108) |
| `entity_source_ids` | CORE | 182,715 | liên kết nguồn |
| `entity_hub` | CORE | 167,006 | entity unified |
| `lexicon` | CORE | 166,278 | từ điển gốc |
| `places` | CORE | 59,161 | nơi FINAL |
| `places_dila` | RAW | 59,167 | nguồn gốc DILA |
| `cbeta_person_mentions` | MAPPING | 72,628 | mentions kinh ↔ nhân vật |
| `place_timeline_events` | CORE | 3,688 | sự kiện niên đại (T22) |
| `vn_person_events` | CORE | 5,351 | sự kiện người (T79/81/82) |
| `en_audit_log` | AUDIT | 3 | log chỉnh sửa admin |

## 4. Checksum Baseline (Data-Lock)

Chạy `python scripts/t82_checksum.py` (streaming zero-RAM, 7 bảng) → `data/checksums.json` (gitignored):
`people` 48,673 · `places` 59,161 · `places_dila` 59,167 · `place_timeline_events` 3,688 ·
`vn_person_events` 5,351 · `place_person_bibl` 13,933 · `entity_claims` 447,885
→ SHA-256 đầy đủ trong file. **Verify:** `python scripts/t82_checksum.py --verify`

Bảng T55 mới (`cbeta_topic_clusters` 8,168 rows — DERIVED, `text_reading_log` 0 rows — AUDIT)
được snapshot riêng trong `data/schema_snapshot.json` + mint qua task T55a/T55c.

## 5. Expected-Change Registry (thay đổi HỢP LỆ qua HITL)

Các bảng này **được phép đổi row** sau freeze (mọi thay đổi phải ghi `en_audit_log` + check-verification):

| bảng | loại thay đổi hợp lệ | ai ghi |
|------|----------------------|--------|
| `person_bio_vi_draft` | admin_approved 0→1 (Bio Review UI T73) | admin |
| `place_desc_vi_draft` | admin_approved 0→1 | admin |
| `geo_cross_ref` | candidate → approved/rejected (geo-enrich T121) | admin |
| `text_reading_log` | append lượt xem (T55c) | user session |
| `en_audit_log` | append log review | code |
| `lineage_conflicts_v2` | open → resolved / partial (conflict workflow T109) | admin |
| `entity_claims` | verification_status unverified→verified/rejected (T83 bootstrap, reviewed_by='T83_auto') | T83 script / admin |

**Quy tắc:** hiện trạng admin_approved/candidate: `place_desc_vi_draft` 0/14,000 · `person_bio_vi_draft` 0/2,093 ·
`geo_cross_ref` candidate 9. `entity_claims` bootstrap: reviewed_by IS NOT NULL từ T83 script. Không có orphan nào trên 4 chuỗi draft chính (T82 audit).

## 6. Quy Tắc Đóng Băng (Rules of Freeze)

1. **0 ALTER / 0 DROP** trên RAW/CORE/MAPPING/AUDIT nếu không có task chuyên trách + revert sạch.
2. **Bảng mới** chỉ theo dạng **DERIVED/additive** (bảng dẫn xuất + ETL có `--revert`), ghi vào ROLLBACK.md.
3. **Mọi thay đổi DB** đi kèm: snapshot backup hoặc revert SQL 1-lệnh trong `docs/ROLLBACK.md`.
4. **Zero-RAM**: ETL luôn scan tuần tự / LIMIT-OFFSET, không `SELECT *` nạp nguyên bảng.
5. **Sau mỗi phiên build**: chạy lại `t82_checksum.py --verify` → phát hiện regress sớm.

## 7. Giám Sát & Release Gate

- `python scripts/verify_design_compliance.py` (T113) — 9 metric M7.2 (`data/design_compliance.json`).
- `python scripts/t82_checksum.py --verify` — data-lock regress check.
- Dashboard `dashboard_process.html` — mục Data Quality hiển thị metrics.
- **Gate release:** checksum verify PASS + compliance 0 FAIL-blocking + admin review queue không rỗi.

## 8. Files

- `data/checksums.json` (gitignored) — checksum baseline 7 bảng
- `data/schema_snapshot.json` (gitignored) — snapshot toàn bộ 137 tables + 4 views (layer + rows)
- `docs/sessions/t82_data_lock_audit.json` (gitignored) — audit phiên trước
- `docs/db_schema.md` — dictionary chi tiết (task metadata cũ, cần refresher riêng nếu cần)

## 9. Revert

Task này chỉ tạo docs + regenerate checksum (read-only). Revert = `git revert a8336fb4` (docs-only).
Không có ALTER/DROP/INSERT nào để revert lại ở DB.