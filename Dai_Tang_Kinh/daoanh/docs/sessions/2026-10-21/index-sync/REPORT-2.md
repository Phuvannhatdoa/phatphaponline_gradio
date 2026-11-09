# REPORT-2 — Đồng bộ .git/index về HEAD (fix2)

- HEAD: `e09444a35ca64a981ac25166455eca20af1d83bc`
- Admin duyệt: đồng bộ index thật (.git/index) về HEAD.
- Không commit, không reset/checkout/stash/push, không sửa file worktree.

## Baseline (pre-fix2.txt)
```
D	Dai_Tang_Kinh/daoanh/docs/sessions/2026-10-21/rename-t451/do_rename.py
D	Dai_Tang_Kinh/daoanh/docs/sessions/2026-10-21/rename-t451/refs.md
D	Dai_Tang_Kinh/daoanh/tasks/T451-claude-place-name-import.md
```
Đúng 3 dòng như Admin mô tả, không có mục nào khác → tiếp tục.

## Kiểm tra
- `git cat-file -e HEAD:<path>` cho cả 3 path: thành công.
- Cả 3 file tồn tại trên đĩa (`os.path.isfile` = True).

## Thực hiện
1. `git read-tree HEAD` vào index tạm `index-sync/tmp3.index` → `git diff --cached` trên index tạm rỗng.
2. Sao lưu `.git/index` → `index-sync/index.before-fix2.bak` (459857 byte, copy byte, kích thước khớp).
3. Ghi byte `tmp3.index` (460285 byte) vào `.git/index` bằng `write_index.py` (`r+b` + write + truncate). Không lỗi quyền.
4. Xóa `tmp3.index`.

## Kết quả sau khi sync
- `git diff --cached --name-status` (lệnh thường): **RỖNG**.
- 3 file vẫn còn trên đĩa.
- HEAD vẫn `e09444a3...`.

## Ghi chú
- Lần ghi đầu `pre-fix2.txt` bằng redirect `>` của PowerShell tạo UTF-16 (không đọc được). Đã ghi lại bằng `git diff --output` → UTF-8, nội dung xác nhận bằng bytes.
- Backup để hoàn nguyên: `docs/sessions/2026-10-21/index-sync/index.before-fix2.bak` (copy lại vào `.git/index` bằng cùng kỹ thuật nếu cần).
- `write_index.py` còn nằm trong index-sync (công cụ, không đụng git).
