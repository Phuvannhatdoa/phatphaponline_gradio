# Session 2026-09-23 — Dashboard UX Reduction + BUG-025/026 Docs + T101/T140 Status Confirm

## Tóm tắt
- Dashboard `dashboard_process.html`: mở rộng full-width, giảm không gian vô dụng, tổ chức lại tbody
- BUG-025 và BUG-026: đã fix (DB thật, SQL trực tiếp) — ghi nhận vào docs
- T101 + T140: xác nhận code đã hoàn thành từ phiên trước, pending admin QA

---

## 1. Dashboard UX Reduction (`daoanh/dashboard/dashboard_process.html`)

### A. Mở rộng full-width
- Xóa `min-width:980px` trên table → dùng `table-layout:fixed` + `<colgroup>` (8%/29%/28%/27%/8%)
- Body padding giảm: `24px` → `10px 14px`
- Section header, summary bar, card, KPI: spacing tight hơn

### B. OpenCode Directives → 1-line compact banner
- Thay tile-grid 4 mục → 1 dòng xanh: `100% · Bước 909/909`
- Giữ `id="directiveCard"/"dirNote"/"dirGroups"` hidden để JS không lỗi

### C. History banners → `<details>` accordion
- 6–8 banner verbose (~300px) → `<details>` collapsed mặc định
- Mỗi banner condense xuống 1–2 dòng compact

### D. tbody tổ chức lại — 18 items + 2 DONE
- T112 và T34 chuyển xuống section "✅ ĐÃ DONE" ở cuối bảng
- Thêm nút DONE button cho tất cả 18 rows còn lại
- IIFE `restoreBugDoneState` cập nhật đủ 18 `{bugId, rowId, btnId}` objects

### CSS compact summary:
```css
body { padding: 10px 14px; }
.summary-card { padding: 8px 14px; min-width: 110px; }
.section-title { margin: 12px 0 6px; }
.task-kpi .kpi { padding: 8px 12px; flex: 1 1 100px; }
.board-col { padding: 8px 10px; min-height: 80px; }
```

---

## 2. BUG-025 Fix (Applied in DB — phiên 2026-09-22)

**A021462** (鏡堂覺圓): `name_vi` sai "Kính Đường Giác Viên" → đã đúng  
**A001984** (靈祐): `name_vi` → "Quy Sơn Linh Hựu"  

SQL revert:
```sql
UPDATE people SET name_vi='...(cũ)...' WHERE id='A021462';
UPDATE people SET name_vi='...(cũ)...' WHERE id='A001984';
```

---

## 3. BUG-026 Fix (Applied in DB — phiên 2026-09-22)

**A001744** (慧辯): `name_vi` đổi từ `Thạch Đầu Hy Thiên` → `Tuệ Biện`  
Root cause: import DILA lầm lẫn định danh — `A001744` là Tuệ Biện, KHÔNG phải Thạch Đầu.

SQL revert:
```sql
UPDATE people SET name_vi='Thạch Đầu Hy Thiên' WHERE id='A001744';
```

---

## 4. T101 Status (pending admin QA)

Code đã apply từ phiên 2026-09-09:
- `app.py`: `_t86_resolve_display_name` trong nexus + curated block
- `lineage.db`: A003881 `name_vi='Nhị Tổ'` (fix typo Nhì→Nhị), A001361 `person_display_names` insert Bồ Đề Đạt Ma
- `places.html`: `_nexusResolveLabelCollisions` (greedy collision avoidance, 8 CANDS × 4 MULTS)

Còn lại: admin xác nhận live UI trên `localhost:8080/daoanh/` → Thiếu Lâm Tự Nexus.

Rollback: `git revert --no-edit <hash_T101>` (xem task file T101).

---

## 5. T140 Status (pending admin QA)

Code đã apply từ phiên 2026-09-15 (`cd247c4`, `d49c48c`):
- AbortController race-guard, breadcrumb header, right rail 2 section
- Edge ⚠ direction_mismatch, legend ngữ nghĩa đúng, zoom label, filter 3 nhóm

Còn lại: admin QA ×1 + deep-link test `?select=<id>`.

Rollback: `git revert --no-edit cd247c4` (places.html code) + `git revert --no-edit 3513640` (docs).

---

## 6. T101 Subgroup Expand Fix (2026-09-23 — Round 2)

### Triệu chứng (admin báo)
"Click Tăng Nhân → Nhà Tùy → child con bung ra đè lên các child khác, size font nhỏ, ko thấy gì, phải zoom 3 lần mới dc"

### Root cause
1. `CHILD_LABEL_MIN_ZOOM = 1.25` — scale lúc expand ~0.3–0.5, tất cả node lá bị ẩn label
2. `network.fit()` fit toàn bộ graph (trăm node) → scale quá nhỏ; các node person mới thêm nhỏ xíu

