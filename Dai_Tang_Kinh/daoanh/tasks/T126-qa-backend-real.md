---
id: T126
title: "Q&A Backend thật + Wire UI (toàn hệ thống)"
priority: high
status: done
owner: AI Engineer (build) · Lee Tổng (phê chuẩn)
module: Hạ tầng / Docs
created: 2026-09-13
updated: 2026-09-13
---
# T126 — Q&A Backend thật + Wire UI (toàn hệ thống)

**Status:** done (build 2026-09-13, live :5000 + :8080)
**Ngày:** 2026-09-13
**Phạm vi:** `app.py` (backend T126) + `places.html` (wire `dtRunQA`/`dtRunDS` thật) + backup + docs.
**Ràng buộc:** additive-only, 0 ALTER, commit temp-index (real index đang có staged deletions từ agent ngoài).

## Mục tiêu
Thay UI safe-fallback (T125/T124) bằng **QA thật**: retrieval toàn hệ thống + LLM Groq, với UI states B (busy spinner thật) / D (no_data) / E (answer).

## Backend — POST /daoanh/api/daitang/qa (app.py)
Endpoint toàn hệ thống (OTT: Đạo Ảnh, TTL, Marcus, dossier, translation). Body JSON `{"question"}`.

### Retrieval (retrieval toàn hệ thống)
| Tầng | Kỹ thuật | verified |
|---|---|---|
| Tokens | `_t126_tokens` → `(vn_norm, vn_orig, han)` — vn_norm bỏ dấu (GLOB), vn_orig giữ dấu (LIKE VN), han Hán trực tiếp | ✓ |
| Hán reverse | `_t126_vn_to_han` (glossary_vi → glossary_term zho) + `extra_han` (name_zh entity) | ✓ |
| P1 (Hán) | từng term dài nhất trước (raw_text/norm_text LIKE), dedupe, `ORDER BY has_vi DESC` | ✓ 雁門關→passage 867 T51n2076 |
| P2 (Việt) | full-phrase `lower(vi_text)/translation_draft LIKE lower(pattern)` (SQLite LIKE case-sensitive ngoài ASCII) | ✓ 'Bồ tát' 29 hits |
| Entity | `_t126_entity_match`: places (`namevi_map_places` 118k) + people (48k), longest-phrase 4→2 token đầu tiên có hit, GLOB char-class dấu-linh-hoạt (`_GLOB_CLASS`), `ORDER BY length(nv) ASC` | ✓ Nhạn Môn Quan→雁門關 PL003873 |

### LLM + Response
- `_t126_build_qa_prompt`: Style Constitution `_t73_style_lock` (rules 12) + evidence `[1..n]` → "trả lời TIẾNG VIỆT, DUY NHẤT từ tư liệu, kèm [số]".
- `_t126_call_groq`: `GROQ_URL` + model `GROQ_MODEL` (qwen/qwen3.8-27b), key từ `llm_config.json`/env. Err 401/403→key_error; 429→rate_limit.
- Response contract: `ok:true mode:'llm'|'retrieval_only'` (citations/evidence/entities/model/latency_ms) | `ok:false mode:'no_data'` (200) | `ok:false error` (400/500).

## UI — places.html (wire thật)
- `dtRunQA()`: validation inline (giữ), state **busy** (⏳ spinner "Đang tra cứu…") → POST `/daoanh/api/daitang/qa` → E: `_dtRenderQAAnswer` (answer `_escHtml`, meta mode/model/ms, mục "📚 TƯ LIỆU LIÊN QUAN": icon 📜/👤/📍 + nhãn + snippet, click copy); D: no_data (📭); HTTP/network lỗi (⚠️). Chống submit trùng `data-qa-state==='busy'`.
- `dtRunDS()` (DeepSearch tab): cùng endpoint, chỉ hiển thị tư liệu/thực thể (không kèm answer).
- Helpers mới: `_dtQAStateIcon`, `_dtQACiteLabel`, `_dtRenderQAAnswer`, `dtQACopy`.
- Dùng lại CSS `dt-qa-ans`/`dt-qa-cite`/`dt-ds-state` (T125/T124); `_escHtml` mọi chuỗi user/API.

## Verify
- `python -m py_compile app.py` PASS (nhiều lần sau refactor entity/match).
- Retriever test `_t126_retrieve` trên DB thật: "Nhạn Môn Quan có trong tác phẩm nào?" → entities 雁門關/雁門郡, evidence passage 867 T51n2076; "Bồ tát" → entities Bồ Tát Tự/閣/泉/Đường + passage; "Thích Ca Mâu Ni Phật" → entities Thích Ca Điện/Viện/釋迦; "Ai sáng lập nơi này?" → 0 (no_data path).
- Live :5000 (restart wmic) `POST /daoanh/api/daitang/qa`:
  - "Nhạn Môn Quan có trong tác phẩm nào?" → **mode=llm, model=qwen/qwen3.8-27b, 5.5s, answer trích dẫn T51n2076 [2] chính xác 紅罏不墜雁門關** + 6 evidence (gồm passage 867) + 6 entities.
  - "Ai sáng lập nơi này?" → `ok:false mode:no_data` (200).
  - `{}` → 400 "Thiếu câu hỏi".
- Live :8080 gateway: `GET /daoanh/places` trả page mới (chứa `daoanh/api/daitang/qa` + "Đang tra cứu"); `POST` qua gateway → mode llm 200. T126 **LIVE**.
- `npm run test` PASS, `npm run e2e` static PASS (e2e:runtime EPERM + lint Node v24 ESM-format pre-existing).

## Files
- `app.py` — block T126 (helpers + route) trước `if __name__ == '__main__'`.
- `docs/sessions/app.py.bak-t126-snapshot.py` — backup pre-T126.
- `places.html` — wire `dtRunQA`/`dtRunDS` thật.
- `tasks/T126-qa-backend-real.md`, `docs/sessions/2026-09-13_t126-qa-backend-real.md`, `docs/tasktodo.md`, `data/progress_data.json`.

## Rolling back
- `git revert <commit>` (temp-index). Real index staged deletions KHÔNG đụng.

## Ghi chú / next
- P2 fallback "từng token '%Bồ%tát%'" đã bỏ (nhiễu 'Bồ-đề'); dùng full-phrase + `lower()`.
- Entity 1-token không dùng (nhiễu "Thi Châu" ← 'thich'); chỉ phrase ≥2 token, longest-first.
- Groq key mới đã 401 invalid; key live trong `llm_config.json` (gitignored) — `retrieval_only` fallback an toàn.
- DeepSearch tab giờ cùng backend QA — cân nhắc endpoint riêng `/deepsearch` sau nếu cần.