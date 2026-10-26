# Audit / Bug Fix Report — BUG-051: /daoanh/places lineage arrows missing

> Task: T438. Lưu tại `docs/BUG-051_PLACES_LINEAGE_ARROWS_REPORT.md`.

## 1. Vị trí audit (thực tế, không đoán)

| Hạng mục | File / Schema / Endpoint thực tế |
|----------|----------------------------------|
| Data source | `GET /daoanh/api/monk/<dila_id>/lineage-tree`, `GET /daoanh/api/ttl/anchor-by-dila` — trả đủ `nodes`/`edges`, không thiếu dữ liệu |
| API endpoint | `/daoanh/api/monk-resolve?name=...` (resolve tên → DILA id), `/daoanh/api/monk/<id>/lineage-tree` |
| Resolver / logic | `places.html` JS: `doSearch()` (~line 1686) → `selectPerson()` → `loadLineageTree()` (~line 6245) → `_renderLineageMode('tree')` → `_renderLineageChain()` (~line 7918) → `_renderHierarchyTree()` (~line 6825, dùng `vis.Network`) |
| Component / renderer | `places.html:745` (`#lineage-inspector` CSS), `places.html:6864-6886` (focus-camera logic sau khi vis.js hierarchical layout dựng cây) |
| Schema contract | Không đổi — bug thuần UI renderer/layout, không chạm data/API |

Route tái hiện: `http://127.0.0.1:8080/daoanh/places`, search "Nghĩa Huyền" (DILA `A003627`), tương tự "Mã Tổ Đạo Nhất" (DILA `A038890`).

## 2. Root cause (đã xác minh)

- **Lớp gây lỗi:** `renderer | layout` (2 nguyên nhân độc lập, cả hai đều ở tầng CSS/JS của `places.html`, không phải data/API).

**Nguyên nhân A — CSS layout (chính, luôn xảy ra):**
`#lineage-inspector` (panel "Chi tiết" bên phải) khai báo `flex:0 0 300px` nhưng KHÔNG có `min-width:0`. Mặc định CSS flexbox cho flex item `min-width:auto`, nghĩa là nội dung không ngắt dòng được (bio DILA dài, URL CBETA/Wikipedia không khoảng trắng) đẩy panel giãn rộng hơn flex-basis khai báo. Đo thực tế: panel giãn từ 300px lên **437px**, khiến `#lineage-canvas` (flex:1, min-width:0 — nơi vis.Network vẽ cây) bị bóp còn **172px × 430px**. vis.Network vẫn khởi tạo và có đủ 80 nodes/79 edges, nhưng canvas quá nhỏ nên tree hiển thị như một ô đen trống (giống đúng mô tả bug "nền đen, trống").

Minh chứng (JS console, trước fix):
```
inspector computed width: 437.48px (flex-basis khai báo: 300px)
canvas (vis.Network container) width: 172.5px, height: 430px
canvas pixel tại tâm: rgba(0,0,0,0) — không vẽ được gì
```

**Nguyên nhân B — race condition + camera lệch (phụ, chỉ lộ rõ với cây lớn như Nghĩa Huyền có >50 đời tổ sư merge từ T152):**
Trong `_renderHierarchyTree()`, sau khi `new vis.Network(...)` dựng xong, code chờ sự kiện `afterDrawing` lần 2 để gọi `_lineageNetwork.focus(center, {scale:0.8})` — nhưng `_lineageNetwork` (biến module-level) chỉ được gán **sau đó** ở dòng `_lineageNetwork = network;` (line ~7118). Nếu `afterDrawing` bắn trước khi dòng gán này chạy, `_lineageNetwork` vẫn là `null`/instance cũ → `focus()` không chạy → camera đứng yên ở vị trí mặc định không khớp vị trí node thật (đo thực tế: camera tại `x=4920` trong khi node trung tâm ở `x=0`). Ngoài ra vis.js hierarchical layout (`blockShifting`/`edgeMinimization`) có thể dịch tiếp vị trí node sau lần `afterDrawing` dùng để focus, khiến ngay cả khi focus() chạy đúng lần đầu, camera vẫn lệch khỏi node sau khi layout ổn định hoàn toàn (xảy ra rõ nhất khi `_lineageMergeAncestorSpine()` (T152) nạp thêm chuỗi tổ sư và kích hoạt re-render).

