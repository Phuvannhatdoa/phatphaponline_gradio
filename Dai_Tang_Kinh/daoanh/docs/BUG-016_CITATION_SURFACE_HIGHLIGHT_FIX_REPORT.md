# Audit / Bug Fix Report — BUG-016 (DAITANG_CITATION_READER_NO_SCROLL_HIGHLIGHT_001)

> Lưu tại `docs/BUG-016_CITATION_SURFACE_HIGHLIGHT_FIX_REPORT.md`.

## 1. Vị trí audit (thực tế, không đoán)

| Hạng mục | File / Schema / Endpoint thực tế |
|----------|----------------------------------|
| Data source | `places_dila.listbibl` / `raw_xml` (fosizhi) — trường `place_tag` = surface form Hán đã trích cho từng citation entry |
| API endpoint | `GET /daoanh/api/entity/<id>/... ` (route xây `dila_references`, app.py:14522-14561) — không đổi, chỉ đọc |
| Resolver / logic | `places.html` JS: `dtRenderRefs` (~line 2927), `dtJumpToPassage` (~line 2968), `dtSwitchPassage` (~line 3056), `dtRenderPassage` (~line 3535+) |
| Component / renderer | `places.html` — Tab Đại Tạng → Dẫn Chiếu (`.dt-ref-item`) → Tab Nguyên Văn (`#dt-han-body .dt-seg-han`) |
| Schema contract | Không đổi — chỉ dùng field `place_tag` đã có sẵn trong response, trước đây bị bỏ phí (chỉ hiển thị làm chip, không dùng để highlight) |

## 2. Root cause (đã xác minh)

- **Lớp gây lỗi:** renderer (frontend JS) — 2 lỗi độc lập:
  1. **Dead reference / thiếu hàm:** `dtHighlightSurface` được nhắc tới trong `docs/bugs.md`
     (fix log cũ 2026-09-10) nhưng **không tồn tại trong code** (`grep dtHighlightSurface
     places.html` → 0 hit trước khi sửa). `dtJumpToPassage(idx)` chỉ nhận 1 tham số, không
     có chỗ nhận `surface`. Nút bị revert lại label cũ "📖 Xem Văn Bản" ở một commit sau đó
     — code thực tế bị "thoái lui" so với log fix đã ghi.
  2. **Bug HTML-attribute quoting phát hiện trong lúc build lại fix** (không có trong log cũ,
     phát hiện mới qua test bằng click thật): khi viết
     `onclick="dtJumpToPassage(' + pIdx + ',' + JSON.stringify(surface) + ')"`,
     `JSON.stringify(surface)` sinh chuỗi bọc bởi dấu `"` (vd `"少林寺"`), nhúng thẳng vào
     attribute cũng dùng `"..."` → trình duyệt cắt attribute tại dấu `"` đầu tiên. Test bằng
     cách gọi hàm trực tiếp trong console (`dtJumpToPassage('...')`) sẽ **PASS giả** vì bỏ
     qua bước parse HTML thật — chỉ lộ ra khi click bằng chuột thật qua DOM đã render.

## 3. Data/API contract trước → sau

| | Trước | Sau |
|--|-------|-----|
| Data | `place_tag` có sẵn trong response, chỉ hiển thị làm chip phụ, không dùng để highlight | Không đổi — chỉ dùng thêm `r.place_tag \|\| window._dtEntityZh` làm "surface" truyền cho `dtJumpToPassage` |
| API response | không đổi | không đổi (0 thay đổi backend) |
| `dtJumpToPassage(idx)` | 1 tham số, chỉ đổi tab + đổi passage, không highlight | `dtJumpToPassage(idx, surface)` — lưu `surface` vào state "sticky" `_dtPendingSurface`, đổi tab + đổi passage + tự động highlight (kể cả sau khi passage render lại bất đồng bộ qua `dtLoadUnits`) |
| Nút UI | "📖 Xem Văn Bản" | "📖 Đọc đoạn văn" |
| `onclick` attribute sinh ra | `dtJumpToPassage(0,"少林寺")` **bị cắt cụt** thành `dtJumpToPassage(0,` (bug quoting) | `dtJumpToPassage(0,"少林寺")` nguyên vẹn (bọc `_escHtml()` quanh `JSON.stringify()`) |

## 4. Files changed

- `daoanh/places.html` — duy nhất file thay đổi:
  - `renderDaiTangMain`: reset `_dtPendingSurface = null` khi nạp entity mới.
  - `dtRenderRefs`: tính `surface`, đổi label nút, sửa `onclick` (kèm `_escHtml` quanh
    `JSON.stringify` để không vỡ attribute).
  - `dtJumpToPassage(idx, surface)`: thêm tham số `surface`.
  - `dtSwitchPassage(idx, keepHighlight)`: thêm tham số `keepHighlight` — điều hướng thủ
    công (dt-pchip) tự huỷ highlight đang chờ.
  - `dtHighlightSurface(surface)` — **hàm mới, re-implement từ đầu** (không tồn tại trước đó).
  - `dtRenderPassage`: gọi lại `dtHighlightSurface(_dtPendingSurface)` ở cuối hàm (bao cả
    nhánh render đồng bộ `dtBuildSegments` fallback và nhánh render lại bất đồng bộ sau
    `dtLoadUnits`).
