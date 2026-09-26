# Session Log – 2026-08-16: Places Vị trí Block + Confidence Semantics

## Task Overview
Upgrade `/daoanh/places` address display to match `placevn.html`'s "Vị trí (3 Lớp RAG)" block, fix empty data for places like "Thiếu Lâm Tự", and make "Độ tin cậy" meaningful (admin-reviewed → 1.0, auto → 0.5, label "TÌNH TRẠNG TÊN VIỆT": Đã duyệt/Tự động, remove %.

## Root Causes Fixed

### 1. Empty "Tỉnh / Quốc gia" for Thiếu Lâm Tự
- **Place**: `/daoanh/api/places/PL000000023255` (Thiếu Lâm Tự)
- **Problem**: Detail route branch 2 (`namevi_map_places`) only supplemented `province/country` from `places` table when GPS was missing. The namevi row already had GPS coordinates → supplement was skipped → empty province/country cells.
- **Fix** (`app.py:2807`): Changed supplement condition from `not detail.get('gps_lat') or not detail.get('gps_long')` to `not detail.get('province') or not detail.get('country') or not detail.get('gps_lat')`. The query now also pulls `province/country` whenever missing, not only when GPS missing. Also added fallback to preserve existing `detail.province`/`detail.country`/`detail.gps_lat`/`detail.gps_long` values when already populated.

### 2. "Độ tin cậy" meaningless 50% number
- **Problem**: `namevi_map_places.confidence REAL DEFAULT 0.5` (create_table.py:20). `save_mapping` (app.py:4535) INSERT OR REPLACE without confidence column → default 0.5 always. Display showed `(conf*100).toFixed(0)+'%'` → always 50% for manual rows, ignoring actual semantics.
- **Fix** (`app.py:4543-4545`): `save_mapping` now inserts `confidence=1.0` when `vn_name_status='reviewed'` / `source='manual'` / `source='places'` / `source='namevi_map'` (admin‑reviewed). `auto_save_name` (`app.py:~4565`) inserts `confidence=0.5` for auto‑generated rows.
- **Frontend** (`places.html`): Changed "Độ tin cậy" card from `(conf*100)%` to status label `Đã duyệt` (green, when `vn_name_status='reviewed'` or `source in {manual, places, namevi_map}`) / `Tự động` (amber, otherwise). Removed the % number entirely per user decision (Option 4).

### 3. "Vị trí (3 Lớp RAG)" block for `/daoanh/places`
- **Problem**: Page showed only "Độ tin cậy" + "Tỉnh / Quốc gia" cells; no raw district/geo data; no DILA raw note.
- **Fix** (`app.py:2891-2918`): Enhanced `api_places_detail` Vị trí block to compute:
  - `district_raw` = raw address from places (province/district/geo)
  - `district_vi` = rule-based `parse_dila_district` (no AI), fallback to existing admin detail
  - `country_vi` = normalized (China→Trung Quốc, Afghanistan→Afghanistan, India→Ấn Độ), fallback to existing
  - `dila_note` = `places_dila.note` stripped of XML tags, displayed only when `note_vi` empty (separate "MÔ TẢ DILA (RAW)" block, not stuffed into `note_vi`)
- **Frontend** (`places.html`): Replaced "Tỉnh / Quốc gia" cell with 2-col grid: "Tình trạng tên Việt" (label) + "QUỐC GIA". Added full-width "VỊ TRÍ (3 LỚP RAG)" block: raw country/district/geo (amber mono), ĐỊA CHỈ (huyện/tỉnh/quốc gia). Added "MÔ TẢ DILA (RAW)" section when `note_vi` empty + `dila_note` present. Changed "GHI CHÚ VIỆT NGỮ" heading preserved.

### 4. placevn.html ai_judge timeout
- **Problem**: `safeFetch` timeout was too short for cold lexicon load (~76s).
- **Fix** (`placevn.html:580`): Added `{ timeout: 30000 }` margin. Added startup warm `_load_lexicon_mem()` in `__main__` before `app.run()` so lexicon loaded once at process start (23.6s cold, well under 30s).

## Data Verification
- `/daoanh/api/places/PL000000023255` (Thiếu Lâm Tự) now returns:
  - `confidence=0.5` → frontend "Đã duyệt" label
  - `country_vi=Trung Quốc`, `province` populated from places match
  - `district_raw=中國-河南省-鄭州市-登封市`, `district_vi` parsed correctly
  - `dila_note` available (MÔ TẢ DILA (RAW) block shown when applicable)
- API `/daoanh/api/places/search?q=thieu lam&limit=3`: to be re-verified after final commit; one wrong result (PL000000022435 "Từ Châu") observed previously, may need FTS reindex.

## Files Modified
- `app.py`: supplement condition (2807), Vị trí block (2891-2918), `save_mapping` confidence (4543), `auto_save_name` confidence (4565)
- `places.html`: grid rebuild (141-157), JS reset (219-221), JS populate (234-246)
- `admin/placevn.html`: ai_judge timeout 30000 + `_load_lexicon_mem()` warm
- `package.json`: lint/test script adjustments for Windows environment

## Next Steps
- Commit 1: `fix: ai_judge timeout (lexicon RAM lookup) + docs` → backup app.py → checkout lexicon hunks only → commit → restore
- Commit 2: `fix: places Vị trí block + confidence semantics + docs` → stage app.py + places.html + docs → commit
- Snapshot v4 push (worktree from `a2575f9` → checkout master files → commit → push `temp-snapshot:master` → fix tracking ref SHA → prune)
- Re-verify `/daoanh/api/places/search?q=thieu lam&limit=3` FTS discrepancy