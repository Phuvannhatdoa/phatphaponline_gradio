---
id: T90
title: Đồ Thị — Text-Hub Routing + Hierarchical Layout
module: places
priority: high
status: done
depends_on: [T16]
created: 2026-09-03
updated: 2026-09-03
done_when: Graph shows place → Cao Tăng Truyện hub → person with LR hierarchy; nearby places shown as chips
---

## Mô tả
Tái cấu trúc Tab Đồ Thị của places.html:

1. **Text-hub edge routing**: persons kết nối qua text node (Tục/Tống/Minh Cao Tăng Truyện) thay vì edge thẳng từ place → person. Cho thấy timeline thời đại rõ ràng.

2. **Remove LIMIT**: Bỏ LIMIT 8/6/[:6] để hiển thị toàn bộ texts, nearby places, persons.

3. **Hierarchical layout LR**: Vis.js hierarchical direction LR, physics disabled. Level 0=place, Level 1=text hub, Level 2=person. Nearby places tách riêng ra chip strip `#gmp-nearby`.

4. **Nexus tab main panel**: Tab Nexus dùng full-width `#nexus-main-panel` cùng pattern với Đồ Thị.

## Acceptance criteria
- [x] Graph Thiếu Lâm Tự hiển thị 3 text hubs (唐/宋/明 Cao Tăng Truyện) ở level 1
- [x] 24 monks phân tán theo text hub tương ứng ở level 2
- [x] 49 địa danh lân cận hiển thị trong chip strip phía trên canvas (clickable)
- [x] Layout LR rõ ràng, không bị force-directed chaos
- [x] Không có duplicate nodes (seenIds filter)
- [x] Nexus tab dùng full-width main panel

## Implementation
`app.py`: api_places_graph
- `_CTT_SH = {'唐高僧傳': '2060', '宋高僧傳': '2061', '明高僧傳': '2062'}`
- `text_node_ids` set để dedup text nodes
- Persons route qua `hub_id` nếu source_book khớp _CTT_SH

`places.html`:
- HTML: `#gmp-nearby` strip (overflow-x: auto)
- `_renderGraphMainPanel`: tách nearbyNodes → chips, hierarchyNodes → vis.js LR hierarchy
- `vis.Network` options: `layout.hierarchical.enabled=true, direction=LR, physics.enabled=false`

## Session log
docs/sessions/2026-09-03_T90_dothi_texthub.md