- Không đổi `app.py`, không đổi DB/schema/route nào khác.
- Backup trước khi sửa: `daoanh/docs/sessions/2026-09-26/places.html.bak-bug016`.
- Chi tiết từng đoạn diff: `daoanh/docs/sessions/2026-09-26/changes.md`.

## 5. Migration / import / dry-run / rollback

- Không chạm DB — không cần migration/backup DB.
- Revert: khôi phục `daoanh/docs/sessions/2026-09-26/places.html.bak-bug016` → `places.html`
  (chưa có git commit cho thay đổi này — theo yêu cầu, KHÔNG tự `git add/commit`).

## 6. Test cases & kết quả

Test qua Browser tool thật (`local_gateway.py:8080` + `app.py:5000` đang chạy sẵn),
route `http://localhost:8080/daoanh/places.html?select=PL000000023255` (Thiếu Lâm Tự).

| Case | Input | Expected | Actual | PASS/FAIL |
|------|-------|----------|--------|-----------|
| Case yêu cầu (đúng evidence BUG-016 gốc) | Click thật (mouse) nút "📖 Đọc đoạn văn" citation `T50n2060_p0457c16` | Chuyển tab Nguyên Văn, scroll + highlight "少林寺" | `activeTab:"fulltext"`, `markCount:1`, `markTexts:["少林寺"]`, `bg:"rgba(196,137,26,.35)"`, `visible:true`; screenshot xác nhận dòng "下已有**少林寺**。即" tô vàng | ✅ |
| Citation khác (place_tag khác nhau, không hard-code) | Click "Đọc đoạn văn" citation `T50n2060_p0485a21` (place_tag = "少林" thay vì "少林寺") | Highlight đúng surface riêng của citation đó | `markCount:1, markTexts:["少林"]` | ✅ |
| Điều hướng thủ công sau khi jump (không dính highlight cũ) | Click 1 `.dt-pchip` khác (không qua nút "Đọc đoạn văn") | Highlight cũ tự dọn, không hiện sai chỗ | `markCount:0` | ✅ |
| Fallback — surface không tồn tại trong passage | `dtHighlightSurface('KHONG_TON_TAI_XYZ')` | Trả `false`, không throw, không tạo `<mark>` rác | `false`, `marksAfter:0` | ✅ |
| Fallback — surface rỗng/null | `dtHighlightSurface('')` / `dtHighlightSurface(null)` | Trả `false`, dọn sạch mark cũ (nếu có), không lỗi | `false`, `false` | ✅ |
| Regression — path cũ không truyền surface | `.dt-rel-item` (Tab Quan Hệ, Section C) gọi `dtJumpToPassage(0)` 1 tham số | Vẫn chuyển tab + đổi passage bình thường, không highlight (hành vi y hệt trước fix) | Code path không đổi, `surface=undefined` → falsy → không highlight, không lỗi | ✅ (logic, entity test hiện tại không có texts nên section C rỗng — không tái hiện được bằng UI thật, nhưng code path xác nhận qua đọc lại) |
| Cú pháp JS toàn file | `@babel/parser` parse 3 script block | 0 lỗi | 0 lỗi (chạy 2 lần, trước & sau khi vá bug quoting) | ✅ |
| Console errors mới | Thao tác click/jump nhiều lần | Không phát sinh lỗi console mới | Chỉ còn lỗi tiền tồn tại không liên quan (`POST .../translate → 500`, `SyntaxError: Unexpected end of input` — cùng nguồn gốc BUG-015, endpoint dịch AI lỗi 500 trả body rỗng) | ✅ (0 lỗi mới) |

## 7. Limitation / data gap còn lại

- `surface` ưu tiên `r.place_tag` (surface form thật của DILA cho đúng citation đó); khi
  citation không có `place_tag` (vd nhánh FOSIZHI thiếu tag, hoặc listbibl entry không có
  `{...}`), fallback dùng tên Hán chung của entity (`window._dtEntityZh`) — có thể không khớp
  y hệt mặt chữ trong passage nếu passage dùng dị bản/từ đồng nghĩa khác entity name. Đây là
  giới hạn dữ liệu nguồn (DILA), không phải bug renderer — không tự "đoán" thêm surface bằng
  LLM hay suy diễn.
- `dtHighlightSurface` chỉ highlight **occurrence đầu tiên** tìm thấy trong segment đầu tiên
  khớp — nếu 1 passage dài có nhiều đoạn đều chứa surface, chỉ đoạn đầu được đánh dấu/scroll
  tới (chấp nhận được cho mục tiêu "định vị nhanh", không mở rộng phạm vi ngoài yêu cầu gốc).
- Không sửa `dt-rel-item` Section C (Tab Quan Hệ, `dtJumpToPassage(0)` không truyền `surface`)
  — giữ nguyên minimal-fix, path đó không nằm trong evidence gốc BUG-016 (route ghi rõ
  "Tab Đại Tạng → Dẫn Chiếu").
- Lỗi 500 tiền tồn tại ở `POST /daoanh/api/place/<id>/translate` (không liên quan BUG-016,
  khả năng liên quan Gemini API key/quota tại `app.py` — xem `CLAUDE.md` mục Gemini API key)
  — flag riêng nếu cần điều tra thêm, không nằm trong phạm vi fix này.
