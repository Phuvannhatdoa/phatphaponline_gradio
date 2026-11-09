---
id: T235
title: CBETA Person Citation Panel — Kinh Điển Dẫn Chiếu
status: done
priority: high
created: 2026-10-05
completed: 2026-10-05
---

## Mục tiêu

Hiển thị dữ liệu `cbeta_person_mentions` (72,628 rows, 10,173 persons) trong person detail panel của `places.html`. Researcher có thể thấy kinh điển CBETA nào đề cập đến thiền sư đang xem.

## Approved contract

Từ PTDA-NEXT-PRODUCT-BUILD-03 + T235-CBETA-PERSON-CITATION-PANEL-BUILD-01.

## Implementation

### Backend
- Route: `GET /daoanh/api/monk/<dila_id>/cbeta-mentions`
- File: `app.py` (sau `api_monk_marcus_network`, trước `admin_dila_stats`)
- Query: `cbeta_person_mentions LEFT JOIN cbeta_catalog_vn ON sigla`
- Group by text, order by `mention_count DESC, sigla ASC`
- Snippets: tối đa 3/text, `rowid ASC`
- X77n1524 và mọi sigla đều được giữ (evidence surface, không filter)
- Unknown dila_id → HTTP 200 `{ok:true, mention_count:0, texts:[]}`

### Frontend
- File: `places.html`
- DOM: `#personCbetaCitationsBlock` (class `da-block hidden`) sau `#personEventsBlock`
- Function: `loadCbetaCitations(dilaId)` — non-blocking, secondary fetch
- Race guard: `_currentPlaceId !== requestedId` discard stale response
- XSS: toàn bộ DB content qua `_escHtml()`
- Snippets: `<details>/<summary>` collapsible
- Zero mentions → section ẩn hoàn toàn

## Tests

File: `tests/test_t235_cbeta_person_citations.py`

22/22 PASS:
- A: existing person ok
- B: correct total mention_count
- C: correct text grouping (incl. orphan text — evidence surface)
- D: per-text mention count
- E: max 3 snippets/text
- F: deterministic text ordering
- G: deterministic snippet ordering
- H: LEFT JOIN fallback
- I: unknown dila_id zero-result
- J: no DB mutation
- K: no schema change
- L: frontend DOM section exists
- M: zero-result section hidden
- N: race guard exists
- O: XSS escaping
- P: bio independent from CBETA fetch
- R1: A001897 actual = 7 mentions
- R2: A001897 in T51n2076 = 6 mentions
- R3: A003623 actual = 0 mentions
- R4: unknown ID zero result
- R5: route defined in app.py
- R6: py_compile PASS

## DB Verification

| dila_id | Thực tế DB (2026-10-05) |
|---------|--------------------------|
| A001897 (Bạch Trượng Hoài Hải) | 7 mentions · 2 texts (T51n2076×6, T50n2062×1) |
| A003623 (Mã Tổ Đạo Nhất) | 0 mentions (expected — not subject of biography section) |

## Done when

- [x] Endpoint `/daoanh/api/monk/<dila_id>/cbeta-mentions` hoạt động
- [x] 22/22 focused tests PASS
- [x] py_compile app.py PASS
- [x] DOM section `#personCbetaCitationsBlock` tồn tại trong places.html
- [x] Race guard pattern exists
- [x] XSS escaping verified
- [x] NO DB mutation, NO schema change, NO external API/LLM

## Commit

`feat(T235): CBETA Person Citation Panel — Kinh Dien Dan Chieu`
HEAD before: `d7fba6a`
