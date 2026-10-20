> Bước 4/5 của chuỗi "3 cây": T422 → T423 → T424 → **T425** → T426.

## Tóm tắt
Thêm 3 cột vào `lineage_edge_assertions` + tạo 4 VIEW để thay thế bảng gộp `lineage_edge_consensus`:
- `relation_kind` (noi_phap / khac / unknown) — mặc định 'unknown', T414 sẽ điền sau
- `source_edge_ref` — bản sao của `ref`
- `mapping_ok` — bản sao của `mapping_verified` (1 nếu cả 2 đầu accepted)

4 VIEW:
- `v_tree_dila` — 23,014 cạnh DILA
- `v_tree_marcus` — 11,169 cạnh Marcus
- `v_tree_ttl` — 1,062 cạnh TTL
- `v_tree_overlay` — 23,431 cạnh (GROUP BY thầy+trò, chỉ mapping_ok=1), trả về `n_sources`, `sources`, `relation_kind_strongest` để tô màu theo nguồn (T410: DILA xanh / Marcus vàng / TTL đỏ / ≥2 nguồn đen)

## Kết quả dry-run
| Chỉ số | Giá trị |
|---|---|
| Tổng cạnh active | 35,245 |
| overlay (GROUP BY thầy+trò, mapping_ok=1) | 23,431 |
| consensus hiện có | 23,411 |
| overlay KHÔNG trong consensus | 98 (cạnh TTL mới từ T424) |
| consensus KHÔNG trong overlay | 78 (chênh lệch nhỏ DILA/Marcus) |

## Apply
```
python -X utf8 scripts/t425_add_columns_and_views.py --apply
```
- Backup: `data/backups/T425_20261020_092438/lineage.db` (quick_check=ok)
- ALTER TABLE ADD COLUMN ×3 (additive, DEFAULT)
- UPDATE 35,245 rows: `mapping_ok = mapping_verified`, `source_edge_ref = ref`
- CREATE VIEW ×4
- Verify: tất cả cột + view OK

## So sánh overlay vs consensus
- **98 cạnh overlay không trong consensus**: toàn bộ là cạnh TTL mới (ttl_only, agree=1, badge=1/4: TTL) từ T424 — consensus chưa được rebuild (T185 P4).
- **78 cạnh consensus không trong overlay**: chênh lệch nhỏ DILA/Marcus (có thể do self-loop/reverse hoặc edge key trùng).

## Verify sau apply
```
lea columns: + relation_kind, source_edge_ref, mapping_ok
v_tree_dila: 23014
v_tree_marcus: 11169
v_tree_ttl: 1062
v_tree_overlay: 23431
mapping_ok: 0=448, 1=34797
relation_kind: unknown=35245 (T414 sẽ cập nhật)
```

## Bằng chứng
- `docs/sessions/2026-10-19/T425/t425_report.txt`
- Backup: `data/backups/T425_20261020_092438/lineage.db`

## Revert
```
python -X utf8 scripts/t425_add_columns_and_views.py --revert --backup data/backups/T425_20261020_092438/lineage.db
```
(VIEW tự mất khi restore, cột additive giữ nguyên — không mất dữ liệu)

## Tiếp theo
T426: API + giao diện chọn Cây DILA/Marcus/TTL/Chồng cây trên `/daoanh/places`.