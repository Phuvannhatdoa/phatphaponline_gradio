# 2026-08-18 — T04: Marcus → DILA people link (phase 1)

## Mô tả ngắn task

T04 — "Term glossaries → people/works (Marcus)": phân tích và tích hợp Marcus dataset (`marcus_reference`, `marcus_networks`) vào hệ thống DILA, không ghi đè dữ liệu, không phá hệ thống hiện tại. Yêu cầu: đảm bảo có thể lưu logs/git commit/update task md, đảm bảo mọi thay đổi có thể rollback thuận tiện.

## Phân tích

- `marcus_reference` (18.127 dòng): cột `node_id, label, label_vi, birth_year, death_year, created_at`.
- `marcus_networks` (11.169 dòng): cột `id, teacher_id, student_id, relation_type, teacher_label, student_label, source_data, ref, created_at`.
- **Phát hiện chính:** `node_id`/`teacher_id`/`student_id` đã dùng thẳng định dạng ID DILA (`A000005`...), khớp chính xác `people.id` ở mức **99%** (không cần fuzzy-match như CBDB).
- Bảng `networks` (bảng hợp nhất cuối, dự kiến chứa quan hệ) xác nhận **0 dòng** — dữ liệu Marcus có sẵn nhưng chưa từng được surface qua API/UI.
- `people` không có cột `teacher_id`/`student_id` — quan hệ chỉ tồn tại độc lập trong `marcus_networks`.
- Đã có sẵn route `/api/monk/<id>/marcus` (app.py, cả trong `server.py`/`api_ttl_rebuild.py`) nhưng route đó đọc từ **file TTL**, không đụng gì tới `marcus_reference`/`marcus_networks` thật — tên trùng gây nhầm lẫn, không phải cái cần cho T04.
- **Điều chỉnh scope:** roadmap gốc nhắc "term_glossaries" nhưng dữ liệu Marcus thật (tên + quan hệ + trích dẫn thư mục CBETA) không chứa nội dung định nghĩa thuật ngữ. Tra cứu web xác nhận Marcus (Bingenheimer) có repo glossary riêng: https://github.com/mbingenheimer/buddhist_studies_glossaries — chưa import vào project, để dành task riêng sau.

## Thiết kế/giải pháp đã chọn (chỉ thêm, không sửa/xoá dữ liệu cũ)

1. Bảng mới `marcus_people_link(person_id PK, marcus_node_id, match_confidence, match_method, created_at)` — populate 18.121 dòng khớp chính xác ID.
2. API `GET /daoanh/api/monk/<dila_id>/marcus-network` — trả `person`, `linked`, `teachers[]`, `students[]` (mỗi quan hệ kèm `ref` trích dẫn CBETA gốc từ Marcus).
3. API `GET /daoanh/api/monk-resolve?name=<tên>` — resolve tên Việt/Hán → DILA id qua bảng `people` (vì `monk_dict` mới có 2 dòng, không đủ để search theo tên).
4. Trang mới `lineage.html` (root `daoanh/`) — hiển thị thầy/trò cho 1 monk; đồng thời sửa link chết `/daoanh/lineage` mà trang HOME (`index.html`, kết quả tìm kiếm loại "Thiền sư") đã trỏ tới từ trước nhưng route chưa từng tồn tại.

### Sự cố kỹ thuật gặp và đã sửa
- Đặt route ban đầu là `/daoanh/api/monk/resolve` — bị route tổng quát `@app.route('/daoanh/api/monk/<monk_id>')` (đã có sẵn, dòng ~9220) nuốt mất "resolve" như một `monk_id`, trả về `{"error":"Monk not found"}` (404) thay vì route của mình. **Fix:** đổi path thành `/daoanh/api/monk-resolve` (không còn chung pattern `/monk/<...>`), loại bỏ hoàn toàn khả năng xung đột.

## Danh sách file đã tạo/sửa

- `data/lineage.db` — bảng mới `marcus_people_link` (18.121 dòng, additive)
- `app.py` — 2 route mới: `api_monk_resolve` (`/daoanh/api/monk-resolve`), `api_monk_marcus_network` (`/daoanh/api/monk/<dila_id>/marcus-network`)
- `lineage.html` (mới)
- `tasks/T04-marcus-glossaries-link.md` — cập nhật status, checklist, ghi chú scope
- `docs/tasktodo.md` — cập nhật dòng Task 4
- `docs/sessions/2026-08-18_t04_marcus_people_link.md` — session log này

## Cách chạy/test

```bash
# Test API trực tiếp (đã verify thành công với A000005 = 鑑堂一)
curl "http://localhost:5000/daoanh/api/monk/A000005/marcus-network"
# -> linked:true, 1 teacher (A000153 幻敏), 6 students (A000668, A003958, A003960, A004000, A004014, A037639)

curl "http://localhost:5000/daoanh/api/monk-resolve?name=%E9%91%92%E5%A0%82%E4%B8%80"
# -> person.id = A000005
```

## Kết quả test

- API `marcus-network`: ✅ verify thành công, trả đúng dữ liệu thật (curl trực tiếp port 5000).
- API `monk-resolve`: ✅ đã fix xung đột route, chưa kịp verify lại lần cuối bằng curl trước khi bị gián đoạn.
- Trang `lineage.html`: ⚠️ **chưa verify được qua browser end-to-end** — trong lúc test, phát hiện có **phiên Claude Code khác đang dev song song** trên cùng project (đã xác nhận với admin), liên tục restart process app.py/port 5000 (quan sát được: 5 tiến trình python cùng lúc, `sync_to_vps.ps1`/`local_gateway.py`/`CLAUDE.md` bị sửa ngoài ý muốn nhiều lần trong phiên) → dừng lại theo yêu cầu admin để tránh giẫm chân, chuyển task khác không đụng file "nóng" (app.py, local_gateway.py).
- **Việc cần làm tiếp (bởi phiên này hoặc phiên khác, sau khi app.py ổn định):**
  1. Verify `lineage.html` load đúng qua `http://localhost:8080/daoanh/lineage?name=鑑堂一`
  2. Chạy `python scripts/build_progress_data.py` để cập nhật dashboard
  3. Gắn khối "Quan hệ truyền thừa (Marcus)" vào sidebar entity chính của `places.html` (hiện chỉ có trang `lineage.html` riêng)

## Liên hệ ROADMAP

- Nguồn liên quan: Marcus glossaries/SNA
- Khoá ROADMAP: Khoá 1 — Xong core Hán → Việt
- Dòng ROADMAP tương ứng: "Marcus glossaries (thuật ngữ) — Authority thuật ngữ... Chuẩn hóa bảng term_glossaries, gắn với people/works, hiển thị 'thuật ngữ liên quan' trên person/TTL"
