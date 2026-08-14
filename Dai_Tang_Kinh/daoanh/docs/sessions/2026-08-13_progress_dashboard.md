# Session 2026-08-13 — Dashboard Process Tracker (docs ↔ code)

**Task:** Xây dashboard đối chiếu tài liệu `docs/*.md` với code Python thật, tính % hoàn thành theo code.
**Plan chi tiết:** `dashboard/plan.md` · **Checklist:** `dashboard/tasks.md` · **Handoff:** `dashboard/handoff.md`

## Kết quả đã làm

1. **Tài liệu plan trong `dashboard/`** — README (entry point), plan, tasks, handoff. Để agent khác (Claude Code / opencode) đọc là tiếp tục được ngay.

2. **`scripts/build_progress_data.py`** — generator (Zero-RAM, không thư viện mới):
   - Parse **TOÀN BỘ `docs/*.md`** (kể cả thư mục con sessions/, bug-reports/, fix-logs/, contracts/) — scan động bằng `os.walk`, không hardcode danh sách file. Mọi .md là cấu trúc hệ thống đã thống nhất, claim nào docs nhắc tới đều tính là "chức năng cần có".
   - Trích claim endpoint (`/api/...`, `/daoanh/api/...`) + script (`` `xxx.py` ``), gán module qua quy tắc prefix (`CLAIM_MODULE_RULES`).
   - Scan code: `@app.route` trong app.py/server.py/api_ttl_rebuild.py/conflict_server.py; script trong scripts/, src_python/, src/python/.
   - Đối chiếu claim vs code → `progress% = code_found/code_claimed`, status `done/in_progress/pending`, warnings khi thiếu.
   - Chuẩn hóa path: bỏ prefix `/daoanh`, thay placeholder `<id>`/`{id}`/ID thật (PL...) → `{}`.
   - Output `data/progress_data.json`: `{generated_at, total_progress, modules[], endpoints_compare[]}`.

3. **Route mới `app.py`**: `GET /daoanh/api/progress/dashboard` — serve JSON; tự chạy script nếu thiếu; `?regenerate=1` ép regenerate. Fix `sys` → `_sys` (app.py chỉ import `sys as _sys`).

