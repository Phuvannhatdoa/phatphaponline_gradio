# Bảng phân tích 9 path (index-sync, 2026-10-21)

HEAD = `f6d34a633aa491bbf3b97c0fb266b384407b9b43` (không đổi trước/sau).
Kiểm HEAD bằng `git cat-file -t HEAD:<path>` → `blob` cho cả 9 path.
Kiểm worktree bằng `Test-Path` → `True` cho cả 9 path.

| # | Path (tiền tố `Dai_Tang_Kinh/daoanh/`) | Trong HEAD | Trong worktree | Staged trước (`git diff --cached`) | Trạng thái sau unstage |
|---|---|---|---|---|---|
| a | docs/sessions/2026-10-21/T263-damaged/2026-10-08_T263_h3_conflicts.tsv | có (blob) | có | D (xóa khỏi index) | đã unstage → khớp HEAD |
| b | docs/sessions/2026-10-21/T263-damaged/2026-10-08_T263_h3_conflicts_summary.tsv | có (blob) | có | D | đã unstage → khớp HEAD |
| c | docs/sessions/2026-10-21/permission/opencode.json.before | có (blob) | có | D | đã unstage → khớp HEAD |
| d | tasks/T449-audit-h3-evidence-guard.md | có (blob) | có | D | đã unstage → khớp HEAD |
| e | .opencode/opencode.json | có (blob) | có | M | đã unstage → khớp HEAD (worktree vẫn sửa, dự kiến ` M`) |
| f | docs/ROLLBACK.md | có (blob) | có | M | đã unstage → khớp HEAD (worktree vẫn sửa, dự kiến ` M`) |
| g | docs/tasktodo.md | có (blob) | có | M | đã unstage → khớp HEAD (worktree vẫn sửa, dự kiến ` M`) |
| h | docs/sessions/2026-10-20_BUG-pl-id-404.md | có (blob) | có | không staged | không đổi |
| i | docs/sessions/2026-10-20_BUG-placevn-baseurl.md | có (blob) | có | không staged | không đổi |

## Ghi chú đối chiếu với kỳ vọng

- Kỳ vọng ban đầu "9 mục staged" **sai**: thực tế có **20 mục staged**. Trong 20 mục đó chỉ 7 nằm trong 9 path được giao (a–g). h và i vốn không staged.
- 13 mục staged ngoài danh sách 9 path (xem REPORT.md) cũng bị unstage, vì fallback AGENTS §17 bước (ii) `git read-tree HEAD` đưa toàn bộ index về HEAD. Đây là hệ quả, không phải lựa chọn có chủ đích theo từng path.
- Cột "sau unstage" suy ra từ index logic. Không xác minh bằng `git status` vì lệnh này hỏng im lặng trên máy này (status-after.txt rỗng, xem REPORT.md).
