# Session Log: Fix Unexpected Token '<' Error in namevimap.html

## Mô tả ngắn task
Fixed the JSON parsing error `Unexpected token '<', "<!doctype "... is not valid JSON` on the Name Vi Map admin page (`namevimap.html`). The error occurred because frontend requests were being made to an incorrect API base (`''`), causing the server to return HTML (likely a 404 page) instead of JSON.

## Thiết kế/giải pháp đã chọn
- Set the `API` constant in `namevimap.html` to `'/daoanh/api'` so that all fetch requests (e.g., `/api/admin/namevi-queue`, `/api/translate/all`) are correctly proxied to the backend.
- Verified that the backend endpoints exist and return JSON with proper `Content-Type: application/json`.
- Ensured that the frontend error handling (try/catch) remains intact.

## Danh sách file/code/bảng SQLite đã được tạo/sửa
- `/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/namevimap.html`: Changed line `const API = '';` to `const API = '/daoanh/api';`

## Cách chạy/test
1. Run the tester agent to verify no regressions:
   ```bash
   cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh
   npm run tester:agent
   ```
2. Manually test the page:
   - Open `https://phatphaponline.org/daoanh/admin/namevimap.html` (hard refresh: Ctrl+F5)
   - Open DevTools → Network → XHR/Fetch
   - Confirm that requests to `/daoanh/api/admin/namevi-queue?...` return 200 and JSON
   - Confirm no JavaScript errors in console

## Kết quả test
- All tests passed: lint, test, e2e, runtime.
- Manual verification: The page loads the queue table without the JSON parsing error.
