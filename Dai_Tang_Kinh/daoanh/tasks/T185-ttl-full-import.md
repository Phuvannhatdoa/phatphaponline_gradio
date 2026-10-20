---
id: T185-ttl-full-import
title: "T185 — ETL Full Import 1038 TTL files vào DB (nguồn thứ 3: ttl_asserted)"
module: Lineage / Data Pipeline
priority: high
status: done
owner: claudecode
depends_on: [T158-lineage-evidence-architecture]
created: 2026-09-28
updated: 2026-09-28
done_at: "2026-09-28 (4-phase ETL APPLY; 1378 TTL assertions; 181 edges ttl_asserted=1; 167 edges 3+ nguồn; Huệ Năng→Hoài Nhượng: DILA+Marcus+TTL verified; commit T185)"
plan_approved_at: "2026-09-28 (Admin: 'Đồng ý build, hãy lưu logs, gitcommit và update các thông tin của các task mới vào các .md files tương ứng.')"
done_when: |
  Script etl_ttl_full_import.py 4 phases hoàn chỉnh (--dry-run + --apply + --phase N);
  1028 TTL files parse thành công (10 encoding errors bỏ qua);
  vn_person_authority: +22 records mới;
  vn_person_relations: +2054 records (2138 total);
  lineage_edge_assertions[TTL]: 1378 rows;
  lineage_edge_consensus[ttl_asserted=1]: 181 edges;
  lineage_edge_consensus[3+ nguồn]: 167 edges;
  Huệ Năng (A001719) → Hoài Nhượng (A004015): source_badge='DILA, Marcus, TTL', agreeing_source_count=3;
  Rollback: DELETE TTL assertions + UPDATE ttl_asserted=0.
---

## Mục tiêu

Import toàn bộ 1038 TTL files (ontology truyền thừa Thiền Tông tiếng Việt) vào `lineage.db` làm nguồn xác minh thứ 3 (`ttl_asserted=1`) bên cạnh DILA và Marcus.

## Kết quả

| Metric | Giá trị |
|--------|---------|
| TTL files parse OK | 1028 / 1038 |
| vn_person_authority rows mới | +22 |
| vn_person_relations rows mới | +2,054 |
| lineage_edge_assertions[TTL] | 1,378 |
| ttl_asserted=1 | 181 edges |
| 3+ nguồn (DILA+Marcus+TTL) | 167 edges |
| Ví dụ xác minh | Huệ Năng → Hoài Nhượng: DILA, Marcus, TTL |

## Bugs đã fix trong session này

- **Bug 1 — UNIQUE constraint vn_person_relations**: `INSERT OR IGNORE` thay `INSERT INTO`
- **Bug 2 — vi_index overwrite**: `people` table ưu tiên cao nhất; vpa không overwrite
- **Bug 3 — Exact-match full-title sai** (vpa 'Tôn Giả Đại Giám Huệ Năng' → A029593 thay vì A001719): Fix `build_vi_index` chỉ dùng `people` table, loại bỏ vpa khỏi vi_idx hoàn toàn; fallback slug_to_dila vẫn dùng vpa.dila_id

## Acceptance Criteria

- [x] Script 4-phase với `--dry-run` / `--apply` / `--phase`
- [x] Encoding fix: `Ð` (U+00D0) → `Đ` (U+0110)
- [x] build_vi_index: chỉ từ `people` table (ground truth)
- [x] INSERT OR IGNORE trong P2 và P3
- [x] `TTL|A001719|A004015` tồn tại trong lineage_edge_assertions
- [x] `A001719|A004015` có ttl_asserted=1 và source_badge='DILA, Marcus, TTL'
- [x] Rollback: xóa TTL assertions + reset ttl_asserted=0

## Rollback

```sql
-- Xóa toàn bộ TTL assertions
DELETE FROM lineage_edge_assertions WHERE source_code='TTL';

-- Reset ttl_asserted trong consensus
UPDATE lineage_edge_consensus SET ttl_asserted=0 WHERE ttl_asserted=1;
UPDATE lineage_edge_consensus SET
  agreeing_source_count=(CASE WHEN dila_asserted=1 THEN 1 ELSE 0 END)+
                        (CASE WHEN marcus_asserted=1 THEN 1 ELSE 0 END)+
                        (CASE WHEN lineage_asserted=1 THEN 1 ELSE 0 END),
  consensus_status=CASE WHEN
    ((CASE WHEN dila_asserted=1 THEN 1 ELSE 0 END)+
     (CASE WHEN marcus_asserted=1 THEN 1 ELSE 0 END))>=2
    THEN 'confirmed_2plus' ELSE 'single_source' END;
```

## Files

- **New:** `scripts/etl_ttl_full_import.py` — ETL pipeline chính
- **New:** `docs/sessions/2026-09-28/t185-ttl-full-import.log` — session log
- **New:** `tasks/T185-ttl-full-import.md` — task này
- **Modified DB:** `data/lineage.db` — vn_person_authority, vn_person_relations, lineage_edge_assertions, lineage_edge_consensus
