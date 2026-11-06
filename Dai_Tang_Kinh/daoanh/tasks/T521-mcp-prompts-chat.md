---
id: T521
title: Tích hợp MCP prompts.chat cho dự án (không cần key)
module: Harness
priority: low
status: pending
depends_on: []
created: 2026-11-06
updated: 2026-11-06
done_when: File .mcp.json tại Dai_Tang_Kinh khai báo server prompts-chat (HTTP, https://prompts.chat/api/mcp); /mcp trong Claude Code hiện trạng thái kết nối
---

# T521 — Tích hợp MCP prompts.chat cho dự án

## Mục tiêu
Gắn MCP server prompts.chat vào dự án để dùng prompt công khai từ Claude Code.

## Cách làm
- File `Dai_Tang_Kinh/.mcp.json` khai báo `prompts-chat` với `type: http`, `url: https://prompts.chat/api/mcp`. Không có key.
- `.gitignore` có ngoại lệ `!Dai_Tang_Kinh/.mcp.json` để commit được.
- Key chỉ dùng khi cần lưu prompt. Không ghi key vào file này.

## Acceptance criteria (checklist)
- [ ] `.mcp.json` có server `prompts-chat` đúng URL
- [ ] `.gitignore` có ngoại lệ cho `.mcp.json`
- [ ] `/mcp` trong Claude Code hiện prompts-chat đã kết nối
