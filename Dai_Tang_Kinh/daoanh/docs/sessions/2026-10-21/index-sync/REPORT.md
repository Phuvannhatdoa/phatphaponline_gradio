# REPORT — Unstage index về HEAD (index-sync, 2026-10-21)

Repo root: `visjs-app`. HEAD: `f6d34a633aa491bbf3b97c0fb266b384407b9b43` (không đổi). Không commit, không reset --hard, không checkout, không stash, không push, không xóa file worktree.

## Kết quả ngắn

- **Staged sau:** rỗng (`git diff --cached --name-status` không in gì).
- **Worktree:** không path nào biến mất. 255/255 dòng status-before khớp với đĩa; 9/9 path còn tồn tại.
- **Lệch so với kế hoạch:** staged ban đầu là **20**, không phải 9. Fallback đã đưa toàn bộ index về HEAD, nên **13 mục ngoài danh sách 9 path cũng bị unstage**. Cần Admin xác nhận (xem mục Rủi ro).

## Bước 1 — Baseline

| File | Nội dung |
|---|---|
| head.txt | `f6d34a633aa491bbf3b97c0fb266b384407b9b43` |
| staged-before.txt | 20 mục staged |
| status-before.txt | 255 dòng |

## Bước 2 — Phân tích 9 path

Xem `analysis.md`. Tóm tắt: cả 9 path có trong HEAD (blob) và tồn tại trong worktree. 7 path staged (a–g), 2 path (h, i) không staged.

## Bước 3 — Unstage

1. `git reset HEAD -- Dai_Tang_Kinh/daoanh/docs/sessions/2026-10-21/T263-damaged/2026-10-08_T263_h3_conflicts.tsv` → in danh sách unstage nhưng kết thúc bằng `fatal: Could not write new index file.` Index **không đổi** (vẫn 20 mục staged). Dừng, không lặp lại.
2. Fallback AGENTS §17:
   - (i) Sao lưu `.git/index` → `index-sync/index.original.bak` (459 593 byte) và bản làm việc `index-sync/index.tmp`.
   - (ii) `cmd /c "set GIT_INDEX_FILE=...index-sync/index.tmp&&git read-tree HEAD"` → không lỗi. `GIT_INDEX_FILE=index.tmp git diff --cached --name-status` rỗng.
   - (iii) `write_index.py` (open `r+b` + write + truncate) ghi byte `index.tmp` vào `.git/index`: `src_len=459593`, `dst_len_after=459593`, `match=True`. SHA-1 trước `3b5b61bd…`, sau `74ddad48…`.
   - (iv) `git diff --cached --name-status` → rỗng.

Không dùng `git reset` không path, không `git checkout`. Không dùng %TEMP%.

## Bước 4 — Xác minh

| Kiểm tra | Kết quả |
|---|---|
| `git diff --cached --name-status` | rỗng (đạt) |
| `git rev-parse HEAD` | không đổi (đạt) |
| `verify_worktree.py` → status-before (255 dòng) vs đĩa | **mismatch_count=0** (đạt) |
| 9 path tồn tại trên đĩa | 9/9 `exists=True` (đạt) |
| `git ls-files -s` + `git diff --name-only` có pathspec (ví dụ T100) | hoạt động, cho thấy đúng trạng thái đã biết |

**Lưu ý về lệnh tự báo cáo bị hỏng im lặng:**
- `status-after.txt` (`git status --short`) **rỗng**.
- `worktree-diff-after.txt` (`git diff --name-status` không pathspec) **rỗng**.
- Đây là lỗi im lặng đã được AGENTS §17 ghi nhận, không phải bằng chứng là worktree trống. Bằng chứng thay thế là `verify-worktree.txt` (script đối chiếu đĩa).
- Trạng thái ` M` mong đợi cho e/f/g chưa xác minh bằng `git status`.

## Bảng 9 path (trả về)

