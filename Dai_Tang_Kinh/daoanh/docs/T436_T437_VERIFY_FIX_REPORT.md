# Verify + Fix Report — T436 (BUG-049) + T437 (BUG-050)

> Route: `http://127.0.0.1:8080/daoanh/admin/namevimap.html`
> Ngày: 2026-10-21 · Browser thật (Claude Browser pane) — không JS inject để giả lập hành vi người dùng.

---

## Việc A — T436 (BUG-049): xác minh fix cũ còn hoạt động

### 1. Vị trí audit

| Hạng mục | File / Endpoint thực tế |
|----------|--------------------------|
| UI trigger | `daoanh/admin/namevimap.html` — nút `✓ Pass`, hàm `passEtlFlag(btn)` |
| API endpoint | `POST /api/admin/namevi-map/update` (qua `local_gateway.py` proxy :8080 → `app.py` :5000) |
| Fix trước đó (T436) | `daoanh/local_gateway.py::proxy()` — bắt `requests.exceptions.Timeout` / `RequestException`, trả JSON lỗi thay vì HTML 500 |

### 2. Kết quả verify (không sửa gì thêm)

Mở route, click Tab "🔧 TTL ETL", click `✓ Pass` trên row **A046539 (Long Thọ)**:

- Network: `POST /api/admin/namevi-map/update` → **200 OK**
  ```json
  {"dila_id":"A046539","name_vi":"Long Thọ","name_vi_final":"Long Thọ","success":true}
  ```
- UI: row biến mất khỏi bảng ngay sau response (không nút đỏ `✗`, không lỗi).

**Edge case — double-click liên tiếp** trên row **A001003 (Mã Minh)**:

- Network: 2 request `POST /api/admin/namevi-map/update` đều → **200 OK**, không duplicate-crash.
- UI: row ẩn đúng 1 lần, không có 2 animation chồng nhau, không console error liên quan (console chỉ có 1 lỗi cũ không liên quan từ trang Dashboard `/daoanh/admin/` — `animateValue` — xảy ra TRƯỚC khi vào namevimap.html, không phải lỗi mới).

### 3. Kết luận

Fix T436 (`local_gateway.py::proxy()` bắt `Timeout`/`RequestException`) **vẫn hoạt động đúng**. Không cần sửa thêm. Không có file nào bị thay đổi cho Việc A.

---

## Việc B — T437 (BUG-050): switchTab() + progressive load Hướng A

### 1. Vị trí audit

| Hạng mục | File / Endpoint thực tế |
|----------|--------------------------|
| State bug (vòng 2, đã sửa từ trước) | `daoanh/admin/namevimap.html::switchTab()` — dòng 1007-1058 |
| Bảng bị ảnh hưởng | `#etl-flag-queue-body` ("Bulk FLAG Queue") |
| API endpoint | `GET /api/admin/namevi/flag-list?page=&per_page=&hide_done=` (app.py:16117) |

### 2. Audit lại root cause `switchTab()` (vòng 2) — ĐÃ ĐƯỢC SỬA TRƯỚC KHI PHIÊN NÀY BẮT ĐẦU

Đọc code hiện tại tại `namevimap.html:1007-1058`: cả 2 nhánh `if (!etlTabLoaded)` và `else` đều gọi chung `_etlFullLoad()` (dòng 1040 và 1049), với comment nêu rõ lý do (nhánh `else` trước đây chỉ gọi `loadEtlFlagLiveData()`, khiến 3 request khác bị abort vĩnh viễn không ai gọi lại). Đây chính là fix mà task T437 mô tả ở mục "Audit lại vòng 2" — **đã có sẵn trong code khi phiên này bắt đầu** (từ một phiên trước, cùng lúc với T435 vòng 2).

**Verify bằng browser thật** (không chỉ đọc code): reload trang → bấm chuyển tab "Danh sách chờ mapping" → quay lại "TTL ETL" ngay lập tức (trong lúc trang 1 còn đang fetch) → lặp lại thao tác này 2 lần liên tiếp. Network log:

