---
id: G208
title: Quy trình commit/revert AN TOÀN khi ghi .git/index bị Windows chặn
status: done
created: 2026-10-02
commit: 6230c40
revert: "git revert --no-edit <sha>"
---

# Quy trình commit/revert AN TOÀN (bắt buộc theo khi gặp lỗi index)

## Triệu chứng
```
fatal: unable to write new index file
fatal: Unable to create '.../.git/index.lock': File exists.
```
Đôi khi git **không** báo lỗi nhưng `git diff --cached` vẫn **RỖNG** — tức đã
ghi `index.lock` xong nhưng bước rename `index.lock` → `index` thất bại, và
`index` cũ không đổi.

## Nguyên nhân
Windows chặn bước **rename** trong `.git/` (antivirus, indexer, hoặc ổ đĩa).
Không liên quan tới nội dung file, không phải hết chỗ.

## 1) KIỂM TRA TRƯỚC KHI LÀM BẤT CỨ GÌ
```bash
git status --short -- <file>       # đọc được index ⇒ repo ổn
git diff --cached --name-only      # phải in RA file vừa add
```
> **`git diff --cached` rỗng sau `git add` ⇒ add KHÔNG thành công.** Không được
> coi là xong.

## 2) CÁCH LÀM ĐÚNG — index tạm + `read-tree` (BẮT BUỘC)

```bash
# a) tạo index tạm, baseline = ĐÚNG commit hiện tại
export GIT_INDEX_FILE="$PWD/.git/wt_tmp_index"
git read-tree HEAD              # <-- BẮT BUỘC read-tree, KHÔNG copy .git/index

# b) add đúng những file cần commit
git add -- path/a.md path/b.py

# c) XÁC MINH trước khi commit
git diff --cached --name-only   # phải ĐÚNG danh sách file dự kiến, không thừa

# d) commit
git commit -m "..."

# e) dọn
unset GIT_INDEX_FILE
rm -f .git/wt_tmp_index .git/wt_tmp_index.lock
```

### ⚠️ TUYỆT ĐỐI KHÔNG
```bash
cp .git/index .git/wt_tmp_index    # SAI — index stale sẽ làm commit XOÁ file
```
Đây chính là nguyên nhân sự cố đã xảy ra trong phiên 2026-10-01: commit sai
xoá 3 file (`scripts/t207_fix_db_mojibake.py`, `scripts/probe_t207_fts.py`,
`tests/test_t207_db_mojibake.py`) + session log, vì index thật đã cũ hơn HEAD.
Khôi phục bằng `git read-tree <commit-truoc>` rồi commit lại (xem mục 4).

## 3) NẾU `git commit` VẪN FAIL (kể cả với index tạm)
Dùng plumbing — không cần rename index:
```bash
export GIT_INDEX_FILE="$PWD/.git/wt_tmp_index"
git read-tree HEAD
git add -- <file>
TREE=$(git write-tree)
NEW=$(git commit-tree "$TREE" -p HEAD -F /path/to/msg.txt)
git update-ref refs/heads/master "$NEW" HEAD
unset GIT_INDEX_FILE
```

## 4) KHÔNG PHẢI DÒNG TRONG `git diff --name-status HEAD~1 HEAD`
Sau **mỗi** commit, kiểm tra ngay:
```bash
git diff --name-status HEAD~1 HEAD      # chỉ được là file bạn cố ý
git log --oneline -2
```
Nếu thấy `D` cho file không mong muốn → hoàn tác ngay:
```bash
export GIT_INDEX_FILE="$PWD/.git/wt_fix_index"
git read-tree <commit-truoc>          # đúng nội dung bạn muốn
git commit -m "Revert \"<commit sai>\""
unset GIT_INDEX_FILE
```

## 5) REVERT MỘT BUG FIX (yêu cầu bắt buộc của Admin)
Mỗi bug fix phải revert được thuận tiện. Thứ tự chuẩn:
1. **Code/docs**: `git revert --no-edit <sha>` (1 lệnh, không cần chỉnh tay).
2. **DB additive** (thêm cột/bảng): script có `--revert` ⇒ `DROP COLUMN`,
   **không mất dữ liệu**. Ưu tiên thiết kế migration theo hướng này.
3. **DB sửa giá trị hàng loạt**: `--revert` khôi phục từ **snapshot từng ô**
   (`data/backups/tNNN_snapshot_*.json`) hoặc từ file backup DB.
4. **TTL/file không git track**: backup file-level + `scripts/tNNN_*.py --revert <dir>`.

Xem bảng chi tiết từng task ở `docs/ROLLBACK.md`.

## 6) VÌ SAO CODE NÊN LÀM ADDITIVE
| Kiểu | Revert | Rủi ro |
|------|--------|--------|
| Thêm cột/bảng (`ADD COLUMN`) | `DROP COLUMN` | **0** — không mất dữ liệu |
| Ghi lại khoá/summary dẫn xuất | `UPDATE` lại từ snapshot | Thấp |
| Xoá hàng loạt | Phải restore từ backup | Cao |
| `ALTER` thu hẹp cột | Cần copy bảng | Rất cao |

T208 là ví dụ: `key_norm` **không bị đụng tới**, chỉ thêm `key_norm_alt` ⇒
revert là `DROP COLUMN`, an toàn tuyệt đối.