| # | Path | Trong HEAD | Trong worktree | Đã unstage |
|---|---|---|---|---|
| a | docs/sessions/2026-10-21/T263-damaged/2026-10-08_T263_h3_conflicts.tsv | có | có | có (từ D) |
| b | docs/sessions/2026-10-21/T263-damaged/2026-10-08_T263_h3_conflicts_summary.tsv | có | có | có (từ D) |
| c | docs/sessions/2026-10-21/permission/opencode.json.before | có | có | có (từ D) |
| d | tasks/T449-audit-h3-evidence-guard.md | có | có | có (từ D) |
| e | .opencode/opencode.json | có | có | có (từ M) |
| f | docs/ROLLBACK.md | có | có | có (từ M) |
| g | docs/tasktodo.md | có | có | có (từ M) |
| h | docs/sessions/2026-10-20_BUG-pl-id-404.md | có | có | không cần (không staged) |
| i | docs/sessions/2026-10-20_BUG-placevn-baseurl.md | có | có | không cần (không staged) |

(Tất cả path ở tiền tố `Dai_Tang_Kinh/daoanh/`.)

## Rủi ro và việc Admin cần quyết

1. **13 mục ngoài 9 path đã bị unstage** (nằm trong danh sách staged-before nhưng không thuộc 9 path):
   - `.opencode/agents/daoanh-debugger.md`, `daoanh-qa.md`, `tich-hop.md`
   - `app.py`
   - `docs/Handoff-2026-10-21-T448-bugfix-batch.md` (D)
   - `docs/sessions/2026-10-21/T406/T406_QA_NOTE.md` (D), `T412/T412_VERIFY_REPORT.md` (D), `T416/T416_REPORT.md` (D)
   - `scripts/t416_add_autocomplete_indexes.py` (D)
   - `tasks/T406-flyto-nan-error.md`, `T412-lineage-node-ttl-full-name.md`, `T416-optimize-autocomplete-api-backend.md`
   - `tasks/T448-fix-bug-batch-ui-gis.md` (D)

   Admin duyệt "các mục staged cũ về unstaged" nên đây khớp ý định, nhưng danh sách 9 path đã định rõ phạm vi. Nếu Admin muốn giữ 13 mục này ở staged, khôi phục bằng cách ghi `index.original.bak` vào `.git/index` theo đúng phương pháp (iii) rồi unstage chỉ 9 path bằng cách khác (cần làm lại với Admin).
2. **Nguy cơ không đọc được `git status`**: không thể dùng `git status` để xác nhận trạng thái sau. Dùng `verify-worktree.txt` và `git ls-files`/`git diff -- <pathspec>` thay thế.
3. **Các file tạm nằm trong repo worktree**: `index-sync/index.original.bak`, `index-sync/index.tmp`, `write_index.py`, `verify_worktree.py`. Đây là file mới chưa track (không commit). Tránh `git add` thư mục `docs/`; xóa sau khi Admin xác nhận. `index.original.bak` là byte gốc, giữ làm đường rollback.
4. Chưa test pipeline/test code; thay đổi chỉ là index.

## Rollback (nếu cần hoàn tác index)

Chạy lại phương pháp (iii) với nguồn là `index-sync/index.original.bak` thay cho `index.tmp`, rồi kiểm `git diff --cached --name-status` ra đúng 20 mục như staged-before.txt. Không có thay đổi nào của worktree hay HEAD cần hoàn tác.

## File báo cáo (`docs/sessions/2026-10-21/index-sync/`)

| File | Vai trò |
|---|---|
| head.txt | HEAD trước |
| staged-before.txt | 20 mục staged trước |
| status-before.txt | git status trước (255 dòng) |
| status-after.txt | rỗng (git status hỏng im lặng, xem trên) |
| worktree-diff-after.txt | rỗng (git diff không pathspec hỏng im lặng) |
| analysis.md | bảng 9 path |
| verify-worktree.txt | kết quả đối chiếu đĩa: mismatch_count=0 |
| index.original.bak | index gốc (rollback) |
| index.tmp | index đã read-tree HEAD (nguồn ghi vào .git/index) |
| write_index.py, verify_worktree.py | script đã dùng |
| REPORT.md | file này |
