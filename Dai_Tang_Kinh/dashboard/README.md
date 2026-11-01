# DILA Team — Agent Dashboard

Dashboard web đọc **trực tiếp** các file Markdown trong `tasks/` (mỗi file = 1 task).

**Không** gọi Claude Code, **không** gọi OpenCode, **không** chạy agent, **không** tự sinh progress,
**không** có `state/agents.json`. Mọi số liệu hiển thị đều lấy nguyên văn từ file task.

---

## 1. Chạy dashboard

```bash
# từ thư mục dự án (thư mục chứa dashboard/ và tasks/)
python dashboard/serve.py --port 8090
```

Mở: **http://127.0.0.1:8090/dashboard/agent_team.html**

`serve.py` là static server tối giản (Python stdlib) + **1 endpoint duy nhất** để Approve/Reject ghi
đúng dòng `## Status` của file task. Không có backend nghiệp vụ, không DB, không state.

> **Không mở bằng double-click** (`file://…`) — trình duyệt chặn `fetch` đọc `/tasks/` nên dashboard
> sẽ hiện cảnh báo và mọi số = 0. Luôn mở qua `http://127.0.0.1:8090/...` như trên.

Chế độ chỉ-đọc (không cần `serve.py`) — Approve/Reject sẽ tải file `.md` đã sửa về thay vì ghi trực tiếp:

```bash
python -m http.server 8090
# rồi mở http://127.0.0.1:8090/dashboard/agent_team.html
```

> Nếu port 8080 đang bận (ví dụ app Đạo Ảnh), dùng `--port 8090` như trên.
> Dashboard tự nhận chế độ: badge **admin write: ON** (có `serve.py`) hoặc **read-only**.

---

## 1b. 3 nguồn dữ liệu THẬT (tab trên dashboard)

Dashboard có 3 tab, tất cả đều đọc file thật trên đĩa — không có dữ liệu mẫu ngầm:

| Tab | Đọc từ | Hiển thị | Ghi được |
|---|---|---|---|
| **DILA tasks** | `tasks/` | card đầy đủ: overall progress, 3 progress bar agent, stepper DILA, AC, blockers | ✅ Approve/Reject (đúng dòng `## Status`) |
| **Task thật** | `daoanh/tasks/` (194 file) | card task thật: `id`, `title`, `status`, `module`, `priority`, AC checklist, `updated` — **mới nhất trước (T462 → T11), hiện đủ 194 file** | ✅ **đổi status ngay trên card** (ghi `status:` trong frontmatter) |
| **Docs thật** | `daoanh/docs/` (183 file) | card tài liệu: tiêu đề thật + trích đoạn đầu + dung lượng + ngày sửa + link mở file | ❌ chỉ đọc |

### Search + lọc + đổi status cùng 1 page

Không có trang phụ — tất cả nằm trên 1 trang (thanh công cụ ngay dưới tab nguồn):

- **Ô tìm**: khớp mã task (`T461`), tiêu đề, tên file, module, status.
- **Select lọc status**: danh sách status thật kèm số lượng (`blocked (28)`, `in_progress (46)`…), dựng từ dữ liệu đang đọc.
- **Xoá lọc**: trả về toàn bộ.
- **Đổi status trên card** (tab Task thật): select `pending / in_progress / **debugging** / blocked / done / deferred / partial / superseded / cancelled / qa / review`
  → `POST /api/real-task-status` ghi đúng 1 dòng `status:` trong frontmatter, các dòng khác giữ nguyên byte-for-byte.
- **Editor ghi chú Admin trên từng card** (cả task DILA và task thật, không áp cho docs):
  bấm **✎ Ghi chú Admin** → nhập mô tả bug/hướng xử lý → **Lưu ghi chú**
  → `POST /api/task-note` **append** 1 dòng vào section `## Admin Notes` của đúng file, dạng
  `- [yyyy-mm-dd hh:mm] nội dung`. Nội dung cũ **không bị sửa**, mỗi lần lưu thêm 1 dòng (audit trail);
  note cũ hiển thị lại trong panel "Admin notes" của card.
  Ví dụ dùng: BUG-025 → ghi note "click lần 2 vẫn mất marker, tái hiện Chrome 138" → chuyển status `debugging` → khi xong chuyển `done`.
