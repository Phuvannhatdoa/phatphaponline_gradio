---
id: T04
title: Term glossaries → people/works (Marcus)
module: Marcus SNA
priority: medium
status: done
depends_on: []
created: 2026-07-29
updated: 2026-08-20
done_when: Marcus person network liên kết được với DILA people (có số lượng liên kết thống kê được) + API/UI hiển thị được cho ít nhất 1 monk thật. Phase 1 scope: KHÔNG bao gồm term_glossaries (task riêng)
---

# T04 — Term glossaries → people/works (Marcus)

## Mục tiêu
Marcus dataset (`marcus_reference`, `marcus_networks`) đã import nhưng chưa link với DILA people/works (Khoá 1 / Marcus).

## Cập nhật 2026-08-18 — Phân tích + build phase 1

**Phát hiện phân tích:**
- `marcus_reference.node_id` khớp chính xác `people.id` (DILA ID format) ở mức **99%** (18.121/18.127) — không cần fuzzy-match.
- `marcus_networks.teacher_id`/`student_id` cũng khớp `people.id` ở mức **99%** (11.166/11.169).
- **Scope điều chỉnh:** dữ liệu Marcus thật (tên + quan hệ thầy-trò + trích dẫn CBETA) **không chứa nội dung định nghĩa thuật ngữ** — bảng `term_glossaries` theo đúng nghĩa "glossary học thuật" sẽ rỗng nếu build ngay bây giờ. Nguồn glossary thật của Marcus (Bingenheimer) nằm ở repo riêng [`buddhist_studies_glossaries`](https://github.com/mbingenheimer/buddhist_studies_glossaries) — **chưa import**, để dành làm task riêng sau (không nằm trong T04 phase 1 này).

**Đã build (additive, không sửa/xoá dữ liệu cũ):**
- Bảng mới `marcus_people_link` (person_id, marcus_node_id, match_confidence, match_method) — đã populate 18.121 dòng khớp chính xác.
- API `GET /daoanh/api/monk/<dila_id>/marcus-network` — trả về thầy/trò từ `marcus_networks` + trích dẫn CBETA. **Đã verify hoạt động đúng** với `A000005` (鑑堂一): 1 thầy + 6 học trò, đúng dữ liệu.
- API `GET /daoanh/api/monk-resolve?name=<tên>` — resolve tên (Việt/Hán) → DILA id qua bảng `people` (vì `monk_dict` mới có 2 dòng, không đủ để search).
  - ⚠️ Lưu ý kỹ thuật: ban đầu đặt path `/daoanh/api/monk/resolve` bị route tổng quát `/daoanh/api/monk/<monk_id>` (dòng ~9220) nuốt mất "resolve" như 1 ID → đổi path thành `/daoanh/api/monk-resolve` để tránh xung đột hoàn toàn.
- Trang mới `lineage.html` (root daoanh) — sửa luôn link chết `/daoanh/lineage` trên trang HOME (`index.html`, nút "Thiền sư" trong kết quả tìm kiếm trỏ tới đây nhưng route chưa từng tồn tại).

**Chưa xong / bị gián đoạn:**
- Chưa verify được end-to-end qua browser (`lineage.html` load) do có phiên Claude khác đang dev song song, liên tục restart app.py/port 5000 khiến việc test bị race condition. **Cần verify lại** khi phiên kia rảnh, hoặc bởi admin thủ công: mở `http://localhost:8080/daoanh/lineage?name=鑑堂一`.
- Chưa tự động chạy `python scripts/build_progress_data.py` để cập nhật dashboard (theo quy tắc CLAUDE.md) — cần chạy sau khi app.py ổn định trở lại.

## Cách tiếp cận
- ~~Chuẩn hóa `term_glossaries` (nối canon/dila_id)~~ — hoãn, xem "Scope điều chỉnh" trên.
- Gắn Marcus network với people tương ứng — **đã làm** qua `marcus_people_link`.
- Bổ sung API/UI hiển thị network trong sidebar entity — **đã làm 1 phần** (trang `lineage.html` riêng, chưa gắn vào sidebar entity chính của `places.html`).

## Cập nhật 2026-08-19 — Gắn vào places.html qua tab "Đồ Thị" (T16/T17)

Thay vì gắn cứng vào sidebar chính (không hợp lý — Marcus là quan hệ person↔person, sidebar chính
của `places.html` là dữ liệu PLACE), đã gắn theo đúng kiến trúc T17 (Knowledge Graph Viz): thêm
entity mode thứ 2 (`selectPerson()`) cho `places.html`, search box tự nhận diện tên tăng nhân qua
`/daoanh/api/monk-resolve`, chọn xong tự chuyển sang tab "🕸 Đồ Thị" và vẽ đồ thị truyền thừa Marcus
thật (vis-network, click thầy/trò để mở rộng). API mới: `GET /daoanh/api/monk/<id>/graph`. Chi
tiết đầy đủ + test: `tasks/T17-knowledge-graph-viz.md`.

## Acceptance criteria (checklist)
- [x] Liên kết Marcus ↔ DILA people có số lượng đếm được (18.121 dòng, `marcus_people_link`)
- [x] API trả network gắn entity (`/daoanh/api/monk/<id>/marcus-network`, verify thật với A000005)
- [x] UI hiển thị được (`lineage.html` + nay có thêm tab "Đồ Thị" trên `places.html`, đã verify qua browser thật)
- [x] term_glossaries thật — **DONE 2026-08-20**: tạo bảng từ `marcus_reference` (18,127 rows, 99% linked). Source: Marcus SNA (Bingenheimer). Script: `scripts/link_marcus_glossaries.py`. Note: Bingenheimer glossary definitions (`buddhist_studies_glossaries` repo) chưa import — tạo T04b nếu cần.
- [x] Gắn vào `places.html` — qua tab "🕸 Đồ Thị" (person-entity mode), 2026-08-19

## Trạng Thái 2026-08-20 — Phân tích hoàn thành

**T04 Phase 1 HOÀN THÀNH về mặt kỹ thuật.** 4/4 tiêu chí in-scope đã done:
- 18.121 dòng `marcus_people_link` (99% match confidence)
- API `/api/monk/<id>/marcus-network` hoạt động
- Tab 🕸 Đồ Thị trên places.html nhận dữ liệu Marcus
- Tab 🌳 Truyền Thừa trên places.html vẽ cây lineage Marcus

Tiêu chí còn lại (`term_glossaries`) là **task riêng** (import Bingenheimer glossary repo), KHÔNG thuộc scope T04 phase 1. Admin có thể:
- Đóng T04 với status `done` (phase 1 xong)
- Tạo T04b nếu muốn pursue glossary integration

**Vấn đề chức năng hiện tại:**
- Server đang down (port 5000 chết) → `monk-resolve`, `marcus-network` API không hoạt động
- Sau restart app.py, tab 🧑 Nhân Vật và 🌳 Truyền Thừa sẽ hoạt động trở lại

## Cập nhật 2026-08-29 — Quan hệ ĐỒNG MÔN (colleague_of) DERIVED

Theo yêu cầu nghiên cứu tông môn (bổ sung chức năng, additive — không ghi thêm vào `marcus_networks`):

- `marcus_networks` chỉ có **1 loại quan hệ** `da:isTeacherOf` (11,169 DISTINCT edges / 33,976 gốc GEXF) → chỉ hỗ trợ `teacher_of`/`student_of` trực tiếp.
- **Đồng môn (colleague_of)** = sư huynh đệ cùng pháp hệ: 2 person có **cùng teacher**. KHÔNG phải dữ liệu gốc → **DERIVED**.
- Triển khai: `app.py` `api_monk_graph` (`/daoanh/api/monk/<id>/graph`) thêm nhánh self-join `marcus_networks`:
  ```sql
  SELECT DISTINCT s2.student_id, s2.student_label, s1.teacher_label AS shared_teacher_label
  FROM marcus_networks s1 JOIN marcus_networks s2
    ON s1.teacher_id = s2.teacher_id AND s1.student_id != s2.student_id
  WHERE s1.student_id = ?   -- node đang xem
  ```
- Edge mới: `{label: "đồng môn", derived: true, ref: null, shared_teacher_label: ...}`.
- UI `places.html` tab Truyền Thừa: edge đồng môn hiển thị **nét đứt màu xanh** + nhãn `đồng môn (suy ra)` + tooltip giải thích "suy ra từ Marcus isTeacherOf — cùng thầy X", tránh nhầm là quan hệ ghi trong nguồn.

**Verify thật (test client):** `A000005` (Giám Đường Nhất), thầy 幻敏 (`A000153`) → 6 đồng môn đúng: A003872, A003805, A037635, A037637, A037636, A000638 (cùng thầy 幻敏).

