---
id: BUG-012
title: "Persistent marker re-triggers selectItem — cluster marker click không update left panel"
module: GIS / Places
priority: P1
status: done
depends_on: []
created: 2026-09-09
updated: 2026-09-16
done_when:
  - Click cluster marker (sau khi filter active) → left panel update đúng ID mới
  - Không có double-fire selectItem (network log chỉ có 1 API call cho ID mới)
  - Persistent marker chuyển sang ID mới ngay sau click, không giữ marker cũ
---

## Triệu chứng

Sau khi filter pill "Chùa / Tự viện" được active và có 1 địa danh đang chọn (persistent marker),
click vào cluster marker khác xung quanh → left panel không cập nhật sang ID mới.

## Root cause

`persistentMarkerLayer` (marker đang chọn, `zIndexOffset: 9000`) chỉ được update trong filter pill
click handler, **không** update trong `selectItem()`.

Khi click cluster marker mới (ví dụ PL023153):
1. `selectItem('PL023153', lat, lng)` → `_selectToken = N`
2. Old persistent marker (vd PL056722, `zIndex: 9000`) vẫn nằm trên map
3. Event propagation hoặc z-order overlap → persistent marker re-fire `selectItem('PL056722')`
   → `_selectToken = N+1`
4. PL023153 response có token=N, `_selectToken=N+1` → DISCARDED (BUG-011 guard)
5. Left panel: PL056722 thắng, không update sang PL023153

Evidence từ network log:
```
PL023153/unified → 200 OK  (bị discard)
PL056722/unified → 200 OK  (thắng — từ persistent marker re-fire)
```

## Fix

`places.html` — trong `selectItem(id, lat, lng)`, sau dòng `_selectedLat/_selectedLng` capture:
thêm code clear `persistentMarkerLayer` và re-add persistent marker cho **ID mới** ngay lập tức.

File: `daoanh/places.html`  
Dòng thêm: sau line ~1050

## Acceptance criteria checklist

- [ ] Click cluster marker sau khi filter active → left panel load đúng ID mới
- [ ] Network log: chỉ 1 `unified` call cho ID mới, không có double-fire
- [ ] Persistent marker icon chuyển sang vị trí ID mới sau click
- [ ] Console: không có error
- [ ] BUG-011 token guard vẫn hoạt động (click rapid không gây stale render)
