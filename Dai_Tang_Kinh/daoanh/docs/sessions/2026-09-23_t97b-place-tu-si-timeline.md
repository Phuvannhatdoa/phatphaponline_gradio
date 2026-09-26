# Session 2026-09-23 — T97b: Tab Sự Kiện place — "Tu Sĩ Liên Quan · Timeline" (co-mention bridge)

## Mục tiêu
Mở rộng T97 (đã bật tab Sự Kiện/Niên Đại cho person) sang chiều place:
hiển thị section "Tu Sĩ Liên Quan · Timeline" trong tab Sự Kiện của một place —
các tu sĩ xuất hiện cùng place trong passage CBETA (nexus co-mention) và có timeline vn_person_events.

## 1. Q&A Trước Build (2026-09-23)
Lee hỏi "code xác định sự kiện trong Tab Sự Kiện = sự kiện trích dẫn trong kinh xoay quanh Thiếu Lâm Tự
hay sự kiện xoay quanh tu sĩ có event timeline liên quan Thiếu Lâm Tự?"

Agent xác định:
- Tab Sự Kiện place hiện là semantics (a): nexus_events (co-mention, passage CBETA nhắc tu sĩ+nơi) +
  event_text_link (trích dẫn kinh cụ thể) + events/event_entities (entity_type='place').
- `vn_person_events` KHÔNG có cột place → không có quan hệ nơi→tu sĩ trực tiếp.
- Cầu nối duy nhất = nexus_events co-mention.
- Thiếu Lâm Tự = PL022435 (name_zh 少林寺) → `_resolve_dila_id` → PL000000023255 (DILA 12-digit).
  👉 **Pitfall:** query trực tiếp PL022435 = 0 rows (format 6-vs-12 digit); phải resolve qua map.
- Kết quả thật: 24 nexus / 31 text_link / 1 event · 20 co-mention persons · 3 có timeline.

Lee chốt: "Đồng ý build" → T97b.

## 2. Build
### Backend (app.py `api_places_events` L7658, +32 dòng)
```python
person_ids = sorted({n['person_dila_id'] for n in nexus if n.get('person_dila_id')})
# query vn_person_events filter event_type IN (active/floruit/birth/death/KeyLifeEvent/Contribution/PhilosophicalStance)
# ORDER BY person_id, event_year IS NULL, event_year ASC
# build by_pid + name_map (từ nexus); trả jsonify thêm "person_timelines"
```
### Frontend (places.html `renderSukienTab`)
insert section "Tu Sĩ Liên Quan · Timeline" trước `if (mentionCount === 0 && t97Events.length === 0)`:
- `personTimelines = d.person_timelines || []` → `ptWithEvents = filter(pt => pt.timeline.length>0)`
- per-person card: name + name_zh + person_dila_id + chip "Kinh: source_book"
  + mô tả "Đề cập cùng passage CBETA với nơi này (co-mention)" + `_personEventsHtml(pt.timeline)`
- reuse `_personEventsHtml` (helper T97) — hoisting OK (cùng script block #5)

## 3. Verify
- python -m py_compile app.py OK
- node --check + @babel/parser 3 scripts 0 err
- Smoke test_client: `/daoanh/api/places/PL000000023255/events` → `person_timelines` 3 entries
  (A008827 floruit 805; A009306 death 709+floruit 709; A009457 floruit 778)
- `npm run guard` PASS · `npm run test` PASS · `npm run e2e` PASS
- `npm run lint` FAIL pre-existing (lint-check.ps1 chỉ quét admin/placevn.html + index.html + zenlineage_review.html,
  node --check ESM break — không liên quan T97b)

## 4. Concurrency — Agent T101 chạy song song (QUAN TRỌNG)
Trong lúc build, agent khác (T101) đã `git add` working tree → UI section T97b trong places.html
bị sweep vào commit T101 của họ. Hệ quả:
- **HEAD places.html ĐÃ có UI section T97b đầy đủ** (line ~9513-9540, verify markers OK)
- Phần còn lại trong working places.html lệch HEAD là **WIP T101** (fontScale line 7464-7484) — KHÔNG đụng
- **app.py backend T97b commit riêng**: `ed03c86` ("feat: T97b places API — person_timelines cross-ref vn_person_events")
- Backup pre-edit: `docs/sessions/places.html.bak-t97b-20260923` (664,605 bytes, 0 left trong working diff)

⚠️ Khi revert T101 commit có thể kéo theo UI section T97b → kiểm tra trước.

## 5. Docs
- Task: `tasks/T97b-place-tu-si-timeline-events.md`
- tasktodo: T97b DONE
- ROLLBACK row `ed03c86`
- ADMIN_REVIEW_DASHBOARD item 17 (T97b QA) — cập nhật E section
- Dashboard regen `data/progress_data.json`

## 6. Next
- Chờ Lee QA :5000: search "Thiếu Lâm Tự" → tab Sự Kiện → "Tu Sĩ Liên Quan · Timeline" (3 tu sĩ)
- Sau khi T101 ổn định: cân nhắc tách UI section T97b ra khỏi commit T101 nếu cần rollback gọn
  (hiện tại nằm an toàn trong HEAD)