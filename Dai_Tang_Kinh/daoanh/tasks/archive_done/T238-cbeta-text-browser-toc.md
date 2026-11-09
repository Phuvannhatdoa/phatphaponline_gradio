---
id: T238
title: CBETA Text Browser — Duyệt văn bản CBETA
status: done
priority: high
created: 2026-10-05
completed: 2026-10-05
---

## Mục tiêu

Researcher có thể duyệt theo cấu trúc văn bản CBETA mà không cần search từ khóa hay chọn người trước.
Discovery path thứ ba: Tab "📜 Đại Tạng" → Danh sách 5 bộ → Chọn bộ → Duyệt các trang → T236 reader.

## Phase 0 — Discovery

**CASE chọn: CASE D** — corpus limited, build với coverage rõ ràng.

| Bảng | Ghi chú |
|------|---------|
| `cbeta_person_mentions` | 72,628 rows, 5 siglas |
| `juan` field | `''` cho tất cả rows — KHÔNG có juan data |
| `page` field | Format `0196c` (4 chữ số + cột a/b/c), string-sortable |

Không có juan → KHÔNG tạo juan browser. Duyệt theo page locator (CASE D).
Nhiều người nhắc cùng trang → GROUP BY page tránh duplicate snippets.

## Real Data

| Sigla | unique_pages | total_mentions |
|-------|-------------|----------------|
| T51n2076 | 493 | 22,275 |
| X77n1524 | 411 | 14,637 |

## Implementation

### Backend

- `GET /daoanh/api/cbeta/texts`
  - Trả danh sách 5 bộ có data trong `cbeta_person_mentions`
  - LEFT JOIN `cbeta_catalog_vn` cho title_vi, title_zh
  - Aggregate: total_mentions, mentions_with_page, unique_pages
  - Sort: total_mentions DESC

- `GET /daoanh/api/cbeta/text/<sigla>/browse?offset=0&limit=20`
  - Exact sigla match, 404 nếu không tồn tại
  - GROUP BY page, MIN(id) as reader_ref, MIN(context_snippet) as snippet
  - ORDER BY page ASC, MIN(id) ASC (deterministic)
  - limit max 100
  - coverage: complete_text=False, granularity='context_snippet'

### Frontend (places.html)

- `#cbetaTextListBlock` — danh sách văn bản, luôn visible trong `#tp-daitang`
  - Tải bằng `cbetaLoadTexts()` khi user mở tab Đại Tạng (1 lần duy nhất)
  - Mỗi dòng: title_vi, title_zh, sigla, unique_pages, total_mentions
  - Nút "Duyệt →" → gọi `cbetaOpenTextBrowser(sigla)`

- `#cbetaTextBrowserBlock` — browser panel (ẩn mặc định)
  - Header: title_vi, title_zh, sigla badge, nút "← Quay lại"
  - Coverage statement: total_mentions, unique_pages, note không toàn văn
  - List items: page locator, snippet, mention_count, "📖 Đọc nguyên bản →"
  - Pagination: Prev/Next nếu > 1 trang
  - AbortController race guard
  - XSS: tất cả DB content qua `_escHtml()`

- `cbetaLoadTexts()` — fetch /api/cbeta/texts, render vào #cbetaTextListItems (1 lần)
- `cbetaOpenTextBrowser(sigla)` — ẩn list, hiện browser, gọi _cbtFetch(0)
- `cbetaCloseBrowser()` — ẩn browser, hiện list + search
- `cbetaBrowseNav(dir)` — điều hướng trang
- `_cbtFetch(offset)` — fetch với AbortController, render items

## T236 Reuse

Cùng `openCbetaPassageReader(mentionId)`:
- Person citation path (T235)
- Corpus search path (T237)
- **Text browser path (T238)** ← mới

Ba discovery paths, một reader contract. ✓

## CASE D — Không có juan data

`juan = ''` cho tất cả rows trong DB thực. Không tạo juan/chapter/section labels.
UI không nói "Quyển" hay "Phẩm". Chỉ hiện page locator dạng `Tr. 0196c`.

## Tests

File: `tests/test_t238_cbeta_text_browser.py`

**27/27 PASS** (A-V + R1-R5):
- A: /texts ok=True
- B: /texts có cả 2 sigla fixture
- C: titles từ catalog
- D: sort total_mentions DESC
- E: unique_pages đúng
- F: browse ok=True
- G: browse meta (sigla, title_vi)
- H: GROUP BY page (không duplicate)
- I: mention_count đúng (2 người cùng trang)
- J: items sort page ASC
- K: reader_ref không null, là integer
- L: items có snippet
- M: coverage.complete_text = False
- N: coverage.granularity = 'context_snippet'
- O: coverage.note không rỗng
- P: pagination có đủ fields
- Q: limit max 100
- R: sigla không tồn tại → None (404)
- S: coverage.unique_pages đúng
- T: pagination.total đúng
- U: offset pagination (không overlap)
- V: ast.parse app.py PASS
- R1: /texts real DB ≥ 5 bộ
- R2: T51n2076 ≥ 100 unique pages
- R3: X77n1524 ≥ 50 unique pages
- R4: Không duplicate pages T51n2076
- R5: reader_ref hợp lệ

## Done when

- [x] `GET /daoanh/api/cbeta/texts` endpoint
- [x] `GET /daoanh/api/cbeta/text/<sigla>/browse` endpoint
- [x] `#cbetaTextListBlock` + `#cbetaTextBrowserBlock` trong tp-daitang
- [x] `cbetaLoadTexts()` / `cbetaOpenTextBrowser()` / `cbetaCloseBrowser()` / `cbetaBrowseNav()` / `_cbtFetch()`
- [x] AbortController race guard
- [x] `openCbetaPassageReader()` reused (T236)
- [x] coverage.complete_text=False, note về đoạn trích
- [x] CASE D: không juan, không tạo labels giả
- [x] GROUP BY page (không duplicate)
- [x] 27/27 T238 tests PASS
- [x] NO DB mutation, NO schema change
- [x] ast.parse PASS

## Commit

`feat(T238): CBETA Text Browser -- Duyet van ban CBETA`
HEAD before: `ea00a8e`
