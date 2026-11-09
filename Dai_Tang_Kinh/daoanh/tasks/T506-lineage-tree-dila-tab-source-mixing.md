---
id: T506
title: "Tab Cây DILA (lineage-tree) trộn nguồn Marcus/TTL"
status: in_progress
owner: daoanh-debugger
created: 2026-10-31
updated: 2026-10-31
---

# T506 — Tab Cây DILA (lineage-tree) trộn nguồn Marcus/TTL

**Trạng thái:** 🔧 FIX APPLIED (2026-10-31) — chờ QA/Admin xác nhận qua UI thật trước khi đánh DONE.

## Kết quả điều tra + fix (2026-10-31)

### Root cause (backend, 2 lớp — không phải JOIN cạnh cây, mà metadata gắn vào cạnh)

1. **`_t138_edge_assertions(conn, subject_id, object_id)`** trong `core.py` (2 bản định nghĩa trùng
   nhau, dòng ~3778 và ~9035 — chỉ bản sau cùng có hiệu lực do Python module-level override) được
   gọi trong nhánh `use_view` của `api_monk_lineage_tree` (`routes_lineage.py` dòng ~661-745, cả
   2 vòng BFS lên/xuống) **KHÔNG filter theo `source_code`**. Dù cạnh BFS đến từ `v_tree_dila`
   (view đã filter `WHERE source_code='DILA'`), hàm vẫn `SELECT ... FROM lineage_edge_assertions
   WHERE subject_person_id=? AND object_person_id=?` không điều kiện nguồn → trả về `sources`
   gồm cả MARCUS/TTL nếu các nguồn đó cũng có assertion cho đúng cặp (subject,object) đó.
   **Verify bằng curl trực tiếp trước fix:**
   `GET /daoanh/api/monk/A003627/lineage-tree?trees=dila` → `source: "VIEW T425: dila"` nhưng
   edge `A003627->A004980` có `sources: [{"source_code":"DILA"},{"source_code":"MARCUS"},
   {"source_code":"TTL"}]`.
   Field `edge.sources` chảy thẳng vào JS `_renderLineageInspectorEdge()` (`places.html` ~8688-8757)
   → panel "NGUỒN & CHỨNG CỨ" hiện dòng "✓ Marcus" dù đang xem tab Cây DILA.

2. **`calculate_edge_color_and_divergence(nbv)`** (gọi tại routes_lineage.py ~678, ~724) nhận
   `nbv` — là 1 hàng từ `_t426_neighbors_view()` cho view đơn nguồn, hàng này CHỈ có
   `id, source_badge, agreeing_source_count, is_primary` — KHÔNG có 3 cột
   `dila_asserted/marcus_asserted/ttl_asserted` mà `calculate_edge_color_and_divergence` cần.
   Kết quả: `dila_v=marc_v=ttl_v=False` luôn → `n_sources=0`, `edge_color_token='unknown'`,
   `dashed=True` cho **MỌI** cạnh ở cả 3 tab đơn nguồn — không phải trộn nguồn, nhưng sai nhãn
   (cạnh DILA thật lại hiện "chưa rõ nguồn", nét đứt).

3. **Frontend `_t275ApplyTtl(ds)`** (`places.html` ~6836-6860) được gọi **không điều kiện** ở cả
   2 nơi render cây (`_renderHierarchyTree` dòng ~8290, `_renderLineageNetwork` dòng ~8488) —
   fetch `/daoanh/api/ttl/anchor-by-dila` và gắn `"TTL <gen>"` / `"TTL ?"` vào label + tooltip của
   **MỌI node**, kể cả nút trung tâm, bất kể tab nào đang active (`window._currentTreeSource`
   không được đọc trong hàm này trước fix). Đây là nguyên nhân trực tiếp của bug
   **"Nút trung tâm hiện 'TTL ?'"** khi đang ở tab Cây DILA.

### "Số đệ tử 24 không khớp tổng 2 nhánh trực hệ" — ĐÃ KIỂM, KHÔNG phải bug

Build lại cây từ response `trees=dila` của A003627 (Python, BFS trên `edges` trả về từ API):
`direct kids of center = 24` (danh sách đủ 24 DILA ID), tổng hậu duệ BFS = 49 — khớp hoàn toàn với
con số UI hiển thị ("24 đệ tử trực tiếp"). Nghĩa Huyền (Lâm Tế) thực sự có 24 đệ tử trực tiếp được
ghi nhận trong DILA. "2 nhánh trực hệ" nhiều khả năng là Admin đếm nhầm trên UI (có thể nhầm với
2 dòng truyền thừa hiển thị ở sidebar "Truyền Thừa Thiền Tông"/"Truyền Thừa Lâm Tế Tông"), không
liên quan đến trộn nguồn Marcus/TTL. Không có fix nào áp dụng cho mục này.

