# Session 2026-09-09 — T101 Graph/Nexus Bug Fix

## Tóm tắt

Fix 5 bugs trong Nexus grouped view và `api_places_graph`.

## Thay đổi

### app.py

**Nexus block** (`api_places_graph`, ~line 4587):
- BEFORE: `pname = r[4] or r[5] or r[1] or pid` — dùng `people.name_vi` trực tiếp
- AFTER: `dn = _t86_resolve_display_name(conn, pid)` — ưu tiên `person_display_names.display_name_vi` (verified_direct/crosswalk)

**Curated block** (`api_places_graph`, ~line 4622):
- BEFORE: `pname = r[4] or r[5] or pid`
- AFTER: `dn = _t86_resolve_display_name(conn, pid)`

### data/lineage.db

```sql
UPDATE people SET name_vi = 'Nhị Tổ' WHERE id = 'A003881';

INSERT INTO person_display_names
  (person_id, dila_person_id, locale, display_name_vi, display_name_zh,
   authority_name_vi, authority_name_zh, style_type, is_preferred,
   verification_status, source_type, source_file, mapping_method, mapping_evidence, import_run_id)
VALUES
  ('A001361', 'A001361', 'vi', 'Bồ Đề Đạt Ma', '菩提達摩',
   'Bồ Đề Đạt Ma', '菩提達摩', 'formal', 1,
   'verified_direct', 'manual', 'manual_correction', 'manual_admin',
   'Admin correction: people.name_vi=Bích Quan Bà La Môn là biệt danh; tên chính: Bồ Đề Đạt Ma (菩提達摩)',
   'session_2026-09-09');
```

### places.html

- `_nexusGroupedFinalize`: ẩn vis.js labels, nodeDistance 100→160
- Thêm hàm `_nexusResolveLabelCollisions` (greedy, priority queue)
- Re-attach afterDrawing sau cả 2 branches
- zoom/dragEnd → redraw

## Kết quả verify

| Bug | Kết quả |
|-----|---------|
| BUG-001 label_zh Thiếu Lâm Tự | ✅ `少林寺` |
| BUG-004 curated nodes | ✅ 2 nodes |
| A003881 Nhị Tổ | ✅ DB updated |
| A001361 Bồ Đề Đạt Ma | ✅ API: `label: Bồ Đề Đạt Ma` |
| Nexus label collision | ✅ Console: `No label overlaps` (3 lần) |

## Pending

- Admin xác nhận live UI
- BUG-002/003: task riêng
