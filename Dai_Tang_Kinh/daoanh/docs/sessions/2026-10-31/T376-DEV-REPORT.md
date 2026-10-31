# T376 — DEV-REPORT (2026-10-31)

Task: `tasks/T376-tasktodo-archive-done.md`. Trạng thái: **in_progress** (chưa DONE).

Nguồn số liệu dùng trong báo cáo này: `tasks/T376-tasktodo-archive-done.md` (frontmatter `outcome`),
`docs/sessions/2026-10-13/housekeeping/README.md`, `docs/sessions/2026-10-13/housekeeping/
progress_counts_before-T376.txt` + `progress_counts_after-T376.txt`, và
`docs/qa_reports/QA-2026-10-31-T376.md` (báo cáo tester, kết luận FAIL). Mỗi số liệu dưới đây ghi rõ
nguồn; không dùng số liệu nào ngoài các file này.

## (a) Việc đã làm ngày 2026-10-13

Theo `outcome` trong `tasks/T376-tasktodo-archive-done.md`: chuyển 74 mục (114 dòng) có task file
`status: done` + dòng trạng thái DONE từ `docs/tasktodo.md` sang `docs/archive/tasktodo-done-2026.md`;
thêm dòng trỏ ở đầu `tasktodo.md`. Dung lượng `tasktodo.md`: 246.439 → 137.091 byte (615 → 434 dòng).
Bảo toàn nội dung: tổng 196.791 ký tự (trừ khoảng trắng) = 109.126 (tasktodo) + 87.665 (archive).
(Nguồn: `tasks/T376-tasktodo-archive-done.md` dòng `outcome:`.)

## (b) Sự cố 12:57–13:00

Theo `docs/sessions/2026-10-13/housekeeping/README.md` mục "Sự cố 12:57–13:00": một phiên khác chuyển
worktree dùng chung sang nhánh orphan `data-authority-lightweight` (7f4e654) ⇒ mọi file tracked của
`master` biến khỏi đĩa, bao gồm `docs/tasktodo.md`. Bảng mô tả ngắn của README ghi T376 "xong, **tasktodo.md
mất do sự cố — chạy lại bằng reapply**" (`reapply_after_restore.py`), cùng cơ chế với T374 (AGENTS/CLAUDE
mất) và T378 (app.py mất). (Nguồn: README.md dòng 13 và mục "Sự cố 12:57–13:00".)

## (c) Bằng chứng số task trước/sau

`progress_counts_before-T376.txt` và `progress_counts_after-T376.txt` (cùng thư mục housekeeping) có nội
dung giống hệt nhau: `tasks 295 {'blocked': 28, 'done': 157, 'in_progress': 33, 'pending': 77}`,
`total_progress 72`, `endpoints_compare 331`. (Nguồn: hai file `.txt` nêu trên, đọc trực tiếp bằng `cat`
trong phiên này — không chạy lại `build_progress_data.py` để không ghi đè `progress_data.json` hiện tại
của worktree.)

## (d) Kết quả tester 2026-10-31

Theo `docs/qa_reports/QA-2026-10-31-T376.md` mục "Kiểm bảo toàn": 407 dòng không trống của bản sao trước
T376 (`tasktodo.md.bak-before-T376`) → 394 dòng còn có trong `tasktodo.md` hiện tại hoặc archive; 13 dòng
thiếu đều là block trạng thái housekeeping T374/T375/T376/T377/T378, không phải mục DONE nào bị mất.
Trong phạm vi L1 của lần sửa hôm nay, 4 block T374/T376/T377/T378 (9 dòng, do mỗi block có `<!--START-->`
+ nội dung + `<!--END-->`) đã được khôi phục vào `docs/tasktodo.md`. Dòng 602 của block T375 cũ (1 dòng
còn thiếu trong 13 dòng QA liệt kê) **không** khôi phục — vì T375 đã `status: done` và nội dung đã nằm
trong `docs/archive/tasktodo-done-2026.md` (không phải mục bị mất, theo yêu cầu công việc rõ ràng). (Nguồn:
QA-2026-10-31-T376.md mục `commands_run` dòng "Kiểm bảo toàn".)

## (e) Thay đổi hôm nay (2026-10-31)

- Sao lưu `docs/tasktodo.md` → `docs/sessions/2026-10-31/tasktodo.md.bak-before-t376-L1` (trước khi sửa).
- Thêm nguyên văn 4 block trạng thái vào **cuối** `docs/tasktodo.md`, lấy từ
  `docs/sessions/2026-10-13/housekeeping/tasktodo.md.bak-before-T376`:
  - dòng 597–599 → `<!-- T374:START -->` ... `<!-- T374:END -->`
  - dòng 605–607 → `<!-- T376:START -->` ... `<!-- T376:END -->`
  - dòng 609–611 → `<!-- T377:START -->` ... `<!-- T377:END -->`
  - dòng 613–615 → `<!-- T378:START -->` ... `<!-- T378:END -->`
  (không chép dòng 601–603 của T375).
