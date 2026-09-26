# Session 2026-09-23 — T97 Timeline/Event Evidence Layer (mở tab cho person)

> **Task:** T97 — Timeline/Event Evidence Layer · **Build** (additive UI)
> **Build commit:** `94a8c00` (feat: T97 enable Sukien+Timeline tabs for person mode)
> **Docs commit:** `cfa92aa215fbb6315ec3fc2809914c1bb0cce6f4` (sẽ hash-fill)
> **Chế độ:** build sau khi Lee duyệt "Đồng ý build"

---

## 1. Bối cảnh phiên này

- Phiên trước (2026-09-22): khép T162/T150b (reseed name_vi) hoàn toàn — DB apply, verify, docs, dashboard, report 155 ambiguous `docs/t162_ambiguous_155.csv`.
- Session này: Lee yêu cầu "ok, hãy tiếp tục công việc của dự án" → agent đề xuất T97 Timeline/Event Evidence Layer làm việc độc lập tiếp theo (không chạm WIP agent khác).
- Lee chốt scope **Phương án A — Bỏ chặn + wire 2 tab cho person** (tái dùng endpoint/source có sẵn, ít rủi ro).

## 2. Đã làm (Build T97)

### Khảo sát (đã verify thật)
- Backend đã có `GET /api/places/<id>/events` (app.py:7568) — nexus_events/text_links/events (candidate+reviewed) → tab Sự Kiện place đầy đủ.
- Backend đã có `GET /api/persons/<id>` (app.py:16492) trả `timeline[]` từ `vn_person_events` (T82 step4, app.py:16534-16552) — 5,351 rows.
- Frontend chặn person hard ở `loadTabData` (places.html:2191): chỉ cho lineage/nexus.

### Sửa đổi — `daoanh/places.html` (+101/−0)
1. **loadTabData whitelist** (~L2191): thêm `sukien` + `timeline` vào danh sách tab cho phép trong person mode.
2. **loadSukienTab person branch:** `_currentEntityType==='person'` → fetch `/daoanh/api/persons/<id>` → `renderPersonSukienTab`; place giữ nguyên.
3. **renderPersonSukienTab (mới):** header "Sự Kiện Liên Quan · Đang xem <tên>" + `_personEventsHtml(tl)`; empty → "Chưa có sự kiện đã xác minh cho nhân vật này".
4. **loadTimelineTab person branch:** tương tự → `renderPersonTimelineTab`.
5. **renderPersonTimelineTab (mới):** header "Niên đại lịch sử" + `_personEventsHtml(tl)`.
6. **`_personEventsHtml(tl)` helper dùng chung:** sort `event_year` (null → cuối, Infinity), card: icon (🌱/🪔/📅/📍/✦) + `event_type` chip + năm (TCN/CE, "—" null) + confidence % + srcMap nguồn. `_escHtml` mọi chuỗi.

**Lưu ý route:** `/api/persons/<id>` trả `jsonify(result)` không có `ok` (chỉ 404 mới `{ok:false}`) → client check `Array.isArray(d.timeline)` chứ không check `d.ok`.

### Backup trước khi sửa
- `docs/sessions/places.html.bak-t97-20260923` (650,825 bytes → pre-edit).

## 3. Kết quả verify

| Hạng mục | Kết quả |
|----------|---------|
| `node --check` 3 script blocks | ✓ 0 err |
| `@babel/parser` 3 blocks | ✓ 0 err |
| Smoke A000001 | `floruit 1053 'Hoạt động khoảng 1053' dila_active_regex conf 0.55` (1 event) |
| Smoke `dai_hue_tong_cao` | 7 events (Contribution/KeyLifeEvent/PhilosophicalStance/birth/death) |
| Render test `_personEventsHtml` | sort, TCN/CE, icon, srcMap, conf — pass, 0 undefined/NaN |
| `npm run guard` | ✓ PASS (SSOT root = visjs-app) |
| `npm run test` | ✓ PASS |
| `npm run e2e` | ✓ PASS (all pages) |
| `npm run lint` | pre-existing env (node --check ESM trên file tạm) — script không quét places.html |

Lint fail là **pre-existing** (script `scripts/lint-check.ps1` chỉ check `admin/placevn.html`, `admin/index.html`, `admin/zenlineage_review.html`; không liên quan edit T97).

## 4. Commit

| Commit | Nội dung | Revert |
|--------|----------|--------|
| `94a8c00` | build: places.html +101 (T97 UI) | `git revert --no-edit 94a8c00` |
| `cfa92aa215fbb6315ec3fc2809914c1bb0cce6f4` | docs: task T97 + session + tasktodo + ROLLBACK + dashboard | `git revert --no-edit cfa92aa215fbb6315ec3fc2809914c1bb0cce6f4` |

DB: **không đụng** (0 write). Backup UI: `docs/sessions/places.html.bak-t97-20260923`.

## 5. Việc tiếp theo
- **Chờ Lee QA x1 trên :5000** (sau khi restart T133-T136): thử person A000001 → tab ⚡ Sự Kiện + ⏱ Niên Đại hiển thị timeline; nơi place (vd Thiếu Lâm Tự) → regression. Nói "T97 done".
- Khi xác nhận: đóng taskdone, cập nhật ADMIN_REVIEW_DASHBOARD nếu cần.