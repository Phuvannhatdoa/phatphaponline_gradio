# T372 (bổ sung) — Teacher/Student hiển thị charwise Hán-Việt

Ngày: 2026-10-13

## Audit — nguồn charwise transliteration hiện có

Hàm transliteration charwise Hán→Hán-Việt **không nằm trong `admin/dila_person_index.html`**
như mô tả trong task — file đó chỉ hiển thị debug UI (đọc kết quả qua API), không chứa
bảng ánh xạ hay thuật toán. Thuật toán thực sự nằm ở backend `app.py`:

- `CUSTOM_HANVIET` (dict literal, `app.py` dòng 560) — override ưu tiên cao nhất cho
  một số chữ hiếm.
- `hanviet_fallback` (bảng SQLite, nạp vào cache `_HV_CACHE` qua `_init_hv_cache()`,
  `app.py` dòng 1026) — bảng ánh xạ chính, 1 chữ Hán → 1 âm Hán-Việt.
- Thuật toán ghép charwise (input: chuỗi Hán, output: chuỗi Hán-Việt cách nhau bởi
  khoảng trắng, viết hoa chữ đầu mỗi âm) đã tồn tại sẵn **lặp lại 2 nơi** trong
  `app.py` trước khi tôi sửa: `_ensure_vietnamese()` (dòng ~1044, không viết hoa/không
  cách — dùng cho mục đích khác) và bên trong route
  `/daoanh/api/admin/person/<id>/revalidate-hv` (dòng ~20481, có viết hoa + cách —
  đúng định dạng "Hành Tư").
- Kết quả bulk-precompute của thuật toán trên được lưu trong bảng
  `person_hanviet_debug.han_viet_charwise` (47.036/48.673 person đã có, cột
  `dict_version='t172-20260928-3dict'`) — đây là nguồn **đáng tin hơn** bảng
  `hanviet_fallback` sống hiện tại vì nó xử lý đúng một số trường hợp đa âm
  (ví dụ 行 trong "行思" → "Hành", trong khi `hanviet_fallback` hiện tại map 行→"hàng"
  mặc định, một âm khác của cùng chữ).

Không có API expose riêng cho việc transliterate 1 chuỗi Hán bất kỳ — chỉ có
per-person route `revalidate-hv` (ghi vào DB) và debug-list route
`/daoanh/api/admin/missing-hanzi` (không liên quan trực tiếp).

## Root cause đã xác minh (bug "chưa có tên VI" cho A003666 teacher/student)

- `admin/person.html` hàm `relCardVi()` (dòng 384+) đã được sửa ở một fix trước đó
  trong cùng task để chỉ đọc `r.hanviet_charwise` (bỏ nguồn TTL cũ) — đúng hướng,
  nhưng **backend chưa từng gắn field `hanviet_charwise` vào payload `relations`**.
- Endpoint `/daoanh/api/person/<person_id>/dila_full` (app.py, route
  `api_person_dila_full`) build `relations` trực tiếp từ dữ liệu XML parse
  (`relations.append({'type', 'person_id', 'name', 'bibl', 'ref_url'})`, app.py dòng
  ~5877) — **không có key `hanviet_charwise`** → front-end luôn nhận `undefined`
  → `relCardVi()` rơi vào nhánh "chưa có tên VI".
- Đây là lỗi **lớp API contract** (backend thiếu field mà frontend đã kỳ vọng), không
  phải lỗi renderer.

## Thay đổi chính (before/after contract)

### `app.py`

1. Thêm hàm dùng chung `_hanviet_charwise_translit(name_zh)` (gần `_ensure_vietnamese()`,
   ~dòng 1072) — tái dùng đúng thuật toán đã có trong route `revalidate-hv` (ghép âm,
   viết hoa chữ đầu, cách bằng khoảng trắng), trả về `(charwise, unknown_chars)`.
   Dùng làm fallback **live** khi person không có dòng precompute.
2. Thêm hàm `_normalize_charwise_caps(s)` — chuẩn hóa viết hoa chữ đầu mỗi âm tiết cho
   giá trị đọc từ `person_hanviet_debug` (một số dòng cũ lưu không nhất quán hoa/thường,
   ví dụ `'Huệ năng'`, `'hơi Thiên'`).
3. Sửa route `/daoanh/api/person/<person_id>/dila_full`: sau khi build `relations`,
   batch-query `person_hanviet_debug.han_viet_charwise` theo `person_id` của từng
   relation (1 query duy nhất, không N+1), **ưu tiên giá trị precompute** (đã qua
   T172 xử lý đa âm) + normalize hoa/thường; nếu person chưa có dòng precompute thì
   fallback tính live bằng `_hanviet_charwise_translit(r['name'])`. Gắn kết quả vào
   `r['hanviet_charwise']` (hoặc `None` nếu rỗng/không có Hán tự).

   **Before**: relation object = `{type, person_id, name, bibl, ref_url}` — không có
   `hanviet_charwise`.
   **After**: relation object = `{type, person_id, name, bibl, ref_url,
   hanviet_charwise}` — `hanviet_charwise` là `string | null`.

