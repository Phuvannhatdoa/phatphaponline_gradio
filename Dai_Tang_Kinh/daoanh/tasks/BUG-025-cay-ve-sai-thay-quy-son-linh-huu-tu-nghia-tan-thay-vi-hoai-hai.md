---
id: BUG-025
title: "Cây pháp hệ vẽ sai thầy của Quy Sơn Linh Hựu — vẽ từ Nghĩa Tân (A010527) thay vì Hoài Hải (A001897), trong khi Hoài Hải mới là pháp mạch đúng"
module: Lineage tree (places.html / ancestor-spine)
priority: P1
status: in_progress
depends_on: []
created: 2026-10-11
updated: 2026-10-11
done_when:
  - Cây pháp hệ (lineage tree, places.html) vẽ Quy Sơn Linh Hựu (A001984) với thầy là Hoài Hải (A001897), không phải Nghĩa Tân (A010527)
  - Root cause xác định rõ: hàm/API nào đang bỏ qua lineage_primary_teacher.is_primary=1
  - Fix không phá các node khác đang vẽ đúng (kiểm tối thiểu 5 trường hợp khác có is_primary=1 ≠ edge DILA mới nhất)
  - Admin xác nhận DONE qua UI thật
---

## Triệu chứng (Admin báo 2026-10-11)

Trên cây pháp hệ, nhánh của Quy Sơn Linh Hựu chỉ vẽ lên từ "Nghĩa Tân", không vẽ từ "Hoài Hải" — trong khi Hoài Hải (Bách Trượng Hoài Hải) mới đúng là pháp mạch của Quy Sơn (Quy Ngưỡng tông: Bách Trượng Hoài Hải → Quy Sơn Linh Hựu).

## Đã xác nhận (chỉ đọc, chưa sửa gì)

- **TTL đúng:** `data/ttl/TS-Quy-Son-Linh-Huu.ttl` dòng 477: `bkg:hasTeacher <ex:monk/bach_truong_hoai_hai>`. Không có "Nghĩa Tân" ở đâu trong TTL.
- **DILA ID:** Quy Sơn Linh Hựu = `A001984` (靈祐). Hoài Hải = `A001897` (懷海). "Nghĩa Tân" = `A010527` (義賓).
- **`lineage_edge_assertions`:** có 2 ứng viên thầy cho A001984 — A001897 (Hoài Hải: 2 cạnh DILA id 15080/15297, 1 Marcus, 1 TTL hasTeacher id 58102, 1 TTL hasDisciple id 57251) và A010527 (Nghĩa Tân: 2 cạnh DILA id 15298/20388, 1 Marcus, **không có TTL**).
- **`lineage_primary_teacher` (bảng đã resolve sẵn, đúng):**
  ```
  id=3315  teacher_id=A001897 disciple_id=A001984 is_primary=1 evidence_source=TTL ttl_confirmed=1
           note: "TTL (Truyền Đăng Lục VN) xác nhận; Marcus không có từ khóa phân loại"
  id=6972  teacher_id=A010527 disciple_id=A001984 is_primary=0 evidence_source=FALLBACK confidence=low
  ```
  → **Dữ liệu đã đúng.** Bảng `lineage_primary_teacher` đã xác nhận Hoài Hải là `is_primary=1`.

## Giả thuyết root cause (CHƯA xác minh code, cần debugger kiểm)

Vì bảng resolve đã đúng nhưng UI vẽ sai, lỗi nhiều khả năng nằm ở **code build cây/ancestor-spine** (không phải ở dữ liệu TTL hay `generation_engine_v2.py parents()` — đã kiểm T270 trước đây dùng đúng filter). Nghi vấn cụ thể:
- Hàm dựng cây lineage trong `places.html` (`loadLineageTree`, `_lineageMergeAncestorSpine`) hoặc endpoint `/daoanh/api/monk/<id>/ancestor-spine` / `/daoanh/api/monk/<id>/lineage-tree` trong `app.py` có thể **không** query `lineage_primary_teacher WHERE is_primary=1`, mà lấy trực tiếp từ `lineage_edge_assertions` theo cách khác (ví dụ ORDER BY id DESC LIMIT 1 trên edge DILA thô) — nếu vậy sẽ luôn ra A010527 vì cạnh DILA id 20388 (Nghĩa Tân) có id lớn nhất trong nhóm DILA thô, mặc dù TTL/primary table đã chỉ rõ Hoài Hải.

## Việc cần debugger làm

1. Tìm chính xác hàm/route build cây pháp hệ dùng khi vẽ ancestor lên trên (không phải generation number engine — khác file/khác mục đích).
2. Xác nhận route đó có dùng `lineage_primary_teacher.is_primary` hay không. Nếu không, đó là root cause.
3. Sửa để ưu tiên `is_primary=1` (hoặc TTL-confirmed) khi dựng cây, nhất quán với cách `generation_engine_v2.py` đã làm.
4. Test tối thiểu: A001984 (Quy Sơn) hiện đúng thầy A001897; dò thêm ≥5 trường hợp khác trong `lineage_primary_teacher` có `is_primary=1` khác với edge DILA mới nhất, xác nhận không bị vẽ sai tương tự sau khi sửa.
5. Backup file trước sửa vào `docs/sessions/2026-10-11/`. Không đổi DB. Verify qua UI thật (click thật, screenshot trước/sau), không JS inject. Không tự đánh DONE.

## Liên quan

T270 (nối pháp TTL + Marcus), T275 (neo số đời TTL), `lineage_primary_teacher` (bảng resolve is_primary).

## Trạng thái 2026-10-11 — Đã sửa, CHƯA DONE (chờ Admin xác nhận UI)

- Root cause: route `GET /daoanh/api/monk/<dila_id>/lineage-tree`, nhánh BFS "lên" trong `app.py` (hàm `api_monk_lineage_tree`) lặp mọi ứng viên thầy và trả nhiều cạnh `teacher` cạnh tranh cho cùng một node. Frontend `_lineageTreeParents()` ghi đè theo "cạnh tới sau thắng" nên lấy Nghĩa Tân (A010527, is_primary=0).
- Sửa: chỉ giữ 1 cạnh thầy đầu tiên hợp lệ (đã sort `is_primary DESC`, bỏ tham học `-1` và cạnh bị rejected). Chiều "xuống" không đổi. Backup: `docs/sessions/2026-10-11/app.py.BUG-025.bak`.
- Kiểm: A001984 còn 1 cạnh thầy là A001897 (UI thật, ảnh chụp). 5 case mẫu qua API đúng. Chưa kiểm hết 168 case cùng kiểu.
- Còn mở: (a) Admin xác nhận DONE qua UI; (b) có giao `daoanh-qa` chạy full 168 case không; (c) có làm phòng thủ ở frontend `_lineageTreeParents()` (chọn is_primary=1) không.
