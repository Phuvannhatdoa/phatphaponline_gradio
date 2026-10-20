
---

## 0. TASKTODO — Session Continuation Protocol

### Save tasktodo to memory
```bash
# After finishing a session, always run:
curl -s -X POST http://127.0.0.1:37700/api/sessions/observations \
  -H "Content-Type: application/json" \
  -d '{"contentSessionId":"daoanh-master","tool_name":"tasktodo","tool_input":{},"tool_response":"{\"current_task\":\"<task_name>\",\"status\":\"<done|in_progress|pending>\",\"next_task\":\"<next_task_name>\"}","cwd":"/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh"}'
```

### Load tasktodo command
When user says `tasktodo`, the agent MUST:
1. Search claude-mem: `curl -s "http://127.0.0.1:37700/api/search/observations?query=tasktodo&limit=3"`
2. Read `docs/tasktodo.md` for full context
3. Read latest session logs: `ls -t docs/sessions/ | head -3`
4. Read git log: `git log --oneline -5`
5. Report current state + suggest next action

### Active Task List (auto-maintained in docs/tasktodo.md)
See `docs/tasktodo.md` for the authoritative task list.

### Commit Convention
```
<type>: <short description> + docs
```
Types: `feat` (new feature), `fix` (bug fix), `docs` (documentation), `refactor`, `test`, `chore`

Always include `+ docs` in message if docs/sessions/ was updated.

---

## 10. Server Architecture (Post-Split 2026-05-14)

### Two-Server Setup

| Server | File | Port | Role |
|--------|------|------|------|
| **Auth Gateway** | `server.py` | **5001** | Login only (Gmail check, session mgmt, admin emails) |
| **Main Server** | `app.py` | **5000** | All business logic (Đạo Ảnh, TTL, Marcus, dossier, translation) |

### Run Commands

```bash
# Auth Gateway (login)
cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh
python server.py        # port 5001

# Main Server (Đạo Ảnh + all APIs)
python app.py           # port 5000
```

### Route Ownership

| Path Prefix | Handled By |
|-------------|-----------|
| `/daoanh/login.html` | server.py:5001 |
| `/daoanh/api/login/*` | server.py:5001 |
| `/api/admin/emails` | server.py:5001 |
| `/daoanh/admin/` → placevn.html | app.py:5000 |
| `/daoanh/panorama/` → panorama.html | app.py:5000 |
| `/daoanh/api/admin/*` | app.py:5000 |
| `/daoanh/api/public/*` | app.py:5000 |
| `/daoanh/static/*` | app.py:5000 |
| `/api/*` (TTL, Marcus, dossier, etc.) | app.py:5000 |

### Key Changes
- server.py stripped from ~2,800 lines → ~125 lines (login only)
- app.py expanded from 429 lines → ~2,600 lines (all business logic)
- `/daoanh/admin/` now serves `placevn.html` (Đạo Ảnh mapping)
- `/daoanh/panorama/` serves `panorama.html` (TTL ontology)
- Nginx must route `/daoanh/api/login/*` to port 5001, everything else to port 5000

## 11. Tester Agent System (Mandatory Before Review)

### 🚀 Quick Start
Before requesting review from admin, **MUST** run tester agent:

```bash
cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh
npm run tester:agent
```

Or using OpenCode:
```
/test
```

### ✅ What Tester Agent Checks
1. **Lint**: JavaScript syntax and style (ESLint)
2. **Test**: Unit/integration tests
3. **E2E**: End-to-end tests (check for JS console errors in HTML pages)

### 📋 Output Example
```
🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔
🚀 TESTER AGENT STARTING
🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔

============================================================
📋 Running: LINT
📝 Description: Check JavaScript syntax and style (ESLint)
💻 Command: npm run lint
============================================================

✅ lint PASSED

============================================================
📋 Running: TEST
📝 Description: Run unit/integration tests
💻 Command: npm run test
============================================================

✅ test PASSED

============================================================
📋 Running: E2E
📝 Description: End-to-end tests (check for JS console errors)
💻 Command: npm run e2e
============================================================

✅ e2e PASSED

============================================================
📊 TESTER AGENT SUMMARY
============================================================
✅ Passed (3/3): lint, test, e2e
❌ Failed (0/3): none
============================================================

🎉 ✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅
   ALL TESTS PASSED, READY FOR REVIEW!
   ✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅
```

