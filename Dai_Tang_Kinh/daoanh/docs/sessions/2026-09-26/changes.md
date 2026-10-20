# Session 2026-09-26 — BUG-016 fix

## Backup
- `places.html` → `docs/sessions/2026-09-26/places.html.bak-bug016` (trước khi sửa)

## Thay đổi (chỉ `places.html`, 0 DB, 0 API, 0 schema)

1. **`dtRenderRefs`** (Tab Đại Tạng → Dẫn Chiếu, `.dt-ref-item`):
   - Tính `surface = r.place_tag || window._dtEntityZh || ''` cho mỗi citation
     (`place_tag` = surface form thật trích từ `listbibl`/`fosizhi` entry của
     chính DILA cho citation đó; fallback = tên Hán của entity đang xem).
   - Nút đổi label `"📖 Xem Văn Bản"` → `"📖 Đọc đoạn văn"`.
   - `onclick="dtJumpToPassage(pIdx)"` → `onclick="dtJumpToPassage(pIdx, surface)"`.

2. **`dtJumpToPassage(idx, surface)`** — thêm lại tham số `surface` (đã bị mất khi
   nút bị revert về label cũ). Lưu `surface` vào biến "sticky" `_dtPendingSurface`
   rồi gọi `dtSwitchTab('fulltext')` + `dtSwitchPassage(idx, true)`.

3. **`dtSwitchPassage(idx, keepHighlight)`** — thêm tham số `keepHighlight`.
   Điều hướng thủ công qua `.dt-pchip` (click trực tiếp, không qua
   `dtJumpToPassage`) gọi `dtSwitchPassage(i)` với `keepHighlight` falsy →
   tự huỷ `_dtPendingSurface` cũ, tránh highlight "dính" sai đoạn khi user tự
   chuyển trang thủ công sau khi jump.

4. **`dtHighlightSurface(surface)` — RE-IMPLEMENT MỚI HOÀN TOÀN** (hàm này
   không tồn tại trong code trước đó — 0 hit khi grep, xác nhận qua audit).
   - Gỡ `<mark class="dt-surface-hl">` cũ (nếu có) trước khi tìm lại.
   - Tìm segment `#dt-han-body .dt-seg-han` đầu tiên có `textContent` chứa
     `surface`.
   - Bọc đúng vị trí khớp trong `innerHTML` (dùng `_escHtml` để so khớp đúng
     chuỗi đã escape) bằng `<mark class="dt-surface-hl" style="background:
     rgba(196,137,26,.35)...">`.
   - `scrollIntoView({behavior:'smooth', block:'center'})` trên `.dt-segment`
     cha của segment đó.
   - Trả `true`/`false` (không tìm thấy) để caller có thể biết kết quả.

5. **`dtRenderPassage(idx)`** — cuối hàm, sau khi `hb`/`vb` đã được set
   `innerHTML` (dù là render đồng bộ lần đầu bằng `dtBuildSegments` fallback,
   hay render lại bất đồng bộ sau khi `dtLoadUnits` fetch xong): nếu có
   `_dtPendingSurface` đang chờ → gọi lại `dtHighlightSurface(_dtPendingSurface)`.
   Vì `dtRenderPassage` luôn ghi đè `innerHTML` từ đầu, không cần dọn `<mark>`
   cũ thủ công ở đây — `dtHighlightSurface` tự dọn theo `querySelectorAll`.

6. **`renderDaiTangMain(d)`** — reset `_dtPendingSurface = null` khi nạp entity
   mới, tránh rò rỉ highlight từ entity trước sang entity sau.

## Không đổi
- `dt-rel-item` (Tab Quan Hệ, Section C "Nguồn Ánh Xạ Kinh Điển") vẫn gọi
  `dtJumpToPassage(0)` (không truyền `surface`) — tương thích ngược hoàn
  toàn (arg thứ 2 undefined → không highlight, hành vi y hệt trước fix, không
  regression).
- Không đụng `app.py`, DB, hay route nào khác.

## Bug phụ phát hiện + fix trong lúc verify (cùng BUG-016, không tách riêng)
Lần verify đầu bằng **click thật qua Browser tool** (không chỉ gọi hàm JS
trực tiếp) phát hiện: `onclick="dtJumpToPassage(' + pIdx + ',' + JSON.stringify(surface) + ')"`
sinh ra HTML attribute bị **vỡ giữa chừng** — `JSON.stringify(surface)` bọc
chuỗi bằng dấu `"` (vd `"少林寺"`), nhúng thẳng vào attribute vốn cũng dùng
`"..."` → trình duyệt parse `onclick` bị cắt ở dấu `"` đầu tiên
(`getAttribute('onclick')` trả về đúng `"dtJumpToPassage(0,"` — cụt).
Click thật do đó **không** gọi được hàm (dù gọi tay `dtJumpToPassage(...)` từ
console vẫn chạy đúng — dễ đánh lừa nếu chỉ test qua console). Fix: bọc thêm
`_escHtml(...)` quanh `JSON.stringify(surface)` để `"` → `&quot;` trước khi
nhúng vào attribute:
`onclick="dtJumpToPassage(' + pIdx + ',' + _escHtml(JSON.stringify(surface)) + ')"`.
Sau fix, `getAttribute('onclick')` trả đúng `dtJumpToPassage(0,"少林寺")`.

## Verify
- `@babel/parser` parse 3 script block trong `places.html` → **0 lỗi cú pháp**
  (chạy lại sau cả 2 vòng sửa).
- Test logic thủ công (Node, không DOM): chuỗi Hán mẫu chứa `少林寺` → wrap
  đúng vị trí bằng `<mark>`, `markCount=1`.
- **Browser thật** (`local_gateway.py:8080` + `app.py:5000` đã chạy sẵn),
  route `/daoanh/places.html?select=PL000000023255` → Tab Đại Tạng → Dẫn Chiếu:
  - Label nút xác nhận đổi thành **"📖 Đọc đoạn văn"** (trước đó "📖 Xem Văn Bản").
  - Click thật (mouse, qua `computer` tool, không phải gọi hàm JS) trên citation
    `T50n2060_p0457c16` → tab tự chuyển sang **Nguyên Văn** (`activeTab:"fulltext"`)
    → `markCount:1, markTexts:["少林寺"], bg:"rgba(196, 137, 26, 0.35)", visible:true`
    → khớp evidence gốc BUG-016 trong `docs/bugs.md`. Screenshot xác nhận
    dòng "下已有**少林寺**。即" tô vàng đúng vị trí.
  - Click citation khác (`T50n2060_p0485a21`, place_tag khác = `"少林"`) →
    cũng highlight đúng surface riêng của citation đó → xác nhận không hard-code,
    lấy đúng theo từng citation.
  - Click thủ công 1 `.dt-pchip` khác (điều hướng không qua nút "Đọc đoạn văn")
    → `markCount:0` → xác nhận highlight cũ tự dọn, không dính sai đoạn (edge case
    yêu cầu trong luồng debug).
  - Console: chỉ còn lỗi tiền tồn tại không liên quan
    (`POST /daoanh/api/place/.../translate → 500` — endpoint dịch AI, đã có
    trước khi sửa, không phải do thay đổi này; `SyntaxError: Unexpected end of
    input` cùng nguồn gốc — response 500 body rỗng, xem BUG-015 cùng dạng).
    0 lỗi console mới phát sinh từ thay đổi BUG-016.
