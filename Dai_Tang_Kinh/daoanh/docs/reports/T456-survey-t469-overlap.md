# T456 — Khảo sát trước khi triển khai (phát hiện trùng phạm vi T469)

> Ngày: 2026-10-30 · Người khảo sát: coordinator · Trạng thái: **chờ Admin quyết 3 điểm**
> Số liệu đo: `scripts/t456_timing.py` (SQL thuần) + `scripts/t456_http_timing.py` (end-to-end HTTP)
> Server đang chạy: `127.0.0.1:5000` (app.py trực tiếp) và `:8080` (gateway)

---

## 1. Phát hiện quan trọng: **T456 đã bị T469 làm gần hết**

T469 (`tasks/T469-homepage-autocomplete-grouped.md`, trạng thái `in_progress`) đã triển khai **đầy đủ backend + frontend** cho autocomplete HOME:

| Thành phần | T469 đã có | Nguồn |
|---|---|---|
| CSS dropdown | `.sr-suggest`, `.sr-suggest-group-title`, `.sr-suggest-item`, `.sr-suggest-name`, `.sr-suggest-han`, `.sr-suggest-meta`, `.sr-suggest-empty` | `index.html` (ghi chú `/* T469: dropdown gợi ý khi gõ */`) |
| HTML | `<input id="heroSearch" role="combobox" aria-expanded aria-autocomplete="list" aria-controls="searchSuggest">` + `<div class="sr-suggest" id="searchSuggest" role="listbox" hidden>` | `index.html` |
| JS | `initSearchSuggest()` (debounce 250 ms, bỏ qua <2 ký tự, `AbortController`), `renderSuggest()`, `_sgPersonMeta()`, `_sgWorkMeta()`, `_sgSetActive()`, `_sgSelect()`, `closeSuggest()` | `index.html` |
| Phím tắt | ↑/↓ di chuyển · Enter chọn · Esc đóng · click ngoài đóng · click dòng → mở đúng trang | `index.html` |
| Endpoint | `GET /daoanh/api/search/suggest?q=` → `{persons:[≤8], works:[≤8], _timing_ms}` | `routes_lineage.py:2497` (`api_search_suggest`) |
| Cache | `_get_person_suggest_cache()` + `_get_work_suggest_cache()` (RAM, không gõ DB mỗi lần) | `routes_lineage.py` |
| Nhóm | 2 nhóm: **"Nhân vật"** + **"Kinh sách / Dịch giả"** | `renderSuggest()` |

**T456 yêu cầu 3 nhóm** (📖 kinh · 🧘 người · 📍 địa danh) ⇒ **phần còn thiếu thật sự chỉ là**:

| # | Phần thiếu | Mô tả |
|---|---|---|
| **1** | **Nhóm "📍 Địa danh"** | Chưa có. T456 định nghĩa: tái dùng `/daoanh/api/public/autocomplete` (T416/T450) |
| **2** | **Nguồn kinh từ DILA** | T469 dùng `cbeta_catalog_vn` (3.122 bộ, Nguyễn Minh Tiến). T456 đòi `dila_catalog_works` (**5.747 bộ**, có `title_vi`/`title_zh`/`cbeta_id`) |
| **3** | **Ưu tiên người có tác phẩm trong kinh lục** | T469 lấy `people` thuần; T456 đòi ưu tiên người có trong `dila_catalog_contributors` (5.589 link) |

---

## 2. Đo hiệu năng (đã có sẵn mọi thứ cần thiết)

### 2a. SQL thuần (3 lần lấy min, ms)
| Truy vấn | `dila_catalog_works` prefix | `cbeta_catalog_vn` prefix | `people` prefix | `people` substring |
|---|---|---|---|---|
| Huyền | 23,7 | 1,2 | 0,3 | 0,3 |
| Thi | 0,4 | 1,4 | 0,3 | 0,2 |
| Long | 16,4 | 2,5 | 2,2 | 0,7 |
| Bát | 0,4 | 0,2 | **36,7** | 2,2 |
| Tâm Kinh | 28,7 | 1,6 | **76,1** | 108,2 |
| Khuy Cơ | 20,8 | 1,0 | **45,2** | 74,6 |
| Thiếu L | 19,3 | 1,9 | **63,9** | 119,7 |
| Nghĩa Huyền | 32,2 | 1,8 | **71,5** | 86,8 |

`EXPLAIN QUERY PLAN` cho `dila_catalog_works`: `SCAN dila_catalog_works` (full scan 5.747 dòng — **vẫn ≤32 ms**).

### 2b. End-to-end HTTP (3 lần lấy min, ms)
| Endpoint | :5000 (trực tiếp) | :8080 (gateway) | Ghi chú |
|---|---|---|---|
| `/daoanh/api/search/suggest` (T469) | **3,7 – 6,6** | 9,5 – 14,6 | ✅ cache RAM |
| `/daoanh/api/public/autocomplete` (T416, places) | **15,6 – 31,5** | 20,6 – 77,2 | ✅ đã <200 ms |
| `/daoanh/api/search` (bấm "Tìm") | 135 – 166 | 156 – 222 | full search, không phải gợi ý |

### 2c. FTS có sẵn trong DB
`places_pending_fts` (FTS5) — đo `MATCH`: "Thiếu L" 39,4 ms (1 hit) · "Nghĩa Huyền" 1,5 ms · "Khuy Cơ" 5,0 ms.
Ngoài ra: `places_search_fts`, `place_norm_fts`, `lexicon_fts`.

