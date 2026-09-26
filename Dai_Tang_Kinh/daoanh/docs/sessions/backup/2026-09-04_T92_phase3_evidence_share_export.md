# SESSION: T92 Phase 3 — Evidence UI + Share/Bookmark/Export + Data-Quality Flag

> **Date:** 2026-09-04
> **Status:** DONE
> **Task:** T92-nexus-implementation-plan.md (Phase 3)
> **Files modified:** `places.html` (frontend-only, 1 file)
> **Backend changes:** NONE (api_nexus unchanged)
> **Rollback:** `git checkout 5300e0f -- daoanh/places.html daoanh/app.py`

---

## Changes Summary

### 1. Evidence UI (DILA/CBETA/FOSIZHI source badges)

**`_nexusEvidenceSource(e)`** — detects source from `ref`/`citation`:
- `CBETA`: ref contains "CBETA" or citation matches `T\d+n\d+`, `X\d+n\d+`, `J\d+n\d+` pattern
- `FOSIZHI`: ref contains "FOSIZHI", "FZ", or "佛寺志"
- `DILA`: ref contains "DILA", "PL", or "daoanh"
- `NGUỒN`: fallback for any other source with ref

**Edge rendering** (`_renderVisGraph`):
- Edges WITH evidence → darker color (`#8a5c08cc` vs `#8a5c0866`), brighter font (`#e0d5b8` vs `#6a5f4d`)
- Edge tooltip: `"Nguồn: [CBETA]\nT51n2076\nCBETA: T51n2076_p0393c16"` format

**Header badges** (`#nmp-evidence-summary`):
- Colored chips: DILA=green, CBETA=cyan, FOSIZHI=purple, NGUỒN=gray
- Shows counts (e.g., "DILA 12 · CBETA 8")

**Detail panel** (`_nexusShowDetail`):
- Evidence grouped by source with colored left-border blocks
- Each source shows count badge + up to 4 refs

### 2. Data-Quality Flag (`_nexusQualityBadge`)

Three warning badges for incomplete data:
- ⚠ "Chưa gắn ID DILA" — person node with `navigable=false`
- ⛔ "Entity_id NULL (synthetic)" — `pers-*` prefixed synthetic nodes
- ◯ "Cô lập (0 cạnh)" — node with no edges

### 3. Share Link (`_nexusShareLink`)

- Creates URL: `?nexus_root=<id>&nexus_type=<place|person>`
- Copies to clipboard via `navigator.clipboard`
- Visual feedback: "✓ Đã sao chép" in green for 2s

### 4. Bookmark (`_nexusBookmark` + `_nexusUpdateBookmarkBtn`)

- Saves/removes from `localStorage('nexus_bookmarks')`
- Each entry: `{id, type, label, label_zh, ts}`
- Toggle button: "⭐ Lưu" ↔ "✓ Đã lưu" with gold color

### 5. Export Graph (`_nexusExportGraph`)

- **JSON**: full `nodes[]` + `edges[]` + `center` + `stats` → auto-download `nexus-{type}-{id}.json`
- **PNG**: vis.js canvas `toDataURL('image/png')` → auto-download `nexus-{type}-{id}.png`

### 6. URL Parameter Auto-Load

- `window.onload` checks `nexus_root` + `nexus_type` URL params
- Auto-calls `selectItem(nexusRoot)` → 600ms delay → auto-clicks Nexus tab button

### 7. Edge Visual Enhancement

- Legend text updated: "Di chuột lên cạnh để xem nguồn · Cạnh sẫm = có bằng chứng"
- Edges with evidence render darker/brighter than edges without

---

## Verification

| Check | Result |
|-------|--------|
| JS syntax (node --check) | ✅ OK |
| py_compile app.py | ✅ OK |
| 22 HTML elements present | ✅ PASS |
| 8 Phase 3 functions present | ✅ PASS |
| 4 integration points present | ✅ PASS |
| Backend unchanged | ✅ CONFIRMED |

---

## What's NOT changed

- `app.py` — zero backend modifications
- `event_text_link` schema — unchanged
- Node/edge contract — unchanged
- Existing Phase 1/2 code — untouched
