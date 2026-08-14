# Tiến độ theo ROADMAP

**Cập nhật:** 2026-08-13 (Progressive batch loading GIS places map)
**Xem roadmap chi tiết:** `docs/roadmap.md`

---

## DILA Authority (Person/Place/Time)

- **Trạng thái:** Đã import chủ yếu person/place vào `places_dila`, `places_pending`; đang mapping tên Việt qua `namevi_map_places` (~118k records). `places_pending` ~175k records. ✅ Đã có monk personography schema (`monk_dict` + `monk_name_index`) + ETL + API.
- **Task gần nhất:** `docs/sessions/2026-06-01_fix-namevimap-json-routes.md` — Fix namevimap.html frontend URLs (`/api/...` → `/daoanh/api/...`) + backend route decorators (`/daoanh/api/admin/namevi-queue`, etc.)
- **Còn thiếu:** Seed thêm dữ liệu monk từ `persons.json` (48K records), tích hợp frontend (tooltip/search). Hoàn thiện mapping DILA ↔ people/places, nối CBETA (canon_citations) và Marcus SNA.

## CBETA (Hán tạng số)

- **Trạng thái:** ✅ Backend + frontend đã hoàn chỉnh. Import test 1 file (T51n2076, 景德傳燈錄, 3917 paragraphs). API translate_gemini_cbeta (Gemini + GoogleTranslate fallback).
- **API:** `GET /stats`, `GET /snippet?id=...`, `GET /unit?id=...`, `POST search-place`, `POST search-person`, `POST /llm/summarize`, `POST /translate_gemini_cbeta`, **`GET /cbeta/resolve`**.
- **Focus han_sentence:** ✅ Cả `translate_gemini_cbeta` và `llm_summarize` đều extract câu chứa `context`/`place_name` (dùng `extract_sentence_with_place`) và chỉ gửi câu ngắn đó cho LLM, không gửi cả khối dài. Giữ full `han_text` cho `build_name_map` (name scanning).
- **Bản dịch sai "Tóc ngọc xõa…":** ✅ Đã xóa khỏi `cbeta_ref_passages` cho `T50n2060_p0457c16`.
- **Kiến trúc resolve 2 tầng:** ✅ Layer 1 (`/cbeta/resolve?ref=...`) — chỉ đọc `cbeta.db`, trả Hán văn thuần. Layer 2 (`translate_gemini_cbeta`) — luôn re-resolve từ `cbeta.db` trước, clear stale cache khi `han_text` thay đổi.
- **Giải thích địa danh (Layer 3):** ✅ `POST /cbeta/explain` — extract câu chứa `place_han`, gọi Gemini giải thích 2–4 câu tiếng Việt, cache vào `cbeta_ref_explanations`. Nút "Giải thích" hiện bên cạnh mỗi citation có context `{place_han}`.
- **UI:** On-demand [CBETA] button per citation → inline Han text (toggle), [CBETA DỊCH VIỆT] button → translate, [Giải thích] button → LLM explanation. Timeout safeFetch nâng từ 20s→60s cho LLM endpoints.
- **Bug fix:** Frontend `toggleCbetaHan` kiểm tra `res?.han_text` thay vì `res?.ok` (API trả `success:true` không có `ok`). Resolve endpoint thêm `ok:true` cho nhất quán.
- **Integration Layer (Phase 1):** ✅ ENTITY (~167k), PASSAGE (3,917), PASSAGE_ENTITY (5,276 links). API entity info + passages hoạt động.
- **Block UI (Phase 2 restructure):** ✅ Gộp DILA + CBETA/LLM → 1 block "NGUỒN DẪN ĐẠI TẠNG KINH" với [CBETA] inline toggle + [CBETA DỊCH VIỆT] translate.
- **Task gần nhất:** `docs/sessions/2026-05-28_fix_cbeta_resolve_inline_and_timeout.md`
- **Còn thiếu:** Import thêm CBETA texts (X77n, T50n, etc.) để có dữ liệu cho các citation DILA đang reference.

## Marcus glossaries & SNA

- **Trạng thái:** Đã import dataset (`marcus_reference`, `marcus_networks`). Chưa link với people/places.
- **Task gần nhất:** —
- **Còn thiếu:** Chuẩn hóa `term_glossaries`, gắn với people/works.