### Fix đã áp dụng

Backup trước sửa: `docs/sessions/2026-10-31/core.pre-T506.py`,
`docs/sessions/2026-10-31/routes_lineage.pre-T506.py`,
`docs/sessions/2026-10-31/places.pre-T506.html`.

1. **`core.py`** — `_t138_edge_assertions()` (cả 2 bản trùng) thêm tham số `source_code=None`.
   Mặc định `None` giữ nguyên hành vi cũ (dùng cho consensus mặc định, `ancestor-spine` — nơi
   trộn nguồn là ĐÚNG thiết kế). Khi có `source_code`, thêm `AND source_code=?` vào cả 3 query
   (forward, reversed, rejected-check).
2. **`core.py`** — thêm hàm mới `_t506_edge_row_for_view(view_name)`: trả `{dila_asserted,
   marcus_asserted, ttl_asserted}` đúng theo `view_name` (chỉ dùng cho view đơn nguồn).
3. **`routes_lineage.py`** — nhánh `use_view` (BFS lên + xuống, 2 chỗ): truyền
   `source_code=view_name.upper()` vào `_t138_edge_assertions()` khi `view_name in ('dila',
   'marcus', 'ttl')` (overlay giữ `source_code=None`, không đổi); dùng
   `_t506_edge_row_for_view(view_name)` thay cho `nbv` thô khi gọi
   `calculate_edge_color_and_divergence()` (trừ overlay, giữ `nbv` gốc — pre-existing bug ở
   overlay KHÔNG sửa, xem mục "Phát hiện khác" bên dưới).
4. **`places.html`** — `_t275ApplyTtl(ds)` thêm guard đầu hàm: chỉ chạy khi
   `window._currentTreeSource` là `'ttl'` hoặc `'overlay'`; mặc định `'dila'` khi biến chưa
   khởi tạo (khớp nút active sẵn trong HTML tĩnh).

### Verify (Browser pane thật, session đăng nhập, force-reload để không dính cache JS cũ)

- **A003627** (Nghĩa Huyền), tab Cây DILA: center node "Nghĩa Huyền ★ / 義玄" — KHÔNG còn dòng
  "TTL ?". `GET lineage-tree?up=2&down=2&trees=dila` (qua `fetch()` trong chính trang, same-origin)
  trả `source: "VIEW T425: dila"`, mẫu edge đầu `sources: ["DILA"]`, `edge_color_token: "dila"`.
  `window._currentTreeSource === "dila"`. KHÔNG có request `anchor-by-dila` nào trong network log
  sau khi tab DILA được load lại (chỉ còn các request cũ từ lần tải trang TRƯỚC khi fix, trong
  cùng lịch sử network log của tab).
- **A004980** (Hưng Hóa Tồn Tưởng), tab Cây DILA: center node "Hưng Hóa Tồn Tưởng ★" — KHÔNG còn
  "TTL ?". Cùng kết quả network log (không có `anchor-by-dila` mới).
- **Tab Cây Marcus** (A004980): cây vẽ lại với cạnh màu vàng (Marcus), center node cũng KHÔNG có
  badge TTL — xác nhận guard hoạt động đúng cho cả 2 tab đơn nguồn, không chỉ DILA.
- `python -m py_compile core.py routes_lineage.py app.py` → OK.
- App server (port 5000) đã restart (`taskkill` PID cũ + chạy lại `python -X utf8 app.py`) để nạp
  code mới; log sau restart toàn 200, không lỗi.

### Phát hiện khác — BÁO ADMIN, KHÔNG tự sửa

- **Tab Chồng cây (overlay)**: `calculate_edge_color_and_divergence(nbv)` vẫn gọi với `nbv` gốc từ
  `_t426_neighbors_view(..., 'overlay')`, hàng này cũng thiếu 3 cột `*_asserted` nên vẫn có thể ra
  `edge_color_token='unknown'` sai cho cạnh overlay (không phải trộn nguồn — overlay vốn đa nguồn
  theo thiết kế — nhưng màu/nhãn "số nguồn" trên cạnh có thể hiển thị sai). KHÔNG sửa vì nằm ngoài
  yêu cầu ("tab DILA/Marcus/TTL") và cần quyết định riêng: muốn SELECT thêm cột
  `GROUP_CONCAT(source_code,',') AS sources` từ `v_tree_overlay` rồi parse ra 3 flag mới sửa đúng
  được — là thay đổi lớn hơn, cần Admin duyệt trước.

---

