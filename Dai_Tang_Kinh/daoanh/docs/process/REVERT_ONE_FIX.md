# Hoàn tác MỘT bản sửa (revert one fix) — quy trình chuẩn

> T374, 2026-10-13. Bổ sung cho `AGENTS.md` §14 (commit/revert an toàn), §17 (worktree dùng chung)
> và `docs/ROLLBACK.md` (bảng commit + backup DB). Tài liệu này chỉ trả lời một câu:
> **làm sao để mỗi bản sửa quay lại được đúng một mình nó, không kéo theo việc của người khác.**

## 1. Nguyên tắc

1. **Một việc = một commit.** Mỗi task/mục có commit riêng, message bắt đầu bằng ID:
   `T375: …`, `fix(T378): …`. Không gộp hai việc vào một commit.
2. **Stage theo đường dẫn tường minh.** Chỉ `git add -- <file1> <file2>`.
   Cấm: `git add -A`, `git add .`, `git add <thư mục>`, `git commit -a` — worktree có nhiều phiên song song.
3. **Kiểm trước khi commit:** `git diff --cached --name-status` phải đúng danh sách file của việc đó.
   Có file lạ đã stage sẵn (của phiên khác) ⇒ dùng commit theo pathspec: `git commit -m "…" -- <file…>`.
4. **Kiểm sau khi commit:** `git show --stat HEAD` (hoặc `git diff --name-status HEAD~1 HEAD`) — thấy
   `D` hay file ngoài phạm vi ⇒ hoàn tác ngay (mục 3).
5. **Ghi SHA lại:** cột `revert:` trong task file + một dòng trong `docs/ROLLBACK.md` + Handoff.
6. **Dữ liệu ngoài git (DB, TTL, file bị ignore) không revert được bằng git.** Phải có backup/manifest riêng
   (xem `docs/process/HARNESS_WORKFLOW.md` §5) và ghi lệnh khôi phục cạnh SHA.

## 2. Commit một việc

```bash
cd <visjs-app>                                   # luôn chạy git từ repo root (AGENTS §13)
git diff --cached --name-status                   # phải rỗng hoặc chỉ có file của mình
git add -- Dai_Tang_Kinh/daoanh/<file1> Dai_Tang_Kinh/daoanh/<file2>
git diff --cached --name-status                   # đúng danh sách? (rỗng = add thất bại, xem AGENTS §14)
git commit -m "T<id>: <mô tả>" -- Dai_Tang_Kinh/daoanh/<file1> Dai_Tang_Kinh/daoanh/<file2>
git show --stat HEAD                              # xác nhận
```

Di chuyển file:
- File được git theo dõi: `git mv -- <cũ> <mới>` (hoặc `mv` rồi `git add -- <cũ> <mới>` — git ghi nhận cả
  xoá lẫn thêm, vẫn chỉ hai đường dẫn đó).
- File không được theo dõi / bị ignore: chỉ `mv`, và **bắt buộc** ghi MANIFEST (đường dẫn gốc → mới) vì git
  không giữ được chúng.

## 3. Hoàn tác đúng một việc

```bash
git log --oneline --grep "T<id>"                  # tìm SHA của việc cần hoàn tác
git show --stat <sha>                             # xem lại phạm vi
git revert --no-edit <sha>                        # tạo commit đảo ngược, giữ lịch sử
git show --stat HEAD                              # xác nhận chỉ đảo đúng các file đó
```

- Nhiều commit cho cùng một việc: revert **từ mới đến cũ** — `git revert --no-edit <sha_moi> <sha_cu>`.
- Xung đột khi revert (file đã bị sửa tiếp sau đó): dừng, `git revert --abort`, báo Admin; không tự gộp.
- Cấm `git reset --hard`, `git checkout -- <file nguyên>`, force push để "hoàn tác".

## 4. Khi chưa commit được (index bị khoá, phiên không có quyền git)

Nếu không commit được, bản sửa vẫn phải hoàn tác được bằng file:
1. Sao lưu file trước khi sửa vào `docs/sessions/YYYY-MM-DD/…/*.bak-before-T<id>`.
2. Di chuyển file thì ghi `MANIFEST.md` (đường dẫn gốc, đường dẫn mới, lý do).
3. Ghi sẵn lệnh commit theo pathspec cho từng việc (ví dụ `docs/sessions/2026-10-13/housekeeping/commit_plan.sh`)
   để Admin/agent có quyền chạy sau — mỗi việc vẫn là một commit riêng.

## 5. Kiểm nhanh

```bash
git diff --cached --name-status      # trước commit
git show --stat HEAD                 # sau commit
git log --oneline -5                 # HEAD có dịch do phiên khác không? (AGENTS §17)
```
