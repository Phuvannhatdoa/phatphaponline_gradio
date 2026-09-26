# Session: Fix `namevimap.html` JSON parsing error (routes mismatch)

## Mô tả ngắn task
Fix `SyntaxError: Unexpected token '<', "<!doctype "... is not valid JSON` on `namevimap.html`. Root cause: frontend calls `/api/...` but nginx only proxies `/daoanh/api/...` to Flask, returning HTML (404/index) instead of JSON.

## Liên hệ ROADMAP
- Nguồn liên quan: DILA / NameVi Map hạ tầng docs.
- Khoá ROADMAP: "Khoả 1 – Xong core Hán → Việt" (mapping + UI).
- Dòng ROADMAP tương ứng: "Hoàn thiện mapping DILA ↔ people/places"

## Thiết kế/giải pháp đã chọn
- **Frontend**: Thay đổi tất cả `fetch(API + '/api/...')` thành `fetch('/daoanh/api/...')` trong `namevimap.html` (7 chỗ).
- **Backend**: Thêm decorator `@app.route('/daoanh/api/...')` cho 5 hàm API thiếu prefix `/daoanh/api/` (namevi-queue, namevi-queue/<id>, namevi-map/delete, namevi-map/update, name_vi/search, translate/all).
- Nginx vẫn proxy `/daoanh/api/` → port 5000; không cần thay đổi config.

## Danh sách file đã sửa
1. `namevimap.html` — 7 fetch URLs: `/api/...` → `/daoanh/api/...`
2. `app.py` — 6 route decorators được thêm `@app.route('/daoanh/api/...')`:
   - `/daoanh/api/admin/namevi-queue` (dòng 5982)
   - `/daoanh/api/admin/namevi-queue/<dila_id>` (dòng 6051)
   - `/daoanh/api/admin/namevi-map/delete` (dòng 6155)
   - `/daoanh/api/admin/namevi-map/update` (dòng 6174)
   - `/daoanh/api/name_vi/search` (dòng 5933)
   - `/daoanh/api/translate/all` (dòng 6346)

3. `docs/sessions/2026-06-01_fix-namevimap-json-routes.md` — Session log này.

## Cách chạy/test
```bash
cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh
npm run tester:agent
```

Manual:
- Mở https://phatphaponline.org/daoanh/admin/namevimap.html
- DevTools → Console: không còn lỗi JSON
- DevTools → Network: tất cả request đến `/daoanh/api/...` trả 200 JSON

## Kết quả test
- ✅ Tester agent: 4/4 passed (lint, test, e2e, runtime)
- ✅ Python syntax: `python3 -m py_compile app.py` → Syntax OK
- ✅ HTML syntax: namevimap.html fetch URLs corrected

## Liên hệ ROADMAP
- Nguồn liên quan: DILA / NameVi Map
- Khoá ROADMAP: Khoá 1 – Xong core Hán → Việt
- Dòng ROADMAP: "Hoàn thiện mapping DILA ↔ people/places"
