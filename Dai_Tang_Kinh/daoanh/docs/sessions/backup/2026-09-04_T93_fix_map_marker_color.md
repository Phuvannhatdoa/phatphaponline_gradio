# T93 — Fix màu marker bản đồ (temple_site → #ef4444)

**Ngày**: 2026-09-04  
**File thay đổi**: `places.html`  
**Commit 1**: `83d0cfe` — fix ban đầu (guessCate + doSearch) — chưa đủ  
**Commit 2**: `55a70ae` — fix root cause thật (markerMap + loadInitialPlaces)  
**Revert commit 2**: `git revert 55a70ae` hoặc `git checkout 83d0cfe -- places.html`  
**Revert cả 2**: `git revert 83d0cfe 55a70ae`

---

## Root Cause Thật (phát hiện ở session 2)

`markerMap` là `const {}` — **không bao giờ bị xóa** khi người dùng click pill filter.

Chuỗi lỗi:
1. Click pill `temple_site` → `clusterGroup.clearLayers()` xóa marker khỏi display
2. Nhưng `markerMap` vẫn giữ tất cả `{id: marker}` cũ (từ lần load trước với cate `''`, màu vàng)
3. `loadInitialPlaces('temple_site')` fetch xong → `addMarkerFromResult(r, 'temple_site')`
4. `addMarkerFromResult` hit guard: `if (markerMap[r.id]) return;` → **bỏ qua hoàn toàn**
5. Marker màu vàng cũ đã xóa khỏi cluster, marker đỏ mới không tạo được → **không hiện marker nào**

Root cause phụ: `loadInitialPlaces()` không dùng `guessCate` nên khi cate='' tất cả marker đều vàng, tích lũy vào `markerMap` và gây tắc nghẽn cho lần filter sau.

---

## Root Cause Phụ (phát hiện ở session 1, commit 83d0cfe)

API `/api/places` không trả về field `cate` hay `note_category` trong response — chỉ có:
```json
{"id":..., "name_zh":"...", "name_vi":"...", "lat":..., "lng":..., "type":..., "confidence":..., "source":...}
```

Khi search không có filter pill active, `currentCate = ''` → `dotColor = 'var(--pp-gold)'` thay vì `#ef4444`.

---

## Tất cả Fix đã áp dụng

### Session 1 — Commit `83d0cfe`

**Fix 1: Thêm `guessCate()` (line ~704)**
```javascript
function guessCate(nameZh) {
    if (!nameZh) return '';
    if (/[寺廟塔庵禪精舍伽藍石窟]/.test(nameZh)) return 'temple_site';
    if (/[山峰嶺崖岳丘]/.test(nameZh))            return 'mountain';
    if (/[江河湖溪潭海港渡]/.test(nameZh))         return 'river_lake';
    if (/[郡州路府道縣鄉]/.test(nameZh))           return 'dynasty_region';
    if (/[洞岩林原坡野]/.test(nameZh))             return 'other';
    return '';
}
```

**Fix 2: `doSearch()` — khi xóa search:**
```javascript
// TRƯỚC: loadInitialPlaces();
loadInitialPlaces(currentCate);
```

**Fix 3: `doSearch()` — khi có search results:**
```javascript
// TRƯỚC: data.results.forEach(r => addMarkerFromResult(r));
data.results.forEach(r => addMarkerFromResult(r, guessCate(r.name_zh) || currentCate));
```

---

### Session 2 — Commit `55a70ae`

**Fix 4: Pill click handler — xóa `markerMap` trước khi reload (line ~1081)**
```javascript
clusterGroup.clearLayers();
if (viLabels) viLabels.clearLayers();
// THÊM MỚI:
Object.keys(markerMap).forEach(k => delete markerMap[k]);
dynamicResults = [];
loadInitialPlaces(cate);
```

**Fix 5: `loadInitialPlaces` first batch — dùng `guessCate` khi không có pill (line ~1114)**
```javascript
// TRƯỚC: withGps.forEach(r => addMarkerFromResult(r, cate));
withGps.forEach(r => addMarkerFromResult(r, cate || guessCate(r.name_zh)));
```

**Fix 6: `loadInitialPlaces` pagination — dùng `guessCate` (line ~1130)**
```javascript
// TRƯỚC: gps.forEach(r => addMarkerFromResult(r, cate));
gps.forEach(r => addMarkerFromResult(r, cate || guessCate(r.name_zh)));
```

**Fix 7: `window.onload` — tránh `cate="undefined"` trong API URL (line ~4254)**
```javascript
// TRƯỚC: loadInitialPlaces();
loadInitialPlaces('');
```

---

## Verify code đúng vị trí

```
grep -n "delete markerMap\|dynamicResults = \[\]\|guessCate(r.name_zh)\|loadInitialPlaces('')" places.html
```

Kết quả mong đợi:
- `1081`: `Object.keys(markerMap).forEach(k => delete markerMap[k]);`
- `1082`: `dynamicResults = [];`
- `1114`: `withGps.forEach(r => addMarkerFromResult(r, cate || guessCate(r.name_zh)));`
- `1130`: `gps.forEach(r => addMarkerFromResult(r, cate || guessCate(r.name_zh)));`
- `4254`: `loadInitialPlaces('');`

---

## Constraints đã tuân thủ

- ✅ Không hardcode Thiếu Lâm Tự hoặc PL000000023255
- ✅ Không đặt tất cả marker thành màu đỏ
- ✅ Không ghi đè `marker-color` trong GeoJSON/dataset
- ✅ Không thêm `!important` vào CSS
- ✅ Không thay đổi database, XML/TEI, GeoJSON nguồn, API data contract
- ✅ Không đổi Leaflet sang thư viện map khác
- ✅ Không làm hỏng legend, popup, tooltip, click marker, cluster, filter, selected-state

---

## Bước tiếp theo: Deploy & Test

Deploy lên VPS (`root@158.220.106.183`) qua SSH/terminal:
```bash
scp places.html root@158.220.106.183:/path/to/daoanh/places.html
```

Verify sau deploy:
1. Mở tab `🗺 BẢN ĐỒ` tại `/daoanh/places`
2. Chọn pill `temple_site` — xác nhận marker đỏ `#ef4444` hiện ra
3. Bỏ chọn pill (tất cả) — search "寺" hoặc "廟" — xác nhận cũng màu đỏ
4. Xác nhận legend vẫn đúng, popup vẫn mở, cluster vẫn hoạt động
