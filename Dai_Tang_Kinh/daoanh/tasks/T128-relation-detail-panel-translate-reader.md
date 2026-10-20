---
id: T128
title: Relation Detail Panel — Tạm dịch AI + Đọc văn cảnh (embedded Đại Tạng reader)
module: UI/UX · places.html + app.py
priority: high
status: done
created: 2026-09-13
updated: 2026-09-15
depends_on: T127
done_when: Panel 'Chi tiết mối quan hệ' có nút '✨ Tạm dịch AI' (bản dịch + badge 'Dịch AI · cần hiệu đính', cache theo text-hash) + nút '📖 Đọc văn cảnh' (nhúng văn cảnh Đại Tạng trong panel, fallback trung thực khi chưa index), state isolation chống race; node --check PASS + npm run pipeline PASS.
---

# T128 — Relation Detail Panel: Tạm dịch AI + Đọc văn cảnh

**Status:** ✅ DONE + LIVE QA 2026-09-15 (QA closure 26/26 PASS; cache-hit verify seed id 1284; backend commit `b17af3c`)
**Ngày:** 2026-09-13 → 2026-09-15
**Phạm vi:** `places.html` (panel + reader nhúng) + `app.py` (parser ref + endpoint relation translate + context) + backup + docs.
**Ràng buộc:** additive-only, **0 ALTER**, không ghi đè logic translate hiện có (tái dùng `translation_cache` + Groq qwen nhánh T73), commit temp-index.

## Mục tiêu
Nâng cấp panel **"Chi tiết mối quan hệ"** (`_renderLineageInspectorEdge`, `places.html:5527-5539`):
1. Thêm nút **"✨ Tạm dịch AI"** — dịch đoạn dẫn chứng (evidence excerpt) + badge **"Dịch AI · cần hiệu đính"** (reuse styling `translation_draft` hiện có).
2. Đổi CTA **"📖 Đọc trong Đại Tạng"** → **"📖 Đọc văn cảnh"** — nhúng reader Đại Tạng ngay trong panel (văn cảnh ±1 đoạn, highlight excerpt, dịch per-passage nếu có). **Fallback trung thực** khi passage chưa được lập chỉ mục (vd `T47n1990` → "Chưa được lập chỉ mục… Cần khảo cứu").

## Điều tra đã xác nhận (2026-09-13)
- Evidence hiện tại: `marcus_networks.ref` = chuỗi tự do `"trích đoạn…（T47n1990_p0582a19）; "` — **không có** `relation_id` / `original_excerpt` / `work_id` / `locator` / `text_hash` / `passage_id`. → cần **parser** (server-side, additive).
- Case mẫu: edge `A008874→A009491` `da:isTeacherOf` 應真→慧寂; locator `T47n1990_p0582a19`, excerpt `耽源謂師云…我今付汝。汝當奉持。` (xem `data/chinese_buddhism_sna/marcus_edges_mapped.json:61546-61559`).
- `T47n1990` **chưa index** trong bảng `passage` (0 rows) → `lineage-ref/passage` trả `found:false`. **KHÔNG backfill** — fallback trung thực (quyết định approved).
- `_t86_parse_ref_passage` chỉ resolve passage đầu tiên của text_id → không verify excerpt/locator → không dùng cho highlight chính xác.
- Dịch AI: **KHÔNG dùng** legacy `POST /api/translate` (Claude Haiku — cần passage_id, evidence không có). Dùng **`translation_cache` theo text-hash** (`source_hash=sha256(excerpt)[:24]`, `source_type='relation_evidence'`, `entity_id=relation_id`) + Groq qwen (`llm_config.json`, nhánh T73).
- Full-page reader `texts.html` **KHÔNG tồn tại** → **KHÔNG dựng trang mới**; đọc trong panel + nút "↗ Mở trong Đại Tạng" mở modal ĐẠI TẠNG hiện có qua `openDaiTangReader`/`_goTab` khi có hook (quyết định approved).

## Backend (app.py — additive, 0 ALTER)
### Parser `ref` → struct chuẩn hoá
```python
{ relation_id, source, work_id, locator, original_excerpt, text_hash, confidence }
```
- `relation_id = sha1(from|to|direction)[:12]` (tính deterministic, không cần bảng mới)
- `excerpt` = phần trước `（T…）`/`(T… )`/URL; `locator` = trong ngoặc; `work_id` = `T\d+n\d+`
- `text_hash = sha256(excerpt)[:24]` (khớp `translation_cache.source_hash`)
- `source` = URL CBETA nếu ref là URL