### Fix
- `CHILD_LABEL_MIN_ZOOM`: 1.25 → 0.5 (line 7391)
- Non-forcedLayout expand: `network.fit()` → `network.fit({ nodes: fitIds })` — fit về đúng các node person vừa expand (lines 7929-7937)
- Backup: `docs/sessions/2026-09-23/places.html.bak-t101-subgroup-expand-fix`

---

## 7. T101 Hierarchical Layout — Đổi layout hoàn toàn (2026-09-23 — Round 3)

### Admin request
"vẫn không được, kết quả vẫn sai như cũ, nhìn trên browse đi, hãy cho làm từng level đi, đừng dùng hình tròn căm xe nữa, cho từng tầng dữ liệu dễ hơn"

### Thay đổi
- **Xóa radial/repulsion layout** cho PLACE type Nexus grouped view
- **Dùng vis.js `layout.hierarchical`** (direction: UD, top-down):
  - Tầng 0 (level: 0) — Place center: Thiếu Lâm Tự
  - Tầng 1 (level: 1) — Groups: Kinh Điển, Tăng Nhân  
  - Tầng 2 (level: 2) — Dynasty subgroups: Nhà Tùy, Nhà Đường, ...
  - Tầng 3 (level: 3) — Person nodes: các tăng nhân
- **Giữ repulsion** cho PERSON type (Marcus teacher/student với `hasForcedLayout`)
- **Xóa arc-grid placement code** — hierarchical tự xếp theo level
- **Auto-fit** về nodes mới expand (fit `_fitIds` sau khi click dynasty)
- Browser verified: Thiếu Lâm Tự → Tăng Nhân (13 vị) → Nhà Tùy (4) → 4 person nodes hiện rõ labels, không overlap, không cần zoom thủ công
- Backup: `docs/sessions/2026-09-23/places.html.bak-t101-subgroup-expand-fix`
- Commit: `d6a326d`

---

---

## 8. T101 Orthogonal Edges + NodeSpacing Fix (2026-09-23 — Round 4)

### Admin request
"các label nhà ngũ đại chồng nhà bắc tống kìa. dùng style cạnh ống nước vuông góc đi, đừng dùng đường line vòng"

### Thay đổi
- **`nodeSpacing`: 140 → 220** — dynasty nodes cách xa hơn, labels không còn chồng
- **Orthogonal edges (cạnh ống nước vuông góc)**: thay `smooth: { type: 'curvedCW' }` → `smooth: false`
  - Thêm preprocessing trong `_nexusGroupedFinalize`: lưu `_orthoColor/_orthoOpacity` gốc, set vis.js edge `color: rgba(0,0,0,0)` (transparent)
  - Thêm `afterDrawing` handler mới: vẽ lại tất cả non-mx edges dạng ống nước vuông góc (L-shape):
    ```
    source.bottom → xuống midY → ngang đến target.x → xuống target.top
    ```
  - mx-edges vẫn do bus-bar canvas renderer xử lý (không đổi)
- **Browser verified**: Thiếu Lâm Tự Nexus → Nhà Ngũ Đại + Nhà Bắc Tống labels rõ ràng, riêng biệt; connectors vuông góc đúng style; expand dynasty → 1 person node đúng vị trí level 3
- **Text clip**: `_nexusDrawGroupedLabels` thêm `ctx.save()/ctx.clip(bbox)/ctx.restore()` cho mỗi node trong vòng lặp — text không tràn ra ngoài vành dù zoom nhỏ (root cause: fontSize = labelSize/scale → rất lớn trong world coords khi scale nhỏ)
- Backup: `docs/sessions/2026-09-23/places.html.bak-t101-orthogonal-edges`

---

---

## 9. T101 Natural Scaling Fix — Text Overflow (2026-09-23 — Round 5)

### Admin report
"vẫn không được, kết quả vẫn sai như cũ, nhìn trên browse đi : Tràn chữ trên label , zoom 3 lần mới xem dc"

### Root cause
`_nexusDrawGroupedLabels` line 7465: `var fontSize = (n._labelSize || 12) / scale;`
- Tại scale=0.373: fontSize = 11/0.373 = **29.5 world units** — text "Nhà Ngũ Đại Thập Quốc (五代十國)" rộng **485 world units** trong khi bbox chỉ **197 world units** (ratio 2.47×)
- Clip bbox cắt giữa chữ → garbled text khi zoom nhỏ

### Fix
- **Đổi `var fontSize = (n._labelSize || 12) / scale;` → `var fontSize = n._labelSize || 12;`** (natural scaling)
- Natural scaling: text trong world coords luôn = labelSize world units, co/giãn theo zoom như vis.js native
- vis.js đã size bbox node theo labelSize → text luôn fit, không bao giờ tràn
- Clip ctx.rect (đã thêm round 4) vẫn giữ nguyên như safety net, nhưng không còn cần thiết
- Xóa ctx.save/clip/restore block thừa để simplify code

