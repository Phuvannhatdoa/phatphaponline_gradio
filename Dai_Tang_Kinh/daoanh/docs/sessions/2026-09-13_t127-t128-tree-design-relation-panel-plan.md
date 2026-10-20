# Session 2026-09-13 — T127 + T128 Plan Approval & Task Creation (Tree Design System + Relation Panel)

## Context
Lee phê chuẩn đề xuất REFACTOR + FIX (phê chuẩn "dev đi" với mode chuyển build):
1. **REFACTOR** — 1 shared Tree Design System cho Pháp Mạch + Phả hệ mở rộng + future trees.
2. **FIX** — Panel "Chi tiết mối quan hệ": thêm "Tạm dịch AI" + embedded Đại Tạng reader.

## Điều tra/phê chuẩn (plan mode → build)
Verified trực tiếp trong `places.html`:
- `_renderLineageNetwork` (L5370-5416): **force layout thật** (`physics:{…, barnesHut:{…}}`, `layout.hierarchical:false`), center = **ellipse** gold `#ad7c1c`, node khác = **dot** gold `#c4891a`, edge label `'thầy→'/'→trò'` L5389. → User's "oval/đen" ≈ đúng shape, màu thật là gold trên navy (không phải đen).
- `_renderLineageInspectorEdge` (L5527-5539): chỉ có nút '📖 Đọc trong Đại Tạng' → `loadLineageCite` → `/daoanh/api/lineage-ref/passage` → `openDaiTangReader` (hook undefined trong repo — phụ thuộc embedding host) hoặc fallback bibliography. Không có nút dịch.
- Bộ lọc 4 checkbox (L467-473): **tồn tại nhưng CHƯA wire** (không JS) → T127 sẽ wire trong shared component.
- Dead code `_renderLineageTree`/`_mkLineageNode` (L4988-5084 / 5329-5368): verified 0 caller.
- Evidence case mẫu: `marcus_networks.ref` = chuỗi tự do `"trích đoạn…（T47n1990_p0582a19）; "` — **không có** relation_id/original_excerpt/work_id/locator/passage_id/text_hash. → cần parser additive server-side (T128).
- `T47n1990` **chưa index** trong `passage` (0 rows) → `lineage-ref/passage` trả `found:false` (fallback "Cần khảo cứu"). 

## Quyết định approved (4 câu hỏi — Lee chọn mặc định)
| Vấn đề | Quyết định |
|---|---|
| Passage T47n1990 chưa index | **Fallback trung thực** "Cần khảo cứu" — KHÔNG backfill passage |
| Full-page reader texts.html (không tồn tại) | **Đọc ngay trong panel/modal ĐẠI TẠNG hiện có** — không dựng trang mới |
| Phả hệ mở rộng chuyển layout | **Có — layered-top-bottom** (bỏ force simulation) |
| Bộ lọc 4 checkbox | **Có — wire trong shared component** |
| Dịch AI | Dùng `translation_cache` text-hash + Groq qwen (nhánh T73) — KHÔNG dùng legacy `/api/translate` (Claude, cần passage_id) |

## Task created
- **T127** `tasks/T127-tree-design-system-refactor.md` — shared `_renderHierarchyTree` + migration 2 tab + wire filters + xóa dead code. Status: `in_progress`.
- **T128** `tasks/T128-relation-detail-panel-translate-reader.md` — panel Tạm dịch AI + Đọc văn cảnh + backend parser/endpoint. Status: `pending` (depends_on T127).

## Docs / Dashboard
- `docs/tasktodo.md` — thêm entry ACTIVE T127 + T128 (header).
- Dashboard: chạy `scripts/build_progress_data.py` → `data/progress_data.json` + `dashboard/dashboard_process.html`.

## Next steps
1. Backup `places.html` → `docs/sessions/places.html.bak-t127-*`.
2. Implement T127: `_renderHierarchyTree` + `TREE_MODE_CONFIG` + filter wiring → migrate expanded → migrate lineage → xóa dead code → verify (node --check + npm pipeline).
3. T128 sau T127.

## Rolling back
- `git revert <commit>` (temp-index via `%TEMP%\opencode\b4_commit.py`). Real index staged deletions KHÔNG đụng.

---

## UPDATE 2026-09-13 — T127 code DONE (chờ live QA + review)

### Implemented in places.html (T127)
1. **Shared Tree Design System** block (trước `_renderLineageMode`): `TREE_MODE_CONFIG` (lineage/expanded), `TREE_PALETTE` (normal blue-teal, root amber, selected teal glow, ancestor indigo, descendant green, overflow, conflict), `TREE_LABEL(n)` (2 dòng Việt/Hán), `_t127NodeColor`, `_t127EdgeStyle` (arrowhead, no label, has_ref solid amber / no-ref dashed gray, conflict red), `_renderHierarchyTree(opts)` (layered-top-bottom UD, physics off, cubicBezier vertical, rect 136×52–220, ancestor bar + controls + click/dblclick/selectEdge/onOverflow wiring, fit afterDrawing), `_applyLineageFilters`.
2. **`_renderLineageNetwork` (expanded)** → shared renderer mode `expanded`: rect 2 dòng, palette theo role ancestor/descendant/center/selected/conflict, bỏ edge label.
3. **`_renderLineageChain` (Pháp Mạch)** → shared renderer mode `lineage`: giữ auto-expand 3 đời, `MAX_SIBLINGS=24` pagination (`__ov__` node), control bar "Mở 2 đời/3 đời/toàn nhánh/Thu gọn", ancestor bar qua `ancestors` (ancestors skip khỏi tree tránh trùng), `_eid`/`_hasRef` gắn edge cho filter.
4. **Wire 4 checkbox** `lineage-filter-all|visible|verified|conflict` trong `_wireLineageControls` → change → `_renderLineageMode(st.mode)`.
5. **Xóa dead code**: `_renderLineageTree` + `_mkLineageNode` (verified 0 caller; không còn ref nào).

### Verify
- `node --check` (inline script) **PASS**.
- `npm run lint` (ESM-format warning pre-existing, Node v24), `npm run test` **PASS**, `npm run e2e` **PASS**; `e2e:runtime` EPERM pre-existing skip.
- Note: working tree có concurrency từ agent ngoài (git status places.html `MM` + nhiều file staged). Restore lại ancSet-skip sau khi phát hiện ancestor-block lạ. Chỉ commit thay đổi T127 của mình qua temp-index.

### Chưa làm (T127 còn lại cho live QA)
- Admin QA trực quan :8080 (2 tab) → xác nhận DONE → chuyển T127 sang `taskdone.md`.
- Sau đó T128 (relation panel translate + reader) — plan giữ nguyên.