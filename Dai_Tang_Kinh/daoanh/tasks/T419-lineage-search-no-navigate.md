---
id: T419
bug_id: BUG-041
title: "Bug verify: BUG-041: Gõ 'Thiên Nhiên' trong ô tìm kiếm lineage không tải cây pháp hệ của Thiên Nhiên"
status: in_progress
created: 2026-10-19
updated: 2026-10-19
owner: daoanh-debugger (audit + sửa) + daoanh-qa (kiểm chứng)
module: Lineage / Nexus search (places.html)
priority: medium
depends_on: [T417]
dispatch: approved (Admin báo bug trực tiếp, kèm kịch bản điều tra chi tiết, 2026-10-19)
plan_approved_at: "2026-10-19 (Admin cung cấp sẵn kịch bản điều tra, không cần duyệt thêm)"
db_write: "Không rõ cần ghi DB hay không — audit trước. Nếu root cause là handler click/navigate (component) thì sửa code trực tiếp (không đổi schema). Nếu root cause là thiếu data trong ancestor-path thì chỉ báo cáo Admin, không tự ghi DB."
done_when: >
  (1) daoanh-debugger audit root cause tại route /daoanh/places?mode=lineage&focus=A007928&lm=tree,
  ô "Tìm trong pháp hệ", theo đúng 1 trong 3 khả năng (A/B/C) nêu trong mô tả bug dưới đây.
  (2) Xác minh bằng dữ liệu thực: gọi API /daoanh/api/monk/search?q=Thiên+Nhiên và
  /daoanh/api/monk/A007928/ancestor-path?root=A001719 để biết Thiên Nhiên có ID nào, có nằm
  trong ancestor-path của A007928 hay không.
  (3) Đọc places.html — _renderLineageSidebar, _fetchAndRenderQuicklist, handler click chip quicklist —
  xác định chip có gọi loadLineageTree() với focus mới không.
  (4) Áp fix nhỏ nhất đúng lớp gây lỗi (không hard-code tên/ID trong component). Nếu root cause là (B)
  (thiếu data) thì KHÔNG tự sửa, chỉ báo cáo cho Admin quyết định.
  (5) Browser-verify thật (feedback_bug_browser_verify): gõ "Thiên Nhiên" vào ô tìm kiếm, click chip
  (nếu có), screenshot before/after, xác nhận cây pháp hệ Thiên Nhiên tải đúng (hoặc nếu không thể do
  thiếu data, chụp bằng chứng API trả về để báo cáo). Network log không có lỗi 4xx/5xx không mong muốn.
  (6) Test regression: case A001719 (Huệ Năng, có cạnh) vẫn hoạt động bình thường sau fix.
  (7) daoanh-qa kiểm chứng độc lập (đọc code + xác nhận bằng chứng, không tự ý claim bằng JS inject).
  (8) Admin xác nhận DONE trước khi đổi status.
