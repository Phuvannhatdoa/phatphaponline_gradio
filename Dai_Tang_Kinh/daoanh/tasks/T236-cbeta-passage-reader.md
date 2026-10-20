---
id: T236
title: CBETA Passage Reader — Đọc trong nguyên bản
status: done
priority: high
created: 2026-10-05
completed: 2026-10-05
---

## Mục tiêu

Sau T235 (Kinh Điển Dẫn Chiếu), researcher có thể click snippet để đọc nguyên bản Hán văn. Loại bỏ dead end: Person → Citation → (hết). Thay bằng: Person → Citation → Passage Reader.

## Phase 0 — Discovery

**CASE chọn: CASE D** (minimal read-only passage reader vertical slice)

Kết quả inspection:
- `cbeta_ref_passages`: 46 rows, 6 siglas, chỉ 1,089/72,628 mentions (1.5%) có exact sigla+page match
- A001897 (Bạch Trượng): 0/7 citations match cbeta_ref_passages → tất cả dùng context_snippet
- `context_snippet`: 200 chars Hán văn, là primary source text cho tất cả mentions
- Không có CBETA reader page hiện có
- Không có fuzzy matching — chỉ exact sigla+page join

## Resolution Contract (Deterministic)

```
Priority 1: cbeta_ref_passages WHERE sigla=pm.sigla AND page=pm.page → han_text (2000-3000 chars)
Priority 2: pm.context_snippet (200 chars)
Priority 3 (NONE): empty → NO button, no fake link
```

## Implementation

### Backend
- Modified `api_monk_cbeta_mentions` (T235 endpoint): thêm `mention_id` vào snippet response
- New route: `GET /daoanh/api/cbeta/person-passage/<int:mention_id>` in app.py
  - LEFT JOIN cbeta_catalog_vn cho title_vi, title_zh
  - Exact sigla+page match cbeta_ref_passages → richer han_text
  - Fallback: context_snippet
  - passage_source: 'cbeta_ref_passages' | 'context_snippet' | 'NONE'
  - Unknown mention_id → HTTP 404

### Frontend  
- Modal `#cbetaPassageModal` added to `</body>` of places.html
  - Header: title_vi, title_zh, sigla badge, page, juan, person_name_zh, source badge
  - Body: `cpm-passage` dùng `.textContent` (XSS safe), font-serif, line-height 2
  - Footer: attribution + Close button
  - Backdrop click closes
- In `loadCbetaCitations()` snippet renderer: "📖 Đọc trong nguyên bản →" button
  - ONLY when `sn.context_snippet` non-empty AND `sn.mention_id` present
  - Calls `openCbetaPassageReader(mention_id)` (integer, no injection)

## Tests

File: `tests/test_t236_cbeta_passage_reader.py`

23/23 PASS (A-M + R1-R6):
- A-C: sigla, juan, page correct
- D: cbeta_ref_passages richer text when available
- D2: context_snippet fallback
- E: deterministic
- F: empty citation → NONE + no fake link
- G: X-series preserved (X77n1524 x14,637 rows)
- H: unknown mention_id → None (404)
- I: no fabrication
- J/K: no DB/schema mutation
- L: T235 backward compatible (mention_id in snippets)
- M: race guard — reader is mention_id-based, independent of person switching
- R1: A001897 IDs present (7 mentions)
- R2: A001897 matches 0 ref_passages (context_snippet fallback confirmed)
- R3: A001897 snippets all non-empty
- R4: route defined
- R5: X-series count 14,637 preserved
- R6: ast.parse PASS

T235 regression: 22/22 PASS

## DB Actual

| mention_id | sigla | page | passage_source | passage_len |
|------------|-------|------|----------------|-------------|
| 2924 | T51n2076 | 0252b | context_snippet | 200 |
| 3796 | T51n2076 | 0268c | context_snippet | 200 |
| 5523 | T51n2076 | (empty) | NONE → no button | — |
| 5784 | T51n2076 | 0310a | context_snippet | 200 |
| 6069 | T51n2076 | 0315a | context_snippet | 200 |
| 14685 | T51n2076 | 0464b | context_snippet | 200 |
| 56279 | T50n2062 | 0916c | context_snippet | 200 |

## Done when

- [x] Endpoint `/daoanh/api/cbeta/person-passage/<int:mention_id>`
- [x] mention_id in T235 snippet response
- [x] Modal `#cbetaPassageModal` in places.html
- [x] "📖 Đọc trong nguyên bản →" button (only when snippet non-empty)
- [x] 23/23 T236 tests PASS
- [x] T235 22/22 regression PASS
- [x] ast.parse PASS
- [x] NO DB mutation, NO schema change, NO external API/LLM

## Commit

`feat(T236): CBETA Passage Reader -- Doc trong nguyen ban`
HEAD before: `30eff6e1`