---

## 10. T101 Multi-Value Dynasty Label Fix (2026-09-23 — Round 6)

### Admin report
"ô chữ nhật nằm giữa nhà Bắc Tống và nhà Bắc Tề không hiện dc chữ"

### Root cause
`grp.tang_nhan` có key `'北宋\n    五代十國'` (combined multi-value từ data). Hàm `_fmtDynasty` dịch
ra `'Nhà Bắc Tống (北宋) · Nhà Ngũ Đại Thập Quốc (五代十國)'` (42 chars) → node bbox quá rộng → collision
detection với `sg-北宋` kế bên → `if (overlap && pri >= 2) continue;` → SKIP draw label → node box hiện
đen không chữ.

### Fix
Trong `_nexusRenderGrouped` dynasty subgroup loop (~line 7643):
- Split `dyn` theo `[\n\/,，;；]+` → `dynParts`
- Nếu multi-value: `dynLabel = dynParts.join('·') + '\n(' + cnt + ')'` → `'北宋·五代十國\n(1)'` (compact, pass collision)
- Tooltip `title` giữ bản dịch đầy đủ tiếng Việt

### Verified
Debug intercept xác nhận `"北宋·五代十國"` drawn tại x=-550 (đúng giữa Bắc Tống x=-770 và Bắc Tề x=-330).
Screenshot browser: label hiển thị đúng.

- **Commit**: `be3402a`

---

## 11. T140 Regression Fix — BUG-018 + BUG-020 (2026-09-23 — Verify session)

### Verify kết quả (agent daoanh-debugger)
- BUG-017 AbortController: ✅ OK — network log xác nhận request abort khi click nhanh
- BUG-018 Default fetch: ❌ REGRESSED bởi commit `6c710b2` (T152 ancestor spine) → up=6&down=6
- BUG-019 Zoom-out label: ✅ OK — code còn nguyên (_lineageSyncCompactLabels + zoom listener)
- BUG-020 Legend text: ❌ REGRESSED bởi commit `62ad40e` (fix tên tăng nhân) → xóa legend text T140

### Fix áp dụng (commit `35b3f6b`)
- BUG-018: khôi phục `up=2&down=2` tại 3 chỗ (places.html:5137, 5147, 5316)
- BUG-020: khôi phục legend text Pháp mạch + Phả hệ mở rộng (places.html:6645, 6715)
- Verified: network log `?up=2&down=2` + DOM query legend text đúng nội dung T140

---

## 12. T164 Lineage Tree UI Cleanup (2026-09-23 — Build session)

### Thay đổi (8 bước từ audit plan ANALYZE_ONLY → APPROVED FIX)

- **S1**: `_buildFtVisTree` — xóa `\n▸ N hậu duệ` / `\n▾ N đệ tử` count string; giữ `\n▸`/`\n▾` chỉ báo. ★◉ giữ nguyên.
- **S8**: `heightConstraint.minimum` 58 → 52 (label bớt 1 dòng đếm).
- **S2**: `_renderHierarchyTree` — xóa ancestor bar block (lines ~5458-5479). Breadcrumb `#lineage-header` đủ context.
- **S3**: Toolbar HTML + JS — xóa `#lineage-zoom-in` + `#lineage-zoom-out` và eventListeners tương ứng.
- **S4**: `#lineage-legend-row` (HTML tĩnh bên dưới toolbar) thay thế `srcNote`/`src` span trong JS ctrlBars.
- **S5**: `#lineage-inspector-evidence-wrap` — collapse `flex:0 0 0px` ban đầu; `_setLineageEvidence` expand/collapse theo html.
- **S6**: Overflow node `__ov__` — `shape:'box'` → `shape:'ellipse'`, xóa `margin`.
- **S7**: `_t129NetFooter` — wrap trong `<details collapsed>`; trả `null` khi không có warnings.

### Backup
`docs/sessions/2026-09-23/places.html.bak-t164-pre`

---

## Files changed this session
- `daoanh/dashboard/dashboard_process.html` — UX reduction (heavy)
- `daoanh/docs/sessions/2026-09-22/changes.md` — BUG-025/026 docs
- `daoanh/docs/bugs.md` — BUG-025/026 + BUG-018/020 regression fix notes
- `agents/SESSION.md` — session state update
- `daoanh/tasks/T101-graph-nexus-bug-fix.md` — updated date + multi-value dynasty fix
- `daoanh/tasks/T140-phap-mach-ui-ux-fix.md` — updated date
- `daoanh/docs/ROLLBACK.md` — dashboard entry
- `daoanh/data/progress_data.json` — rebuild
- `daoanh/places.html` — T101 orthogonal edges + nodeSpacing 220 + natural scaling + multi-value dynasty fix + T140 BUG-018/020 regression fix + T164 lineage tree UI cleanup (8 edits)
