---
id: T140
title: "PhÁp Mạch UI/UX Fix — Truyền Thừa tab (breadcrumb, 3 đời default, legend nguồn, race-guard, zoom-label, filter nhóm)"
module: places.html (UI only — API/Schema/DB NONE)
priority: high
status: in_progress
created: 2026-09-15
updated: 2026-09-23
depends_on: T127 (shared renderer) ✦ T129 (Tâm/footer/level sẵn) ✦ T138 (edge assertion L1–L4)
done_when: Breadcrumb+summary header trong #lineage-main-panel · default fetch ?up=2&down=2 với initial expanded = center+1 đệ tử · legend nguồn Marcus=base/DILA=overlay (không hiểu nhầm ngang hàng) · AbortController bọc loadLineageTree+centerLineageOn (hết race click nhanh) · edge HIDE nguồn Zen (0 assertions) · zoom-out truncate label non-selected giữ tooltip đầy đủ · filter nhóm PHẠM VI/NGUỒN/TRẠNG THÁI · bỏ "N/A" field null · node --check + lint + E2E PASS + Admin QA ×1 DONE.
---

# T140 — Pháp Mạch UI/UX Fix — Tab Truyền Thừa

## Mục tiêu
Hiệu chỉnh UI/UX tab **🌳 Truyền Thừa / Pháp Mạch** theo plan đã audit logic (4 hiệu chỉnh)
và được user phê chuẩn 2026-09-15. Chỉ sửa `daoanh/places.html`; **không** đổi API/Schema/DB.

## Quyết định đã chốt (sau audit logic — bắt buộc tuân theo)

1. **Không tách mode theo relation vocabulary** — data `lineage_edge_assertions`
   chỉ có `raw_relation_type` = {`da:isTeacherOf`, `dila:teacher_of`};
   **không tồn tại** `dharma_heir_of/ordained_by/studied_under/associated_with/
   candidate/disputed`. Giữ 3 mode hiện có:
   - **Pháp mạch** (tree top-down trình tự, L1–L2 chính mạch),
   - **Phả hệ mở rộng** (network đủ gen + cycles footer + L3 + `direction_mismatch` + rejected),
   - **Niên đại** (timeline).
2. **Không tạo cột "NGUỒN & CHỨNG CỨ" riêng** (canvas co lại) — dùng **right rail 2 section**
   (CHI TIẾT phía trên + NGUỒN & CHỨNG CỨ phía dưới, scroll riêng); **giữ** toggle-left/right.
3. **Deep-link = `?select=<id>` KHÔNG dùng `#hash`** — `places.html` không đọc hash,
   `window.onload` chỉ đọc `window.location.search` (fly/select/q/nexus_root) tại :8371.
4. **Ngữ nghĩa nguồn đúng:** Marcus = nền tảng cấu trúc (`marcus_networks`),
   DILA = overlay đối chiếu (`_t138_edge_assertions`: ✓ / ⚠ ngược chiều),
   Zen = ẩn (0 assertions). Legend [M]/[D] không hiển thị ngang hàng.
5. **Default "3 đời" = 1 thầy + root + 1 đệ tử:** đổi fetch `?up=2&down=2` +
   initial `_ftExpanded` = center + 1 gen đệ tử; giữ nút "+N đệ tử" / "Mở 2 đời" /
   "Mở 3 đời" / "Mở thêm đời trên" (có sẵn :5577-5602).
6. **Race guard:** bọc `loadLineageTree` (:4810) + `centerLineageOn` (:4981) bằng
   AbortController (pattern `loadAbortController`:862 / `_linEdgeState.ctrl`:5912) —
   2 hàm này hiện KHÔNG abort, click nhanh A→B→C render sai.
7. **Label zoom-out:** `network.on('zoom')` → node non-selected font nhỏ/ẩn label,
   tooltip `_t129NodeTitle` đầy đủ; selected luôn đầy đủ; giữ node key DILA id,
   không global relayout (docs/rules/graph-layout.md).
8. **Filter nhóm client-side (giữ ID checkbox cũ `#lineage-filter-all/visible/verified/conflict`):**
   - PHẠM VI  = all / visible (edge count > 0)
   - NGUỒN   = "Có chứng cứ CBETA" (has_ref) + "Mâu thuẫn DILA ngược chiều" (direction_mismatch)
   - TRẠNG THÁI = verified (L1–L2; legacy fallback has_ref) + "sẵn sàng L3" (dashed)
9. **Header mới** trong `#lineage-main-panel`: breadcrumb "Trang chủ › Truyền Thừa › <tông/phái> › <người chọn>"
   + summary người chọn (display_name, DILA ID, tông phái, niên đại, "N đệ tử");
   **ẩn field null** — không render "N/A".

## Việc làm (chi tiết)

