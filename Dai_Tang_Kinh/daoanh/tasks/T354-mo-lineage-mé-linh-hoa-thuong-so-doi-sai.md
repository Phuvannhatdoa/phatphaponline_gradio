---
id: T354
title: "BUG-032 — Cây truyền thừa: click Mễ Lĩnh Hòa Thượng không tính được số đời (phải ra 2 đời)"
bug_id: BUG-032
module: Lineage / places.html
priority: high
status: in_progress
depends_on: []
created: 2026-10-11
updated: 2026-10-11
done_when: >
  Mở http://127.0.0.1:8080/daoanh/places.html?mode=lineage&focus=A001984&lm=tree&chain=A005255%2CA009491%2CA010583
  → click "Mễ Lĩnh Hòa Thượng" → panel hiển thị số đời đúng 2 đời:
  (1) Truyền thừa Thiền tông: tính từ Ma Ha Ca Diếp;
  (2) Truyền thừa Quy Ngưỡng Tông: Đời thứ 3;
  bằng chứng: screenshot trước/sau + network log API liên quan;
  daoanh-qa xác nhận không hồi quy cho các nút khác trong cây.
---

# BUG-032 (T354) — Số đời truyền thừa không tính được khi click Mễ Lĩnh Hòa Thượng

> Quy tắc: bug phải có số BUG-xxx, ghi trên dashboard (bảng "A. BUGS"), chỉ đánh Done khi Admin bấm xác nhận.

## Triệu chứng (Admin báo)

- URL: `http://localhost:8080/daoanh/places.html?mode=lineage&focus=A001984&lm=tree&chain=A005255%2CA009491%2CA010583`
- Thao tác: click "Mễ Lĩnh Hòa Thượng".
- Hiện tại: thuật toán không tính ra số đời truyền thừa.
- Kỳ vọng theo logic: node này mang 2 đời:
  - Truyền thừa Thiền tông: tính từ thời Ma Ha Ca Diếp.
  - Truyền thừa Quy Ngưỡng Tông: Đời thứ 3.

## Phạm vi dự kiến

- Logic tính số đời: nhánh `mode=lineage` trong `places.html` và API liên quan (`/api/trace_lineage`, `evidence-based generation`, T232/T275 nếu có).
- Dữ liệu: chuỗi `chain=A005255,A009491,A010583` và focus `A001984`.

## Nguyên nhân nghi ngờ (chưa xác minh)

- Số đời chỉ tính theo một chuỗi (single chain), không gộp nhiều chuỗi truyền thừa của cùng một node.
- `chain` có 3 mã nhưng chỉ dùng một phần.

## Nguyên nhân đã xác minh (2026-10-11, trước khi sửa code)

Entity đúng trong cây: "Mễ Lĩnh Hòa Thượng" con của Kính Sơn Hồng Nhân (A010583)
là **A027028** (米嶺和尚, xác nhận bằng DILA edge `DILA:5481/20464/31557`
subject=A010583→object=A027028, và bằng UI thật: panel "ĐỆ TỬ" của A010583
hiện "Mễ Lĩnh 米嶺 DILA ID: A027028"). Có một entity trùng tên khác A027242
(con của Mã Tổ Đạo Nhất A003623) nhưng KHÔNG nằm trong nhánh được click ở đây —
loại trừ giả thuyết "nhầm node trùng tên".

Có **2 bug độc lập**, cả hai cùng góp vào triệu chứng:

