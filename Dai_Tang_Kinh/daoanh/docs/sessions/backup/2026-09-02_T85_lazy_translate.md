# Session 2026-09-02 — T85 Lazy Translate TOÀN PTDA

## Task / Mục đích
Áp dụng lazy translate cho toàn bộ dự án PTDA 3 loại nội dung (Person bio / Place note / Đại Tạng passage). Quyết định admin: chuyển Đại Tạng sang lazy on-demand, background full-backfill defer sang T85.

## Work State
### Audit (trước build)
- Person bio: POST translate ✅, manual button ✅, report ✅ → đã lazy
- Place note: GET+POST ✅, auto-trigger ✅, report ✅ → đã lazy
- Đại Tạng passage: **thiếu translate endpoint + frontend trigger** (batch-only T50) → **làm đầy đủ**

### Completed
1. **Backend `app.py`**:
   - `GET/POST /daoanh/api/passage/<id>/translate` (`api_passage_translate` ~13558): GET=cache-only, POST=cache+Groq-on-miss, auto-update `passage.vi_text`+`translation_draft=1`, lưu cache `source_type='passage'`
   - `api_person_translate` mở rộng GET (cache-only pre-check)
   - Fix `@app.route` thiếu cho `api_admin_translation_cache_list`
   - `py_compile` PASS
2. **Frontend `places.html`**:
   - Layer B cards (main ~1664 + pagination ~1754): nút `Dịch (AI)` khi `!p.has_vi` + `Dịch lại` khi bản nháp + inline kết quả
   - Reader modal: nút `Dịch (AI)` khi chưa có vi_text + auto-refresh list
   - Hàm `daiTangTranslate`, `daiTangRetranslate`, `daiTangRefreshList`
   - node syntax PASS (5 blocks)
3. **Docs**: `tasks/T85-full-db-translate.md`, `docs/tasktodo.md` (T85 entry prepended), `docs/progress.md` (Cập nhật)

### Tests
- `py_compile` PASS
- node syntax places.html/search.js PASS
- `npm run test` PASS, `npm run e2e` PASS
- lint/node--check skip (node v24 `.html` ext) — không phải lỗi code
- e2e:runtime EPERM = volume E:\Backup 2025 blocker (không phải code)
- Test client: GET passage translate 200 (cache), POST report 200

## Blocked
- e2e:runtime fail do EPERM unlink trên volume `E:\Backup 2025` (đã biết, không phải code)

## Next Move
1. T85 full-backfill script `t85_full_translate.py` (--category person/place/passage/all, --model, --max-per-hour, --sleep, resume, progress log)
2. Admin dashboard `admin/full_translate.html` (coverage + model selector + re-translate reported)
3. Git commit T85 (T83 byte-ref) + verify
4. Session state save (tasktodo POST)

## Relevant Files
- `app.py`: `api_passage_translate` ~13558, `api_person_translate` ~13290, `api_admin_translation_cache_list` ~13685
- `places.html`: Layer B cards ~1664/1754, `openDaiTangReader` ~1537, `daiTangTranslate` ~1791
- `search.js`: person lazy (giữ nguyên)
- `tasks/T85-full-db-translate.md`
- Rollback git: `scripts/t83_ref_write.py --restore`
