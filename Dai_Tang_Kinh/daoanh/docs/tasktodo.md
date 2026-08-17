# TASKTODO — Đạo Ảnh Dev Roadmap

**Cập nhật:** 2026-08-16
**Context:** Fix timeout placevn.html (places_search FTS prefix + threaded servers) + autocomplete /daoanh/places + places Vị trí block + confidence semantics (Độ tin cậy: admin-reviewed→1.0, auto→0.5, label "TÌNH TRẠNG TÊN VIỆT": Đã duyệt/Tự động, remove %), session docs 2026-08-16.

> **Trạng thái tasks:** Task 1 ✅, Task 2 ✅, Task 3 ✅, Task 4 ✅, Task 5 ✅ (2026-07-29), Task 6 ⏭️ tiếp theo, Task 9 ✅ (2026-08-14), Task 10 ✅ (2026-08-15), Task 11 ✅ (2026-08-16), Task 12 ✅ (2026-08-16)

---

## Trạng thái tổng quan

| Module | GUI | Docs | API | Task |
|--------|-----|------|-----|------|
| Landing Page `/` | ✅ | ✅ | N/A | — |
| Dashboard `/daoanh/admin/` | ✅ stats hiển thị | ✅ | ✅ `/daoanh/api/admin/dashboard/stats` 200 | **#9 ✅** |
| GIS Places `/daoanh/places/` | ✅ map + search | ✅ | ✅ | **#6** |
| PlaceVN Mapping | ✅ page load | ✅ | ✅ | — |
| Name Vi Map | ✅ queue + translate | ✅ | ✅ 48,412 records | **#1** |
| TTL Rebuild | ✅ v4.0 loading | ✅ | ✅ | — |
| Search All | ✅ | ✅ | ✅ | — |
| Keyword Import | ✅ | ✅ | ✅ | — |
| Entity API `/{id}` | ✅ | ✅ | ✅ Thiếu Lâm Tự | — |
| Passages API `/{id}/passages` | ✅ | ✅ | ⚠️ count=0 | **#2** |
| CBETA Catalog VN | ✅ | ✅ | ✅ 3,122 records | **#3** |

---

## Task Priority Queue

### 🔴 Task 1 — Seed monk từ persons.json (48K records)
- **Nguồn:** DILA / Khoá 1
- **Mô tả:** namevi-queue API có 48,412 records, nhưng chỉ 335/48,412 có `name_vi`. Cần ETL bulk auto-generate từ persons.json.
- **API evidence:** `GET /daoanh/api/admin/namevi-queue` → `{"all": 48412, "approved": 335}`
- **Cách tiếp cận:** 
  - Đọc persons.json → extract tên Hán + metadata
  - Chạy Hán-Việt transliteration cho từng tên
  - Bulk upsert vào namevi_map_places

### 🔴 Task 2 — Passage_VI + entity summary (CBETA)
- **Nguồn:** CBETA / Khoá 1
- **Mô tả:** `/entity/PL000000023255/passages` trả `count=0`. Cần import thêm CBETA texts, build PASSAGE_VI translations, entity summary API via LLM.
- **API evidence:** `{"count": 0, "passages": []}`
- **Cách tiếp cận:**
  - Kiểm tra dữ liệu CBETA hiện có trong cbeta.db
  - Import thêm texts nếu cần
  - Xây PASSAGE_VI table
  - Entity summary endpoint

### 🟡 Task 3 — Fuzzy matching title_zh ↔ place (CBETA Catalog)
- **Nguồn:** CBETA Catalog / Khoá 1
- **Mô tả:** Hiện dùng LIKE matching, cần RapidFuzz để match mờ.

### 🟡 Task 4 — Term glossaries → people/works (Marcus)
- **Nguồn:** Marcus / Khoá 1
- **Mô tả:** Chưa link Marcus với DILA people/works.

### 🟡 Task 5 — TTL VN → authority Person VN ✅ (2026-07-29)
- **Nguồn:** TTL / Khoá 2
- **Trạng thái:** Đã xây `vn_person_authority` + relations/places/works/events từ 16 file TTL (`data/ttl/old/`). ETL: `scripts/etl_ttl_person_authority.py`. Session log: `docs/sessions/2026-07-29_etl_ttl_person_authority.md`.
- **Còn lại:** ETL cho ~2000 file TTL còn lại, gắn `dila_id` cho 11 nhân vật chưa verified, tích hợp API/UI.

