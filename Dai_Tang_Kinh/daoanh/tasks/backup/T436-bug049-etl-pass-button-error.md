---
id: T436
title: "BUG-049: namevimap.html TAB ETL — button Pass không chạy, hiện nút đỏ X"
status: done
created: 2026-10-20
updated: 2026-10-21
done_when: "Click button Pass trong TAB 3 (TTL ETL) chạy thành công, lưu DB, ẩn row — không còn hiện lỗi đỏ X; network request trả 200."
---

## Triệu chứng

- Route: `http://localhost:8080/daoanh/admin/namevimap.html`
- TAB 3: TTL ETL (switchTab('etl', this))
- Click button "✓ Pass" (class `etl-flag-pass`, hàm `passEtlFlag(this)`) không chạy đúng.
- UI hiện nút đổi thành màu đỏ (class `.err`, theo code dòng ~1869: `setTimeout(() => { btn.textContent = '✓ Pass'; btn.classList.remove('err'); }, 3000)` — nghĩa là catch error đã add class `err` trước đó).
- Không có phản hồi thành công (không ẩn row, không lưu DB).

## Nguyên nhân nghi ngờ (chưa xác minh — audit trước khi sửa)

- `passEtlFlag()` gọi API nào trong `app.py`? (nghi: `/api/admin/namevi-queue/<id>` hoặc endpoint `canonical_decision` liên quan ETL flag pass, khoảng dòng 1839-1870 của namevimap.html).
- Có thể: endpoint 404/500, payload sai field, thiếu CSRF/auth, hoặc lỗi SQL trong app.py.
- Cần xác minh bằng request network thực tế (không đoán).

## Phạm vi dự kiến

- File khả năng sửa: `daoanh/admin/namevimap.html` (hàm `passEtlFlag`), `daoanh/app.py` (endpoint xử lý pass ETL flag).
- Không sửa raw TTL/DILA data.
- Không hard-code giá trị hiển thị.

## Việc cần làm (giao daoanh-debugger)

1. Mở browser → `http://127.0.0.1:8080/daoanh/admin/namevimap.html` (dùng 127.0.0.1, không dùng localhost).
2. Click TAB "🔧 TTL ETL".
3. Click một button "✓ Pass" bất kỳ trong bảng ETL FLAG.
4. Screenshot lỗi (nút đỏ X / state err).
5. Đọc console error + network request/response (status code, payload, response body).
6. Audit code: `passEtlFlag()` trong namevimap.html (~dòng 1839-1870), endpoint tương ứng trong `daoanh/app.py`.
7. Xác định root cause: API không tồn tại / lỗi 500 trong app.py / payload JS sai / auth fail.
8. Backup file sẽ sửa vào `daoanh/docs/sessions/2026-10-20/BUG-049/` trước khi sửa.
9. Fix đúng lớp (data/API/resolver/renderer) — fix nhỏ nhất.
10. Test lại: click Pass → thành công, row ẩn, DB lưu đúng.
11. Không commit git.

## Báo cáo

- `daoanh/docs/BUG-049_ETL_PASS_BUTTON_FIX_REPORT.md`
- Cập nhật `daoanh/docs/bugs.md` mục BUG-049.

## Kết quả (2026-10-20, chờ QA + Admin confirm — chưa tự đánh Done)

- Root cause xác minh: `daoanh/local_gateway.py::proxy()` không bắt `requests.exceptions.Timeout`
  → Flask trả HTML 500 khi backend chậm (burst `loadEtlFlagLiveData`) → JS `JSON.parse()` crash
  → nút Pass hiện đỏ `✗`. Không phải lỗi ở `passEtlFlag()` hay endpoint `/api/admin/namevi-map/update`.
- Fix: thêm `except requests.exceptions.Timeout` + `except requests.exceptions.RequestException`
  trong `proxy()`, trả JSON lỗi (504/502) thay vì HTML crash.
- Backup: `daoanh/docs/sessions/2026-10-20/BUG-049/local_gateway.py.bak`
- Test: Pass 1 lần (200 OK, row ẩn), double-click Pass (không lỗi, không duplicate), regression
  tab Xác Minh + Place OK, `py_compile` OK. Chi tiết: `daoanh/docs/BUG-049_ETL_PASS_BUTTON_FIX_REPORT.md`.
- Giới hạn: nguyên nhân sâu hơn (burst N-request khi mở tab ETL khiến backend đôi lúc chậm)
  chưa được xử lý triệt để — đó là trade-off đã chấp nhận từ T427, ngoài phạm vi BUG-049.

## Verify lại (2026-10-21)

- Browser thật: click Pass (A046539) → 200 OK, row ẩn ngay. Double-click Pass (A001003) →
  2 request đều 200 OK, không duplicate/crash. Fix `local_gateway.py::proxy()` vẫn hoạt
  động đúng, không cần sửa thêm. Chi tiết: `daoanh/docs/T436_T437_VERIFY_FIX_REPORT.md`.

## Verify bằng browser thật (2026-10-21, điều phối tự mở browser do agent thiếu công cụ browser)

- Mở `http://127.0.0.1:8080/daoanh/admin/namevimap.html`, TAB TTL ETL, click "✓ Pass"
  hàng A001716 (Tuệ Hải). Network log thật: `POST /api/admin/namevi-map/update → 200 OK`.
  Row biến mất khỏi "Bulk Flag Queue" ngay (311/311 → 310/310 sau khi trừ dòng vừa Pass).
  Không có nút đỏ ✗.
- Không còn console error.

## Xác nhận DONE

Admin xác nhận DONE 2026-10-21.

**Admin xác nhận DONE (2026-10-26).** Báo cáo: docs/BUG-049_ETL_PASS_BUTTON_FIX_REPORT.md (BUG-049). Commit docs xem git log.