## 3. Data/API contract trước → sau

Không đổi — đây là bug render/layout thuần UI. API trả 200 OK với đủ `nodes`/`edges` ở cả trước và sau khi sửa.

| | Trước | Sau |
|--|-------|-----|
| `#lineage-inspector` computed width | 437px (giãn, vượt flex-basis 300px) | 300px (đúng flex-basis) |
| `#lineage-canvas` computed width | 172px | 310px (chiếm phần còn lại đúng tỉ lệ) |
| Camera vis.Network sau khi cây dựng xong | lệch khỏi node trung tâm (đen/trống) | focus đúng node trung tâm, re-confirm sau 150ms khi layout ổn định |

## 4. Files changed

- `Dai_Tang_Kinh/daoanh/places.html`
  - Line 745: thêm `min-width:0;max-width:300px;overflow-x:hidden` cho `#lineage-inspector` — ngăn nội dung dài (bio/URL) đẩy panel giãn quá flex-basis, trả lại không gian đúng cho canvas cây truyền thừa.
  - Line ~6871-6886: sửa 2 chỗ gọi `_lineageNetwork.focus(...)` → dùng closure `network` (instance vừa tạo, luôn đúng) thay vì biến module-level `_lineageNetwork` (có thể chưa kịp gán do race condition); thêm `setTimeout(..., 150)` focus lại một lần sau khi vis.js hierarchical layout (blockShifting/edgeMinimization) chắc chắn đã ổn định, chỉ áp dụng nếu network đó vẫn còn là cây đang hiển thị (`_lineageNetwork === network`).

## 5. Migration / import / dry-run / rollback (nếu chạm DB)

- Không chạm DB/data — chỉ sửa file tĩnh `places.html` (CSS inline + JS). Không cần migration/dry-run.
- Backup trước khi sửa: `docs/sessions/2026-10-20/BUG-051/places.html.bak-20261020_182252`
- Revert: khôi phục từ file backup trên, hoặc `git checkout -- Dai_Tang_Kinh/daoanh/places.html` (chưa commit).

## 6. Test cases & kết quả

| Case | Input | Expected | Actual | PASS/FAIL |
|------|-------|----------|--------|-----------|
| Case yêu cầu | Search "Nghĩa Huyền" trên `/daoanh/places`, tab Truyền Thừa → Cây DILA | Hiện cây với mũi tên teacher→student (Hi Vận → Nghĩa Huyền), không nền đen | Hiện đúng: "Hi Vận" → mũi tên trắng → "Nghĩa Huyền", cả ở view mặc định lẫn sau khi ancestor-spine (T152) merge xong (6-9s) | ✅ |
| Fallback — monk khác | Search "Mã Tổ Đạo Nhất" (DILA `A038890`) | Hiện cây với mũi tên, không đen | Hiện đúng: "Thiên Chân Tự Tính" → mũi tên xanh → "Mã Tổ Đạo Nhất" | ✅ |
| Regression — "Phả hệ mở rộng" (network mode) | Click tab "Phả hệ mở rộng" cho Mã Tổ Đạo Nhất | Vẫn hiện cây + mũi tên, inspector không đè canvas | Hiện đúng, canvas rộng, inspector 300px cố định, không đen | ✅ |
| Console/Network | Theo dõi trong lúc search + render | Không lỗi JS mới phát sinh | Chỉ có warning "running a development build" (không liên quan), không lỗi | ✅ |

## 7. Limitation / data gap còn lại

- Nguyên nhân B (race condition `_lineageNetwork` + hierarchical layout dịch chuyển tiếp) được vá bằng safety re-focus 150ms thay vì tái cấu trúc toàn bộ cơ chế focus — đây là fix nhỏ nhất xử lý đúng triệu chứng quan sát được; nếu sau này thấy camera vẫn lệch với cây cực lớn (>100 nodes) hoặc máy chậm hơn 150ms để layout ổn định, có thể cần thay bằng cơ chế chờ `stabilizationIterationsDone` hoặc double-rAF thay vì timeout cố định.
- Không regression nào phát hiện ở Events/Nexus/các tab khác trong phạm vi test (chưa test toàn bộ 131+ routes, chỉ test tab Truyền Thừa + 2 case monk theo đúng phạm vi task).