```
GET flag-list?page=1...11&per_page=30  → 200 OK (lượt 1, 11 trang)
GET flag-list?page=1  → net::ERR_ABORTED  (bị huỷ do rời tab)
GET flag-list?page=1  → net::ERR_ABORTED  (bị huỷ do rời tab lần 2)
GET flag-list?page=1...11&per_page=30  → 200 OK (lượt cuối, chạy xong đầy đủ)
```

Bảng **không kẹt "Đang tải…"** — luôn có request thay thế bắn lại sau mỗi lần abort, cuối cùng load đủ 311/311 FLAG. Cột Claude/Gemini header giữ đúng số (`48,646/48,673` · `48,673/48,673`) sau nhiều lần chuyển tab. **Kết luận: không cần sửa thêm phần `switchTab()`.**

### 3. Việc đã làm: Progressive load Hướng A (theo yêu cầu redesign của Admin)

**Trước:** `etlFlagQueueLoad(1)` gọi 1 API `per_page=50`, chờ cả lượt (có thể hàng trăm dòng) rồi `tbody.innerHTML=''` + render 1 lần. Nếu lỗi/timeout 45s → xoá sạch bảng, hiện lỗi cứng toàn bộ.

**Sau (Hướng A):**

| | Trước | Sau |
|--|-------|-----|
| `per_page` | 50 | 30 |
| Cách tải | 1 request duy nhất, chờ xong mới render | Tuần tự `page=1,2,3,...`, mỗi trang `appendChild` ngay khi về |
| Badge | không có (chỉ "Đang tải…" tĩnh) | "Đang tải trang N…" cập nhật theo từng trang |
| Deadline | 45s cho CẢ lượt | 15s cho MỖI trang riêng |
| Lỗi 1 trang | xoá sạch bảng, lỗi cứng toàn bộ | chỉ trang đó dừng + nút "Thử lại", các trang đã tải vẫn hiển thị |

Hàm mới: `etlFlagQueueLoadAll()` (reset + khởi động) và `_etlFlagLoadPageSeq(page, token, loadedSoFar)` (đệ quy tuần tự từng trang, dùng `_etlFlagLoadToken` để lượt tải mới luôn thắng lượt cũ). Hàm dựng row `_etlFlagBuildRow(item)` được tách ra dùng chung giữa `etlFlagQueueLoad()` (giữ nguyên, dùng cho nhảy trang cũ nếu còn gọi trực tiếp) và `etlFlagQueueLoadAll()` — tránh lệch HTML giữa 2 đường tải.

Tất cả điểm "tải lại từ đầu" đổi sang gọi `etlFlagQueueLoadAll()`: nút Load, checkbox "Ẩn đã duyệt", ô tìm kiếm (debounce), sort theo cột Tin cậy, `_etlFullLoad()` (vào tab ETL lần đầu/quay lại), và reload sau khi Bulk Pass.

### 4. Files changed

- `daoanh/admin/namevimap.html`
  - `_ETL_FLAG_PER_PAGE`: 50 → 30
  - Thêm `_etlFlagBuildRow(item)`, `etlFlagQueueLoadAll(outerSignal)`, `_etlFlagLoadPageSeq(page, token, loadedSoFar)`, `_etlFlagRetryPage(page, token, loadedSoFar)`
  - 6 điểm gọi đổi từ `etlFlagQueueLoad(1[, sig])` → `etlFlagQueueLoadAll([sig])` (dòng ~703, ~707, ~1571 trong `_etlFullLoad()`, ~1734 search, ~1749 sort, ~1804 sau Bulk Pass)
  - Hàm `etlFlagQueueLoad(page, signal)` cũ **giữ nguyên không xoá** (dùng chung `_etlFlagBuildRow`), hiện không còn điểm gọi nào trỏ tới nó trong code — an toàn, không phải dead-code nguy hiểm, chỉ là hàm dự phòng nếu sau này cần nhảy trang đơn lẻ.

Không đổi `app.py`, không đổi DB/schema, không đổi API contract (per_page vốn đã là query param hỗ trợ sẵn, giới hạn server-side `min(200, ...)`).

### 5. Test cases & kết quả