## Bối cảnh / Bug Admin báo (2026-10-31)

Trang `places.html?mode=lineage&focus=A003627&lm=tree` (ví dụ Nghĩa Huyền) có 3 tab nguồn: Cây DILA, Cây Marcus, Cây TTL.
Khi đang ở tab **Cây DILA**, cây vẫn lấy/trộn dữ liệu từ Marcus và TTL. Triệu chứng Admin thấy:

- Nút trung tâm hiện **"TTL ?"** (trong khi tab đang chọn là DILA).
- Hộp chọn nhánh hiện đệ tử **"chưa có nguồn"**.
- Số đệ tử hiển thị (ví dụ 24) không khớp tổng 2 nhánh trực hệ.

## Yêu cầu nghiệp vụ

- Tab **Cây DILA** CHỈ dùng dữ liệu DILA để vẽ cây: quan hệ thầy-trò, đệ tử, đời (generation), tên hiển thị, cạnh (edges), nhãn nguồn — không JOIN/UNION/fallback sang Marcus hoặc TTL, kể cả để bổ sung cạnh thiếu, đời thiếu, hay phục vụ chọn nhánh.
- Tương tự: tab Marcus chỉ Marcus, tab TTL chỉ TTL.
- **CHỈ sửa tab Marcus/TTL nếu phát hiện chúng cũng bị trộn nguồn tương tự — và phải báo Admin TRƯỚC, không tự sửa.** Đây có thể cần quyết định riêng của Admin.

## Phạm vi điều tra bắt buộc

1. `routes_lineage.py` route `/daoanh/api/monk/<dila_id>/lineage-tree` (~dòng 600): tham số chọn nguồn (`?source=dila`?), có JOIN/UNION/fallback sang Marcus/TTL ở nhánh nào không (tên, đệ tử, tổng đếm).
2. JS vẽ cây trong `places.html` (render lineage tree, "Mở 1 đời tiếp", "Chọn nhánh trực hệ", nút trung tâm): có tự gọi API Marcus/TTL khi tab DILA active không; có biến/cache dùng chung giữa 3 tab (ví dụ `currentTreeData`) bị tab khác ghi đè không.
3. Browser pane thật (session đã đăng nhập), route `http://127.0.0.1:8080/daoanh/places.html?mode=lineage&focus=A003627&lm=tree`, tab Cây DILA: đọc network log khi load trang, bấm "Mở 1 đời tiếp", bấm "Chọn nhánh trực hệ" — xác nhận request/response nào chứa field/giá trị gốc Marcus/TTL (ví dụ `source:"ttl"`). Screenshot bằng chứng lỗi ban đầu ("TTL ?", "chưa có nguồn").
4. Xác định root cause: backend trộn nguồn SQL, client lẫn biến/cache giữa tab, hoặc cả hai.
5. Backup trước khi sửa: `docs/sessions/2026-10-31/` (dùng suffix mới nếu đã có backup từ phiên trước, không đè).
6. Sửa tối thiểu: lọc rõ nguồn trong SQL (`WHERE source='dila'` hoặc tương đương, không JOIN/fallback bảng khác), và/hoặc sửa JS tránh cache chung giữa tab, đảm bảo đổi tab gọi lại API đúng nguồn, không giữ dữ liệu tab cũ.
7. `python -m py_compile` cho mọi `.py` đã sửa.
8. Verify bằng click thật: tab Cây DILA cho CẢ A003627 và A004980 — screenshot + network log cho thấy nút trung tâm không còn "TTL ?", hộp chọn nhánh không còn "chưa có nguồn", số đệ tử khớp tổng nhánh hiển thị; response lineage-tree khi tab DILA active không có field/giá trị gốc Marcus/TTL.
9. Nếu phát hiện tab Marcus/TTL cũng bị trộn nguồn tương tự: KHÔNG tự sửa — ghi rõ vào báo cáo + task file này, chờ Admin quyết định.
10. Cập nhật task file này + `docs/tasktodo.md` với toàn bộ root cause, fix, bằng chứng.

## Ràng buộc

- KHÔNG đánh DONE.
- KHÔNG git commit.
- KHÔNG tự UPDATE DB bằng tay.

## Báo cáo cần có

1. Root cause xác định (trích code cụ thể: dòng, hàm, nhánh nào trộn nguồn).
2. Fix đã áp dụng (file, before/after).
3. Bằng chứng click thật trước/sau cho cả 2 ID (screenshot + network log).
4. Phát hiện về tab Marcus/TTL nếu có vấn đề tương tự (chỉ báo, không tự sửa).
5. `py_compile`.
6. Task file + tasktodo đã cập nhật.