### ❌ If Tests Fail
```
❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌
   SOME TESTS FAILED!
   Please fix errors above and run again before asking for review.
   ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌ ❌
```

### 📂 Files Created
```
package.json          - Updated with lint, test, e2e, tester:agent scripts
scripts/tester-agent.mjs     - Main tester agent script
scripts/e2e-test.js          - E2E tests (check HTML/JS errors)
.opencode/plugins/tester-agent.js - OpenCode plugin (optional)
```

### 🔧 Technical Details
- **Lint**: Uses ESLint (or basic syntax check with `node -e`)
- **Test**: Runs unit tests (placeholder created if none exist)
- **E2E**: Checks HTML pages for JS syntax errors and inline event handlers
- **OpenCode Plugin**: Registers `/test` command (if plugin API available)

### 📝 Workflow Rule
1. Developer makes changes
2. Run `npm run tester:agent` (or `/test` in OpenCode)
3. If all pass → Request review from admin
4. If any fail → Fix errors → Run again
5. Admin ONLY reviews when "All tests passed" is shown

**NO EXCEPTIONS!** 🚫

---


---

## 12. Quick Command Reference for Tester Agent

### 🚀 For Devs (MUST run before review):

**Option 1: Full pipeline (recommended)**
```bash
cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh
npm run pipeline
```

**Option 2: Tester agent only**
```bash
cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh
npm run tester:agent
```

**Option 3: Global command (run from anywhere)**
```bash
tester-agent
```

### 📋 What Each Command Does:

| Command | Description | Expected Output |
|----------|-------------|-------------------|
| `npm run lint` | Check JS syntax in all HTML files | ✅ All lint checks passed! |
| `npm run test` | Run unit/integration tests | ✅ Tests passed! |
| `npm run e2e` | Check HTML pages for JS errors | ✅ All pages passed E2E checks! |
| `npm run tester:agent` | Run all 3 steps above | ✅ ALL TESTS PASSED, READY FOR REVIEW! |
| `npm run pipeline` | Run lint + test + e2e | ✅ PIPELINE COMPLETE: All checks passed! |
| `tester-agent` | Same as `npm run tester:agent` | ✅ ALL TESTS PASSED, READY FOR REVIEW! |

### 🎯 Workflow:

1. **Make changes** to code
2. **Run tester**: `npm run pipeline` or `tester-agent`
3. **If ✅ PASSED**: Request review from admin
4. **If ❌ FAILED**: Fix errors shown, run again
5. **Admin ONLY reviews** when "All tests passed" is shown

### 📝 Example Output (Success):

```
✅ LINT: All syntax checks PASSED!
✅ TEST: Tests passed!
✅ E2E: All pages passed E2E checks!

🎉 ✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅
   ALL TESTS PASSED, READY FOR REVIEW!
   ✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅
```

### 📂 Files Created for Tester Agent:

```
package.json              - Updated with lint, test, e2e, tester:agent, pipeline
scripts/tester-agent.mjs     - Main tester script (ES module)
scripts/e2e-test.js          - E2E checks (HTML/JS errors)
scripts/lint-check.sh        - Bash script for JS syntax check
.opencode/plugins/tester-agent.js - OpenCode plugin (optional)
README-tester-agent.md       - Documentation
AGENTS.md                - Updated with workflow + commands
```

**NO EXCEPTIONS!** 🚫
- Devs MUST run `npm run pipeline` before requesting review
- Admin ONLY reviews when tests pass
- Fix errors and re-run until "All tests passed"

---

## 13. SSOT Repo Root Guard (T155)

