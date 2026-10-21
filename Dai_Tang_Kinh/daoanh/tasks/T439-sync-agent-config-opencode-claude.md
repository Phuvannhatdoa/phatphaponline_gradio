---
id: T439
title: "Đồng bộ cấu hình agent .opencode theo .claude (settings/agents/skills)"
status: done
created: 2026-10-20
updated: 2026-10-20
owner: null
module: Dev Tooling / Agent Config
priority: medium
depends_on: []
dispatch: approved (Admin duyệt plan 2026-10-20, chọn phương án A — giữ 2 bản skill có banner đồng bộ)
plan_approved_at: "2026-10-20"
done_when: >
  (1) daoanh/.opencode có opencode.json mirror permission của .claude/settings.json
      (allow/ask/deny cùng quy tắc: git chỉ-đọc allow, git add/commit/reset ask,
      --apply/--revert ask, .env + config/ deny đọc, data/** deny edit).
  (2) 3 agent (daoanh-qa, daoanh-debugger, tich-hop) + 2 skill (daoanh-task,
      lineage-audit) có bản .opencode đúng định dạng (mode: subagent, SKILL.md
      trong thư mục riêng).
  (3) opencode debug config không lỗi; opencode debug skill load đúng
      lineage-audit từ daoanh/.opencode; agent list có đủ 3 agent.
  (4) .gitignore (root + daoanh) thêm negation để config được track.
  (5) Cả hai bản daoanh-task (.opencode + .claude) có banner cảnh báo đồng bộ.
  (6) Commit + ROLLBACK.md có lệnh revert.
---

# T439 — Đồng bộ cấu hình agent .opencode theo .claude

**Commit:** `15b03e21` (parent `a84c8d03`, branch `truyen-dang-the-pho-clean`, 2026-10-20)

## Bối cảnh

`daoanh/.claude/` có settings.json + launch.json chuẩn Claude Code (T439 trước đó
đã sửa), còn `daoanh/.opencode/` chỉ có 1 skill cũ + plugin tester, không có
opencode.json, không có agent. Admin yêu cầu mô phỏng .claude để update .opencode
cho đồng nhất 2 bên.

## Đã làm

1. **`daoanh/.opencode/opencode.json`** (mới): `permission` mirror settings.json —
   bash `*`: ask + allowlist (python/node/npm run/ls/cat/git chỉ-đọc...), ask cho
   `git add/commit/reset/checkout/restore/read-tree/update-index/push`, `--apply`,
   `--revert`, `--reset`, `ai_batch_transliterate*`; deny `git push --force`,
   `git clean`, `rm -rf`, `Remove-Item -Recurse`, `sqlite3 DROP/DELETE`;
   read deny `.env`, `config/**`; edit deny `data/**`, `.env*`.
   `instructions: ["CLAUDE.md"]` để opencode nạp cùng ngữ cảnh dự án với Claude.
2. **3 agent** (mới, `.opencode/agents/`): `daoanh-qa.md` (mode subagent, edit deny,
   bash chỉ py_compile/node --check/lineage tester/git chỉ-đọc/sqlite3 SELECT),
   `daoanh-debugger.md` (edit deny data/**), `tich-hop.md` (edit ask + docs/** allow).
   Frontmatter opencode: `mode: subagent` + `permission:`; bỏ `model:` Claude-specific.
3. **2 skill** (mới, `.opencode/skills/`): `daoanh-task/SKILL.md`,
   `lineage-audit/SKILL.md` (định dạng đúng: thư mục riêng + SKILL.md; bản
   `.claude/skills/lineage-audit.md` phẳng không đạt chuẩn).
4. **Banner đồng bộ** đầu 2 bản `daoanh-task` (bản chuẩn = .opencode; sửa phải
   sửa cả hai) — phương án A do Admin chọn.
5. **`.gitignore`**: root thêm negation cho 3 file json cấu hình (bị `*.json`
   nuốt); daoanh thêm `!.opencode/opencode.json`. Verify bằng `git add --dry-run`: 8/8 add được.
6. **launch.json** (sửa trước đó trong .claude): URL `127.0.0.1` (không localhost),
   thêm config `gateway` khởi động `local_gateway.py`.

## Verify (bằng chứng)

- `opencode --version` → 1.19.3.
- `opencode debug config` → parse OK, 0 lỗi; permission rules resolve đúng thứ tự.
- `opencode agent list` / `debug config` → có `daoanh-qa`, `daoanh-debugger`,
  `tich-hop` (subagent) với đúng permission.
- `opencode debug skill` → `lineage-audit` load từ
  `daoanh/.opencode/skills/lineage-audit/SKILL.md`; `daoanh-task` load từ bản
  `.claude` (external scan) — nội dung 2 bản giống nhau, có banner đồng bộ.
- JSON hợp lệ (python json.load) cho cả 2 file json.

## Lưu ý

- Skill `daoanh-task`: opencode quét skill ngoài và ưu tiên bản
  `Dai_Tang_Kinh/.claude/skills/` — 2 bản phải sửa đồng bộ (banner đã ghi).
- Agent không đặt `model:` (ID kiểu `claude-sonnet-5` không hợp lệ trong
  opencode dạng `provider/model`) → dùng model mặc định.
- `openrouter.md`, `opencode.md`, `harness.md` (cấp Dai_Tang_Kinh) không mirror.
- Cần restart opencode để nạp cấu hình mới.

## Revert

Xem `docs/ROLLBACK.md` dòng T439 — thuần git, không DB.
