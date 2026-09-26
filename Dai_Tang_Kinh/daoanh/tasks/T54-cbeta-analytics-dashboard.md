---
id: T54
title: "CBETA Analytics & Admin Dashboard"
module: CBETA Analytics / UI
priority: medium
status: pending
depends_on: [T50, T53]
created: 2026-08-26
updated: 2026-08-26
done_when: >
  Admin CBETA dashboard page showing import status, translation coverage,
  entity distribution, fuzzy quality, SAT/Toh coverage,
  Home page CBETA tab functional with catalog browser
---

# T54 — CBETA Analytics & Admin Dashboard

> **Lưu ý:** Task này trước đây mang số **T52**, được đổi sang T54 vào 2026-08-26
> để nhường số T52 cho chức năng mới "Đối Chiếu Tam Tạng".

## Mục tiêu
Xây dashboard cho admin theo dõi tình trạng CBETA data + implement Home page CBETA tab.

## Audit Findings (2026-08-26)
- Text import: 5/3,122 = **0.16%**
- Translation: 46/7,563 = **0.6%**
- Entity links: 378,483 but **no aggregate view**
- Fuzzy matches: 61,706 but **91% noise**
- Home page CBETA tab: **stub only**

## Subtasks

### T54a — CBETA Stats Dashboard
- New page: `admin/cbeta-dashboard.html`
- Sections:
  - Text Import Status (5/3,122 with breakdown by series)
  - Translation Coverage (46/7,563 with backfill progress)
  - Entity Mention Distribution (places vs persons, top 20)
  - Fuzzy Match Quality (histogram: 60-70, 70-80, 80-90, 90-100)
  - SAT/Toh Crossref Coverage (2,913/3,122 = 93% SAT, 10/3,122 = 0.3% Toh)
  - Legacy Canon Mapping (2,698 from buddhist_db.sqlite)

### T54b — "Kinh Điển Liên Quan" Analytics
- Enhancement to existing `/api/places/<id>/cbeta` endpoint
- Add: "Thiếu Lâm Tự xuất hiện trong 15 kinh, 3 dòng/triều đại"
- Show mention count per text, dynasty distribution

### T54c — Home Page CBETA Tab
- Update `home.html` — implement Dai Tang tab (currently stub)
- Features:
  - Search 3,122 texts by title (Chinese/Vietnamese)
  - Filter by dynasty, series, translator
  - Click text → show metadata (juans, dynasty, translator, SAT link)
  - Link to SAT Daizokyō for fulltext

### T54d — CBETA Quality Report Card
- Auto-generated weekly snapshot
- Script: `scripts/t54_weekly_quality_snapshot.py`
- Stores in `cbeta_quality_history` table
- Trend: import count, translation count, quality score over time

## API Changes
- New: `GET /admin/cbeta/dashboard-data` — all stats in one call
- New: `GET /api/cbeta/catalog` — public catalog browser (paginated, searchable)
- New: `GET /api/cbeta/catalog?dynasty=唐&series=T` — filtered catalog

## Frontend
- New: `admin/cbeta-dashboard.html`
- Update: `home.html` — implement CBETA tab
- Update: `admin/index.html` — add CBETA quality card

## Estimated Effort: ~12 hours
