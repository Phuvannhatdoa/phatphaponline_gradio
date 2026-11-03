# Quy trình làm việc cho Orca / OpenCode — dự án Đạo Ảnh (visjs-app)

Áp dụng cho mọi task Txxx chạy qua Orca (nơi điều khiển) gọi OpenCode (agent thực thi).
Đây là quy tắc bắt buộc, không có ngoại lệ.

## 0. Luồng Orca → OpenCode

- **Orca** là nơi điều khiển: nhận lệnh từ Admin, chọn task, tạo/giao worktree, gọi OpenCode
  chạy, theo dõi output, và báo lại Admin. Orca không tự sửa code.
- **OpenCode** là agent thực thi: nhận prompt từ Orca kèm đường dẫn worktree cụ thể của task,
  code/sửa file trong đúng worktree đó, chạy test, commit trong worktree, rồi báo kết quả
  (file đã sửa, commit hash, output test) về cho Orca.
- Orca tổng hợp báo cáo của OpenCode và trình Admin. Nếu Admin duyệt QA, **việc merge vào
  main do Claude (vai trò điều phối) quyết định và thực hiện qua `scripts/wt_integrate.py`**
  — không phải Orca, không phải OpenCode.
- Không có bước nào trong luồng này được phép bỏ qua cổng duyệt DB (mục 2) hay cổng merge
  (mục 4).

## 1. Phạm vi làm việc

- Mỗi task chỉ làm trong **worktree của chính task đó** (ví dụ `...\orca\workspaces\visjs-app\T53`
  hoặc `C:\Users\Nam Thien\.claude\worktrees\<task>`), trên nhánh cùng tên task.
- **Không ghi vào cây chính** (`E:\...\visjs-app`, nhánh `truyen-dang-the-pho-clean`). Không sửa
  file ở đó, không tạo file mới ở đó.
- **Không tạo worktree mới** hoặc checkout nhánh khác trong worktree của task khi chưa được
  Admin duyệt.
- **Không dùng** `git reset --hard`, `git clean -fd`, `git stash drop`, `git checkout --`,
  `git restore` trên bất kỳ cây nào. Nếu cần hoàn tác, báo Admin.

## 2. Ghi cơ sở dữ liệu

- DB thật là `Dai_Tang_Kinh/daoanh/data/lineage.db`, đang được editor dùng.
- **Chỉ chạy dry-run** (mặc định của script). Không được chạy `--apply`, không được ghi DB bằng
  bất kỳ cách nào khác.
- Sau dry-run, báo Admin số liệu: số dòng thêm, sửa, xóa; bảng và cột bị đổi.
- Chỉ khi Admin tạo file duyệt `approvals/<Txxx>.approved` thì mới được chạy `--apply`. File
  duyệt phải khớp với hash kết quả dry-run mà Admin đã xem. Không có file duyệt này thì
  `--apply` bị chặn — xem `scripts/check_orca_guard.py::check_approval()`.
- Trước mọi lệnh `--apply`, phải có sao lưu an toàn (sao lưu DB vào `E:\DaoAnh-Backup\db\`,
  không ghi đè).

## 3. Kiểm chứng trước khi báo xong

- Chạy test của task (ví dụ `npm run test:<task>` hoặc `python -m unittest <module>`), ghi lại
  output thật.
- Không báo "xong" nếu test chưa chạy hoặc chưa đạt.
- Ghi số liệu trước và sau khi thay đổi (đếm dòng, quick_check), không chỉ mô tả.

## 4. Commit và bàn giao

- Commit **trong worktree của task**, chỉ các file của task. Không dùng `git add .`.
- Dòng cuối commit: tùy agent thực thi — OpenCode/Claude Haiku ghi
  `Co-Authored-By: Claude Haiku 5.5 <noreply@anthropic.com>` theo chỉ định của Admin cho task đó.
- **Không merge vào main, không push** từ Orca hay OpenCode. Việc merge chỉ do Claude (điều
  phối) thực hiện, sau khi QA đạt, qua `scripts/wt_integrate.py`.
- Báo Admin: danh sách file đã sửa, commit hash, output test, số liệu dry-run, việc còn lại.

## 5. Khi không chắc

- Dừng lại và hỏi Admin. Không tự quyết định ghi DB, xóa dữ liệu, merge, hay đổi cây chính.

## 6. Tóm tắt 6 quy tắc cứng (tham chiếu nhanh)

1. Chỉ làm trong worktree của task — không ghi cây chính, không tạo worktree mới khi chưa
   được duyệt.
2. Không `--apply` DB khi chưa có `approvals/<Txxx>.approved` khớp hash dry-run.
3. Phải chạy test thật và ghi output trước khi báo "xong".
4. Commit trong worktree, không `git add .`, không merge, không push.
5. Merge vào main chỉ do Claude (điều phối) quyết định và thực hiện qua
   `scripts/wt_integrate.py`, sau khi QA đạt.
6. Cấm `git reset --hard`, `git clean -fd`, `git stash drop`, `git checkout --`, `git restore`
   trên mọi cây — cần hoàn tác thì hỏi Admin.
