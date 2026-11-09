NHÁP — chờ Admin duyệt trước khi dán vào docs/bugs.md

> OI-14 (2026-10-21). Hai entry dưới đây chỉ là bản nháp, soạn từ báo cáo gốc, chưa ghi vào `docs/bugs.md`.
> Trạng thái đề xuất là `pending_confirm`, chưa đánh DONE: theo `docs/bugs.md` header, chỉ Admin mới đóng bug.

---

## BUG-048 — Cột Claude trong namevimap.html không hiện số đếm (done/total)

**Route/URL:** `http://127.0.0.1:8080/daoanh/admin/namevimap.html` → TAB 3 "🔧 TTL ETL" — header cột "Claude" của bảng Bulk FLAG Queue (`#etl-flag-queue-table`)
**Task:** [T435](../tasks/T435-bug048-claude-column-no-count.md)
**Thời gian phát hiện:** 2026-10-20 (suy từ thư mục backup `docs/sessions/2026-10-20/T435/`; báo cáo không ghi giờ phát hiện — Admin xác nhận)
**Expected:** Header cột Claude hiện số đếm `(done/total)` giống cột Gemini, ví dụ `CLAUDE (48,646/48,673)`.
**Actual:** Header "Claude" trống, không có số. Endpoint `GET /api/admin/codex-transliterate/status` chưa tồn tại (404).
**Root cause:** Lỗi contract ở 3 lớp, không phải lỗi dữ liệu:
  1. API: `app.py` chỉ có `ai_transliterate_status()` (đếm `ai_person_name` = Gemini), không có route đếm `codex_person_name` (Claude).
  2. Renderer: header `<th class="codex-name-header">` (`namevimap.html:728`) không có `<span>` để JS ghi số, trong khi header Gemini có `<span id="ai-col-status">`.
  3. JS: không có hàm fetch cho Claude (chỉ có `loadAiColStatus()`).
  Đếm trần `COUNT(*)` không JOIN sẽ cho 49,335 > 48,673 (101%) — sai, nên phải JOIN `people` (xem Evidence).
**Evidence (SQL trên `data/lineage.db`, đo khi audit):**
  - `SELECT COUNT(*) FROM codex_person_name WHERE name_vi IS NOT NULL AND name_vi != ''` → 49,335 (không dùng, vì không JOIN)
  - `SELECT COUNT(DISTINCT c.dila_id) FROM codex_person_name c JOIN people p ON p.id = c.dila_id WHERE c.name_vi IS NOT NULL AND c.name_vi != '' AND p.name_zh IS NOT NULL AND p.name_zh != ''` → 48,646 (con số dùng)
  - `SELECT COUNT(*) FROM people WHERE name_zh IS NOT NULL AND name_zh != ''` → 48,673 (mẫu số)
**Changed files:**
  - `daoanh/app.py` — thêm route `codex_transliterate_status()` (~dòng 16286), cùng pattern auth + JSON với `ai_transliterate_status()`
  - `daoanh/admin/namevimap.html` — dòng ~728 (thêm `<span id="codex-col-status">`), ~2394 (hàm `loadCodexColStatus()`), ~1074 (gọi sau `loadAiColStatus()`)
**Test evidence:**
  - `python -m py_compile app.py` → OK
  - Gọi API không token → 403 `{"error":"Unauthorized","ok":false}`
  - Gọi API với `X-Session-Token` hợp lệ → 200 `{"ok":true,"done":48646,"total":48673,"pct":99.9}`
  - Token sai (edge) → 403, server không crash
  - UI (trình duyệt thật, namevimap.html, tab TTL ETL): header "CLAUDE (48,646/48,673)"; cột Gemini vẫn "GEMINI (48,673/48,673)" (không regression)
  - Network: `/api/admin/codex-transliterate/status` → 200 OK (2 lần qua gateway 8080)
  - **Chưa test:** case DB lock thật. Báo cáo chỉ dựa vào việc code bọc try/except theo pattern của endpoint Gemini. Ghi rõ là chưa test trực tiếp.
**Trạng thái:** pending_confirm — chưa commit (chờ daoanh-qa độc lập và Admin xác nhận DONE). Backup trước sửa: `docs/sessions/2026-10-20/T435/app.py.bak`, `docs/sessions/2026-10-20/T435/namevimap.html.bak`.
**Nguồn:** `docs/T435_BUG048_FINAL_REPORT.md`

---

## BUG-051 — /daoanh/places: cây Truyền Thừa không hiện mũi tên, canvas đen trống

