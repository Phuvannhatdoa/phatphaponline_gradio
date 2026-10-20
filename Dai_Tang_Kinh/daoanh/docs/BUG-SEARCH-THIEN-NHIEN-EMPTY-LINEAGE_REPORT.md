# Audit / Bug Fix Report — BUG: Search "Thiên Nhiên" no results (empty lineage quicklist)

> Route/case: `/daoanh/places?mode=lineage&focus=A007928&lm=tree`

## 1. Vị trí audit (thực tế, không đoán)

| Hạng mục | File / Schema / Endpoint thực tế |
|----------|----------------------------------|
| Data source | `data/lineage.db` — `entity_claims`/lineage edge tables (gián tiếp qua API) |
| API endpoint | `GET /daoanh/api/monk/A007928/lineage-tree?up=2&down=2&include_single=1` → `{"ok":true,"edges":[],"nodes":[1 node]}` (0 edges, đúng — A007928 không có quan hệ thầy/trò nào trong DB) |
| API endpoint (phụ) | `GET /daoanh/api/monk/A007928/ancestor-path?root=A001719` → `{"ok":true,"found":false,"path":[{center node}]}` (hoạt động đúng, trả về path 1 phần tử = chính nó) |
| Resolver / logic | `places.html:6207` hàm `loadLineageTree(dilaId)` |
| Component / renderer | `places.html:6246-6254` (nhánh "không có cạnh truyền thừa") + `places.html:6400-6406` `_renderLineageSidebar()` + `places.html:8648-8652` listener ô input `#lineage-search` ("Tìm trong pháp hệ") |
| Schema contract | Không đổi — 0 DB/API mutation |

## 2. Root cause (đã xác minh)

- **Lớp gây lỗi:** renderer (early-return bug trong hàm JS `loadLineageTree`)
- **Nguyên nhân chính xác:** Ô "Tìm trong pháp hệ" (`#lineage-search`, placeholder "Tìm tăng nhân...") KHÔNG gọi API tìm kiếm — nó chỉ lọc (ẩn/hiện) các nút `<button>` đã có sẵn trong `#lineage-quicklist` (xem `_renderLineageSidebarHighlight()` tại `places.html:8663-8671`). Quicklist này được nạp bởi `_renderLineageSidebar()` → `_fetchAndRenderQuicklist()` (gọi `/api/monk/<id>/ancestor-path`).

  Trong `loadLineageTree()` (`places.html:6207`), khi cây truyền thừa trả về **0 cạnh** (`d.edges.length === 0` — đúng là trường hợp của A007928/Thiên Nhiên, người này chưa có quan hệ thầy/trò nào ghi trong DB), code rẽ vào nhánh "empty tree" tại dòng 6246 và **`return` sớm TRƯỚC khi gọi `_renderLineageSidebar()`** (dòng 6255, chỉ nằm ở nhánh else). Hệ quả: `#lineage-quicklist` không bao giờ được nạp nội dung cho các nhân vật không có cạnh truyền thừa — kể cả chính node trung tâm (A007928/Thiên Nhiên) cũng không có trong danh sách để lọc.

  Khi Admin gõ "Thiên Nhiên" vào ô tìm kiếm, `_renderLineageSidebarHighlight()` lọc trên danh sách rỗng → 0 kết quả hiển thị, trong khi API `monk-resolve`/`autocomplete`/`ancestor-path` đều trả dữ liệu đúng (đã kiểm bằng curl và DevTools network — không có request mới nào được gửi khi gõ vào ô này, xác nhận đây là lọc client-side thuần, không phải lỗi API/DB).

- **Bằng chứng trước khi sửa:** gõ "Thiên Nhiên" vào ô `#lineage-search` tại route trên → `document.getElementById('lineage-quicklist').innerHTML.length === 0` (đo bằng JS console) → không có chip nào để lọc, dù `/api/monk/A007928/ancestor-path?root=A001719` trả về đúng node "Thiên Nhiên".

## 3. Data/API contract trước → sau