revert: "Nếu fix sai hướng: revert file đã sửa từ backup trong docs/sessions/2026-10-19/."
outcome: >
  2026-10-19: Admin báo BUG-041 (tiếp theo BUG-040/T417). Tạo task, backup file liên quan trước khi
  giao daoanh-debugger audit root cause.
  2026-10-19 (daoanh-debugger): Root cause = (A). #lineage-search handler cũ CHỈ gọi
  _renderLineageSidebarHighlight(q) — lọc DOM các <button> đã có sẵn trong #lineage-quicklist
  (chuỗi ancestor-path của node đang xem), không fetch/navigate gì cả (xác nhận bằng network log:
  gõ "Thiên Nhiên" không phát sinh request nào trước khi sửa). Với A007928 quicklist chỉ có 1 chip
  (chính nó, không onclick vì là center) nên gõ tên mình cũng không có gì xảy ra.
  Phụ: /daoanh/api/monk/search dùng bảng monk_dict/monk_name_index KHÔNG chứa A007928 (dataset khác
  với bảng `people` DILA dùng cho cây pháp hệ) — không phải endpoint đúng cho tính năng này. Endpoint
  đúng (đã có sẵn, search trên bảng `people`): /daoanh/api/admin/search_all (dùng chung ô search
  chính của trang) — trả về đúng A007928 + 15 người trùng tên khi query "Thiên Nhiên".
  Fix áp (chưa commit): places.html — thêm div#lineage-search-results (dropdown); input handler
  debounce 250ms gọi /daoanh/api/admin/search_all, lọc cate_internal==='person', render kết quả;
  click kết quả → centerLineageOn(p.id) (hàm fetch+render cây đã dùng chung với chip quicklist) để
  navigate. Không hard-code tên/ID.
  Browser-verify: gõ "Thiên Nhiên" tại A007928 → dropdown 16 kết quả (search_all 200 OK). Click
  A009460 (Đan Hà Thiên Nhiên) → URL đổi focus=A009460, cây Huệ Năng→Hành Tư→Hi Thiên→Thiên Nhiên
  render đầy đủ, đúng. Regression A001719 (Huệ Năng): tree vẫn render bình thường, search cũng fetch
  đúng. Không lỗi 4xx/5xx (chỉ ERR_ABORTED do debounce huỷ request cũ — đúng thiết kế).
  Bằng chứng: docs/sessions/2026-10-19/BUG-041/ (screenshots 01-04, network_log_summary.md).
  Còn chờ: daoanh-qa kiểm độc lập, sau đó Admin xác nhận DONE (chưa tự đổi status, giữ in_progress).
---

# T419 / BUG-041 — Gõ "Thiên Nhiên" không tải cây pháp hệ

## Route/Case

`http://127.0.0.1:8080/daoanh/places?mode=lineage&focus=A007928&lm=tree`
(Luôn dùng 127.0.0.1, không dùng localhost — xem CLAUDE.md.)

## Triệu chứng (Admin báo 2026-10-19)

- Mở URL trên (focus A007928 — node không có cạnh truyền thừa).
- Gõ "Thiên Nhiên" vào ô "Tìm trong pháp hệ" (sidebar trái).
- Expected: tải/hiển thị cây pháp hệ của Thiên Nhiên (navigate sang focus Thiên Nhiên hoặc render cây
  của họ trong viewport).
- Actual: không có kết quả — không tải cây.

## Liên quan BUG-040 / T417

T417 đã fix chip quicklist hiện đúng khi gõ (gọi `_renderLineageSidebar()` trong nhánh no-edge).
BUG-041 là bước tiếp theo: sau khi chip hiện, click chip có navigate sang cây Thiên Nhiên không?

## Root cause cần xác định (1 trong 3 khả năng)

- (A) Chip hiện nhưng click không navigate (handler thiếu hoặc sai trong `places.html`).
- (B) Chip không hiện vì Thiên Nhiên không có trong ancestor-path A007928 → T417 fix chưa đủ phạm vi
  cho case search-to-navigate (chỉ cần báo Admin, không tự sửa).
- (C) Chip hiện + click navigate OK, nhưng cây Thiên Nhiên không render (fetch tree lỗi, hoặc Thiên
  Nhiên cũng no-edge nên không có gì để vẽ).

## Các bước

- [x] RC backup file nghi liên quan (`places.html`) vào `docs/sessions/2026-10-19/` nếu chưa có bản mới nhất
- [x] daoanh-debugger: reproduce qua browser thật + API, xác định root cause (A/B/C) → (A)
- [x] Áp fix nhỏ nhất đúng lớp (nếu A hoặc C); nếu B thì chỉ báo cáo
- [x] Browser-verify: screenshot before/after, network log
- [x] Test regression A001719 (Huệ Năng)
- [ ] daoanh-qa kiểm độc lập
- [ ] Báo Admin, hỏi xác nhận DONE
