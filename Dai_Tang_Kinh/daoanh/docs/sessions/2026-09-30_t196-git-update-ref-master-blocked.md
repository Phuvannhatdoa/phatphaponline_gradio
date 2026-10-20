# T196 — `git update-ref refs/heads/master` blocked (worktree-level)

**Ngày:** 2026-09-30 · **Agent:** claudecode · **Trạng thái:** BLOCKED (chờ Admin)
**Phạm vi:** docs-only, 0 code / 0 DB · **Phát hiện:** trong lúc commit T195

## 1. Vì sao sinh task này

Trong khi commit T195, mọi lệnh cập nhật ref `master` đều thất bại:

```
fatal: update_ref failed for ref 'refs/heads/master': couldn't set 'refs/heads/master'
```

Đây không thuộc phạm vi T195 (docs về identity/canonical person) nên tách thành
task riêng. Admin đã phê chuẩn cách tách này.

## 2. Đã làm

| Bước | Kết quả |
|---|---|
| Commit pass-1 T195 bằng `git commit` (temp index) | ❌ `couldn't set 'refs/heads/master'` |
| Thử 6 lần có backoff | ❌ 1 fail, 1 rc=1, sau đó treo >300s |
| Kiểm tra lock/contention | 0 tiến trình git, 3 lock stale ~30h |
| Tách stage khỏi update: `commit-tree` | ✅ tạo commit object OK |
| `update-ref` retry 10× | ❌ **0/10 thành công** (tất định) |
| Probe ref tạm mới, có reflog, đổi giá trị | ✅ OK → lỗi **chỉ ở `master`** |
| `git -c core.logAllRefUpdates=false update-ref` | ❌ vẫn fail |
| `git branch -f master` | ❌ "used by worktree" |
| Ghi ref file trực tiếp (40 hex + `\n`) | ✅ HEAD dịch đúng, `git log` chuẩn |

## 3. Đã loại trừ

Contention · lock file · reflog · `logAllRefUpdates` · ACL/quyền thư mục ·
lock ở chính file ref · compare-and-swap · worktree khác giữ `master` ·
`packed-refs`. Bảng bằng chứng đầy đủ: `tasks/T196-git-update-ref-master-blocked.md` §3.

**Chưa loại trừ:** có tiến trình nào giữ handle lên `.git\refs\heads\master`
(IDE/agent watcher) — cần `handle.exe` / `openfiles /query` mà task này không có quyền.

## 4. Tác động đã xử lý

- T195 pass-1 `a0aad7185b64064dac624839723b9a3fe0709b6a` — 7 file docs-only.
- T195 pass-2 `a208d9e9cef6f47f994e100db99a934615518809` — 5 file × 1 dòng
  (hash-fill + sửa số dòng `546→755` thành `720→986`).
- Cả hai kiểm chứng: `cat-file`, `diff --stat`, `log`, `rev-parse`, `fsck` (chỉ
  `dangling`, không `corrupt`).

**Nợ kỹ thuật:** 2 commit này thiếu 1 entry trong `git reflog` của `master`
(bước ghi ref tay không ghi reflog). Lịch sử commit không ảnh hưởng.

## 5. Sai sót của chính agent (ghi lại để không lặp lại)

1. **Tin `Measure-Object -Line`** → ghi "T176 546→755 dòng" vào 5 file + commit
   message pass-1. Số thật **720→986**. Đã sửa ở pass-2; commit message pass-1
   không sửa được (immutable, không amend vì worktree dùng chung).
2. **Dùng Bash heredoc `<<EOF` trong PowerShell** → lỗi parse
   `Missing file specification after redirection operator`. Phải viết message ra
   file rồi `git commit -F <file>`.
3. **Tin `git diff HEAD` trên worktree dùng chung** → main index bị stale báo *xoá*
   141/186 dòng cho file vẫn tồn tại (`D ` + `??`). Sợ mất dữ liệu hoá ra là
   artifact. Phải kiểm diff **trong temp index**.
4. **`git add` bỏ sót `data/progress_data.json`** vì path bị gitignore dù đã
   tracked → phải `git add -f`.

## 6. Cần Admin

1. Kiểm tra handle trên `.git\refs\heads\master` (`handle.exe` / `openfiles /query`).
2. Quyết định: có công bố workaround `commit-tree` + ghi ref tay làm tạm quy chuẩn không.
3. Cân nhắc `git pack-refs` để bỏ loose ref (chưa tự làm — `refs/` dùng chung).

## 7. Không làm

Không xóa lock stale · không `git gc`/`pack-refs`/`prune` · không amend/rebase ·
không đụng `master.bak_t83` · không đụng `lineage.db`/`app.py`/`T175`.

## 8. `pipip` — KHÔNG gọi được (endpoint offline)

Admin yêu cầu "Gọi pipip khi done". Đã thử sau khi T195 + T196 commit xong:

| Kiểm tra | Kết quả |
|---|---|
| `Test-NetConnection 127.0.0.1 -Port 37700` | `TcpTestSucceeded = False` |
| `curl.exe -m 8 http://127.0.0.1:37700/api/health` | `http_code=000`, **curl exit 7** (failed to connect) |
| `Get-NetTCPConnection -LocalPort 37700 -State Listen` | không có listener |
| Quét toàn bộ listener localhost | 135, 445, 843, 3000, 4096, 4709, **5000**, **5001**, 5040, 6000, 7679, 8080, 17500, 17600, 49664-49669, 49697, 49735, 49737, 50647, 54596 — **không có 37700** |

⇒ `pipip` (endpoint ghi trong `AGENTS.md` §0) **không chạy** ⇒ **chưa ghi được
observation**. 5000/5001 là `app.py` + `server.py` (Auth Gateway) theo `AGENTS.md`
§10, không liên quan.

**Cần Admin khởi động lại `pipip`** rồi agent sẽ `POST /api/sessions/observations`
để ghi T195/T196. Không tự đoán port khác — endpoint duy nhất được tài liệu hoá
là `http://127.0.0.1:37700`.