- Lọc/đếm **không gọi lại server** (lọc tại chỗ trên dữ liệu đã đọc); chỉ khi bấm ⟳ hoặc đổi status mới đọc lại file.
- Dòng `statsNote` báo `đang lọc: 12/194 card` để không nhầm với tổng thật.

### Admin xác nhận DONE → build progress + Tiểu Thiên báo Done

Khi Admin đổi status task thật sang **`done`** (chỉ đúng hành động này), server tự chạy 2 bước:

1. `python scripts/build_progress_data.py` (cwd `daoanh/`)
2. `powershell -ExecutionPolicy Bypass -File scripts/notify_done.ps1 -Title "T<id> Done" -Message "<mô tả ngắn>"`

- `<id>` = `id:` trong frontmatter (`T22` → `-Title "T22 Done"`), `-Message` = `title:` cắt còn ~150 ký tự.
- **Không** truyền `-Image` / `-NoSound` — script tự chọn ảnh Tiểu Thiên ngẫu nhiên trong
  `daoanh/static/notify/` và phát "ting ting" 3 lần.
- **Không gọi** khi: status không phải `done`, task đã `done` từ trước, hoặc Admin đang đổi sang
  trạng thái khác (`blocked`, `debugging`, `pending`…), hoặc task chưa được Admin xác nhận.
- Build mất ~40-90s → chạy **nền**, UI trả về ngay; kết quả xem qua `GET /api/notify-done/last`
  (dashboard tự poll và báo toast khi xong).
- Gọi lại thủ công/kiểm tra: `POST /api/notify-done {"id":"T22","title":"..."}`;
  thêm `"dry": true` để chỉ xem lệnh, `"skipNotify": true` để chỉ chạy build.

### Chip Cate — gom task theo trạng thái

Hàng chip dưới toolbar (bấm là lọc ngay, không gọi server):

| Chip | Gom các status |
|---|---|
| 💻 Coding | `in_progress`, `coding` |
| 🧪 Testing | `testing`, `retesting`, `qa`, `review` |
| 🐞 Debugging | `debugging`, `bug_found` |
| ⛔ Blocked | `blocked` |
| 📋 Pending | `pending`, `created`, `planning`, `deferred` |
| ✅ Done | `done`, `approved`, `partial`, `superseded`, `cancelled` |
| • Khác | status lạ |

- Chip hiện **số lượng** thật; chip 0 task vẫn hiện (mờ) để thấy đủ cấu trúc trạng thái.
- Bấm **Tất cả** → card được **gom thành từng nhóm** có tiêu đề `💻 Coding (47)`… (nhóm việc đang làm đứng trước).
- Bấm 1 chip → chỉ xem nhóm đó (`statsNote` ghi `nhóm 💻 Coding`); **Xoá lọc** trả về toàn bộ.
- Đây là lớp **hiển thị**: `status:` trong file giữ nguyên, không ghi lại thành "nhóm".


Quy tắc adapter cho task thật (`daoanh/tasks/*.md`):

- Đọc YAML frontmatter `id`, `title`, `status`, `updated`, `module`, `priority`.
- Acceptance criteria lấy từ section `## Acceptance criteria` → `percent` = số `[x]/tổng` (đúng rule
  "progress = done/total hoặc checklist"); không có AC → `—`, không bịa.
- Task thật **không có** block 3 agent → hiện "chưa có dữ liệu", không tự điền.
- Task thật **không áp workflow DILA** (status gốc `pending/in_progress/done/…` giữ nguyên, ghi rõ trên card).
- Giới hạn hiển thị để dashboard nhẹ: DILA 40 · **task thật 300 (đủ 194)** · docs 120 file
  (số còn lại ghi ở dòng "Nguồn:").

API tương ứng: `GET /api/list?source=dila|real|docs` → `{dir, count, files:[{file,size,modified}]}`.

> Đổi tab bằng nút, hoặc giữ nguyên tab khi F5 bằng `?source=real` / `?source=docs`.

---


| File | Vai trò |
|---|---|
| `dashboard/agent_team.html` | Khung giao diện |
| `dashboard/agent_team.css` | Theme Amber Gold `#d97706` trên Dark Slate `#020617` |
| `dashboard/agent_team.js` | Parse Markdown → render card, progress bar, checklist, blockers, Approve/Reject |
| `dashboard/serve.py` | Static server + `POST /api/task-status` (ghi Status) |
| `dashboard/test_agent_team.js` | Test parser/render (Node, DOM giả) — không cần browser |
| `tasks/DILA-TASK-0001.md` | Mẫu `bug_found`, overall 60% |
| `tasks/DILA-TASK-0002.md` | Mẫu `coding`, overall 40% |
| `tasks/DILA-TASK-0003.md` | Mẫu `done_pending_admin`, overall 100% |