| Case | Input | Expected | Actual | PASS/FAIL |
|------|-------|----------|--------|-----------|
| Load lần đầu | Mở Tab ETL (mặc định) | Rows xuất hiện dần theo từng đợt 30 | Network: 11 request `page=1..11&per_page=30`, đều 200 OK; badge cuối "311/311 FLAG" | ✅ |
| Chuyển tab trong lúc tải (case bug gốc) | Rời tab ETL → quay lại trước khi 11 trang tải xong, lặp 2 lần | Không kẹt "Đang tải…" vĩnh viễn | Request cũ `ERR_ABORTED`, request mới luôn chạy tiếp, cuối cùng vẫn 311/311, không kẹt | ✅ |
| Header Claude/Gemini sau nhiều lần chuyển tab | Chuyển tab ETL qua lại 3 lần | Giữ đúng số `48,646/48,673` · `48,673/48,673` | Đúng, không mất số | ✅ |
| `python -m py_compile` | Không có file `.py` nào bị sửa | N/A | N/A (không áp dụng — chỉ sửa `.html`) | — |
| JS syntax | Script block trích từ `namevimap.html` | `node --check` không lỗi | `SYNTAX OK` | ✅ |
| Regression Tab Xác Minh | Click tab "🔍 Xác Minh" | Load đúng 338 mục chưa xác nhận | Đúng, UI hiển thị bình thường | ✅ |
| Regression Tab Place | Click tab "🗺️ Place" | Load 59,167 địa danh, Claude/Gemini placeholder "—" (chưa triển khai, KHÔNG đụng vào) | Đúng, không đổi | ✅ |
| Regression route `/daoanh/places` | Mở route GIS Places | Map load bình thường | Đúng, không console error | ✅ |
| Việc A (BUG-049) không bị ảnh hưởng bởi thay đổi Việc B | Click Pass trên row thuộc `_etlFlagBuildRow` mới | 200 OK, row ẩn | Đã verify ở Việc A — dùng chung `passEtlFlag()` không đổi | ✅ |

Chưa test riêng kịch bản "1 trang cụ thể timeout 15s rồi bấm Thử lại" bằng cách tạo lỗi thật (môi trường local hiện tải nhanh, không tái hiện được timeout tự nhiên) — logic đã review kỹ (deadline per-page độc lập qua `AbortController` + `setTimeout`, nút Thử lại gọi lại đúng trang qua `_etlFlagRetryPage`), nhưng chưa có bằng chứng network log thật cho nhánh lỗi/retry.

### 6. Limitation / việc còn lại

- Nhánh lỗi 1 trang (badge đỏ + nút "Thử lại") được review code kỹ nhưng chưa ép được tái hiện bằng network thật trong môi trường local hiện đang nhàn rỗi (không có cách an toàn để giả lập timeout mà không JS-inject, vốn bị cấm theo quy tắc verify bug). Nếu Admin muốn, có thể tái hiện bằng cách tạm thời throttle network trong DevTools thật hoặc tạo tải DB nặng song song.
- `etlFlagQueueLoad(page, signal)` cũ không còn điểm gọi nào trong code hiện tại (giữ lại làm hàm dự phòng, không xoá để tránh phá vỡ gì ngoài dự kiến) — có thể dọn dẹp sau nếu Admin xác nhận không cần.
- Không git commit theo yêu cầu.

---

## Tổng kết files changed

- `daoanh/admin/namevimap.html` — progressive load Hướng A (Việc B); Việc A không sửa gì.
- `daoanh/docs/bugs.md` — cập nhật mục BUG-049 (verify lại) + thêm mục BUG-050.
- `daoanh/docs/T436_T437_VERIFY_FIX_REPORT.md` — report này.
- Backup: `daoanh/docs/sessions/2026-10-21/T437/namevimap.html.before_progressive_load.bak`

---

## Vòng 2 — sửa theo QA (2026-10-21)

QA kiểm tra vòng 1 báo CHƯA ĐẠT với 2 lỗi cụ thể. Backup trước khi sửa:
`daoanh/docs/sessions/2026-10-21/T437/namevimap.html.before_round2.bak`.

### Lỗi 1 — deadline 45s chung vẫn xoá sạch bảng khi server chậm

