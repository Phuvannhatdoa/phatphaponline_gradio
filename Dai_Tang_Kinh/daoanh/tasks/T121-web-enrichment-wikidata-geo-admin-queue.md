---
id: T121
title: "Web Enrichment vào DILA — Wikidata Geo/Elevation + Admin Queue (candidate-only)"
module: Places / Geo Enrichment
priority: medium
depends_on: [T22, T56, T109, T100]
created: 2026-09-09
updated: 2026-09-10
status: in_progress
---

# T121 — Web Enrichment vào DILA (Wikidata Geo + Elevation + Hàng đợi Admin Duyệt)

## Bối cảnh
Rà đặc tả "Tích hợp dữ liệu web enrichment vào DILA" (JSON 2026-09-09): yêu cầu
auto-fetch Wikipedia/Wikidata cho places → lat/lon/elevation + GIS map.
**Đối chiếu thực tế: ~90% infra ĐÃ XÂY SẴN** (listed dưới). Delta thật nhỏ và
phải sửa 1 lỗi logic NGHIÊM TRỌNG trong đặc tả (auto-canonicalize = vi phạm T109).

## Phủ lại (đã có, KHÔNG build lại)
| Đặc tả đề nghị | Hiện trạng |
|---|---|
| "places không có tọa độ" | ❌ SAI — `places_dila.geo_lat/geo_long` 58,480 place; + `places.gps_lat/lng` + `places_vps` + `namevi_map_places` |
| 2 bảng mới `places_enriched`/`external_refs` | ❌ TRÙNG — enrichment đã có `web_enrichment_cache` (1 row: PL000000048247 Mahabodhi, raw_content + summary_vi auto) · `place_wiki_snapshots` · `geo_cross_ref` (bridge dila_id↔wikidata_qid, 181 rows) |
| Fetch Wikipedia/Wikidata | ✅ `/daoanh/api/admin/wiki/fetch` (save snapshot) · `/daoanh/api/entity/<id>/web-enrich` + `web-enrichments` + `web-enrich/report` · `/daoanh/api/admin/web-enrichments` (page `web_enrichments.html`) · `_fetch_wikidata_founders` + SPARQL + P112 |
| GET `place/<id>/full` combined | ✅ `/daoanh/api/places/unified` + `/places/<id>/` (persons, cbeta, claims, chronology…) |
| placevn.html tọa độ + wiki + GIS map | ✅ `admin/placevn.html` Leaflet `L.map` + wiki + geo_lat/geo_long hiển thị |
| Cron `enrich_places.py` | ⚠️ Chưa có (delta — sinh candidate, KHÔNG tự ghi) |

## Lỗi logic đặc tả cần sửa (bắt buộc)
1. **KHÔNG auto-commit** example `PL…053 Na Ha Lê Thành → Q1997494 Jalalabad` (lat/lon/elev
   như sự thật đã đóng). Đây là đồng nhất HỌC THUẬT (Nagarahara 那竭罗曷国 = Jalalabad) —
   tự gộp nguồn không duyệt **vi phạm T109 Zero-Loss**. → chỉ **candidate** + admin Approve/Reject
   (pattern `place/<id>/canonical` · `namevi-map-places/save` · `bio-review`), merge có `owl:sameAs`.
2. **Tên trùng**: "Jalalabad" (Afghanistan vs Jakkabari Bangladesh) → resolve bằng tên thuần sai ~50%.
   Cần confidence + context (kinh văn/lineage) + bằng chứng hiển thị khi duyệt.
3. **KHÔNG tạo bảng trùng** `places_enriched`/`external_refs` (SSOT: dùng `geo_cross_ref` +
   `web_enrichment_cache` + `place_wiki_snapshots`; `external_refs` khái niệm ≈ `marcus_reference`
   + `cbeta_ref` + `dila_reference` + `geo_cross_ref`).