### Rule bắt buộc
- **SSOT repo root = `git rev-parse --show-toplevel` = `visjs-app`** (daoanh là subdir, KHÔNG phải repo riêng).
- **Mọi lệnh git PHẢI chạy từ toplevel** (`visjs-app`). Không `cd` vào `Dai_Tang_Kinh/daoanh` rồi chạy git.
- **CẤM `git init` trong `Dai_Tang_Kinh/daoanh/`** (hoặc bất kỳ subdir nào) — sẽ tách lịch sử và phá revert.
- Các thư mục dữ liệu là nested repo ngoài (`Authority-Databases`, `chinese_buddhism_sna_temp`) **không được track**; đã `.gitignore`. Không `git add` chúng.

### Guard tự động
```bash
cd /opt/.../visjs-app/Dai_Tang_Kinh/daoanh
npm run guard      # hoặc: python -X utf8 scripts/repo_guard.py
```
- PASS khi `--show-toplevel` khớp `visjs-app` VÀ không có `.git/HEAD` trong `daoanh/`.
- FAIL (exit 1) → dừng pipeline, sửa trước khi commit.
- `npm run pipeline` đã tự chạy guard ở bước đầu tiên.

### Dấu hiệu bất thường cần báo Admin
- Xuất hiện `Dai_Tang_Kinh/daoanh/.git/HEAD` (repo lồng thật).
- `git status` hiện ` m <data-dir>` (gitlink mồ côi tái xuất).
- Đã vô hiệu `.git` hỏng cũ bằng cách rename → `.git.disabled-20260917/` (giữ vết, hoàn nguyên được).

---

---

## 14. QUY TR?NH COMMIT/REVERT AN TO?N (B?T BU?C)

> Ngu?n ??y ??: `tasks/G208-safe-commit-revert-procedure.md`

**V? sao c?n m?c n?y:** ghi `.git/index` tr?n ? n?y hay b? Windows ch?n ?
b??c rename ? `fatal: unable to write new index file`. T? h?n: ??i khi git
**kh?ng b?o l?i** nh?ng `git diff --cached` v?n R?NG ? `git add` coi nh?
xong oan.

1. **Sau m?i `git add`, ph?i ki?m** `git diff --cached --name-only` c? in ra
   file kh?ng. R?ng ? add ?? th?t b?i.
2. L?i index ? d?ng index t?m, **t?o b?ng `git read-tree HEAD`**:
   ```bash
   export GIT_INDEX_FILE="$PWD/.git/wt_tmp_index"
   git read-tree HEAD        # B?T BU?C read-tree
   git add -- <file>
   git diff --cached --name-only   # x?c minh ??ng danh s?ch
   git commit -m "..."
   unset GIT_INDEX_FILE; rm -f .git/wt_tmp_index*
   ```
3. **TUY?T ??I KH?NG** `cp .git/index .git/wt_tmp_index` ? index c? h?n HEAD
   s? l?m commit **xo? nh?m file** (?? x?y ra 1 l?n, kh?i ph?c b?ng
   `git read-tree <commit-truoc>` r?i commit l?i).
4. `git commit` v?n fail ? plumbing: `git write-tree` ? `git commit-tree`
   ? `git update-ref refs/heads/master <new> HEAD`.
5. **Sau m?i commit** ki?m `git diff --name-status HEAD~1 HEAD` ? th?y `D`
   ngo?i ? mu?n l? ho?n t?c ngay.
6. M?i bug fix ph?i revert ???c: code = `git revert --no-edit <sha>`;
   DB **additive** = `DROP COLUMN` (m?t 0 d? li?u); DB s?a h?ng lo?t =
   restore t? snapshot t?ng ?; TTL = backup file-level + `--revert <dir>`.
   ?u ti?n thi?t k? additive cho m?i migration DB.---

## 15. QUY TẮC ĐẶT TÊN FILE HANDOFF (BẮT BUỘC)

> Admin yêu cầu (2026-10-02): mọi thông tin để lại cho admin/agent sau phải nằm
> trong file đặt tên theo convention, **càng chi tiết càng tốt** để agent
> Claude Code rành xét lại và Admin dễ review.

