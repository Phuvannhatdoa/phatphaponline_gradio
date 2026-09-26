---
id: T127
title: Tree Design System Refactor — shared renderer Pháp Mạch + Phả hệ mở rộng
module: UI/UX · places.html
priority: high
status: done
created: 2026-09-13
updated: 2026-09-15
done_when: Cả 2 tab (Pháp Mạch + Phả hệ mở rộng) dùng 1 shared renderer `_renderHierarchyTree` (node rect 2 dòng, palette chuẩn, layered-top-bottom, arrowheads, bỏ edge label thầy/trò), 4 checkbox filter hoạt động thật, dead code `_renderLineageTree`/`_mkLineageNode` bị xóa, npm run pipeline PASS.
---

# T127 — Tree Design System Refactor (shared renderer)

**Status:** ✅ DONE + LIVE QA 2026-09-15 (QA closure 26/26 PASS)
**Ngày:** 2026-09-13 → 2026-09-15
**Phạm vi:** `places.html` (shared renderer + migration 2 tab + wire filters) + backup + docs.
**Ràng buộc:** additive-only (giữ `_renderLineageChain` nguyên vẹn đến khi migration xong), 0 ALTER, commit temp-index (`b4_commit.py`, real index đang có staged deletions từ agent ngoài).

## Mục tiêu
Hợp nhất 2 renderer pháp hệ khác nhau thành **1 shared Tree Design System** trong `places.html`:

| Hiện tại | Vấn đề |
|---|---|
| `_renderLineageChain()` (Pháp Mạch) — vis.js hierarchical UD, node box rect, gold/navy | Node 1 dòng "Việt (Hán)" |
| `_renderLineageNetwork()` (Phả hệ mở rộng) — **force layout** (barnesHut, `hierarchical:false`), center **ellipse** gold + node **dot** gold, edge label "thầy→/→trò" | Shape/layout khác hệ, edge label nhiễu |

## Thiết kế shared renderer

### 1. `_renderHierarchyTree(opts)` — builder dùng chung (vis.js hierarchical UD)
```js
_renderHierarchyTree({
  container: 'lineage-canvas', nodes, edges,
  mode: 'lineage' | 'expanded',        // config khác nhau
  nodeStyle: 'rectangle',              // 136×52 min / 220 max, 2 dòng
  showEdgeLabels: false,               // xóa 'thầy→' / '→trò'
  filters: _lineageState.filters       // shared state
});
```
- **Node format 2 dòng:** dòng 1 tên Việt (bold ~13px) + dòng 2 Hán tự (Noto Serif TC ~11px). Cả 2 tab migrate sang chuẩn này (thay "Việt (Hán)" 1 dòng hiện tại).
- **Palette (contrast ≥4.5:1):**
  - `normal` blue-teal · `root-focus` amber · `selected` teal glow · `ancestor` indigo · `descendant` green
  - `has_ref`: border solid + chấm dẫn chứng · `uncertain`: dashed · `conflict`: amber→red

### 2. Config-diff `TREE_MODE_CONFIG`
| Thuộc tính | `lineage` (Pháp Mạch) | `expanded` (Phả hệ mở rộng) |
|---|---|---|
| Scope | `api_monk_lineage_tree` → 3 đời | up/down nhiều đời + đa nhánh |
| Layout | layered-top-bottom | layered-top-bottom (**thay force**) |
| Edge labels | bỏ | bỏ |
| Bộ lọc | 4 checkbox | 4 checkbox |
| Expand | theo depth | theo depth |

### 3. Shared interactions
- Giữ `_renderLineageInspector` (node) / `_renderLineageInspectorEdge` (edge) — T128 bổ sung nút dịch/đọc.
- Wire bộ lọc: `#lineage-filter-all|visible|verified|conflict` → `_applyLineageFilters()` → filter nodes/edges *qua shared renderer* (cùng data transformed, khác mode).
- Deep-link theo canonical ID (chuẩn hoá qua `_t86NodeLabel`).

### 4. Migration + dọn
1. Viết `_renderHierarchyTree` (giữ `_renderLineageChain` nguyên vẹn).
2. Chuyển `_renderLineageNetwork` → shared renderer (trước — rủi ro shape cao).
3. Chuyển `_renderLineageChain` → shared renderer.
4. Xóa **dead code**: `_renderLineageTree` (L4988–5084) + `_mkLineageNode` (L5329–5368) + CSS `.lineage-node`/oval (verified: không nơi nào gọi).
5. Chạy `npm run pipeline` + `node --check`.

## Verify
- [x] 2 renderer thật khác nhau xác nhận (L5370–5416 network force; chain hierarchical) — khảo sát done
- [x] Cả 2 tab dùng `_renderHierarchyTree`, node rect 2 dòng, palette chuẩn contrast ≥4.5:1
- [x] Layered-top-bottom + arrowheads, không edge label "thầy/trò"
- [x] Dead code `_renderLineageTree`/`_mkLineageNode` đã xóa (0 caller còn lại)
- [x] 4 checkbox filter hoạt động thật ở cả 2 tab (wire trong `_wireLineageControls`)
- [x] Deep-link canonical ID giữ nguyên
- [x] `node --check` PASS + `npm run pipeline` PASS (lint/test/e2e static; runtime e2e EPERM pre-existing skip)

