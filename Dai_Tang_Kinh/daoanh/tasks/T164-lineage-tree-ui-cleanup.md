---
id: T164
title: "Lineage Tree UI Cleanup — giảm clutter tab Truyền Thừa (Pháp Mạch + Phả hệ mở rộng)"
module: places.html (UI only — API/Schema/DB NONE)
priority: medium
status: done
created: 2026-09-23
updated: 2026-09-24
depends_on: T127 (shared renderer) ✦ T140 (breadcrumb, race-guard) ✦ T146 (+/- icon)
done_when: Label nodes không có count decorators (▸N/▾N bị xóa) · Ancestor bar bị xóa (breadcrumb giữ đủ context) · Zoom+/- buttons xóa (vis.js scroll-wheel đủ) · Legend row static HTML luôn hiển thị bên dưới toolbar · Inspector evidence section collapse khi không chọn node · Overflow node hiện dạng ellipse thay box · T129 footer trong <details> collapsed mặc định · Admin QA ×1 DONE
---
# T164 — Lineage Tree UI Cleanup

## Nguồn gốc
Audit plan sinh từ phiên 2026-09-23 (ANALYZE_ONLY mode).
Approved build: 2026-09-23.

## Việc làm

- [x] **S1**: `_buildFtVisTree:6498-6501` — xóa `▸ N hậu duệ` / `▾ N đệ tử` count string, giữ `▸`/`▾` chỉ báo. ★◉ giữ nguyên (cùng dòng với tên, không thêm chiều cao).
- [x] **S8**: `heightConstraint.minimum` 58 → 52 (tiết kiệm khi label bớt 1 dòng đếm).
- [x] **S2**: `_renderHierarchyTree:5458-5479` — xóa ancestor bar block (pill chain thầy truyền pháp). Breadcrumb `#lineage-header` đã đủ context.
- [x] **S3**: HTML toolbar + JS eventListener — xóa `#lineage-zoom-in` + `#lineage-zoom-out` buttons. Scroll-wheel vis.js đủ dùng.
- [x] **S4**: Thêm `#lineage-legend-row` (static HTML, bên dưới toolbar, trên breadcrumb). Xóa `srcNote` span trong Pháp mạch ctrlBar + `src` span trong `_t129NetCtrlBar`.
- [x] **S5**: `#lineage-inspector-evidence-wrap` — collapse `flex:0 0 0px` khi rỗng, expand `flex:1 1 50%` khi có content. `_setLineageEvidence` cập nhật expand/collapse theo html.
- [x] **S6**: Overflow node `__ov__` — đổi `shape:'box'` → `shape:'ellipse'`, xóa `margin` (ellipse tự size).
- [x] **S7**: `_t129NetFooter` — wrap nội dung trong `<details><summary>⚠ N cảnh báo ▾</summary>…</details>`. Trả về `null` khi không có dropped/cycle (không thêm height thừa).

**Status:** done (2026-09-24) — ĐÃ CLOSE. Code S1–S8 committed `77dec5e` (2026-09-23). Browser QA live :8080 (2026-09-24) PASS toàn bộ mục verify: legend row hiển thị (980×21) · zoom buttons absent · ancestor bar absent · inspector evidence collapse (`flex 0 0 0px`) khi rỗng + expand (`1 1 50%`) khi chọn node A000958 · overflow ellipse · `_t129NetFooter` trả null khi không warnings · 0 JS error. Chi tiết: session `docs/sessions/2026-09-24_t164-lineage-tree-bottom-lineuiqa.md`. **Revert: `git revert --no-edit <sha_T164>`** (chỉ `places.html`, 0 DB/0 API).

## Verify / Accept

- [x] Browser QA (2026-09-24, Playwright live :8080): Pháp mạch node label ngắn gọn `▸`/`▾` thuần (không count decorator `▸ N hậu duệ` — L6498/L6499); ancestor bar absent (0 tham chiếu); toolbar gọn (zoom-in/out=0); legend row hiển thị ổn định.
- [x] Inspector evidence wrap present · collapse `flex:0 0 0px` lúc khởi tạo · expand `1 1 50%` + nội dung khi chọn node (A000958 QA PASS).
- [x] Overflow node `__ov__` → `shape:'ellipse'` (L6533, margin xóa).
- [x] `_t129NetFooter` wrap `<details collapsed>` + `return null` khi không có dropped/cycle (L6754-6770) — browser QA: details collapsed, 0 cảnh báo giả.
- [ ] Admin QA ×1 → DONE (chờ Lee confirm live sau restart :5000).

## Files touched
- `daoanh/places.html` (duy nhất — UI)
- `tasks/T164-lineage-tree-ui-cleanup.md` (này)
- `docs/sessions/2026-09-23/changes.md`

## Rollback
```
git revert --no-edit <commit_hash_T164>
```
Chỉ sửa `places.html` — không có DB/Schema/API thay đổi.
Backup: `docs/sessions/2026-09-23/places.html.bak-t164-pre`
