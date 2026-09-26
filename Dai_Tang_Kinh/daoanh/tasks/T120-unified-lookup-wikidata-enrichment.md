---
id: T120
title: "Unified Lookup + Wikidata Enrichment — 5-layer architecture dùng tables đã có"
module: Data / Enrichment / Lookup
priority: medium
depends_on: [T112, T115]
created: 2026-09-09
updated: 2026-09-10
status: done
---

# T120 — Unified Lookup + Wikidata Enrichment

## Bối cảnh & quyết định thiết kế

Phân tích kiến trúc 2026-09-09 (session admin): DB đã có 130+ bảng, trong đó:

| Bảng có sẵn | Rows | Vai trò trong T120 |
|---|---|---|
| `geo_cross_ref` | 181 | **Crosswalk places → Wikidata QID** (dila_id → wikidata_qid) |
| `place_wiki_snapshots` | 0 | Schema sẵn, cần populate từ enrichment |
| `place_cbdb_map` | 10 | Sparse — CBDB mapping cho places |
| `web_enrichment_cache` | 2 | Cache Wikipedia text + AI summary |
| `sat_crossref` | 2,913 | CBETA sigla → SAT URL (texts only) |
| `entity_source_ids` | 182,715 | Internal ID → DILA ID (không phải multi-source) |

**Quyết định kiến trúc:** KHÔNG tạo bảng mới. Extend những gì đã có.

## Root causes đã xác nhận

1. **Không có fallback chain** — `_t75_search_wikipedia` chỉ thử vi + zh Wikipedia
   → **Đã fix một phần (2026-09-09):** thêm EN Wikipedia fallback trong `api_web_enrich`
2. **`geo_cross_ref` chưa được dùng** — 181 Wikidata QIDs đang có nhưng không query
3. **`place_wiki_snapshots` rỗng** — không cache sau enrichment
4. **Không có unified endpoint** — mỗi source có flow riêng lẻ
5. **Không có normalizer** — raw data từ Wikidata/CBDB không merge được vào schema DILA

## Giải pháp 5-layer (reuse tables hiện có)

### Layer 1 — Unified lookup endpoint (mới)
```
GET/POST /daoanh/api/v1/entity/<id>/lookup
Params: ?sources=wikidata,wikipedia,cbdb (default: wikidata,wikipedia)
Response: { id, name_vi, name_zh, name_en, geo: {lat, lon}, refs: [...], sources_used, confidence }
```
Endpoint gọi `_t120_lookup_with_fallback(entity_id, sources)`.

### Layer 2 — ID Crosswalk (dùng `geo_cross_ref` + `place_cbdb_map`)
```python
# Không tạo bảng mới — query các bảng đã có:
wikidata_qid = conn.execute(
    "SELECT wikidata_qid FROM geo_cross_ref WHERE dila_id=?", (entity_id,)
).fetchone()
cbdb_id = conn.execute(
    "SELECT cbdb_addr_id FROM place_cbdb_map WHERE place_id=?", (entity_id,)
).fetchone()
```

### Layer 3 — Cache (dùng `web_enrichment_cache` + `place_wiki_snapshots`)
```
web_enrichment_cache: cache text + AI summary (TTL 30 ngày, status=auto/verified/rejected)
place_wiki_snapshots: cache Wikipedia raw (wiki_title, snippet, full_text, source)
```
Sau mỗi enrichment thành công → save cả hai bảng.

### Layer 4 — Fallback chain
```
1. geo_cross_ref.wikidata_qid → Wikidata API (GPS + label_vi + wikipedia_url) [timeout 3s]
2. web_enrichment_cache (cache hit < 30 ngày)                                  [instant]
3. vi.wikipedia.org + zh.wikipedia.org + en.wikipedia.org (đã implement)       [timeout 8s]
4. place_cbdb_map → CBDB API (nếu có mapping)                                  [future]
```

### Layer 5 — Normalizer
```python
def _t120_normalize(source_data, source_type) -> dict:
    """Map kết quả từ Wikidata/Wikipedia/CBDB về schema DILA-compatible."""
    return {
        "id": entity_id,
        "name_vi": ..., "name_zh": ..., "name_en": ...,
        "geo": {"lat": ..., "lon": ..., "elevation": ...},
        "refs": [{"source": source_type, "id": ..., "url": ...}],
        "confidence": 0.0-1.0,
        "sources_used": [source_type]
    }
```

## Implementation plan

### Phase A — Wikidata integration (ROI cao nhất, ít code)
**File:** `app.py` — **DONE 2026-09-10 (T120 Phase A LIVE)**

1. ✅ `_t120_query_wikidata(qid)` — Wikidata Entity API:
   ```
   GET https://www.wikidata.org/w/api.php?action=wbgetentities&ids=Q232771
       &props=labels|claims|sitelinks&languages=vi|zh|en&format=json
   ```
   → Lấy: `label_vi`, `label_zh`, `label_en`, GPS (P625), elevation (P2044), Wikipedia sitelinks
   → **HITL: KHÔNG ghi DB** — trả candidate dict, lưu trong response `wikidata_live` field