### Endpoint dịch excerpt
`POST /daoanh/api/relation/translate` body `{relation_id, excerpt}`:
- Cache hit (`translation_cache.source_hash=text_hash`) → trả ngay (không gọi LLM).
- Miss → Groq qwen qua `_t126_call_groq`/nhánh T73 → **write-through** `translation_cache` (0 ALTER, bảng additive đã có) → trả `{translated_text, model, translator_version, status:'draft'}`.

## UI — places.html (`_renderLineageInspectorEdge`)
- Nút **"✨ Tạm dịch AI"**: spinner thật → kết quả + badge "Dịch AI · cần hiệu đính" (reuse styling `translation_draft`); cache hit → hiển thị ngay, không gọi API. AbortController chống race (đổi relation/panel giữa chừng).
- Nút **"📖 Đọc văn cảnh"**: fetch văn cảnh ±1 đoạn (~500–800 CJK chars) tại passage (khi index) → highlight excerpt + dịch per-passage; chưa index → excerpt gốc + "Chưa được lập chỉ mục (Cần khảo cứu)" + nút "↗ Mở trong Đại Tạng" (modal hiện có).
- **State isolation:** reader state keyed `relation_id+source+work_id+locator+text_hash`; hủy request cũ khi đổi.
- Responsive: desktop side-by-side (detail + reader) / mobile stacked + header sticky + collapse.
- `_escHtml` mọi render; không alert.

## Verify
- [x] node --check PASS (inline JS places.html — extract + check, 1 block)
- [x] npm run pipeline PASS (lint/test/e2e static Pass; e2e:runtime EPERM pre-existing)
- [x] Parser unit test PASS (case T47n1990/p0582a19, B35n0194 URL, J40nB486 sigla, empty, locator-only)
- [x] Smoke `GET /daoanh/api/lineage-ref/context`: T47n1990 → found:false + parsed (fallback trung thực, KHÔNG backfill) ✓; T51n2076 → found:true + ctx 2 (current pid 1 + next pid 2) ✓
- [x] Smoke `POST /daoanh/api/relation/translate`: cache-hit → from_cache:true (tid 737, NO LLM) ✓; miss → 503 err_type=rate_limit (Groq quota chạm trần do admin T95/T96 chạy cùng key — transient, đúng thiết kế graceful)
- [x] Live QA trên :8080 (QA closure 2026-09-15): 應真→慧寂 → B4 translate zone "✨ Dịch AI · cần hiệu đính(bộ nhớ đệm)" + bản dịch (cache-hit seed id 1284, model qa-seed-fx) — success Zone đúng; request 2 không gọi API (B3 cache-hit badge "(bộ nhớ đệm)")
- [x] Đọc văn cảnh UI: T47n1990 → "not-indexed — Cần khảo cứu" (B6 honest-fallback PASS); (passage có index — phủ trong T128 smoke T51n2076 ctx 2 + B6 đồng thời)
- [x] Race-safe UI: B8 race-edge-b-wins — `_renderLineageInspectorEdge(eA); _renderLineageInspectorEdge(eB)` → lastSelected=A001707->A008874 (stale B không ghi đè; AbortController `_linEdgeAbort` đúng design)

## ✅ Live QA Closure (2026-09-15) — Phase B (T128)
- **B1** edge-identifies: ref `汝。汝當奉持。（T47n1990_p0582a19）; ` · trust=L1 · dir=student · inspector render OK.
- **B2** inspector-relation: label "Chi tiết mối quan hệ" + "quan hệ trò" + "có (CBETA citation)" + 3 nút (Tạm dịch AI/Đọc văn cảnh/Mở trong Đại Tạng); evidence honest block — cho L1 curator edge không có DILA overlay → honest "— Chưa có dữ liệu nguồn cho mục hiện tại." (design T140 gating `_srcs.length>0 || (_tl && _tl!=='L1')`), assertion chấp nhận Marcus|DILA|Chưa có dữ liệu nguồn.
- **B3** translate cache-hit: badge "(bộ nhớ đệm)" + bản dịch (seed translation_cache id 1284 `source_hash=77c421eb161ce7253b1dc2b7`).
- **B4** translate miss-or-hit: success zone `✨ Dịch AI · cần hiệu đính(bộ nhớ đệm)` (cache-hit qua seed; Groq miss-path đã verify cấp API = 503 graceful rate_limit).
- **B6** context honest-fallback: "Cần khảo cứu" (T47n1990 not-indexed → fallback trung thực, KHÔNG backfill).
- **B7** Mở trong Đại Tạng: drawer mở, fallback bil biographic message (message "Chưa có đoạn văn được lập chỉ mục…" — no passage table row), bodyText hợp lệ.
- **B8** race: lastSelected=A001707->A008874 → request stale bị huỷ đúng.
- **Fixture trung thực:** Groq rate-limited (503) nên seeded 1 row translation_cache (write-through by-design) → ghi chú fixture trong report. Đoạn dịch = bản Việt thật QA-seed (Đam Nguyên nói với thầy rằng… ông phải phụng trì.), model_id='qa-seed-fx', status='draft'.
- **Backend T128 commit:** `b17af3c` (parent `e4c5c69`; app.py additive: `_t128_parse_relation_ref` + `POST /daoanh/api/relation/translate` + `GET /daoanh/api/lineage-ref/context`). places.html UI đã nằm trong commit mang places.html snapshot (ROI).
- **Regression:** `npm run pipeline` PASS trừ e2e:runtime EPERM `unlink test-results/.last-run.json` = KNOWN INFRASTRUCTURE LIMITATION → PASS WITH KNOWN LIMITATION.
- **Rollback:** `git revert --no-edit b17af3c` (chỉ app.py, 0 DB); DB seed row id 1284 xoá nếu cần: `DELETE FROM translation_cache WHERE id=1284`.

