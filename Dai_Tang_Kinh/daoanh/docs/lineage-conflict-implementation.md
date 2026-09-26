# Implementation: Phân loại Conflict Tab Truyền Thừa

**Ngày:** 2026-09-04  
**Session:** a392f78a  
**Audit doc:** [lineage-conflict-audit.md](lineage-conflict-audit.md)

---

## Thay đổi

### 1. `daoanh/app.py` — `_t86_person_conflict()` (line ~4789)

**Trước:** SELECT chỉ lấy `dila_count, marcus_count`; trả về dict không có `issue_category`.

**Sau:** SELECT thêm `dila_data, marcus_data`; phân loại mỗi row:

| Điều kiện | `issue_category` | `severity` |
|-----------|-----------------|-----------|
| `dila_count == 0` hoặc `marcus_count == 0` | `source_coverage_gap` | `info` |
| Cả hai > 0 VÀ có IDs chung (overlap) | `source_coverage_gap` | `info` |
| Cả hai > 0 VÀ không overlap | `direction_disagreement` | `warning` |

Return dict bổ sung 2 field: `issue_category`, `severity`.

---

### 2. `daoanh/places.html` — Node badge

**Trước:** Mọi conflict → badge đỏ `⚠ N mâu thuẫn`.

**Sau:**
- `direction_disagreement` → badge đỏ `⚠ N mâu thuẫn nguồn`
- `source_coverage_gap` (và không có direction_disagreement) → badge vàng nhỏ `ℹ Khác biệt nguồn`
- Không có conflict → không có badge (như cũ)

---

### 3. `daoanh/places.html` — Node tooltip title

**Trước:** `⚠ Có mâu thuẫn dữ liệu. [label]`

**Sau:**
- direction_disagreement → `⚠ Có mâu thuẫn nguồn dữ liệu. [label]`
- source_coverage_gap only → `ℹ Khác biệt phạm vi nguồn. [label]`
- Không conflict → `[label]`

---

### 4. `daoanh/places.html` — Edge màu đỏ

**Trước:** Edge đỏ nếu BẤT KỲ endpoint nào có `conflicts.length > 0`.

**Sau:** Edge đỏ chỉ khi endpoint có `direction_disagreement` (mâu thuẫn thật).

---

### 5. `daoanh/places.html` — Inspector conflict section

**Trước:** Tất cả conflict hiển thị màu đỏ `⚠ N mâu thuẫn dữ liệu (DILA vs Marcus)`.

**Sau:** Tách thành 2 nhóm riêng:

**Nhóm direction_disagreement (đỏ):**
```
⚠ N mâu thuẫn nguồn (DILA vs Marcus)
• Mâu thuẫn danh sách thầy — DILA: X · Marcus: Y
```

**Nhóm source_coverage_gap (vàng):**
```
ℹ N khác biệt phạm vi nguồn
• Khác biệt phạm vi danh sách thầy (DILA: 0 · Marcus: 1) — Marcus có quan hệ được ghi nhận; DILA chưa có record tương ứng
```

---

## Tác động thực tế

- **Trước:** 40,321 badges đỏ `⚠ mâu thuẫn`
- **Sau:** ~4,879 badges đỏ (direction_disagreement thật) + ~35,442 badges vàng `ℹ Khác biệt nguồn`
- **Giảm 88% false alarm** màu đỏ

---

## Không thay đổi

- Schema `lineage_conflicts_v2` — không migration
- Dữ liệu DILA/Marcus raw
- Logic resolved=1 (các conflict đã admin resolve vẫn bị ẩn hoàn toàn)
- Các tab khác, map, search

---

## Rà đặc tả "Lineage Consensus Engine" (2026-09-09) — Gap & xác nhận

Làm theo đặc tả T109 cũ (header nhầm "T115"). Kết quả đối chiếu với hạ tầng hiện hữu:

| Yêu cầu đặc tả | Thực trạng |
|---|---|
| Pool `lineage_conflicts_v2` (40,327) + dila_data/marcus_data | ✅ có sẵn |
| `resolutions_log` (thời gian / người / lý do) | ✅ có sẵn (`resolved_at`·`resolved_by`·`notes` → `chosen_source`/`previous_source`) |
| UI Quản trị tranh chấp | ✅ `admin/conflicts.html` + `/daoanh/api/admin/lineage-conflicts` (resolve) |
| Audit không xóa lịch sử | ✅ `en_audit_log` (editor/evidence/created_at) |
| "Không lọt ra truy vấn chính thức" (Data Lock) | ✅ hệ quả kiến trúc — `v_assertions`/query tách biệt pool (additive) |
| Human-in-the-loop / không tự gộp | ✅ khớp nguyên tắc T109 (chỉ Admin phê) |

### Gap thật (2)
1. **Authority Score chưa render ở UI:** `admin/conflicts.html` hiển thị dila_data/marcus_data nhưng chưa hiện Score. Nguồn sẵn: `source_authority` (DILA=100 · MARCUS=60) — JOIN read-only, **additive, Zero-ALTER**. → (tùy chọn) task T117 nếu Lee cần UI đúng nguyên văn.
2. **Không có cờ `lock` tên riêng:** hiện dùng `is_conflict`/`resolved`; tính năng "Data Lock" vốn là hệ quả additive (pool tách biệt) — KHÔNG cần cờ mới (tránh phình, Zero-ALTER).

### Cam kết
- KHÔNG tạo `CONFLICT_ENGINE_SPEC.md` (trùng file này + lineage-conflict-audit.md) — đặc tả là cam kết quản trị, đã phủ.
- KHÔNG re-open T109/T115; không tự gộp; không xóa lịch sử.
