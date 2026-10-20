---
id: T97b
title: "Tab Sự Kiện place: Section Tu Sĩ Liên Quan · Timeline (co-mention → vn_person_events)"
priority: high
status: done
owner: AI Engineer (build) · Lee Tổng (QA confirm)
module: Timeline / Event Evidence
created: 2026-09-23
updated: 2026-09-23
---
# T97b — Tab Sự Kiện place: Section "Tu Sĩ Liên Quan · Timeline" (co-mention → vn_person_events)

**Status:** DONE (build `ed03c86` + docs) — CHỜ ADMIN QA (item 17 ADMIN_REVIEW_DASHBOARD)
**Date:** 2026-09-23
**Loại:** additive (0 ALTER/0 Schema/0 DB/0 route mới)
**Revert:** `git revert --no-edit ed03c86` (app.py backend); UI section bị sweep vào commit T101, kiểm tra trước khi revert T101.

## 1. Mục tiêu
Khi mở tab ⚡ Sự Kiện của một **place** (vd Thiếu Lâm Tự), hiển thị thêm section
**"Tu Sĩ Liên Quan · Timeline"** — các tu sĩ xuất hiện cùng place trong passage CBETA
(`nexus_events` co-mention) và có timeline trong `vn_person_events`.

## 2. Semantics (xác định rõ, tránh overclaim)
- Tab Sự Kiện place = các sự kiện **được trích dẫn trong kinh điển (CBETA passage)** xoay quanh nơi đó.
- GPU bridge: tu sĩ ↔ place **KHÔNG** có cột place trong `vn_person_events`;
  cầu nối duy nhất = `nexus_events` co-mention (passage CBETA nhắc cùng lúc tu sĩ + nơi).
- UI ghi rõ **"Đề cập cùng passage CBETA với nơi này"** — KHÔNG khẳng định tu sĩ trụ tại nơi
  (đó là inference cần nghiên cứu riêng).

## 3. Backend (app.py `api_places_events` L7658)
Cross-ref `vn_person_events` cho các person co-mention:
- `person_ids` = person_dila_id duy nhất trong `nexus_events`
- Query `vn_person_events` filter `event_type IN ('active','floruit','birth','death','KeyLifeEvent','Contribution','PhilosophicalStance')`
- ORDER BY `person_id, event_year IS NULL, event_year ASC`
- Build `by_pid` dict + `name_map` lấy person_name_vi/zh + source_book từ nexus
- Trả thêm field `person_timelines` (additive, không đổi field cũ)
- Ví dụ Thiếu Lâm Tự: 20 co-mention persons → 3 có timeline
  (A008827 floruit 805; A009306 death 709 + floruit 709; A009457 floruit 778)

## 4. Frontend (places.html `renderSukienTab`)
Section "Tu Sĩ Liên Quan · Timeline" render TRƯỚC empty-check (`mentionCount===0 && t97Events.length===0`):
- `personTimelines = d.person_timelines || []` → filter `pt.timeline.length>0`
- Mỗi person: tên (person_name_vi || name_zh || dila_id) + name_zh + person_dila_id + chip "Kinh: source_book"
  + dòng "Đề cập cùng passage CBETA với nơi này (co-mention)" + `_personEventsHtml(pt.timeline)`
- Reuse helper `_personEventsHtml` (T97) — sort năm null→cuối, icon, srcMap, confidence

## 5. Verify
- `python -m py_compile app.py` OK
- node --check + @babel/parser places.html 0 err
- Smoke test client: `/daoanh/api/places/PL000000023255/events` → `person_timelines` 3 entries
- `npm run guard` / `npm run test` / `npm run e2e` PASS
- Working-tree concurrency: UI section bị agent T101 sweep vào commit T101 (HEAD places.html đã có đầy đủ);
  phần app.py của T97b commit riêng `ed03c86`.

## 6. QA cho Admin
- :5000 → search "Thiếu Lâm Tự" → tab Sự Kiện → thấy section "Tu Sĩ Liên Quan · Timeline" (3 tu sĩ)
- Xác nhận dòng ghi chú co-mention (không overclaim trụ tại nơi)
- Regression: place khác (vd A000001 person) tab Sự Kiện/Niên Đại không đổi