# Session: 2026-09-15 T140 — Pháp Mạch UI/UX Fix (Audit logic + Plan chốt + Task tạo)

## Mục tiêu
Audit logic của plan "FIX UI/UX — Tab Truyền Thừa / Pháp Mạch" trước khi code, đối chiếu
với dữ liệu thật (`lineage_edge_assertions`) và code thật (`places.html` / `app.py`) → trả
lời 9 mục khảo sát → đề xuất hiệu chỉnh → được Lee phê chuẩn → tạo task T140 + docs + dashboard.

## Kết quả thật (audit)

| Hạng mục | Kết quả |
|---|---|
| DB `raw_relation_type` distinct | **chỉ {`da:isTeacherOf`, `dila:teacher_of`}** — KHÔNG tồn tại dharma_heir_of/ordained_by/studied_under/associated_with/candidate/disputed |
| DB `source_code` / `trust_level` / `status` | {MARCUS, DILA} / {L1, L2} / {active} — Zen = 0 assertions |
| Deep-link | `places.html` KHÔNG đọc hash; `window.onload` chỉ đọc `window.location.search` :8371 (fly/select/q/nexus_root) |
| Race bug | `loadLineageTree` :4810 + `centerLineageOn` :4981 KHÔNG có AbortController → click nhanh A→B→C render sai |
| Network layout | `_renderLineageNetwork` :5708, `_netExpand` default above/below=2, gen tuyệt đối tâm=0, cycle Tarjan SCC footer |
| Control bar | :5577-5602 — nút "Mở 2 đời/Mở 3 đời/Mở toàn nhánh/Thu gọn" + "+N đệ tử"; `MAX_SIBLINGS=24` (`__ov__`) |
| Filter hiện có | `_applyLineageFilters` :5221, 4 checkbox `#lineage-filter-all/visible/verified/conflict`; conflict = `direction_disagreement` |
| Inspector | node :5805 (display_name TTL + DILA ID + provenance) · edge :6000 (trust badge L1–L3, dẫn chứng, sources ✓Marcus/✓DILA) |
| Serve | `places.html` serve tĩnh (nginx/:8080); app.py không có route cho places.html |
| CDN | tailwindcss · leaflet 1.9.4 · markercluster 1.5.3 · vis-network@10.0.1 standalone UMD |

## Quyết định đã phê chuẩn (vào task T140)
1. **Không tách mode theo relation vocab** (vocab không tồn tại) — giữ 3 mode hiện có.
2. **Không tạo cột "NGUỒN & CHỨNG CỨ" riêng** — right rail 2 section, giữ toggle.
3. **Deep-link = `?select=<id>`**, KHÔNG #hash.
4. **Marcus = base · DILA = overlay · Zen ẩn** — đúng ngữ nghĩa nguồn.
5. Default "3 đời" = 1 thầy + root + 1 đệ tử → fetch `?up=2&down=2` + initial `_ftExpanded` center+1.
6. **AbortController** bọc loadLineageTree/centerLineageOn (chống race).
7. Zoom-out truncate label non-selected, tooltip đầy đủ, selected luôn đầy đủ.
8. Filter 3 nhóm (PHẠM VI/Nguồn/Trạng thái) giữ ID checkbox cũ.
9. Header breadcrumb + summary, ẩn field null (không "N/A").

## Files changed (session này)
- `tasks/T140-phap-mach-ui-ux-fix.md` (mới — plan đã chốt)
- `docs/tasktodo.md` (T140 ACTIVE top)
- `docs/sessions/2026-09-15_t140-phap-mach-ui-ux-fix.md` (này)
- `data/progress_data.json` + `dashboard/dashboard_process.html` (dashboard regen)

Commit: `a4d1ef5` (docs, temp-index parent `feec1c0`) — ROLLBACK.md row ghi `a4d1ef5`.

---

# Session (phiên implement): Build 9 mục plan → code DONE + commit `cd247c4`