## TTL thiền sư Việt Nam

- **Trạng thái:** ✅ Đã xây `vn_person_authority` + 4 bảng phụ trợ (relations/places/works/events). ETL 16 file TTL trong `data/ttl/old/` bằng rdflib → 16 nhân vật, 84 quan hệ, 46 địa danh, 10 tác phẩm, 45 sự kiện. 5/16 nhân vật có `dila_id` verified từ `ttl_mapping`.
- **Task gần nhất:** `docs/sessions/2026-07-29_etl_ttl_person_authority.md` — ETL TTL → Authority Person VN.
- **Còn thiếu:** ETL cho ~2000 file TTL còn lại (định dạng dòng phái), gắn dila_id cho 11 nhân vật chưa verified, tích hợp UI/API, fact extraction → knowledge graph. Task 6 theo tasktodo.md.

## CBDB (China Biographical Database)

- **Trạng thái:** ✅ CBDB thật + API response chuẩn. Luôn 200, `has_cbdb` + `cbdb_places[]` array.
- **Task gần nhất:** `docs/sessions/2026-05-22_fix_cbdb_cbeta_search.md`
- **Còn thiếu:** Task sau: thêm nút "Gửi cho chatling.AI viết mượt và lưu vào ghi chú Việt ngữ".

## Wikipedia (tham khảo CC BY-SA)

- **Trạng thái:** ✅ Tính năng mới — fetch Wikipedia vi/zh tự động, cache vào DB, disclaimer CC BY-SA.
- **API:** `POST /daoanh/api/admin/wiki/fetch` — trả `{has_wiki, wiki_title, wiki_url, snippet}`. Luôn 200.
- **UI:** Block "Wikipedia (CC BY-SA)" trong sidebar. Nút "Tra Wikipedia" → auto-fetch từ tên Việt (DILA) → hiển thị snippet + link.
- **Task gần nhất:** `docs/sessions/2026-05-22_wikipedia_block.md`
- **Còn thiếu:** Cache refresh, multi-language fallback mạnh hơn.

## DILA Integration Layer (Phase 1 + 2)

- **Trạng thái:** ✅ Phase 1 hoàn thành. Phase 2 đã xong restructure 3-block UI (2026-05-24).
- **Phase 1:** ENTITY unified index (167,002 rows). PASSAGE từ CBETA T51n2076 (3,917 passages). PASSAGE_ENTITY (5,276 links).
- **Phase 2a:** ✅ LIKE fallback — thêm `?mode=like` query param vào API passages endpoint.
- **Phase 2b:** ✅ Tích hợp entity passages vào `placevn.html` sidebar.
- **Phase 2c:** ✅ **Search ưu tiên DB + name_vi_norm** — thêm cột `name_vi_norm` vào `places_pending` (diacritics-free), populate save + migration, update search endpoint (Phase 1 DB → word fallback → han_fallback).
- **Phase 2d:** ✅ **3-block DILA restructure** — metadata-only DILA list (Block 1) + CBETA modal (Block 2) + Trích Dẫn Đại Tạng LLM translation (Block 3).
- **Phase 2e:** ✅ **Merge 2 blocks → 1** — gộp DILA citations + LLM translation thành 1 block "NGUỒN DẪN ĐẠI TẠNG KINH"; thêm `highlightKeyword` function (name_vi highlight trong modal CBETA).
- **API:** `GET /daoanh/api/admin/places_search?q=...&cate=...` — trả về `mode` (db/word_fallback/han_fallback).
- **Task gần nhất:** `docs/sessions/2026-05-24_dila_3block_restructure.md`
- **Còn thiếu:** fuzzy matching, PASSAGE_VI, entity summary API (LLM), mở rộng import CBETA.

## Keyword Import Tool

- **Trạng thái:** ✅ Hoàn thành (2026-05-24). Table `keyword_map` + 2 API routes + admin UI page.
- **API:** `POST /daoanh/api/admin/keywords/parse_txt` (parse StarDict/2-line → preview), `POST /daoanh/api/admin/keywords/bulk_import` (bulk insert vào `keyword_map`).
- **UI:** `/daoanh/admin/keyword_import.html` — paste txt → preview editable table → import.
- **Table:** `keyword_map(id, keyword, value, category, source, created_at)` trong `lineage.db`.
- **Task gần nhất:** `docs/sessions/2026-05-24_keyword_import.md`
- **Còn thiếu:** Admin có thể muốn feature export/delete keyword_map, hoặc thêm category filter.

