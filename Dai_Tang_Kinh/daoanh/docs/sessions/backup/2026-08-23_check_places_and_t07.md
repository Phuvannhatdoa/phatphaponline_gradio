# 2026-08-23 — Kiểm tra places.html (Thiếu Lâm Tự) + T07 Wikipedia fallback

## Mô tả ngắn task

User yêu cầu: mở browser, test case Thiếu Lâm Tự qua các tab Thực Thể/Đại Tạng/Đồ Thị/Niên Đại,
sửa nếu có lỗi, rồi làm tiếp task chưa xong theo đúng thứ tự trên dashboard.

## Kiểm tra places.html — phát hiện 2 lỗi thật (đã sửa)

Phiên dev khác vừa mở rộng `places.html` từ 6 tab lên ~15 tab ("15 TABs expansion"). Khi test
`selectItem('PL000000023255')` (Thiếu Lâm Tự) qua browser thật:

1. **Crash toàn bộ trang khi chọn bất kỳ địa danh nào:** `Cannot set properties of null (setting
   'className')` — vòng lặp reset chip nguồn (`['chipDila','chipCbeta','chipBdrc'].forEach(...)`)
   vẫn tham chiếu `chipBdrc`, nhưng phần tử HTML này đã bị gỡ khỏi trang (có sẵn comment
   `// BDRC block removed`) mà quên xoá khỏi mảng JS. Sửa: bỏ `'chipBdrc'` khỏi cả 2 vòng lặp reset.
2. **Tab "📜 Đại Tạng" crash khi click:** `Cannot read properties of null (reading 'style')` —
   nút tab đổi `data-t="daitang"` (đặt tên lại theo tiếng Việt) nhưng panel HTML vẫn giữ
   `id="tp-cbeta"` cũ, không đổi theo. `loadTabData()` đã có sẵn remap `daitang→cbeta` nhưng dòng
   hiển thị panel (`document.getElementById('tp-'+target).style.display=...`) nằm TRƯỚC
   `loadTabData()`, không có remap này nên vẫn lấy `tp-daitang` = null. Sửa: thêm cùng remap +
   guard `if (panel)` phòng các tab mới khác cũng thiếu panel tương tự.

Sau khi sửa: tab Thực Thể + Đại Tạng + Niên Đại đều verify được qua browser thật (gõ/click thật,
không chỉ gọi hàm), dữ liệu hiển thị đúng — kể cả thấy được T21 (Niên Đại/Wikidata bridge) đã được
phiên kia build xong (495 CE, Bắc Ngụy, nguồn Wikidata P571 + DILA time_periods).

**Tab "🕸 Đồ Thị" không verify được lần này** — không phải do code (API trả dữ liệu đúng, code
`_renderVisGraph` không đổi so với bản đã test kỹ ở T17/T28) mà do `document.visibilityState` của
tab browser tool đang là `"hidden"` lúc test, khiến `requestAnimationFrame` (vis-network physics
dùng để layout) bị trình duyệt tạm dừng hoàn toàn — treo cuộc gọi `javascript_exec`. Xác nhận qua
việc gọi `_renderVisGraph()` trực tiếp với dữ liệu tối giản (1 node) vẫn treo y hệt, còn
`document.title`/`1+1` chạy bình thường khi KHÔNG liên quan tới rAF. Đây là giới hạn của môi trường
test, không phải lỗi sản phẩm.

## T07 — Wikipedia multi-language fallback

Task tiếp theo chưa xong theo đúng thứ tự dashboard (T05 kiểm tra lại xác nhận vẫn `blocked` —
~2.000 file TTL còn lại chưa từng tồn tại trong môi trường local, đã đánh dấu rõ trong task file).

**Backend** (`app.py`, viết lại `wiki_fetch()` + `_wiki_search_lang()` mới):
- Bug cũ: fallback zh chỉ chạy khi vi tìm KHÔNG RA kết quả, không chạy khi request vi bị lỗi mạng
  (nằm sau `continue` bỏ qua đoạn code đó). Không có tầng `en` dù acceptance criteria yêu cầu.
- Viết lại: thử tuần tự `vi → zh → en`, mỗi tầng thử cả `name_zh` (khớp tốt hơn, là tên gốc) và
  `name_vi`. Thêm `refresh` param (bỏ qua cache). Lưu `source`(=lang)/`license` vào
  `place_wiki_snapshots` (cột có sẵn nhưng trước đó không populate) để UI biết ngôn ngữ đã khớp.
- Bug hiển thị phát hiện lúc test: snippet còn giữ HTML entity literal (`&quot;`) vì code cũ chỉ
  regex-strip tag chứ không unescape entity — thêm `html.unescape()`.

**Đụng độ song song:** phiên dev khác ĐÃ viết sẵn JS frontend (`loadWiki`/`refreshWiki`, đúng tên
biến/hàm, đúng contract API) nhưng CHƯA thêm HTML markup (`#wikiBlock` và các con) — JS đó gọi
`document.getElementById('wikiBlock')` ra `null`, luôn no-op im lặng. Ban đầu tôi tự viết cả JS lẫn
HTML riêng, dính trùng khai báo `_wikiPlaceId`/`loadWiki` → `SyntaxError` crash toàn trang. Xử lý:
giữ bản JS của họ (có `if (!block) return` guard tốt hơn), bỏ bản JS trùng của mình, chỉ thêm phần
HTML còn thiếu + gọi `loadWiki()` đúng chỗ trong `selectItem()`.

**Test:** curl (cache hit, `refresh:true` sống, case không tìm thấy wiki) + browser thật (chọn
Thiếu Lâm Tự → khối Wikipedia hiện đúng, badge "VI", nút "🔄 Làm mới" hoạt động, không còn `&quot;`).

## File đã sửa

- `app.py` — viết lại `wiki_fetch()`, `_wiki_search_lang()` (mới)
- `places.html` — fix `chipBdrc` crash, fix `daitang`/`tp-cbeta` panel mismatch, thêm HTML
  `#wikiBlock` cho T07 (JS giữ nguyên của phiên kia)
- `tasks/T05-ttl-expand-etl.md` — xác nhận lại `blocked`, ghi rõ lý do
- `tasks/T07-wikipedia-fallback.md` — thêm ghi chú về đụng độ + fix entity-decode
- `docs/sessions/2026-08-23_check_places_and_t07.md` — session log này

## Liên hệ ROADMAP

- Việc còn lại theo đúng thứ tự dashboard sau T07: T11 (RAG Việt chat), T12 (Dịch Mượt & Cache
  Translation) — cả 2 priority `high`, quy mô lớn hơn nhiều, cần thảo luận scope trước khi bắt đầu.
- Đồ Thị (Thiếu Lâm Tự) cần verify lại qua browser thật ở phiên sau khi môi trường test không bị
  `document.visibilityState === "hidden"`.
