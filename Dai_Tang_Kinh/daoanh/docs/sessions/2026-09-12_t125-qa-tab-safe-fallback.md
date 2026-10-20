# Session 2026-09-12 — T125 Q&A Tab Safe-Fallback

## Bối cảnh
Sau T123 (Style Constitution, live :5000) + T124 (DeepSearch tab safe-fallback, live :8080),
tab ❓ Hỏi & Đáp trong places.html vẫn còn pattern mock + leak giống DeepSearch CŨ (đã sửa T124).

## Vấn đề (verified trước khi sửa)
| Vị trí | Lỗi |
|---|---|
| places.html cũ L694 | Idle banner `AI trả lời có trích dẫn nguồn · API đang phát triển` — hứa hẹn tính năng không tồn tại |
| places.html cũ L3526 | Fake spinner `Groq RAG đang xử lý...` (không có request thật) |
| places.html cũ L3531 | **Leak endpoint + stack:** `Cần: POST /daoanh/api/entity/{id}/qa + RAG pipeline + Ollama/Groq` |
| places.html cũ L3527-3534 | `setTimeout(...800)` giả vờ xử lý → "Q&A RAG — API chưa sẵn sàng" |

**API Q&A verified = KHÔNG tồn tại:** 0 route `/qa|/deepsearch|/semantic|/answer` trong toàn bộ `*.py`.
Đối chiếu live :5000 `GET /daoanh/api/entity/PL000000000002/qa` → 404 (đúng, backend chưa có).

## Sửa (1 file places.html)
- **HTML tab Q&A (L683-696):** thêm `dt-ds-head` (title + sub "Đặt câu hỏi tự nhiên về văn bản Phật giáo, nhân vật, địa danh..."), `aria-label` cho input/button, Enter → `preventDefault()` (không submit form), `#dt-qa-hint` (Gợi ý + `dtUseQASuggestion`), `#dt-qa-validation` (inline, không alert), `#dt-qa-result` trống (idle render qua JS). Bỏ idle banner cũ hứa hẹn API.
- **Example chips (`_dtRenderLeftRelated`):** chuyển sang dùng `dtUseQASuggestion(i+1)` — fill + focus + clear validation, **không auto-submit**, `type="button"` + class `.dt-ds-sug`.
- **`dtSwitchTab`:** hook `if (name==='qa') dtRenderQAIdle()`.
- **JS mới:**
  - `dtRenderQAIdle()` — idle render đúng 1 lần (giữ kết quả khi đã có text), ghi `data-qa-state`.
  - `dtUseQASuggestion(index)` — fill + focus + clear validation.
  - `dtRunQA()` (thay thế bản mock): input trống/whitespace → validation + idle + focus; có câu hỏi → state **unavailable** ("Hỏi & Đáp đang được hoàn thiện — Bạn vẫn có thể tra cứu qua các tab Dẫn Chiếu, Nguyên Văn và Quan Hệ"). Không setTimeout, không spinner giả, không leak endpoint/Groq, `_escHtml` mọi render.
- Dùng lại CSS `dt-ds-*`/`dt-ai-*` đã có (T124) — không thêm CSS mới cần thiết.

## Verify
- `node --check` 1 script block → **JS SYNTAX OK**.
- Logic test DOM stub → **18/18 PASS** (validation trống→idle+focus; whitespace→validation;
  có hỏi→unavailable không Groq/endpoint/Ollama; không setTimeout; `_escHtml` chống XSS;
  idle render 1 lần + giữ khi có text; suggestion fill+focus+clear validation).
- `npm run test` → **PASS**. `npm run e2e` (static) → **"All pages passed E2E checks!"**
  (e2e:runtime EPERM pre-existing; không tạo spec Playwright vì trang :8080 quá nặng — ghi nhận T124).
- Live :8080 verify: page có `dt-qa-validation`/`dtUseQASuggestion`/`dtRenderQAIdle`/`dt-ds-head`,
  KHÔNG còn "Groq RAG"/"/entity/{id}/qa"/"API đang phát triển". T125 **LIVE**.

## Files
- `places.html` (edit Q&A tab).
- `docs/sessions/places.html.bak-qa-t125` — backup trước sửa (525,847 bytes).
- `tasks/T125-qa-tab-safe-fallback.md`, `docs/sessions/2026-09-12_t125-qa-tab-safe-fallback.md`,
  `docs/tasktodo.md`, `data/progress_data.json`.

## Ghi chú
- 0 ALTER bảng, 0 app.py, additive-only. Real index staged deletions (agent ngoài) KHÔNG đụng.
- Commit temp-index. Rollback: `git revert <commit>`.
- Search.js `searchWithRAG`/`RAGConnector` chưa dùng — chờ backend Q&A thật (task riêng sau).