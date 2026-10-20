---
id: T130
title: Pháp Mạch = trực hệ 1 nhánh (primary chain + icon +/- + chooser + routing)
module: app.py (additive param) · places.html (chain rewrite)
priority: high
status: done
created: 2026-09-13
updated: 2026-09-24
depends_on: T127 (shared renderer) · T129 (Tâm/footer/level sẵn)
done_when: Pháp Mạch (mode 'tree') chỉ hiển thị chuỗi trực hệ thầy→trò (ancestors + center + canonical successor), icon +/- thật trên node (DOM overlay, 28px, aria, tooltip, stopPropagation), 1 đời/click, collapse thu subtree đúng, +N nhánh → chooser (không auto-pick), CTA "Xem Phả hệ mở rộng ↗", controls chuẩn (Fit/Tâm/Thu gọn tất cả/Mở 1 đời tiếp, BỎ "Mở toàn nhánh"), deep-link ?mode=lineage&chain=..., ?expand= backend lazy, node-body click = mở hồ sơ; node --check + algorithm test + npm run pipeline PASS.
---

# T130 — Pháp Mạch: direct-lineage projection (trực hệ 1 nhánh) + node expand icon

**Status:** done (2026-09-24) — **CLOSED 5/5 sessions.** Backend Session 1 (commit `f07d8cb`), frontend Session 2–3 (commit `f125c44`), deep-link/pushState Session 4 (commit `74ef34c`), T129 regression + browser QA Session 5 (18/18 PASS, docs commit `7ac2204`). Chi tiết closure: `docs/sessions/2026-09-24_t130_session5_t129_regression_browser_qa.md` + task `tasks/T165-dash-regen-t130-closure.md`. Phần ngoài scope đã document: pick/tup riêng (gộp về chain), network depth `&net=` chưa vào URL, B2 source_authority→confidence DEFER.
**Phạm vi:** `app.py` (1 tham số additive, 0 ALTER) + `places.html` (chain rewrite). KHÔNG đụng DB.
**Ràng buộc:** additive-only; giữ `_renderHierarchyTree`/palette/label shared (T127) + `_t129NodeTitle/_t129EdgeTitle` (T129); network/expanded mode GIỮ NGUYÊN (full tree đúng triết lý "Phả hệ mở rộng"); real git index không đụng (temp-index khi được yêu cầu); chạy `npm run pipeline` trước review.

## Bối cảnh & Verdict (verified 2026-09-13)
Spec yêu cầu Pháp Mạch = chuỗi trực hệ duy nhất (ví dụ Đạt-ma → Huệ Khả → Tăng Xán → Đạo Tín), mở rộng từng đời bằng icon +/−, không sibling. **Chỉ khớp ~20%** với logic hiện tại (phần shared renderer + arrowhead V-H-V + bỏ edge label ĐÚNG; còn lại hiện là "full subtree + auto-expand 3 đời + chính-mạch heuristic + overflow pagination"). Diff đầy đủ trong `docs/sessions/2026-09-13_t130-phap-mach-direct-lineage.md`.

**Sự thật dữ liệu (bắt buộc biết):**
- `marcus_networks` (11,169) chỉ có `relation_type='da:isTeacherOf'`, `source='MARCUS'`, `ref/has_ref`. **KHÔNG có primary/confidence/authority per edge.** → `primary_successor_id`/`branch_status`/`lineage_confidence` phải DERIVE client-side (không persist).
- `canonical_decision` = quyết định TÊN (canonical_name_vi), KHÔNG phải succession. `source_authority` (7 nguồn) có thể nuôi confidence về sau (DEFER, ghi Ghi chú).
- `lineage_conflicts_v2` (40,327 open) = nguồn đánh dấu "cần khảo cứu" (resolved=0). Node có conflict thật sự nên về branch_status='uncertain'.
- Mã Tổ Đạo Nhất 141 trò → benchmark cho `+N nhánh`; 澄觀/無演 7 thầy → ancestor multi-teacher (cần chooser THẦY, không chỉ trò).
- Endpoint `/lineage-tree?up=3&down=3` (clamp 0–6) — docstring ghi `?expand=` nhưng **CHƯA implement** (app.py:5225-5329). → B1 của task này.