### Tên file bắt buộc
```
docs/Handoff-YYYY-MM-DD.md                  # bàn giao cuối session
docs/Handoff-YYYY-MM-DD-<mô-tả>.md          # khi có nhiều task trong 1 ngày
```
- Đúng convention: `Handoff-`, viết hoa `H`, kém `YYYY-MM-DD`.
- **Không** dùng tên khác (`HANDOFF_`, `notes.md`, `handoff.txt`).
- File cũ để nguyên dạng, **thêm 1 file Handoff mới** mỗi session.

### Bố cục 10 mục (thiếu dễ đọc dễ đánh giá)
1. **Bảng thông tin đọc nhanh**: ngày bàn giao, HEAD, session đã làm, trạng thái
   test, preflight, DB, TTL.
2. **Đọc trong 2 phút** — Admin review nhanh: đã làm gì, phát hiện quan trọng
   nhất, 3 việc Admin cần làm ngay.
3. **Đề suất phần chữa dựng** cho từng task: vấn đề, cách sửa, bằng chứng, kết
   quả đo được (không mô tả chung chung).
4. **Cảnh báo bắt buộc** — mọi thủ tục cần biết khi làm việc mới: git lock, TTL
   không git track, session chạy song song.
5. **Lệnh revert từng task** — copy/paste được chạy, kèm bảng "mất dữ liệu?"
   (additive vs restore).
6. **Bảng file tạo/sửa** trong session.
7. **Sai lầm tự mình làm** + bài học thuật đã vấp — để agent sau không lặp lại.
8. **Việc CHƯA xong** theo thứ tự ưu tiên, kèm câu hỏi cần Admin phải quyết.
9. **Lệnh kiểm tra nhanh** để agent sau tự verify trong 1 phút.
10. **Ghi chú cho agent kế tiếp** — checklist thao tác để người nhận không phải mò.

### Ví dụ bắt buộc
- **Cảnh báo đều dễ bị sót nhất trong file** — để kẻ đọc không bỏ sót.
- Mọi claim phải kèm **kiểm chứng** (số đo, output lệnh, diff).
- Ghi rõ **điều đã bị bác bỏ** — "tôi đã thử X nhưng sai, đổi sang Y" thì phải ghi
  "X đã bị kiểm chứng sai".
- **Không liệt kê tối thiểu được commit** trong file Handoff — trỏ thẳng tới
  `git log`, tránh bịn khi bàn giao.

### Đường dẫn liên quan
| File | Vai trò |
|---|---|
| `docs/Handoff-2026-10-02.md` | Ví dụ đầy đủ (10 mục) |
| `docs/TTL-FILE-STATUS-REPORT.md` | Báo cáo trạng thái file TTL (sinh tự động) |
| `docs/ROLLBACK.md` | Quy trình revert + row từng task |
| `AGENTS.md` §14 | Quy trình commit/revert an toàn |
| `tasks/G208-safe-commit-revert-procedure.md` | Chi tiết lỗi `index.lock` |

---

## 16. CẤP ID TASK — PHẢI KIỂM 2 TẦNG (T220+)

> Thêm 2026-10-02 sau khi phát hiện **6 ID trùng** trong repo (`T158`, `T206`, `T215`)
> và 1 vụ race: session khác tạo `tasks/T217-vnpa-etl-preservation-guard.md` **trong lúc**
> đang cấp T217 cho task khác.

### Tầng 1 — trùng file (đã tự động chặn)

```bash
cd /opt/.../Dai_Tang_Kinh/daoanh
npm run dup:ids        # build_progress_data.py --check-dup-ids
```

Đã nối vào `npm run pipeline` ngay sau `guard` ⇒ trùng ID sẽ **FAIL pipeline**.
Guard chấp nhận:
- `docs/Mimo-Flash/_book/` — mirror, loại trừ.
- File tên `X-*` — bản superseded, cố ý giữ `id` gốc ⇒ chỉ INFO.
- `tasks/*.md` thiếu `id:` frontmatter ⇒ suy ID từ tiền tố tên file (đọc `utf-8-sig`).
- `docs/**` khai báo `task: tasks/<...>` ⇒ bản mở rộng của task đó, không phải task thứ hai.

