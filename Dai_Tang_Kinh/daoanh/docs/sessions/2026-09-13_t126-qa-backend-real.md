# Session 2026-09-13 — T126 QA Backend Real + Wire UI

## Bối cảnh
Sau T123 (Style Constitution :5000) + T124/T125 (DeepSearch + Q&A tab safe-fallback :8080), task này
dựng **QA backend thật** (display "build QA thật" -> ENDPOINT "POST /daoanh/api/daitang/qa") + wire
`dtRunQA`/`dtRunDS` thật trong places.html. Người dùng interject "hi" giữa build — ack và tiếp tục.

## Nghiên cứu schema (trước khi build)
- `passage` 7,563; `cbeta_catalog_vn` 3,122 (sigla/title_vi/dynasty_vi/translator_vi/q_number);
  `people` 48,673; `places_dila` 59,167; `glossary_vi` + `glossary_term` 248,095; `translation_cache` 529;
  `namevi_map_places` 118,296 (name_vi/name_zh/dila_id/note_vi/gps/district_vi/country_vi) — reverse lookup VN→Hán.
- `name_vi_map` 51,141 bị nhiễu (bio_snippet) → KHÔNG dùng; dùng `people`.
- GLOB `[..]` char-class hoạt động; LIKE không hỗ trợ `[]`. Verified: 'Nhạn Môn Quan' → 雁門關 (PL003873);
  passage 867 (T51n2076) raw `台州六通院志球...紅罏不墜雁門關`; `lower(vi_text) LIKE '%bồ tát%'` → 29 hits.

## Build app.py (block T126 trước `if __name__`)
Helpers: `_t126_has_han`, `_t126_tokens` (3-tuple), `_t126_vn_to_han`, `_GLOB_CLASS`,
`_t126_glob_pattern`, `_t126_entity_match` (places+people, longest-phrase-first),
`_t126_retrieve` (P1 từng-han-term-longest-first / P2 full-phrase lower),
`_t126_build_qa_prompt` (Style Constitution), `_t126_call_groq`, route `POST /daoanh/api/daitang/qa`.

### Refactor quan trọng (khi retest)
1. **Entity nhiễu org-name** ("Thi Châu" cho 'thich', "Bộc"/"Bồ Âm" cho 'bo') → bỏ fallback 1-token;
   thử LẦN LƯỢT phrase 4→2, lấy longest-phrase đầu có hit.
2. **P2 noise** ('Bồ-đề-đạt-ma' hit '%Bồ%tát%') → full-phrase + `lower()` 2 vế (SQLite LIKE case-sensitive
   ngoài ASCII) — KHÔNG fallback từng token.
3. **P1 OR+LIMIT flood** (雁門郡 lấn 雁門關, passage 867 vi=None tụt dưới raster) → vòng từng term
   sorted `(len, index) reverse`, `LIMIT 4`/term, dedupe, `ORDER BY has_vi DESC`. → 雁門關 lên top.

## Build places.html (wire thật)
`dtRunQA` và `dtRunDS` bỏ state 'unavailable' → POST `/daoanh/api/daitang/qa`:
- validation inline giữ; busy state (⏳ "Đang tra cứu…"/"Đang tìm kiếm…") + chống submit trùng `dataset busy`.
- `_dtRenderQAAnswer` (QA): answer `_escHtml` + meta (mode/model/ms) + `📚 TƯ LIỆU LIÊN QUAN` (icon + nhãn + snippet, click copy).
- no_data → 📭; http/network lỗi → ⚠️.
- DS: chỉ hiển thị tư liệu (không answer). Helpers: `_dtQAStateIcon`, `_dtQACiteLabel`, `_dtQACopy`.

## Verify
- py_compile PASS; retriever test: Nhạn Môn Quan→雁門關+passage 867; Bồ tát→Bồ Tát Tự/閣/泉/Đường+passage;
  Thích Ca Mâu Ni Phật→釋迦 entities+passage; "Ai sáng lập nơi này?"→0/0 (no_data).
- Restart :5000 (wmic kill 24948, app.py PID 7656): `POST /daoanh/api/daitang/qa` → mode **llm**
  (qwen/qwen3.8-27b, 5.5s, answer trích T51n2076 [2] chính xác), no_data (200), `{}`→400.
- Gateway :8080 (local_gateway.py PID 2616) serve page mới + proxy QA → mode llm. LIVE.
- npm run test PASS; npm run e2e static PASS. Lint Node v24 ESM + e2e:runtime EPERM = pre-existing.

## Files
- `app.py` edit (T126 block ~347 dòng, file ~18,418 dòng).
- `docs/sessions/app.py.bak-t126-snapshot.py` mirror git HEAD pre-T126 (831,131 bytes).
- `places.html` edit dtRunQA/dtRunDS (+ helpers).
- `tasks/T126-qa-backend-real.md`, `docs/sessions/2026-09-13_t126-qa-backend-real.md`,
  `docs/tasktodo.md`, `data/progress_data.json`.

## Ghi chú / next
- Không tạo route DeepSearch riêng — DS tab dùng chung QA endpoint (hiển thị evidence thôi).
- Sentinel: server app.py :5000 + gateway :8080 đang chạy (từ PowerShell phiên này).
- Key Groq: mới 401 invalid; live trong `data/llm_config.json` (gitignored). `retrieval_only` fallback đủ an toàn.
- Backup cho task tiếp theo: T127 có thể = P2 fallback từng-token an toàn nếu full-phrase miss (dùng ' '.join ≥2),
  hoặc danh mục kinh flipped (title_vi trong cbeta_catalog_vn + sigla lookup passage text_id).