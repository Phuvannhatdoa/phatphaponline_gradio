---
id: T125
title: "Q&A Tab Safe-Fallback (đồng bộ pattern T124 DeepSearch)"
priority: high
status: done
owner: AI Engineer (build) · Lee Tổng (phê chuẩn)
module: Hạ tầng / Docs
created: 2026-09-12
updated: 2026-09-12
---
# T125 — Q&A Tab Safe-Fallback (đồng bộ pattern T124 DeepSearch)

**Status:** done (build 2026-09-12, live :8080)
**Ngày:** 2026-09-12
**Phạm vi:** 1 file `places.html` (tab ❓ Hỏi & Đáp) + backup + docs.
**Ràng buộc:** additive-only, KHÔNG đụng app.py/DB, commit temp-index (real index đang có staged deletions từ agent ngoài).

## Vấn đề (verified 2026-09-12)
Tab Hỏi & Đáp (`dtRunQA`) dùng pattern mock + leak giống DeepSearch cũ (đã sửa ở T124):

| Vị trí (places.html cũ) | Lỗi |
|---|---|
| L694 idle banner | `AI trả lời có trích dẫn nguồn · API đang phát triển` — hứa hẹn tính năng không tồn tại |
| L3526 | Fake spinner `Groq RAG đang xử lý...` (không có request thật) |
| L3531 | **Leak endpoint + stack:** `Cần: POST /daoanh/api/entity/{id}/qa + RAG pipeline + Ollama/Groq` |
| L3527-3534 | `setTimeout(...800)` — giả vờ xử lý rồi trả "chưa sẵn sàng" |

**API Q&A verified = KHÔNG tồn tại:** 0 route `/qa|/deepsearch|/semantic|/answer` trong toàn bộ `*.py` (tương tự T124 DeepSearch). `search.js` có `searchWithRAG`/`RAGConnector` — chưa dùng, chờ backend thật.

## Kế hoạch sửa (an toàn, trung thực UI)
Đồng bộ y đúc pattern T124 DeepSearch:

1. **HTML tab (L683-696):**
   - Giữ header "Đặt câu hỏi về văn bản Phật giáo".
   - Thêm `aria-label` cho input/button (accessibility).
   - Enter → `preventDefault()` để tránh submit form ẩn (giống DS L676).
   - `dt-qa-examples`: chips gợi ý bấm **fill + focus** (không tự submit) + clear validation.
   - Thêm `#dt-qa-validation` (inline validation, không alert) — giống `#dt-ds-validation`.
   - Thêm `#dt-qa-hint` (Gợi ý bấm được).
   - Idle ban đầu render qua JS `dtRenderQAIdle()` (bỏ nội dung tĩnh hứa hẹn API).

2. **JS `dtRunQA()` (L3522-3535):**
   - Bỏ mock spinner, bỏ `setTimeout`, bỏ leak endpoint/Groq.
   - Validation: input trống → hiện `#dt-qa-validation` + focus + idle state.
   - Nếu có câu hỏi: render state **unavailable** an toàn: "Hỏi & Đáp đang được hoàn thiện — Bạn vẫn có thể tra cứu qua các tab Dẫn Chiếu, Nguyên Văn và Quan Hệ." (không lộ endpoint/Groq).
   - Giữ `_escHtml` cho câu hỏi nhắc lại (chống XSS).

3. **JS `dtRenderQAIdle()`:** hook vào `dtSwitchTab` khi `name==='qa'` (renders idle đúng một lần khi chưa có input), ghi `data-qa-state`. Giống `dtRenderDSIdle`/`dtUseSuggestion`.

4. **CSS:** dùng lại class `dt-ds-state`/`dt-ai-*` đã có (T124) — 0 CSS mới cần thiết. Nếu cần, thêm tối thiểu.

## Verify
- `node --check` (1 block script) → PASS.
- Logic test Node (DOM stub) → **18/18 PASS** (validation trống → idle+focus; whitespace → validation;
  có hỏi → unavailable không lỗi, không Groq/endpoint/Ollama, không setTimeout; suggestion fill+focus,
  idle render 1 lần, `_escHtml` chống XSS).
- `npm run test` + `npm run e2e` (static "All pages passed"; e2e:runtime EPERM pre-existing).
- Live :8080: page mới có `dt-qa-validation`/`dtUseQASuggestion`/`dtRenderQAIdle`, KHÔNG còn Groq/mock → **LIVE**.

## Files
- `places.html` — sửa Q&A tab.
- `docs/sessions/places.html.bak-qa-t125` — backup trước khi sửa.
- `docs/sessions/2026-09-12_t125-qa-tab-safe-fallback.md` — session log.
- `docs/tasktodo.md`, `data/progress_data.json` — cập nhật.

## Rollback
- `git revert <commit>` (commit temp-index) — real index staged deletions KHÔNG đụng.