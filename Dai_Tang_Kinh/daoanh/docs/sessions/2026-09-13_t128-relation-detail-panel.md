# Session T128 — Relation Detail Panel (Tạm dịch AI + Đọc văn cảnh)

- **Ngày:** 2026-09-13
- **Trạng thái:** CODE DONE — chờ live QA (Groq quota trống để verify miss-path thật)
- **Depends:** T127 (shared Tree Design System — panel `_renderLineageInspectorEdge` chuẩn chung đã ổn định)

## Mục tiêu (plan approved, xem `tasks/T128-relation-detail-panel-translate-reader.md`)
Nâng cấp panel "Chi tiết mối quan hệ":
1. Nút **"✨ Tạm dịch AI"** — dịch evidence excerpt + badge "Dịch AI · cần hiệu đính" (cache theo text-hash, write-through `translation_cache`).
2. Đổi CTA "📖 Đọc trong Đại Tạng" → **"📖 Đọc văn cảnh"** — nhúng văn cảnh ±1 đoạn, highlight excerpt; fallback trung thực khi passage chưa index (T47n1990 → KHÔNG backfill).

## Backend (app.py — additive, 0 ALTER)
- `_T128_WORKID_RE = r'(?:[A-Za-z]\d+n[A-Za-z]?\d*)'` — sau unit test phát hiện `J40nB486` không khớp `J\d+n\d+` (sau n là chữ số theo sau bởi chữ+c) → mở rộng.
- `_t128_parse_relation_ref(ref, from_id, to_id, direction)` → `{relation_id=sha1('|'.join([from,to,direction]))[:12], source(URL CBETA), work_id, locator, original_excerpt, text_hash=sha256(excerpt)[:24], has_ref}`. Locator đuôi dạng `（T47n1990_p0582a19）`/`(…)`; fallback URL CBETA; trung thực (thiếu gì bỏ nấy, không bịa).
- `POST /daoanh/api/relation/translate` — body `{ref, relation_id, from_id, to_id, direction}`:
  - Cache hit: `translation_cache WHERE source_hash=? AND source_type='relation_evidence' AND status!='invalidated' ORDER BY id DESC LIMIT 1` → `from_cache:true`, KHÔNG gọi LLM.
  - Miss: `_t73_build_style_prompt(xs[:1400], _t73_style_lock(conn), label='đoạn dẫn chứng')` + `_t73_call_gemini` → `INSERT OR REPLACE` status='draft', entity_id=relation_id.
  - Không có excerpt → 422; LLM fail → 503 `{error_type}`.
  - KHÔNG dùng legacy `/api/translate` (Claude cần passage_id).
- `GET /daoanh/api/lineage-ref/context?ref=...` — `_t86_parse_ref_passage` → current + prev (`text_id=? AND passage_id<? ORDER BY passage_id DESC LIMIT 1`) + next (`ASC LIMIT 1`) → `{ok, parsed, resolved, context[]}`. found:false → still 200, UI fallback trung thực.

## UI (places.html)
- `_linEdgeState={edge, ctrl}` module state + `_linEdgeAbort()` — set/abort ở đầu `_renderLineageInspectorEdge`; trả `_linEdgeState.edge` mỗi render.
- `_t128ParseRef(ref)` — mirror client-side (relation_id + excerpt cho hiển thị ngay + POST).
- `t128TranslateEdge()` — AbortController fetch → spinner → cache-hit/draft hiển thị: badge `.dt-bilingual-badge` gold "✨ Dịch AI · cần hiệu đính" (+ "(bộ nhớ đệm)" nếu from_cache) + Hán (.dt-seg-han) + Vi (.dt-seg-vi) + model/#cache.
- `t128ReadContextEdge()` — fetch context → `.dt-bilingual-badge.dt-ref-badge` green "📖 Văn cảnh ±1 đoạn" + từng passage (current gold border ◈, prev/next neutral) + `_t128Highlight` mark excerpt trong raw_text + nút "↗ Mở trong Đại Tạng" (`openDaiTangReader(pid)`) + link ↗ CBETA.
- Fallback: excerpt gốc + "not-indexed — … • **Cần khảo cứu.**" + ↗ CBETA.
- Gate buttons `if (e.has_ref)`; `<div id="lin-edge-area">`; pwa văn cảnh `_escHtml` mọi render, `_t128ErrorBox` thay alert.

## Verify
- [x] Parser unit test (5 case: T47n1990/p0582a19, B35n0194 URL, J40nB486 URL, empty, locator-only) — ALL PASS; relation_id deterministic.
- [x] Smoke context T47n1990 → found:false, parsed.work_id=T47n1990 locator=p0582a19 text_hash=77c421... → UI fallback trung thực.
- [x] Smoke context T51n2076 (_p0234a05) → found:true pid=1 ctx=2 (pid1 len185 + pid2 len8; prev none vì đoạn đầu).
- [x] Smoke translate cache-hit: seed row hash 77c421eb... → POST → ok from_cache:true tid=737 → DELETE row (đã clean).
- [x] Smoke translate miss → **503 err_type=rate_limit** — Groq quota chạm trần (key dùng chung với T95/T96 CBETA translate đang chạy 15:4x). Transient, đúng graceful.
- [x] node --check places.html (1 inline block, 460,333 chars) PASS.
- [x] npm run pipeline: lint (ESM warning pre-existing), test PASS, e2e static PASS; e2e:runtime EPERM pre-existing.
- [ ] Live QA (:8080 Ctrl+F5; cần :5000 đã restart PID 14500).

## Ghi chú / chặn
- **That's e2e/lint chỉ check `admin/placevn.html` (125KB cũ) — KHÔNG check `places.html` (553KB live).** Đã chạy node --check trực tiếp trên places.html.
- Groq quota: admin đang chạy luồng dịch CBETA T95/T96 trên cùng key → propose test miss-path lúc vắng hoặc chờ quota reset.
- Kết nối: gateway_local :8080 phục vụ places.html từ disk (không restart); backend :5000 restart PID 14500.
- **Chưa commit** (policy: chỉ commit khi user yêu cầu). Sẵn sàng temp-index commit `b4_commit.py` theo yêu cầu.
- Concurrency: git index có staged deletions ngoài (external agent) — không đụng; commit qua temp-index.
- Backup file: `docs/sessions/places.html.bak-t127-tree-design-system.html` (trước T127) — T128 chỉ thêm block JS + sửa 2 hàm panel; có thể backup `places.html.bak-t128` khi commit.

## Next
1. Live QA khi: (a) quota Groq trống → test miss-path thật (bản dịch + badge); (b) admin mở :8080 → 應真→慧寂 → ✨ Tạm dịch AI + 📖 Đọc văn cảnh (T47n1990 → fallback).
2. Nếu QA pass → T128 → DONE; chuyển T127 + T128 sang `taskdone.md`.
3. Ghost race test: chọn relation A rồi ngay relation B → chỉ B render.