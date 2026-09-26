---
id: T158
title: "Lineage Consensus Layer — Đa Nguồn Đồng Thuận Pháp Mạch"
module: Lineage / Pháp Hệ
priority: high
status: done
depends_on: [T157]
created: 2026-09-22
updated: 2026-09-22
done_when: "lineage_edge_consensus table populated, API dùng consensus thay marcus_networks, UI legend và edge inspector hiện source_badge, 12/12 tests pass"
---

## Mô tả

Refactor pháp mạch truyền thừa từ "Marcus = backbone" sang hệ đa nguồn đồng thuận:
- Tạo bảng `lineage_edge_consensus` tổng hợp 4 nguồn (DILA, Marcus, TTL, Lineage)
- Mặc định chỉ hiện `relation_type='dharma_transmission'` với `agreeing_source_count >= 2`
- Block cạnh mâu thuẫn ngược chiều (`opposite_source_count > 0`)
- Thêm `source_badge` ("N/4: Source1, Source2") vào edge data
- Thay legend "Marcus = cấu trúc chính" bằng mô tả consensus
- Backend BFS dùng `_t158_neighbors_consensus` thay `_t86_neighbors`

## Acceptance Criteria

- [x] Bảng `lineage_edge_consensus` được tạo với đúng schema (migration_marker, UNIQUE constraint)
- [x] Backfill từ `lineage_edge_assertions`: 23018 rows (11165 confirmed_2plus, 11853 single_source)
- [x] Test case A001060→A021462: confirmed_2plus, is_visible=1, badge="2/4: Marcus, DILA" ✓
- [x] API `/daoanh/api/monk/<id>/lineage-tree` dùng consensus, trả `source: "consensus:>=2/4..."`
- [x] Edge response có `source_badge`, `agreeing_source_count`, `consensus_status`
- [x] Legend UI: "Mạch mặc định: ≥2/4 nguồn đồng thuận cùng chiều · Nguồn: DILA · Marcus · TTL · Lineage"
- [x] Inspector hiện badge màu xanh cho ≥2 nguồn + verdict context-aware
- [x] 12/12 tests pass (tests/test_t158_consensus.py)
- [x] Script migration idempotent (--stats / --apply / --revert)

## Files thay đổi

| File | Thay đổi |
|------|----------|
| `scripts/t158_consensus_migration.py` | Mới — DDL + backfill + revert |
| `tests/test_t158_consensus.py` | Mới — 12 tests |
| `app.py` | Thêm `_t158_neighbors_consensus`, sửa `api_monk_lineage_tree` |
| `places.html` | 2 legend text + inspector badge + visEdges fields |

## DB Change

`lineage_edge_consensus` table created 2026-09-22:
- Total: 23018 rows
- confirmed_2plus: 11165 (is_default_visible=1)
- single_source: 11853 (is_default_visible=0)

## Commit

`d6b9154` — feat: T158 - Lineage Consensus Layer (2026-09-22)
Revert: `git revert d6b9154` + `python scripts/t158_consensus_migration.py --revert`

## Evidence

API test (direct port 5000):
```json
{
  "source": "consensus:>=2/4 sources (DILA, Marcus, TTL, Lineage)",
  "include_single": false,
  "edge0_source_badge": "2/4: Marcus, DILA",
  "edge0_agreeing_count": 2,
  "edge0_consensus_status": "confirmed_2plus",
  "edge0_relation_type": "dharma_transmission"
}
```
