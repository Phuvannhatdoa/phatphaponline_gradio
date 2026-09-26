---
id: T101
title: Graph/Nexus Bug Fix — Tên hiển thị + Label Collision
module: Nexus / Graph / UI
priority: high
status: done
depends_on: []
created: 2026-09-09
updated: 2026-09-23 (DONE — admin xác nhận)
done_when: Admin xác nhận tất cả acceptance criteria bên dưới pass trên live UI
---

## Mô tả

Fix 5 bugs phát hiện trong Nexus grouped view và API places/graph của Thiếu Lâm Tự:

- **BUG-001**: Nexus center `label_zh` trả về `少室寺` thay vì `少林寺`
- **BUG-004**: `api_places_graph` curated nodes (Bồ Đề Đạt Ma, Nhị Tổ) trả 0 node
- **BUG-005**: Dynasty subgroup hiển thị sai (đã fix session trước)
- **Typo**: A003881 `name_vi='Nhì Tổ'` → `'Nhị Tổ'`
- **Tên biệt danh**: A001361 hiển thị 'Bích Quan Bà La Môn' thay vì 'Bồ Đề Đạt Ma'
- **Nexus label collision**: Labels chồng lên nhau trong grouped view 99 nodes

## Nguyên nhân gốc

- BUG-001/004: Server chưa reload sau khi fix code session trước
- Typo: DB `people.name_vi` sai
- Tên biệt danh: `api_places_graph` dùng `p.name_vi` từ `people` table thay vì `_t86_resolve_display_name`
- Label collision: vis.js render labels gốc, không có cơ chế tránh chồng

## Các thay đổi đã thực hiện

### app.py — Nexus block & Curated block
- Thêm `_t86_resolve_display_name(conn, pid)` vào cả nexus block (~line 4587) và curated block (~line 4622) trong `api_places_graph`
- Backup: `docs/sessions/2026-09-09/app.py.bak_t101_displayname`

### data/lineage.db — DB updates
- `UPDATE people SET name_vi='Nhị Tổ' WHERE id='A003881'` (fix typo Nhì→Nhị)
- `INSERT INTO person_display_names` cho A001361: `display_name_vi='Bồ Đề Đạt Ma'`, `display_name_zh='菩提達摩'`, `verification_status='verified_direct'`

### places.html — Nexus label collision (implement thật 2026-09-23)
- `_nexusStashLabelStyle(nodes)`: lưu màu/size/bold gốc vào `_labelColor/_labelSize/_labelBold`, set `font.color='transparent'` để ẩn vis.js native label
- `_nexusDrawGroupedLabels(ctx)`: canvas-based rendering với priority order (selected → center → group/subgroup → leaf) + `network.getBoundingBox(id)` cho real bounds + `LABEL_COLLISION_PADDING=5` + `CHILD_LABEL_MIN_ZOOM=1.25`
- `_nexusGroupedCenterId`: track center node id cho priority
- afterDrawing hook gọi `_nexusDrawGroupedLabels` — tự re-trigger theo mọi zoom/pan/drag/stabilize
- selectNode/deselectNode → `network.redraw()` để re-render selection ngay
- Constants: `LABEL_COLLISION_PADDING = 5`, `CHILD_LABEL_MIN_ZOOM = 1.25`
- Backup: `docs/sessions/2026-09-23/places.html.bak-t101-label-fix`
- **Note**: hàm `_nexusResolveLabelCollisions` (ghi trong task cũ) chưa từng được implement — claim trong acceptance criteria cũ là sai. Thay hoàn toàn bằng `_nexusDrawGroupedLabels`.

### places.html — Subgroup expand auto-fit (2026-09-23)
- `CHILD_LABEL_MIN_ZOOM`: hạ từ `1.25` → `0.5` — node lá hiện visible ở scale ~0.5+ thay vì phải zoom đến 1.25
- Non-forcedLayout expand branch: thay `network.fit()` toàn bộ bằng `network.fit({ nodes: fitIds })` — sau khi expand subgroup, viewport tự fit về các node person vừa thêm, admin không cần zoom 3 lần thủ công
- Backup: `docs/sessions/2026-09-23/places.html.bak-t101-subgroup-expand-fix`

### places.html — Orthogonal edges + natural scaling fix (2026-09-23)
- `nodeSpacing: 140 → 220` — dynasty nodes cách xa hơn, labels không chồng nhau
- Edge preprocessing trong `_nexusGroupedFinalize`: lưu `_orthoColor/_orthoOpacity`, set vis.js `color: rgba(0,0,0,0)` cho non-mx edges
- Thêm `afterDrawing` handler vẽ cạnh ống nước vuông góc (L-shape): `source.bottom → midY → target.x → target.top`
- `_nexusDrawGroupedLabels` font fix: `var fontSize = (n._labelSize || 12) / scale` → `var fontSize = n._labelSize || 12` (natural scaling — text co với zoom, không bao giờ overflow bbox)
  - Root cause: `/scale` làm fontSize=29.7 world units tại scale=0.373, text rộng 485px trong bbox 197px (ratio 2.47×)
  - Natural scaling: vis.js đã size bbox để chứa đúng labelSize world units → text luôn fit
- `smooth: { type: 'curvedCW' }` → `smooth: false` (vis.js edges transparent, canvas renderer xử lý)
- Backup: `docs/sessions/2026-09-23/places.html.bak-t101-orthogonal-edges`
- Commit orthogonal edges: `9f561c5` / Natural scaling fix: `a672bd7` / Multi-value dynasty label fix: `be3402a`

### places.html — Multi-value dynasty label fix (2026-09-23)
- Dynasty subgroup loop: split `dyn` theo `[\n\/,，;；]+` → `dynParts`
- Nếu multi-value: `dynLabel = dynParts.join('·') + '\n(' + cnt + ')'` → `'北宋·五代十國\n(1)'`
- Tooltip `title` giữ bản dịch tiếng Việt đầy đủ
- Root cause: `'北宋\n    五代十國'` → `_fmtDynasty` ra 42-char label → collision skip → black rect không chữ

## Acceptance Criteria

- [x] BUG-001: `api_places_graph` nexus center trả `label_zh: 少林寺` ✅ (verified via API)
- [x] BUG-004: curated nodes trả 2 nodes (Bồ Đề Đạt Ma + Nhị Tổ) ✅ (verified via API)
- [x] BUG-005: dynasty subgroup hiển thị đúng ✅
- [x] A003881 name_vi = 'Nhị Tổ' ✅ (DB updated)
- [x] A001361 label = 'Bồ Đề Đạt Ma' ✅ (API confirmed: `label: Bồ Đề Đạt Ma | label_zh: 菩提達摩`)
- [x] Nexus label collision: `_nexusDrawGroupedLabels` canvas-based (priority + getBoundingBox + zoom threshold) implement 2026-09-23
- [x] Admin xác nhận live UI — 'Thiếu Lâm Tự' và 'Nhà Ngũ Đại Thập Quốc' đọc được riêng biệt ✅ (2026-09-23)
- [ ] BUG-002: Script migration identity fix (task riêng — out of scope T101)
- [ ] BUG-003: Script migration confidence fix (task riêng — out of scope T101)

## Blockers

~~Chờ admin xác nhận live UI trước khi set status: done.~~ **DONE 2026-09-23 — Admin confirmed.**
