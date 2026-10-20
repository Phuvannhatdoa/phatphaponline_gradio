# REPORT TAB TRUYỀN THỪA (T86) — Lineage Research Workspace

Ngày: 2026-09-02 · Module: Truyền Thừa · Trạng thái: Build hoàn thành, chờ kiểm tra trực quan admin

## 1. Tóm tắt
Tab 🌳 Truyền Thừa giờ là **workspace 3 cột** để nghiên cứu pháp hệ truyền thừa dữ liệu **100% thật** từ Marcus SNA (Bingenheimer, ChineseBuddhism_SNA). Không bịa — thiếu dữ liệu hiển thị rõ "Chưa có dữ liệu" / "Cần khảo cứu".

## 2. API thực tế

### `GET /daoanh/api/monk/<dila_id>/lineage-tree?up=3&down=3`
Trả cây pháp hệ quanh một tăng nhân (BFS đệ quy thầy/trò, lazy expand).

| Field | Loại | Ghi chú |
|-------|------|---------|
| `ok` | bool | false + 404 nếu person không có trong `people` |
| `center` | object | `{id,name_vi,name_zh,dynasty,sect,birth_year,death_year,conflicts[],origin_place,has_more_up,has_more_down}` |
| `nodes[]` | object | cùng shape `center`, enrich mỗi node |
| `edges[]` | object | `{from,to,direction:'teacher'\|'student',relation_type:'da:isTeacherOf',ref,has_ref,derived:false}` |
| `up`/`down` | int | độ sâu đã yêu cầu |

### `GET /daoanh/api/lineage-ref/passage?ref=...`
Resolve dẫn chiếu CBETA → passage ("Đọc trong Đại Tạng").

| Field | Mô tả |
|-------|-------|
| `resolved.found` | true nếu match text_id trong `passage` |
| `resolved.passage_id`/`text_id`/`loc_ref` | khi found=true |
| `resolved.message` | giải thích trung thực khi found=false |

## 3. Dữ liệu thật (số liệu từ lineage.db)

| Bảng | Số row | Vai trò |
|------|--------|---------|
| `marcus_networks` | 11,169 | quan hệ thầy/trò (mọi row có `ref`) |
| `marcus_people_link` | 18,121 | person ↔ marcus node (id đồng nhất) |
| `marcus_reference` | 18,127 | tên chuẩn + label_vi + niên đại |
| `people` | 48,673 | name/dynasty/sect |
| `person_origin_link` | 11,929 | quê quán → bản đồ |
| `lineage_conflicts_v2` | 40,327 | mâu thuẫn DILA vs Marcus (is_conflict=1) |
| `passage` | ~6,347 | chỉ 5 text_id — ref lineage đa số không index |

## 4. Khoảng trống dữ liệu phát hiện (DATA GAPS)
1. **Passage index rất hạn chế**: hầu hết `ref` cascade (B35n0194, J40nB486, X84n1582...) **không có passage** trong bảng `passage`. "Đọc trong Đại Tạng" hiện trả `found:false` trung thực. Khi index đầy đủ (T85 full-backfill + passage import), resolver sẽ tự hoạt động — đã kiểm chứng path `found:true` với T51n2076.
2. **`people.birth_year/death_year` không tin cậy** (nhiễm số trang CBETA, T79) → workspace dùng `marcus_reference.birth_year/death_year` là nguồn ưu tiên; phần lớn vẫn NULL (niên đại "chưa rõ").
3. **`origin_place.name_vi/name_zh` có thể NULL**: VD A001738 (Huệ Cơ) có `place_id=PL000000036457` nhưng tên trống trong `places`. Cần verify data places row.
4. **Conflict**: mọi node trong mẫu đều có cả `teacher_set` + `student_set` (is_conflict=1) — marker hiển thị đầy đủ, không phải lỗi.

## 5. Cấu trúc UI
- **Placeholder**: nút "Tới tab Nhân Vật" khi chưa chọn.
- **Sidebar**: title pháp hệ + quicklist chips (click = recenter) + bộ lọc (Tất cả / Chỉ hiển thị / Chỉ có dẫn chứng / Chỉ mâu thuẫn — hộp kiểm) + tìm trong pháp hệ (lọc quicklist).
- **Canvas**: dải công cụ (view-mode segmented: Pháp mạch/Phả hệ/Niên đại + zoom ＋－ + Fit + Tâm + Fullscreen) + canvas.
- **Inspector**: node (tên HÁN-VIỆT, DILA ID, triều đại, tông, niên đại, quê quán + "Xem trên bản đồ", mâu thuẫn, danh sách thầy/trò kèm dẫn chứng + nút Đọc trong Đại Tạng, nút "Đưa vào tâm pháp hệ") · edge (quan hệ, has_ref/chưa có, ref text).
- **Drawer bằng chứng**: kết quả resolve passage hoặc thông báo thiếu index.

