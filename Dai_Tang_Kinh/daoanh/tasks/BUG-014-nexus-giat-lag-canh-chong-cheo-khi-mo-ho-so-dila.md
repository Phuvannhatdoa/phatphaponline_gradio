---
id: BUG-014
title: "Nexus giật lag + cạnh chồng chéo rối khi click Hồ Sơ DILA — nexus-dila-expand-physics-jitter"
module: Nexus / vis-network
priority: P1
status: in_progress
fix_applied: 2026-09-09
depends_on: []
created: 2026-09-09
updated: 2026-09-09
done_when:
  - Click "Hồ Sơ DILA" không còn hiệu ứng giật/lag kinh khủng
  - Các cạnh (edges) không chồng chéo lên nhau khi expand
  - Animation mở rộng nhẹ nhàng, mượt mà
  - Admin xác nhận DONE
---

## Triệu chứng

Tab Nexus → Click node "Hồ Sơ DILA" →
- Hiệu ứng giật lag kinh khủng (jitter)
- Các nút node văng lung tung rồi mới dừng
- Các cạnh (edges) chồng chéo lên nhau, rối mắt

## Root cause

### 1. Edge overlap — `smooth: { type: 'curvedCW' }`
`curvedCW` bắt tất cả cạnh cong theo cùng một hướng (clockwise). Khi nhiều DILA node
expand ra từ trung tâm, tất cả cạnh nối từ center → các node đều cong cùng chiều → chồng nhau.

**Fix:** Đổi sang `smooth: { type: 'dynamic' }` — vis-network tự chọn hướng cong riêng
cho từng cặp node để minimize overlap.

### 2. Jitter khi expand — physics quá mạnh + spawn quá gần

Khi click "Hồ Sơ DILA" (incremental update path, places.html line ~5900):
- Nodes mới được spawn trong vòng ±15px quanh node g-dila (quá gần nhau)
- Physics bật lại với `repulsion { nodeDistance: 150 }` rất mạnh
- Nodes từ cluster ±15px → repulsion 150px → văng mạnh ra ngoài = jitter
- Timeout 2000ms quá dài → user nhìn thấy toàn bộ quá trình văng

### 3. Physics initial quá mạnh

Initial network: `repulsion { nodeDistance: 150 }` với 0 damping → không có lực cản
→ khi stabilize lần đầu cũng rung lắc

## Fix (places.html)

### Thay đổi 1: Edge smooth (line ~5838)
```diff
- edges: { arrows: { to: { enabled: false } }, smooth: { type: 'curvedCW', roundness: 0.2 } },
+ edges: { arrows: { to: { enabled: false } }, smooth: { type: 'dynamic' } },
```

### Thay đổi 2: Spawn range rộng hơn (line ~5887-5889)
```diff
- n.x = base.x + (Math.random() - 0.5) * 30;
- n.y = base.y + (Math.random() - 0.5) * 30;
+ n.x = base.x + (Math.random() - 0.5) * 80;
+ n.y = base.y + (Math.random() - 0.5) * 80;
```

### Thay đổi 3: Physics expand nhẹ nhàng hơn (line ~5902-5904)
```diff
- _nexusNetwork.setOptions({ physics: { enabled: true } });
- const _tp = setTimeout(function() { ... }, 2000);
+ _nexusNetwork.setOptions({ physics: { enabled: true, solver: 'repulsion',
+     repulsion: { nodeDistance: 100, damping: 0.5 },
+     stabilization: { iterations: 60, fit: false } } });
+ const _tp = setTimeout(function() { ... }, 800);
```

### Thay đổi 4: Initial physics nhẹ hơn (line ~5836)
```diff
- physics: { enabled: true, solver: 'repulsion', repulsion: { nodeDistance: 150 } },
+ physics: { enabled: true, solver: 'repulsion', repulsion: { nodeDistance: 100, damping: 0.4 }, stabilization: { iterations: 150 } },
```

## Fix đã áp dụng (places.html)

- Line 5836: physics `nodeDistance:150` → `nodeDistance:100, damping:0.4, stabilization:{iterations:150}`
- Line 5838: edges `smooth:{type:'curvedCW',roundness:0.2}` → `smooth:{type:'dynamic'}`
- Line 5888-5889: spawn range `30px` → `80px`
- Line 5902-5905: physics re-enable timeout `2000ms` → `800ms`, thêm `damping:0.5`

## Kết quả test JS (2026-09-09)

- Edge smooth confirmed `type:'dynamic'` ✅
- Physics tự tắt sau 800ms (nodes: 25→40 khi expand 15 persons) ✅
- Không có JS errors liên quan ✅

## Acceptance criteria checklist

- [ ] Click "Hồ Sơ DILA" → các nút expand ra nhẹ nhàng, không giật (CHỜ ADMIN CONFIRM real UI)
- [ ] Các cạnh không chồng chéo lên nhau khi expand (CHỜ ADMIN CONFIRM)
- [ ] Admin xác nhận DONE
