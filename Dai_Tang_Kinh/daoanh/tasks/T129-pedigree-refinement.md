---
id: T129
title: Phả hệ mở rộng — pedigree refinement (generation, cycle-safe, expand, sort)
module: UI/UX · places.html
priority: high
status: done
created: 2026-09-13
updated: 2026-09-15
depends_on: T127
done_when: Phả hệ mở rộng (mode network) có (1) generation tuyệt đối theo tâm (level normalize ≥0, cùng gen cùng hàng), (2) sort ngang trong gen theo (niên đại→tên), (3) nút mở đời trên/dưới + toàn nhánh + thu gọn, (4) Tâm hoạt động ở network, (5) phát hiện chu trình (Tarjan SCC) → cạnh chu trình loại khỏi cây + footer "Mâu thuẫn/chu trình", (6) node không nối tới tâm bị ẩn + thông báo, (7) hover edge "X truyền pháp cho Y", (8) node title meta (triều đại/niên đại/tông/#thầy/#trò/dẫn chứng/mâu thuẫn); node --check PASS + npm run pipeline PASS.
---

# T129 — Phả hệ mở rộng: pedigree refinement batch

**Status:** ✅ DONE + LIVE QA 2026-09-15 (QA closure 26/26 PASS; C7 edge tooltip fix trong places.html)
**Ngày:** 2026-09-13 → 2026-09-15
**Phạm vi:** `places.html` (+ backup + docs). Backend KHÔNG đổi (data `up=3/down=3` sẵn có).
**Ràng buộc:** additive-only, **0 backend thay đổi**, giữ shared `_renderHierarchyTree` (T127), không đụng git index real (commit temp-index theo yêu cầu), chạy `npm run pipeline` trước review.

## Bối cảnh
Kết quả verify spec 10 mục vs T127: ~80% đã đúng (hierarchical UD, `physics:false`, arrowhead V-H-V vào student, bỏ edge label, evidence solid/dashed). Các khoảng trống còn lại được xử lý trong batch này:

## Mục tiêu (fix rõ)
1. **Generation tuyệt đối theo tâm (network):** `gen[center]=0`; thầy −1,−2…; trò +1,+2… (BFS ngắn nhất, cycle-safe); `level = gen − minGen` (normalize ≥0, vis yêu cầu non-negative) → cùng gen cùng hàng `y`.
2. **Sort ngang trong gen:** (birth_year||death_year → name_vi) — vis UD sắp theo thứ tự chèn → sắp mảng trước khi vẽ, hạn chế cạnh chéo (thay cho Sugiyama đầy đủ; giữ `edgeMinimization/blockShifting/parentCentralization` sẵn có).
3. **Expand controls (network):** control bar `Mở thêm đời trên / Mở thêm đời dưới / Hiện toàn bộ nhánh / Thu gọn`; state `st._netExpand={above:2, below:2, all:false}`; giữ generation/order cũ ổn định khi mở (deterministic level).
4. **Tâm (network):** `#lineage-center` → `_lineageNetwork.focus(center)` (hiện bỏ trống ở network).
5. **Chu trình:** Tarjan SCC trên `st.edges` → cạnh trong SCC size>1 hoặc self-loop = cycle; LOẠI khỏi graph hierarchical (vis không vẽ cycle đúng), đưa vào footer "⚠ Mâu thuẫn/chu trình — điều tra" (chip click → inspector edge).
6. **Node không nối tới tâm:** chỉ giữ connected (reachable qua gen map); số node ẩn hiển thị trong footer note.
7. **Hover edge:** `"X truyền pháp cho Y"` + ref (cả chain lẫn network) qua `_t129EdgeTitle`.
8. **Node title meta:** triều đại / niên đại / tông / đời / #thầy / #trò / số dẫn chứng / ⚠ mâu thuẫn (cả 2 mode) qua `_t129NodeTitle`.
9. (cosmetic KHÔNG làm trong batch này: oval shape, badge "Đang xem", aria keyboard, Fit padding 48 — ghi ở Ghi chú.)

## Khảo sát code (đã xác nhận)
- `_renderLineageNetwork` places.html:5484 — dùng `st.d.nodes` (toàn bộ subtree), `st.edges` (canonical from=teacher→to=student), `teacherOf[e.to]=e.from`, ancSet walk lên; visNodes KHÔNG set `level` hiện tại; `onNodeClick:()=>{}`; không expand.
- `_renderHierarchyTree` places.html:4989 — `options.controls` (DOM trước visDiv) + `options.ancestorBar`; cần thêm `options.footer` (DOM sau visDiv) để gắn research list.
- `_lineageTreeFromEdges`/`_lineageTreeParents` places.html:5179/5192 — kidsOf/par chuẩn; dùng lại cho gen map + reachable.
- `#lineage-center` handler places.html:5824 — mode 'tree' OK, mode 'network' bỏ trống (bug).
- Nút toggle sidebar tái fit sau `requestAnimationFrame` — không đụng.

## Implement (append/override additive)
### Shared helpers (chèn trước `_renderLineageMode`)
- `_lineageGenMap(centerId, kidsOf, par)` — BFS 2 chiều, first-visit-wins.
- `_lineageSccEdges()` — Tarjan trên `st.edges`, trả cạnh cycle.
- `_t129NodeTitle(n,{gen,nT,nS,ev})` — reuse `_fmtDynasty`, `_t86Years`, `TREE_LABEL`.
- `_t129EdgeTitle(parentId, toId, edge)` — "X truyền pháp cho Y".
- `_t129YearOf/_t129NameOf` — sort keys. `_t129EdgeTitle` dùng cho cả chain.

### `_renderHierarchyTree`
- Thêm `options.footer` (accept hàm hoặc node) — append sau visDiv.

### `_renderLineageNetwork` (rewrite additive)
- `st._netExpand` default `{above:2, below:2, all:false}`.
- gen map + reachable set → filter `st.d.nodes`; `level = gen−minGen`; sort theo (level, year, name).
- visEdges: skip cycle edges + edge ngoài keep-set; `_t129EdgeTitle` override title; node title = `_t129NodeTitle(...)` với đếm thầy/trò/dẫn chứng.
- controls = `_netCtrlBar()`; footer = research footer (cycle chips + node bị ẩn note).

### `_wireLineageControls`
- `#lineage-center`: network → `focus(center)`.

### Chain mode (tinh chỉnh title)
- `addEdge` + ancestor edges: override `title` bằng `_t129EdgeTitle`; node `title` dùng `_t129NodeTitle`.

## Verify
- [x] Algorithm unit test **15/15 PASS** (2026-09-13): trích helper thật từ file (không drift) — gen map T=−1/C=0/S1S2=+1/G=+2; cycle rời A↔B loại khỏi gen map + SCC đánh dấu đúng 2 cạnh; edge title "C truyền pháp cho S1" + ref, no-ref → "○ Cần khảo cứu"; node title meta (đời/dynasty/Trò).
- [x] node --check PASS (inline JS places.html, main script ~471k chars, file 565,447B).
- [x] npm run pipeline static PASS (lint ESM + e2e:runtime EPERM pre-existing).
- [ ] Live QA (:8080 Ctrl+F5): chọn tăng nhân có pháp hệ → mode Phả hệ mở rộng → thầy trên/trò dưới, cùng gen cùng hàng; nút mở đời/Thu gọn không nhảy layout; Tâm đưa focus vào giữa; cycle/mâu thuẫn hiện trong footer; hover edge "X truyền pháp cho Y".

## ✅ Live QA Closure (2026-09-15) — Phase C (T129) — QA v3.2: **26/26 PASS (0 FAIL)**
- **C1** generation-map (tâm A003623 = Mã Tổ Đạo Nhất, 294 edges): gen map center=0, nodes=295 edges=294, reachable=295 (cycle-safe BFS, reachable-only). API probe: A003623 lineage-tree nhanh 1.62s/32KB vs chậm 20.91s/525KB — **endpoint chậm cho pháp hệ lớn, KHÔNG phải bug** (test chờ 160s).
- **C3** chain expand: `Mở 2 đời`=142 nodes · `3 đời`=142 · `Toàn bộ nhánh`=295 (min=3 → mở toàn nhánh đầy đủ).
- **C2** generation ordering (network): nodes=295, levels [0..4] non-negative + ascending — cùng gen cùng hàng.
- **C7b** network expand-ctrl: all=295 min=295 (nút điều khiển network OK).
- **C4** center focus: `focus(center)` — scale=1.00 pos={"x":1705,"y":0}.
- **C7** edge-hover-title: `edge#2 "Mã Tổ Đạo Nhất truyền pháp cho Hoài Hải / ● (X79n1557_p0002a12); "` — **BUG THẬT đã fix**: `_renderHierarchyTree` `cleanEdges` strip `{id, from, to}` làm mất title mọi mode → fix additive `{id, from, to, title: e.title}` (~:5170). ROI: `git log -S "title: e.title" -- places.html` = snapshot `2c9fbf2`.
- **C8** node-title-meta: "Tôn Giả Đại Giám Huệ Năng · 慧能 / Triều đại: Nhà Đường (唐) / Tông/Phái: Thiền Tông / Đời: -2 / Trò:…".
- **C5** cycle: Tarjan SCC → 0 cycle edges (direction_mismatch = overlay, KHÔNG phải topology cycle).
- **C9** responsive mobile: desktop-first pre-existing (docW=753≥winW=390 → scroll ngang, không vỡ, canvasH=0); **C9b** recover-after-resize → 1440px: canvas=685 · insp=685 · net=true · nodes=295 (không dead state). Ghi: mobile layout ngoài scope T127-129 (không @media query trong places.html).
- **C10** console/pageerror scan: pageErrors=0 · consoleErrors=0 (benign only).
- **Regression:** `npm run pipeline` PASS trừ e2e:runtime EPERM `unlink test-results/.last-run.json` = KNOWN INFRASTRUCTURE LIMITATION → PASS WITH KNOWN LIMITATION.
- **Screenshots + report:** `docs/sessions/qa_closure_2026-09-15/01..20_*.png` + `qa_report_t127_t128_t129.json`.

## Files
- `places.html`
- `docs/sessions/2026-09-13_t129-pedigree-refinement.md`
- `docs/sessions/places.html.bak-t129-*.html` (backup pre-edit trong session doc)
- `tasks/T129-pedigree-refinement.md`, `docs/tasktodo.md`, `data/progress_data.json` (regen)

## Rolling back
- Backup `places.html.bak-t129` trong session → copy đè. Real index staged deletions KHÔNG đụng.

## Ghi chú / next
- Cosmetic deferred: oval shape (giữ box — đọc tốt hơn), badge "Đang xem" (có ★ rồi), aria/keyboard, Fit padding 48px — có thể tách task UX sau.
- Default mode giữ 'tree' (spec "Ưu tiên mode mở rộng" = áp rule cho mode mở rộng, không đổi default).
- Groq quota vẫn đang bị T95/T96 chiếm — KHÔNG liên quan T129 (không gọi LLM).