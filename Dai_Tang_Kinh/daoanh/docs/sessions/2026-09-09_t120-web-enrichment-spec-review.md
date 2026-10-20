# Session — Rà đặc tả "Web Enrichment vào DILA" (tạo task T121, docs-only)

**Ngày:** 2026-09-09 · **Commit:** `17274284`

> **Xử lý trùng số:** tiến trình song song đã tạo `tasks/T120-unified-lookup-wikidata-enrichment.md`
> (17:33, cùng đặc tả "Web Enrichment", hướng 5-layer unified lookup). Task của phiên này **đổi T120 → T121**
> (BỔ TRỢ: geo/elevation P625/P2044 + HITL admin queue + cron candidate). Không đè việc ngoài.

## Bối cảnh
Lee gửi đặc tả JSON "Tích hợp dữ liệu web enrichment vào DILA": auto-fetch Wikipedia/Wikidata
cho places → lat/lon/elevation + GIS maps. Yêu cầu: 2 bảng mới, 2 endpoints, placevn.html,
cron `enrich_places.py`.

## Kết luận (read-only, verified)
**~90% infra ĐÃ XÂY SẴN.** Bảng đối chiếu:
- "places không có tọa độ" → ❌ SAI — `places_dila.geo_lat/geo_long` **58,480** place; + `places.gps_lat/lng` + `places_vps` + `namevi_map_places`.
- 2 bảng mới `places_enriched`/`external_refs` → ❌ TRÙNG — có `web_enrichment_cache` (1 row PL…48247 Mahabodhi) · `place_wiki_snapshots` · `geo_cross_ref` (bridge dila_id↔wikidata_qid, 181 rows).
- Fetch Wikipedia/Wikidata → ✅ `/daoanh/api/admin/wiki/fetch` · `/entity/<id>/web-enrich` + `web-enrichments` + `web-enrich/report` · `/admin/web-enrichments` · `_fetch_wikidata_founders` + SPARQL + P112.
- GET combined → ✅ `/places/unified` + sub-apis persons/cbeta/claims.
- placevn.html (admin) → ✅ Leaflet map + wiki + tọa độ.
- Cron → ⚠️ chưa có (delta; candidate-only, KHÔNG auto-commit).

### Lỗi logic đặc tả (đã sửa trong kế hoạch)
1. **Auto-canonicalize** example `PL…053 Na Ha Lê Thành → Q1997494 Jalalabad` = VI PHẠM T109
   (tự gộp nguồn không duyệt) → chỉ sinh candidate; admin Approve/Reject; merge `owl:sameAs`.
2. **Tên trùng** ("Jalalabad" Afghanistan vs Bangladesh) → confidence + context + bằng chứng khi duyệt.
3. **Không tạo bảng trùng** (SSOT giữ `geo_cross_ref` + `web_enrichment_cache`).

## Delta thật (task T121, pending)
- **D1**: Wikidata P625 (lat/lon) + P2044 (elevation_m — duy nhất chưa có) → additive vào `geo_cross_ref`
  (`elevation_m`, `coord_source`, `coord_checked_at`).
- **D2**: admin queue candidates/approve/reject (pattern `bio-review`/`place/<id>/canonical`).
- **D3**: cron `scripts/enrich_places.py` — 100 place/đêm, sinh candidate, KHÔNG ghi canonical.
- Ràng buộc: Wikipedia/Wikidata/OSM free · 5s timeout + retry 3 · cache 30 ngày.

## Cam kết
- KHÔNG tạo `places_enriched`/`external_refs`; KHÔNG auto-commit; HITL bắt buộc; 0 code phiên này.

## Thay đổi (docs-only, 0 code, 0 DB)
1. `tasks/T121-web-enrichment-wikidata-geo-admin-queue.md` (mới, pending; đổi số từ T120).
2. `docs/tasktodo.md` — dòng T121.
3. `docs/ROADMAP_META_UPDATE.md` §5 luật + §2 line (task=39).
4. `docs/ROLLBACK.md` — row `17274284`.
5. Session này.

## Rollback
- `git revert --no-edit 17274284` (docs-only, 0 DB).