### 🟡 Task 6 — GIS cluster click handler
- **Nguồn:** GIS / Khoá 1
- **Mô tả:** Cluster chưa zoom-to-bounds khi click.

### 🟡 Task 7 — Wikipedia multi-language fallback
- **Nguồn:** Wikipedia / Khoá 1
- **Mô tả:** Cache refresh + fallback mạnh hơn.

### 🟡 Task 8 — Missing hanzi admin view
- **Nguồn:** Hán-Việt / Khoá 1
- **Mô tả:** Bảng missing_hanzi có nhưng chưa có UI admin.

### ⚪ Task 9 — Dashboard stats API 404 fix ✅ (2026-08-14)
- **Nguồn:** Hạ tầng / Khoá 1
- **Mô tả:** `/api/admin/dashboard/stats` trả 404.
- **Trạng thái:** ✅ Đã fix — thêm alias route `/api/admin/dashboard/stats` + `/daoanh/api/admin/dashboard/stats` vào `api_dashboard_stats()` (app.py:6057). Session log: `docs/sessions/2026-08-14_t09_dashboard_stats_api.md`.

### ⚪ Task 10 — Fix lỗi 500 trang Đạo Ảnh (charmap cp1252) ✅ (2026-08-15)
- **Nguồn:** Hạ tầng / Admin Đạo Ảnh
- **Mô tả:** `places_search` trả 500 khi tìm địa danh có dấu ("Thiếu Lâm") do `print()` tiếng Việt lỗi encode cp1252.
- **Trạng thái:** ✅ Đã fix — `sys.stdout/stderr.reconfigure(utf-8)` đầu app.py + `subprocess.run(encoding='utf-8', errors='replace')`. Test: search tiếng Việt 200, regenerate 200, e2e + playwright PASS. Session log: `docs/sessions/2026-08-15_fix_places_search_charmap.md`.

### ⚪ Task 11 — Fix Timeout placevn.html (FTS prefix + threaded servers) ✅ (2026-08-16)
- **Nguồn:** Hạ tầng / Admin Đạo Ảnh
- **Mô tả:** "Máy chủ phản hồi chậm (Timeout)!" tái diễn — gõ dở rơi về LIKE full-scan ~15.8s + 2 server single-threaded chặn lẫn nhau.
- **Trạng thái:** ✅ Đã fix — `places_search` Phase 0 FTS **prefix** (`"q"` → `q` → `t1* t2* …`, union 2 bảng FTS, miss → `[]` nhanh); `threaded=True` cho app.py + local_gateway.py; `sqlite timeout=10`; rebuild sạch FTS (bảng thường dùng `DELETE FROM`, ngưỡng `_docsize`); thêm `dashboard/restart_servers.ps1`. Session log: `docs/sessions/2026-08-16_fix_places_search_timeout.md`.

### ⚪ Task 11 — Fix Timeout placevn.html (FTS prefix + threaded servers) ✅ (2026-08-16)
- **Nguồn:** Hạ tầng / Admin Đạo Ảnh
- **Mô tả:** "Máy chủ phản hồi chậm (Timeout)!" tái diễn — gõ dở rơi về LIKE full-scan ~15.8s + 2 server single-threaded chặn lẫn nhau.
- **Trạng thái:** ✅ Đã fix — `places_search` Phase 0 FTS **prefix** (`"q"` → `q` → `t1* t2* …`, union 2 bảng FTS, miss → `[]` nhanh); `threaded=True` cho app.py + local_gateway.py; `sqlite timeout=10`; rebuild sạch FTS (bảng thường dùng `DELETE FROM`, ngưỡng `_docsize`); thêm `dashboard/restart_servers.ps1`. Session log: `docs/sessions/2026-08-16_fix_places_search_timeout.md`.

### ⚪ Task 12 — Autocomplete /daoanh/places (FTS endpoint + dropdown) ✅ (2026-08-16)
- **Nguồn:** GIS / Khoá 1 (`places.html`)
- **Mô tả:** Ô search gõ "Thiếu Lâm Tự" autocomplete không chạy; chọn gợi ý xong ô search hiện tên.
- **Trạng thái:** ✅ Đã fix — rewrite `/daoanh/api/places/search` bằng FTS (khớp không dấu/gõ dở/ID/Hán, 0.3-1s thay vì 0 kết quả + LIKE 300-860ms); thêm dropdown gợi ý `ul#autocompleteList`; `selectResult()` set `searchInput.value = name_vi`. Session log: `docs/sessions/2026-08-16_fix_places_autocomplete.md`.

