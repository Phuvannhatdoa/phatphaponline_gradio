---
id: T86
title: Truyền Thừa (Lineage) Research Workspace — 3 cột
module: Lineage Visualization
priority: high
status: done
depends_on: [T16, T17]
created: 2026-09-02
updated: 2026-09-02
done_when: Tab Truyền Thừa là workspace 3 cột (sidebar/canvas/inspector) — dữ liệu 100% thật từ Marcus SNA, 3 view-mode (Pháp mạch tree / Phả hệ network / Niên đại), edge mang dẫn chứng thật + "Cần khảo cứu", cross-tab link tới Nhân Vật và Đại Tạng
---

# T86 — Truyền Thừa (Lineage) Research Workspace

## Mục tiêu
Thiết kế lại tab 🌳 Truyền Thừa thành **workspace nghiên cứu pháp hệ** 3 cột:
- **Sidebar trái**: chọn nhanh tăng nhân + bộ lọc + tìm trong pháp hệ
- **Canvas giữa**: 3 view-mode — Pháp mạch (cây doc, mặc định) / Phả hệ mở rộng (network, không mặc định) / Niên đại (timeline)
- **Inspector phải**: chi tiết node (tên, triều đại, tông, niên đại, quê quán, mâu thuẫn) hoặc edge (quan hệ, dẫn chứng, cách mở trong Đại Tạng)
- **Drawer bằng chứng** phía dưới: resolve dẫn chiếu CBETA → passage ("Đọc trong Đại Tạng")

## Ràng buộc (task spec)
- KHÔNG mount Leaflet/Google map trong tab này (địa lý = link "Xem trên bản đồ" ra tab Bản đồ).
- Network/graph KHÔNG phải view mặc định (cây doc dọc = mặc định).
- Nội dung thiếu dữ liệu → ghi "Chưa có dữ liệu" / "Cần khảo cứu" — KHÔNG bịa.
- Mobile = stacked (3 cột xếp dọc).
- Mỗi phiên build có report riêng: `docs/REPORT_TAB_TRUYENTHUA.md`.

## DATA REALITY (audit T86)
- `marcus_networks` 11,169 rows — toàn bộ `relation_type='da:isTeacherOf'`, **mọi row đều có `ref`** (CBETA citation URL).
- `marcus_people_link` 18,121 rows: person_id ↔ marcus_node_id. Trong dataset này marcus_node_id == person_id, vẫn resolve qua bridge cho chắc.
- `marcus_reference` 18,127 rows: label/label_vi/birth_year/death_year (nguồn niên đại ưu tiên — `people.birth_year/death_year` nhiễm số trang CBETA, T79).
- `people` 48,673 rows: name_zh/name_vi/dynasty/sect.
- `person_origin_link` 11,929 rows: person → place (quê quán/bản đồ) — confidence đã sort desc lấy top 1.
- `lineage_conflicts_v2` 40,327 rows: `conflict_type='teacher_set'/'student_set'`, `is_conflict=1` — real DILA-vs-Marcus mismatch source.
- `passage` CHỈ có 5 text_id (T51n2076, T50n2060/61/62, X77n1524) — hầu hết ref lineage (B35n0194, J40nB486...) KHÔNG có passage index → resolver trả `found:false` trung thực.

## Build (2026-09-02)

### Backend (`app.py`)
- `GET /daoanh/api/monk/<dila_id>/lineage-tree?up=3&down=3` (`api_monk_lineage_tree` ~4535): BFS đệ quy thầy (up) + trò (down), lazy (không crawl toàn bộ), mỗi edge mang `ref` thật + `has_ref` proxy dẫn chứng; enrich node: `conflicts` (lineage_conflicts_v2), `origin_place` (person_origin_link→places), `has_more_up/down` (expandable). Center phải có trong `people` → ngược trả 404.
- `GET /daoanh/api/lineage-ref/passage?ref=...` (`api_lineage_ref_passage`): parse text_id từ URL CBETA → match `passage.text_id` → `found:true/false` trung thực (message rõ nếu chưa index).
- Helpers: `_t86_person_info`, `_t86_neighbors`, `_t86_person_conflict`, `_t86_origin_place`, `_t86_parse_ref_passage`.

### Frontend (`places.html`)
- Markup `#tp-lineage` ~267: placeholder + workspace 3 cột.
- `loadLineageTree`, `centerLineageOn` (recenter lazy), `_renderLineageMode`, `_renderLineageTree` (tree doc, connectors V-H-V kèm has_ref), `_renderLineageNetwork` (vis, dash khi !has_ref), `_renderLineageTimeline`, `_renderLineageSidebar`, `_renderLineageInspector`/`_renderLineageInspectorEdge`, `_t86EdgeChip` (kèm nút 📖 Đọc trong Đại Tạng), `loadLineageCite`, `openDaiTangReader`, `goToPlaceLineage`, `_wireLineageControls`.
- `loadTabData` lineage nhánh → `loadLineageTree(placeId)`.
- `selectPerson` → click lineage tab → loadLineageTree (bỏ fetch /graph trùng lặp).

## Tests
- `py_compile` PASS
- node syntax places.html PASS
- `npm run test` PASS, `npm run e2e` PASS
- Runtime jsdom + live backend 5099: `loadLineageTree('A000005')` ok (10 nodes/9 edges), `centerLineageOn('A000153')` (17 nodes), render tree/network/timeline/inspector — **KHÔNG throw**
- Ref resolver: `found:true` (T51n2076 có passage) / `found:false` trung thực (B35n0194 chưa index) / `None` ref rỗng
- 404: person không có trong `people`

## Blocked
- e2e:runtime EPERM trên volume `E:\Backup 2025` (backup agent chặn unlink/rename — không phải code)
- lint/node--check trên `.html` node v24 'Unknown file extension' — dùng custom `new Function`

## Rollback
```bash
python scripts/t83_ref_write.py --restore
```

## Acceptance criteria (checklist)
- [x] Backend `lineage-tree` đệ quy + lazy expand
- [x] Backend `lineage-ref/passage` resolver (found true/false trung thực)
- [x] Frontend 3 cột: sidebar/canvas/inspector
- [x] View-mode: Pháp mạch (default tree) / Phả hệ (network) / Niên đại (timeline)
- [x] Edge semantics: has_ref (CBETA citation) / no_ref → "Cần khảo cứu"
- [x] Conflict marker từ lineage_conflicts_v2 (real)
- [x] Origin place → link "Xem trên bản đồ"
- [x] "Đọc trong Đại Tạng" → ref resolver → reader
- [x] Robustness: empty, 404, no-niên-đại, edits
- [ ] Kiểm tra trực quan trên trình duyệt thật (admin) — chưa có môi trường browser ở đây