- Không sửa, không xóa dòng nào khác trong `docs/tasktodo.md` (kiểm bằng `diff` với bản backup: chỉ có
  dòng thêm vào cuối, không có dòng bị đổi/xóa — xem mục kiểm tra trong báo cáo gửi Admin).
- Viết file DEV-REPORT này.
- Chạy `npm run guard` và `npm run dup:ids` (xem log riêng gửi kèm báo cáo chat) — cả hai PASS, không liên
  quan đến thay đổi L1/L2 (guard kiểm SSOT repo root; dup:ids kiểm ID task trùng).

## (f) Vì sao archive hiện có 80 block thay vì 74

Theo `docs/qa_reports/QA-2026-10-31-T376.md` mục `files_changed`: `docs/archive/tasktodo-done-2026.md`
tại thời điểm T376 chạy (2026-10-13, commit a4397c2a) có 74 block, nhưng hiện tại (worktree) có 80 block —
QA ghi "script đã được chạy lại sau này, thêm T479 (2026-10-27...)" và "không xác định được session nào
chạy lại, không quy cho T376 2026-10-13". Vậy việc archive có 80 block là do **một session khác chạy lại
quy trình archive sau ngày 2026-10-13**, không phải lỗi hoặc công việc của T376 trong lần sửa hôm nay.
(Nguồn: QA-2026-10-31-T376.md dòng `files_changed`.)

## (g) Vì sao không tái lập được phép so ký tự (2)

Theo `docs/qa_reports/QA-2026-10-31-T376.md` mục `done_when (2)`: phép so ký tự
196.791 = 109.126 + 87.665 (ghi trong `outcome` của task file, mục (a) trên) **không tái lập được** trong
lần kiểm 2026-10-31, vì cả `docs/tasktodo.md` và `docs/archive/tasktodo-done-2026.md` đã bị một hoặc nhiều
session khác sửa tiếp sau 2026-10-13 (archive từ 74 → 80 block, như mục (f); tasktodo cũng đã có nhiều
block mới của các task sau T481 v.v.). Lần sửa hôm nay (L1) chỉ thêm 4 block housekeeping vào cuối file,
không chạy lại phép so ký tự này, vì phạm vi công việc không yêu cầu và không tái lập được một cách có ý
nghĩa trên trạng thái file hiện tại. (Nguồn: QA-2026-10-31-T376.md dòng `done_when (2)`.)

## (h) Trạng thái commit

Chờ Admin quyết định. Không ghi SHA trong báo cáo này hoặc trong task file (giữ `<sha_T376>` placeholder
như hiện trạng). Theo QA (`done_when (4)`): không có commit riêng cho T376; thay đổi gốc 2026-10-13 nằm
gộp trong commit `a4397c2a` (3191 file) — revert commit đó sẽ xóa luôn các file khác không liên quan.
Thay đổi L1/L2 hôm nay (2026-10-31) **chưa commit**; theo chỉ định công việc, không chạy
`git add/commit/reset` trong lần sửa này.

## (i) Cách hoàn tác

1. Chép `docs/sessions/2026-10-13/housekeeping/tasktodo.md.bak-before-T376` → `docs/tasktodo.md` (khôi
   phục toàn bộ về trạng thái trước T376 ngày 2026-10-13 — bản này có 615 dòng, gồm cả các mục DONE chưa
   archive).
2. Sau đó bỏ các block T374/T376/T377/T378 vừa thêm hôm nay nếu không muốn giữ (4 block ở cuối file, mỗi
   block có marker `<!-- Txxx:START -->` ... `<!-- Txxx:END -->`, dễ tìm bằng `grep -n`).
3. **Cẩn thận**: `docs/tasktodo.md` hiện đang có thay đổi của nhiều session khác (theo QA, 50 file trong
   worktree thay đổi, phần lớn không phải của T376) — bước 1 (chép đè toàn bộ file) sẽ làm mất mọi thay đổi
   khác chưa commit của `docs/tasktodo.md`, không chỉ của T376. Nên đối chiếu `git diff` trước khi chép đè,
   hoặc chỉ xóa đúng 4 block vừa thêm (cách an toàn hơn, không ảnh hưởng phần khác của file).
4. Bản sao vừa tạo trong lần sửa hôm nay: `docs/sessions/2026-10-31/tasktodo.md.bak-before-t376-L1` (trạng
   thái `docs/tasktodo.md` ngay trước khi thêm 4 block L1) — dùng bản này để hoàn tác riêng phần L1 mà
   không ảnh hưởng gì khác, vì nó chụp đúng trạng thái file tại thời điểm bắt đầu sửa hôm nay.

## Việc KHÔNG làm trong lần sửa này (đúng theo chỉ định công việc)

- Không điền placeholder `<sha_T376>`.
- Không sửa `docs/ROLLBACK.md`.
- Không `git add/commit/reset`.
- Không ghi DB.
- Không đánh DONE, không đổi `status` trong frontmatter `tasks/T376-tasktodo-archive-done.md`.
