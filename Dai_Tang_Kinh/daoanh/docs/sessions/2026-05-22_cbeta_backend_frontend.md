# Session: CBETA Backend + Frontend

**Date:** 2026-05-22
**Task:** Integrate CBETA (Chinese Buddhist Electronic Text Association) into Đạo Ảnh admin — search place/person mentions across the CBETA canon from the placevn UI.

## References / Khoá

- **Roadmap:** `docs/roadmap.md` §5.3 (CBETA integration)
- **Source:** `data/cbeta/` — schema, import script, raw XML
- **Related:** `data/cbeta/schema_cbeta.sql`, `data/schema_cbeta_mentions.sql`

## Changes Made

### 1. Import Script Improved (`data/cbeta/import_cbeta.py`)
- Enhanced `parse_xml()` to also extract `<head>` and `<item>` elements (not just `<p>`)
- Fixed FTS schema: removed `content='cbeta_content_index'` (standalone FTS5, triggers handle sync)
- Fixed XPath for `pb` lookup (removed unsupported `preceding::` axis)
- Added dedup on extracted text to avoid duplicate rows
- FTS count now correct (3917 rows for T51n2076)

### 2. Flask Routes Added (`app.py`, lines 786-870)
- `CBETA_PATH` constant + `get_cbeta_conn()` helper
- **`POST /daoanh/api/admin/cbeta/search-place`**: Search place name across CBETA. Two-step: (1) `cbeta_place_mentions` table for annotated mentions, (2) FTS5 full-text search for implicit mentions. Merged results with type flag.
- **`POST /daoanh/api/admin/cbeta/search-person`**: Same pattern for person names.
- **`GET /daoanh/api/admin/cbeta/stats`**: DB statistics (text count, paragraph count, FTS entries, import log, mentions).

### 3. React Component Added (`admin/placevn.html`)
- **`cbetaInputRef`**: `useRef` for search input
- **State**: `cbetaResults`, `cbetaTotal`, `cbetaLoading`, `cbetaSearched`
- **`handleCbetaSearch()`**: POST to `/daoanh/api/admin/cbeta/search-place` with the query, renders results
- **Auto-fill**: On place load, `cbetaInputRef` auto-populated with `details.name_zh`
- **UI**: Search input + "Tra" button + results list (sigla, title, juan, page, context snippet, CBETA Online link). Styled with amber accent to differentiate from CBDB's emerald.

### 4. FTS Schema Fixed (`data/cbeta/schema_cbeta.sql`)
- Removed `content='cbeta_content_index'` from FTS5 definition — was causing "no such column: T.sigla" error because content table doesn't have `sigla`/`title_zh` columns
- Now standalone FTS5 with triggers that join `cbeta_texts` at INSERT time

## Test Data

| Metric | Value |
|--------|-------|
| Texts imported | 1 (T51n2076, 景德傳燈錄) |
| Content paragraphs | 3917 |
| FTS entries | 3917 |
| Place mentions | 0 (no inline annotations in this file) |
| Person mentions | 0 (no inline annotations in this file) |

## Pipeline
- ✅ Lint: All HTML files pass
- ✅ Test: Passes
- ✅ E2E: All pages passed
- ❌ e2e:runtime: Playwright browser not installed (infrastructure issue, not code issue)

## Next Todo
- Import more CBETA volumes when network is available
- Replace `<mark>` in FTS snippets with proper color span for React dangerouslySetInnerHTML
- Person search frontend (personvn.html)
- CBETA full-text search block (search any term, not just place/person names)