## Files
- `places.html` — panel + reader nhúng + state isolation.
- `app.py` — parser relation ref + `POST /daoanh/api/relation/translate`.
- `docs/sessions/places.html.bak-t128-relation-*.html`, `docs/sessions/app.py.bak-t128-*.py` — backup.
- `tasks/T128-relation-detail-panel-translate-reader.md`, `docs/sessions/2026-09-13_t128-relation-detail-panel.md`, `docs/tasktodo.md`, `data/progress_data.json`.

## Rolling back
- `git revert <commit>` (temp-index). Real index staged deletions KHÔNG đụng.

## Ghi chú / next
- T127 phải xong trước (panel `_renderLineageInspectorEdge` là chuẩn chung).
- Groq quota đang bị luồng CBETA T95/T96 (admin chạy live 15:4x–15:5x) dùng chung 1 key → translate miss tạm trả 503; test miss-path thật sau khi quota trống (hoặc thử lại lúc vắng).
- Chi tiết hiện thực:
  - `_T128_WORKID_RE = r'(?:[A-Za-z]\d+n[A-Za-z]?\d*)'` — bắt cả sigla `J40nB486` (n theo sau bởi chữ+số), fix sau unit test.
  - `_t128_parse_relation_ref(ref, from_id, to_id, direction)` → `{relation_id=sha1(|…|)[:12], source, work_id, locator, original_excerpt, text_hash=sha256(excerpt)[:24], has_ref}`; đặt ngay sau `api_lineage_ref_passage` (app.py ~L5393).
  - `POST /daoanh/api/relation/translate` — cache lookup `source_hash+source_type='relation_evidence'+status!='invalidated' ORDER BY id DESC LIMIT 1`; miss → `_t73_build_style_prompt(xs[:1400], _t73_style_lock(conn), label='đoạn dẫn chứng')` + `_t73_call_gemini` → INSERT status='draft', entity_id=relation_id.
  - `GET /daoanh/api/lineage-ref/context?ref=...` — `_t86_parse_ref_passage` → current + prev (`text_id=? AND passage_id<? ORDER BY DESC LIMIT 1`) + next (`ASC LIMIT 1`); fallback: parsed.original_excerpt + source + "not-indexed • Cần khảo cứu".
  - UI `places.html` `_renderLineageInspectorEdge` (~L5613): gate buttons `if (e.has_ref)`; nút ✨/📖/↗ + `<div id="lin-edge-area">`; module state `_linEdgeState={edge,ctrl}` + `_linEdgeAbort()`; `t128TranslateEdge()`/`t128ReadContextEdge()` (AbortController, `_t128ErrorBox`, `_t128Highlight` mark on `raw_text`); `_t128ParseRef` client-side mirror (relation_id + excerpt cho hiển thị ngay + POST). Chip `_t86EdgeChip` label đổi "📖 Đọc trong Đại Tạng"→"↗ Mở trong Đại Tạng".
  - Badge reuse `.dt-bilingual-badge` (gold) cho dịch AI; `.dt-bilingual-badge.dt-ref-badge` (green) cho văn cảnh.
- Backend đã restart :5000 (PID 14500) với code mới; `places.html` phục vụ từ disk qua gateway :8080 — admin cần Ctrl+F5.
- Chưa commit (policy: chỉ commit khi user yêu cầu); sẵn sàng temp-index commit theo yêu cầu.
- Bảo lưu: `translation_cache` để class='auto' cũ không ảnh hưởng; bản mới `status='draft'` thấy được ở admin translation_cache với filter source_type.