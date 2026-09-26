# Audit: Logic Mâu Thuẫn Dữ Liệu Tab Truyền Thừa

**Ngày audit:** 2026-09-04  
**Auditor:** Claude Code (session a392f78a)

---

## 1. File liên quan

| File | Vai trò |
|------|---------|
| `daoanh/app.py` | Backend: `_t86_person_conflict()` (line ~4789), `api_monk_lineage_tree` (line ~4862) |
| `daoanh/places.html` | Frontend: render node badge + inspector conflict section (line ~3735–3900) |
| `daoanh/data/lineage.db` | SQLite: bảng `lineage_conflicts_v2`, `marcus_networks`, `people` |

---

## 2. Schema bảng liên quan

### `lineage_conflicts_v2` (40,327 rows)
```
id, person_id, label, name_vi, conflict_type, dila_data (JSON array IDs),
marcus_data (JSON array IDs), dila_count, marcus_count,
is_conflict, resolved, notes, created_at
```
- `conflict_type`: `teacher_set` | `student_set`
- `dila_data`: JSON array DILA person IDs trong relation set đó
- `marcus_data`: JSON array Marcus person IDs trong relation set đó
- `is_conflict=1`: ETL đã đánh dấu là conflict
- `resolved`: 0 = chưa xử lý, 1 = admin đã resolve

### `marcus_networks` (nguồn dữ liệu edges)
```
id, teacher_id, student_id, relation_type, teacher_label, student_label,
source_data, ref (CBETA citation), created_at
```

---

## 3. Cách tính conflict hiện tại (ETL)

ETL so sánh COUNT:
- DILA teacher set ≠ Marcus teacher set → `teacher_set` conflict
- DILA student set ≠ Marcus student set → `student_set` conflict

**Đây là root cause của vấn đề:** bất kỳ khác biệt count nào đều bị gọi là conflict.

---

## 4. Kết quả kiểm tra từng nhân vật

### Bồ Đề Đạt Ma (A001361) — resolved=1
- `teacher_set`: DILA 5 ids, Marcus 1 id, không overlap → direction_disagreement (thật)
- `student_set`: DILA 1 id (A004683), Marcus 5 ids, không overlap → direction_disagreement (thật)
- **Kết luận:** Real conflict — DILA đảo ngược Bát Nhã Đa La (A004683) từ thầy → trò. Đã resolved.

### Giám Trí Tăng Xán (A001601) — resolved=1
- `teacher_set`: DILA=Đạo Tín (A003654), Marcus=Huệ Khả (A003881), không overlap → direction_disagreement
- `student_set`: DILA=Huệ Khả, Marcus=Đạo Tín → direction_disagreement
- **Kết luận:** Real conflict — DILA đảo chiều. Đã resolved.

### Ni Tổng Trì (A019993) — resolved=0
- `teacher_set`: DILA count=0, Marcus=[A001361 Bồ Đề Đạt Ma] → một bên = 0
- `student_set`: DILA=[A001361 Bồ Đề Đạt Ma], Marcus count=0 → một bên = 0
- **Nhìn tổng thể:** DILA ghi A001361 là TRÒ, Marcus ghi A001361 là THẦY → thực chất là direction_disagreement với A001361
- **Phân loại UI:** source_coverage_gap (count=0) nhưng ngữ nghĩa là direction issue

### Đàm Lâm / Đạo Dục / Đạo Phó — chưa query riêng
- Đây là đệ tử của Bồ Đề Đạt Ma, khả năng cũng bị DILA đảo chiều tương tự

### Bát Nhã Đa La (A004683) — resolved=1
- `teacher_set`: DILA=[A001361], Marcus=[] → gap
- `student_set`: DILA=[A008788], Marcus=[A001361] → direction_disagreement
- **Kết luận:** Đã resolved.

---

## 5. Thống kê tổng (40,321 unresolved)

| Loại | Số lượng | % |
|------|----------|---|
| source_coverage_gap (count=0 hoặc có overlap) | 35,442 | 88% |
| direction_disagreement (cả hai > 0, không overlap) | 4,879 | 12% |

**88% các cảnh báo hiện tại là false alarm** — chỉ là một nguồn thiếu dữ liệu.

---

## 6. Phân biệt "thiếu dữ liệu" vs "mâu thuẫn thật"

### source_coverage_gap (không phải mâu thuẫn)
- Một trong hai count = 0
- Ý nghĩa: một nguồn chưa import đủ, không có claim tương ứng
- UI đúng: "Khác biệt phạm vi dữ liệu nguồn" (badge vàng/info)

### direction_disagreement (mâu thuẫn thật)
- Cả hai count > 0, không overlap giữa IDs
- Ý nghĩa: hai nguồn ghi hai người hoàn toàn khác nhau cho cùng vai trò
- UI đúng: "Mâu thuẫn nguồn" (badge đỏ)

---

## 7. Kế hoạch fix

**File cần sửa:**
1. `daoanh/app.py`: Thêm `issue_category` + `severity` vào `_t86_person_conflict()`
2. `daoanh/places.html`: Sửa render badge + inspector theo category

**Không thay đổi:**
- Schema DB (không migration)
- Dữ liệu raw DILA/Marcus
- Bảng `lineage_conflicts_v2`
- Các tab khác, map, URL params
