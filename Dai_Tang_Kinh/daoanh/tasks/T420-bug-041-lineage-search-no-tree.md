---
id: T420
title: "[TRÙNG T419] BUG-041 — Gõ 'Thiên Nhiên' trong ô tìm kiếm lineage không tải cây pháp hệ"
status: deferred
duplicate_of: T419
dispatch: null
created: 2026-10-19
updated: 2026-10-19
done_when: "Gõ 'Thiên Nhiên' trong ô tìm lineage tại focus=A007928 dẫn tới cây pháp hệ của Thiên Nhiên hiện đúng (click chip hoặc kết quả search điều hướng/tải tree); không regression case A001719/Huệ Năng; QA xác nhận."
outcome: "2026-10-19 07:40: Admin \"rename cái trùng\" — task trùng hẳn T419 (cùng BUG-041), hoãn; mọi việc làm ở T419. Không xoá file."
---

## Triệu chứng

URL tái hiện: `http://127.0.0.1:8080/daoanh/places?mode=lineage&focus=A007928&lm=tree`
Thao tác: gõ "Thiên Nhiên" vào ô "Tìm trong pháp hệ".
Expected: tải và hiển thị cây pháp hệ của Thiên Nhiên (navigate sang focus Thiên Nhiên hoặc render cây của họ).
Actual: không có kết quả / không tải cây pháp hệ của Thiên Nhiên.

## Liên quan

BUG-040 đã fix chip quicklist hiện đúng (`_renderLineageSidebar()` gọi trước return sớm trong nhánh no-edge, places.html ~dòng 6248-6256). Nhưng click chip "Thiên Nhiên" hoặc kết quả tìm kiếm không dẫn tới cây của Thiên Nhiên.

## Nguyên nhân nghi ngờ (chưa xác minh)

- (A) Chip hiện nhưng click không navigate đúng — handler click chip gọi sai hàm hoặc sai param.
- (B) Thiên Nhiên không có trong ancestor-path của A007928 (root=A001719) — cần curl API kiểm tra.
- (C) Chip hiện + click navigate OK nhưng fetch tree cho ID mới không chạy/lỗi.

## Phạm vi điều tra

- `GET /daoanh/api/monk/A007928/ancestor-path?root=A001719`
- `GET /daoanh/api/search_monk?q=Thiên+Nhiên`
- `daoanh/places.html`: `_fetchAndRenderQuicklist`, `_renderLineageSidebarHighlight`, handler click chip (`loadLineageTree`/`centerLineageOn`/`selectPerson` — xác định hàm thực tế được gọi).

## Phạm vi dự kiến

Chỉ sửa lớp đúng theo root cause tìm được (UI handler / resolver / API), không hard-code data, không sửa raw DILA/Marcus/CBETA/TTL.

## Vòng 2 — QA báo CHƯA ĐẠT (2026-10-19)

**Lỗi còn lại:** Tại `focus=A007928&lm=tree`, gõ "Thiên Nhiên" → click kết quả A009460 (Đan Hà Thiên Nhiên) → sidebar/header/inspector đổi đúng nhưng cây vis.js KHÔNG hiện trên canvas. Bằng chứng QA: `docs/sessions/2026-10-19/BUG-041/03_after_click_navigated_A009460.jpg` — không có cột canvas, dòng "Chưa tìm thấy quan hệ truyền thừa Marcus..." vẫn hiện.

**Root cause QA xác định:** `centerLineageOn` trong `daoanh/places.html` (~dòng 6484-6515) fetch `/api/monk/{pid}/lineage-tree`, cập nhật `_lineageState.edges`, nhưng không set lại `#lineage-canvas` display='block' hoặc ẩn `#lineage-empty`. `loadLineageTree` (nhánh no-edge, ~dòng 6247-6249) có logic ẩn canvas/hiện empty khi edges rỗng, nhưng không có nhánh ngược (có edge → hiện canvas, ẩn empty) được gọi từ `centerLineageOn`. Nếu canvas đang ở trạng thái ẩn từ lần focus trước (A007928 không có cạnh), nó vẫn ẩn sau khi `centerLineageOn` load xong dữ liệu có cạnh của A009460.

