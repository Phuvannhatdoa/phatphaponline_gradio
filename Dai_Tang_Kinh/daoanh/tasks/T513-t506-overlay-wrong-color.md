---
id: T513
title: "Tab Chồng cây (overlay) tô sai màu cạnh — tách từ T506"
status: pending
created: 2026-11-01
updated: 2026-11-01
depends_on: [T506]
done_when: |
  Tab Chồng cây (overlay) trên places.html?mode=lineage&lm=tree tô đúng màu
  cạnh theo nguồn thật của cạnh đó (DILA/MARCUS/TTL/đa nguồn), không còn
  edge_color_token='unknown' sai cho cạnh có nguồn xác định. Kiểm trên
  trình duyệt thật (127.0.0.1, session đăng nhập, force-reload), screenshot
  + network log before/after cho ít nhất 2 ID (A003627, A004980) giống cách
  T506 đã verify cho tab DILA/Marcus. Không đụng tab Cây DILA và Cây Marcus
  (đã sửa xong ở T506, giữ nguyên hành vi).
---

# T513 — Tab Chồng cây (overlay) tô sai màu cạnh

## Bối cảnh — tách từ T506

Trong lúc điều tra T506 ("Tab Cây DILA trộn nguồn Marcus/TTL"), agent
`daoanh-debugger` phát hiện thêm một lỗi khác ở tab **Chồng cây (overlay)**
nhưng KHÔNG tự sửa, vì nằm ngoài yêu cầu gốc của T506 ("tab DILA/Marcus/TTL")
và cần Admin quyết định hướng sửa riêng. Trích nguyên văn phần "Phát hiện
khác" trong `tasks/T506-lineage-tree-dila-tab-source-mixing.md`:

> **Tab Chồng cây (overlay)**: `calculate_edge_color_and_divergence(nbv)`
> vẫn gọi với `nbv` gốc từ `_t426_neighbors_view(..., 'overlay')`, hàng này
> cũng thiếu 3 cột `*_asserted` nên vẫn có thể ra `edge_color_token='unknown'`
> sai cho cạnh overlay (không phải trộn nguồn — overlay vốn đa nguồn theo
> thiết kế — nhưng màu/nhãn "số nguồn" trên cạnh có thể hiển thị sai). KHÔNG
> sửa vì nằm ngoài yêu cầu ("tab DILA/Marcus/TTL") và cần quyết định riêng:
> muốn SELECT thêm cột `GROUP_CONCAT(source_code,',') AS sources` từ
> `v_tree_overlay` rồi parse ra 3 flag mới sửa đúng được — là thay đổi lớn
> hơn, cần Admin duyệt trước.

Admin đã quyết (2026-11-01): tách lỗi này thành task riêng (T513) để không
trộn phạm vi với T506 (T506 giữ nguyên phạm vi gốc: tab DILA/Marcus/TTL).

## Triệu chứng

- Tab **Chồng cây (overlay)** trong `places.html` (`?mode=lineage&lm=tree`,
  chọn tab "Chồng cây"): cạnh có thể hiện màu/nhãn "chưa rõ nguồn"
  (`edge_color_token='unknown'`, nét đứt) dù cạnh đó thực tế có nguồn xác
  định (DILA, Marcus, TTL, hoặc nhiều nguồn đồng thuận).
- Khác với lỗi T506: overlay vốn **thiết kế để đa nguồn** (không phải lỗi
  trộn nguồn sai tầng dữ liệu) — vấn đề chỉ là màu/nhãn hiển thị không khớp
  số nguồn thật của từng cạnh.

## Nguyên nhân nghi ngờ (ghi lại từ điều tra T506, cần daoanh-debugger xác
minh lại độc lập trước khi sửa)

`routes_lineage.py`, nhánh `use_view` khi `view_name='overlay'`: gọi
`calculate_edge_color_and_divergence(nbv)` với `nbv` lấy thẳng từ
`_t426_neighbors_view(conn, ..., 'overlay')` trong `core.py`. Hàng `nbv` này
chỉ có `id, source_badge, agreeing_source_count, is_primary` — thiếu 3 cột
`dila_asserted/marcus_asserted/ttl_asserted` mà hàm
`calculate_edge_color_and_divergence()` cần để tính màu/nét cạnh, nên luôn
rơi về nhánh `n_sources=0` → `edge_color_token='unknown'`.

Hướng sửa gợi ý (từ T506, CHƯA áp dụng, cần Admin/daoanh-debugger đánh giá
lại độ lớn thay đổi trước khi làm): SELECT thêm
`GROUP_CONCAT(source_code, ',') AS sources` từ `v_tree_overlay` (hoặc view
tương đương overlay dùng), parse chuỗi đó thành 3 flag
`dila_asserted/marcus_asserted/ttl_asserted` cho đúng overlay, rồi truyền
vào `calculate_edge_color_and_divergence()` giống cách T506 đã làm cho 3
tab đơn nguồn bằng `_t506_edge_row_for_view(view_name)`.

## Phạm vi

- CHỈ tab Chồng cây (overlay).
- KHÔNG đụng tab Cây DILA, Cây Marcus (đã sửa ở T506, đang chờ QA/Admin
  xác nhận DONE riêng — không sửa lại trong task này).
- KHÔNG đụng tab Cây TTL (T507, task riêng khác).

## Việc cần làm

1. Backup trước khi sửa: `docs/sessions/YYYY-MM-DD/` (file `core.py`,
   `routes_lineage.py` liên quan).
2. Xác minh lại root cause bằng curl/Browser pane thật (không chỉ tin lại
   kết luận của T506 — đọc trực tiếp response `lineage-tree?...&trees=overlay`
   cho A003627/A004980, đối chiếu `edge_color_token` với nguồn thật của
   từng cạnh trong DB).
3. Sửa tối thiểu theo hướng gợi ý ở trên (hoặc hướng khác nếu xác minh ra
   nguyên nhân khác), chỉ trong nhánh `view_name='overlay'`.
4. `python -m py_compile` cho mọi file `.py` đã sửa.
5. Verify bằng click thật (Browser pane, 127.0.0.1, session đăng nhập,
   force-reload): tab Chồng cây cho A003627 và A004980 — screenshot +
   network log trước/sau cho thấy màu/nhãn cạnh khớp đúng nguồn thật.
6. Cập nhật task file này + `docs/tasktodo.md`.

## Ràng buộc

- KHÔNG đánh DONE.
- KHÔNG git commit.
- KHÔNG tự UPDATE DB bằng tay.
- KHÔNG sửa lại code của tab Cây DILA/Marcus đã áp dụng ở T506.

## Báo cáo cần có

1. Root cause xác minh lại độc lập (trích code, dòng, hàm).
2. Fix đã áp dụng (file, before/after).
3. Bằng chứng click thật trước/sau cho cả A003627 và A004980 (screenshot +
   network log).
4. `py_compile`.
5. Task file + tasktodo đã cập nhật.
