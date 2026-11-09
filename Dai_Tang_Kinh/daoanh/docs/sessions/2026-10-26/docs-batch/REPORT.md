# REPORT — docs-batch 2026-10-26 (không commit file này)

## Kết quả nhanh
- PARENT: `e4fbc5baac4b4db4ae73e615de65b7d6ea632c7b`
- NEW: `9bf4c021d042f3b2e03a361dea0d6539f8819958` (HEAD hiện tại)
- Commit: `docs: T435 xac nhan DONE (BUG-048) + T453 chot ban ghi moi + docs` — 2 file, +3 dòng, 0 xoá.
- Chỉ commit được 2/7 mục yêu cầu. 3 task (T436/T437/T438) và 4 task (T454–T457) không đủ điều kiện blob-only (xem dưới).

## Bước 0 — đồng bộ index thật
- Baseline `pre-index.txt`: 4 mục staged cũ (`M` daoanh-qa.md, tich-hop.md, docs/bugs.md, verify_design_compliance.py) — **của phiên khác**.
- Backup byte: `index.before.bak`. Sau khi ghi index tạm (read-tree HEAD) vào `.git/index`: `git diff --cached --name-status` rỗng.
- Hệ quả: 4 mục staged cũ đã bị bỏ khỏi index. Nội dung worktree của 4 file đó KHÔNG đổi. Ai cần staged lại phải `git add` có chủ đích.

## Bảng file đã commit

| File | Loại | Nội dung thay đổi |
|---|---|---|
| `Dai_Tang_Kinh/daoanh/tasks/T435-bug048-claude-column-no-count.md` | M (+2) | dòng trống + "Admin xác nhận DONE (2026-10-26)" → docs/T435_BUG048_FINAL_REPORT.md (BUG-048) |
| `Dai_Tang_Kinh/daoanh/docs/tasktodo.md` | M (+1) | 1 dòng ghi chú chốt trong khối T453 (không đụng phần khác) |

## Bước 1 — 4 file task BUG-048..051

| Task | Đường dẫn thực tế | Trạng thái | Hành động |
|---|---|---|---|
| T435 | `tasks/T435-...md` (tracked) | Chưa có dòng DONE ở HEAD | **Đã commit** → BUG-048 |
| T436 | `tasks/backup/T436-bug049-etl-pass-button-error.md` | **Không có ở HEAD** (untracked). Worktree đã có dòng DONE (dòng 80) | **BỎ QUA**, báo lại |
| T437 | `tasks/backup/T437-bug050-namevimap-stuck-loading.md` | Không có ở HEAD (untracked). Worktree có dòng DONE (dòng 189) | **BỎ QUA**, báo lại |
| T438 | `tasks/backup/T438-bug051-places-lineage-arrows-missing.md` | Không có ở HEAD (untracked). Worktree có dòng DONE (dòng 59) | **BỎ QUA**, báo lại |

Lý do không dựng blob T436–T438: không có blob HEAD; commit = thêm file untracked nguyên khối, tức là nuốt WIP phiên khác. Không sửa worktree.

Lưu ý: T435 ở worktree đang **bị xoá** (`git diff HEAD` = −68 dòng), đây là WIP phiên khác (có thể di chuyển vào `tasks/backup/`). Commit dựng từ blob HEAD nên không nuốt việc xoá đó; nhưng trạng thái worktree T435 vẫn cần chủ sở hữu xử lý.

Báo cáo đích BUG-049/050/051 (`docs/BUG-049_...`, `docs/T436_T437_VERIFY_FIX_REPORT.md`, `docs/BUG-051_...`) cũng đều là untracked — chỉ T435→`docs/T435_BUG048_FINAL_REPORT.md` được trỏ tới trong commit, file này cũng untracked (tồn tại ở worktree). Cần Admin/agent đưa báo cáo vào git nếu muốn link resolve từ lịch sử.

## Bước 2 — T453: bản ghi mới nhất

| Nguồn | mtime (worktree) | git log | Nội dung |
|---|---|---|---|
| `docs/tasktodo.md` khối T453 — **worktree (WIP)** | 2026-10-26 14:46 | commit HEAD 2026-10-25 11:48 | Ghi "(A) import XONG, (B) search HOME chờ duyệt" — **cũ** (mốc 2026-10-22 ~06:00) |
| `docs/tasktodo.md` khối T453 — **HEAD** | — | — | "🔄 chờ Admin xác nhận DONE", đủ 5.747 bộ, backup 152039 (mốc 2026-10-22 15:20) |
| `tasks/T453-dila-catalog-a-import-vi.md` (untracked) | 2026-10-26 13:50 | không có (untracked) | Nhật ký tới **2026-10-25 16:00** + Admin Notes **2026-10-25 18:33**; frontmatter `status: done`; "Admin chưa xác nhận DONE" |

