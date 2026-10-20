# Session — T120 Phase A Live Wikidata Lookup (2026-09-10)

## Trạng thái phiên
- **Task hoàn thành:** T120 Phase A — `_t120_query_wikidata(qid)` + `?live=1` trên lookup endpoint.
- **Task đang dở:** T120 chờ Lee xác nhận "Admin xác nhận DONE" (success criteria còn 1 checkbox); 15 items khác trên ADMIN_REVIEW_DASHBOARD chờ Lee.
- **Todo tiếp theo:** Lee test lookup endpoint `/daoanh/api/v1/entity/PL000000023255/lookup?live=1`; sau đó đóng T120, đi tiếp T55 (related texts) hoặc Batch C khi agent ngoài bàn giao.

## Commit
- `b87ba913` (feat: T120 Phase A) — code + tasktodo + task file + ROADMAP + regen.

## Chi tiết kỹ thuật
- `_t120_query_wikidata(qid)` ở `app.py:` — `wbgetentities` P625/P2044/sitelinks, trả dict
  `{label_vi, label_zh, label_en, lat, lon, elevation_m, wiki_*}`. Timeout 8s, HW hdr riêng.
- Lookup endpoint nhận `?live=1`: Layer 2 có QID → fetch live → thêm `wikidata_live` candidate
  vào response + `sources_used.append('wikidata_live')` + `confidence += 0.15`.
- **HITL:** KHÔNG ghi DB — chỉ trả data candidate trong response; admin tự quyết enrich.
- Network fail → graceful fallback (cached data + `live_unavailable=true` + `live_error`).
- Smoke test_client PASS:
  - cached: `sources=['dila','wikidata_ref']` conf=0.8 (HTTP 200)
  - live: `['dila','wikidata_ref','wikidata_live']` conf=0.95 — Q232771 Chùa Thiếu Lâm,
    label_vi/zh/en + lat=34.507 lon=112.935 + wiki_en Shaolin Monastery.
- Pipeline: lint/test/e2e ✅ (e2e:runtime EPERM `.last-run.json` pre-existing volume, non-blocking).

## Bằng chứng tái lập
```bash
cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh
curl "http://localhost:8080/daoanh/api/v1/entity/PL000000023255/lookup?live=1"
# → {"ok":true,"sources_used":["dila","wikidata_ref","wikidata_live"],"confidence":0.95,"data":{...}}
```

## Lưu ý
- `enrich_places.py` dry-run 15 mẫu: nhiều QID match nhưng **thiếu P625** (Wikidata coverage ceiling,
  đúng T22/T64 kết luận). 678 places thiếu toạ độ; yield khai thác thấp — không chạy mass batch.
- Observation server `:37700` vẫn DOWN — tasktodo POST không gửi được.