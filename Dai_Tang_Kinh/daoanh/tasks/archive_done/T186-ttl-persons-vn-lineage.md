---
id: T186-ttl-persons-vn-lineage
title: "T186 — ttl_persons: Hệ thống hóa danh tăng VN từ TTL local vào lineage tree"
module: Lineage / Data Pipeline
priority: high
status: done
owner: claudecode
depends_on: [T185-ttl-full-import]
created: 2026-09-28
updated: 2026-09-28
done_at: "2026-09-28 (ttl_persons 211 rows; 422 VN edges vào consensus; API patch 3 guards + search fallback; syntax OK)"
plan_approved_at: "2026-09-28 (Admin: 'tạo ttl_persons với ghi chú là tree do tài liệu local VN')"
done_when: |
  Bảng ttl_persons tồn tại với 211 danh tăng VN chỉ có trong TTL;
  422 cạnh VN vào lineage_edge_consensus (migration_marker='T186_TTL_VN', is_default_visible=0);
  lineage_edge_assertions[TTL] = 1800 (thêm 422 so với T185);
  API lineage-tree, root-ancestor, ancestor-spine không 404 với TTL-only person;
  _t86_person_info fallback sang ttl_persons với source_type='ttl_local';
  api_dila_persons_search UNION ttl_persons khi có query q;
  Rollback: xem bên dưới.
---

## Bối cảnh

DILA và Marcus chỉ bao phủ truyền thừa Hán văn (~thế kỷ 15 trở về trước).
Sau khi dòng Thiền Tông truyền sang Việt Nam, các thiền sư VN KHÔNG có trong
DILA. Toàn bộ thông tin dòng truyền VN chỉ có trong TTL files tiếng Việt —
ghi chép rải rác qua các đời tổ sư, chưa phải dữ liệu học thuật chuẩn như DILA.

## Kết quả

| Metric | Giá trị |
|--------|---------|
| ttl_persons (danh tăng VN) | 211 |
| VN edges mới vào assertions | +422 |
| VN edges vào consensus | 422 (T186_TTL_VN) |
| is_default_visible | 0 (ẩn mặc định, bật bằng ?include_single=1) |
| source_badge | 'TTL-VN' |
| agreeing_source_count | 1 |

## Ví dụ

**Bạch Vân Không Độ** (bach_van_khong_do):
- DILA: KHÔNG CÓ
- ttl_persons: `name_vi='Bạch Vân Không Độ', source='TTL_LOCAL'`
- consensus: 6 thầy + 6 đệ tử, source_badge='TTL-VN', is_default_visible=0
- Khi search "Bạch Vân" → xuất hiện trong kết quả với badge TTL local
- Khi click vào node → lineage-tree render được (không 404)

## API thay đổi (app.py)

| Chỗ | Thay đổi |
|-----|---------|
| `_t86_person_info` | Fallback sang `ttl_persons` nếu không có trong `people`; thêm `source_type='ttl_local'` |
| `api_monk_lineage_tree` | Guard `OR ttl_persons WHERE id=?` |
| `api_monk_root_ancestor` | Guard `OR ttl_persons WHERE id=?` |
| `api_monk_ancestor_spine` | Guard `OR ttl_persons WHERE id=?` |
| `api_dila_persons_search` | UNION ttl_persons khi có query q, field `note` và `source_type` |

## Rollback

```sql
-- Xóa VN-only edges khỏi consensus
DELETE FROM lineage_edge_consensus WHERE migration_marker='T186_TTL_VN';

-- Xóa VN-only assertions (chỉ những cái có ref là TTL slug không phải DILA ID)
DELETE FROM lineage_edge_assertions WHERE source_code='TTL'
  AND (subject_person_id NOT LIKE 'A%' OR object_person_id NOT LIKE 'A%');

-- Xóa bảng ttl_persons
DROP TABLE IF EXISTS ttl_persons;
```

Code: `git revert --no-edit <sha_T186>`

## Files

- **New:** `scripts/etl_ttl_persons.py`
- **New:** `tasks/T186-ttl-persons-vn-lineage.md`
- **Modified:** `app.py` (4 guards + _t86_person_info + search)
- **Modified DB:** `data/lineage.db` (ttl_persons, lineage_edge_assertions, lineage_edge_consensus)
