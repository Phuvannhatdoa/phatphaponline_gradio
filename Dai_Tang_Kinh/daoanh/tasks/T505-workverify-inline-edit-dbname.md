---
id: T505
title: "Tab Xác Minh Tác Giả (namevimap.html) — sửa trực tiếp cột \"Tên hiện tại (DB)\" trước khi Pass"
status: in_progress
created: 2026-10-31
former_ids: []
related: [T503, T504]
---

# T505 — Inline edit cột "Tên hiện tại (DB)" trong tab Xác Minh Tác Giả

## Yêu cầu Admin (2026-10-31)

Trên `http://127.0.0.1:8080/daoanh/admin/namevimap.html`, tab **"✍️ Xác
minh tác giả"** (`#tab-workverify`, T486), Admin muốn sửa trực tiếp tên
trong cột **"Tên hiện tại (DB)"** ngay trên bảng (inline edit), không cần
ô Name riêng như trước (T503). Khi Admin sửa tên trong ô đó rồi bấm Pass,
giá trị đã sửa phải được gửi qua ĐÚNG luồng Pass hiện có (`POST
/daoanh/api/admin/work-verify/<person_id>/pass`) để lưu vào
`people.name_vi`. Nếu Admin KHÔNG sửa gì, hành vi giữ như T503: Pass dùng
tên DB hiện tại.

## Quyết định hợp nhất ô Name (T503) + cột "Tên hiện tại (DB)"

Trước T505, mỗi dòng chưa Pass có **2 ô riêng**: cột 3 "Tên hiện tại (DB)"
(text tĩnh) và ô Name trong cột "Pass" (`input.wv-pass-input`, placeholder
"Nhập tên Việt…", mặc định trống, dùng `data-name-db` làm fallback khi để
trống — xem T503). Admin yêu cầu rõ: "Đây là thay đổi tách biệt khỏi phần
'ô Name' đã có (nếu 2 ô đó trùng nhau thì hợp nhất, nêu rõ quyết định
trong báo cáo)".

**Quyết định: hợp nhất.** 2 ô này cùng mục đích (xác định `name_vi` sẽ gửi
lên API Pass) — giữ cả 2 sẽ gây nhầm lẫn (Admin không biết sửa ô nào có
tác dụng). Xoá hẳn `input.wv-pass-input` trong cột Pass; biến cột 3 "Tên
hiện tại (DB)" thành `input.wv-dbname-input` (khởi tạo = `it.name_db`),
cột Pass chỉ còn nút `✓ Pass` (không còn ô nhập liệu).

## Thay đổi code (`admin/namevimap.html`)

### `wvLoad()` — dòng ~3064-3085 (trước)

Before:
```js
const pass = it.passed
    ? `<span style="color:#22c55e;font-size:12px">✓ ${_esc(it.name_db)}</span>`
    : `<input type="text" class="wv-pass-input" value="" placeholder="Nhập tên Việt… (để trống = giữ nguyên &quot;${_esc(it.name_db || '—')}&quot;)" title="..." data-name-db="${_esc(it.name_db || '')}" style="width:220px;font-size:12px" oninput="wvToggleBtn(this)"> <button class="etl-flag-pass" onclick="wvPassPerson(this)">✓ Pass</button>`;
return `<tr data-person-id="${_esc(it.person_id)}">
    <td>${dilaLink(it.person_id)}</td>
    <td>${_esc(it.name_zh || '—')}</td>
    <td style="font-size:12px">${_esc(it.name_db || '—')}</td>
    ...
    <td>${pass}</td>
</tr>`;
```

After:
```js
const dbNameCell = it.passed
    ? `${_esc(it.name_db || '—')}`
    : `<input type="text" class="wv-dbname-input" value="${_esc(it.name_db || '')}" data-orig="${_esc(it.name_db || '')}" title="Sửa trực tiếp tên hiện tại trong DB — bấm Pass sẽ lưu đúng giá trị đang hiện ở đây. Để nguyên = giữ tên cũ." style="width:150px;font-size:12px">`;
const pass = it.passed
    ? `<span style="color:#22c55e;font-size:12px">✓ ${_esc(it.name_db)}</span>`
    : `<button class="etl-flag-pass" onclick="wvPassPerson(this)">✓ Pass</button>`;
return `<tr data-person-id="${_esc(it.person_id)}">
    <td>${dilaLink(it.person_id)}</td>
    <td>${_esc(it.name_zh || '—')}</td>
    <td style="font-size:12px">${dbNameCell}</td>
    ...
    <td>${pass}</td>
</tr>`;
```

### `wvPassPerson()` — dòng ~3116-3129 (trước)

Before:
```js
async function wvPassPerson(btn) {
    const tr = btn.closest('tr');
    const personId = tr.dataset.personId;
    const input = tr.querySelector('.wv-pass-input');
    const typed = (input?.value || '').trim();
    const nameDb = (input?.dataset.nameDb || '').trim();
    const name = typed || nameDb;
    if (!name) { alert('Chưa có tên hiện tại trong DB — vui lòng nhập tên Việt trước khi Pass.'); return; }
    ...
```

