# T130 Session 2 — Frontend Core (Direct-Chain Control Bar) — 2026-09-24

## Summary
Completed Session 2 of T130 (Pháp Mạch Trực Hệ / Direct Chain): replaced the tree-mode
4-button control block in `places.html` with T130 direct-chain controls per spec.
Additive — 0 ALTER legacy renderer/backbone, `_t129NetCtrlBar` (network mode) untouched.

## Commit
- **SHA**: `f125c44`
- **Message**: `feat: T130 Session 2 - direct-chain control bar (Phap Mach = truc he)`
- **Files**: `Dai_Tang_Kinh/daoanh/places.html` (+55/-18)

## Exact Location (places.html)
- Enclosing function: `_renderLineageChain()` (line 6389) — tree-mode chain renderer.
- Control bar block: was 4 buttons (`Mở 2 đời`, `Mở 3 đời`, `Mở toàn nhánh`,
  `Thu gọn nhánh dưới`) → replaced with T130 block.
- Old comment at 352895 updated: `expanded: true, // có nút 'Mở 2 đời/3 đời/Thu gọn'`
  → `// có nút control chain (T130: Mở 1 đời tiếp / Thu gọn / Fit / Tâm)`.

## Changes

### Old buttons (REMOVED)
- `ctrlBar.appendChild(mkCtrlBtn('Mở 2 đời', ...))` — expands center + 1 gen (violated limit=1-at-a-time semantics)
- `mkCtrlBtn('Mở 3 đời', ...)` — expands 2 gens
- `mkCtrlBtn('Mở toàn nhánh', ...)` — `Object.keys(st.nodes)` full blast (`_ftFullExpanded`-style, banned in T130 chain)

### New T130 direct-chain controls (ADDED)
1. **Fit** → `_t130FitAll()`: `_lineageNetwork.fit({ animation: true })`
2. **Tâm** → `_t130FocusCenter()`: `_lineageNetwork.focus(center, { scale: 0.9, animation: true })`
3. **Thu gọn nhánh dưới** (kept): `expanded.clear(); fullExp.clear(); rerender();` — collapses ONLY below-center, ancestor spine stays full
4. **Mở 1 đời tiếp** → `_t130ExpandNextGen()`: exactly ONE generation per click
5. **CTA "Xem Phả hệ mở rộng ↗"** → `_renderLineageNetwork()` (primary-color styled)

### `_t130ExpandNextGen` (1 đời/click)
- Computes frontier = all `expanded` parents that still have unexpanded children (`kidsOf[pid]`).
- 1 hidden child → `expanded.add(k.id)` directly.
- >1 hidden child → `_t130Chooser(pid, kids)` popover (branch chooser, KHÔNG auto-pick).
- After expanding all frontier → `fullExp.clear(); rerender();`

### `_t130Chooser` (branch chooser popover)
- Promise-based; mask overlay z-index 12000 + card.
- Header: `'Chọn nhánh trực hệ (N đệ tử trực tiếp)'`.
- Each child: button with `＋ ` + `TREE_LABEL(...).vi` (+ Hán) + real source ref chip
  `'✓ ' + k.ref` when `k.has_ref && k.ref`, else `'(chưa có nguồn)'`.
- `Đóng` button; click button → resolve(k.id), remove mask, then expand.

## Scoping / Variables (verified in-place)
- `st` = `_lineageState` (not a local shadow) — `st.nodes`, `st.edges` used by chooser.
- `expanded` = `st._ftExpanded`, `fullExp` = `st._ftFullExpanded` (both Sets from enclosing `_renderLineageChain`).
- `kidsOf` (teacher pid → [{id, ref, has_ref}]), `directKids`, `totalDescRoot`, `rerender` all in scope.
- `_lineageNetwork` = global `let` (line 5052), set by `_renderHierarchyTree` (line 5609) → Fit/Tâm valid in tree mode too.
- `_renderLineageNetwork` global fn exists (network mode CTA target).

## Verification
- `npm run guard` → `[OK] SSOT repo root = visjs-app`, no nested `.git` ✓
- `node --check` on all 3 inline script blocks of places.html → `exit=0` all ✓
- `py_compile` app.py → OK (no backend change this session) ✓
- `npm run e2e` → `✅ All pages passed E2E checks!` ✓
- `git diff places.html` → exactly 2 hunks, +55/-18 (comment + control bar block) ✓
- Backup pre-edit: `places.html.backup_t130_s2` (653,301 bytes; post = 654,391 bytes)

## Compliance with Spec
| Spec Requirement | Status |
|-----------------|--------|
| Controls: Fit / Tâm / Thu gọn tất cả / Mở 1 đời tiếp / CTA "Xem Phả hệ mở rộng ↗" | ✅ |
| REMOVE "Mở 2 đời" / "Mở 3 đời" / "Mở toàn nhánh" from direct mode | ✅ (0 remains runtime) |
| exactly ONE generation per click (limit=1 client) | ✅ `_t130ExpandNextGen` frontier 1 tầng |
| >1 direct child → chooser, KHÔNG auto-pick | ✅ `_t130Chooser` |
| Branch chooser shows REAL source refs | ✅ `k.has_ref && k.ref` chips |
| Collapse keeps ancestor spine (only below-center) | ✅ `expanded.clear()+fullExp.clear()` |
| `_t129NetCtrlBar` (network/phả hệ mở rộng) T129 kept | ✅ untouched |
| No ancestor bar removal, no legacy `_ov__`/`_ftFullExpanded` full-blast in chain | ✅ |

## Deferred to Later Sessions
- **Session 3**: Direct chain controls replace T129 controls in direct mode (deeper chain UX).
- **Session 4**: Deep-link + state — pushState/popstate, URL sync (`_buildPrimaryChain`
  routing via `?expand=<id>&dir=up|down` interactive pushState).
- **Session 5**: T129 regression + browser QA.

## Rollback
```bash
git revert --no-edit f125c44
```
- Affects: `Dai_Tang_Kinh/daoanh/places.html` only
- No database changes / no schema changes / no backend change

## Related Files
- Task: `tasks/T130-phap-mach-direct-lineage.md`
- Session 1: `docs/sessions/2026-09-23_t130_session1_backend_compliance.md`
- Audit: `docs/sessions/2026-09-18_t130-t131-integration-audit-report.md`
- ROLLBACK: Added entry for `f125c44`