**Yêu cầu sửa vòng 2:**
- Sửa `centerLineageOn` (hoặc điểm dùng chung) để: edges.length > 0 → ẩn `#lineage-empty`, hiện `#lineage-canvas` TRƯỚC khi render; edges.length === 0 → giữ hành vi hiện tại (hiện empty, ẩn canvas).
- Xác nhận fix áp dụng luôn cho chip quicklist (`_fetchAndRenderQuicklist`, ~6452/6479) vì dùng chung `centerLineageOn`.
- Test 3 case: (a) A007928 → search "Thiên Nhiên" → click A009460 → cây phải hiện; (b) A009460 (có cây) → search sang A007928 (không cạnh) → phải hiện đúng thông báo trống, không sót cây cũ; (c) regression A001719 → "Huệ" → chip "Huệ Năng" → cây vẫn hiện đúng.
- Screenshot 3 case lưu `docs/sessions/2026-10-19/BUG-041/` (tên mới, không ghi đè ảnh cũ).

## Vòng 2 — Đã sửa (2026-10-19, daoanh-debugger)

**Fix:** thêm hàm dùng chung `_lineageSyncCanvasVisibility(edges)` (places.html ~dòng 6208-6222)
và gọi trong `centerLineageOn()` (~dòng 6531) ngay sau khi cập nhật `st.edges`, trước
`_renderLineageMode()` — đồng bộ hiện/ẩn `#lineage-canvas`/`#lineage-empty` theo số cạnh của
tâm mới. Áp dụng chung cho cả click kết quả search và click chip quicklist (cùng gọi
`centerLineageOn`).

**node --check:** 2 khối script tách ra, cả 2 pass (exit 0).

**Browser-verify 3 case:** (a) A007928→search→click A009460 → cây hiện đúng; (b) A009460→search→
click A007928 → hiện đúng thông báo trống, không sót cây cũ; (c) regression A001719→"Huệ"→
"Huệ Năng" → không đổi. Screenshot: `docs/sessions/2026-10-19/BUG-041/r2_*.jpg`. Network log:
`docs/sessions/2026-10-19/BUG-041/r2_network_log_summary.md`. Không có lỗi 4xx/5xx.

**Trạng thái:** RC đã browser-verify vòng 2, chờ daoanh-qa kiểm độc lập rồi Admin xác nhận DONE.
Chi tiết đầy đủ đã cập nhật vào `docs/bugs.md` mục BUG-041 (dòng ~636 trở xuống).

## QA vòng 2 (2026-10-19, daoanh-qa)

**Kết quả:** ĐẠT trên phần kiểm độc lập được (code thật, cú pháp node --check, dữ liệu API gọi
trực tiếp, so khớp ảnh debugger với ảnh lỗi cũ). KHÔNG KIỂM ĐƯỢC phần click UI thật — agent
daoanh-qa không có công cụ điều khiển browser, chỉ đọc code + gọi API + xem ảnh debugger để lại.

Xác nhận: `_lineageSyncCanvasVisibility` (places.html dòng 6212-6223) được gọi đúng vị trí trong
`centerLineageOn` (dòng 6531, trước `_renderLineageMode`); `loadLineageTree` không bị ảnh hưởng
(vẫn tự ẩn/hiện riêng, không gọi hàm mới — QA ghi chú nhỏ: comment dòng 6210 nói dùng chung với
`loadLineageTree` nhưng thực tế chưa gọi, không chặn task, có thể sửa comment sau); API
lineage-tree cho cả 3 ID trả đúng số cạnh kỳ vọng (A007928=0 cạnh, A009460=17 cạnh, A001719=99
cạnh); ảnh `r2_a_tree_rendered_A009460.jpg` cho thấy khác biệt rõ với ảnh lỗi cũ
`03_after_click_navigated_A009460.jpg`.

**Trạng thái:** Chờ Admin tự click 3 kịch bản trên browser (khuyến nghị mở DevTools Network để
có log gốc) rồi xác nhận DONE. Không tự đánh DONE.
