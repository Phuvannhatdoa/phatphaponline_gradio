# Session 2026-10-25 — T462 Harness: coder/tester/debug loop

## Admin phê chuẩn
- Claude Code: QA + tạo task, viết tiêu chí DONE và nội dung test; gọi `daoanh-debugger` khi có bug.
- OpenCode GO: code, báo DONE. Chuỗi: `mimo-v2.5` → OpenCode free còn quota → OpenRouter FREE `nvidia/nemotron-3-ultra-550b-a55b:free`.
- OpenRouter FREE `nvidia/nemotron-3.5-lightning:free`: tester (model khác coder để trung lập).
- Mọi model OpenRouter phải là bản `:free`.
- Vòng lặp test → bug → debug → test lại đến DONE, rồi Admin verify.

## Đã làm
- Chọn ID: T80 đã có file, T81 bị nhắc trong tasktodo, T82/T83/T85 cũng được nhắc. Max đang dùng là T461, nên cấp **T462**.
- Tạo `tasks/T462-harness-coder-tester-loop.md`.
- Cập nhật `docs/tasktodo.md` (block T462 đặt trên T461).
- Sao lưu `docs/tasktodo.md` trước khi sửa: `docs/sessions/2026-10-25/T462/tasktodo.before.md`.
- Cập nhật `.claude/agents/opencode.md` (model `mimo-v2.5`, fallback chain) và `.claude/agents/openrouter.md` (vai trò tester).
- Chạy `scripts/build_progress_data.py`: 193 task trên board; `--check-dup-ids` không có trùng thật.
- Kiểm dashboard: T462 và T445 hiển thị.

## Kiểm tra gọi API (không ghi key ra)
| Model | Kết quả |
|---|---|
| OpenRouter `nvidia/nemotron-3.5-lightning:free` | HTTP 200 |
| OpenRouter `nvidia/nemotron-3-ultra-550b-a55b:free` | HTTP 200 |
| OpenRouter `nvidia/nemotron-3-nano-30b-a3b:free` | HTTP 404 (không còn free) |
| OpenCode GO `mimo-v2.5` | HTTP 429 (hết quota tuần) |
| OpenCode free `big-pickle` | `FreeUsageLimitError` |
| OpenCode GO `deepseek-v4-flash` | không có trong danh sách |

## Chưa làm
- Chưa code T445. Chưa commit. Chưa thay đổi DB, không cần backup DB.
- Chưa xác nhận `opencode` gọi được khi GO còn quota.
- Phiên hiện tại có thể đang cache định nghĩa agent cũ: cần phiên mới để nạp.
