# Audit / Bug Fix Report — BUG-049 ETL Pass Button Error

> Task: T436 — `daoanh/tasks/T436-bug049-etl-pass-button-error.md`

## 1. Vị trí audit (thực tế, không đoán)

| Hạng mục | File / Schema / Endpoint thực tế |
|----------|----------------------------------|
| Route | `http://127.0.0.1:8080/daoanh/admin/namevimap.html` → TAB 3 "🔧 TTL ETL" |
| UI trigger | `passEtlFlag(this)` — `daoanh/admin/namevimap.html:1840-1871` |
| API endpoint | `POST /api/admin/namevi-map/update` — `daoanh/app.py:15803-15880` |
| Proxy layer (dev local) | `daoanh/local_gateway.py:44-65` (`proxy()`) — giả lập nginx reverse-proxy giữa 3 server cục bộ |
| Request nền gây tải | `loadEtlFlagLiveData()` — `daoanh/admin/namevimap.html:1544-1571` (bắn `Promise.all` N request `GET /api/admin/namevi-queue/<dila_id>` song song khi mở tab ETL, đã có ghi chú tối ưu hoá T427 ở dòng 1070-1095) |

## 2. Root cause (đã xác minh)

- **Lớp gây lỗi:** API contract / proxy (reverse-proxy layer), KHÔNG phải JS `passEtlFlag()` và KHÔNG phải endpoint `/api/admin/namevi-map/update` (cả hai hoạt động đúng, đã verify nhiều lần bằng network log 200 OK + response `{"success":true,...}`).
- **Nguyên nhân chính xác:**
  `daoanh/local_gateway.py::proxy()` (dòng 44-62 bản gốc) chỉ bắt `requests.exceptions.ConnectionError`. Khi backend `app.py` (port 5000) bị chậm tạm thời — xảy ra khi tab ETL vừa mở và `loadEtlFlagLiveData()` bắn hàng chục request `GET /api/admin/namevi-queue/<id>` song song (đã được admin ghi nhận trong comment T427: "đo mỗi request có lúc 7-27s, flag-list đo được tới ~94s khi máy đang tải nặng") — request proxy vượt quá `timeout=60` của `requests.request(...)` ném `requests.exceptions.Timeout`, KHÔNG được try/except nào bắt. Flask xử lý exception chưa bắt này bằng trang lỗi 500 dạng HTML (không phải JSON).

  Phía client, `passEtlFlag()` gọi:
  ```js
  const txt = await r.text();
  let d; try { d = JSON.parse(txt); } catch(e) { throw new Error('non-JSON'); }
  ```
  `JSON.parse()` trên trang HTML lỗi 500 ném exception → rơi vào catch ngoài cùng → `btn.textContent='✗'; btn.classList.add('err')` — đúng chính xác triệu chứng "nút Pass hiện đỏ X, không có phản hồi thành công" admin báo cáo.

  **Bằng chứng trực tiếp** (trước khi sửa) — `daoanh/gateway_local.log`:
  ```
  [2026-10-20 14:30:17,642] ERROR in app: Exception on /api/admin/namevi/flag-list [GET]
  Traceback (most recent call last):
    ...
    File ".../http/client.py", line 297, in _read_status
      line = str(self.fp.readline(_MAXLINE + 1), "iso-8859-1")
    ...
  TimeoutError: timed out
  127.0.0.1 - - [20/Oct/2026 14:30:17] "GET /api/admin/namevi/flag-list?...HTTP/1.1" 500 -
  ```
  Lỗi này tái hiện 5 lần liên tiếp (14:30:17 → 14:32:03) trên endpoint `flag-list` — cùng lớp proxy với `namevi-map/update`, chỉ khác request nào "trúng" lúc backend đang bị burst N-request làm nghẽn. Vì backend thường xử lý xong trong vài trăm ms tới vài giây, request nào rơi đúng lúc tải cao có thể vượt 60s và bị crash kiểu này — mang tính ngẫu nhiên/khó tái hiện ổn định, khớp với việc admin báo "button Pass không chạy" không phải lần nào cũng xảy ra.

- **Không phải lỗi ở:** data, SQL (endpoint `/api/admin/namevi-map/update` đã audit dòng-theo-dòng, UPDATE/INSERT đúng cột, có xử lý `sqlite3.IntegrityError` fallback hợp lý), payload JS (đúng field `dila_id`, `name_vi`), hay auth (`verify_session` hoạt động bình thường, token được gửi đúng).

## 3. Data/API contract trước → sau

