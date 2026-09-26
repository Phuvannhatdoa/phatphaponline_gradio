# Session 2026-09-24 — T130 Session 5: T129 regression + browser QA (T130 CLOSE)

**Task:** `tasks/T130-phap-mach-direct-lineage.md` (Session 5/5) | **Status:** ✅ DONE — T130 CLOSED (5/5 sessions)
**QA:** LIVE :8080 — 18/18 PASS (Phase A deep-link + Phase B T129 regression)
**Code change:** 0 (places.html KHÔNG đụng) — docs-only + 1 QA driver script mới.

---

## 1. Tóm tắt

Session 5 = bước đóng T130: **regression T129 sau khi Session 2 thay control bar tree-mode** + **browser QA toàn diện deep-link Session 4**. Không sửa code — chỉ xác minh xuyên server thật (:8080, served places.html byte-identical với working tree, sha256 khớp).

## 2. Static regression audit (31/31 PASS)

Kiểm tra từng đặc trưng T129 còn nguyên + wire đúng trong file làm việc:

| T129 feature | Trạng thái |
|---|---|
| ① `_lineageGenMap` (BFS 2 chiều) | ✅ def + dùng trong `_renderLineageNetwork` |
| ⑤ `_lineageSccEdges` (Tarjan SCC) | ✅ def + dùng + loại cycle `cycleSet.has(e.from+'|'+e.to)` khỏi cây |
| ⑦ `_t129EdgeTitle` "X truyền pháp cho Y" | ✅ chain edges + ancestor edges + network edges |
| ⑧ `_t129NodeTitle` meta | ✅ descendant + ancestor + network |
| ③ `_t129NetCtrlBar` (4 nút network) | ✅ def + wired `controls: () => _t129NetCtrlBar()` |
| ④ Tâm `_lineageNetwork.focus(center)` | ✅ |
| ⑥ `_t129NetFooter` (dropped/cycle) | ✅ def + wired `footer: () => _t129NetFooter(...)` |
| T127 shared renderer + options | ✅ `_renderHierarchyTree` + `options.controls`/`options.footer` |
| T130 Session 2 (chain ctrl bar, chooser) | ✅ Mở 1 đời tiếp / Thu gọn nhánh dưới / CTA Xem Phả hệ mở rộng |
| T130 Session 4 dead-code clean | ✅ `/api/lineage/expand?`, `expand-primary` fetch, `t130-chain-box` = 0 tham chiếu |

## 3. Verify tự động

- `node --check` places.html 3/3 blocks PASS (block 2 = 572,362 chars) — dùng extraction đúng (PowerShell trả lỗi giả `Unexpected token '>'` do regex không bỏ `>` đóng tag `<script>` + `.tmp` không .js).
- `npm run pipeline`: guard ✅ · test ✅ · UAT 3/3 ✅ · compliance ✅ · test:gov 17/17 ✅ · e2e ✅ · e2e:runtime EPERM (pre-existing, Playwright lock test-results\.last-run.json).
- Served :8080 `/places.html` sha256 == local working file (byte-identical). App đang live: port 5000 (app.py) + 8080.

## 4. Browser QA live :8080 — 18/18 PASS

Driver: `scripts/qa_t130_session5_regression.mjs` (base `_lineageState`/`_lineageNetwork` bare access, Chromium headless). Report: `docs/sessions/qa_t130_session5_regression/qa_report_t130_session5.json` + screenshots.

### Phase A — Deep-link T130 Session 4 (A1–A6)
- **A1** `?mode=lineage&focus=A008874&lm=tree` → center A008874, edges 16, mode tree, canvas hiện, tab lineage active (khác-focus path: `_t130Pending` → `selectPerson` → pending consume ~6402).
- **A2** `&chain=A009491` → `_ftExpanded = ["A008874","A009491"]` (center + child, override auto-expand).
- **A3** click mode network trên deep-link → `_lineageState.mode=network`, `_lineageNetwork` 17 nodes, URL pushState `?mode=lineage&focus=A008874&lm=network&chain=A009491`, history +1 (dedupe giữ chain).
- **A4/A4b** `goBack()` → tree (`lm=tree`, popstate restore same-focus không reload) · `goForward()` → network.
- **A5** legacy `?expand=A009491` → map `mode=lineage&focus=A009491&lm=tree`, tab lineage active.
- **A6** 0 pageerror/console.error (Phần A).

### Phase B — T129 regression trên A003623 Mã Tổ Đạo Nhất (301 nodes) (B1–B10)
- **B1** gen map: center gen=0, có thầy (gen<0) + trò (gen>0), reachable 301.
- **B2** network ordering: 295 nodes, levels `[0..4]` non-negative + ascending (sort theo level).
- **B3** `_t129NetCtrlBar` đủ 4 nút: Mở thêm đời trên ↑ / Mở thêm đời dưới ↓ / Toàn bộ nhánh / Thu gọn nhánh dưới.
- **B4** expand/fold: default 295 → all 295 → fold 295 (dữ liệu reachable đã đầy trong phạm vi — expand an toàn không crash).
- **B5** `#lineage-center` → `_lineageNetwork.focus` scale ~0.81 + center position.
- **B6/B6b** edge tooltip "Mã Tổ Đạo Nhất truyền pháp cho Bách Trượng Hoài Hải / ○ Cần khảo cứu…" · node title meta "Tôn Giả Đại Giám Huệ Năng · 慧能 / Triều đại: Nhà Đường / Tông/Phái: Thiền Tông / Đời: -2 / …".
- **B7** SCC cycle-scan 0 crash (0 true cycles cho A003623).
- **B8** research footer hiện (⚠ cảnh báo nghiên cứu, honest).
- **B9** tree↔network switch nguyên vẹn (về tree 148 nodes).
- **B10** 0 pageerror/console.error (Phần B) — request `ancestor-spine` bị abort trong GOTO chủ động đầu Phase B là navigation artifact, đã clear trước khi đo.

## 5. Files trong session

- `scripts/qa_t130_session5_regression.mjs` (mới, driver QA)
- `docs/sessions/qa_t130_session5_regression/` (report JSON + screenshots)
- `docs/tasktodo.md` (Session 5 DONE + T130 CLOSED)
- `docs/ROLLBACK.md` (row `7ac2204`)
- Không đụng `places.html` / `app.py`.

## 6. T130 tổng kết (CLOSED, 5/5 sessions)

| Session | Commit | Nội dung |
|---|---|---|
| S1 backend | `f07d8cb` | `/api/lineage/expand-primary` (limit=1, cache, has_more) + `/api/lineage/direct` |
| S2+S3 frontend core | `f125c44` | Direct-chain control bar (Fit/Tâm/Thu gọn nhánh dưới/Mở 1 đời tiếp/CTA) + `_t130Chooser` |
| S4 deep-link/state | `74ef34c` | `T130.serialize`/`_t130SyncUrl`/`restoreFromUrl`/`deepLink`/popstate + guard hooks |
| S5 QA + regression | docs này | T129 regression + browser QA 18/18 PASS |

**Ngoài scope T130 (đã document, DEFER):** `pick`/`tup` riêng biệt (gộp về `chain`), network depth `&net=` vào URL, B2 `source_authority→lineage_confidence` (cần quyết định nguồn ưu tiên — chỉ hiển thị, không tự chọn).

## 7. Next

T130 đóng → task list tiếp theo theo `docs/tasktodo.md` (chờ Lee/admin review row này + QA report snapshots).