**Route/URL:** `http://127.0.0.1:8080/daoanh/places` → tìm "Nghĩa Huyền" (A003627) hoặc "Mã Tổ Đạo Nhất" (A038890) → tab Truyền Thừa
**Task:** [T438](../tasks/T438-bug051-places-lineage-arrows-missing.md)
**Thời gian phát hiện:** không ghi trong báo cáo; backup 2026-10-20 (`docs/sessions/2026-10-20/BUG-051/`) — Admin xác nhận
**Expected:** Cây truyền thừa hiện node và mũi tên thầy → trò (ví dụ Hi Vận → Nghĩa Huyền), không có nền đen.
**Actual:** Canvas vis.Network trống (pixel tại tâm `rgba(0,0,0,0)`). Đo trước sửa: `#lineage-inspector` rộng 437.48px (flex-basis khai báo 300px); `#lineage-canvas` chỉ 172.5 × 430px. Camera đứng ở x=4920 trong khi node trung tâm ở x=0.
**Root cause:** Lớp renderer/layout, 2 nguyên nhân độc lập (dữ liệu và API đều đúng, 80 node / 79 edge):
  - A (CSS, luôn xảy ra): `#lineage-inspector` có `flex:0 0 300px` nhưng thiếu `min-width:0`. Flex item mặc định `min-width:auto`, nội dung không ngắt dòng (bio DILA dài, URL không khoảng trắng) đẩy panel rộng ra, bóp canvas.
  - B (race, lộ rõ với cây lớn > 50 đời sau khi T152 merge spine): trong `_renderHierarchyTree()`, `focus()` gọi qua biến module-level `_lineageNetwork` chưa được gán khi sự kiện `afterDrawing` bắn; và layout hierarchical (blockShifting/edgeMinimization) còn dịch node sau lần focus đầu.
**Evidence:** Đo JS console trước sửa — inspector 437.48px, canvas 172.5×430px, pixel tâm trong suốt; camera x=4920 so với node x=0.
**Changed files:** `daoanh/places.html`
  - dòng ~745: `#lineage-inspector` thêm `min-width:0;max-width:300px;overflow-x:hidden`
  - dòng ~6864–6886: `focus()` dùng closure `network` (instance vừa tạo) thay biến module-level; thêm `setTimeout(..., 150)` focus lại một lần, chỉ khi `_lineageNetwork === network`
**Test evidence:**
  - Case yêu cầu: "Nghĩa Huyền" trên tab Truyền Thừa → hiện "Hi Vận" → mũi tên trắng → "Nghĩa Huyền", cả khi view mặc định lẫn sau khi ancestor-spine (T152) merge (6–9s) — PASS
  - Fallback monk khác: "Mã Tổ Đạo Nhất" → "Thiên Chân Tự Tính" → mũi tên xanh → "Mã Tổ Đạo Nhất" — PASS
  - Regression: "Phả hệ mở rộng" (network mode) của Mã Tổ Đạo Nhất → cây + mũi tên đúng, inspector 300px cố định — PASS
  - Console/Network: không có lỗi JS mới (chỉ warning "development build")
**Trạng thái:** pending_confirm — chưa commit (chờ daoanh-qa độc lập và Admin xác nhận DONE). Backup: `docs/sessions/2026-10-20/BUG-051/places.html.bak-20261020_182252`. Revert: khôi phục từ backup, hoặc `git checkout -- Dai_Tang_Kinh/daoanh/places.html` khi đã commit.
**Rủi ro còn lại:** fix B dùng timeout cố định 150ms thay vì chờ `stabilizationIterationsDone`. Có thể không đủ với cây > 100 node hoặc máy chậm. Chưa test cây > 100 node.
**Nguồn:** `docs/BUG-051_PLACES_LINEAGE_ARROWS_REPORT.md`

---

## Ghi chú cho Admin khi duyệt (KHÔNG dán vào bugs.md)

- Thời gian phát hiện của BUG-048 và BUG-051 là suy từ thư mục backup, không phải số đo trong báo cáo. Admin cần xác nhận hoặc điền lại.
- Hai báo cáo chưa có commit. Cả hai file `places.html` và `app.py` đang có WIP của phiên khác (xem OI-6/OI-7/OI-9), nên commit phải tách hunk theo task.
- Phát hiện thêm khi đối chiếu `docs/bugs.md`: BUG-046 chưa có entry trong `bugs.md`, dù có báo cáo `docs/BUG-046_claude_column_namevimap_REPORT.md`. BUG-047 chỉ thấy được nhắc trong comment code (`places.html`, `app.py`), chưa thấy báo cáo riêng. Không đưa vào nháp này vì ngoài phạm vi OI-14 (chỉ BUG-048 và BUG-051).
