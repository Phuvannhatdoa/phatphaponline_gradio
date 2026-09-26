---
id: T144
title: "Nexus: double-click node → set làm root ngay lập tức"
module: places.html (UI only — API/Schema/DB NONE)
priority: high
status: done
created: 2026-09-15
updated: 2026-09-15
depends_on: T143 (sidebar toggle unified)
done_when: Double-click bất kỳ node person/place trong Nexus graph → _nexusSetRoot() được gọi → graph reload với node đó làm root mới.
---

# T144 — Nexus double-click node → set root ngay

## Vấn đề (user report 2026-09-15)

Trước đây để set một node làm root mới trong Nexus, user phải:
1. Single-click node → mở detail panel
2. Bấm nút "✦ Set làm root" trong panel

**Yêu cầu:** Double-click trực tiếp vào label/node trong Nexus → set làm root ngay, không cần qua panel.

## Giải pháp

Thêm `doubleClick` event handler vào vis.js network trong cả hai render path:

### 1. Place-type Nexus (`_renderVisGraph`, line ~3940)

```javascript
network.on('doubleClick', params => {
    if (!params.nodes.length) return;
    const nid = params.nodes[0];
    if (nid === center.id) return;
    const n = nodeMap[nid];
    if (n && n.navigable && (n.group === 'person' || n.group === 'place')) _nexusSetRoot(n);
});
```

### 2. Person-type grouped Nexus (`_nexusGroupedFinalize`, line ~6898)

```javascript
// Double-click any leaf person/place node → set as new Nexus root immediately
_nexusNetwork.on('doubleClick', function(params) {
    if (!params.nodes.length) return;
    const nid = params.nodes[0];
    const node = _nexusGroupedNodesRef.find(function(n) { return n.id === nid; });
    if (!node || !node._nxPerson) return;
    var p = node._nxPerson;
    if (p.navigable && (p.group === 'person' || p.group === 'place')) _nexusSetRoot(p);
});
```

## UX flow

1. User double-click node → vis.js fires `click` (single) → detail panel opens briefly
2. vis.js fires `doubleClick` → handler gọi `_nexusSetRoot(node)`
3. API fetch `/daoanh/api/nexus/<id>?type=<group>` → `renderNexusTab(d)` → graph reload
4. Root mới là node vừa được double-click

## Files touched

- `daoanh/places.html` — JS only (thêm doubleClick listener)

## Rollback

```
git revert --no-edit <this-commit-hash>
```

Không có DB/API/Schema change.

## Acceptance

- [x] Handler code tại `_renderVisGraph` (place-type) — line 3940
- [x] Handler code tại `_nexusGroupedFinalize` (person-type grouped) — line 6898
- [x] Chỉ fire với node có `navigable=true` và `group=person/place`
- [x] Center node bị skip (không set root thành chính nó)
- [x] `_nexusSetRoot()` hoạt động đúng (verified via direct call → graph reload)
- [x] Browser verified: vis.js `doubleClick` event với node A027020 → `_nexusSetRoot(A027020)` ✓
- [x] Browser verified: vis.js `doubleClick` event với node A000490 → `_nexusSetRoot(A000490)` ✓
- [x] Browser verified: vis.js `doubleClick` event với node A001897 → `_nexusSetRoot(A001897)` ✓
- [x] Screenshot: graph header đổi từ "Hoàng Phách Đoạn Tế" → "Bách Trượng Hải" sau double-click