## Pha 1 — Backend (app.py, additive, 0 ALTER)
- **B1. Implement `?expand=<person_id>&dir=up|down`** trên `/daoanh/api/monk/<id>/lineage-tree`: fetch `_t86_neighbors` 1 tầng từ `<person_id>` theo `dir`, merge node mới (dedupe theo `nodes`/`seen_*`) + edge mới, cập nhật `has_more_*`/`conflicts`/`display_name` cho `<person_id>`, trả envelope cũ (ok/center/up/down/source/nodes/edges). Lazy, zero-RAM. Validate person tồn tại. Smoke: `?expand=A008874&dir=down`.
- **B2 (DEFER):** `source_authority → lineage_confidence` hint. KHÔNG làm vòng đầu; không quyết hộ primary.
- py_compile + restart :5000 + smoke.

## Pha 2 — Client `_renderLineageChain` rewrite (mode 'tree'), 8 mục

### P2.1 Projection trực hệ `_buildPrimaryChain()` (thay BFS full)
- Ancestors: walk `_lineageTreeParents()` từ center lên gốc (đã có). Nếu node có >1 teacher → branch_status='uncertain' + badge "nhiều thầy" → chooser THẦY (không auto-pick). `st._chainPickUp[pid]=teacherId`.
- Successor: mỗi node đếm `direct_children_count=(st.edges).filter(from===id).length`:
  - `1` → canonical, thêm vào chain.
  - `0` → leaf, dừng.
  - `>1` → `+N nhánh` badge; **KHÔNG extend, KHÔNG auto-pick** (spec cấm tự chọn). `st._chainPick[pid]=childId` từ chooser.
- Default render: ancestors (full) + center + tổi đa canonical succession có trong `st.d` (khớp acceptance A). Không hiện sibling.
- `branch_status` derive: `1→canonical`, `0→leaf`, `>1→uncertain` (hoặc node `direction_disagreement` conflict → uncertain). `lineage_confidence`: shown chip "cao" (ref có) / "chưa xác minh".

### P2.2 Icon +/- trên node (DOM overlay, KHÔNG chèn vào canvas)
- `_renderHierarchyTree` nhận `options.iconLayer`: sau khi tạo network, tạo `div.lineage-icon-layer` bên trong `visDiv` (`position:absolute;inset:0;pointer-events:none`). Mỗi click-position lại: `network.getPositions()` + `canvasToDOM` → set button absolute tại node góc phải trên (`top:-9px;right:-9px`); clamp khỏi mép container.
- Real `<button>` (không text SVG): `+` (collapsed) / `−` (expanded) / `+N nhánh` (badge → chooser). 24–28px, focus ring, `aria-label` "Mở đời truyền thừa tiếp theo của <tên>", `aria-expanded`, tooltip spec. `stopPropagation()` phòng thủ.
- Recompute trên `afterDrawing` + `zoom` + `dragEnd` + `resize`.
- **Node body click → `_renderLineageInspector(pid)`** (đổi khỏi toggle-expand hiện tại L5532). Edge click → inspector edge (giữ).

### P2.3 Expand/collapse (1 đời/click, ownership)
- Chain là **single-path** → node con chỉ qua đúng 1 cha trong chain ⇒ collapse ở X = bỏ MỌI node dưới X (tự thoả "không thu node mở độc lập").
- State: `st._chainOrder=[]` (thứ tự visible ids gốc→...→lá) + `st._chainPick` (successor) + `st._chainPickUp` (teacher). `+` tại X: chèn descendant X (canonical hoặc child đã pick) kế X; nếu X có `has_more_down` và con ngoài `st.d` → gọi `?expand=<X>&dir=down` merge rồi chèn. `−` tại X: cắt mọi node sau X.
- Nút "Mở 1 đời tiếp" = expand tại lá hiện tại. Max 1 gen/click.
- Cache: `st._chainCache[key=`${pid}|${_chainVersion}`]` (version=`st.d.source|st.d.nodes.length`).

