---
id: T87
title: Truyền Thừa theo Địa Điểm (Place → Person → Tree)
module: Lineage Visualization
priority: high
status: done
depends_on: [T86]
created: 2026-09-03
updated: 2026-09-03
done_when: Tab 🌳 Truyền Thừa trong ngữ cảnh ĐỊA ĐIỂM hiển thị bộ chọn tăng nhân liên kết với địa danh (curated + bibl + origin + bio), mỗi người gắn nhãn 🌳 TRUYỀN THỪA nếu có dữ liệu pháp hệ; click → mở workspace 3 cột của T86; trạng thái rỗng/thiếu trung thực "Cần khảo cứu"
---

# T87 — Truyền Thừa theo Địa Điểm (Place → Person → Tree)

## Mục tiêu
Trước T87, tab 🌳 Truyền Thừa trong ngữ cảnh **địa điểm** là **dead-end**: `places.html:1388`
(`if (_currentEntityType === 'place' && tab === 'lineage') return;`) → người dùng mở `#PL...` rồi
bấm Truyền Thừa chỉ thấy canvas trống (main panel hiện nhưng không có gì render).

T87 biến nó thành luồng **Place → Person → Tree**:
- Khi đang ở 1 địa danh + tab Truyền Thừa → render bộ chọn tăng nhân liên kết với địa danh đó.
- Tăng nhân có dữ liệu pháp hệ → nhãn `🌳 TRUYỀN THỪA`, click → `selectPerson()` → mở lại **workspace 3 cột T86** (Pháp mạch/Phả hệ/Niên đại + inspector + drawer) quanh người đó.
- Tăng nhân không có pháp hệ / địa danh không có nhân vật → trạng thái trung thực "Cần khảo cứu".

## DATA REALITY (audit T87)
- **Hai namespace id địa danh song song**:
  - `places` (map/selectItem): id ngắn `PL000000` (8 ký tự, zeropad).
  - `places_dila` + `person_origin_link.place_id` + `place_person_bibl.place_id`: id dài `PL000000000002` (13 ký tự).
  - `/persons` endpoint nhận cả 2, nhưng dữ liệu bibl/origin trả về chỉ có với **id dài** (khớp places_dila).
- `/daoanh/api/places/<id>/persons` (app.py `api_places_persons`) gộp 4 nguồn: `persons` (curated,
  `place_person_link`), `bibl_persons` (`place_person_bibl` — CBETA bibl), `origin_persons`
  (`person_origin_link` — quê quán), `bio_persons` (`place_person_bio_cache` — tự động). Mỗi người:
  `id` (DILA == `people.id` == `marcus_people_link.person_id`), `name_vi/zh`, `marcus_label`, `dynasty`,
  `relation_type`, `source_name`, `note`, `has_lineage`.
- `has_lineage` = tồn tại trong `marcus_people_link` (có node), **KHÔNG đảm bảo có cạnh thầy/trò**.
  Người có node nhưng 0 cạnh (`marcus_networks`) → `lineage-tree` trả center-only (ok:true) — bộ chọn
  hiển thị đúng, click mở tree 1 nút + "Chưa có dữ liệu truyền thừa Marcus".
- Ví dụ: `PL000000042182` (長安縣) 142 bibl / 118 có lineage / 38 có cạnh — demo giàu.
  `PL000000000002` (Hưng Đô Khố Thập Sơn/Hindu Kush) 6 bibl (A005671 Pháp Dũng...) hầu hết cô lập.

## Build (2026-09-03) — frontend-only (places.html)
- Bỏ no-op `places.html:1388` → gọi `loadPlaceLineagePicker(placeId)`.
- `loadPlaceLineagePicker(placeId)`: fetch `/persons`, render vào `#lineage-canvas` (main panel T86):
  header (count + số có truyền thừa), nhóm theo nguồn (curated/bibl/origin/bio, bỏ wikidata chưa gắn DILA),
  mỗi dòng = `_personPickerRow(p)`:
  - `has_lineage` → badge `🌳 TRUYỀN THỪA`, `onclick=selectPerson(id,label)`.
  - không → muted "Cần khảo cứu" + "Không có dữ liệu pháp hệ Marcus", không click được.
  - Rỗng → da-warn "Chưa có dữ liệu nhân vật cho địa danh này (Cần khảo cứu)" (trung thực).
- Trong picker: vô hiệu hoá các nút chế độ `#lineage-mode` (opacity .5, disabled) + inspector hint.
- `_t86EnableModeBtns()`: bật lại nút chế độ — gọi trong `_renderLineageMode` VÀ nhánh empty (0 edges)
  của `loadLineageTree` (tránh kẹt disabled khi người được chọn cô lập).

## Tests (2026-09-03)
- node syntax places.html PASS (`new Function`).
- Runtime jsdom + live backend 5000 (server được khởi động lại — code cũ đang 404 do stale process):
  - `loadPlaceLineagePicker('PL000000042182')` → 175 dòng, badge + "Cần khảo cứu".
  - `loadPlaceLineagePicker('PL000000000002')` (địa điểm người dùng) → 9 dòng, badge + cần khảo cứu.
  - `loadPlaceLineagePicker('PLDOESNOTEXIST')` → 0 dòng + warn.
  - Mode buttons disabled trong picker; sau `selectPerson('A005671')` → title "Pháp hệ · Pháp Dũng",
    mode re-enabled, empty-shown (cô lập) — luồng click-through OK.
- `npm run test` PASS, `npm run e2e` PASS.
- Backend không đổi → không cần py_compile, nhưng test_client xác nhận `lineage-tree` 200 (A005671).

## Rollback / lưu ý
- Git rollback T87: `python scripts/t83_ref_write.py --restore` (sau commit T87).
- Server 5000 đã restart trong phiên này để chạy code hiện tại (trước đó stale → lineage-tree 404).
