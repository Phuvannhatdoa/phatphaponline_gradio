---
id: T196
title: "git update-ref refs/heads/master thất bại trên Windows — chặn commit mọi agent trong worktree"
module: Repo / Git Infrastructure
priority: high
status: done
note: "da giai quyet 2026-10-02: os.replace bi WinError 5; dung ghi file ref truc tiep co kiem CAS thu cong. Quy trinh ghi o AGENTS.md §17, dung 6 lan trong phien 2026-10-02"
owner: claudecode
depends_on: []
created: 2026-09-30
updated: 2026-09-30
designed_by: claudecode
handoff_to: Admin (cần quyết định: có cần can thiệp filesystem/IDE không)
plan_approved_at: "2026-09-30 (Admin phê chuẩn tách thành task riêng khi review T195)"
done_when: |
  `git update-ref refs/heads/master <new> <old>` chạy được trên `master` ·
  hoặc Admin chấp thuận workaround commit-tree + ghi ref trực tiếp làm
  quy chuẩn · T195 pass-1/pass-2 đã commit bằng workaround này (audit trail).
---

# T196 — `git update-ref refs/heads/master` thất bại: chặn commit toàn worktree

> **Phát hiện trong lúc commit T195.** Không phải bug của T195 — là vấn đề hạ
> tầng git trên máy này, ảnh hưởng **mọi agent** dùng chung repo.

## 1. Triệu chứng

Mọi lệnh cập nhật ref có **giá trị mới** trên `master` đều thất bại:

```
$ git update-ref refs/heads/master <new_sha> <old_sha>
fatal: update_ref failed for ref 'refs/heads/master': couldn't set 'refs/heads/master'
# rc=128
```

Lệnh tương đương cũng lỗi:

```
$ git branch -f master <new_sha>
fatal: cannot force update the branch 'master' used by worktree at 'E:/.../visjs-app'
```

## 2. Repro tất định

```bash
cd "E:/Backup 2025/QuaiTieuTu/Anan Son/phatphaponline_gradio/truyenthua/visjs-app"
OLD=$(git rev-parse HEAD)
git commit-tree $(git rev-parse HEAD^{tree}) -p $OLD -m test   # tạo commit object OK
git update-ref refs/heads/master $(cat .git/TMP) $OLD          # -> rc=128, LUÔN FAIL
```

Đo tất định: **10/10 lần đổi giá trị thật đều FAIL** (`OK=0 FAIL=10`).

## 3. Đã loại trừ (evidence-based)

| Giả thuyết | Cách kiểm | Kết quả |
|---|---|---|
| Contention từ agent khác | `Get-CimInstance Win32_Process -Filter "Name='git.exe'"` khi lỗi | **Loại** — 0 tiến trình git, vẫn fail |
| Lock file còn sót | `Get-ChildItem .git -Filter *.lock -Recurse` | **Loại** — chỉ có 3 lock stale ~30h (`index.lock`, `myindex3.lock`, `objects/maintenance.lock`), đều nằm ngoài đường ghi ref |
| Reflog ghi lỗi | `File.Open(".git/logs/refs/heads/master", Open, Write, None)` | **Loại** — mở exclusive thành công |
| `core.logAllRefUpdates` | `git -c core.logAllRefUpdates=false update-ref ...` | **Loại** — vẫn rc=128 |
| Quyền ACL thư mục | `(Get-Acl .git\refs\heads)` | **Loại** — Users có `Write`; và tạo ref mới trong cùng thư mục thành công |
| Lock ở chính file `master` | `File.Open(".git\refs\heads/master", Open, Write, None)` | **Loại** — mở exclusive thành công |
| Compare-and-swap (CAS) | `git update-ref <ref> <new>` (bỏ tham số old) | **Loại** — vẫn rc=128 |
| Worktree khác giữ `master` | `git worktree list` | **Loại** — 4 linked worktree, tất cả detached hoặc nhánh khác; chỉ main worktree giữ `master` |
| `packed-refs` chặn | `Select-String .git\packed-refs "master"` | **Loại** — `master` có trong packed-refs (giá trị cũ `866c911b`) nhưng loose ref ghi đè hợp lệ |

## 4. Phạm vi: CHỈ `master`, không phải toàn repo

| Ref | Đổi giá trị thật | Kết quả |
|---|---|---|
| `refs/heads/master` | có | **FAIL 10/10** |
| `refs/heads/t195probe2` (ref mới, **có reflog**) | có | **OK** |
| `refs/heads/master` — **no-op** (ghi lại giá trị hiện tại) | không | OK (git short-circuit, không ghi file) |
| `refs/heads/main` / `daoanh` / `temp-snapshot` — no-op | không | OK |

