# Báo cáo so sánh ZTJ ↔ PTDA (chỉ đọc)

Nguồn ZTJ: `toduongtap-data-normalized.json` (260 node / 220 cạnh).
Nguồn PTDA: `ptda-export/persons.json` (23.285) + `lineage-edges.json` (23.411).

Quy tắc khớp: **dila_id** (chính) → **marcus_id** (phụ). KHÔNG khớp theo tên hiển thị.
Cạnh: ZTJ thầy→trò, PTDA teacher→disciple; chỉ so `dharm_successor_of`.

## Node
| Loại | Số lượng |
|---|---|
| matched | 249 |
| ztj_only | 11 |
| ptda_only | 23036 |
| id_conflict | 0 |

## Cạnh
| Loại | Số lượng |
|---|---|
| matched | 197 |
| ztj_only | 23 |
| ptda_only | 23214 |
| direction_conflict | 0 |
| predicate_conflict | 0 |

## Nguồn cho cạnh khớp (matched edges)
- ZTJ + DILA cùng xác nhận: **197**
- ZTJ + MARCUS cùng xác nhận: **197**
- Đủ điều kiện cây mặc định (>=2 nguồn): **197**
- Trong đó ZTJ ghi hướng 'unknown': **6**

## Xung đột / khác biệt cần xem tay
- label_mismatch: **217**

## Ghi chú
- Khớp chính bằng dila_id; khớp phụ bằng marcus_id (không bao giờ khớp theo tên).
- ZTJ edge = thầy→trò; PTDA from_dila_id→to_dila_id = thầy→trò; match phải cùng chiều.
- predicate_conflict = 0: ZTJ không mang trường predicate; PTDA luôn dharm_successor_of.
- default_tree_eligible = True khi >=2 nguồn độc lập cùng chiều (consensus_count>=2).
- HTML chỉ vẽ cây con PTDA quanh phần trùng lặp (đủ ngữ cảnh, nhẹ); dữ liệu đầy đủ ở JSON/CSV.
