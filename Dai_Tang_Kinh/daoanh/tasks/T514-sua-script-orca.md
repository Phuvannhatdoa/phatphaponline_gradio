---
id: T514
title: "Sửa lỗi nhỏ trong script Orca/tích hợp"
module: Process / Orca
priority: medium
status: pending
depends_on: []
created: 2026-11-03
updated: 2026-11-03
done_when: >
  wt_integrate.py in được thông báo cuối trên Windows (cp1252) không lỗi UnicodeEncodeError,
  check_orca_guard.TASK_ID_RE không nhận ký tự xuống dòng cuối,
  wt_integrate.py nhận nhánh t<số>-<mô tả> (và vẫn nhận wt/<tên>),
  test liên quan đều đạt
---

# T514 — Sửa lỗi nhỏ trong script Orca/tích hợp

## Mục tiêu
Hai lỗi nhỏ đã biết trong script quy trình Orca. Không đổi hành vi nào khác.

## Phạm vi
1. `scripts/wt_integrate.py`: dòng in thông báo cuối gây `UnicodeEncodeError` trên console Windows cp1252. Merge vẫn thành công, chỉ lỗi ở bước in. Sửa để in không lỗi (ví dụ đặt encoding của stdout hoặc thay ký tự không in được).
2. `scripts/check_orca_guard.py`: `TASK_ID_RE = re.compile(r"^T\d+$")` dùng `$` nên chấp nhận ký tự xuống dòng cuối. Sửa dùng `fullmatch` hoặc `\Z`.
3. Thêm hoặc cập nhật test trong `tests/test_check_orca_guard.py` cho trường hợp `"T53\n"` phải bị từ chối.
4. `scripts/wt_integrate.py`: hiện chỉ nhận nhánh `wt/<tên>`. Thêm nhận diện nhánh `t<số>-<mô tả>` (ví dụ `t53-cbeta-content-enhancement`, `t514-sua-script-orca`), không đổi logic merge. Nhánh `wt/<tên>` cũ vẫn chạy bình thường. Thêm test cho cả hai dạng tên và cho tên sai (ví dụ `t-abc`, `T53` không có mô tả) phải bị từ chối.

## Không làm
- Không đổi logic merge, lock, hay bước kiểm tra của `wt_integrate.py`. Chỉ thêm nhận diện tên nhánh.
- Không chạy merge, không ghi DB, không đụng cây chính.

## Quy tắc chạy (bắt buộc)
- Làm trong worktree T514 (nhánh T514). Không ghi cây chính. Không tạo worktree hay nhánh khác.
- Không dùng reset --hard, clean -fd, stash drop, checkout --, restore.
- Chạy test liên quan và ghi output thật. Không báo xong nếu chưa chạy test.
- Commit chỉ các file của task, dòng cuối: `Co-Authored-By: Claude Haiku 5.5 <noreply@anthropic.com>`.
- Không merge vào nhánh chính. Báo lại danh sách file, commit hash và output test để Claude (coordinator) QA.