2. ✅ Lookup endpoint wire: `?live=1` param → Layer 2 gọi `_t120_query_wikidata` on-demand
   - Nếu qid có trong `geo_cross_ref` + live=1 → fetch live → thêm `wikidata_live` + `sources_used.append('wikidata_live')` + `conf += 0.15`
   - Nếu network fail → trả cached data + `live_unavailable=true` + `live_error=network_timeout_or_blocked`
   - **KHÔNG ghi DB** (HITL-safe, Zero-ALTER)

### Phase B — ~~Populate geo_cross_ref~~ (ĐÃ DONE bởi T21/T39/T64)

> **Lưu ý quan trọng (2026-09-09):** `geo_cross_ref` 181 rows là kết quả của T21 (spatial join)
> + T39 (SPARQL P1188 — chỉ có ~148 DILA places trên Wikidata có P1188, không phải 1,000+).
> Phase B ban đầu viết "seed 1,000+ entries" là **SAI** — Wikidata P1188 coverage thực tế rất thấp.
> KHÔNG cần viết thêm seed script. Scope Phase B = skip.

### Phase C — Unified endpoint `/api/v1/entity/<id>/lookup`
**File:** `app.py`

Gọi `_t120_lookup_with_fallback` theo chain Layer 4.
Response trả `sources_used` + `confidence` để UI biết độ tin cậy.

## Ràng buộc

- **KHÔNG ALTER** bảng base (`places`, `people`, `places_dila`, `entity_claims`)
- KHÔNG tạo bảng mới — dùng `geo_cross_ref`, `web_enrichment_cache`, `place_wiki_snapshots`
- Timeout mỗi nguồn: 3s (Wikidata) / 8s (Wikipedia)
- Rate limit Wikidata: 1 req/s (add `time.sleep(1)` trong batch script)
- T112 phải hoàn tất (source activation) trước khi Phase B scale lên production

## Success criteria

- [ ] `PL000000000053` (Nagarahara) → trả GPS + Wikipedia text từ `geo_cross_ref` + en.Wikipedia
- [x] `PL000000023255` (Thiếu Lâm Tự) → trả GPS từ Wikidata Q232771 (đã có QID) — Batch E1 smoke 200✓
- [x] `PL000000023255` + `?live=1` → `wikidata_live` label_vi='Chùa Thiếu Lâm', lat=34.507, lon=112.935, conf=0.95 — Phase A smoke 2026-09-10✓
- [ ] `web_enrichment_cache` hit rate > 70% sau 1 tháng dùng
- [ ] `place_wiki_snapshots` được populate cho mọi entity đã enrich
- [x] Phase B seed: ~~180+~~ ĐÃ DONE bởi T21/T39/T64
- [x] Phase C endpoint: GET /api/v1/entity/<id>/lookup trả sources_used + confidence < 5s — Batch E1✓
- [ ] Admin xác nhận DONE

## Ghi chú triển khai

- **EN Wikipedia fallback đã thêm (2026-09-09)** trong `_t75_search_wikipedia` — đây là quick-fix Phase A đầu tiên
- Wikidata P1188 = DILA Place ID — property chính thức trên Wikidata, dùng được ngay
- `geo_cross_ref` có `mapped_by='sparql_p1188'` cho 2 rows đầu — đây là pattern đúng
- Không dùng CBDB API trực tiếp đến khi T112 chốt license

## Ghi chú triển khai (Batch E1, 2026-09-10)

- **Phase C IMPLEMENTED (additive, đã smoke 4 cases):**
  `GET /daoanh/api/v1/entity/<id>/lookup` — 5-layer fallback read-only tại thời điểm gọi
  (0 network, 0 ALTER, 0 bảng mới — đọc cache `geo_cross_ref`/`place_wiki_snapshots`/
  `web_enrichment_cache` + DILA core).
  - PL000000023255 (Thiếu Lâm Tự) → `sources=['dila','wikidata_ref']` conf=0.8, kèm note DILA + GPS Q232771
  - PL000000000048 → `['dila']` conf=0.7 (candidate QID null — trung thực hiện trạng T121)
  - PL056722 (short ID) → `['dila']` conf=0.6 (fallback places_dila)
  - NOPE999 → 404
- **Phase A DONE (2026-09-10):** `_t120_query_wikidata(qid)` = `wbgetentities` P625/P2044/sitelinks, returns dict `{label_vi, label_zh, lat, lon, elevation_m, wiki_*}`. HITL: KHONG ghi DB, tra `wikidata_live` candidate trong response. Wire: `?live=1` -> Layer 2 fetch on-demand + `sources_used` + `conf+=0.15`. Network timeout -> graceful fallback (`live_unavailable=true`). Smoke: Q232771 cached=200 conf=0.8 + live=200 conf=0.95 PASS.
- **Revert:** `git revert --no-edit <hash>` — endpoint là hàm mới, 0 xóa bảng.

## Files liên quan

- `app.py` — `_t75_search_wikipedia`, `api_web_enrich`, thêm `_t120_*` functions
- `data/lineage.db` — `geo_cross_ref`, `web_enrichment_cache`, `place_wiki_snapshots`
- `scripts/seed_t120_wikidata_geo.py` — seed script (Phase B)
- `daoanh/places.html` — hiển thị enrichment data (đã có UI webEnrichCard)