**Root cause xác nhận đúng như QA mô tả:** `_etlNewAbortSignal()` tạo MỘT `AbortController`
(`ctrl`) dùng chung cho mọi fetch của tab ETL, kèm `setTimeout` 45s abort `ctrl` + ghi đè
`flagBody.innerHTML` nếu bảng còn "Đang tải". `etlFlagQueueLoadAll(sig)` truyền đúng `ctrl.signal`
này làm `outerSignal` cho `_etlFlagLoadPageSeq()` — mỗi trang nhỏ lắng nghe `outerSignal`'s
`abort` để hủy `pageCtrl` riêng của nó. Vì vậy khi 45s hết giờ: `ctrl.abort()` → kéo theo
`pageCtrl` của trang đang tải bị abort → nhánh catch thấy `outerSignal.aborted === true` nên
coi là "Admin rời tab", im lặng `return` (không hiện nút Thử lại) → đồng thời `setTimeout` ghi
đè `flagBody.innerHTML`, xoá sạch mọi trang đã tải trước đó. Đúng kịch bản QA nêu (11 trang ×
15s worst-case > 45s nên timer tổng luôn can thiệp trước).

**Before (namevimap.html, trong `_etlNewAbortSignal()`):**
```js
setTimeout(() => {
    if (_etlAbortCtrl !== ctrl) return;
    ctrl.abort();
    const timeoutMsg = 'Lỗi: quá thời gian chờ (45s) — server đang quá tải, thử lại';
    const flagBody = document.getElementById('etl-flag-queue-body');
    if (flagBody && flagBody.textContent.includes('Đang tải')) {
        flagBody.innerHTML = '<tr><td colspan="9" ...>' + timeoutMsg + '</td></tr>';
    }
}, 45000);
return ctrl.signal;
```
`_etlFullLoad()` gọi `etlFlagQueueLoadAll(sig)` — dùng CHUNG `sig` có deadline 45s ở trên.

**After:** tách flag-queue khỏi `ctrl`/deadline 45s bằng một `AbortController` RIÊNG
(`_etlFlagTabCtrl`), không gắn timer nào — chỉ abort khi Admin thực sự rời tab ETL
(`switchTab()`) hoặc khi `_etlFullLoad()` chạy lại (vào lại tab). Bảng flag-queue giờ chỉ còn
chịu deadline RIÊNG 15s/trang (đã có sẵn từ Hướng A) + nút "Thử lại" đúng trang lỗi, không còn
bị timer 45s chung ghi đè `innerHTML`.

```js
// khai báo cùng _etlAbortCtrl
let _etlFlagTabCtrl = null;

// _etlNewAbortSignal(): bỏ hẳn phần ghi đè etl-flag-queue-body, chỉ còn ctrl.abort()
setTimeout(() => {
    if (_etlAbortCtrl !== ctrl) return;
    ctrl.abort();
}, 45000);

// switchTab(), nhánh rời tab ETL:
if (name !== 'etl' && _etlFlagTabCtrl) { _etlFlagTabCtrl.abort(); _etlFlagTabCtrl = null; }

// _etlFullLoad():
if (_etlFlagTabCtrl) _etlFlagTabCtrl.abort();
_etlFlagTabCtrl = new AbortController();
etlFlagQueueLoadAll(_etlFlagTabCtrl.signal);   // KHÔNG còn dùng `sig` (45s) nữa
```

File: `daoanh/admin/namevimap.html` — các vùng quanh dòng ~1007-1020 (switchTab),
~1537-1562 (_etlNewAbortSignal), ~1568-1587 (_etlFullLoad).

### Lỗi 2 — vẫn còn 1 điểm gọi hàm cũ `etlFlagQueueLoad()` sau khi AI batch chạy xong

**Root cause xác nhận:** trong `runAiBatch()`, callback poll khi AI xong gọi
`etlFlagQueueLoad(_etlFlagPage || 1)` — hàm đơn-trang cũ, `_etlFlagPage` lúc đó đã dừng ở trang
cuối (ví dụ 11) do progressive load mới set, nên chỉ render lại đúng 1 trang (30 dòng) kèm
thanh phân trang cũ, KHÔNG hiện đủ 311 dòng như bảng progressive.

