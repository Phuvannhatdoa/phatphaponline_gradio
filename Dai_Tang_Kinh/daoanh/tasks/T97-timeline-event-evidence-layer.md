---
id: T97
title: "Timeline/Event Evidence Layer — Mở tab Sự Kiện + Niên Đại cho person (T82 data reuse)"
module: ui
priority: high
status: done
depends_on: [T82, T79, T81, T83, T109]
created: 2026-09-23
updated: 2026-09-23
done_when:
  - "[x] Gỡ chặn tab sukien/timeline trong person mode (loadTabData whitelist)"
  - "[x] loadSukienTab + renderPersonSukienTab wire person qua /api/persons/<id> → timeline[]"
  - "[x] loadTimelineTab + renderPersonTimelineTab wire person (cùng nguồn vn_person_events)"
  - "[x] Helper _personEventsHtml dùng chung (sort theo năm, icon, srcMap, confidence)"
  - "[x] Node syntax + @babel/parser 3 blocks/0 error"
  - "[x] Smoke: A000001 floruit 1053 DILA_active + dai_hue_tong_cao (7 events birth/death/KeyLifeEvent)"
  - "[x] Backup places.html.bak-t97-20260923 + 1 commit build revert-friendly"
---

# T97 — Timeline/Event Evidence Layer (mở tab cho person)

> **Module:** `ui` (`places.html`) · **Priority:** high · **Status:** done
> **Type:** build additive (UI-only, 0 ALTER, 0 Schema, 0 DB, 0 API, 0 route mới)
> **Created:** 2026-09-23 · **Updated:** 2026-09-23
> **Depends on:** T82 (wire timeline vn_person_events), T79/T81 (birth/death/active-floruit), T83/T109 (event source)
> **SSOT canonical:** `tasks/T97-timeline-event-evidence-layer.md` (1 unique)

---

## 1. Bối cảng (Context)

Trước T97, `places.html` đã có:
- **Place mode:** tab ⚡ Sự Kiện (`loadSukienTab`/`renderSukienTab`) render `/api/places/<id>/events` (T97 Build 2 — nexus_events 10,458 + text_links 17,284 + events reviewed/candidate 3,530) — hoạt động đầy đủ.
- **Person mode:** **chặn cứng** mọi tab ngoài `lineage`/`nexus` (loadTabData ~L2191) → nhân vật chỉ có block nhỏ `personEventsBlock` trong sidebar khi mở người, **không tab riêng**.

Dữ liệu person đã có sẵn từ T82:
- `vn_person_events` 5,351 rows (birth/death/active/floruit/KeyLifeEvent/Contribution/PhilosophicalStance) + `source` (dila_active_regex/dila_person_regex/legacy_ttl) + `confidence`.
- `GET /daoanh/api/persons/<id>` (app.py:16492) **đã trả `timeline[]`** — chỉ thiếu UI tận dụng.

→ T97 mở 2 tab cho person, tái dùng endpoint có sẵn, **0 route mới**.

## 2. Giải pháp (Solution) — additive UI

**File duy nhất:** `daoanh/places.html` (101 insertions, 0 deletions).

1. **loadTabData whitelist** (~L2191): person mode được phép `sukien` + `timeline` (ngoài lineage/nexus).
2. **loadSukienTab person branch:** `_currentEntityType==='person'` → fetch `/daoanh/api/persons/<id>` → `renderPersonSukienTab`; place giữ nguyên.
3. **renderPersonSukienTab (mới):** header "Sự Kiện Liên Quan · Đang xem <tên>" + `_personEventsHtml(tl)`; empty → "Chưa có sự kiện...".
4. **loadTimelineTab person branch:** tương tự → `renderPersonTimelineTab`.
5. **renderPersonTimelineTab (mới):** header "Niên đại lịch sử" + `_personEventsHtml(tl)`.
6. **`_personEventsHtml(tl)` (helper dùng chung):** sort theo `event_year` (null → cuối), render card mỗi mốc: icon (🌱 birth/🪔 death/📅 active/📍 floruit/✦ khác) + `event_type` chip + năm (TCN/CE, — nếu null) + confidence % + nguồn (srcMap `dila_active_regex`→"DILA (hoạt động)", `dila_person_regex`→"DILA (sinh/tịch)", `legacy_ttl`→"TTL duyệt thủ công"). Mọi giá trị qua `_escHtml`.

**Lưu ý route:** `/api/persons/<id>` trả `jsonify(result)` **không có field `ok`** (chỉ 404 mới có `{ok:false}`) → điều kiện person dùng `Array.isArray(d.timeline)`.

## 3. Kết quả (Results) — 2026-09-23

| Kiểm tra | Kết quả |
|----------|---------|
| Thay đổi | `places.html` +101 / −0 (additive thuần) |
| Syntax | `node --check` 3 inline script blocks: 0 err |
| Babel | `@babel/parser` 3 blocks: 0 err |
| Smoke person | A000001 → 1 event floruit 1053 · source `dila_active_regex` · conf 0.55 |
| Smoke multi | `dai_hue_tong_cao` → 7 events (Contribution/KeyLifeEvent/PhilosophicalStance/birth/death) |
| Render test | `_personEventsHtml` sort (null cuối), TCN/CE, icon, srcMap, conf: PASS, không undefined/NaN |
| Guard | `npm run guard` PASS (SSOT root) |
| Test/E2E | `npm run test` PASS · `npm run e2e` PASS |
| Lint | `npm run lint` pre-existing env fail (node --check ESM trên file tạm; script không quét places.html) |

**Số liệu DB (read-only, 0 mutation):** `vn_person_events` = 5,351 rows; top person `dai_hue_tong_cao`/`ngu_to_phap_dien` = 7 events.

## 4. Backup & Revert

| Hạng mục | Chi tiết |
|----------|----------|
| Backup UI | `docs/sessions/places.html.bak-t97-20260923` (đã commit cùng docs) |
| Code revert | `git revert --no-edit <sha_build_T97>` (chỉ places.html, 0 DB) |
| DB | **Không đụng** (0 ALTER, 0 INSERT, 0 write) |

## 5. Verification Commands

```bash
# Syntax + parse
node --check <extracted scripts> ; npm run test ; npm run e2e

# Smoke backend (read-only)
python -X utf8 -c "import sqlite3; con=sqlite3.connect('data/lineage.db'); print(con.execute(\"SELECT COUNT(*) FROM vn_person_events WHERE person_id='A000001'\").fetchone())"
```

## 6. Files Changed

- `daoanh/places.html` (build, commit riêng)
- `docs/sessions/places.html.bak-t97-20260923` (backup)
- `tasks/T97-timeline-event-evidence-layer.md` (canonical, new)
- `docs/sessions/2026-09-23_t97-person-events-tabs.md` (session)
- `docs/tasktodo.md` (T97 → DONE)
- `docs/ROLLBACK.md` (row build + row docs)
- `data/progress_data.json` (regen)

## 7. Acceptance Criteria

- [x] Person chọn tab ⚡ Sự Kiện / ⏱ Niên Đại hiển thị timeline thật (không placeholder chặn)
- [x] Place mode regression: place tab Sự Kiện giữ nguyên logic cũ
- [x] Canonical task + session + tasktodo + ROLLBACK + dashboard regen
- [x] Commit build riêng / docs riêng → revert từng phần

---

*Canonical T97 closure — additive, 0 ALTER, 0 Schema, 0 DB write, 0 route mới. Chờ Admin QA x1 trên :5000 (thử A000001 + 1 nơi place) → confirm.*