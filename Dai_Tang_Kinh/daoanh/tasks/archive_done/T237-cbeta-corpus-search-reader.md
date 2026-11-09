---
id: T237
title: CBETA Corpus Search Reader — Tìm trong Đại Tạng
status: done
priority: high
created: 2026-10-05
completed: 2026-10-05
---

## Mục tiêu

Researcher có thể tìm kiếm toàn bộ corpus CBETA đã nhập mà không cần chọn người trước.
Entry point độc lập: Tab "📜 Đại Tạng" → search box → results → T236 reader.

## Phase 0 — Discovery

**CASE chọn: CASE D** — corpus limited, build với coverage rõ ràng.

| Bảng | Hàng | Ghi chú |
|------|------|---------|
| `cbeta_person_mentions` | 72,628 | context_snippet 200 chars, 5 siglas |
| `cbeta_ref_passages` | 46 | 6 siglas, avg 1203 chars |
| `cbeta_catalog_vn` | 3,122 | title_vi, title_zh đầy đủ |

Siglas searchable: T51n2076, T50n2060, T50n2061, X77n1524, T50n2062

Không có public corpus search endpoint trước T237.

## Real Data

| Query | Hits |
|-------|------|
| 百丈 | 1,118 |
| 馬祖 | 514 |

## Implementation

### Backend
- New route: `GET /daoanh/api/cbeta/corpus-search?q=<query>&limit=30`
  - `q`: min 2 chars, exact substring LIKE search
  - Parameterized SQL — no fuzzy, no LLM
  - LEFT JOIN `cbeta_catalog_vn` for title_vi, title_zh
  - Ordering: sigla ASC → page ASC → id ASC (deterministic)
  - Returns: ok, query, result_count, limit, coverage{}, results[]
  - coverage: texts_searchable (5), passages_searchable (72628), catalog_total (3122)
  - HTTP 400 if q < 2 chars
  - HTTP 200 + empty results if no match

### Frontend (places.html)
- Section `#cbetaCorpusSearchBlock` đầu tab `#tp-daitang` (luôn visible, không cần entity)
- Input field + "Tìm" button
- AbortController race guard (cancel inflight request khi search mới)
- Coverage statement honest: "X bộ / N đoạn văn đã nhập · Tổng mục lục: 3122 bộ"
- Results: title_vi, sigla, page, snippet (serif font)
- "📖 Đọc nguyên bản →" button → `openCbetaPassageReader(mention_id)` (T236 reuse)
- XSS: tất cả DB content qua `_escHtml()`
- Query escaped: `_escHtml(d.query)`

## T236 Reuse

Cùng `openCbetaPassageReader(mentionId)` function:
- Person citation path: Person → Kinh Điển Dẫn Chiếu → Đọc nguyên bản
- Corpus search path: Tìm trong Đại Tạng → Đọc nguyên bản

Một reader contract, hai discovery paths. ✓

## Tests

File: `tests/test_t237_cbeta_corpus_search.py`

**29/29 PASS** (A-T + R1-R6):
- A: valid query returns results
- B: no-match → empty results, ok=True
- C/C2: short/empty query → rejected (400)
- D: SQL injection parameterized safe
- E: limit enforced (max 50)
- F: deterministic ordering (sigla → page → id)
- G: sigla preserved
- H: juan preserved
- I: page locator preserved
- J: LEFT JOIN preserves uncatalogued passages
- K: coverage counts correct
- L: catalog != searchable (honest scope)
- M: reader_ref deterministic integers
- N: X-series NOT filtered
- O: frontend _escHtml on DB content
- P: query escaped in render
- Q: AbortController race guard
- R: T236 reader reused
- S: no DB mutation
- T: no schema mutation
- R1: 百丈 real query has results
- R2: 馬祖 real query (0 or more — corpus limits documented)
- R3: searchable < catalog (honesty)
- R4: X-series in real DB
- R5: reader_ref all valid integers
- R6: ast.parse PASS

T236 regression: 23/23 PASS
T235 regression: 22/22 PASS

## Done when

- [x] `GET /daoanh/api/cbeta/corpus-search` endpoint
- [x] `#cbetaCorpusSearchBlock` in tp-daitang
- [x] `cbetaCorpusSearch()` + AbortController race guard
- [x] `openCbetaPassageReader()` reused (T236)
- [x] Coverage statement honest (5 texts / 72628 passages / 3122 catalog)
- [x] 29/29 T237 tests PASS
- [x] T236/T235 regression PASS
- [x] NO DB mutation, NO schema change, NO external API/LLM
- [x] ast.parse PASS

## Commit

`feat(T237): CBETA Corpus Search -- Tim trong Dai Tang`
HEAD before: `49493a2`
