---
id: T504
title: Link ID trong tab "Xác Minh Tác Giả" (namevimap.html) tới trang sửa person
status: in_progress
created: 2026-10-31
former_ids: []
related: [T503]
---

# T504 — Link ID → trang sửa person (tab Xác Minh Tác Giả)

## Yêu cầu Admin (2026-10-31)

Trên `http://127.0.0.1:8080/daoanh/admin/namevimap.html`, tab **"✍️ Xác minh tác giả"**
(`#tab-workverify`, T486), mỗi dòng hiển thị "Mã người" (ví dụ `A001583`, `A001301`).
Admin muốn: bấm vào ID của một dòng phải mở được trang sửa đúng người đó.

Admin đoán trang sửa là `admin/person.html` (route `admin_person_page` ở
`routes_pages.py` dòng ~110), truyền `person_id` — yêu cầu xác minh lại bằng
code thật trước khi sửa, không giả định.

**Tách riêng khỏi T503** (bug nút Pass tab này không hoạt động — đã xử lý ở
`tasks/T503-workverify-pass-button-not-working.md`, cùng file HTML nhưng khác
hành vi). T504 **không đổi** logic Pass của T503.

## Bước 1 — Xác minh route/tham số thực tế

`routes_pages.py` dòng 110-114:
```python
@app.route('/daoanh/admin/person.html')
def admin_person_page():
    resp = make_response(send_from_directory(ADMIN_DIR, 'person.html'))
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return resp
```
Route chỉ serve static file, **không** tự nhận tham số phía server — tham số
ID được `admin/person.html` đọc ở phía client (JS).

`admin/person.html` dòng 158:
```js
var personId = new URLSearchParams(location.search).get('id') || '';
```
→ tham số đúng là **`?id=`** (không phải `?person_id=`).

Dữ liệu người được nạp qua (dòng 898):
```js
fetch('/daoanh/api/persons/' + encodeURIComponent(personId))
```
API `/daoanh/api/persons/<person_id>` (`routes_lineage.py` dòng 4341-4351):
```python
@app.route('/daoanh/api/persons/<person_id>')
def api_person_by_id(person_id):
    p = conn.execute(
        "SELECT id, name_zh, name_vi, name_en, sect, dynasty, birth_year, death_year, bio, bio_vi "
        "FROM people WHERE id = ?", (person_id,)
    ).fetchone()
```
→ `person.html?id=X` dùng X để query trực tiếp **`people.id`**.

## Bước 2 — Xác minh ID trong bảng verify có khớp loại ID mà person.html cần

Backend bảng "Xác Minh Tác Giả" — `routes_namevi.py` dòng 1259-1316
(`admin_work_verify_list`), field `person_id` trả cho frontend lấy từ:
```python
for r in conn.execute(
    f"SELECT id, name_zh, name_vi FROM people WHERE id IN ({qmarks})", pids
).fetchall():
```
→ `person_id` hiển thị trong bảng (`A001583`, `A001301`...) **chính là
`people.id`** — cùng cột, cùng loại ID mà `/daoanh/api/persons/<id>` dùng để
query. **Không có lệch loại ID, không cần map.**

## Bước 3 — Sửa UI

`admin/namevimap.html`, hàm `wvLoad()` (tab Xác Minh Tác Giả), cột "Mã người"
trước đó render **link chết** (`href="#"` + `onclick="return false"`):

Before (dòng ~3070-3071):
```js
return `<tr data-person-id="${_esc(it.person_id)}">
    <td style="font-family:monospace;font-size:11px"><a href="#" class="dila-link" onclick="return false" title="${_esc(it.person_id)}">${_esc(it.person_id)}</a></td>
```

After:
```js
return `<tr data-person-id="${_esc(it.person_id)}">
    <td style="font-family:monospace;font-size:11px">${dilaLink(it.person_id)}</td>
```

Dùng lại hàm `dilaLink(id)` đã có sẵn trong file (dòng 2167-2175, dùng ở các
tab khác như "Xác Minh" `#tab-xcm`) — hàm này đã tự:
- Route `A######` → `/daoanh/admin/person.html?id=...`
- Route `PL######` (địa danh) → `/daoanh/admin/placevn.html?id=...` (phòng khi
  sau này tab work-verify có lẫn ID địa danh)
- Mở `target="_blank"` (tab mới) — Admin không mất vị trí đang duyệt danh sách.

Không sửa hàm `wvPassPerson()` hay bất kỳ phần nào của T503.

## Backup

`docs/sessions/2026-10-31/namevimap.html.bak3` (trước khi sửa; `.bak`/`.bak2`
đã có sẵn từ T503 vòng 1/2, không đè).

## Test thật (Browser pane, session Admin đã đăng nhập Google)

1. Mở `http://127.0.0.1:8080/daoanh/admin/namevimap.html` → click tab
   "✍️ Xác minh tác giả".
