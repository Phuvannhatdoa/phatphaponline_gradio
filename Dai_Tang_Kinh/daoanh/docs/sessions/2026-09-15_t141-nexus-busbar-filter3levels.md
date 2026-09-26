# Session: 2026-09-15 T141 + T140-addendum — Nexus Bus Bar + Filter 3 mức tin cậy

## Tóm tắt

Phiên này fix 2 vấn đề trong `places.html` (UI only):

1. **T141 — Nexus Bus Bar**: Thay afterDrawing Z-path renderer bằng bus bar design cho Nexus Marcus
2. **T140 addendum — Filter 3 mức**: Tách checkbox "L1-L2 đã xác nhận" → 3 checkbox riêng theo mức nguồn

---

## 1. T141: Nexus Bus Bar

### Vấn đề ban đầu

Tab Nexus → expand "Truyền thừa Marcus" (47+ học trò) → renderer cũ vẽ 47 Z-path độc lập:
- 47 thanh ngang chồng nhau tại cùng y → visual noise
- Row 1 học trò gần thầy nhất có thân mũi tên ngắn tới mức chỉ thấy đầu tên

### Thiết kế Bus Bar

Gom các cạnh theo `sourceId + round(tp.y/200)*200` → mỗi group vẽ:

```
source.bottom
     │ ← trunk 1 lần, dọc xuống busY
─────┼────────────── ← bus bar ngang 1 lần/row, từ min(src.x, left.x) đến max(src.x, right.x)
     │      │      │
     ▼      ▼      ▼  ← drop từng trò + mũi tên tam giác
    trò1   trò2   trò3
```

### Code thay đổi

File `places.html` ~line 6628: thay toàn bộ `afterDrawing` listener cũ (per-edge Z-path)
bằng bus bar renderer mới:

```javascript
// Group edges: (sourceId | targetYRow) → 1 bus bar per group
var groups = {};
mxEdges.forEach(function(edge) {
    var rowKey = Math.round(tp.y / 200) * 200;
    var gk = String(edge.from) + '|' + rowKey;
    if (!groups[gk]) groups[gk] = { srcId: edge.from, rowKey, edges: [] };
    groups[gk].edges.push(edge);
});

// Mỗi group: 1 trunk + 1 bus bar ngang + N drops
Object.keys(groups).forEach(function(gk) {
    // busMinX = min(src.x, leftmost target.x)
    // busMaxX = max(src.x, rightmost target.x)
    // safeBusY: tránh cắt qua oval trung gian
    // trunk: src → busY; bar: busMinX→busMaxX; drop: busY→target.bbTop + arrow
});
```

### safeBusY logic

Scan tất cả node bboxes giữa startY và repEndY → đẩy safeStart qua cuối bbox nằm xen giữa
→ busY = (safeStart + repEndY) / 2 → không cắt oval label trung gian.

---

## 2. T140 addendum: Filter 3 mức tin cậy

### Vấn đề

Checkbox cũ: "✓ Chỉ cạnh L1–L2 đã xác nhận" — user không biết L1/L2/L3 nghĩa gì.

### Giải pháp

Tách thành 3 checkbox với mô tả plain-language:

| ID cũ | ID mới | Label | Nghĩa kỹ thuật |
|-------|--------|-------|----------------|
| `lineage-filter-verified` | `lineage-filter-tl1` | ✓ MARCUS ghi nhận | trust_level = L1 |
| (không có) | `lineage-filter-tl2` | ✓ DILA xác nhận | trust_level = L2 |
| (không có) | `lineage-filter-tl3` | ~ Chưa đối chiếu nguồn | trust_level = L3 hoặc null |

**Hành vi filter:** Nếu tick ≥1 ô → chỉ giữ cạnh khớp mức đó (OR logic). Không tick = hiện tất cả.

**Tooltip hover:** Mỗi checkbox có `title=` giải thích đầy đủ không cần đọc jargon.

**Ghi chú deviation từ T140 spec:** T140 ban đầu yêu cầu "giữ ID checkbox cũ `lineage-filter-verified`".
Thay đổi này phá vỡ ID đó → update logic `_applyLineageFilters` đọc 3 ID mới thay vì ID cũ.
Không còn backward-compat với `lineage-filter-verified` (đã xoá khỏi HTML + JS).

---

## Files touched

- `daoanh/places.html` (duy nhất — UI)
- `tasks/T141-nexus-busbar-truyenthua-arrows.md` (mới)
- `docs/sessions/2026-09-15_t141-nexus-busbar-filter3levels.md` (này)
- `docs/tasktodo.md`
- `docs/ROLLBACK.md`

## Rollback

- Code commit `d49c48c`: `git revert --no-edit d49c48c`
- Không có DB/API/Schema change nên không cần rollback data.
