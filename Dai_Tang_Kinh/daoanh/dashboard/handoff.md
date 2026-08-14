# HANDOFF — Session Continuation

> **Đọc trước khi bắt đầu.** Mục tiêu: agent kế tiếp (Claude Code / opencode) tiếp tục công việc KHÔNG gián đoạn, không phải đoán.
> Quy tắc: sau mỗi task → cập nhật mục này (5 dòng) + tick `tasks.md`.

## Trạng thái hiện tại (2026-08-13)

- **Đang ở bước:** 6 — docs + commit. Xong hết. Dashboard hoạt động. Đã thêm **Task Board** (chuẩn Claude Code) + **seed 17 task** + **docs chuẩn GitBook** (SUMMARY.md + README + README thư mục con).
- **Đã làm:**
  1. 4 file tài liệu `dashboard/` (README, plan, tasks, handoff).
  2. `scripts/build_progress_data.py` — parse docs/*.md (headers/✅⏳❌/claims path+script) + scan code (route app.py/server/api_ttl_rebuild/conflict_server; scripts; src_python; src/python) → `data/progress_data.json`. Scan **toàn bộ** docs/ bằng os.walk (gồm sessions/, bug-reports/, fix-logs/, contracts/). Hiện: 12 module, 80 endpoints (41 found / 39 missing), 65%.
  3. Route mới `GET /daoanh/api/progress/dashboard` trong app.py (serve JSON, `?regenerate=1` chạy lại script). Đã fix `sys` → `_sys` (app.py import `sys as _sys`). Thêm route tĩnh `/dashboard/` + `/daoanh/dashboard/` (fix 404 khi mở thẳng :5000).
  4. `dashboard/dashboard_process.html` — UI tĩnh (theme #d97706/#020617), fetch JSON, module cards + bảng endpoints, Refresh + auto 60 phút, **Task Board** (KPI + Kanban pending/in_progress/blocked/done). Đã thêm vào e2e-test.js.
  5. **Task tracking mới (chuẩn Claude Code):** thư mục `tasks/` — 1 file = 1 chức năng (`tasks/T<id>-<slug>.md`, frontmatter YAML + acceptance criteria). Quy ước: `tasks/README.md` + mục "Task tracking" trong `CLAUDE.md`. `build_progress_data.py` parse → `data.progress_data.json` thêm `tasks[]` + `task_meta`. Seed: **17 task T01–T17** (tasktodo T1–T8 + T09 cũ + Khoá 4 DILA Place Index + Khoá 6 RAG + Khoá 7 Dịch Mượt + DEV_HISTORY Time Authority/Nexus/KG Viz + progress GIS cluster).
  5b. **Docs chuẩn GitBook:** `docs/SUMMARY.md` (mục lục), `docs/README.md` (entry), `docs/{bug-reports,fix-logs,sessions}/README.md` (index thư mục con).
  5c. **GitBook thật (Honkit):** book root = `daoanh/` (`book.json`, `README.md`, `SUMMARY.md`, `styles/website.css` dark theme). Chạy `npm run docs:serve` → `http://localhost:4000`. `npm run docs:build` → `_book/`. Honkit copy toàn cây trừ `.gitignore` → đã loại `data/ .opencode/ ontology/...` (build trước 180s+ timeout → giờ 30s). File tên có space bị honkit bỏ → đã rename `update contract_opencode.md` → `update_contract_opencode.md`. **Auto-update 12:00 hằng ngày** qua Task Scheduler `GitBook_DailyUpdate_1200` (script `scripts/gitbook_daily_update.ps1`, log `%TEMP%\gitbook_daily_update.log`).
  6. **Restart server xong**: app.py chạy lại với route mới.
- **Bước kế tiếp:** Xem dashboard: `http://localhost:8080/dashboard/dashboard_process.html` → Refresh (17 task). Xem GitBook: `http://localhost:4000` (đang serve). Dev theo thứ tự ưu tiên: **T09 → T01 → T02 → T14** (xem DEV_HISTORY §đề xuất). Mỗi task → tick acceptance + đổi status → Refresh dashboard. Commit nhỏ cho tasks/docs.
- **Lệnh verify:** `python scripts/build_progress_data.py` (OK, 65%, 17 task, 474 commits) · `GET http://localhost:5000/daoanh/api/progress/dashboard?regenerate=1` (200, tasks[]) · qua gateway 8080 (200) · `node scripts/e2e-test.js` (PASS) · `npm run docs:build` (20 pages) · `npm run docs:serve` (http://localhost:4000, mọi link 200).
- **Ghi chú:** `npm run lint` cần bash (WSL chưa cài) → trên Windows dùng e2e + `node --check` thay thế. `fix_all.py` không chạy. data/progress_data.json auto-gen (gitignored). Không dùng Add-Content trong PowerShell để ghi file UTF-8 tiếng Việt (gây hỏng encoding) — dùng tool Write/Edit.

## Log phiên

| Ngày | Task | Nội dung |
|------|------|----------|
| 2026-08-13 | T1–T4 | Tạo 4 file tài liệu plan trong `dashboard/` |
| 2026-08-13 | T5–T9 | Script `build_progress_data.py` + JSON hợp lệ (45%, 12 module) |
| 2026-08-13 | T10–T11 | Route `/daoanh/api/progress/dashboard` + test 5010 (200, regenerate OK) |
| 2026-08-13 | T12–T15 | `dashboard_process.html` hoàn tất + thêm vào e2e-test.js |
| 2026-08-13 | T16–T17 | Verify API 200 + static 8080 200 + E2E PASS |
| 2026-08-13 | T17b | Restart app.py (kill PID 13576) → API 5000 + gateway 8080 + regenerate đều OK (49%) |
| 2026-08-13 | T18–T20 | Session doc + progress.md + tasks/handoff cập nhật |
| 2026-08-13 | T21–T22 | ⏳ Pipeline đầy đủ cần bash (đã chạy e2e thay thế); commit `5cfb47e` xong |
| 2026-08-13 | TB1 | Task Board: tạo `tasks/` (README + T09 seed) + quy ước trong CLAUDE.md; build_progress_data.py parse tasks → `tasks[]`+`task_meta`; UI Kanban (KPI + 4 cột); e2e PASS; API 65% / 1 task |
| 2026-08-13 | TB2 | Module card hiển thị "Tasks chưa Done" + desc; Git Timeline (473 commits, by_month + by_module); scan_git_history() trong build_progress_data.py |
| 2026-08-13 | TB3 | Seed 17 task T01–T17 (tasktodo+roadmap Khoá 4/6/7+DEV_HISTORY audit+progress) vào `tasks/`; docs chuẩn GitBook: SUMMARY.md + README (docs + bug-reports/fix-logs/sessions); registry trong tasks/README; verify 65%/17 task/474 commits + API 200 + E2E PASS |
| 2026-08-13 | GB1 | **GitBook thật (Honkit)**: cài honkit v6.2.2; book root = daoanh/ (book.json + README.md + SUMMARY.md + styles/website.css dark theme); .gitignore loại node_modules/data/.opencode/... (fix build timeout); rename `update contract_opencode.md`→`update_contract_opencode.md` (honkit bỏ file tên có space); npm scripts docs:serve (port 4000) + docs:build; verify 20 pages / 112 assets / mọi link 200 |
| 2026-08-14 | T09 | **Dashboard stats API fix** — thêm alias route `/api/admin/dashboard/stats` + `/daoanh/api/admin/dashboard/stats` vào `api_dashboard_stats()` (app.py:6057); 5/5 path 200 qua :5000 & :8080; restart toàn stack (5000/5001/8080); session log `2026-08-14_t09_dashboard_stats_api.md`; tasktodo #9 ✅; tasks/T09 done |
| 2026-08-13 | GB2 | **Auto-update 12:00 hằng ngày**: Task Scheduler `GitBook_DailyUpdate_1200` → `scripts/gitbook_daily_update.ps1` (ASCII-only vì PS5.1 cp1252); port 4000 sống→watch tự rebuild, chết→build+restart; log `%TEMP%\gitbook_daily_update.log`; Start-ScheduledTask test OK (LastTaskResult=0) |