**Bug A — UI không gọi lại tính số đời khi click node trong cây Pháp mạch.**
`places.html` hàm `network.on('click', ...)` (~dòng 6695-6747, nhánh
`options.mode === 'lineage'`) khi click thân node chỉ tự cập nhật
`#lineage-sidebar-title`, `#lineage-header`, `#lineage-quicklist` bằng DOM
trực tiếp (dòng 6723-6744) — KHÔNG gọi `selectPerson`, `openPersonLineage`,
`_gmpShowNodeDetail`, hay `_nexusShowDetail`. Đây là 4 hàm duy nhất bị
`admin/places-generation-v2.js` (dòng 63-64) monkey-patch để trigger
`load(id)` → fetch `/api/admin/ttl_v2/generation/calculate/<id>`. Kết quả:
click node trong Pháp mạch không bao giờ tính lại số đời cho node vừa chọn —
panel “Truyền Thừa … Đời thứ N” giữ nguyên giá trị của lần tính trước đó
(stale), trong khi tiêu đề/breadcrumb/quicklist vẫn cập nhật đúng (verify
bằng network log: chỉ có đúng 1 request `generation/calculate/A001984` dù đã
click sang nhiều node khác nhau).

**Bug B — Engine chặn số đời do "nhiễu" tổ tiên không liên quan tới đường
chứng minh đã chọn.** `src_python/generation_engine_v2.py` hàm `compute()`
(dòng 308-333 bản trước sửa): sau khi duyệt toàn bộ tổ tiên bắc cầu
(BFS ngược từ person_id qua `parents()`), nếu `base['issues']` (danh sách
toàn cục, gồm cả vấn đề ở nhánh tổ tiên-của-tổ-tiên hoàn toàn không nằm trên
đường chứng minh số đời đã chọn) KHÁC RỖNG thì trả `status='incomplete'`,
`number=None` — bất kể `candidates` đã tính ra MỘT giá trị duy nhất, không
mâu thuẫn. Gọi trực tiếp API xác nhận: với A027028, scheme `guiyang`
(Quy Ngưỡng) có `candidates=[3]` (đúng kỳ vọng Đời thứ 3!) và scheme
`chan_ca_diep_1` có `candidates=[39]`, nhưng cả hai trả `number=null`,
`status=incomplete` vì nhiều `issues` (`orphan_outside_root`,
`unresolved_parent_branch`) ở các tổ tiên xa (ví dụ A008803, A002397…)
không nằm trên witness path của A027028. `admin/places-generation-v2.js`
hàm `renderInto()` chỉ hiển thị dòng có `r.number!==null` nên dòng này bị ẩn
hoàn toàn dù số đã tính được nội bộ.

→ Chỉ sửa Bug A thì UI sẽ gọi đúng API cho A027028 nhưng vẫn không hiện số
(do Bug B). Phải sửa cả hai mới đạt done_when.

## Đã sửa (2026-10-11)

**Backup trước sửa:**
- `daoanh/docs/sessions/2026-10-11/places.html-bugA-before` (Bug A)
- `daoanh/docs/sessions/2026-10-11/generation_engine_v2.py-bugB-before` (Bug B)

**Bug A sửa:** `daoanh/places.html` dòng 6748 
- Đã được sửa: `if (window._ptdaLoadGenerationV2) { window._ptdaLoadGenerationV2(pid); }` 
- Gọi `load()` khi click node trong lineage tree để tính số đời.
- Hàm `load()` được assign tại `daoanh/admin/places-generation-v2.js` dòng 68.
- **Trạng thái:** ✅ Code đã có (không cần thay đổi thêm).

**Bug B sửa:** `daoanh/src_python/generation_engine_v2.py` dòng 326-335
- Trước: `if base['issues']:return dict(...status='incomplete'...)` — chặn kết quả nếu có bất kỳ issue nào.
- Sau: nếu có `candidates` (đường chứng minh tồn tại) thì return `number`, dù có issues ở nhánh tổ tiên khác.
- Issues vẫn ghi nhận trong message nhưng không chặn kết quả.
- **Trạng thái:** ✅ Code đã sửa (chờ server restart để test).

**Cần:** Admin restart `app.py` (port 5000) để load `generation_engine_v2.py` sửa, rồi test lại URL.

## Ràng buộc

- Không git add/commit/push.
- Test local dùng `127.0.0.1`, không dùng `localhost`.
- Bằng chứng bắt buộc: click thật trên UI + screenshot trước/sau + network log.
