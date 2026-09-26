---
id: T124
title: "DeepSearch UI V1 — Safe-Fallback (biến tab 🤖 DeepSearch từ mock thành UI hoàn chỉnh, không backend)"
module: Editorial / User Frontend
priority: high
status: done
depends_on: []
created: 2026-09-12
updated: 2026-09-12
plan_approved_at: "2026-09-12 (Lee phê chuẩn đề xuất — ít nhất là UI/UX safe-fallback, debugger sẽ trả lời sau khi xác minh.)"
done_when: "Tab DeepSearch trong places.html: có mô tả 'Hỏi theo ngữ cảnh', gợi ý bấm được fill+focus không submit, placeholder tiếng Việt, Enter=nút, validation inline input trống, đủ states idle/loading/unavailable (no-result/result là code path), không lộ endpoint/Groq; không regression 4 tab kia; npm run pipeline PASS; commit temp-index revert được."
---

# T124 — DeepSearch UI V1 (Safe-Fallback) (2026-09-12)

Kế hoạch chi tiết thảo luận + Lee phê chuẩn. Mục tiêu: biến tab **🤖 DeepSearch** trong
`places.html` từ chỗ hiển thị thử nghiệm (banner "Groq semantic ranking · API đang phát triển"
+ mock spinner/setTimeout) thành UI/UX hoàn chỉnh, an toàn khi backend chưa sẵn sàng.

## Nguyên nhân gốc
- `places.html:664` banner idle kỹ thuật: "Groq semantic ranking · API đang phát triển".
- `dtRunDS()` (places.html:3452-3465): not found validation (return im lặng), setTimeout 600ms
  giả lập loading, rồi hiện state "API chưa sẵn sàng" nhưng **lộ endpoint
  `POST /daoanh/api/entity/{id}/deepsearch + Groq semantic-rank`** (L3461) và nhắc Groq trên UI công khai.
- API DeepSearch thật: **KHÔNG tồn tại** trong `app.py`/`*.py` (0 route `/deepsearch`, `/qa`,
  `semantic-rank`). Chỉ có trong docs: `API_DOCS.md:146`, `DAI_TANG_KINH_TAB_SPEC.md`,
  `GAP_REPORT.md:729` đánh CRITICAL-missing. → Safe-fallback + không tự dựng request giả là đúng.

## Quyết định thiết kế (chốt 2026-09-12)
1. **Chỉ UI/UX + luồng client** trong `places.html`. KHÔNG sửa SQLite/corpus/source text,
   không gọi Groq thật, không thêm API key, không tạo câu trả lời/trích dẫn/dữ liệu giả.
2. **States:** A idle, B loading (chỉ khi có request thật — bỏ setTimeout giả), C unavailable
   (không lộ endpoint/Groq/stacktrace; nhắc tab Dẫn Chiếu/Nguyên Văn/Quan Hệ), D no-result,
   E result — D/E là code path chờ API thật khi đã xác minh route+payload+schema.
3. **Input:** placeholder tiếng Việt "Ví dụ: Nhạn Môn Quan có trong tác phẩm nào?";
   Enter = nút "🔍 Tìm kiếm"; input rỗng → validation inline "Hãy nhập một câu hỏi để bắt đầu
   tìm kiếm." (không alert()).
4. **Gợi ý:** "Gợi ý: Nhạn Môn Quan có trong tác phẩm nào?" bấm → fill + focus, không submit.
5. **Accessibility + an toàn render:** aria-label input/nút, focus state, dùng `_escHtml`
   (places.html:2193) cho mọi text render; không render undefined/null/[object Object].

## Checklist
- [x] T1. Task file T124 + session doc + tasktodo + `build_progress_data.py` (dashboard)
- [x] T2. Backup `places.html` → `docs/sessions/places.html.bak-deepsearch-t124`
- [x] T3. Tab HTML: mô tả "Hỏi theo ngữ cảnh" + nội dung dưới tab bar; placeholder VN mới
- [x] T4. Gợi ý bấm được (fill + focus, không submit) theo mẫu chips Q&A (places.html:2470)
- [x] T5. `dtRunDS()`: validation inline input rỗng (không alert, không return im lặng);
       Enter = nút; bỏ setTimeout giả; states A/B/C/D/E đúng UI copy + xóa leak endpoint/Groq
- [x] T6. Accessibility: aria-label input + button; focus state nhìn thấy
- [x] T7. Regression: 4 tab kia (Dẫn Chiếu/Nguyên Văn/Quan Hệ/Hỏi & Đáp) không hỏng;
       `_escHtml` cho mọi render; không console error mới
- [x] T8. `npm run test` + `npm run e2e` PASS (lint Node v24 + e2e:runtime EPERM = pre-existing)
- [x] T9. Commit temp-index (parent = HEAD b650e1b) — revert thuận tiện từng tầng

## Files
- `places.html` — tab DeepSearch (:658-666) + `dtRunDS()` (:3452-3465)
- `docs/sessions/places.html.bak-deepsearch-t124` — backup
- `tasks/T124-deepsearch-ui-safe-fallback.md`
- `docs/sessions/2026-09-12_t124-deepsearch-ui-v1.md`

## Done khi
UI DeepSearch hoàn chỉnh safe-fallback; không lộ endpoint/Groq; không regression; pipeline PASS;
commit temp-index revert được.