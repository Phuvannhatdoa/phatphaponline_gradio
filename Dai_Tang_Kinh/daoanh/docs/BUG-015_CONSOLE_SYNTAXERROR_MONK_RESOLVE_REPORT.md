# Audit / Bug Fix Report — BUG-015 (CONSOLE_SYNTAXERROR_MONK_RESOLVE_001)

> Console errors: `monk-resolve 404 NOT FOUND` + `Uncaught SyntaxError: Unexpected end of input (×3)`
> Route/case: `/daoanh/places.html?fly=34.5885,112.9343&select=PL000000023255` (Thiếu Lâm Tự)

## 1. Vị trí audit (thực tế, không đoán)

| Hạng mục | File / Schema / Endpoint thực tế |
|----------|----------------------------------|
| API endpoint | `GET /daoanh/api/monk-resolve?name=<name>` — `daoanh/app.py:10390-10422` (`api_monk_resolve`) |
| Caller (JS) | `daoanh/places.html:1779-1827` (`runAutocomplete(q)`), fired from `searchInput` `input` event, debounced 150ms |
| Proxy layer | `daoanh/local_gateway.py:44-65` (`proxy()`) — dev-only nginx stand-in, forwards `app.py:5000` responses to browser via port `8080` |
| DB | `data/lineage.db` table `people` (48k+ rows), queried by `name_vi`/`name_zh` exact then `LIKE` |

## 2. Root cause (đã xác minh)

- **Lớp gây lỗi:** API contract (chính) + proxy header passthrough (phòng ngừa thêm).
- **Route KHÔNG hề thiếu** — trái với giả thuyết ban đầu trong `docs/bugs.md` ("route gọi... → 404 vì thiếu route"). Route `/daoanh/api/monk-resolve` tồn tại và hoạt động đúng logic SQL; nó cố ý trả `404` khi không tìm thấy `people` row khớp tên.
- **Nguyên nhân chính xác:** `runAutocomplete()` gọi đồng thời cả `places/search` (địa danh) và `monk-resolve` (tăng nhân) cho MỌI chuỗi gõ ≥ 2 ký tự, vì UI không biết trước loại thực thể user đang tìm (search box dùng chung cho cả 2 loại — đây là thiết kế cố ý, không phải lỗi). Khi user gõ một địa danh thuần túy như "Thiếu Lâm Tự", `monk-resolve` hợp lệ trả **404** (đúng theo code, vì không có row `people` khớp) — nhưng **404 lại là kết quả bình thường/mong đợi của một resolver "tìm không thấy"**, không phải lỗi server. Việc dùng status code 404 cho một outcome hợp lệ khiến: (a) Console log field đỏ "Failed to load resource: 404" gây nhiễu, và (b) tái hiện trực tiếp trên browser thật cho thấy khi 404 này xảy ra đồng thời với loạt request khác đang chạy song song (search / unified / pali / web-enrichments / translate / canon / cbeta units — 6+ request cùng lúc do `selectItem` re-trigger toàn bộ tab khi search khớp lại đúng entity đang chọn), console ghi nhận `Uncaught SyntaxError: Unexpected end of input` — dấu hiệu kinh điển của `response.json()` nhận body rỗng/bị cắt. Verify trực tiếp: **trước khi fix**, gõ "Thiếu Lâm Tự" vào ô tìm kiếm trên browser thật (Claude Browser, CDP) tái hiện đúng cặp lỗi 404 + 2 SyntaxError trong cùng 1 lần gõ. **Sau khi fix** (đổi status 404→200 + restart `app.py`), lặp lại thao tác gõ y hệt (kể cả xóa/gõ lại, gõ nhanh nhiều ký tự) — 0 lỗi mới xuất hiện qua nhiều lần thử.
- **Nguyên nhân phụ đã rà nhưng loại trừ:** route thiếu (sai — route có sẵn từ T04, session `2026-08-18_t04_marcus_people_link.md`); body 404 rỗng/HTML (sai — `curl` xác nhận body luôn là JSON hợp lệ `{"error":"not found","ok":false}`); `JSON.parse()` trên `localStorage` (không áp dụng — 2 chỗ dùng `JSON.parse` trong `places.html` đều có `|| '[]'` fallback an toàn cho chuỗi rỗng/null); cú pháp JS tĩnh sai trong file (loại trừ — toàn bộ `<script>` chính parse và chạy bình thường, mọi tính năng khác hoạt động).
- **Hardening bổ sung (phòng ngừa, không phải nguyên nhân đã xác nhận):** `local_gateway.py` forward `Content-Length` header nguyên văn từ response upstream (`app.py:5000`) trong khi body gửi đi là `resp.content` đã qua `requests` xử lý — nếu 2 giá trị lệch nhau (vd. tương lai `app.py` bật gzip/compress) trình duyệt sẽ đọc body bị cắt và `fetch(...).then(r=>r.json())` sẽ ném đúng lỗi `Unexpected end of input`. Đã bỏ `content-length` khỏi header passthrough để Flask/Werkzeug tự tính lại theo body thật — loại bỏ hoàn toàn class lỗi này bất kể endpoint nào, không chỉ `monk-resolve`.