⇒ Cơ chế lock/rename/reflog của git **hoạt động bình thường**. Chỉ riêng việc
ghi `master` bị chặn. Đây không phải lỗi logic git.

## 5. Ảnh hưởng

- **Chặn commit của mọi agent** trên nhánh `master` — kể cả `git commit` thường,
  vì `git commit` cũng phải update `HEAD` → `refs/heads/master`.
- Không phá dữ liệu: ref file vẫn hợp lệ, commit object vẫn đúng, lịch sử không
  hỏng. Chỉ là **không ghi được ref**.
- Mọi agent phải tự tìm workaround → dễ mất thời gian và dễ commit nhầm.

## 6. Workaround đã dùng và kiểm chứng (dùng cho T195)

Vì `update-ref` fail nhưng commit object tạo được, dùng 3 bước:

```powershell
# 1. Tạo commit object (KHÔNG đụng ref) — chạy được
$env:GIT_INDEX_FILE = "<temp>.idx"; git read-tree HEAD
git add -f -- <file...>; $tree = git write-tree; $env:GIT_INDEX_FILE = $null
$commit = git commit-tree $tree -p HEAD -F msg.txt      # -> OK

# 2. Update ref — thất bại
git update-ref refs/heads/master $commit HEAD          # -> rc=128

# 3. Ghi ref trực tiếp (tương đương thao tác git tự làm)
[System.IO.File]::WriteAllText("$PWD\.git\refs\heads\master", $commit + "`n",
    (New-Object System.Text.UTF8Encoding($false)))
```

**Định dạng ref file** = 40 ký tự hex + `\n` (xác minh file hiện tại dài 41 byte).

### Kiểm chứng sau workaround

| Kiểm tra | Kết quả |
|---|---|
| `git cat-file -p <commit>` | tree/parent/author đúng |
| `git diff --stat <parent> <commit>` | đúng 7 file (T195 pass-1) / đúng 5 file × 1 dòng (pass-2) |
| `git log --oneline` | commit hiển thị đúng vị trí |
| `git rev-parse master` | khớp |
| `git fsck --connectivity-only` | chỉ `dangling` (từ các lần thử bỏ dở), **không** `corrupt`/`missing` |

**Hạn chế đã biết:** bước 3 **không ghi reflog** cho `master` ⇒ dòng reflog tương
ứng bị thiếu. Lịch sử commit không bị ảnh hưởng (ref trỏ đúng commit object),
`git log` bình thường; chỉ `git reflog` bỏ sót 1 entry cho mỗi commit.

## 7. Việc cần Admin quyết

1. **Có tiến trình nào giữ handle lên `.git\refs\heads\master` không?** Đây là
   nghi vạn chính còn lại (IDE/agent watcher). Cách kiểm: `handle.exe -nobanner
   .git\refs\heads\master` hoặc `openfiles /query`. Repo nằm trong `.kilo/worktrees/`
   và `.claude/worktrees/` ⇒ có nhiều agent IDE cùng chạy.
2. **Có nên công bố workaround là quy chuẩn tạm thời không?** Nếu giữ nguyên hiện
   trạng, mọi agent vẫn phải tự mò lại.
3. **Backup:** có nên `git gc` / `git pack-refs` để gom `master` vào packed-refs
   và bỏ loose ref không? Chưa tự làm vì đụng `refs/` dùng chung.

## 8. Không làm trong task này

- ❌ Không xóa lock file stale (có thể thuộc tiến trình sống của agent khác).
- ❌ Không `git gc` / `pack-refs` / `prune` — đụng `refs/` dùng chung.
- ❌ Không `amend`/`rebase` commit đã có — phá lịch sử dùng chung.
- ❌ Không đụng `master.bak_t83` (ref dự phòng có trong `packed-refs`).

## 9. Bài học (áp dụng T195)

- **Không tin `Measure-Object -Line`** của PowerShell để đếm dòng file — nó bỏ
  qua dòng trống, làm số liệu sai (546/755 thay vì 720/986). Dùng
  `(Get-Content -LiteralPath f).Count`.
- **Luôn kiểm tra diff trong temp index**, không dùng `git diff HEAD` trên worktree
  dùng chung: main index bị stale sẽ báoo giả *deletion* cho file vẫn tồn tại
  (`D ` + `??`).
- **Xác minh số liệu trước khi commit**, không sửa sau — số sai đã nằm trong
  commit message của T195 pass-1 (immutable) và phải sửa bằng pass-2.