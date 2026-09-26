---
id: T80
title: "Web Enrichment Cache — Cập nhật tin mới từ Internet cho Place/Person"
module: Place / Person Content
priority: medium
status: done
depends_on: [T73]
created: 2026-09-01
updated: 2026-09-01
completed: 2026-09-01
done_when: >
  User xem profile địa danh/tăng nhân → thấy panel "Thông Tin Cập Nhật Từ Web" và nút "Cập nhật".
  Click → Wikipedia search → Gemini AI tóm tắt → lưu vào web_enrichment_cache.
  Người sau xem cùng entity → thấy ngay summary đã cache (cooldown 30 ngày).
  Nút "Báo lỗi" → admin kiểm tra qua admin/web_enrichments.html.
---

# T80 — Web Enrichment Cache

## Mục tiêu

Cho phép user lấy thông tin mới nhất từ internet (Wikipedia) cho bất kỳ địa danh/tăng nhân nào
trong DB, AI tóm tắt bằng tiếng Việt học thuật, lưu cache để người sau xem không cần fetch lại.

**Ví dụ**: "Bạch Mã Tự được UNESCO công nhận 2026" — DILA chưa có, nhưng Wikipedia có.

## Kiến trúc

```
User click "🌐 Cập nhật" trên profile địa danh/tăng nhân
  → POST /daoanh/api/entity/<id>/web-enrich
      → Check cooldown (30 ngày) → nếu đã có, trả cache
      → Lookup entity name từ places_dila / people
      → Wikipedia API (vi → zh fallback): tìm theo name_en / name_zh
      → Gemini AI tóm tắt → 150-250 từ tiếng Việt học thuật
      → Lưu vào web_enrichment_cache
  → Hiển thị panel với summary + link nguồn + ngày
  → Nút "Báo lỗi" → report_count++, status='reported' khi >= 2
```

## Subtasks

- [x] T80a: Bảng `web_enrichment_cache` (migration script t75_web_enrichment.py)
- [x] T80b: API `GET /daoanh/api/entity/<id>/web-enrichments` — list cached
- [x] T80c: API `POST /daoanh/api/entity/<id>/web-enrich` — fetch + AI + save (cooldown 30d)
- [x] T80d: API `POST /daoanh/api/entity/<id>/web-enrich/report` — báo lỗi
- [x] T80e: API `GET /daoanh/api/admin/web-enrichments` — admin list + filter
- [x] T80f: API `POST /daoanh/api/admin/web-enrichment/<id>/status` — verify/reject
- [x] T80g: Frontend `places.html` — `#webEnrichBlock` + JS (initWebEnrichPanel, webEnrich, reportWebEnrichment)
- [x] T80h: Frontend `search.js` — panel trong person bio + personWebEnrich, reportPersonEnrich
- [x] T80i: Admin `admin/web_enrichments.html` — list, filter, verify/reject
- [x] T80j: Admin menu `admin/index.html` — thêm "Web Enrichment"
- [x] T80k: py_compile OK

## Ghi chú

- Wikipedia vi → zh fallback: nếu không tìm thấy bằng name_en trên vi.wikipedia, thử name_zh trên zh.wikipedia
- Cooldown 30 ngày: không fetch lại nếu đã có entry còn mới (tránh spam API)
- Gemini prompt: học thuật Phật học, Hán-Việt, không pinyin, kết thúc "(Theo [nguồn])"
- Admin có thể verify (xanh) hoặc reject (đỏ) từng entry
- report_count >= 2 → status='reported' → admin thấy ưu tiên trong queue