## GeoNames (VN GPS)

## GIS Visualization (Đạo Ảnh Map)

- **Trạng thái:** ✅ Progressive batch loading — markers xuất hiện ngay sau ~2s, batch 800/lần, AbortController chống race condition. 11,267 địa danh load xong trong ~15s (trước: đợi ~10s blank rồi dump hết).
- **Task gần nhất:** `docs/sessions/2026-08-13_progressive-places-load.md`
- **Còn thiếu:** Cluster click handler mở rộng (zoom to cluster bounds khi click), tối ưu icon cluster theo mật độ.

## CBETA Catalog VN (License Tracking)

- **Trạng thái:** ✅ Đã import `cbeta_catalog_vn` (3,122 records) từ Nguyễn Minh Tiến's Mục Lục Đại Chánh Tân Tu, kèm 6 cột license/source attribution (CC BY-SA 4.0).
- **API:** `GET /daoanh/api/places/<id>` trả về `text_info` block với title_vi, dynasty, translator, source, license.
- **UI:** Hiển thị NGUỒN & GIẤY PHÉP block trong sidebar khi place có matching CBETA catalog entry.
- **Task gần nhất:** `docs/sessions/2026-05-29_cbeta_catalog_vn_license.md`
- **Còn thiếu:** Fuzzy matching title_zh ↔ place name_zh (hiện đang dùng LIKE).

## Hán‑Việt Pipeline & Place Name Cleanup

- **Trạng thái:** ✅ Cải tiến `_ensure_vietnamese()` với CUSTOM_HANVIET override (~300 chars), bỏ qua chữ Hán không biết (log vào `missing_hanzi` thay vì giữ nguyên). Bảng `missing_hanzi` tự động tạo. Script batch fix có sẵn `scripts/fix_vietnamese_names.py`.
- **Task gần nhất:** `docs/sessions/2026-05-27_fix_hv_place_names_and_cbeta_translate.md`
- **Còn thiếu:** Admin xem bảng `missing_hanzi` và bổ sung vào CUSTOM_HANVIET dần.

## Hạ tầng docs & automation

- **Trạng thái:** ✅ Đã hoàn thành docs standardization (2026-05-21). `docs/` với 5 skeleton files + roadmap + progress.
- **Task gần nhất:** `docs/sessions/2026-05-21_docs_cleanup_scan.md`
- **Tiếp theo:** Mỗi task mới sẽ cập nhật file này theo quy định trong `docs/contract_opencode.md` §6.

## Dashboard Process Tracker (docs ↔ code)

- **Trạng thái:** ✅ Xây xong backend + frontend (2026-08-13). Dashboard đối chiếu `docs/*.md` với code Python thật, tính % theo code (không hardcode).
- **Script:** `scripts/build_progress_data.py` → `data/progress_data.json` (12 module, endpoints compare).
- **API:** `GET /daoanh/api/progress/dashboard` (app.py) — serve JSON, `?regenerate=1` chạy lại script.
- **UI:** `dashboard/dashboard_process.html` (theme chuẩn) — module cards + progress bar + bảng endpoints ✓/✗, Refresh + auto 60 phút. Truy cập qua `/dashboard/dashboard_process.html`.
- **Tài liệu plan:** `dashboard/README.md`, `plan.md`, `tasks.md`, `handoff.md` — để Claude Code/opencode tiếp nhận công việc không gián đoạn.
- **Task gần nhất:** `docs/sessions/2026-08-14_t09_dashboard_stats_api.md` — **T09 ✅**: `/api/admin/dashboard/stats` (và `/daoanh/api/admin/dashboard/stats`) giờ trả 200 JSON thật nhờ alias route vào `api_dashboard_stats()` (app.py:6057). Trước đó UI thật vẫn dùng `/daoanh/api/dashboard/stats` (đã 200).
- **Còn thiếu:** Hoàn thiện mapping claim cho các module còn 0 claim (DILA Authority, CBDB...).