---

## 3. DILA Team — 3 vai trò

| ID | Vai trò | Nhiệm vụ |
|---|---|---|
| `claude_code_planner` | QA / Planner / Debugger | Tạo Task Number, acceptance criteria, nhận Bug Report, tạo fix task; không code trừ khi debug |
| `opencode_developer` | Developer | Code theo Task Number, không mở rộng scope, báo files changed + test result |
| `openrouter_tester` | Tester (OpenRouter FREE, model khác coder) | Test theo acceptance criteria, không sửa code; FAIL → Bug Report, PASS → `READY_FOR_ADMIN` |

Chi tiết: `agents/dila_team.md`, `agents/dila_team.json`, `agents/orchestrator_prompt.md`.

Workflow:

```
created → planning → coding → testing ──PASS──► done_pending_admin → approved / rejected
                      ▲            │
                      │            └─FAIL─► bug_found → debugging → retesting
                      └──────────────────────────────(fix xong)──────┘
```

Quy tắc: chỉ Orchestrator điều phối · progress = `done/total` hoặc checklist · không tự sinh progress ·
`done` phải chờ Admin duyệt · bug quay về Planner.

Dashboard thể hiện đúng luật này:

- **stepper** hiển thị đúng 10 state; state lỗi hiện nhánh `bug_found → debugging → retesting` kèm chú thích
  "↺ bug quay về claude_code_planner".
- **agent đang phụ trách** được tô sáng: `created/planning/debugging/bug_found` → Planner,
  `coding` → Developer, `testing/retesting` → Tester, `done_pending_admin` → không agent nào (chờ Admin).
- Phân quyền field (ai được sửa gì trong file task): xem [agents/dila_team.md](../agents/dila_team.md) §4.

---

## 4. Format file task

```markdown
# DILA-TASK-0004

## Title
Tiêu đề task

## Status
coding            <!-- created | planning | coding | testing | bug_found | debugging | retesting | done_pending_admin | approved | rejected -->

## Overall Progress
done: 6
total: 10
percent: 60

## Agents

### Claude Code
- Status: working
- Progress: 8/20
- Percent: 40
- Bugs: 0

### OpenCode
- Status: working
- Progress: 7/20
- Percent: 35
- Bugs: 1

### OpenRouter Tester
- Status: testing
- Progress: 8/20
- Percent: 40
- Bugs: 1

## Acceptance Criteria
- [x] Tiêu chí đã xong
- [ ] Tiêu chí còn lại

## Blockers
- Blocker 1

## Last Updated
2026-10-25 15:05
```

Parser chấp nhận cả tên vai trò mới (`### Claude Code Planner`, `### OpenCode Developer`,
`### DeepSeek Tester`) và tên cũ (`### Claude Code`, `### OpenCode`) — cùng map về 3 agent của DILA Team.

---

## 5. Quy tắc hiển thị

- **Tiêu đề card**: mã task luôn đứng trước mô tả —
  `T22 : Founding Date Pipeline — 59K Places → HOME Integration`.
  Nếu title trong file đã bắt đầu bằng mã (VD `T22 — …`) thì không lặp lại; header card chỉ còn badge status.
- **Mô tả nhiệm vụ & mục tiêu hoàn thành** (panel `📄` trong card, mở bằng click):
  - *Mô tả*: lấy từ section `## Mô tả` / `## Mục tiêu` / `## Overview` / `## Description`… (tối đa 3 đoạn);
    không có section thì lấy đoạn văn đầu tiên của body (riêng task thật) — DILA task không có thì ẩn panel.
  - *Mục tiêu hoàn thành (done_when)*: lấy `done_when:` trong frontmatter task thật, **hỗ trợ block `>` / `|`
    nhiều dòng**; thiếu thì lấy section "Done when / Mục tiêu hoàn thành / Definition of done".
  - Kèm `⛓ Phụ thuộc` (từ `depends_on`) và `🗓 Tạo` (từ `created`) để Admin đủ căn cứ xác nhận TaskDone.
  - Song song với panel **Acceptance criteria** (`- [x]`) — hai thứ cộng lại chính là căn cứ check Done.
