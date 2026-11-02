@AGENTS.md

# Đạo Ảnh — Claude Code Project Context

> **SSOT workflow/commit/handoff/ID rules:** xem `AGENTS.md` (cùng thư mục) — mọi quy tắc làm việc, commit, revert, handoff, cấp ID đều nằm ở đó. File này chỉ giữ bối cảnh nhanh của dự án Đạo Ảnh; không lặp lại quy tắc.

## Bắt đầu session (đọc trước khi làm)

1. `docs/tasktodo.md` — trạng thái task mới nhất (block có ngày gần nhất).
2. `docs/Handoff-*.md` — file bàn giao có ngày mới nhất.
3. `docs/integration/REALITY_CHECK.md` — số liệu DB/code thực tế.
4. Nếu có việc đang dở: task file trong `tasks/` và `docs/ROLLBACK.md`.

Không tự tạo lại schema/SQL từ đầu khi các file trên đã có.

## Kiến trúc server

| File | Port | Vai trò |
|------|------|---------|
| `app.py` | 5000 | Main app — 131+ routes, business logic |
| `server.py` | 5001 | Auth gateway |
| `local_gateway.py` | 8080 | Static files + reverse proxy (local only) |

VPS dùng nginx thật; `local_gateway.py` chỉ dùng local dev.

## Khởi động local

```powershell
# Chạy từ thư mục daoanh/
python server.py > server_local.log 2>&1
python app.py    > app_local.log    2>&1
python local_gateway.py > gateway_local.log 2>&1
```

Kiểm tra port: `Get-NetTCPConnection -LocalPort 5000,5001,8080 -State Listen | Select LocalPort`

Nếu nhiều process trùng port → kill hết trước khi restart: `Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object CommandLine -like '*app.py*'`

**QUAN TRỌNG — Test local dùng IP thay vì hostname:**  
Luôn dùng `http://127.0.0.1:8080/daoanh/...` (IPv4), KHÔNG dùng `http://localhost:8080/daoanh/...`.  
Lý do: Windows resolve `localhost` → `::1` (IPv6) trước `127.0.0.1`, có thể hit process khác cùng port 8080 (ví dụ ZenQ server Node.js bind `[::]:8080`).

## Database

`data/lineage.db` — SQLite 1.4GB, 156 tables. Không có ORM — query trực tiếp SQLite.  
Số liệu thực tế (đo 2026-10-02): 313 routes, 14 nguồn trong `data_sources`, 447K claims.  
Nguồn sự thật: `docs/integration/REALITY_CHECK.md`.

## Git — KHÔNG tự ý chạy

Repo root là `visjs-app` (2 cấp trên `daoanh/`).  
Git index có anomaly (mass staged-deletion). **Không chạy `git add/commit/reset`** khi chưa có lệnh rõ ràng từ user.

## API keys

Lưu trong `.env` (không commit). `app.py` load tự động qua `python-dotenv`.

```
GEMINI_API_KEY=...   # rotate tại console.cloud.google.com nếu key cũ lộ
ANTHROPIC_KEY=...
```

**Sau khi đổi key:** chỉ cần sửa `.env`, không cần sửa code.

## ZQ — nguồn tên tiếng Việt

Mọi tên Việt trong DB đều do ZQ tạo (phiên âm tự động, confidence 0.5), không phải từ DILA/CBETA/MARCUS.  
**Quy tắc code bắt buộc:** `entity_claims.source_id`: DILA=1 (tên Hán), ZQLOCAL=5 (tên Việt).  
UI phải badge rõ nguồn. KHÔNG gán tên Việt của ZQ cho nguồn DILA.

## Task tracking

File task: `tasks/T<id>-<slug>.md` (YAML frontmatter: id/title/status/...).  
Status: `pending | in_progress | blocked | deferred | done`.
`deferred` = Admin hoãn có chủ đích, không tính là việc đang treo.  
Sau thay đổi chạy: `python scripts/build_progress_data.py`

## Permissions

Được phép tự chạy command trong project mà không hỏi từng lần.  
Vẫn cần xác nhận: force push, xóa data lớn, thay đổi schema DB, deploy VPS.

## Backup trước khi sửa code

Copy file vào `docs/sessions/YYYY-MM-DD/` trước khi edit.

## Harness: Đạo Ảnh

**Mục tiêu:** Điều phối bug, task và kiểm chứng trong dự án Đạo Ảnh theo quy trình có xác nhận của admin.

**Hồ sơ agent/skill** (nằm trong `Dai_Tang_Kinh/.claude/`):
- `daoanh-task` (skill điều phối): dùng khi sửa bug, thêm tính năng, xử lý task trong `tasks/`.
- `daoanh-debugger` (agent): sửa bug data/UI theo phạm vi đã ghi trong file task.
- `daoanh-qa` (agent, chỉ đọc): kiểm chứng sau khi sửa, trước khi hỏi admin xác nhận DONE.
- `tich-hop` (agent): tích hợp nguồn dữ liệu mới.
- `lineage-audit` (skill): kiểm tra logic truyền thừa.

**Khi nào dùng:** mọi yêu cầu sửa bug hoặc task trong dự án này. Câu hỏi thuần túy thì trả lời trực tiếp.

**Quy trình chuẩn:** `docs/process/HARNESS_WORKFLOW.md` (đề xuất → Admin duyệt → sao lưu → agent làm → QA → Admin xác nhận DONE). Đọc file này trước khi bắt đầu bất kỳ việc nào có ghi file hoặc DB.

**Vai trò của Claude khi có harness:** điều phối. Giao việc cho agent đúng vai (`daoanh-debugger` sửa, `tich-hop` tích hợp nguồn), để `daoanh-qa` kiểm chứng độc lập (chỉ đọc). Claude tự làm chỉ khi lập kế hoạch, trình Admin duyệt, ghi tài liệu, hoặc việc quá nhỏ không đáng giao (nói rõ lý do).

**Lịch sử thay đổi harness:**
| Ngày | Thay đổi | Đối tượng | Lý do |
|---|---|---|---|
| 2026-10-08 | Thêm agent `daoanh-qa` và skill `daoanh-task`, thêm mục này | `.claude/agents/daoanh-qa.md`, `.claude/skills/daoanh-task/` | Chưa có bước kiểm chứng và điều phối thống nhất trước khi đóng task |

## VPS

IP: `158.220.106.183` · Path: `/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/`

**Quy tắc (Admin chốt 2026-11-01):** local là bản chính. Mọi code, check và dev đều làm trên local (Claude Code, OpenCode). **Không sửa trực tiếp trên VPS** — VPS chỉ nhận code từ local qua `sync_daoanh.ps1` (17:00 hằng ngày). Agent không được chạy ssh/scp/rclone để ghi lên VPS.
