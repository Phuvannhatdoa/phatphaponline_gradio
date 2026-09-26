# Changes — Session 2026-09-05

## Files Modified
- `places.html` — 4 UX fixes
- `app.py` — FIX 1 alias enrichment in `api_places_graph`

## Backup Created
- `docs/sessions/2026-09-05/places.html.bak`
- `docs/sessions/2026-09-05/app.py.bak`

## FIX 1: Global UI Standard — Viet/Han-Viet truoc, Han sau

Added `_fmtName(name_vi, name_zh)` global helper (places.html, near `_t86NodeLabel`):
- Returns `vi (zh)` when both present and different
- Returns `vi` alone or `zh` alone when only one is available
- Returns empty string for null/undefined inputs

Updated:
- `_t86NodeLabel(n)` — now uses `_fmtName(n.name_vi, n.name_zh)`
- `_biLabel(vi, zh, fb)` in `_gmpBuildDatasets` — uses `_fmtName`
- Alias chip display in `renderGraphTab` altBox — uses `_fmtName(a.vi, a.zh)`
- Alias nodes in `_gmpBuildDatasets` — uses `_fmtName(a.vi, a.zh)`
- `_dtRenderRelated` entity labels — uses `_fmtName(name_vi, name_zh)`

`api_places_graph` in app.py:
- `alt_names` now returns `[{zh, vi}]` objects instead of plain strings
- Looks up `name_vi` from `namevi_map_places` WHERE `name_zh = alt_name`
- Frontend handles both formats (backward compat via `_normalizeAlias`)

## FIX 2: Tab Quan He — MANG LUOI DAN CHIEU

- Header changed: "Quan He Thuc The Lien Quan" -> "Mang Luoi Dan Chieu"
- `_dtRenderRelated()` rewritten with:
  - Dynamic summary stats line
  - Amber warning box: "Cung xuat hien trong van ban khong dong nghia voi quan he lich su"
  - Section A: "Quan He Da Bien Tap" — curated persons from place_person_link
  - Section B: "CUNG XUAT HIEN TRONG VAN BAN" — places + canonical persons (co-mention)
  - Section C: "Nguon Anh Xa Kinh Dien" — text mappings
  - All entity labels use `_fmtName(name_vi, name_zh)`
  - Places deduped by entity_id

## FIX 3: Tab Do Thi — Controls + LOD

- Added "Mo tat ca" / "Tong quan" buttons
- Added "Chi co dan chung" toggle button with `_gmpFilterEvidence()`
- `_graphEvidenceOnly` flag: filters edges to only those with `ref` or `has_ref`
- Legend updated: solid=xac minh, dotted=cung xuat hien, dashed=dan chieu
- Alias chips use `_fmtName` label with raw Han as tooltip

## FIX 4: Phap he (Lineage) — Cay khong lap ancestor

`_renderLineageChain()` Section 2 rewritten:
- Removed: DFS path-per-leaf (caused node repetition)
- Added: `treeVisited` Set initialized with `center` + all `ancestors`
- Added: `_mkTreeLi(pid, depth)` recursive function:
  - Cycle guard: if `treeVisited.has(pid)` renders `[chu ky — name]` placeholder
  - Each canonical ID renders EXACTLY ONCE
  - Children as nested ul/li with arrow connectors
  - Depth limit 8
- Result: Hue Vien / Phap Thuong / Hue Quang each appear once

## GRAPH REDESIGN 2026-09-05 — 3-Node Default View (Đồ Thị Quan Hệ)

### Backup
- `docs/sessions/2026-09-05/places.html.bak2`

### HTML Changes (places.html)
- **Line 667**: Added "Cùng xuất hiện" toggle button `#gf-comention` in controls bar
- **Line 682**: Refactored canvas wrapper to `display:flex;flex-direction:column`
- **Line 684**: Added `#gmp-alias-chips` strip (HTML overlay for alias names — NO vis.js nodes for aliases)
- **Line 688**: Added `#gmp-mobile-fallback` div (accordion tree for viewport < 768px)
- `gmp-canvas` changed from `height:100%` to `flex:1` in flex column

### JS Changes (places.html)
New state variables:
- `_graphDataset` — `{ nodes: vis.DataSet, edges: vis.DataSet }` for live expand/collapse
- `_graphCoMentionVisible` — toggle state for co-mention edge visibility

New functions added (lines ~3591–3790):
- `_srcToViet(src)` — maps Chinese source book titles to Vietnamese full names
- `_gmpRenderAliasChips(d)` — renders alias chips as HTML overlay above canvas
- `_gmpExpandWorks(d, dataset)` — replaces group-works node with individual text nodes (level -2)
- `_gmpExpandPersons(d, dataset)` — replaces group-persons node with subgroup nodes by source (level 2)
- `_gmpExpandSubgroup(subgroupId, d, dataset)` — expands subgroup to individual person nodes (level 3)
- `_gmpMobileFallback(d)` — renders `<details>` accordion tree in `#gmp-mobile-fallback`
- `_gmpToggleCoMention()` — show/hide co-mention dashed edges via DataSet.update
- `_gmpReset()` — alias for `_renderGraphMainPanel(_graphData, true)`

Updated functions:
- `_renderGraphMainPanel` — complete rewrite; default 3-node view using `vis.DataSet` (root + group-works level=-1 + group-persons level=1); LR hierarchical layout; click handler dispatches to expand functions
- `_gmpExpandAll()` — now uses `_graphDataset` to expand via DataSet mutations; warns if > 20 nodes
- `_gmpCollapseAll()` — now calls `_gmpReset()` instead of re-render

Layout spec:
- `hierarchical: { direction:'LR', levelSeparation:220, nodeSpacing:80 }`
- Works (texts) at level -1/-2 (left of root), Persons at level 1/2/3 (right)
- Edge colors: verified #c8a96e solid, co-mention #666 dashed opacity:0.4

Preserved (NOT modified):
- `_gmpBuildDatasets` — kept unchanged (no longer called in main flow but not deleted)
- `_gmpBuildRelList`, `_gmpRelRowClick`, `_gmpShowNodeDetail`, `_gmpCloseDetail`
- `_gmpToggleFilter`, `_gmpAliasToggle`, `_gmpFilterEvidence`
- `renderGraphTab` — unchanged

## Acceptance Tests Status
- [x] Header "MANG LUOI DAN CHIEU"
- [x] Amber warning box
- [x] 3 sections A/B/C separate
- [x] _fmtName used globally
- [x] No "undefined ()" or "null ()"
- [x] Lineage tree: each node once, cycle guard works
- [x] "Chi co dan chung" filter button
- [x] app.py syntax valid
