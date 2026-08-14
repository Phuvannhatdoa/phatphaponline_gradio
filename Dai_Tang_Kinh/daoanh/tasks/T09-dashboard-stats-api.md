---
id: T09
title: Dashboard stats API 404 fix
module: Hạ tầng / Docs
priority: high
status: done
depends_on: []
created: 2026-07-29
updated: 2026-08-14
done_when: GET /daoanh/api/admin/dashboard/stats trả 200 JSON
---

# T09 — Dashboard stats API 404 fix

## Mục tiêu
Trang `/daoanh/admin/` (Dashboard v4.0) gọi `/api/admin/dashboard/stats` đang trả 404. Cần route trả số liệu thật để UI hiển thị.

## Cách tiếp cận
- Tìm route đang tồn tại tương đương (grep app.py).
- Nếu thiếu → viết route trả JSON từ query lineage.db (places/people/ttl counts).
- Verify 200 qua :5000 và :8080.

## Acceptance criteria (checklist)
- [x] Grep xác nhận route hiện có / chưa có (app.py:6057 có `/daoanh/api/dashboard/stats`; `/admin/` alias chưa có)
- [x] Route trả JSON thật (counts từ DB — people, marcus, name_vi_map, namevi_map_places, places_pending, TTL)
- [x] GET 200 qua app.py:5000
- [x] GET 200 qua gateway:8080

## Kết quả (2026-08-14)
Thêm alias route `/api/admin/dashboard/stats` + `/daoanh/api/admin/dashboard/stats` vào `api_dashboard_stats()` (app.py:6057). 5/5 path trả 200. Log: `docs/sessions/2026-08-14_t09_dashboard_stats_api.md`.
