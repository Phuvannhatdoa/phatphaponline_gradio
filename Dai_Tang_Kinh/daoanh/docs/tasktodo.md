# TASKTODO — Đạo Ảnh Dev Roadmap

**Cập nhật:** 2026-08-16
**Context:** Fix timeout placevn.html (places_search FTS prefix + threaded servers) + autocomplete /daoanh/places

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

### ⚪ Task 12 — Autocomplete /daoanh/places (FTS endpoint + dropdown) ✅ (2026-08-16)
- **Nguồn:** GIS / Khoá 1 (`places.html`)
- **Mô tả:** Ô search gõ "Thiếu Lâm Tự" autocomplete không chạy; chọn gợi ý xong ô search không hiện tên.
- **Trạng thái:** ✅ Đã fix — rewrite `/daoanh/api/places/search` bằng FTS (khớp không dấu/gõ dở/ID/Hán, 0.3-1s thay vì 0 kết quả + LIKE 300-860ms); thêm dropdown gợi ý `ul#autocompleteList`; `selectResult()` set `searchInput.value = name_vi`. Session log: `docs/sessions/2026-08-16_fix_places_autocomplete.md`.

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
