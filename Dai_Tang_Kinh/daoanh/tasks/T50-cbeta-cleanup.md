---
id: T50
title: "CBETA Data Cleanup & Quality (merged T84 - passage vi_text draft cache + report)"
module: CBETA Core / Data Quality
priority: high
status: in_progress
depends_on: [T03, T20, T35, T38, T40, T73, TAB_DAI_TANG_PLACE]
created: 2026-08-26
updated: 2026-09-12
done_when: >
  Fuzzy matches quality-flagged, buddhist_db merged, catalog_mapping audited,
  passage.vi_text backfilled (draft AI) + translation_cache reuse + báo lỗi → Dashboard
---

# T50 — CBETA Data Cleanup & Quality (merged T84)

> **2026-09-02 (T85)**: Phương thức backfill T50c được **thay bằng lazy translate** (quyết định Admin 2026-09-02).
> Đại Tạng passage giờ dịch on-demand khi user click qua `GET/POST /daoanh/api/passage/<id>/translate` (T85);
> batch backfill toàn DB defer sang `tasks/T85-full-db-translate.md`. Script `t50_passage_vi_backfill.py` giữ làm reference/tools, 200 bản dịch có sẵn trong DB vẫn dùng lại qua cache.
>
> **2026-09-02**: Merged T84 (passage.vi_text draft translation cache + báo lỗi) vào T50c theo quyết định Admin.
> Build 2026-09-02: T50a/b/d đã done trong DB từ trước; code + schema + docs của T50c đã build (chạy backfill chờ key LLM).
>
> **2026-09-12 (UNBLOCKED)**: Key user cấp `gsk_tvJp...` → **401 invalid_api_key**; key có sẵn `data/llm_config.json.groq_key` **vẫn LIVE** (đang dùng trong tab Đại Tạng lazy-translate, app.py:15620). Chạy backfill T51n2076 bằng key này, resume-safe, rate-limit 30s auto-retry. **Lệnh đúng: `python scripts/t50_passage_vi_backfill.py --sigla T51n2076 --limit 0 --sleep 1.0`** (KHÔNG có `--apply` trong script — default = apply; có `--dry-run/--verify/--revert`). Session: `docs/sessions/2026-09-12_t50-unblock-groq-key-test.md`.

## Mục tiêu
Dọn dẹp dữ liệu CBETA hiện có: giảm noise, merge orphaned data, backfill translations
(`passage.vi_text`) làm **bản dịch nháp AI** dùng lại qua `translation_cache`, kèm nút **Báo lỗi** → Dashboard.

## Kết quả Audit theo DATA REALITY (2026-09-02)
- **T50a DONE (trong DB):** `cbeta_catalog_place_fuzzy.low_confidence` = 56,318/61,706 (score<80); 5,388 high-confidence.
- **T50b DONE (trong DB):** `legacy_canon_mapping` = 2,698 rows từ `buddhist_db.sqlite` (5 sources); 0 orphan.
- **T50d DONE (trong DB):** `catalog_mapping` = 6,564 rows, **verified 0 orphaned** (JOIN `canon_catalog` CAST(cb_cbeta AS TEXT)=catalog_id).
- **T50c = còn lại thật sự (target 6,347).** Tab "Đại Tạng" đọc `passage.vi_text` qua `passage_entity JOIN passage` — 6,347 distinct passage gắn PLACE đều `vi_text=NULL`, chỉ 5 văn bản:
  | sigla | passage |
  |-------|--------|
  | T51n2076 (Chỉ Nguyệt Lục) | 3,202 |
  | T50n2061 | 1,212 |
  | T50n2060 | 976 |
  | X77n1524 | 727 |
  | T50n2062 | 230 |

## Subtask T50c — Backfill `passage.vi_text` (bản nháp) + cache + báo lỗi

### Thiết kế (đã Admin chốt 2026-09-02)
1. **Dịch nháp bằng Groq API miễn phí** → lưu `passage.vi_text` + `passage.translation_draft=1`.
2. **Dùng lại cache mỗi lần load** (không gọi lại LLM): ghi song song `translation_cache(source_type='passage', source_hash=sha256(raw_text)[:24], status='auto')`.
   - pattern tái sử dụng đã có sẵn từ T73 `api_place_translate` GET → cache hit / POST → translate+cache.
3. **Báo lỗi** ở card passage và reader modal → endpoint `POST /daoanh/api/passage/<id>/translate/report` → `report_count++`, đủ 3 → `status='reported'`, hiện trong admin `translation_cache.html` + banner Dashboard.

### Schema (additive, đã apply)
```sql
ALTER TABLE passage ADD COLUMN translation_draft INTEGER NOT NULL DEFAULT 0;
```

### Backend (đã build, app.py)
- `entity_canon` (~11650): select thêm `p.translation_draft` → response `is_translation_draft`.
- Endpoint mới `api_passage_translate_report` (~13558, sau `api_place_translate_report`):
  body JSON `{note}`; tìm cache theo `source_hash=sha256(raw_text)[:24]` + `source_type='passage'`; upsert `report_count`; ≥3 → `status='reported'`; trả `{ok, report_count, status}`.
- Dùng lại helper: `_t73_source_hash` (sha256[:24]), `make_cbeta_prompt`, `clean_gemini_output`, `_call_gemini`(=Groq), `_llm_config_read/write`.

