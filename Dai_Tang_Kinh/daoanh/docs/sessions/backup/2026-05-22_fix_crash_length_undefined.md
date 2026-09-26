# Session: Fix React App crash — .length on undefined (knowledgeData.cbetaIds)

**Date:** 2026-05-22
**Bug:** `TypeError: Cannot read properties of undefined (reading 'length')` at `App` component, line 1145.

## Root Cause

The `knowledgeData` hook's **default return** (when `details` is null on initial render) was:

```js
{ bibls: [], variants: [], xmlNote: "" }
```

Missing `cbetaIds: []`.

The JSX on **line 1145** called `knowledgeData.cbetaIds.length > 0` **without optional chaining** — a separate expression from line 1142 (which safely checks `!knowledgeData.cbetaIds || ...`). In JSX, all expressions are evaluated every render, so line 1145 crashed regardless of line 1142's short-circuit.

## Fix

**Fix 1 — Add `cbetaIds: []` to default** (`admin/placevn.html:718`):
```js
// Before (crash when details=null)
if (!details) return { bibls: [], variants: [], xmlNote: "" };
// After
if (!details) return { bibls: [], variants: [], xmlNote: "", cbetaIds: [] };
```

**Fix 2 — Optional chaining** (`admin/placevn.html:1145`):
```js
// Before
{knowledgeData.cbetaIds.length > 0 && ...}
// After
{knowledgeData.cbetaIds?.length > 0 && ...}
```

## Verification

- Playwright e2e runtime test: 2/2 passed, no JS console errors
- `npm run pipeline`: all 4 stages passed (lint, test, e2e syntax, e2e runtime)

## Files changed

- `admin/placevn.html` — 2 lines (default + optional chaining)