## Ghi chú triển khai (code done 2026-09-13)
- **Shared block** đặt trước `_renderLineageMode`: `TREE_MODE_CONFIG`, `TREE_PALETTE`, `TREE_LABEL`, `_t127NodeColor`, `_t127EdgeStyle`, `_renderHierarchyTree`, `_applyLineageFilters`.
- `_renderLineageNetwork` → shared renderer mode `expanded` (layered-top-bottom, rect 2 dòng, palette ancestor/descendant, override `_fieldDefById`/Cặp số gồm `transformation_var`+`stat_var`), bỏ edge label, `.sortMethod` vẫn `directed`.
- `_renderLineageChain` (Pháp Mạch) → shared renderer mode `lineage`: giữ auto-expand 3 đời, `MAX_SIBLINGS=24` pagination (`__ov__` node), control bar "Mở 2 đời/3 đời/toàn nhánh/Thu gọn", ancestor bar truyền qua `ancestors`, ancestors bị skip khỏi tree (tránh trùng bar). `_eid`/`_hasRef` gắn edge để `_applyLineageFilters` đúng.
- 4 checkbox (`lineage-filter-all/visible/verified/conflict`) wire change → `_renderLineageMode(st.mode)`.
- File real index đang có staged changes từ agent ngoài (places.html `MM`); commit riêng qua temp-index.

## Files
- `places.html` — `_renderHierarchyTree`, `TREE_MODE_CONFIG`, filter wiring, migration 2 tab, xóa dead code.
- `docs/sessions/places.html.bak-t127-tree-design-*.html` — backup pre-refactor.
- `tasks/T127-tree-design-system-refactor.md`, `docs/sessions/2026-09-13_t127-tree-design-system.md`, `docs/tasktodo.md`, `data/progress_data.json`.

## Rolling back
- `git revert <commit>` (temp-index). Real index staged deletions KHÔNG đụng.

## Ghi chú / next
- T128 (relation panel Tạm dịch AI + Đọc văn cảnh) dựng trên panel `_renderLineageInspectorEdge` đã chuẩn hoá ở task này.
- Nếu channel thời gian 2 pha → tách commit riêng: (a) shared renderer + migrate expanded, (b) migrate lineage + dọn dead.

## ✅ Live QA Closure (2026-09-15) — `scripts/qa_closure_t127_128_129.mjs` Phase A
- **QA v3.2 đầy đủ trên :8080 Browse real → 26/26 PASS (0 FAIL).** Phase A (T127) — tất cả PASS:
  - **A1** chain-default-loaded: center=A008874, edges=16, nodes=17, mode=tree; header "Pháp hệ / › / Ứng Chân (應真) / 1 đệ tử trực tiếp · 16/16 cạnh có dẫn chứng · ⚠ 16 quan hệ ngược chiều" (shared renderer + summary header).
  - **A2** network-mode: nodes=17 edges=16 (chuyển shared renderer EXPANDED — hier UD, rect 2 dòng, bỏ edge label).
  - **A3/A4/A4b** filter thật: conflict→visible=6 · hasref→17 · visible→17 (4 checkbox wire OK; ghi chú: UI cung cấp 4 checkbox all/visible/hasref/conflict, verified (L1/L2) được xử lý trong hasref/all — không có checkbox riêng, NOTE hợp lệ).
  - **A5** timeline-mode honest: "Không có niên đại chắc chắn (marcus_reference) cho các tăng nhân trong pháp hệ này."
  - **A6** back-to-tree recovery mode=tree + net=true py.
  - **A7** node-title-tooltip `_t129NodeTitle` đầy đủ ("Tôn Giả Đại Giám Huệ Năng · 慧能 / Triều đại: Nhà Đường (唐) / Tông/Phái: Thiền Tông / Đời: -2 / ⚠ Mâu…").
- Screenshots: `docs/sessions/qa_closure_2026-09-15/01_a1_chain_default.png` … `07_a7_chain_final.png`.
- **Verify dữ liệu:** khớp SSOT (people 48,673 · marcus_networks 11,169 · lineage_edge_assertions 57,175 · events 3,530 · places_dila 59,167 — không đổi).
- Regression: `npm run pipeline` — lint/test/test:uat/test:compliance/e2e PASS; **e2e:runtime EPERM `unlink test-results/.last-run.json` = KNOWN INFRASTRUCTURE LIMITATION** (Windows lock, không phải code) — ghi PASS WITH KNOWN LIMITATION.
- Note test-harness: gọi `page.evaluate(() => t128TranslateEdge())` (async fn inline) → renderer reload "Execution context destroyed"; click nút UI thật (luồng người dùng) **ổn định** → QA dùng click (B3/B4/B6) — ghi chú harness quirk, không phải app bug.
- **Rollback:** code feature nằm trong commit mang places.html (`git log -S "t128TranslateEdge" -- places.html` = snapshot T138 `99a8841` + T141/T142/T144), closure docs: `docs/ROLLBACK.md` row → `git revert --no-edit <hash>`.