## 3. Data/API contract trước → sau

| | Trước | Sau |
|--|-------|-----|
| `GET /daoanh/api/monk-resolve?name=<không khớp>` | `404 NOT FOUND` + body `{"ok":false,"error":"not found"}` | `200 OK` + body `{"ok":false,"error":"not found","results":[]}` |
| `GET /daoanh/api/monk-resolve?name=<khớp>` | `200 OK` + `{"ok":true,"person":{...}}` (không đổi) | `200 OK` + `{"ok":true,"person":{...}}` (không đổi) |
| `local_gateway.py` proxy headers | passthrough `content-length` từ upstream nguyên văn | `content-length` bị loại khỏi passthrough; Werkzeug tự tính theo `resp.content` thực gửi |

Front-end (`places.html`) không cần đổi gì — code đã kiểm tra `monk.ok && monk.person` (không dựa vào HTTP status), nên tương thích ngược 100%.

## 4. Files changed

- `daoanh/app.py` (dòng ~10416-10418, hàm `api_monk_resolve`) — đổi response "not found" từ `404` sang `200` kèm `results: []`.
- `daoanh/local_gateway.py` (hàm `proxy()`, dòng ~63-65) — thêm `content-length` vào tập header bị loại khi forward response, để Flask tự tính lại Content-Length đúng theo body thực gửi.

## 5. Migration / import / dry-run / rollback

- Không chạm DB, không cần migration.
- Rollback: `git diff`/`git checkout -- daoanh/app.py daoanh/local_gateway.py` (chưa commit) hoặc revert 2 đoạn code trên nguyên văn.
- Cần **restart `app.py` (port 5000)** và **`local_gateway.py` (port 8080)** để nạp code mới — cả 2 process không chạy debug/reloader (`debug=False`). Đã restart, xác nhận đang listen (`Get-NetTCPConnection`).

## 6. Test cases & kết quả

| Case | Input | Expected | Actual | PASS/FAIL |
|------|-------|----------|--------|-----------|
| Case yêu cầu | Gõ "Thiếu Lâm Tự" vào searchInput trên `places.html?fly=34.5885,112.9343&select=PL000000023255` | Không còn `monk-resolve 404`, không còn `Uncaught SyntaxError` | `monk-resolve` → `200 OK` liên tục qua nhiều lần gõ/xóa/gõ lại; 0 SyntaxError mới trong console | ✅ |
| Fallback — tên khớp thật (person tồn tại) | `monk-resolve?name=明因妙善普濟法師` (A000001, DB thật) | `200` + `ok:true` + đúng `person` | `200 OK`, `{"ok":true,"person":{"id":"A000001","name_vi":"Minh Nhân Diệu Thiện Phổ Tế Pháp Sư",...}}` — không regression logic resolve | ✅ |
| Fallback — route lạ không tồn tại (Content-Length passthrough) | `GET /daoanh/api/definitely-not-a-real-route-xyz` qua gateway `8080` | `Content-Length` header khớp đúng số byte body thực | `Content-Length: 207`, body 207 bytes (khớp) | ✅ |
| Regression — các tab khác của cùng entity | `unified`, `pali`, `web-enrichments`, `place/translate`, `canon`, `related`, `cbeta/passages/*/units`, `graph`, `nexus`, `events` | Tất cả vẫn `200 OK`, không lỗi mới trong `app_local.err` | Toàn bộ `200 OK`, log server sạch, không traceback | ✅ |

## 7. Limitation / data gap còn lại

- Không tái hiện được 100% xác định *cơ chế byte-level* khiến body bị đọc là rỗng trên proxy dev (`local_gateway.py`) tại thời điểm 404 xảy ra đồng thời với 6+ request song song — vì đến lúc audit, mọi request qua `curl` tuần tự đều trả body/Content-Length khớp nhau hoàn hảo (không lỗi). Fix áp dụng theo hướng loại bỏ toàn bộ class lỗi này (đổi 404→200 cho outcome hợp lệ + bỏ Content-Length passthrough) thay vì vá đúng 1 dòng race cụ thể chưa bắt được trực tiếp.
- Đã thử tái hiện lại nhiều lần (gõ đầy đủ, xóa+gõ lại, gõ nhanh) sau khi fix và restart — 0 lỗi mới trong toàn bộ các lần thử. Cần Admin xác nhận trên môi trường thật (browser riêng của Admin) trước khi đóng bug.
- **CHỜ ADMIN CONFIRM DONE** — theo quy tắc `feedback_bug_verify_protocol` (không tự claim done bằng JS inject; đã verify bằng click UI thật + screenshot console before/after qua Claude Browser, network log làm bằng chứng ở trên).
