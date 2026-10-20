# Session 2026-09-13 — T129 Phả hệ mở rộng refinement

**Task:** `tasks/T129-pedigree-refinement.md` | **Status:** code done + verified, chờ live QA
**Kế hoạch phê chuẩn:** Lee (bản verify spec "Menu Pháp Hệ > Phả hệ mở rộng" → T129 batch 1–7; cosmetics box/oval defer)

## Mục tiêu
Đóng 8 khoảng trống khi so spec Phả hệ mở rộng vs T127 (vốn đã đúng ~80%). **KHÔNG đụng backend/DB** — thuần `places.html`, additive.

## Việc đã làm (đều trong places.html)
1. **Shared helpers** (chèn sau `_applyLineageFilters`, trước `_renderLineageMode`):
   - `_lineageGenMap(centerId, kidsOf, par)` — BFS hai chiều, first-visit-wins: `gen[center]=0`, thầy −n, trò +n; chỉ node tới được tâm (chu trình an toàn).
   - `_lineageSccEdges()` — Tarjan SCC trên `st.edges`; cạnh trong SCC size>1 hoặc self-loop = cạnh chu trình.
   - `_t129NodeTitle(n,{gen,nT,nS,ev})` — tooltip meta (triều đại/niên đại/tông/đời/#thầy/#trò/dẫn chứng/⚠ mâu thuẫn).
   - `_t129EdgeTitle(parentId,toId,edge)` — "X truyền pháp cho Y" + dẫn chứng/○ Cần khảo cứu.
   - `_t129YearOf/_t129NameOf` — khóa sort.
2. **`_renderHierarchyTree`**: nhận `options.footer` (additive, append sau visDiv) — dành cho research list.
3. **`_renderLineageNetwork`** (rewrite additive):
   - state `st._netExpand={above:2,below:2,all:false}`; node giữ khi reachable + trong depth; `level=gen−minGen` (normalize ≥0 cho vis); sort theo (level, year, name_vi).
   - visEdges: bỏ cạnh chu trình + cạnh ngoài keep-set; `title` = `_t129EdgeTitle`.
   - controls = `_t129NetCtrlBar()` (Mở thêm đời trên ↑ / Mở thêm đời dưới ↓ / Toàn bộ nhánh / Thu gọn + chú thích hiện trạng + nguồn Marcus·DILA).
   - footer = `_t129NetFooter()` (note "N node không nối tới tâm đã ẩn" + chips "⚠ Quan hệ mâu thuẫn/chu trình" click → inspector edge).
4. **`_wireLineageControls` `#lineage-center`**: network → `_lineageNetwork.focus(center)` (sửa noop bug ở network; giữ tree + timeline cũ).
5. **Chain mode**: edge title `_t129EdgeTitle` (addEdge + ancestor edges); node title `_t129NodeTitle` (descendant gen=depth, ancestor gen=level); counts `nT/nS/evCnt` tính tại đỉnh hàm.

## Verify
- Algorithm unit test **15/15 PASS** (`C:\Users\NAMTHI~1\AppData\Local\Temp\opencode\t129_fn_test.js`) — trích đúng helper thật từ file (marker `// ── T129:` → `function _renderLineageMode(`), không drift:
  - gen: center=0, teacher=−1, student=+1, grandchild=+2; cycle rời A↔B KHÔNG reachable.
  - SCC: A↔B flag đúng 2 cạnh; T→C không flag.
  - edge title "C truyền pháp cho S1" + ref; no-ref → "○ Cần khảo cứu".
  - node title: Đời/dynasty/Trò count; ancestor Đời: -1.
- `node --check` main inline script PASS (file 565,447B; script ~471k chars).
- `npm run pipeline` static PASS (lint ESM warning + e2e:runtime EPERM pre-existing).
- Ghi chú: PowerShell `Copy-Item` không chép được (im lặng no-op môi trường này) → dùng `[System.IO.File]::Copy($src,$dst,$true)`.

## Backup
- `docs/sessions/places.html.bak-t129-pedigree-refinement.html` (565,447B, pre-T129? — đúng, chứa T128 + T127, CHƯA có T129).

## Chờ đợi
- **Live QA (:8080 Ctrl+F5):** chọn tăng nhân có pháp hệ → mode "Phả hệ mở rộng" → thầy trên/trò dưới cùng hàng; nút mở đời/Thu gọn ổn định; Tâm focus; footer chu trình; hover "X truyền pháp cho Y".
- QA xong → chuyển T127/T128/T129 CÙNG đợt (T128 vẫn chờ Groq quota).

## Rollback
Copy backup đè `places.html`. Real git index KHÔNG đụng (temp-index policy khi được yêu cầu commit).