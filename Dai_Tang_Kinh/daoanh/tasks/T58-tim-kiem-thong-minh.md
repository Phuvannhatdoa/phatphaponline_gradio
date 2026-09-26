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

## Estimated Effort: ~10 hours