### Tầng 2 — trùng *prose* (phải tự kiểm, guard không thấy)

ID có thể bị **đặt chỗ bằng văn bản** mà không tạo file task. Vụ `T216` là ví dụ:
4 file ghi *"Follow-up task: T216 — ETL UPSERT guard"* ⇒ `dup:ids` không báo gì.

**Trước khi cấp ID mới, bắt buộc chạy cả hai:**

```bash
npm run dup:ids
grep -rnE '(?<![A-Za-z0-9_-])T[0-9]{3}(?![0-9])' docs/tasktodo.md docs/Mimo-Flash/ 2>/dev/null \
  | grep -vE '_book/' | sort -u
```

Cả 3 điều sau đều **bắt buộc** khi cấp ID:
1. `tasks/Txxx-<slug>.md` có frontmatter `id: Txxx` (viết tay, không copy từ task khác).
2. Không ID nào đang `in_progress`/`blocked` bị dùng lại.
3. Ghi `former_ids: [...]` nếu là đổi số từ ID cũ, để grep ID cũ vẫn ra.

### Nếu đã cấp ID trùng

Đổi số **phía có footprint nhỏ nhất**, theo thứ tự: (1) `status` kết thúc → (2) ít
tham chiếu đến → (3) không có `docs/plans|reports/` đi kèm → (4) không phải ID mà
`docs/tasktodo.md` đã công bố. Rồi commit rename + `former_ids` + dòng ROLLBACK.

---

## 17. DỰ ÁN SONG SONG — HEAD DỊCH CHUYỂN LIÊN TỤC

> Worktree dùng chung: nhiều session commit cùng lúc. Trong một phiên đã quan sát
> HEAD dịch `334f6c2 → 0aa0113 → 46c5bb3 → 1283ee9` **không do mình**.

### Không dùng `git add` trên cây thư mục

```bash
# SAI — nuot luon WIP cua session khac trong cung file
git add -- docs tasks

# DUNG — HEAD blob + thay doi cua minh
git show HEAD:Dai_Tang_Kinh/daoanh/<file> > tmp     # tu dung HEAD
# sua tmp, roi:
sha=$(git hash-object -w tmp)
git update-index --add --cacheinfo "100644,$sha,Dai_Tang_Kinh/daoanh/<file>"
```

Cặp đường dẫn khác nhau, sai là hỏng:
- `git add` / `--force-remove` (pathspec) → **tương đối `cwd`**
- `--cacheinfo` / `git show HEAD:<p>` → **tương đối repo root**
- `git ls-tree HEAD` **không có `--`** → liệt kê theo `cwd` hiện tại (dễ tưởng cấu trúc lệch)

### `update-ref` CAS thất bại trên máy này

`git update-ref refs/heads/master <new> <old>` → `couldn't set` / `PermissionError
[WinError 5]` khi `os.replace`. Nguyên nhân: khác biệt `update-ref` (ghi file ref) và
CAS (giữ `refs/heads/master.lock`) — AGENTS §14 chỉ ghi "tạo temp index bằng
`read-tree`", chưa nêu chỗ này. **Fallback: ghi file ref trực tiếp, có CAS thủ công:**

```python
if open(ref).read().strip() != parent:   # kiểm CAS bằng tay
    abort()
open(ref, "w").write(new + "\n")          # ghi tại chỗ, không dùng os.replace
```

Đừng tin `update-ref` không CAS trả về 0 — nếu `new == old` thì git **bỏ qua ghi**,
nên "OK" là no-op, chưa hề commit.

### Nguyên nhân gốc của mọi "Unable to write …" / `WinError 5` (đã đo 2026-10-06)

Không phải bug của git — là **quyền file của shell**:

| đo | kết quả |
|---|---|
| `whoami /groups` | **MEDIUM IL** (không được UAC) |
| `BUILTIN\Administrators` | *Group used for deny only* |
| ACL `.git/index`, `HEAD`, `config` | `Users` = `Write, ReadAndExecute` — **không có DELETE** |
| rename `index` / `HEAD` / `config` | **Access denied** |
| mở `.git/index` với `FileShare.None` | **thành công** ⇒ không ai giữ handle |

File mình tạo thì `CREATOR OWNER` FullControl → rename được; file của git thì
không. Vậy **git không bao giờ rename được gì trong `.git/`**, kể cả
`index.lock → index` → `git update-index` báo `fatal: Unable to write new
index file`.

**Sync `.git/index` khi không rename được** (dùng khi cần đưa file mới vào
index mà không muốn mất staged của session khác):

1. Copy `.git/index` → file tạm (giữ nguyên format + checksum SHA-1 cuối).
2. Chạy mọi `git update-index` trên file tạm với `GIT_INDEX_FILE` (ở
   `%TEMP%` rename được).
3. **Ghi byte file tạm vào `.git/index` bằng `open(..., "r+b")` +
   `truncate()`** — ghi tại chỗ chỉ cần Write.
4. Tasktodo/docs dùng chung: dựng từ **bản đang nằm trong index** của
   session khác (`git ls-files -s` → `git cat-file blob <sha>`), **không**
   lấy worktree, rồi mới chèn phần của mình — lấy worktree sẽ nuốt WIP
   chưa staged của họ.
5. Backup byte gốc trước, so `git diff --cached --name-status` sau.

`git status` trên máy này cũng **hỏng im lặng** (exit 1, stdout/stderr 0
byte) dù xoá `index.lock`; chạy được khi có pathspec. Dùng
`git diff --cached` / `git diff <a> <b>` thay thế. Chi tiết:
`docs/sessions/2026-10-06_T251-ld2-era-gap.md` §8.

### Luôn kiểm trước khi commit

```bash
git diff --cached --name-status   # phai dung danh sach file mong doi
git rev-parse HEAD                # HEAD dang o dau?
```

Cặp `(parent, new)` phải tính lại **ngay trước lúc** commit, không dùng số đo lúc
đầu phiên.

## 18. BÁO "DONE" — PHÁT ÂM THANH `pipip` (BẮT BUỘC)

Khi **hoàn thành một việc** (commit xong, task done, revert xong, pipeline xanh),
agent **phải phát âm thanh báo cho Admin** trước khi báo cáo kết thúc.
Admin không ngồi canh màn hình — tiếng kêu là dấu hiệu "xong rồi".

```powershell
# 3 nốt lên (done) + âm hệ thống — chạy được ngay, không cần file nào
[System.Media.SystemSounds]::Asterisk.Play()
[console]::Beep(880,150); [console]::Beep(1175,150); [console]::Beep(1568,300)
```

- Lệnh gọi: `pipip` (nếu đã tạo `scripts/pipip.ps1`) hoặc chạy thẳng đoạn trên.
- Trạng thái lỗi / cần Admin quyết → **không** phát pipip (tránh báo nhầm done).
- Nếu Admin yêu cầu âm khác, sửa đoạn này trong AGENTS.md — đây là SSOT.

## 20. BÁO "DONE" BẰNG NHÂN VẬT TRÊN DESKTOP (Admin chốt 2026-10-15)

Khi xong một task/bug (sau QA, hoặc khi cần Admin xác nhận DONE), ngoài tin nhắn, gọi:

```powershell
powershell -ExecutionPolicy Bypass -File scripts
otify_done.ps1 -Title "T404 Done" -Message "BUG-034: Ô Search trang places"
```

Nhân vật **Tiểu Thiên** (`static/notify/mascot.png`) hiện ở góc phải dưới cạnh khay hệ thống, kèm âm "ting ting" kêu 3 lần.
Admin click trái để ẩn, click phải để mở Dashboard. Script tự chạy nền, không chặn agent; chỉ chạy local.
Thay cho đoạn `pipip` ở §18 (vẫn giữ quy tắc: trạng thái lỗi / cần Admin quyết thì KHÔNG báo Done).
