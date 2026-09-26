# Session 2026-09-09 — BUG-012 GIS_SEARCH_MARKER_STATE_MISMATCH_001

**Bug:** Lệch state GPS/RAG giữa tìm kiếm và marker bản đồ  
**Alias:** GIS_SEARCH_MARKER_STATE_MISMATCH_001  
**File thay đổi:** `places.html`  
**Status sau session:** IMPLEMENTED / READY_FOR_ADMIN_TEST — CHỜ ADMIN CONFIRM DONE

---

## Repro Steps

1. Click icon chùa trên bản đồ → panel hiện đúng GPS: Đăng Phong, Trịnh Châu, Hà Nam
2. Gõ/chọn "Áo Lợi Trấn" trong ô tìm kiếm → panel chuyển sang PL000000022436 / 奧利鎮 ✓
3. **Lỗi:** Khối "Vị Trí · 3 Lớp RAG" vẫn hiện GPS của record cũ ✗
4. **Lỗi:** Web Update đang tra "Thiếu Thất Tự (Tạm dịch)" — tên của place vừa click ✗

---

## Root Cause Analysis

### Bug (A) — Web Update dùng entity sai

`initWebEnrichPanel(d.source_record_id)` tại line 1212 **chỉ được gọi bên trong `if (d.note)` block**.

Nếu entity mới (vd. Áo Lợi Trấn) qua unified path nhưng `src.dila.note` là null/empty:
- `if (d.note)` = false → `initWebEnrichPanel` KHÔNG được gọi
- `_currentEnrichEntityId` giữ nguyên ID của entity trước (Thiếu Thất Tự)
- Khi user nhấn "🌐 Cập nhật": `webEnrich()` → `entityId = _currentEnrichEntityId` = Thiếu Thất Tự ✗

### Bug (B) — GPS/RAG data cũ không bị clear kịp

`initWebEnrichPanel` không có `_selectToken` guard trong fetch callback. Nếu response từ entity cũ trả về sau response của entity mới, panel bị ghi đè bằng data sai.

Đồng thời `_currentEnrichEntityId` không được reset về `null` ngay khi `selectItem` bắt đầu, khiến khoảng thời gian giữa 2 async fetches có thể trigger stale state.

---

## Code Changes

### 1. Sync reset trong `selectItem` (~line 1086-1089)

```javascript
// BUG-012: reset Web Enrich state synchronously
_currentEnrichEntityId = null;
(function(){ const _p = document.getElementById('webEnrichPanel'); if (_p) _p.innerHTML = '<span style="color:var(--da-dim)">Đang tải...</span>'; })();
console.debug('[select]', { id, lat, lng, token: _selectToken });
```

**Tác dụng:** Ngay khi `selectItem(newId)` bắt đầu, state của entity cũ bị xóa — không còn window nào mà `_currentEnrichEntityId` trỏ sai.

### 2. Unified path — gọi `initWebEnrichPanel` vô điều kiện (~line 1210-1213)

**Trước:**
```javascript
if (d.note) {
    ...
    if (d.source_record_id) {
        initWebEnrichPanel(d.source_record_id);  // chỉ khi có note
    }
}
```

**Sau:**
```javascript
// BUG-012: always init Web Enrich regardless of d.note
const _b12EnrichId = d.source_record_id || id;
console.debug('[web-update]', { placeId: id, enrichId: _b12EnrichId, token: _selectToken });
initWebEnrichPanel(_b12EnrichId);
// ... if (d.note) block vẫn còn, chỉ xóa initWebEnrichPanel ở đây
```

**Tác dụng:** Mọi entity có DILA source (dù thiếu note) đều trigger `initWebEnrichPanel` với đúng entity ID.

### 3. `_selectToken` guard trong `initWebEnrichPanel` (~line 1960-1977)

```javascript
function initWebEnrichPanel(entityId) {
    _currentEnrichEntityId = entityId;
    const _b12EnToken = _selectToken;  // capture token
    ...
    fetch(...)
        .then(r => r.json())
        .then(d => {
            if (_b12EnToken !== _selectToken) return;  // stale guard
            ...
        })
        .catch(() => {
            if (_b12EnToken !== _selectToken) return;  // stale error guard
            ...
        });
}
```

**Tác dụng:** Response từ entity cũ không thể ghi đè panel của entity mới.

### 4. Debug logs

| Log | Khi nào |
|-----|---------|
| `[select]` | Mỗi lần `selectItem` bắt đầu |
| `[rag-geo]` | Khi `rawGeo` được set từ unified DILA GPS |
| `[web-update]` | Khi `initWebEnrichPanel` được gọi từ unified path |
| `[web-update-fetch]` | Khi fetch web-enrichments bắt đầu |

---

## Verify Logic (không cần browser)

**Test A — Click marker → search place khác → GPS/RAG update đúng:**
- `selectItem(A)` T1 → sync reset: `_currentEnrichEntityId=null`, webEnrichPanel="Đang tải..."
- `selectItem(B)` T2 → sync reset lần nữa
- A's callback: `T1 ≠ T2` → return ✓ (GPS stays reset)
- B's callback: `T2 === T2` → GPS populated, `initWebEnrichPanel(B_id)` với `_b12EnToken=T2` → check `T2===T2` → render ✓

**Test B — Search liên tiếp 3 địa danh → không stale:**
- T1, T2, T3 tăng dần
- `initWebEnrichPanel` T1 callback: `T1 ≠ T3` → return ✓
- `initWebEnrichPanel` T2 callback: `T2 ≠ T3` → return ✓
- `initWebEnrichPanel` T3 callback: `T3 === T3` → render đúng ✓

**Test C — Web Update dùng đúng entity:**
- Mọi entity đều gọi `initWebEnrichPanel(_b12EnrichId)` (dù thiếu DILA note)
- `_currentEnrichEntityId` = entity hiện tại
- `webEnrich()` → `entityId = _currentEnrichEntityId` → đúng ✓

---

## Syntax Check

```
OK: 1 FAIL: 0
```

---

## Ghi chú

- **KHÔNG tự mark Done** — chờ Admin test thực tế và confirm.
- Tasktodo.md: BUG-012 (GIS_SEARCH_MARKER_STATE_MISMATCH_001) thêm vào OPEN BUGS.
- bugs.md: BUG-012 entry thêm vào trước BUG-009.