### Frontend (đã build, places.html)
- Chip bản dịch: `BẢN DỊCH NHÁP` (gold `--da-gold`) khi `is_translation_draft`, ngược lại `BẢN DỊCH THAM KHẢO` (green). Áp dụng cả 2 bản render Layer B (main tab ~1664 + pagination ~1751).
- Preview vi_text: prefix `(bản dịch nháp)` + border-left gold khi draft.
- Nút `⚑ Báo sai` (card) và `⚑ Báo sai đoạn văn` (reader) → `daiTangReportPassage(p.passage_id, refLabel)` → POST report endpoint (prompt note, alert số lần báo).

### Script (đã build, scripts/t50_passage_vi_backfill.py)
- Flags: `--dry-run/--limit/--offset/--sigla/--next/--verify/--revert/--apply/--api-key/--sleep`.
- Key resolution: env `GROQ_KEY` → `data/llm_config.json.groq_key` → regex parse `app.py GROQ_KEY` (không import app để tránh khởi động Flask). Model: env `GROQ_MODEL` → llm_config → `qwen/qwen3.8-27b`.
- Vòng lặp: một passage 1 lần gọi AI (batch 1), update `passage.vi_text`/`translation_draft=1` + INSERT cache `source_type='passage'`; có `--sleep` ngắt để tránh rate limit (SQLite WAL, retry lock).
- Resumable: chỉ chọn passage `vi_text IS NULL` (đã dịch bỏ qua); `--verify`/`--dry-run` không đổi DB.
- `--revert`: vi_text=NULL, translation_draft=0, DELETE cache passage (theo `--sigla` nếu có) — rollback 1-lệnh.
- **BLOCKED (2026-09-02):** cả 2 key trong repo đều chết — Groq hardcode app.py:13131 → **403 Forbidden** mọi model; Gemini key batch_translate_places.py:30 → **404 Not Found** mọi variant. Không còn key hoạt động local. Resume khi có key:

```bash
python scripts/t50_passage_vi_backfill.py --apply --limit 20   # test chất lượng
python scripts/t50_passage_vi_backfill.py --apply --sigla T51n2076 --sleep 0.15
python scripts/t50_passage_vi_backfill.py --apply --sigla T50n2061 --sleep 0.15
python scripts/t50_passage_vi_backfill.py --apply --sigla T50n2060 --sleep 0.15
python scripts/t50_passage_vi_backfill.py --apply --sigla X77n1524 --sleep 0.15
python scripts/t50_passage_vi_backfill.py --apply --sigla T50n2062 --sleep 0.15
python scripts/t50_passage_vi_backfill.py --verify
```

### Trạng thái Build 2026-09-02
- ✅ DB backup `data/lineage_backup_t50_20260902.db` (1.3 GB).
- ✅ Script py_compile + `--verify` (analysis pass) + `--dry-run --limit 5` OK.
- ✅ Backend py_compile OK. Frontend node --check OK (PLACES_JS_SYNTAX_OK).
- ⏸ Full run: **chờ Groq key hoạt động** (cấp qua env `GROQ_KEY`, `data/llm_config.json.groq_key`, hoặc `--api-key`).

## DB Schema Changes đã apply (additive)
```sql
ALTER TABLE passage ADD COLUMN translation_draft INTEGER NOT NULL DEFAULT 0;
```
(Trước đây T50a/b/d đã thêm: `cbeta_catalog_place_fuzzy.low_confidence`, `catalog_mapping.quality_flag`, `legacy_canon_mapping`.)

## API Changes
- New: `POST /daoanh/api/passage/<passage_id>/translate/report` (báo lỗi bản dịch passage → translation_cache).
- (Plan trước đây `/admin/cbeta/quality-report` không build — dữ liệu đã review qua `translation_cache.html`.)

## Rollback
- Backend/frontend: `git revert` commit T50 (hoặc `python scripts/t83_ref_write.py --restore` về ref cũ).
- Schema + data: `python scripts/t50_passage_vi_backfill.py --revert` (restore vi_text + xóa cache) + khôi phục `lineage_backup_t50_20260902.db` nếu cần.

## Estimated Effort: ~12 hours (đã build phần code/schema/docs; run chờ key)

---

## ⚠ Kiến trúc mới — Alignment Schema (2026-09-04, T94)

**Quyết định kiến trúc bổ sung:** Việc backfill `passage.vi_text` bằng T85 lazy translate chưa giải quyết được vấn đề **alignment alignment Vi–Hán**. T50 chỉ lo translation text; T94 lo alignment structure.

**Lỗi xác nhận:** Hán đoạn 41 ≠ Vi đoạn 41 về nội dung (lệch ~8 đoạn).

**Hướng giải quyết dài hạn (T94):** 3 bảng mới:
- `text_passages` — canonical passage IDs
- `translation_segments` — segment-level translations  
- `passage_translation_alignment` — mapping Hán ↔ Việt (không theo ordinal)

**Quy tắc bất biến áp dụng cho T50:**
1. `vi_text` hiện tại (backfill T85) = "phân phối tự động" — KHÔNG dùng làm học thuật
2. Mọi citation/evidence phải dùng `passage_id`, không dùng ordinal index
3. Khi alignment table sẵn sàng: frontend tự động chuyển từ `≈` sang số thật

Xem: `tasks/T94-cbeta-alignment-schema.md` · `docs/cbeta-global-passage-standard.md`