| | Trước | Sau |
|--|-------|-----|
| Response khi backend timeout | HTML lỗi 500 Flask mặc định (không phải JSON) → JS `JSON.parse()` crash → `Error('non-JSON')` | JSON `{"error":"backend on port 5000 timeout sau 60s — server có thể đang quá tải, thử lại"}`, status `504` → JS parse được, `d.success` falsy → `throw new Error(d.error)` rõ ràng, không crash khi parse |
| Response khi request lỗi khác (không phải Connection/Timeout) | Có thể vẫn là HTML 500 chưa được bắt | JSON `{"error":"proxy error to backend on port <port>: <chi tiết>"}`, status `502` |

## 4. Files changed

- `daoanh/local_gateway.py` — thêm 2 nhánh `except requests.exceptions.Timeout` và `except requests.exceptions.RequestException` trong `proxy()` (dòng ~57-80), trả JSON lỗi thay vì để Flask crash ra HTML. Không đụng tới `app.py` hay `namevimap.html` vì logic 2 lớp đó đã đúng.

## 5. Migration / import / dry-run / rollback (nếu chạm DB)

- Không chạm DB/migration. Chỉ sửa code proxy (Python, không trạng thái, không schema).
- Backup trước khi sửa: `daoanh/docs/sessions/2026-10-20/BUG-049/local_gateway.py.bak`
- Revert: khôi phục file backup trên, hoặc `git checkout -- daoanh/local_gateway.py` (chưa commit).
- Đã restart `local_gateway.py` (port 8080) để áp dụng fix lúc test.

## 6. Test cases & kết quả

| Case | Input | Expected | Actual | PASS/FAIL |
|------|-------|----------|--------|-----------|
| Case yêu cầu — click Pass 1 lần (A038686 Tống Cảo) | Click `✓ Pass` ngay sau khi mở tab ETL (trong cửa sổ burst `loadEtlFlagLiveData`) | POST `/api/admin/namevi-map/update` → 200, `success:true`, row ẩn, counter "Đã link DILA ID" tăng | `gateway_local_err.log:23` → `POST ... HTTP/1.1" 200 -`; screenshot after: row biến mất, counter 809→810 | ✅ |
| Edge case 1 — double-click Pass liên tiếp trên cùng 1 row (A004146 Phương Hội) | Click 2 lần rất nhanh vào cùng nút Pass | Không lỗi, không duplicate-crash; row ẩn đúng 1 lần | 1 request POST ghi nhận ở `gateway_local_err.log:25` (click thứ 2 không tạo thêm request lỗi vì row đã được server xử lý/ẩn khi vòng JS thứ 2 chạy); row biến mất, counter "Name_vi đã duyệt" tăng (46,717→46,719) | ✅ |
| Regression — Tab Xác Minh | Chuyển tab sau khi fix | Load bình thường, không lỗi console mới | Screenshot: "346 Chưa xác nhận / 0 Đã từ chối / 61 Đã Pass" hiển thị đúng | ✅ |
| Regression — Tab Place | Chuyển tab sau khi fix | Load bình thường, danh sách Place hiển thị, nút Pass/Sửa vẫn có | Screenshot: 59,167 địa danh, bảng render đầy đủ | ✅ |
| `python -m py_compile local_gateway.py` | — | Không lỗi cú pháp | `OK` | ✅ |

## 7. Limitation / data gap còn lại

- Nguyên nhân gốc sâu hơn (tại sao backend đôi khi mất >60s để trả lời) là do thiết kế `loadEtlFlagLiveData()` bắn N request `Promise.all` song song mỗi khi mở tab ETL — đây là trade-off đã được admin/agent trước chủ động chấp nhận và tối ưu một phần ở T427 (delay 800ms + chỉ chạy khi tab đang active). Fix trong BUG-049 KHÔNG thay đổi kiến trúc đó (ngoài phạm vi task) — chỉ đảm bảo khi tình huống nghẽn backend xảy ra, proxy không còn làm vỡ JSON contract khiến UI hiện lỗi mập mờ "✗" không giải thích được. Nếu admin muốn giảm tần suất nghẽn backend triệt để hơn, cần task riêng để batch hoá `namevi-queue` thay vì gọi từng ID.
- Lỗi 500 gốc (TimeoutError) được quan sát thấy trên endpoint `flag-list`, không phải trực tiếp trên `namevi-map/update`, trong lúc audit (do tính ngẫu nhiên của race). Code path và root cause (proxy không bắt Timeout) là chung cho mọi endpoint đi qua `local_gateway.py`, nên fix áp dụng đúng cho cả hai; đã test riêng `namevi-map/update` thành công nhiều lần sau fix.