2. Screenshot bảng: cột "MÃ NGƯỜI" hiện `A001583 Cưu Ma La Thập`,
   `A001301 Trí Khải`... dạng link màu amber.
3. Click thật vào ID `A001583` → mở
   `http://127.0.0.1:8080/daoanh/admin/person.html?id=A001583`
   (xác nhận qua `read_network_requests`: `200 OK`).
4. Trang đích hiển thị tiêu đề `A001583` / `Cưu Ma La Thập` / Hán `鳩摩羅什` —
   khớp đúng dòng đã bấm.

py_compile: không áp dụng (không sửa file `.py` nào).

## Trạng thái

`in_progress` — đã sửa + verify bằng Browser pane thật, **CHƯA đánh DONE**,
**CHƯA commit**. Chờ Admin xác nhận hành vi mở tab mới (`target="_blank"`)
đúng ý muốn trước khi đóng task.

## Cập nhật 2026-10-31 (Admin báo link A001844 không mở được)

Admin báo sau khi đã verify A001583 OK, link `A001844` không click được.
Điều tra lại bằng Browser pane thật (session Admin đã đăng nhập), không đoán.

### Điều tra

1. Đọc lại `admin/namevimap.html` dòng 3070-3071 (code hiện tại, sau fix
   T504 vòng 1) — cột "Mã người" gọi `dilaLink(it.person_id)` cho **mọi**
   dòng, không có nhánh riêng theo ID — về lý thuyết A001844 phải render
   giống hệt A001583.
2. Query DB trực tiếp `SELECT id, name_zh, name_vi FROM people WHERE
   id='A001844'` → `('A001844', '闍那崛多', 'Đồ Na Quật Đa')` — không có ký
   tự đặc biệt (dấu nháy, `<`, `>`) có thể làm vỡ HTML của `<tr>`/`<a>`.
3. Curl trực tiếp `GET /daoanh/api/admin/work-verify?...` → `person_id:
   "A001844"` sạch, không có khoảng trắng thừa, không null.
4. Mở thật `http://127.0.0.1:8080/daoanh/admin/namevimap.html` → tab
   "Xác minh tác giả" → gõ `A001844` vào ô tìm kiếm → `read_page`/`find`
   xác nhận phần tử render đúng:
   `link "A001844" href="/daoanh/admin/person.html?id=A001844"`
   (giống hệt A001583 — `href="/daoanh/admin/person.html?id=A001583"`).
5. **Click thật** cả 2 link:
   - A001844 → trang `person.html?id=A001844` mở đúng, tiêu đề "A001844" /
     "Đồ Na Quật Đa" / Hán `闍那崛多` — khớp.
   - A001583 → trang `person.html?id=A001583` mở đúng, tiêu đề "A001583" /
     "Cưu Ma La Thập" / Hán `鳩摩羅什` — khớp.
   Console không có lỗi JS (`read_console_messages` rỗng).

### Kết luận root cause

**Không có bug code cho riêng A001844.** `dilaLink()` áp dụng đồng nhất
cho mọi `A######`, dữ liệu DB sạch, click thật qua Browser pane mở đúng cả
2 ID. Phát hiện thêm: trong Browser pane của phiên này có 1 tab khác
(`tab-3`) đang mở `admin/namevimap.html` qua đường dẫn **`file://...`**
(mở trực tiếp từ ổ đĩa, không qua server `http://127.0.0.1:8080`) — tab
đó không gọi được API (`fetch('/daoanh/api/...')` không có server để
resolve dưới `file://`), toàn bộ số liệu dashboard hiện `—` (rỗng). Nếu
Admin từng test trên 1 tab mở kiểu `file://` tương tự (thay vì qua
`127.0.0.1:8080`), bảng "Xác Minh Tác Giả" sẽ không tải được dữ liệu/JS sự
kiện đúng cách và toàn bộ link trong bảng (không riêng A001844) sẽ không
hoạt động — đây là ứng viên giải thích hợp lý nhất, không phải lỗi ở
`dilaLink()`/`wvLoad()`. Khả năng khác (ít chắc hơn, chưa loại trừ hẳn):
tab trình duyệt cũ của Admin chưa load lại JS mới sau khi fix T504 vòng 1
được lưu (file HTML tĩnh, `Cache-Control: no-cache` nhưng vẫn cần 1 lần
reload để nạp JS mới nếu tab đã mở từ trước khi sửa).

### Không có thay đổi code thêm cho mục này

Không sửa gì thêm trong `dilaLink()`/`wvLoad()` — code đã đúng cho mọi ID.
Khuyến nghị Admin: luôn mở `http://127.0.0.1:8080/daoanh/admin/namevimap.html`
(không mở file HTML trực tiếp bằng `file://`), và hard-refresh (Ctrl+F5)
nếu tab đã mở từ trước khi có fix.
