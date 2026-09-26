# Session: Fix CBETA no_match error toast "LỖI TRA CBETA: UNKNOWN"

**Date:** 2026-05-22
**Task:** Sửa lỗi frontend hiển thị "LỖI TRA CBETA: UNKNOWN" khi không có kết quả CBETA

## Vấn đề

Mở địa danh PL000000000003 (勝境關) → phần "NGUỒN CBETA" báo:
- "Không tìm thấy kết quả."
- "LỖI TRA CBETA: UNKNOWN"

## Nguyên nhân

### Backend
Response không có `message` field để phân biệt no-match vs error.
Error format dùng `{"success": False, "error": "..."}` — frontend check `data?.success` fail → vào else branch.

### Frontend
```javascript
if (data?.success) {
  // show results
} else {
  // show error toast ← sai, vì no match không phải error
}
```

Khi `data?.success` không tồn tại (no match), `data?.error` cũng undefined → hiển thị "UNKNOWN".

## Sửa chữa

### Backend (`app.py`)

**`cbeta_search_place` + `cbeta_search_person`:**
- Response khi không kết quả:
  ```json
  {"has_cbeta": false, "results": [], "message": "no_match", "total": 0}
  ```
- Response khi có kết quả:
  ```json
  {"has_cbeta": true, "results": [...], "total": N, "message": "found"}
  ```
- Response khi lỗi hệ thống:
  ```json
  {"error": true, "message": "cbeta_db_connection_failed"}
  ```
  Status 500.

### Frontend (`admin/placevn.html:474-494`)

```javascript
if (data?.error) {
  // System error → show toast
  setMessage({ type: 'error', text: 'Lỗi tra CBETA: ' + (data.message || 'cbeta_error') });
} else if (data?.has_cbeta) {
  // Has results → render
  setCbetaResults(data.results || []);
  setCbetaTotal(data.total || 0);
} else {
  // No match → silent, no toast
  setCbetaResults([]);
  setCbetaTotal(0);
}
```

## Kết quả test

```
Test 1: {"query": "勝境關"} → {"has_cbeta": false, "message": "no_match", "results": []} (200)
Test 2: {}               → {"has_cbeta": false, "message": "no_match", "results": []} (200)
Test 3: {"place_name": "釋迦文"} → {"has_cbeta": true, "message": "found", "results": [1], "total": 1} (200)
```

Frontend: no_match → render "Không tìm thấy kết quả." (dòng 1102-1104), không toast error.

## Liên hệ ROADMAP

- **Nguồn liên quan:** CBETA (Hán tạng số)
- **Khoá ROADMAP:** Khoá 1 – Xong core Hán → Việt

## Files changed

- `app.py` — 2 handlers: thêm `message` field, đổi error format
- `admin/placevn.html` — `handleCbetaSearch`: phân biệt error vs no_match vs success
- `docs/sessions/2026-05-22_fix_cbeta_no_match_error_toast.md` — session log (new)
