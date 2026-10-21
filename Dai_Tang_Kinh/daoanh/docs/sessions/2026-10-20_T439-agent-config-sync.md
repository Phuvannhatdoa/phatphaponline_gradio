# Session Log 2026-10-20 — T439 Đồng bộ cấu hình agent .opencode theo .claude

## Thông tin nhanh

- **Task:** `tasks/T439-sync-agent-config-opencode-claude.md` (status: done)
- **Phạm vi:** chỉ config/docs — **0 thay đổi DB, 0 code app.py**
- **Admin duyệt:** phương án A (giữ 2 bản skill `daoanh-task` + banner đồng bộ)

## Đã làm (thứ tự thực hiện)

1. Sửa `daoanh/.claude/settings.json` — cú pháp chuẩn Claude Code, `$schema`, git chuyển deny→ask, thêm ask cho `--apply/--revert/--reset/ai_batch_transliterate*`, deny đọc `.env`/`config/`, deny edit `data/**`.
2. Sửa `daoanh/.claude/launch.json` — URL `127.0.0.1` (CLAUDE.md cấm localhost), thêm config `gateway` (local_gateway.py, port 8080).
3. Tạo `daoanh/.opencode/opencode.json` — mirror permission (bash/read/edit/glob/grep), `instructions: ["CLAUDE.md"]`.
4. Tạo 3 agent `.opencode/agents/`: `daoanh-qa.md` (edit deny), `daoanh-debugger.md` (data/** deny), `tich-hop.md` (docs/** allow) — thân file copy nguyên từ `Dai_Tang_Kinh/.claude/agents/`, frontmatter đổi sang opencode (`mode: subagent`, `permission:`; bỏ `model:` Claude-specific, bỏ `tools:`).
5. Tạo 2 skill `.opencode/skills/`: `daoanh-task/SKILL.md`, `lineage-audit/SKILL.md` (định dạng đúng — bản `.claude/skills/lineage-audit.md` phẳng không đạt chuẩn).
6. Banner đồng bộ đầu 2 bản `daoanh-task` (phương án A).
7. `.gitignore`: root thêm negation 3 json config (bị `*.json` nuốt); daoanh thêm `!.opencode/opencode.json`.
8. Verify + commit (SHA thấy trong `git log --oneline -3`).

## Bằng chứng verify

```
opencode --version        → 1.19.3
opencode debug config     → parse OK, 0 lỗi ConfigInvalid
opencode agent list       → có daoanh-qa, daoanh-debugger, tich-hop (subagent)
opencode debug skill      → lineage-audit load từ daoanh/.opencode/skills/lineage-audit/SKILL.md
git add --dry-run         → 8/8 file cấu hình không bị ignore
```

## Phát hiện quan trọng

- Root `.gitignore` dòng `*.json` đang nuốt **mọi** json — gồm cả `.claude/settings.json`, `launch.json` → trước T439 không file cấu hình nào được track.
- opencode nạp skill `daoanh-task` từ `Dai_Tang_Kinh/.claude/skills/` (external scan) chứ không từ bản `.opencode` → 2 bản phải sửa đồng bộ (đã thêm banner).
- Quy tắc permission opencode: **rule khớp CUỐI cùng thắng** → deny/ask phải đặt SAU allow trong object.

## Bài học / sai lầm tránh lặp

- `git check-ignore -v` in cả pattern phủ định `!...` với rc=0 — **không** dùng rc để đoán ignored; dùng `git add --dry-run` mới chắc chắn.
- PowerShell 5.1: `opencode ...` qua shim in stderr noise (NativeCommandError) — output vẫn dùng được, đừng hoảng.

## Chưa xong / cần Admin

- Skill `lineage-audit.md` phẳng ở `Dai_Tang_Kinh/.claude/skills/` — nên chuyển thành thư mục `lineage-audit/SKILL.md` cho chuẩn Claude Code (không thuộc phạm vi T439).
- `visjs-app/.claude/settings.local.json` (cấp root) chứa nhiều permission tạm một lần — nên dọn.
- Model ID `claude-sonnet-5` trong agent `.claude` chưa xác minh — cân nhắc đổi sang alias `sonnet`.

## Revert

`git revert <sha>` — thuần git, không DB. Xem `docs/ROLLBACK.md` mục T439.