## 6. Edge semantics (proxy dẫn chứng — quyết định admin T86)
- `has_ref=true` → nét liền màu vàng (CBETA citation thật). *Không có edge no_ref trong dữ liệu thật hiện tại* (mọi marcus_networks.ref đều rỗng→không, thực tế mọi row có ref), nên nhánh "Cần khảo cứu" (nét đứt) là dự phòng cho dữ liệu tương lai.
- Conflict chỉ từ `lineage_conflicts_v2` (real), không suy diễn.

## 7. Cross-tab links
- Node inspector → "Xem trên bản đồ" → tab Bản đồ (selectItem(placeId)).
- "Đọc trong Đại Tạng" → resolve → mở Reader modal của tab Đại Tạng.
- Quicklist chip / click node → recenter pháp hệ quanh người đó.
- Placeholder → "Tới tab Nhân Vật".

## 8. Xác nhận
- Backend: py_compile PASS; test client: lineage-tree 200 (A000005/9 node; A000153/11 node up=3), 404 person lạ, ref resolver found true/false.
- Frontend: node syntax PASS; runtime jsdom + live backend — mọi render path (tree/network/timeline/inspector) không throw; recenter A000153 → 17 node.
- npm test PASS, npm e2e PASS.
- **Chưa có kiểm tra trình duyệt thật** (admin) — cần xác nhận trực quan layout/scroll/fullscreen.

---

# T87 — Phụ lục: Truyền Thừa theo Địa Điểm (Place → Person → Tree)

## Vấn đề (trước T87)
Tab 🌳 Truyền Thừa trong ngữ cảnh **địa điểm** là dead-end: `places.html:1388` return sớm
(`_currentEntityType === 'place' && tab === 'lineage'`) → mở `#PL...` + bấm Truyền Thừa = canvas trống
(main panel hiện nhưng không render gì). Người dùng chỉ đạt được hệ truyền thừa khi đi qua tab 🧑 Nhân Vật.

## Giải pháp (T87, 2026-09-03) — frontend-only
- **Place → Person → Tree**: địa danh + tab Truyền Thừa → `loadPlaceLineagePicker(placeId)` render
  bộ chọn tăng nhân liên kết với địa danh (4 nguồn: curated `place_person_link`, bibl `place_person_bibl`,
  origin `person_origin_link`, bio `place_person_bio_cache` — bỏ `wikidata_persons` chưa gắn DILA id).
- Mỗi dòng `_personPickerRow(p)`: có `has_lineage` → badge `🌳 TRUYỀN THỪA` + `onclick=selectPerson(id,label)`
  → mở lại **workspace 3 cột T86** (Pháp mạch/Phả hệ/Niên đại + inspector + drawer). Không có lineage →
  muted "Cần khảo cứu" (không click được). Rỗng → da-warn trung thực.
- Vô hiệu hoá nút chế độ trong picker; `_t86EnableModeBtns()` bật lại ở `_renderLineageMode` VÀ nhánh
  empty (0 edges) của `loadLineageTree` (tránh kẹt khi người được chọn cô lập).

## DATA REALITY (T87)
- **Hai namespace id địa danh**: `places` dùng `PL000000` (ngắn, map/selectItem); `places_dila`/
  `person_origin_link`/`place_person_bibl` dùng `PL000000000002` (dài). `/persons` nhận cả 2, nhưng dữ
  liệu bibl/origin chỉ trả về với id dài.
- `has_lineage` = có trong `marcus_people_link` (có node), KHÔNG đảm bảo có cạnh thầy/trò. Người 0 cạnh
  → `lineage-tree` trả center-only → bộ chọn hiển thị đúng, click mở tree 1 nút + "Chưa có dữ liệu truyền thừa".
- `PL000000000002` (Hưng Đô Khố Thập Sơn/Hindu Kush): 6 bibl (A005671 Pháp Dũng...) hầu hết cô lập.
  `PL000000042182` (長安縣): 142 bibl / 118 lineage / 38 cạnh — demo giàu.

## Xác nhận (T87)
- node syntax places.html PASS; runtime jsdom + live backend: picker rich (175 dòng) / địa điểm user
  (9 dòng cho `PL000000000002`) / unknown (0 + warn); click-through `selectPerson(A005671)` → "Pháp hệ ·
  Pháp Dũng", mode re-enabled, empty-shown (cô lập) — OK.
- npm test PASS, npm e2e PASS. Backend không đổi (test_client lineage-tree 200).
- Server 5000 restart trong phiên để chạy code hiện tại (trước đó stale → lineage-tree 404 không rõ lý do).
- Task: `tasks/T87-place-lineage-picker.md`. Session: `docs/sessions/2026-09-03_T87_place_lineage.md`.