### `admin/person.html`

- Không đổi logic hiển thị (đã đúng từ fix trước), chỉ thêm `title` tooltip rõ ràng
  cho badge "charwise" để nhấn mạnh đây là suy luận tự động, không phải nguồn DILA
  (source_id=1) / ZQLOCAL (source_id=5) đã xác thực (đúng quy tắc trong
  `daoanh/CLAUDE.md` mục "ZQ — nguồn tên tiếng Việt").

## Kết quả test

### Case chính

- Route thực tế chứa 行思 (A003666) làm **teacher** của người khác:
  `http://127.0.0.1:8080/daoanh/admin/person.html?id=A010291` (Thạch Đầu Hy Thiên).
  Mở bằng Claude Browser (JS thật, không inject): section "THẦY" hiển thị
  **"Hành Tư"** kèm badge `charwise` và `(行思) A003666` — đúng yêu cầu. Screenshot
  xác nhận bằng mắt (khu vực Thầy/Học trò).
- Route gốc trong task: `http://127.0.0.1:8080/daoanh/admin/person.html?id=A003666` —
  section "THẦY" (惠能) hiển thị "Huệ Năng", "HỌC TRÒ" (希遷) hiển thị "Hơi Thiên" —
  cả hai đều có badge `charwise`, không còn "chưa có tên VI".
- API trực tiếp (`/daoanh/api/person/A010291/dila_full`) xác nhận field
  `hanviet_charwise: "Hành Tư"` cho relation `person_id=A003666`.

### Case fallback

- `_hanviet_charwise_translit('')` → `('', [])`, `_hanviet_charwise_translit(None)` →
  `('', [])` — không crash, trả rỗng.
- `_normalize_charwise_caps(None)` → `None`, `_normalize_charwise_caps('')` → `''` —
  không crash.
- Khi `hanviet_charwise` rỗng/`None`, `relCardVi()` (JS không đổi logic) tự fallback
  về nhánh cũ: hiện tên Hán + `"chưa có tên VI"`, không có lỗi JS — xác nhận qua
  `read_console_messages(onlyErrors=true)` ở mọi trang test, không có log lỗi nào.

### Regression (các case khác của T372)

Kiểm tra lại `http://127.0.0.1:8080/daoanh/admin/person.html?id=A000074` qua browser
thật: Alternative names (4), Birth/death, Sex, Dynasty, Place of origin ("許州"),
Works in Tripitaka, Bibliography/CBETA citations, Wikidata IDs (2) — tất cả vẫn hiển
thị đúng như các fix trước. Không có section "THẦY/HỌC TRÒ (DILA LINEAGE)" bị
duplicate (chỉ 1 block Teacher/Student, đúng như fix trước đã xóa section dư). Không
có log lỗi console mới ở cả 3 trang test (A010291, A003666, A000074).

## Report

`daoanh/docs/T372_TEACHER_STUDENT_CHARWISE_FIX_REPORT.md` (file này).

## Limitation / blocker còn lại

- `person_hanviet_debug` chỉ phủ 47.036/48.673 person (DB snapshot hiện tại); phần
  còn thiếu dùng fallback live qua `hanviet_fallback`/`CUSTOM_HANVIET`, có thể cho âm
  đọc sai với chữ đa âm (như 行) vì bảng `hanviet_fallback` sống hiện không có cơ chế
  disambiguation theo ngữ cảnh — đây là hạn chế đã có từ trước (ghi nhận trong chính
  `person_hanviet_debug.han_viet_validation_reason = 'đa âm 行: hàng'`), không thuộc
  phạm vi fix này.
- Một số âm charwise chất lượng thấp do bảng ánh xạ chính nó (ví dụ 希→"Hơi" thay vì
  "Hy" quen thuộc hơn, thấy ở 希遷 trong `person_hanviet_debug`) — đây là vấn đề chất
  lượng dữ liệu `hanviet_fallback`/`person_hanviet_debug`, nằm ngoài phạm vi task này
  (task chỉ yêu cầu wiring charwise logic đã có, không yêu cầu sửa bảng ánh xạ).
- Server local (app.py, port 5000) khi audit phát hiện có nhiều process trùng chạy
  song song từ các phiên trước (3 process `python app.py` đồng thời, chỉ 1 cái thực
  sự bind port 5000 tuỳ thời điểm) khiến lần đầu restart test ra kết quả cũ/sai lệch.
  Đã dọn sạch và chỉ còn đúng 1 process đang chạy (PID hiện tại phục vụ port 5000).
  Nên lưu ý khi restart local test sau này: kiểm tra `Get-CimInstance Win32_Process
  -Filter "Name='python.exe'" | Where CommandLine -like '*app.py*'` để chắc chắn
  không có process cũ còn sống trước khi coi restart là thành công.
