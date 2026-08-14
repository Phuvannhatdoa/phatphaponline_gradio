# Bug Report: Search Results Not Displaying in GUI Panels

> **Date:** 2026-04-17
> **Severity:** High
> **Status:** FIXED

---

## Issue Summary

When users search for entities like "Mã Tổ Đạo Nhất" on the Đạo Ảnh map:
- Data loads successfully (17 CBETA + 17 Taisho results in console)
- Console shows: `📋 Loaded: M01164 | CBETA: 17 | Taisho: 17`
- **BUT** Workbench panels don't show the new content
- Panels still display old "Thiếu Lâm Tự" data

---

## Root Cause Analysis

### 1. Wrong HTML IDs Used
- **Expected IDs:** `panel-vn-list`, `panel-a-list`, `panel-b-list`
- **Code was using:** `block1-content`, `block2-content`, `block3-content` (non-existent)

### 2. Auto-render on Page Load
- `index.html` was calling `renderPanelList()` on page load with hardcoded "Thiếu Lâm Tự" data
- This overwrote search results after they were loaded

### 3. Race Condition
- Search results loaded async, but auto-render fired after page load
- No proper callback chain to update panels after search completed

---

## Environment

- **URL:** https://phatphaponline.org/daoanh/
- **Backend:** Flask port 5000
- **Files:**
  - `src/js/search.js` - Main search logic
  - `index.html` - HTML with workbench panels

---

## Console Evidence

```
🚀 Bắt đầu quy trình SSOT cho: Mã Tổ Đạo Nhất
📋 Block search: 1 results
📋 CBETA "Mã Tổ Đạo Nhất": 17
📋 Taisho "Mã Tổ Đạo Nhất": 17
📋 Loaded: M01164 | CBETA: 17 | Taisho: 17
✅ Đã đồng bộ SSOT thành công cho: Mã Tổ Đạo Nhất
```

**Data loaded successfully but GUI not updating.**

---

## Related Issues

- Previous fixes in SESSION.md V17, V18, V19
- Dedup fix (V19) - changed Set to Map with displayName key
- UI interaction fix - Tab/Enter keyboard navigation
- Loading indicator fix - spinning 🔄 animation