### 🟠 Task 13 — Places Vị trí block + confidence semantics ✅ (2026-08-17)
- **Nguồn:** GIS / Khoá 1 (`/daoanh/places`, `placevn.html`)
- **Mô tả:** Cập nhật hiển thị địa chỉ theo dạng "Vị trí (3 Lớp RAG)" giống placevn.html (country/district/geo rule-based, không tốn AI); sửa rỗng Tỉnh/Quốc gia cho Thiếu Lâm Tự bằng bổ sung province/country từ places theo name_zh; làm "Độ tin cậy" có ý nghĩa: admin-reviewed → "Đã duyệt" (xanh), auto/phiên âm → "Tự động" (vang), bỏ % số; thêm block "MÔ TẢ DILA (RAW)" hiển thị places_dila.note strip XML khi note_vi rỗng; thay đổi label "Tình trạng tên Việt": Đã duyệt / Tự động.
- **Root causes fixed:** (1) Supplement condition namevi_map branch 2 giờ chỉ supplement province/country khi THIẾU (không chỉ GPS thiếu); (2) save_mapping confidence=1.0 khi reviewed, 0.5 khi auto; (3) Frontend label đổi "Đã duyệt"/"Tự động", remove %, thêm dila_note block; (4) placevn.html timeout margin 30s + startup lexicon warm.
- **Kết quả:** `/daoanh/api/places/PL000000023255` (Thiếu Lâm Tự) giờ trả province/country đã populate, "Đã duyệt" thay vì 50%, Vị trí block hiển thị 3 lớp RAG + DILA raw note. Session log: `docs/sessions/2026-08-16_fix_places_vitri_block.md`.
- **Trạng thái:** ✅ Build xong, tests Passed (4/4: lint, test, e2e, runtime), committed c013bba.

---

## GUI Working Pages (confirmed 2026-07-29)

```
GET / → 200 Landing
GET /daoanh/admin/ → 200 Dashboard v4.0
GET /daoanh/places/ → 200 GIS Map
GET /daoanh/admin/placevn.html → 200 PlaceVN
GET /daoanh/admin/namevimap.html → 200 NameVi Map
GET /daoanh/admin/panorama.html → 200 TTL Rebuild v4.0
GET /daoanh/admin/search_all.html → 200 Search
GET /daoanh/admin/keyword_import.html → 200 Keyword Import
```

## API Working (confirmed 2026-07-29)

```
200 GET /daoanh/api/entity/PL000000023255  → Thiếu Lâm Tự
200 GET /daoanh/api/admin/namevi-queue     → 48,412 records
200 GET /daoanh/api/admin/places_search    → ✅ Fixed tiếng Việt có dấu (2026-08-15) + FTS prefix gõ dở/không dấu (2026-08-16)
200 GET /daoanh/api/places/search          → ✅ Fixed autocomplete FTS (2026-08-16): không dấu/gõ dở/ID/Hán
200 GET /daoanh/api/admin/dashboard/stats  → ✅ Fixed (2026-08-14) alias route
404 GET /daoanh/api/monk_names              → (thientong.py, not daoanh)
```

## Task 14 — DILA Time Authority (time_periods = 0)

**ID:** T14
**Title:** Import DILA Time Authority (time_periods = 0)
**Module:** DILA Authority
**Priority:** high
**Status:** in_progress
**Depends on:** []
**Created:** 2026-08-13
**Updated:** 2026-08-16
**Done when:** time_periods có dữ liệu (lunar_month/era/emperor/dynasty) + API tra cứu niên hiệu

## Mục tiêu
DEV_HISTORY audit 2026-08-11: \	ime_periods\ = 0 rows. Cần import DILA Time Authority (lunar_month / era / emperor / dynasty) — core missing module, JDN-based (Khoá 2 / DEV_HISTORY).

## Cách tiếp cận
- Xác định nguồn DILA Time Authority (DILA github Authority-Databases).
- ETL import vào bảng \	ime_periods\ (JDN-based).
- API tra cứu niên hiệu / đổi lịch Trung-Hoa-Nhật.
- Tích hợp vào chronology / timeline nếu có.