### P2.4 Sibling/branch
- Không render sibling trong chain; bỏ micro-label `▸/▾` cũ + overflow node `__ov__` (MAX_SIBLINGS) trong chain (giữ `_renderHierarchyTree` không đổi).
- `+N nhánh` → chooser popover (abs overlay): danh sách student với ref chip + has_ref dot; click → `st._chainPick` + chèn 1 đời; kèm CTA "Xem đầy đủ trong Phả hệ mở rộng" → `_renderLineageMode('network')`.

### P2.5 Visual
- Giữ shared palette/label/connector/arrowhead. Thêm: icon base teal/amber theo state, border rõ, focus ring ∅, 28px, contrast ≥4.5:1; node expanded → viền/outline nhẹ (tem "đang mở").

### P2.6 Routing/state
- Deep-link: `?mode=lineage&focus=<pid>&chain=<c1>,<c2>&pick=<pid>:<child>[,...]&tup=<pid>:<teacher>[,...]`. Ngầm: `?tab=...&lm=lineage&focus=...&chain=...`.
- `history.pushState` on expand/collapse/pick/mode; `popstate` → restore (`_renderLineageMode('tree')` + set chain). Đọc param trong `loadLineageTree`/`loadPlaceLineage`.
- Key = canonical person/id, KHÔNG position index.

### P2.7 Controls cấp tree (chain bar thay thế)
- Giữ: `Fit` (có), `Tâm` (có — T129 đã sửa network+tree), thêm `Thu gọn tất cả` (clear chainOrder → về default) + `Mở 1 đời tiếp`; thêm CTA `Xem Phả hệ mở rộng ↗` (→ network). **BỎ** "Mở 2 đời"/"Mở 3 đời"/"Mở toàn nhánh" + overflow pagination.
- Filters (`_applyLineageFilters`): chain = backbone; filter `verified/conflict` KHÔNG được làm rách chuỗi — chain-added node giữ backbone bất chấp filter; thuộc tính lọc chỉ áp node chưa mở/branch badge. Quyết định này ghi rõ.

### P2.8 Acceptance + verify
- A–I theo spec (chain đơn; `+`; `−`; không sibling; chooser không auto; network vẫn full; body click panel; shared style).
- Unit test algorithm (extract code thật như T129): `_buildPrimaryChain` 1:1 → canonical; A008874 (1 trò) canonical; Mã Tổ (141) → uncertain + N; ancestor multi-teacher → uncertain; collapse cắt đúng; pick persist; `?expand` merge dedupe.
- `node --check`, `npm run pipeline`, restart :5000 smoke expand, live :8080.

## Files
- `app.py` (+ `docs/sessions/app.py.bak-t130-snapshot.py`)
- `places.html` (+ `docs/sessions/places.html.bak-t130-phap-mach-direct-lineage.html`)
- `tasks/T130-phap-mach-direct-lineage.md` · `docs/sessions/2026-09-13_t130-phap-mach-direct-lineage.md` (session) · `docs/tasktodo.md` · `data/progress_data.json` (regen)

## Rollback
- Copy backup đè file. `?expand` tham số additive — vô hại khi bỏ. Real git index không đụng (temp-index theo yêu cầu).

## Ghi chú / next
- B2 source_authority→confidence: DEFER (cần quyết định về nguồn ưu tiên — không tự chọn; chỉ hiển thị). 
- Network (Phả hệ mở rộng): GIỮ NGUYÊN "Toàn bộ nhánh" (spec cho phép full tree ở đây); không đổi T129.
- `lineage_version` không có trong dữ liệu → chuỗi derive client (`source|count`); ghi nhận giới hạn làm cache key.
- Case được chọn để test chính: 應真→慧寂 A008874→A009491; Mã Tổ Đạo Nhất = multi-branch benchmark; 澄觀 = multi-teacher benchmark.
- Groq quota không liên quan T130 (không gọi LLM).