- **percent**: nguồn theo thứ tự `percent:` → `done/total` → checklist `[x]/[ ]`; thiếu cả ba → `—`
  (không bịa số; giao diện ghi rõ nguồn: "từ percent:" / "từ done/total" / "từ checklist").
- **Bug count** = tổng `Bugs:` của 3 agent (`none`/`0`/rỗng = 0).
- **Blocker count** = số bullet trong `## Blockers`, bỏ qua `- None`, `-`, `- Không có`.
- **Acceptance criteria** = checklist `- [ ]` / `- [x]` + đếm `x/y`.
- **Approve/Reject** chỉ render khi `Status = done_pending_admin`. Approve → `## Status: approved`,
  Reject → `## Status: rejected`, ghi vào đúng file, mọi dòng khác giữ nguyên byte-for-byte.

---

## 6. Thêm task mới

1. Tạo `tasks/DILA-TASK-0004.md` theo format ở mục 4 (Task Number trong heading `#`).
2. Bấm **⟳ Làm mới** — file mới hiện ngay, không cần sửa code, không cần restart server.

## 7. Agent cập nhật task

Agent chỉ cần sửa file `.md` của mình trong `tasks/` — dashboard đọc lại khi refresh:

```python
# ví dụ: developer cập nhật progress
import re, pathlib
p = pathlib.Path("tasks/DILA-TASK-0002.md")
s = p.read_text(encoding="utf-8")
s = re.sub(r"(### OpenCode\n(?:- [^\n]*\n)*?- Progress: )\d+/\d+", r"\g<1>9/20", s, flags=re.M)
s = re.sub(r"(### OpenCode\n(?:- [^\n]*\n)*?- Percent: )\d+", r"\g<1>45", s, flags=re.M)
p.write_text(s, encoding="utf-8")
```

Hoặc dùng tool `edit` sửa thẳng dòng `- Progress: 7/20` → `- Progress: 9/20`.
Sau đó cập nhật `## Last Updated` và `## Status` theo workflow.

---

## 8. API (chỉ dùng cho nút Approve/Reject)

| Method | Path | Mô tả |
|---|---|---|
| `GET` | `/api/health` | `{ok, root, tasks_dir, dashboard}` — dashboard dùng để phát hiện chế độ ghi |
| `GET` | `/tasks/` | JSON `{"tasks":[{"file","size","modified"}]}` (hoặc autoindex HTML nếu dùng `python -m http.server`) |
| `GET` | `/tasks/<file>.md` | Nội dung Markdown thô |
| `POST` | `/api/task-status` | Body `{"file":"DILA-TASK-0003.md","status":"approved"\|"rejected"}` → ghi đúng dòng `## Status` |
| `POST` | `/api/real-task-status` | Body `{"file":"T462-harness-coder-tester-loop.md","status":"done"}` → ghi đúng dòng `status:` trong frontmatter task thật |
| `POST` | `/api/task-note` | Body `{"source":"real","file":"BUG-025-....md","note":"mô tả bug"}` → append `- [ts] note` vào `## Admin Notes` (source `dila` hoặc `real`) |
| `POST` | `/api/notify-done` | Body `{"id":"T22","title":"..."}` → chạy lại pipeline build + Tiểu Thiên (`"dry":true` chỉ trả lệnh, `"wait":true` chạy đồng bộ) |
| `GET` | `/api/notify-done/last` | `{last:{state,result}}` — trạng thái lần chạy pipeline gần nhất |

Chặn: tên file phải khớp `^[A-Za-z0-9][A-Za-z0-9._-]*\.md$` và nằm trực tiếp trong thư mục nguồn
(không traversal), status chỉ nhận trong whitelist (`approved/rejected` cho task DILA;
`pending/in_progress/blocked/done/deferred/partial/superseded/cancelled/qa/review` cho task thật).

---

## 9. Test

```bash
node dashboard/test_agent_team.js
```

76 assertion: parse 3 task thật, quy tắc percent, render 3 card + 9 progress bar + 15 checkbox,
nút Approve/Reject chỉ xuất hiện ở `done_pending_admin`, và kiểm tra JS không spawn process /
không gọi agent / không lưu state.