- [x] Breadcrumb + summary header nhúng vào đầu `#lineage-main-panel` (`#lineage-header` + `_renderLineageHeader`, gọi trong loadLineageTree/centerLineageOn/picker; ẩn khi chọn nhân vật).
- [x] `loadLineageTree`: thêm AbortController mới mỗi lần gọi (`_linLoadCtrl`/`_linLoadAbort`), abort lần trước; fetch `?up=2&down=2`.
- [x] `centerLineageOn`: bọc abort để click nhanh không chồng render; fetch `?up=2&down=2`.
- [x] Initial expanded = center + 1 gen đệ tử (`_autoExp` depth>=2) thay vì auto mở 3 đời phía dưới.
- [x] Right rail: tách 2 section scroll riêng (`#lineage-inspector` flex 50/50: CHI TIẾT + NGUỒN & CHỨNG CỨ `#lineage-inspector-evidence`); giữ toggle trái/phải.
- [x] Edge styling: `direction_mismatch` vẽ badge ⚠ trên canvas (`edge._conflict`, afterDrawing) + text "⚠ ... ngược chiều giữa nguồn" trong "Đối chiếu nguồn"; Zen edge HIDE (ẩn hẳn dòng ZENLINEAGE).
- [x] Legend chú giải đúng ngữ nghĩa: "Marcus = cấu trúc chính · DILA = đối chiếu (✓ khớp / ⚠ ngược chiều) · Zen hiện ẩn".
- [x] `network.on('zoom')` → thu nhỏ label non-selected (`_treeShortLabel` + `_lblFull/_lblShort`, selectEvent re-sync `_lblSync`), giữ tooltip `_t129NodeTitle`; selected luôn đầy đủ.
- [x] Filter nhóm gom lại 3 group (PHẠM VI / NGUỒN / TRẠNG THÁI) giữ ID checkbox cũ `#lineage-filter-all/visible/verified/conflict` + thêm `#lineage-filter-hasref` (Có chứng cứ CBETA), wire trong `_applyLineageFilters` + `_wireLineageControls`.
- [x] Bỏ render "N/A" cho field null trong side panel (ní đại chỉ render khi có năm; không còn dòng "Đang hiển thị tên authority DILA" thừa).
- [ ] Deep-link test: mở `?select=<id>` (VD `?select=PL4043` hay id nhân vật) render đúng ngay (code không đổi — onload :8371 đã đọc `select`; cần verify thủ công).

## Verify / Accept

- [x] `@babel/parser` toàn file (5 script blocks / 0 errors) + `node --check` qua lint PASS.
- [x] `npm run pipeline` PASS cho lint/test/test:uat/test:compliance/e2e (e2e:runtime EPERM pre-existing — ghi nhận trước T140).
- [ ] Thủ công: click nhanh A→B→C không lệch node; zoom out label gọn; filter đúng; không field "N/A"; legend đúng ngữ nghĩa nguồn.
- [ ] Admin QA ×1 → DONE.

## Files touched
- `daoanh/places.html` (duy nhất — UI)
- `tasks/T140-phap-mach-ui-ux-fix.md` (này)
- `docs/tasktodo.md`, `docs/sessions/2026-09-15_t140-phap-mach-ui-ux-fix.md`, `docs/ROLLBACK.md`
- `data/progress_data.json` + `dashboard/dashboard_process.html` (regen)

## Rollback
Chỉ sửa `places.html` → `git revert <hash>` (hoặc checkout lại bản trước) là đủ; không có
thay đổi DB/Schema/API nên không cần rollback dữ liệu.
- Task này (docs, 2026-09-15): commit `a4d1ef5` → `git revert --no-edit a4d1ef5`.
- Code build (2026-09-15): commit `cd247c4` (places.html — 17 edits 9 mục plan) → `git revert --no-edit cd247c4`.
- Docs build/hash-fill (2026-09-15): commit `3513640` → `git revert --no-edit 3513640`.

## Ghi chú
- Audit timeline tách từ summary trước (harmony): edge inspector :6000, node inspector :5805,
  filter hiện có :5221, network renderer :5708 (`_netExpand` default above/below = 2).
- Không hard-code instance (VD Duy Khoan/Huệ Luân/A042195).
- Zen lineaged data BLOCKED chờ license — T140 không phụ thuộc.

## Addendum 2026-09-15 — Filter 3 mức tin cậy (UX improvement, phiên T141)

Tách checkbox "✓ Chỉ cạnh L1–L2 đã xác nhận" thành 3 checkbox riêng plain-language:
- `lineage-filter-tl1` → "✓ MARCUS ghi nhận" (L1, 11,169 cạnh)
- `lineage-filter-tl2` → "✓ DILA xác nhận" (L2, 46,006 cạnh)
- `lineage-filter-tl3` → "~ Chưa đối chiếu nguồn" (L3/null, nét đứt)

**Deviation:** T140 spec yêu cầu "giữ ID `lineage-filter-verified`" — thay đổi này thay bằng 3 ID mới.
`_applyLineageFilters` đã cập nhật đọc `f.tl1/tl2/tl3` thay vì `f.verified`.

Commit code: xem `docs/ROLLBACK.md` row T141.
Session: `docs/sessions/2026-09-15_t141-nexus-busbar-filter3levels.md`.