4. **`dashboard/dashboard_process.html`** — UI tĩnh (theme #d97706/#020617, Inter + Noto Serif TC):
   - Header + nút Refresh + timestamp.
   - Summary bar: tổng %, số module, route thật, script thật, endpoint đối chiếu.
   - Module cards: progress bar màu theo trạng thái, badge, chips route, warnings đỏ.
   - Bảng endpoints: docs claim ✓/✗ vs code thật (bắt được 404 `/daoanh/api/admin/dashboard/stats`).
   - Auto-refresh 60 phút, fetch có AbortController timeout 60s.

5. **E2E**: thêm `dashboard/dashboard_process.html` vào `scripts/e2e-test.js`.

## Kết quả verify

| Kiểm tra | Kết quả |
|----------|---------|
| `python scripts/build_progress_data.py` | OK — 12 module, 45% tổng, 39 endpoints, JSON hợp lệ |
| Route API (test port 5010) | 200, `?regenerate=1` → 200 (regenerated=True) |
| Static HTML qua gateway 8080 | 200 (len 14151) |
| `node scripts/e2e-test.js` | PASS (cả dashboard_process.html) |
| `node --check` inline JS dashboard | OK |

## Vướng mắc / cần làm tiếp

- **Port 5000 bị tiến trình cũ giữ**: PID 13576 (elevated, code cũ) vẫn giữ port 5000 → request vào route mới trả 404. Cần restart app.py bằng quyền admin (hoặc `taskkill /F /PID 13576` ở terminal admin) rồi chạy lại `python app.py`.
- `npm run lint` cần bash (WSL chưa cài trên máy này) → đã chạy e2e + `node --check` thay thế; trên VPS/CI có thể chạy pipeline đầy đủ.
- Chưa commit (chờ admin restart server + xác nhận).

## File tạo/sửa

| File | Loại |
|------|------|
| `dashboard/README.md`, `plan.md`, `tasks.md`, `handoff.md` | mới |
| `dashboard/dashboard_process.html` | mới |
| `scripts/build_progress_data.py` | mới |
| `data/progress_data.json` | auto-gen |
| `app.py` | sửa (+route progress dashboard, fix `_sys`) |
| `scripts/e2e-test.js` | sửa (thêm dashboard page) |
| `docs/progress.md` | sửa (section Dashboard) |
| `docs/sessions/2026-08-13_progress_dashboard.md` | mới (file này) |

## Cập nhật 2026-08-13 (PM): scan toàn bộ .md

- Yêu cầu admin: KHÔNG bỏ .md nào khỏi tính toán — mọi .md là cấu trúc hệ thống đã thống nhất. Roadmap thêm chức năng 2028 thì % hạ là đúng (code chưa theo kịp).
- Đổi DOCS_FILES: hardcode 6 file → scan động os.walk toàn bộ docs/ (sessions/, bug-reports/, fix-logs/, contracts/...).
- Kết quả: 12 module, 80 endpoints (41 found / 39 missing), tổng 65% (trước: 39 endpoints, 49%).
- Lưu ý: % là cơ chế động — cập nhật .md sẽ lập tức thay đổi claim và %.
- E2E PASS, API total=65%.

## Cập nhật (tối 2026-08-13): Task Board theo chuẩn Claude Code

- Yêu cầu admin: đề xuất thêm cấu trúc quản lý tiến độ chức năng cần dev theo chuẩn Claude Code, admin nhìn rõ tình hình trên dashboard.
- **Thêm `tasks/`** — 1 file = 1 chức năng (`tasks/T<id>-<slug>.md`, frontmatter YAML: id/title/module/priority/status/depends_on/created/updated/done_when + acceptance criteria checklist). Quy ước đầy đủ: `tasks/README.md`.
- **Thêm mục "Task tracking" vào `CLAUDE.md`** — agent bắt buộc cập nhật status (pending/in_progress/blocked/done) sau mỗi chức năng.
- **`build_progress_data.py`**: thêm `scan_tasks()` (parse frontmatter + đếm checkbox acceptance criteria) → output `tasks[]` + `task_meta` (done_percent, blocked_tasks...).
- **`dashboard_process.html`**: thêm Task Board — KPI (done %, tổng, đang làm, blocked) + 4 cột Kanban (Pending/In-progress/Blocked/Done), mỗi card hiện module, priority, depends_on, done_when, thanh tiến độ tiêu chí. Blocked hiện viền đỏ.
- **Seed:** `tasks/T09-dashboard-stats-api.md` (từ tasktodo.md #9). Giữ nguyên `docs/tasktodo.md`.
- **Quy tắc ghi nhớ:** không dùng PowerShell `Add-Content` cho file UTF-8 tiếng Việt (gây hỏng encoding) — dùng tool Write/Edit.
- Kết quả verify: script 65%, 1 task (T09 pending 0/4) · API `?regenerate=1` 200 có tasks[] · E2E PASS · JS syntax OK.

## Cập nhật (khuya 2026-08-13): Tasks trong module card + Git Timeline

- Yêu cầu admin: (1) mỗi card module hiển thị task chưa Done + mô tả chức năng để hình dung; (2) scan git commit (claudecode tạo sau mỗi update code) để tính Timeline.
- **`build_progress_data.py`**:
  - `scan_tasks()`: thêm `desc` (trích section "## Mục tiêu" hoặc khối sau frontmatter).
  - Mới `scan_git_history()`: chạy `git log` từ git root `visjs-app/` (path `Dai_Tang_Kinh/daoanh`) → đếm commit theo module (keyword MODULES) + theo tháng → `git_history{total, first_date, last_date, by_module{}, by_month[], unmatched}`.
  - Kết quả: **473 commits** (2026-04-07 → 2026-08-13); GIS/Places 68, DILA Authority 63, CBETA 35, TTL 33, Hạ tầng 33, Translation 17; unmatched 167 (commit chung/không rõ module).
- **`dashboard_process.html`**:
  - Mỗi **module card**: thêm block "Tasks chưa Done" — list task (id, title, priority, status, desc mô tả chức năng), blocked hiện viền đỏ.
  - Section mới **Git Timeline**: bar chart commits theo tháng + commits theo module (thanh ngang) + stats (total, range, unmatched).
  - Lưu ý: tasks/ mới có 1 task (T09) nên các module khác hiện "Không có task đang mở" — tạo thêm file `tasks/T*.md` là dashboard hiện ngay.
- Verify: script 65% + 473 commits · API `?regenerate=1` 200 có git_history · E2E PASS · JS OK · HTML 8080 200 (28735 bytes).
