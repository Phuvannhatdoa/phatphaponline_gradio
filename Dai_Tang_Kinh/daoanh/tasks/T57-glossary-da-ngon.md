---
id: T57
title: "Glossary Đa Ngôn — Multilingual Buddhist Terminology Popup"
module: Marcus / 84000 / StarDict / UI
priority: low
status: pending
depends_on: [T04, T34]
created: 2026-08-26
updated: 2026-08-26
done_when: >
  Click thuật ngữ Phật học trong giao diện đọc kinh → popup hiển thị nghĩa đa ngôn
  (Hán-Việt, Pali, Sanskrit, Tibetan, English), nguồn 84000 Glossary + Marcus + StarDict,
  liên kết định nghĩa chuẩn. Không ghi đè glossary nội bộ dùng cho translations.
---

# T57 — Glossary Đa Ngôn (Multilingual Glossary Popup)

## Mục tiêu
Click thuật ngữ khó → popup giải nghĩa đa ngôn, giúp Tăng/Ni tra cứu nhanh khi đọc kinh.

## Hiện Trạng (Codebase)
- `marcus_reference` (18,127 rows) — tên/nhân vật, không phải glossary thuật ngữ học thuật
- Register nguồn "glossary" trong `dataset_sources` (24 nguồn) — attribution Marcus `buddhist_studies_glossaries` (CC0)
- StarDict: 22 từ điển PG (~748K entries) — dùng cho `hanviet_normalization.py:227 load_glossary()` (nội bộ)
- T34 Giai đoạn D plan: 84000 `api/glossary-terms` — click thuật ngữ → nghĩa chuẩn (CHƯA build)
- `read.84000.co` Glossary — mỗi khái niệm có link định nghĩa chuẩn

## Khoảng Trống (Gap)
- Chưa có user-facing glossary UI
- `marcus_reference` chủ yếu là person names, không phải thuật ngữ
- StarDict glossary là nội bộ (translation), chưa expose ra UI
- 84000 glossary API chưa integrate

## Subtasks

### T57a — Glossary Lookup Backend
- Route: `GET /daoanh/api/glossary?term=<hanzi|pali|sanskrit>`
- Tra cứu: Han-Viet (StarDict/22 dict) + 84000 glossary API (realtime cache) + Marcus terms
- Trả về định nghĩa + nguồn attribution + link ngoài (84000)

### T57b — Định Danh Thuật Ngữ Trong Text
- Khi hiển thị kinh văn → tô đậm các thuật ngữ có trong glossary (từ khóa dùng lâu dài)
- Popup onclick → gọi `/api/glossary`
- Không hiểu nghĩa → fallback Google/Wikipedia multi-lang (dùng lại T07 logic)

### T57c — 84000 Glossary Cache
- Bảng: `glossary_cache(term, source, definition, lang, url, ts)`
- Cache 24h — tránh gọi 84000 API liên tục
- Seed từ StarDict Hán-Việt phổ biến (top N thuật ngữ PG)

### T57d — Nguồn & License Display
- Mỗi popup phải ghi rõ nguồn (tránh gán nhầm Marcus cho 84000)
- Tuân thủ nguyên tắc: ZQ là bridge tiếng Việt, wikidata last resort

## API Changes
- New: `GET /daoanh/api/glossary?term=`

## Frontend
- Update giao diện đọc kinh (đoạn CBETA preview) — popup glossary
- Tooltip style (tailwind)

## Không Xung Đột Với
- `hanviet_normalization.py` glossary nội bộ — KHÔNG sửa, chỉ đọc thêm
- T04 Marcus — dùng lại data, không sửa
- T34 Giai đoạn D — glossary 84000 (T57 dùng plan đó, làm sau khi T34)

## Estimated Effort: ~10 hours


## Cập nhật 2026-08-29 — Import Yokoyama + Glossary Lookup + Popup UI

**Quyết định từ logic-check (user):**
- KHÔNG import DILA PersAuthority (trùng people 48K) và Japanese NED (trùng đối tượng NER).
- DPPN bản Việt ĐÃ có trong `lexicon` (22 từ điển PG VN) → chỉ đọc + hiển thị chuỗi nguồn.
- Import Yokoyama-Hirosawa 1996 (Sanskrit–Tibetan–Chinese, index Yogācārabhūmi) — Việt chưa có → plant.
- Bổ sung quan hệ **đồng môn (colleague_of)** — derived từ Marcus `isTeacherOf` (cùng thầy), phục vụ nghiên cứu tông môn.

**Đã làm (ngày 2026-08-29):**
- **T62b — Import Yokoyama đa ngôn:**
  - Script mới `scripts/import_glossary_yokoyama.py` (generator zero-RAM; tự tải `.gls` từ repo MB `chinese/yokoyama-hirosawa1996.zip` nếu chưa có local).
  - Bảng mới `glossary_term(term, language, definition, full_text, source_id, created_at)` — additive, UNIQUE(term, language).
  - Data `.gls` tại `data/glossary/` (git-ignored do `data/`): `Yokoyama.1996.瑜伽师地论汉藏梵索引_sanTibChin.gls` (14MB) + `..._chinOnly.gls` (2.8MB).
  - Đã import **248,095 rows**: san 17,171 / zho 67,461 / bod 65,195 / bo-Latn 98,268.
  - Attribution: `dataset_sources.MB_GLOSSARY` (id=6) được bổ sung `origin_url` + `attribution_text` (CC0).
  - **PLANT bản Việt hóa:** Yokoyama là thuật ngữ Duy Thức San–Tib–Chi, chưa có bản dịch Việt → cần admin bản Việt hóa (ghi ở task này).
- **T57a — Glossary Lookup Backend:**
  - Route `GET /daoanh/api/glossary?term=` tra theo thứ tự: `lexicon` (bản Việt 22 từ điển, khớp `term` → fallback `normalized`), `glossary_term` (Yokoyama), `term_glossaries` (Marcus).
  - Mỗi kết quả ghi rõ `source_label`/`source_key` (tránh gán nhầm nguồn).
- **T57b/c — Popup UI:**
  - `places.html`: thêm `openGlossaryPopup(term)` + `bindGlossarySpans(container)` — click phần tử `.da-glossary` → popup modal tra cứu đa ngôn, hiển thị nguồn rõ ràng.

**Verify:**
- `a-bhaya` → Yokoyama (san: 無畏), `無畏` → Yokoyama (zho) + Marcus.
- `Bồ Tát` → lexicon (bản Việt 22 từ điển, 5 matches).
- `npm run lint / test / e2e` ✅; `e2e:runtime` 2 tests PASSED (chạy với output dir tạm do EPERM file `test-results/.last-run.json` bị Playwright worker cũ giữ — lỗi môi trường, không phải code).

**Còn lại (pending):**
- T57c highlight chủ động thuật ngữ trong kinh văn (CBETA preview) khi T52c có content — hiện chỉ hỗ trợ click `.da-glossary`.
- Tích hợp vào giao diện đọc kinh nơi text ~ T52/T34 giai đoạn D (84000 glossary là nguồn bổ sung).
- Bản Việt hóa Yokoyama (admin cung cấp).