---

## 3. Trả lời 2 câu hỏi đang treo (Q4a, Q4b)

### Q4a — Tạo bảng FTS5 mới cho kinh lục, hay chỉ LIKE prefix?
> **Đề xuất: KHÔNG tạo bảng FTS5 mới.**
> - `dila_catalog_works` chỉ **5.747 dòng** → LIKE prefix **≤32 ms** ⇒ không cần FTS.
> - `people` đã có **cache RAM** (T469) ⇒ không gõ DB mỗi lần.
> - `places` đã có **`places_pending_fts`** + route T416 đạt **15–77 ms**.
> ⇒ **Mục tiêu <200 ms đạt được dễ dàng, không cần ghi DB** (giữ nguyên nguyên tắc "additive, không tạo bảng mới khi chưa cần").

### Q4b — T450 (pending) làm trước, hay T456 đi trước?
> **Đề xuất: T456 đi trước; T450 chuyển sang bước verify + xác nhận DONE.**
> - T450 yêu cầu "FTS5 cho `/daoanh/api/public/autocomplete` để đạt <200 ms" — **đo thực tế route đã 15,6–31,5 ms** ⇒ mục tiêu kỹ thuật **đã đạt** (kể cả qua gateway 77,2 ms).
> - T450 còn lại: đo lại bằng `curl`, ghi `ROLLBACK.md`, daoanh-qa, Admin xác nhận ⇒ **không cần viết FTS mới**.
> - T456 là thứ Admin đang chờ để chuyển tiếp; làm T456 trước để có giao diện 3 nhóm, sau đó T450 chỉ còn thủ tục.

---

## 4. Quyết định cần Admin: T456 có bị T469 "nuốt" không?

### Phương án **(α) — Gộp T456 vào T469** ⭐ đề xuất
- T456 đánh dấu **superseded**; phần việc còn lại chuyển thành **bổ sung cho T469**.
- **Không** tạo route mới `/daoanh/api/public/suggest` ⇒ không trùng lặp code/UI.
- Mở rộng `api_search_suggest`:
  - thêm nhóm `places` (tái dùng logic `places_pending_fts` hoặc gọi `/public/autocomplete`)
  - đổi nguồn `works` từ `cbeta_catalog_vn` → **`dila_catalog_works`** (5.747 bộ, badge nguồn DILA) — hoặc giữ cả 2 nguồn
  - thêm trọng số: người có trong `dila_catalog_contributors` được ưu tiên lên đầu
- UI: thêm nhóm "📍 Địa danh" vào `renderSuggest()` (CSS `.sr-suggest-group-title` đã có sẵn)
- ✅ 1 endpoint, 1 UI, không trùng lặp · ✅ T469 đã có nền tảng (cache, phím tắt, a11y)
- ❌ Task T456 bị đánh dấu superseded → cần Admin đồng ý đổi phạm vi task

### Phương án **(β) — Giữ T456, tạo endpoint riêng `/daoanh/api/public/suggest`**
- T456 giữ nguyên 3 nhóm, tự viết route + UI mới
- ❌ Trùng lặp: 2 endpoint gợi ý, 2 bộ JS gõ, 2 dropdown — dễ lệch nhau
- ❌ Phải viết lại cache, phím tắt, a11y đã có sẵn ở T469

---

## 5. Kế hoạch thực thi (nếu chọn α)

| Bước | Việc | Ghi chú |
|---|---|---|
| 1 | Backup `routes_lineage.py` + `index.html` → `docs/sessions/2026-10-30-t456/` | bắt buộc trước khi sửa |
| 2 | `routes_lineage.py`: `api_search_suggest` thêm `places` + đổi nguồn `works` sang `dila_catalog_works` + ưu tiên `dila_catalog_contributors` | **không** tạo bảng DB mới |
| 3 | `index.html`: `renderSuggest()` thêm nhóm "Địa danh" (biểu tượng 📍) + badge nguồn DILA cho works | CSS có sẵn |
| 4 | Đo lại latency end-to-end (mục tiêu <200 ms) — `scripts/t456_http_timing.py` | |
| 5 | Test thật trên trình duyệt: "Huyền Trang" (cả 3 nhóm) · "Khuy Cơ" (địa danh) · "Long Môn" · console không lỗi JS | screenshot + network log |
| 6 | `npm run lint` + `npm run e2e` + `npm run pipeline` | |
| 7 | Ghi `ROLLBACK.md` + cập nhật task file + tasktodo + Handoff + commit | 1 task = 1 commit |

**Rủi ro**: thấp — không ghi DB, chỉ sửa 2 file code; đã có sẵn UI + cache + phím tắt.

---

## 6. Lệnh kiểm tra lại

```bash
# đo SQL thuần (5.747 works vs 3.122 cbeta vs 49.490 people)
python -X utf8 scripts/t456_timing.py

# đo end-to-end HTTP (3 endpoint × 6 chuỗi × 3 lần)
python -X utf8 scripts/t456_http_timing.py

# khảo sát code index.html (UI + endpoint đã gọi)
python -X utf8 scripts/t456_survey_index.py

# khảo sát ID task (để cấp ID mới nếu cần)
python -X utf8 scripts/t456_id_survey.py
```
