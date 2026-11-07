---
id: T524
title: "BUG-052 follow-up — retry có chờ khi Groq trả 429 cho route dila_translate"
status: in_progress
created: 2026-11-07
updated: 2026-11-07
done_when: >
  Route POST /daoanh/api/person/<id>/dila_translate retry gọi lại Groq
  (qwen/qwen3.8-27b) tối đa 3 lần tổng cộng khi gặp HTTP 429 / không có
  'choices' hợp lệ / finish_reason != 'stop' (có thể làm JSON parse lỗi ở
  bước sau). Thời gian chờ trước mỗi lần retry ưu tiên đọc Retry-After
  header hoặc "try again in Xs" trong body lỗi của Groq, fallback backoff
  cố định 1s/2s nếu không tìm được gợi ý. KHÔNG đổi max_tokens=4096,
  groq_model/GROQ_URL, timeout=35 của MỖI request; KHÔNG đổi điều kiện
  fallback Gemini (vẫn chạy khi vi_text None sau khi Groq hết retry). Giữ
  nguyên 3 dòng log cảnh báo cũ (finish_reason, no choices, Groq error).
  py_compile OK. Test thật gọi 1 lần A000004 (không force=1), ghi lại HTTP
  status + ok/done/missing_fields + số lần 429/retry từ log server.
---

## Triệu chứng

Groq giới hạn OTPM 1000 cho model `qwen/qwen3.8-27b`; route
`api_person_dila_translate` (nhánh Groq, app.py dòng ~22416-22449 tại HEAD
worktree) xin `max_tokens=4096` mỗi request nên khoảng 9/10 lần bị HTTP 429.
Route hiện tại gọi Groq ĐÚNG 1 LẦN — khi 429 thì `gd.get('choices')` rỗng,
log warning "no choices", `vi_text` vẫn `None` → rơi thẳng xuống fallback
Gemini (dòng ~22451-22473) dù Groq lẽ ra có thể thành công nếu thử lại sau
một khoảng chờ ngắn (đúng ý nghĩa rate-limit tạm thời, không phải lỗi cứng).

Log cảnh báo cho 2 case lỗi JSON (429/other, finish_reason != 'stop') đã
được thêm ở commit b811f623 (BUG-052 follow-up trước) — chỉ log, chưa có
retry.

## Root cause

- Nhánh gọi Groq trong `api_person_dila_translate` chỉ có 1 lần
  `requests.post(...)`, không có loop retry/backoff khi nhận 429 hoặc
  response thiếu `choices` hoặc `finish_reason` khác `'stop'`.
- Có sẵn pattern retry 429 tương tự ở hàm khác cùng file:
  `_t73_call_gemini` (tên hàm gây nhầm, thực ra gọi Groq) dòng ~21611-21689,
  dùng `_T73_429_MAX_RETRY = 2`, backoff `BASE * 2**attempt` cố định
  (0.5s/1s), KHÔNG đọc gợi ý thời gian thật từ response Groq.
- Route `dila_translate` cần đọc gợi ý thời gian thật (`Retry-After` header
  hoặc "try again in Xs" trong body lỗi) trước khi dùng backoff cố định, vì
  Groq OTPM reset theo giây cụ thể — đây là điểm khác với
  `_t73_call_gemini` nên không copy y nguyên hằng số của hàm đó.

## Phạm vi sửa

CHỈ trong `app.py`, nhánh gọi Groq của `api_person_dila_translate`
(khoảng dòng 22416-22449 tại HEAD worktree này). KHÔNG đổi:
- `max_tokens=4096`, `groq_model`, `GROQ_URL`, `timeout=35` của từng request.
- Luồng/điều kiện fallback Gemini (dòng ~22451-22473).
- 3 dòng log warning cũ (giữ nguyên text, có thể thêm log mới bên cạnh).

## Cách đếm "tối đa 3 lần"

1 lần gọi đầu + tối đa 2 lần gọi lại nếu lần trước thất bại theo điều kiện
retry (429 / không có choices / finish_reason != 'stop') — tổng tối đa 3
lần gọi `requests.post` tới Groq trong 1 request HTTP tới route này.
