# Session 2026-09-02 — T86 Truyền Thừa (Lineage) Research Workspace

## Task / Mục đích
Thiết kế lại tab 🌳 Truyền Thừa thành workspace nghiên cứu pháp hệ 3 cột (sidebar / canvas / inspector + evidence drawer) với dữ liệu 100% thật từ Marcus SNA.

## Work State

### Audit (trước build)
- `marcus_networks` 11,169 rows — mọi row `relation_type='da:isTeacherOf'`, đều có `ref` (CBETA citation).
- `marcus_people_link` 18,121 · `marcus_reference` 18,127 · `people` 48,673 · `person_origin_link` 11,929 · `lineage_conflicts_v2` 40,327 (is_conflict=1).
- **ID đồng nhất**: marcus_node_id == person_id trong dataset → route qua bridge + verify `people`.
- `passage` CHỈ 5 text_id (T50/X77) — ref lineage đa số (B35n0194, J40nB486) KHÔNG index → resolver trung thực `found:false`.
- `places` có `name_vi/name_zh`; `person_origin_link.confidence` đã có.

### Completed
1. **Backend `app.py`** (chèn sau `api_monk_graph` ~4400):
   - `GET /daoanh/api/monk/<dila_id>/lineage-tree?up=3&down=3` (`api_monk_lineage_tree` ~4535): BFS đệ quy up/down, lazy, mỗi edge `ref`+`has_ref`; node enrich `conflicts`/`origin_place`/`has_more_up/down`; center phải trong `people` → 404.
   - `GET /daoanh/api/lineage-ref/passage?ref=` (`api_lineage_ref_passage`): resolve text_id CBETA → passage, `found:true/false` trung thực.
   - Helpers `_t86_*`.
   - `py_compile` PASS.
2. **Frontend `places.html`**:
   - Markup `#tp-lineage` ~267: placeholder + workspace 3 cột (sidebar/canvas/inspector/drawer).
   - `loadLineageTree`/`centerLineageOn` (recenter lazy)/`_renderLineageMode`/`_renderLineageTree` (cây docs cột theo thế hệ, connector V-H-V kèm has_ref)/`_renderLineageNetwork` (vis)/`_renderLineageTimeline`/`_renderLineageSidebar`/`_renderLineageInspector(&Node|Edge)`/`_t86EdgeChip`/`loadLineageCite`/`openDaiTangReader`/`goToPlaceLineage`/`_wireLineageControls`.
   - `loadTabData` lineage → `loadLineageTree(placeId)`; `selectPerson` bỏ fetch /graph trùng lặp.
   - node syntax PASS.
3. **Docs**: `tasks/T86-truyenthua-workspace.md`, `docs/REPORT_TAB_TRUYENTHUA.md` (đang viết), session này.

### Tests
- `py_compile` PASS
- node syntax places.html PASS (1 script block)
- `npm run test` PASS, `npm run e2e` PASS
- **Runtime jsdom + live backend 5099** (test client thật):
  - `loadLineageTree('A000005')` → ok=true, 10 nodes/9 edges, mode=tree
  - render tree/network/timeline/inspector → **không throw**
  - `centerLineageOn('A000153')` → 17 nodes (recenter thật)
  - ref resolver: `found:true` (T51n2076→passage 1), `found:false` (B35n0194 chưa index), `None` (ref rỗng)
  - 404 person lạ

## Blocked
- e2e:runtime EPERM trên volume `E:\Backup 2025` (backup agent chặn unlink/rename — không phải code)
- lint/node--check `.html` node v24 'Unknown file extension' — dùng custom `new Function`
- Chưa kiểm tra trình duyệt thật (admin) — layout/fullscreen/scroll trực quan

## Next Move
1. Đổi trạng thái T86 trong tasktodo/progress → Build hoàn thành
2. Git commit T86 (T83 byte-ref) + verify + rollback sẵn
3. Session state save (tasktodo POST)

## Relevant Files
- `app.py`: `api_monk_lineage_tree` ~4535, `api_lineage_ref_passage` ~4655, helpers `_t86_*` ~4403-4520
- `places.html`: markup `#tp-lineage` ~267, frontend T86 block ~2143-2647, `selectPerson` ~1379, `loadTabData` lineage ~1340
- `tasks/T86-truyenthua-workspace.md`
- `docs/REPORT_TAB_TRUYENTHUA.md`
- Rollback git: `scripts/t83_ref_write.py --restore`
