---
id: T85
title: Lazy Translate TOÀN PTDA — Full DB Translation System
module: Translation Pipeline
priority: high
status: done
depends_on: [T50, T73]
created: 2026-09-02
updated: 2026-09-06
done_when: Cả 3 loại nội dung (Person bio / Place note / Đại Tạng passage) có nút Dịch (AI) on-demand hoạt động với Groq key hợp lệ
---

# T85 — Lazy Translate TOÀN PTDA

## Mục tiêu
Thay chiến lược batch backfill (cần API key liên tục, chi phí cao) bằng **lazy on-demand**:
- User mở entity → bấm "Dịch (AI)" → gọi Groq → kết quả ghi vào DB cache → lần sau load từ cache
- Không tốn API cho 99% entity mà không ai tra

## Phạm vi phủ (3 loại)

| Loại | Source | Target | Status |
|------|--------|--------|--------|
| Person bio | `people.bio` (Hán DILA) | `translation_cache` | ✅ đã có endpoint + button |
| Place note | `places_dila.note` (Hán) | `translation_cache` | ✅ đã có auto-trigger |
| Passage text | `passage.raw_text` | `passage.vi_text` + `translation_cache` | ✅ endpoint mới T85 |

## Build hoàn thành (2026-09-02)

### Backend (app.py)
- `GET /daoanh/api/passage/<id>/translate` — cache-only, không gọi LLM (~13558)
- `POST /daoanh/api/passage/<id>/translate` — cache + Groq on-miss, ghi `passage.vi_text` + `translation_draft=1`
- `api_person_translate` — mở rộng GET trả cache-only pre-check
- Fix `@app.route` thiếu cho `api_admin_translation_cache_list`

### Frontend (places.html)
- Layer B cards (main render ~1664 + pagination ~1754): nút `Dịch (AI)` khi `!p.has_vi`; `Dịch lại` khi bản nháp
- Reader modal: nút `Dịch (AI)` khi chưa có vi_text + auto-refresh list
- Hàm: `daiTangTranslate()`, `daiTangRetranslate()`, `daiTangRefreshList()`

## T85 v2 — Lazy translate → translation_segments ✅ DONE (2026-09-06)

Admin quyết định storage = **`translation_segments`** (đồng bộ T94/T95, không dùng vi_text cho bản mới).
Unified route `/daoanh/api/passage/<passage_id>/translate` (GET+POST) giờ:
- Passage **có text_passages** (T50n2060 hiện tại) → dịch từng unit on-demand bằng Groq,
  ghi `translation_segments` (provider=`groq`, `quality_status='unreviewed'`, prompt `t96v1`,
  `revision_no` tăng dần, `force` → supersede bản `done` cũ + `supersedes_translation_id`),
  phản chiếu `passage.vi_text` = concat units (giữ tương thích frontend `p.has_vi`/chip "BẢN DỊCH NHÁP").
- Passage **chưa có text_passages** (vd T51n2076) → legacy: Groq toàn passage → `passage.vi_text` (+ cached GET).
- **Đã xoá route trùng `/daoanh/api/passage/<int:passage_id>/translate`** (đăng ký trước nên choán POST,
  chưa bao giờ đi qua segments; hành vi gộp vào legacy fallback).
- Frontend: `daiTangTranslate(pIndex, force)` + `daiTangRetranslate` truyền `force=true`.

Helper: `_t85_units/_t85_done_unit/_t85_get_segments/_t85_translate_unit/_t85_post_segments` (app.py).

Verify: py_compile + node --check + `npm run test`/`e2e` PASS + test_client DB tạm **20/20** + 🖥️ live
Groq thật passage 3923 (1 unit 0426a): POST done → GET `from_cache` → force → `superseded` rev2 + `done` rev3
`supersedes_translation_id` ✅; DB row `provider=groq`, `quality_status=unreviewed`, `passage.vi_text` cập nhật.
Session: `docs/sessions/2026-09-06_T85_v2_lazy_translate.md`.

## Blocker (cũ, ĐÃ HẾT)
- Groq key hoạt động (trong `data/llm_config.json`, model `qwen/qwen3.8-27b`) — live test 2026-09-06 PASS.
- Gemini key 404 — đường gemini chỉ còn trong helpers T73 (`_t73_call_gemini`), route passage không còn dùng.

## Resume khi có Groq key
```bash
# Test 1 passage
curl -X POST http://localhost:8080/daoanh/api/passage/T51n2076_p0001/translate

# Verify
curl http://localhost:8080/daoanh/api/passage/T51n2076_p0001/translate
```

## Tests đã pass
- py_compile PASS
- node syntax OK
- npm test/e2e PASS (e2e:runtime EPERM = volume E:\Backup 2025 blocker chung — không phải code)
- test client: GET passage translate 200 + report 200 verified

## Rollback
```bash
python scripts/t83_ref_write.py --restore
# + backup DB: data/lineage_backup_t50_20260902.db
```

## Acceptance criteria (checklist)
- [x] Endpoint `GET /daoanh/api/passage/<id>/translate` (cache-only — segments/vi_text)
- [x] Endpoint `POST /daoanh/api/passage/<id>/translate` (Groq on-miss → translation_segments, force supersede)
- [x] Frontend nút "Dịch (AI)" Layer B cards (main + pagination)
- [x] Frontend nút "Dịch (AI)" trong Reader modal
- [x] `api_person_translate` GET pre-check cache
- [x] Fix `api_admin_translation_cache_list` route
- [x] Groq key hợp lệ — live test passage 3923 dịch thành công (2026-09-06)
- [x] `passage.vi_text` được ghi sau POST translate (mirror từ translation_segments)
- [x] Cache reuse: GET lần 2 trả từ cache, không gọi LLM lại
- [x] UI hiển thị chip "BẢN DỊCH NHÁP" sau khi dịch xong (có sẵn T85 v1)