## Acceptance criteria (checklist)
- [ ] ETL import time_periods thành công
- [ ] Bảng time_periods có rows (era/emperor/dynasty)
- [ ] API tra cứu niên hiệu hoạt động
- [ ] Đối chiếu JDN chính xác

---

## Task 15 — Entity Identity Hub (DILA + BDRC + CBETA + MARCUS + ZQLOCAL)

**ID:** T15
**Title:** Entity Identity Hub (Multi-source Provenance)
**Module:** Identity Hub
**Priority:** high
**Status:** in_progress
**Depends on:** [T14]
**Created:** 2026-08-16
**Updated:** 2026-08-16
**Done when:** entity_hub có dữ liệu + entity_source_ids đã mapping + API claims hoạt động

## Mục tiêu
Xây dựng kiến trúc identity hub chuyên nghiệp:
- ZQ INTERNAL ENTITY: entity_id INTEGER PK, canonical_label, entity_type
- SOURCE REGISTRY: data_sources (DILA, BDRC, CBETA, MARCUS, ZQLOCAL)
- ENTITY SOURCE IDS: entity_source_ids (mapping giữa ZQ internal ID và các source ID)
- CLAIM / EVIDENCE LAYER: entity_claims (claim_type, authority_role, confidence, verification_status)
- PROVENANCE: Mỗi thông tin truy ngược về nguồn gốc
- COMPATIBILITY VIEW: v_entity_places (frontend tiếp tục hoạt động)

## Quy tắc authority
Không đặt DILA = luôn MAIN, BDRC = luôn MAIN. Authority phụ thuộc claim_type.

## Acceptance criteria (checklist)
- [ ] Tạo entity_hub với entity_id INTEGER PK
- [ ] Tạo entity_source_ids với UNIQUE(source, source_entity_id)
- [ ] Tạo data_sources registry (có BDRC, ZQLOCAL)
- [ ] Tạo entity_claims với các claim_type
- [ ] Tạo entity_summary (VIETNAMESE_SUMMARY)
- [ ] Tạo v_entity_places compatibility view
- [ ] Test case Thiếu Lâm Tự: DILA + BDRC + ZQLOCAL mapping
- [ ] API/entity-hub/resolve trả về unified response object
- [ ] Existing APIs (/daoanh/places/) không break

---

## Task 16 — BDRC Adapter (stub)

**ID:** T16
**Title:** BDRC Integration Adapter
**Module:** Adapters
**Priority:** medium
**Status:** completed
**Depends on:** [T15]
**Created:** 2026-08-16
**Updated:** 2026-08-16
**Done when:** adapters/bdrc/ module tạo xong + staging DB sẵn sàng

## Mô-đun bao gồm:
- dapters/bdrc/discover(): liệt kê entitities BDRC
- dapters/bdrc.fetch_entity(): fetch entity từ BDRC source
- dapters/bdrc.normalize(): normalize BDRC data vào ZQ format
- dapters/bdrc.resolve_identity(): map BDRC entity → ZQ entity_id
- dapters/bdrc.fetch_evidence(): fetch evidence/changelog từ BDRC

**Lưu ý:** BDRC data không có sẵn trong project. Adapter tạo sẵn staging DB rỗng + schema, chờ dữ liệu nguồn import.

---

## Task 17 — Conflict & Provenance Handling

**ID:** T17
**Title:** Conflict Detection & Provenance Integrity
**Module:** Quality Assurance
**Priority:** medium
**Status:** in_progress
**Depends on:** [T15]
**Created:** 2026-08-16
**Updated:** 2026-08-16
**Done when:**
- [ ] Xử lý conflict: DILA history ≠ BDRC history → tạo conflict record
- [ ] Mỗi factual paragraph có source badge
- [ ] Click source → xem source gốc
- [ ] UI không tự động overwrite text DILA/BDRC/CBETA


## Task 14 — DILA Time Authority (time_periods = 0)

**ID:** T14
**Title:** Import DILA Time Authority (time_periods = 0)
**Module:** DILA Authority
**Priority:** high
**Status:** in_progress
**Depends on:** []
**Created:** 2026-08-13
**Updated:** 2026-08-17
**Done when:** time_periods có dữ liệu (lunar_month/era/emperor/dynasty) + API tra cứu niên hiệu

