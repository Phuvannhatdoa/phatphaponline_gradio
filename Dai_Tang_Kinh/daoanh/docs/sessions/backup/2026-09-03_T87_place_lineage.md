# Session 2026-09-03 — T87: Truyền Thừa theo Địa Điểm (Place → Person → Tree)

## Bối cảnh
User mở `http://localhost:8080/daoanh/places#PL000000000002` (địa danh) và bấm tab 🌳 Truyền Thừa
nhưng không thấy gì — dead-end. Chẩn đoán: `places.html:1388` return sớm cho entity `place` khi tab
`lineage` active. Yêu cầu: làm Trưyền Thừa có nghĩa trong ngữ cảnh địa danh.

## Quyết định (admin, qua câu hỏi)
Chọn **Place → Person → Tree** (nhẹ, tái dùng T86) thay vì aggregate lineage-by-place to.
Ràng buộc: không bịa dữ liệu → trạng thái thiếu = "Cần khảo cứu"; địa lý = link ra tab Bản đồ.

## Phát hiện quan trọng
1. **Hai namespace id địa danh**: `places` id ngắn `PL000000`; `places_dila`/`person_origin_link`/
   `place_person_bibl` id dài `PL000000000002`. `/persons` nhận cả 2 nhưng bibl/origin chỉ có với id dài.
2. **Server 5000 stale**: `lineage-tree` 404 (Flask default, body rỗng) dù code hiện tại + DB đều đúng
   (test_client → 200). Nguyên nhân: process cũ PID 4988 từ phiên trước. Đã cleanup + khởi động lại
   server mới → 200. Lưu ý deployment.
3. `has_lineage` (persons) = có node trong `marcus_people_link`, KHÔNG đảm bảo cạnh thầy/trò. Người
   cô lập → tree center-only, bộ chọn vẫn hiển thị đúng + "Cần khảo cứu" khi click.

## Build (frontend-only, places.html)
- Bỏ no-op 1388 → `loadPlaceLineagePicker(placeId)`.
- `loadPlaceLineagePicker`: fetch `/persons`, worker render vào `#lineage-canvas`: header count +
  số có truyền thừa + nhóm theo nguồn (bỏ wikidata); `_personPickerRow` (badge 🌳 TRUYỀN THỪA / muted
  "Cần khảo cứu"); rỗng → da-warn trung thực. Vô hiệu nút chế độ `#lineage-mode` trong picker.
- `_t86EnableModeBtns()`: bật lại nút chế độ — gọi ở `_renderLineageMode` + nhánh empty (0 edges)
  của `loadLineageTree`.

## Dữ liệu
- `PL000000042182` (長安縣): 142 bibl / 118 lineage / 38 cạnh (demo giàu).
- `PL000000000002` (Hưng Đô Khố Thập Sơn/Hindu Kush): 6 bibl (A005671 Pháp Dũng...) hầu hết cô lập.

## Tests
- node syntax places.html PASS; runtime jsdom + live backend: picker rich (175 dòng), địa điểm user
  (9 dòng), unknown (0 + warn), click-through A005671 → "Pháp hệ · Pháp Dũng" + mode re-enabled +
  empty-shown — OK. npm test PASS, npm e2e PASS. Backend không đổi.

## Commit
- T83 byte-ref recipe. Files: places.html (+picker/helpers), tasks/T87.., REPORT addendum, session log,
  tasktodo.md, progress.md, data/progress_data.json (gitignored → `-f`).

## To làm tiếp
- Kiểm tra trực quan trình duyệt thật (admin) — layout/content picker + click-through.
- T87 rollback git: `python scripts/t83_ref_write.py --restore`.
