---
id: T233
title: Cột Codex phiên âm Hán Việt DILA bằng phiên ChatGPT Codex
status: blocked
priority: high
created: 2026-10-04
updated: 2026-10-05
---

# T233 — Codex name_vi tham khảo

Admin yêu cầu cột Codex ngay sau DILA name_vi và chạy toàn bộ 48.673 ID vào DB để đối chiếu. Ngày 05/10 Admin xác nhận **không API trả phí, chỉ Codex/Claude Code Cloud Session**.

## Cấu trúc đã triển khai

Bảng codex_* riêng, lịch sử revision và ID/Hán/hash/model/prompt/CLI/session artifact provenance. Canonical names/Gemini/TTL/quan hệ/số đời không tự thay. Cột ở hai bảng và danh sách full corpus có phân trang. Runner dùng Codex CLI login ChatGPT, bắt auth chatgpt, loại API key env, read-only/schema output, tuần tự/OS lock/resume/pause, quota/lỗi không fallback trả phí. Admin API submit/collect trả409 paid disabled.

## Kết quả thực

Codex CLI0.159.2, Logged in using ChatGPT; gpt-6.1-sol chạy thật32+256 tên, nhập **288/48.673** tại mốc ban đầu (19 needs_review). Full run39836c390adf4e9993649eacca7a546c:48.641 còn lại/191nhóm, chạy nền tiếp sau nhóm0; tổng tiến độ đọc DB/log hiện tại. Chưa được ghi full DONE.

Unit26/26, UI/browser0pageerrors và pipeline.exit0; compliance còn2metricFAIL. Windows RunAs reloadmain bị hủy; CLI độc lập vẫn chạy, backend web cần nạp code mới rồi verify subscription status. Không lặp UAC. Mốc/count và trạng thái có thể đổi khi runner chạy, xem [report live](../docs/reports/T233-codex-session-20261005/README.md).

## Tiếp theo

1. Theo dõi quota/lỗi, resume phần chưa ingested; đối soát đủ48673ID/request/nguồn trước DONE.
2. Admin nạp main bằng quyền Windows, xác nhận paid_api_enabled=false và nút chạy/dừng.
3. Review quality/needs_review trước chuẩn hóa tên chính; không tự nhận fine-tune Phật học.
4. Hoàn tác theo run với guard row/revision, giữ dữ liệu session khác. [Handoff](../docs/Handoff-2026-10-05-T233-codex-session.md).

Cách Batch ngày04/10 là lịch sử, không còn hướng đang dùng: [report cũ](../docs/reports/T233-codex-namevi-20261004/README.md). Không yêu cầu OPENAI_API_KEY.

## Kiểm tra lại 2026-10-09 — chờ hạn mức Codex

DB hiện có **1.312/48.673 ID đã xử lý**, fulljob blocked_session. Group5/events.jsonl ghi usage_limit và try again Oct10th2026 10:21AM. Đây là thời gian theo log05/10, chưa xác nhận reset mới; Codex loginChatGPT hiện còn hợp lệ (CLI0.162.0-alpha.17.2). Ngày09/10 không gọi lại model, không API trả phí. Khi hạn mức cho phép mới resume request chưa nhập; còn47.361ID. [Bàn giao](../docs/Handoff-2026-10-09-A000662-distinct-closeout.md).
