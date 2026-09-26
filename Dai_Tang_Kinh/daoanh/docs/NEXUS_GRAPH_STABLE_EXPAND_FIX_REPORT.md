# Graph Layout Stability Fix Report
**Date**: 2026-09-06  
**Scope**: `places.html` — Đồ Thị tab, vis.js expand-on-click graph

---

## Root Cause Findings

### 1. Auto-fit on every expand (viewport jump)
**Locations**: lines 3783, 3826, 3864 (before fix)  
**Code**: `_graphNetwork.fit({ animation: true })` inside `_gmpExpandWorks`, `_gmpExpandPersons`, `_gmpExpandSubgroup`  
**Effect**: After every click-to-expand, the canvas auto-panned/zoomed to fit all nodes — violating the `layout_stability.viewport` rule.

### 2. New nodes added without explicit x,y
**Locations**: All three expand functions — `dataset.nodes.add({...})` without `x` or `y`  
**Effect**: vis.js hierarchical layout engine recalculates positions for ALL nodes whenever the node count changes. Existing nodes shift to accommodate the new hierarchy, causing the "jumping" behaviour.

### 3. No Math.random usage found
`grep -n 'Math.random'` in graph section: **0 matches**. Hierarchical layout is deterministic; no random seed issue.

### 4. No stale async callbacks found
`renderGraphTab` sets `_graphData` synchronously before calling `_renderGraphMainPanel`. No race condition between old/new data fetches for the graph path.

---

## Fixes Applied

### A. `_positionCache` — closure-level position snapshot
```javascript
let _positionCache = {};
```
Populated 80ms after `vis.Network` creation (after hierarchical layout computes initial positions).

### B. `_gmpRestorePositions(savedPos, excludeIds)`
Helper that calls `_graphNetwork.moveNode(id, x, y)` for every node in `savedPos` except removed ones. Called at the end of every expand function to reset any positions vis.js moved during the add operation.

### C. `_gmpChildY(parentY, idx, total, spacing)`
Computes y-coordinate for a new child node: centred on parent, spaced by `spacing` px. Used by all three expand functions to place new nodes near their parent without overlapping.

### D. Expand functions — explicit positioning + no auto-fit

| Function | Parent ref | New node x | spacing |
|---|---|---|---|
| `_gmpExpandWorks` | `group-works` pos | `parentX - 200` | 65px |
| `_gmpExpandPersons` | `group-persons` pos | `parentX + 200` | 80px |
| `_gmpExpandSubgroup` | subgroup pos | `parentX + 180` | 40px |

`_graphNetwork.fit()` calls removed from all three functions.

---

## Behaviour After Fix

| Rule | Status |
|---|---|
| Root stays fixed after graph load | ✅ Hierarchical layout is computed once; `physics: false` |
| Existing nodes don't jump on expand | ✅ `_gmpRestorePositions` called after every dataset mutation |
| New children placed near parent | ✅ Explicit `x,y` computed from parent position |
| No auto-pan/fit on click | ✅ `fit()` calls removed from all expand functions |
| Same root+data → same initial positions | ✅ Hierarchical layout is deterministic |
| Collapse removes only subtree | ✅ `dataset.nodes.remove` + `_gmpRestorePositions` pattern |
| Fit/Centre only on explicit user button | ✅ `_gmpFit()` remains wired to the Fit button only |