## Đã làm (17 edits — `daoanh/places.html`, UI only)
1. **AbortController**: `_linLoadCtrl`/`_linLoadAbort()` bọc `loadLineageTree` + `centerLineageOn` (abort lần trước, check sau `res.json()`, state mới).
2. **Default fetch `?up=2&down=2`** (cả 2 hàm), state `up/down=2`, header "đang tải…" trong lúc fetch.
3. **Auto-expand center+1 đệ tử**: `_renderLineageChain` đổi `_autoExp(center,0)` (depth>=2) — bỏ auto mở 3 đời phía dưới.
4. **Header mới**: HTML `#lineage-header` sau toolbar + helper `_renderLineageHeader()` (breadcrumb "Trang chủ › Truyền Thừa › <tên>" + summary: N đệ tử trực tiếp · x/y cạnh có dẫn chứng · ⚠ conflict `direction_disagreement`; ẩn khi chọn nhân vật; clear trong `loadPlaceLineagePicker`).
5. **Right rail 2 section**: `#lineage-inspector` flex column — `#lineage-inspector-body` (CHI TIẾT) + `#lineage-inspector-evidence` (NGUỒN & CHỨNG CỨ) scroll riêng, `flex:0 0 300px`; giữ `#toggle-sidebar` trái/phải.
6. **Inspector node + edge rewrite**: tách 2 section; bỏ render "N/A"/field null (niên đại chỉ khi có năm); evidence = TTL provenance + "Đối chiếu nguồn" (✓/⚠/— MARCUS/DILA; **bỏ dòng ZENLINEAGE** — Zen ẩn 0 assertions) + Mức hiển thị.
7. **Edge ⚠ ngược chiều**: `_buildFtVisTree.addEdge` tính `_conflict` (direction_disagreement) → edge object, network edge `raw._conflict`, `_renderHierarchyTree` afterDrawing vẽ marker "⚠" (font `max(9,11/sc)`, amber) gần đầu mũi tên; tooltip/text inspector giải thích.
8. **Zoom-out label**: `_treeShortLabel(n,L,kidsCount,isExpanded)` + `_lblFull`/`_lblShort` trên mọi node; `network.on('zoom')` set font theo scale (threshold <0.72); selected + `__ov__` luôn đầy đủ; `_lineageNetwork._lblSync` re-sync khi chọn; reset `_labelCompact=false` sau build.
9. **Filter nhóm 3**: HTML 3 group PHẠM VI (all/visible) · NGUỒN (Có chứng cứ CBETA `#lineage-filter-hasref` mới + Mâu thuẫn DILA `#lineage-filter-conflict`) · TRẠNG THÁI (verified); giữ ID checkbox cũ; `_applyLineageFilters` đọc hasref (giữ center node); `_wireLineageControls` thêm id (5 checkbox).
10. **Legend đúng ngữ nghĩa**: chain `'Marcus = cấu trúc chính · DILA = đối chiếu (✓ khớp / ⚠ ngược chiều) · Zen hiện ẩn'`; network `'Nguồn: Marcus (cấu trúc chính) · DILA (đối chiếu ✓/⚠) · Zen ẩn'`.
11. `TREE_MODE_CONFIG.lineage.scope` text cập nhật.

## Verify đã chạy
- `@babel/parser` scan toàn `places.html`: **5 script blocks — 0 errors** (block 5 = 499,586 chars, trước build cũng tương đương).
- `npm run pipeline`: **lint PASS (exit 0; lỗi ESM `get_format:185` = placevn.html pre-existing)** · **test PASS** · **test:uat 3/3 PASS** · **test:compliance PASS (9 metric: pass7/warn1/fail1 như baseline)** · **e2e 4 trang PASS** · `e2e:runtime` **EPERM unlink test-results/.last-run.json — pre-existing** (nên đã verify bằng parser trực tiếp thay thế).
- `api_monk_lineage_tree` (app.py:5330-5449): server clamp `up/down ∈ [0,6]`, BFS cắt theo depth, docstring có `?expand=<id>&dir=up|down` (lazy sâu hơn). Default `?up=2&down=2` khớp scope: "Mở 3 đời" còn dữ liệu depth-2 trong `st.edges`; "<2 đời" hợp lý.

## Files changed (phiên implement)
- `daoanh/places.html` (commit `cd247c4` — temp-index, parent `e5a66e8`) → `git revert --no-edit cd247c4`.
- docs: `docs/bugs.md` (BUG-017..020 status → fix applied + hash), `tasks/T140-phap-mach-ui-ux-fix.md` (checklist code [x]), `docs/tasktodo.md` (T140 build done), session này.
- Commit docs build + regen: `3513640` (comments: BUG resolutions + checklist + tasktodo + session + ROLLBACK row cd247c4 + `data/progress_data.json` + `dashboard/dashboard_process.html`) → `git revert --no-edit 3513640`.

## Chờ
- **Admin QA ×1** (thủ công :8080 Ctrl+F5 — mục Verify/Accept task T140) → cập nhật bugs.md DONE + task DONE + chuyển taskdone.md.

## Files sẽ đổi ở phiên implement
- `daoanh/places.html` (DUY NHẤT — UI); API/Schema/DB = NONE.

## Ghi chú
- Code CHƯA bắt đầu ở session này — plan đã chốt + task đã tạo; implement là bước tiếp theo
  theo thứ tự: bugs.md OPEN → code places.html → `npm run pipeline` → tester agent → Admin QA ×1 → DONE.
- Rollback mọi thay đổi chỉ cần `git revert` (không có DB/Schema change).
- Next (phiên sau): mở `docs/bugs.md` entry OPEN → implement 9 mục trong tasks/T140 → verify.