| | Trước | Sau |
|--|-------|-----|
| Data/API | Không đổi — API vẫn trả `edges:[]` cho A007928 (đúng, không có quan hệ truyền thừa ghi nhận) | Không đổi |
| Renderer: nhánh "0 cạnh" trong `loadLineageTree()` | `return` trước khi gọi `_renderLineageSidebar()` → `#lineage-quicklist` rỗng vĩnh viễn | Gọi thêm `_renderLineageSidebar()` trước khi `return` → quicklist có ít nhất node trung tâm, ô "Tìm trong pháp hệ" lọc đúng |

## 4. Files changed

- `daoanh/places.html:6246-6259` — thêm lệnh gọi `_renderLineageSidebar()` trong nhánh "0 cạnh truyền thừa" của `loadLineageTree()`, để `#lineage-quicklist` (nguồn dữ liệu cho ô tìm kiếm "Tìm trong pháp hệ") luôn được nạp bất kể cây có cạnh hay không. Không đổi logic hiển thị cây rỗng (`emptyBox`/`canvas`), không đổi API, không đổi DB.

## 5. Migration / import / dry-run / rollback (nếu chạm DB)

- Không chạm DB/schema/API. Chỉ sửa 1 file JS trong `places.html`.
- Backup trước khi sửa: `daoanh/docs/sessions/2026-10-19/places.html.bak-before-BUG-thien-nhien-search`
- Revert: khôi phục file backup trên, hoặc `git checkout -- daoanh/places.html` nếu đã commit riêng.

## 6. Test cases & kết quả

| Case | Input | Expected | Actual | PASS/FAIL |
|------|-------|----------|--------|-----------|
| Case yêu cầu | Route `/daoanh/places?mode=lineage&focus=A007928&lm=tree`, gõ "Thiên Nhiên" vào ô "Tìm trong pháp hệ" | Quicklist hiện chip "Thiên Nhiên" (center node), được giữ lại sau khi lọc | Sau fix: quicklist có chip "Thiên Nhiên", gõ "Thiên Nhiên" → chip vẫn hiển thị (match) | ✅ |
| Fallback: query không khớp | Gõ "xyz_no_match" | Chip bị ẩn (0 kết quả hiển thị, đúng hành vi lọc) | Chip "Thiên Nhiên" biến mất khi gõ "xyz_no_match" | ✅ |
| Regression: node có cạnh truyền thừa | Route `/daoanh/places?mode=lineage&focus=A001719&lm=tree` (Huệ Năng, 99 cạnh) | Quicklist vẫn nạp bình thường như trước khi sửa (nhánh else không đổi) | Quicklist hiện chuỗi tổ truyền (bắt đầu "Huệ Năng"), không lỗi console | ✅ |
| API phụ trợ | `curl /daoanh/api/public/autocomplete?q=Thiên+Nhiên`, `curl /daoanh/api/monk-resolve?name=Thiên+Nhiên` | Trả dữ liệu đúng (không phải nguồn gây bug) | Cả 2 API trả 200 + dữ liệu đúng, xác nhận bug nằm ở renderer không phải API | ✅ (xác nhận không phải lỗi API) |

## 7. Limitation / data gap còn lại

- A007928 (Thiên Nhiên) thực sự không có quan hệ thầy/trò nào trong DB (`lineage-tree` trả 0 cạnh) — đây là tình trạng dữ liệu thật, không phải lỗi; UI "Pháp hệ trống" (`emptyBox`) hiển thị đúng cho trường hợp này. Fix chỉ đảm bảo ô tìm kiếm phụ "Tìm trong pháp hệ" không bị trống một cách vô lý khi node trung tâm chính là kết quả hợp lệ duy nhất.
- Chưa kiểm tra toàn bộ các node khác có 0 cạnh truyền thừa trong DB (có thể còn nhiều node tương tự A007928) — fix áp dụng chung cho mọi trường hợp qua cùng 1 nhánh code nên không cần sửa riêng từng node.