**Kết luận (bản ghi mới nhất theo nội dung có mốc thời gian):** file task `tasks/T453-dila-catalog-a-import-vi.md` — (A) và (B) đã xong, toàn bộ 26 tạng đã nạp (5.747 bộ), thẻ người/kinh/"Xem tất cả"/đầy đủ thông tin đã làm; QA độc lập ĐẠT; **chờ Admin xác nhận DONE**.

Lưu ý về mtime: tasktodo.md (worktree) có mtime mới hơn, nhưng khối T453 trong worktree là bản **cũ** — file có mtime mới hơn không có nghĩa khối T453 mới hơn. Bản ghi mới hơn là file task (mốc nội dung 2026-10-25 18:33).

Chỉnh sửa đã commit: khối T453 của HEAD đã khớp trạng thái (chờ Admin DONE). Chỉ thêm ghi chú chốt (1 dòng) nêu nguồn và mốc.

Không sửa khối T453 trong worktree (WIP, khác HEAD). Cần chủ sở hữu tasktodo.md đồng bộ lại khối đó (đang ghi "(B) chờ duyệt").

## Bước 3 — T454–T457 (mục "## Mô tả")

| Task | Trạng thái file | Hành động |
|---|---|---|
| T454 | untracked, không có "## Mô tả" | **Không commit**. Nháp trong `mota-drafts.md` |
| T455 | untracked, không có "## Mô tả" | **Không commit**. Nháp |
| T456 | untracked, không có "## Mô tả" | **Không commit**. Nháp |
| T457 | untracked, **đã có** "## Mô tả" (dòng 31) | Không cần chèn. Ghi chú bổ sung nêu trong nháp |

Câu hỏi Admin trong nháp: T454→Q5 · T455→Q3a/b/c · T456→Q4a/b + Q1 (Gate 0, chặn T456) · T457→Q2a/b/c (trong n4-plan, chưa có đáp án). Không đổi status, done_when hay nội dung cũ.

## Bước 4 — commit
- Lặp CAS: 1/3 lần, ref `refs/heads/truyen-dang-the-pho-clean` khớp PARENT, ghi file trực tiếp (không `update-ref`, không `os.replace`).
- `git diff --cached --numstat` trước commit: tasktodo 1+/0−; T435 2+/0− (trong đó 1 dòng trống).
- Index thật sau commit: đồng bộ bằng bytes (`read-tree NEW` → ghi tại chỗ). `git diff --cached --name-status` → **rỗng**.
- `git show --stat 9bf4c021...` → 2 file, 3 insertions.
- `git rev-parse HEAD` == `9bf4c021...`.

## dup:ids
`python -X utf8 scripts/build_progress_data.py --check-dup-ids` → `[OK] Không có task ID trùng thật.` (5 INFO X-superseded, 1 INFO T199 docs phụ; không lỗi).

## File tạm / scratch (untracked, không commit)
- `step0.py`, `inspect_t453.py`, `build_commit.py`: script đã chạy (không có lệnh git ngoài danh sách).
- `pre-index.txt`, `index.before.bak`: baseline và backup index gốc (để khôi phục nếu cần).
- `mota-drafts.md`: nháp mục Mô tả cho T454–T456.
- `tmp.index`, `sync.index`: đã xoá.

## Rủi ro còn lại
1. Phiên khác có WIP trên `tasktodo.md` và `T435` (worktree). Khi họ `git add` file đó, có thể đưa lại trạng thái cũ, do worktree khác HEAD mới. Cần báo chủ sở hữu.
2. 4 mục staged cũ (daoanh-qa.md, tich-hop.md, bugs.md, verify_design_compliance.py) đã bị bỏ khỏi index (worktree không đổi). Có thể cần `git add` lại có chủ đích.
3. Báo cáo BUG-049/050/051 và T435 report, cùng 7 task file (T436–T438, T453, T454–T457) vẫn untracked. Lịch sử git không có các file này.
4. Chưa chạy `npm run pipeline` (không có thay đổi code; chỉ docs).
