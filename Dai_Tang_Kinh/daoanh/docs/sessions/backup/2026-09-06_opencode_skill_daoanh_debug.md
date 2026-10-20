# Session 2026-09-06 — OpenCode Skill + Agent Debug cho Đạo Ảnh (PTDA)

**Loại:** Dev-environment / tooling (không thuộc task board nào) — admin duyệt build 2026-09-06.

## Vấn đề
Mỗi bug trước đây phải gửi prompt dài (lặp lại toàn bộ quy tắc). Nhận thấy rule đã có sẵn
tại `docs/rules/` (4 file) và agent Claude `.claude/agents/daoanh-debugger.md` (170 dòng),
chưa có cơ chế tái sử dụng chuẩn cho OpenCode.

## Quyết định
- OpenCode chạy từ `daoanh/` → đặt `.opencode/` trong `daoanh/` (đã có sẵn thư mục chứa plugin tester).
- Skill dành riêng cho OpenCode, không đụng agent `.claude` hiện có.
- Nguồn DUY NHẤT của rule vẫn là `docs/rules/`; SKILL.md chỉ là lớp loader mỏng `bước 0 = đọc docs/rules/*`.
- Bỏ trường `skills:` trong agent frontmatter (OpenCode schema không hỗ trợ — field lạ bị route vào `options`).

## Files tạo / sửa

| File | Nội dung |
|------|----------|
| `.opencode/skills/daoanh-data-ui-debug/SKILL.md` | Skill mỏng: role, bước 0 đọc `docs/rules/*` theo chủ đề, rule cứng tóm tắt (kèm phân định LLM), workflow 5 bước, bug-report format ngắn, đầu ra 6 mục |
| `.opencode/agents/daoanh-debugger.md` | Agent `mode: primary`, mỏng — nhiệm vụ nạp skill + tuân thủ; KHÔNG có trường `skills:` |
| `docs/templates/audit-report.md` | Template báo cáo audit/fix (đang thiếu — agent `.claude` cũ tham chiếu nhưng file chưa tồn tại) |
| `docs/rules/data-integrity.md` | + mục "LLM keys (bảo mật — không commit)": `data/llm_config.json` gitignored, `_llm_config_read()`, rollback doc |
| `docs/rules/ui-evidence-rules.md` | + mục "LLM policy (phân định rõ)": CẤM suy diễn học thuật; CHO PHÉP pipeline dịch Groq→translation_segments (unreviewed, duyệt admin) |

## Sau này
- Bug mới chỉ cần prompt ngắn:
  ```
  Task: Fix tab Sự Kiện.
  Route/case: /daoanh/places · Thiếu Lâm Tự · PL000000023255.
  Bug: Header "55 sự kiện" nhưng card chỉ là CBETA mentions; không có action/time.
  Expected: - Phân loại event vs textual_mention từ schema thật. - Mention không đếm là event. ...
  Report: docs/EVENTS_TAB_SEMANTIC_FIX_REPORT.md
  ```
- SKILL.md tự nạp khi task khớp `description` (restart OpenCode sau khi tạo config).

## Ghi chú
- Cần **restart OpenCode** để skill/agent được nạp (config load 1 lần khi khởi động).
- Agent `.claude` cũ còn 2 điểm stale nội bộ (thời điểm key Gemini "app.py 1065/1105") —
  để nguyên theo quyết định "skill dành riêng cho opencode".