## Delta thật (additive, candidate-only)
### D1: Wikidata structured geo vào `geo_cross_ref` (additive, ALTER thêm cột nullable)
- Thêm cột: `elevation_m REAL`, `coord_source TEXT` ('wikidata'|'osm'|'dila'|'manual'),
  `coord_checked_at TEXT`, giữ `confidence`/`mapped_by`/`source_url` sẵn có.
- Fetch bằng **P625** (lat/lon) + **P2044** (elevation_m — cái duy nhất chưa có trong hệ).
- 5s timeout + retry 3; cache theo `coord_checked_at` ≥ 30 ngày (pattern web_enrichment_cache).

### D2: Admin queue Approve/Reject (pattern bio-review / place canonical)
- `GET /daoanh/api/admin/enrich/candidates` — (place ↔ QID) match + confidence + bằng chứng
  (kim luật: không resolve mù bằng tên; chỉ show candidate có evidence).
- `POST /daoanh/api/admin/enrich/<candidate_id>/approve` → ghi `geo_cross_ref`
  (additive) + `en_audit_log`.
- `POST /daoanh/api/admin/enrich/<candidate_id>/reject` → ghi lý do, KHÔNG xoá.
- UI: tab trong `admin/placevn.html` hoặc trang `admin/enrich-queue.html`.

### D3: Cron `scripts/enrich_places.py` (heritage `scripts/` CLI, đúng Zero-RAM)
- Mỗi đêm chọn **100 place chưa có** `geo_cross_ref.wikidata_qid` → fetch candidacy →
  INSERT vào hàng đợi (chưa duyệt). **KHÔNG ghi canonical tự động.**
- `crontab` entry kèm doc; chạy thủ công bằng `--dry-run` để kiểm tra.

## Ràng buộc (giữ nguyên đặc tả)
- Chỉ Wikipedia/Wikidata/OSM miễn phí; 5s timeout + retry 3; cache 30 ngày;
  Flask 127.0.0.1:5000 + Nginx `/daoanh/` prefix.

## Ghi chú task
- KHÔNG tạo `places_enriched`/`external_refs`; KHÔNG auto-commit; HITL bắt buộc.
- Liên hệ: T22 (founding via Wikidata), T56 (bản đồ lịch sử), T109 (Zero-Loss).

## X?y d?ng Batch B (2026-09-10) ? IMPLEMENTED (candidate-only, HITL)
- `geo_cross_ref` additive c?t: enrich_status (none|candidate|approved|rejected), enrich_source_qid,
  enrich_lat/lon/elevation_m, enrich_checked_at, wikidata_lat/lon, elevation_m, elevation_source.
- `scripts/enrich_places.py` ? cron candidate: places_dila thi?u to? ?? ? ch?a enrich ? Wikidata
  P625 (globecoordinate) + P2044 (elevation) ? ch? ghi `enrich_status='candidate'` (kh?ng t? approve).
- `GET /daoanh/api/admin/geo-enrich/candidates` + `POST /daoanh/api/admin/geo-enrich` (admin approve,
  upsert main fields confidence='verified') + `POST .../geo-enrich/<id>/status` (reject/candidate).
- Kh?ng ALTER b?ng n?n; kh?ng t? set wikidata_qid ch?nh th?c khi ch?a duy?t.
- Tr?ng th?i: **in_progress** ? ch? Lee review h?i quy + ch?y cron ? done.
## L?n ch?y ??u (Batch D, 2026-09-10) ? candidate ghi OK
- `python scripts/enrich_places.py --limit=50 --run` ? ghi `enrich_status='candidate'`
  (lat/lon P625 + elevation P2044), KH?NG set wikidata_qid ch?nh th?c.
- K?t qu? th?t: **9 candidate** ghi (PL000000000048 ? PL000000008349), 2/9 k?m elevation
  (94m / 242m); timeout m?ng (Wikidata ch?m) d?ng tr??c limit 50 ? ch?y ti?p sau qua cron.
  Candidate ?? admin duy?t trong tab Geo Enrichment (editor-dashboard.html).