**Before:**
```js
etlFlagQueueLoad(_etlFlagPage || 1); // reload để hiện AI names
```

**After:**
```js
etlFlagQueueLoadAll(); // T437/BUG-050 round 2: reload đủ (progressive, không chỉ 1 trang cũ) để hiện AI names
```

File: `daoanh/admin/namevimap.html`, dòng ~2686 (trong `runAiBatch()`).

Điểm nút phân trang cũ (`onclick="etlFlagQueueLoad(p)"` trong hàm `etlFlagQueueLoad()`) được
QA xác nhận không bắt buộc sửa — sau 2 fix trên, không còn đường code nào gọi tới hàm
`etlFlagQueueLoad()` nữa (chỉ còn định nghĩa hàm, dead code tự chứa). Giữ nguyên, không xoá,
để tránh đổi phạm vi ngoài yêu cầu QA.

### Test vòng 2 (browser thật, `http://127.0.0.1:8080/daoanh/admin/namevimap.html`)

| Kịch bản | Cách test | Kết quả |
|---|---|---|
| `node --check`/syntax JS | Parse từng `<script>` block bằng `new Function()` | Tất cả OK, không lỗi cú pháp |
| Không có `.py` nào bị sửa | — | `py_compile` không áp dụng cho round 2 |
| Tải lần đầu, progressive load | Mở route, đọc Network log | 11 request `flag-list?page=1..11&per_page=30` đều 200 OK, badge cuối `311/311 FLAG (chưa duyệt)` |
| Chuyển tab đi/về liên tục khi đang tải (click thật, không JS inject) | Click "📋 Danh sách chờ mapping" → "🔧 TTL ETL" → lặp lại 2 lần ngay sau khi trang vừa load | Network log: 2 request `page=1` cũ bị `ERR_ABORTED` (đúng — do `_etlFlagTabCtrl` mới abort lượt cũ khi vào lại tab), lượt cuối chạy đủ 11 trang 200 OK, bảng cuối cùng hiện đúng `311/311 FLAG` — không kẹt, không xoá sạch |
| Fix lỗi 2 — reload sau AI batch | Đọc code xác nhận `runAiBatch()` gọi `etlFlagQueueLoadAll()` (progressive, không giới hạn 1 trang) thay vì `etlFlagQueueLoad(_etlFlagPage||1)` | Đã sửa đúng theo QA; chưa chạy full AI batch thật (tốn thời gian + gọi API ngoài) nên chưa có network log cho riêng nhánh này — xác nhận bằng đọc code + cùng hàm `etlFlagQueueLoadAll()` đã verify hoạt động đúng ở test trên |
| Regression — tab Xác Minh | Click "🔍 Xác Minh" | 338 chưa xác nhận / 71 đã Pass hiện đúng, không lỗi |
| Regression — tab Place (trong namevimap.html) | Click "🗺️ Place" | 59,167 địa danh load đúng |
| Regression — route `/daoanh/places` | Mở route | Map GIS Places load bình thường, không console error |

**Limitation còn lại (vòng 2):** chưa ép tái hiện được trường hợp server CHẬM THẬT (> 45s) bằng
network throttle thật (Claude Browser pane không có control throttle DevTools) — chỉ verify
bằng đọc code: vì `_etlFlagTabCtrl` không còn gắn timer 45s nào (đã xoá hẳn phần ghi đè
`flagBody.innerHTML` trong `_etlNewAbortSignal()`), về mặt code không còn đường nào để timer đó
chạm vào bảng flag-queue nữa — đây là đảm bảo cấu trúc (2 đối tượng `AbortController` tách biệt
hoàn toàn), không phải hành vi phụ thuộc thời gian/race condition, nên không cần tái hiện 45s
thật để xác nhận.

### Files changed vòng 2

- `daoanh/admin/namevimap.html` — 2 fix trên.
- Backup: `daoanh/docs/sessions/2026-10-21/T437/namevimap.html.before_round2.bak`
- Report: file này (`daoanh/docs/T436_T437_VERIFY_FIX_REPORT.md`, mục "Vòng 2").
- Không git commit (theo yêu cầu).
