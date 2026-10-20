---
id: T417
bug_id: BUG-040
title: "Bug verify: BUG-040: Search box 'Tìm trong pháp hệ' không hiển thị quicklist khi gõ ký tự tìm kiếm trong lineage mode"
status: in_progress
created: 2026-10-19
updated: 2026-10-19
owner: daoanh-debugger (sửa) + daoanh-qa (kiểm chứng)
module: Lineage / Nexus search (places.html)
priority: medium
depends_on: []
dispatch: approved (Admin yêu cầu trực tiếp "Go!" kèm bước test chi tiết, 2026-10-19)
plan_approved_at: "2026-10-19 (Admin cung cấp sẵn kịch bản browser-verify, không cần duyệt thêm)"
db_write: "Không rõ cần ghi DB hay không — audit trước; nếu root cause là data/mapping thì chờ Admin duyệt ghi DB, nếu là resolver/renderer thì sửa code trực tiếp (không đổi schema)."
done_when: >
  (1) daoanh-debugger audit root cause theo lớp: raw data → DB → API → resolver → component → UI state,
  tại route /daoanh/places?mode=lineage&focus=A007928&lm=tree, ô "Tìm trong pháp hệ".
  (2) Xác định vì sao quicklist rỗng khi gõ "T" → "h" → "i" (ví dụ kỳ vọng thấy "Thiên Nhiên").
  (3) Áp fix nhỏ nhất đúng lớp gây lỗi (không hard-code tên trong component).
  (4) Browser-verify thật theo feedback_bug_browser_verify: screenshot BEFORE (quicklist rỗng) và AFTER (chip xuất hiện),
  gõ lại "T"→"h"→"i" để xác nhận chip còn khi filter tiếp; test case "xyz_no_match" (chip phải ẩn đúng); test
  regression case khác (A001719) không bị ảnh hưởng; network log không có lỗi.
  (5) daoanh-qa kiểm chứng độc lập (đọc code + xác nhận bằng chứng QA, không tự ý claim bằng JS inject).
  (6) Admin xác nhận DONE trước khi đổi status.
revert: "Nếu fix sai hướng: revert file đã sửa từ backup trong docs/sessions/2026-10-19/."
outcome: >
  2026-10-19: Admin yêu cầu browser-verify trực tiếp (BUG-040). Tạo task, backup file liên quan trước khi giao
  daoanh-debugger audit + fix + verify.

  2026-10-19 (audit + browser-verify): Root cause xác nhận đúng như comment fix đã áp trong places.html
  (~dòng 6240-6256): trong loadLineageTree(), nhánh xử lý khi d.edges rỗng (node không có cạnh truyền thừa
  trong lineage-tree, ví dụ A007928 Thiên Nhiên) return sớm mà KHÔNG gọi _renderLineageSidebar() →
  #lineage-quicklist không bao giờ được render (không fetch ancestor-path, không có <button> nào) →
  input filter _renderLineageSidebarHighlight() (dòng ~8669) chỉ toggle display trên các button có sẵn
  trong quicklist nên luôn "rỗng" dù gõ gì, vì danh sách nguồn (DOM) trống từ đầu — đây là bug tầng
  renderer/component (không phải data/API: /daoanh/api/monk/<id>/ancestor-path vẫn trả 200 OK có dữ liệu).
  Fix đã áp (thêm lời gọi _renderLineageSidebar() trước return sớm) đúng lớp gây lỗi, không hard-code data.

  Browser-verify thật (Chrome pane, click/type UI, không JS inject):
  - Route A007928 (no-edge): quicklist ban đầu hiện 1 chip "Thiên Nhiên" (từ ancestor-path fetch).
    Gõ "T" → chip còn. Gõ "Thi" → chip còn (PASS). Gõ "xyz_no_match" → chip ẩn đúng (PASS not-found).
  - Route A001719 (Huệ Năng, có cạnh — regression case): gõ "Huệ" → chip "Huệ Năng" hiện đúng, quicklist
    hoạt động bình thường, không bị ảnh hưởng bởi fix (PASS, không regression).
  - Network log (read_network_requests) cho cả 2 route: toàn bộ request 200 OK, không có 4xx/5xx.
  - Evidence lưu tại docs/sessions/2026-10-19/BUG-040/ (7 screenshot + network_log_summary.md).

  Đã cập nhật docs/bugs.md (mục BUG-040) và docs/tasktodo.md (block T417). Status giữ in_progress — chờ
  daoanh-qa kiểm độc lập và Admin xác nhận DONE, KHÔNG tự đổi status.
---

# T417 / BUG-040 — Quicklist tìm kiếm trong pháp hệ rỗng khi gõ ký tự

## Route/Case

`/daoanh/places?mode=lineage&focus=A007928&lm=tree`

Ô "Tìm trong pháp hệ" (search box trong lineage mode).

## Triệu chứng (Admin báo)

- Trước fix: quicklist rỗng khi gõ "T" → "h" → "i" dù kỳ vọng có gợi ý (ví dụ "Thiên Nhiên").
- Sau khi áp fix dự kiến ở `places.html`: quicklist phải hiện chip đúng và giữ khi filter tiếp.
- Case "xyz_no_match" phải ẩn chip (not-found hoạt động đúng).
- Case khác có cạnh (A001719) không được regression.

## Phạm vi

Audit trước (không đoán file/API). Khả năng liên quan: dữ liệu quicklist nguồn từ API nào (ancestor-spine / lineage-tree
node list?), logic filter phía client trong `places.html`, và liệu A007928 có đủ node liên quan trong DB để quicklist
hiển thị.

## Các bước

- [x] RC tạo task, backup file nghi liên quan vào `docs/sessions/2026-10-19/`
- [x] daoanh-debugger: reproduce qua API/DB, xác định root cause (renderer — `loadLineageTree()` return sớm bỏ qua `_renderLineageSidebar()` khi no-edge)
- [x] Áp fix nhỏ nhất (đã áp sẵn từ phiên trước, xác nhận đúng lớp — không sửa thêm)
- [x] Browser-verify: screenshot before/after, network log, 3 test case trên (PASS cả 3, xem `docs/sessions/2026-10-19/BUG-040/`)
- [ ] daoanh-qa kiểm độc lập
- [ ] Báo Admin, hỏi xác nhận DONE
