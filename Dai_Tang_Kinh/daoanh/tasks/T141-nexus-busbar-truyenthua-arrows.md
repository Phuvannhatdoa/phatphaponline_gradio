---
id: T141
title: "Nexus Bus Bar — Mũi tên Truyền Thừa Marcus dùng shared horizontal bus bar thay Z-path riêng từng cạnh"
module: places.html (UI only — API/Schema/DB NONE)
priority: high
status: done
created: 2026-09-15
updated: 2026-09-15
depends_on: T140 (Nexus panel đã có, afterDrawing listener tồn tại)
done_when: Mỗi row học trò cùng thầy chung 1 thanh bus bar ngang · thân mũi tên dài nhìn thấy rõ · không còn Z-path riêng chồng lên nhau.
---

# T141 — Nexus Bus Bar: Mũi tên Truyền Thừa Marcus

## Vấn đề (bug user report)

Tab Nexus → click nhóm "Truyền thừa Marcus" → expand hiện cây thầy-trò.
Renderer cũ (`afterDrawing`) vẽ mỗi cạnh thầy→trò như 1 đường Z-path độc lập:
- 47 cạnh → 47 thanh ngang chồng lên nhau cùng y-level → trông như 1 đường dày nhòe
- Học trò row 1 (gần thầy nhất) có thân mũi tên rất ngắn, trông như chỉ có đầu tên

User yêu cầu: "cho cùng 1 đời chung 1 thầy thì chung 1 line hàng ngang, thanh mũi tên truyền thừa phải dài, thấy cạnh chứ ko chỉ có mũi tên như line 1"

## Giải pháp: Bus Bar Design

Thay thế per-edge Z-path bằng bus bar layout:

```
Thầy (y=0)
  │  trunk dọc từ thầy xuống bus bar
  │
──┬──────────────┬──────────────┬──  ← bus bar ngang, 1 thanh/row
  │              │              │
  ▼              ▼              ▼      ← drop + mũi tên xuống từng trò
 Trò1           Trò2           Trò3   (y=180)
```

**Group logic:** gom các cạnh có cùng `sourceId + targetYRow` (round tp.y/200) → 1 bus group.
- 1 trunk dọc từ source → busY
- 1 thanh ngang từ min(source.x, leftmost target.x) → max(source.x, rightmost target.x)
- Từng trò: drop dọc từ busY → target.bbTop + mũi tên

**safeBusY:** tránh horizontal bar cắt qua oval label trung gian bằng cách push safeStart qua
các node bbox nằm giữa startY và repEndY.

**Tọa độ:** dùng `getBoundingBox()` cho điểm tiếp xúc oval border (không phải center).

## Files touched

- `daoanh/places.html` — thay afterDrawing listener trong `_nexusRenderGrouped` (duy nhất)

## Rollback

Chỉ `places.html`:
```
git revert --no-edit d49c48c
```
Không đụng DB/API/Schema. Commit `d49c48c` (2026-09-15).

## Acceptance

- [x] Học trò cùng row → chung 1 thanh ngang (không còn thanh riêng/cạnh)
- [x] Trunk dọc từ thầy (center) xuống bus bar dài nhìn thấy rõ
- [x] Drop từ bus bar xuống từng trò có thân dài, không chỉ là đầu tên
- [x] Khi teacher→center: L-shape path đúng (không phải đường dọc thẳng đứng bỏ qua ngang)
- [x] Không chồng chéo thanh ngang giữa các row
- [x] Arrow chạm vành oval border (getBoundingBox), không đâm vào tâm label
