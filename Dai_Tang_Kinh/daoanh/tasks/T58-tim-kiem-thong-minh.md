---
id: T58
title: "Tìm Kiếm Thông Minh — Cross-Language Search (Hán/Pali/Sanskrit)"
module: Search / Entity Resolution / UI
priority: low
status: pending
depends_on: [T07, T30]
created: 2026-08-26
updated: 2026-08-26
done_when: >
  Tìm "Rajagriha" → match "Vương Xá Thành" (Han) + "Wang She Cheng", tìm Pali/Sanskrit term
  → trả kết quả Hán/Việt tương ứng. Không phá FTS5 search hiện có trên /daoanh/api/search.
---

# T58 — Tìm Kiếm Thông Minh (Cross-Language Search)

## Mục tiêu
Cho phép tìm kiếm bằng Pali/Sanskrit token và tự động resolve sang tên Hán/Việt tương ứng.

## Hiện Trạng (Codebase)
- `/daoanh/api/search` (T30): search monks + places + works, dùng FTS5 — chủ yếu Hán/Việt
- `places_search_fts`: name_vi + name_zh cho 118K places
- `hanviet_normalization.py`: 22 dictionaries, diacritics-free
- `/daoanh/api/public/transliterate`: Hán→Việt transliteration
- `/daoanh/api/public/autocomplete`: autocomplete
- T07 `_wiki_search_lang()`: multi-lang Wikipedia fallback
- `pali_place_ref` (T37): 15 Indian sites có name_pali + name_skt

## Khoảng Trống (Gap)
- Search không hỗ trợ Pali/Sanskrit query (tìm "Rajagriha" → không có kết quả)
- Chưa có cross-language entity resolution (Pali → Hán → Việt)
- Chưa có tìm kiếm thuật ngữ đa ngôn

## Subtasks

### T58a — Pali/Sanskrit Alias Table
- Bảng: `place_lang_alias(place_id, lang, name)` 
- Seed: `pali_place_ref` (15 sites) + map tên kinh điển (Hán ↔ Pali ↔ Sanskrit)
- Nguồn: DILA place names + Wikipedia langlinks + Bangkok/CBETA biệt danh

### T58b — Extended Search Backend
- Mở rộng `/daoanh/api/search` — tham số `lang` (vi/zh/pa/sa/en)
- Khi query Pali/Sanskrit → map qua `place_lang_alias` → tìm FTS5 theo Hán/Việt
- Trả về: kết quả + "tên gốc" + link các bản dịch

### T58c — Unified Search Results UI
- Home search box → dropdown chọn ngôn ngữ
- Kết quả hiển thị nhiều phiên bản tên (Hán/Việt/Pali) cùng 1 hàng
- Highlight match + diacritics-free

## API Changes
- Update: `GET /daoanh/api/search` (add `lang` param) — backward compatible

## Frontend
- Update: `home.html` search box
- Update: kết quả search hiển thị đa ngôn

## Không Xung Đột Với
- FTS5 hiện có — chỉ thêm lớp alias, không sửa index
- T30 Home Global Search — tái sử dụng, mở rộng param

## Ghi chú triển khai 2026-10-08 — PHƯƠNG ÁN (b)

**Admin đã chọn phương án (b): KHÔNG tạo bảng `place_lang_alias`.** Viết lớp tra
cứu Python đọc trực tiếp `pali_place_ref` (15 địa danh có sẵn, seed DILA +
SuttaCentral) — không tự suy map tên kinh điển mở rộng vì không có nguồn seed.

**Đã làm (một phần T58a + T58b):**
- Hàm `_pali_sanskrit_lookup(q, conn)` trong `app.py`: đọc `pali_place_ref`
  (CHỈ SELECT), tách `name_pali`/`name_skt` theo dấu `/` (nhiều biến thể trong 1
  cột), so khớp sau khi bỏ dấu/hạ chữ qua `normalize_text()` có sẵn (substring 2
  chiều), có fallback fuzzy (`rapidfuzz.ratio >= 85`, chỉ khi query dài ≥4 ký tự)
  để chịu được biến thể La-tinh hóa khác nhau trong CÙNG 15 dòng seed (ví dụ
  "Rajagriha" vs "Rājagṛha" bỏ dấu thành "rajagrha" — thiếu "i" so với cách viết
  phổ biến khác). KHÔNG thêm địa danh/biến thể nào ngoài 15 dòng có sẵn.
- `GET /daoanh/api/search?q=...&lang=pa|sa` — thêm param `lang` (backward
  compatible: không có `lang` → hành vi cũ y nguyên, đã test). Khi `lang=pa`
  hoặc `lang=sa`, kết quả Pali/Sanskrit match được hợp nhất (union) vào
  `place_ids` dùng cho truy vấn `places_pending`; response thêm field additive
  `cross_lang: {lang, matched_dila_ids, source:"pali_place_ref"}` để UI biết
  nguồn gốc match (phần "tên gốc" trong T58b).

**KHÔNG làm (ghi rõ để không ai hiểu nhầm):**
- **`lang=en`** hoặc ngôn ngữ khác ngoài `pa`/`sa` — **không map**, vì
  `pali_place_ref` chỉ có 2 cột ngôn ngữ (`name_pali`, `name_skt`); test xác nhận
  `lang=en` không trả `cross_lang`, không ảnh hưởng hành vi cũ.
- **T58a mở rộng** (map tên kinh điển Hán ↔ Pali ↔ Sanskrit ngoài 15 sites, hoặc
  qua Wikipedia langlinks/CBETA biệt danh) — không có nguồn seed đã xác minh,
  không tự bịa.
- **T58c (Unified Search Results UI)** — chưa làm dropdown chọn ngôn ngữ trên
  `home.html` hay hiển thị đa phiên bản tên trên 1 hàng kết quả; route API đã
  sẵn `cross_lang` để UI dùng sau, nhưng phần UI tối thiểu chưa làm (ngoài scope
  (b) đã thống nhất, cần Admin xác nhận thiết kế UI trước).

**Test đã chạy:** `python -m py_compile app.py` OK; `app.test_client()`:
"Rajagriha"+lang=sa → `PL000000048261` (Vương Xá Thành) — đúng case nêu trong
`done_when`; "Rajagaha"+lang=pa, "Kapilavastu"+lang=sa — khớp đúng; query từ
không liên quan ("Bihar"+lang=sa) → rỗng, không false-positive; query rỗng → trả
rỗng không lỗi; không `lang` ("Thích Ca") → hành vi cũ y nguyên (backward-compat
xác nhận không có field `cross_lang`); regression `tests/test_t259_*`,
`test_t260_*`, `test_t262_*` — 66/66 PASS (route `/daoanh/api/search` không có
test riêng trong `tests/`, đã kiểm tay qua test_client thay vì script riêng).

## Estimated Effort: ~10 hours