After:
```js
async function wvPassPerson(btn) {
    const tr = btn.closest('tr');
    const personId = tr.dataset.personId;
    const input = tr.querySelector('.wv-dbname-input');
    const name = (input?.value || '').trim();
    if (!name) { alert('Ô "Tên hiện tại (DB)" đang trống — vui lòng nhập tên Việt trước khi Pass.'); return; }
    ...
```
Phần gửi request (`fetch(.../pass, {body: JSON.stringify({name_vi: name})})`) và
xử lý sau thành công (`tr.remove()`, cập nhật `#wv-total-label`) **không đổi** —
chỉ đổi nguồn lấy `name`.

`wvToggleBtn()` giữ nguyên (không còn được gọi từ markup mới, giữ lại để
không vỡ nếu còn cache JS cũ nào gọi qua `oninput`).

## Backend — không đổi

`routes_namevi.py` `admin_work_verify_pass()` (dòng ~1392-1434, từ T503)
đã có logic: nếu `name_vi` gửi lên rỗng → tự lấy `people.name_vi` hiện có
làm fallback; nếu `name_vi` có giá trị → dùng đúng giá trị đó. Vì frontend
giờ luôn gửi giá trị không rỗng của ô `.wv-dbname-input` (đã chặn client
nếu rỗng), nhánh fallback phía backend chỉ còn là lớp an toàn thứ 2, không
cần sửa gì thêm.

## py_compile

```
python -m py_compile routes_namevi.py   →  PY_COMPILE_OK (không đổi file này, chạy lại để chắc)
```
Không sửa `.py` nào ở T505 — chỉ sửa `admin/namevimap.html` (JS phía client).

## Backup

`docs/sessions/2026-10-31/namevimap.html.bak4` (trước khi sửa T505, sau
khi đã có fix T504 vòng link A001844 — không đè `.bak`/`.bak2`/`.bak3` cũ
của T503/T504).

## Verify thật (Browser pane, session Admin đã đăng nhập Google)

Test trên `A001844` (闍那崛多 / Đồ Na Quật Đa, group `C_review`, có đề
xuất file khác nội dung = `Xà-na Quật-đa`):

1. Trước khi sửa — DB: `people.name_vi = 'Đồ Na Quật Đa'`,
   `name_vi_map` chưa có dòng nào cho `A001844`.
2. Mở tab Xác Minh Tác Giả → tìm `A001844` → cột "Tên hiện tại (DB)" hiện
   `<input>` khởi tạo sẵn `Đồ Na Quật Đa`, cột Pass chỉ còn 1 nút `✓ Pass`
   (không còn ô Name riêng) — screenshot xác nhận.
3. Triple-click chọn hết text trong ô, gõ đè `Xà-na Quật-đa` (đúng giá trị
   "Tên đề xuất (file)" của dòng này — chọn giá trị có ý nghĩa thật trong
   hệ thống, không phải chuỗi rác, để test phản ánh đúng luồng dùng thật)
   — screenshot xác nhận ô hiện `Xà-na Quật-đa`.
4. Click thật nút `✓ Pass` → `read_network_requests` xác nhận
   `POST /daoanh/api/admin/work-verify/A001844/pass → 200 OK`; dòng biến
   mất khỏi bảng ngay (còn `0 người` khi đang lọc theo `A001844`) — khớp
   hành vi T503 (`tr.remove()`).
5. Query DB trực tiếp SAU khi Pass:
   ```
   people.name_vi = 'Xà-na Quật-đa'            (đổi đúng từ 'Đồ Na Quật Đa')
   name_vi_map: ('A001844', 'Xà-na Quật-đa', 'nhatdoaphuvan@gmail.com',
                  '2026-10-31T17:10:10...')
   ```
   → xác nhận giá trị **đã sửa inline** (không phải giá trị DB cũ) được
   lưu đúng qua luồng Pass thật, `approved_by` = email session thật.
6. Reload lại trang, tìm lại `A001844` → cột "Tên hiện tại (DB)" hiện
   text tĩnh `Xà-na Quật-đa`, cột Pass hiện `✓ Xà-na Quật-đa` màu xanh —
   khớp dữ liệu đã ghi ở bước 5 (screenshot xác nhận).

Case "không sửa gì" (fallback giữ nguyên tên DB) đã được verify ở T503
vòng 2 (A001583, A001301) — không lặp lại ở đây vì luồng gửi giá trị
input không đổi bản chất (input vẫn gửi đúng text đang hiển thị, dù đó là
text gốc chưa sửa hay text đã sửa).

## CHƯA làm (đúng ràng buộc)

- Chưa đánh dấu DONE.
- Chưa `git add/commit`.
- Không có UPDATE DB thủ công nào — toàn bộ test đều qua click thật trên
  UI + API `/pass` thật (xem mục Verify).

## Việc còn lại / cần Admin xác nhận

1. Xác nhận quyết định hợp nhất 2 ô (xoá ô Name riêng, dùng thẳng ô "Tên
   hiện tại (DB)") đúng ý muốn.
2. Admin lưu ý: `A001844` trong DB hiện đã đổi thành `Xà-na Quật-đa` (do
   test thật ở trên, không phải dữ liệu giả lập) — nếu muốn giữ nguyên
   `Đồ Na Quật Đa` thay vì đổi sang `Xà-na Quật-đa`, cần Admin tự sửa lại
   qua UI (không tự ý revert bằng tay).