## Mục tiêu
DEV_HISTORY audit 2026-08-11: \	ime_periods\ = 0 rows. Cần import DILA Time Authority (lunar_month / era / emperor / dynasty) — core missing module, JDN-based (Khoá 2 / DEV_HISTORY).

## Cách tiếp cận
- Xác định nguồn DILA Time Authority (DILA github Authority-Databases).
- ETL import vào bảng \	ime_periods\ (JDN-based).
- API tra cứu niên hiệu / đổi lịch Trung-Hoa-Nhật.
- Tích hợp vào chronology / timeline nếu có.

## Acceptance criteria (checklist)
- [ ] ETL import time_periods thành công
- [ ] Bảng time_periods có rows (era/emperor/dynasty)
- [ ] API tra cứu niên hiệu hoạt động
- [ ] Đối chiếu JDN chính xác

---

## Task 15 — Entity Identity Hub (DILA + BDRC + CBETA + MARCUS + ZQLOCAL)

**ID:** T15
**Title:** Entity Identity Hub (Multi-source Provenance)
**Module:** Identity Hub
**Priority:** high
**Status:** in_progress
**Depends on:** [T14]
**Created:** 2026-08-16
**Updated:** 2026-08-17
**Done when:** entity_hub có dữ liệu + entity_source_ids đã mapping + API claims hoạt động

## Mục tiêu
Xây dựng kiến trúc identity hub chuyên nghiệp:
- ZQ INTERNAL ENTITY: entity_id INTEGER PK, canonical_label, entity_type
- SOURCE REGISTRY: data_sources (DILA, BDRC, CBETA, MARCUS, ZQLOCAL)
- ENTITY SOURCE IDS: entity_source_ids (mapping giữa ZQ internal ID và các source ID)
- CLAIM / EVIDENCE LAYER: entity_claims (claim_type, authority_role, confidence, verification_status)
- PROVENANCE: Mỗi thông tin truy ngược về nguồn gốc
- COMPATIBILITY VIEW: v_entity_places (frontend tiếp tục hoạt động)

## Quy tắc authority
Không đặt DILA = luôn MAIN, BDRC = luôn MAIN. Authority phụ thuộc claim_type.

## Acceptance criteria (checklist)
- [ ] Tạo entity_hub với entity_id INTEGER PK
- [ ] Tạo entity_source_ids với UNIQUE(source, source_entity_id)
- [ ] Tạo data_sources registry (có BDRC, ZQLOCAL)
- [ ] Tạo entity_claims với các claim_type
- [ ] Tạo entity_summary (VIETNAMESE_SUMMARY)
- [ ] Tạo v_entity_places compatibility view
- [ ] Test case Thiếu Lâm Tự: DILA + BDRC + ZQLOCAL mapping
- [ ] API/entity-hub/resolve trả về unified response object
- [ ] Existing APIs (/daoanh/places/) không break

---

## Task 16 — BDRC Adapter (stub)

**ID:** T16
**Title:** BDRC Integration Adapter
**Module:** Adapters
**Priority:** medium
**Status:** completed
**Depends on:** [T15]
**Created:** 2026-08-16
**Updated:** 2026-08-17
**Done when:** adapters/bdrc/ module tạo xong + staging DB sẵn sàng

## Mô-đun bao gồm:
- dapters/bdrc/discover(): liệt kê entitities BDRC
- dapters/bdrc.fetch_entity(): fetch entity từ BDRC source
- dapters/bdrc.normalize(): normalize BDRC data vào ZQ format
- dapters/bdrc.resolve_identity(): map BDRC entity → ZQ entity_id
- dapters/bdrc.fetch_evidence(): fetch evidence/changelog từ BDRC

**Lưu ý:** BDRC data không có sẵn trong project. Adapter tạo sẵn staging DB rỗng + schema, chờ dữ liệu nguồn import.

---

## Task 17 — Conflict & Provenance Handling

**ID:** T17
**Title:** Conflict Detection & Provenance Integrity
**Module:** Quality Assurance
**Priority:** medium
**Status:** completed
**Depends on:** [T15]
**Created:** 2026-08-16
**Updated:** 2026-08-17
**Done when:**
- [ ] Xử lý conflict: DILA history ≠ BDRC history → tạo conflict record
- [ ] Mỗi factual paragraph có source badge
- [ ] Click source → xem source gốc
- [ ] UI không tự động overwrite text DILA/BDRC/CBETA

