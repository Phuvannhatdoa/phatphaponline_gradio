# Lệnh lịch chạy cho agent điều phối Hermes

> **⛔ ĐÃ HUỶ CHẠY THEO LỊCH (Admin 2026-10-20 04:01):** *"hủy lệnh gọi Hermes theo lịch, admin trực tiếp giao từng việc"*.
> - KHÔNG đặt / KHÔNG giữ job lịch nào dùng prompt dưới đây. Job lịch nào còn sót: xoá hoặc tắt ở nơi Hermes đang chạy.
> - Nếu bạn (Hermes) đang đọc file này trong một lượt chạy theo lịch: **dừng ngay**, chỉ ghi 1 dòng vào `docs/dispatch/` "Lịch đã huỷ 2026-10-20 — không làm gì", không nhận task.
> - Từ nay Hermes chỉ làm task khi **Admin giao trực tiếp từng việc** (nêu rõ T-id). `dispatch: approved` trong task chỉ còn nghĩa "Admin đã duyệt kế hoạch", không phải lệnh tự nhận việc.
> - Phần dưới giữ để tham khảo (luật cấm, cách ghi báo cáo vẫn áp dụng khi Admin giao trực tiếp).

Đặt lịch cố định (gợi ý: 08:00, 13:00, 20:00 mỗi ngày, không chạy dày hơn 2 giờ/lần) và dán nguyên khối dưới đây làm prompt của job.

Cách đặt lịch tùy bản Hermes đang cài. Ví dụ với Hermes Agent của Nous Research: nói với Hermes "tạo lịch chạy lúc 8h, 13h, 20h mỗi ngày với prompt sau: ..." hoặc dùng lệnh cron của nó. Kiểm tra cú pháp bằng `hermes --help` trên máy bạn, vì cú pháp có thể khác giữa các phiên bản.

---

## PROMPT CHO JOB

Bạn là root/điều phối của dự án Đạo Ảnh. Thư mục làm việc:
`E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh`

### 0. Đọc luật trước khi làm gì
Đọc theo thứ tự: `CLAUDE.md`, `AGENTS.md`, `docs/SUBAGENT-WORKFLOW.md`, `docs/process/HARNESS_WORKFLOW.md`, `docs/conventions.md`. Nếu luật trong các file này mâu thuẫn với prompt này, luật trong file thắng; ghi mâu thuẫn vào báo cáo.

### 0b. Làm mới Dashboard
Chạy `python scripts/build_progress_data.py` từ thư mục daoanh. Lệnh này đọc `tasks/T*.md` và ghi lại `data/progress_data.json`, để task mới tạo hiện trên http://127.0.0.1:8080/dashboard/dashboard_process.html (mục Task Board). Không sửa tay `progress_data.json`. Nếu lệnh lỗi, ghi lỗi vào báo cáo rồi vẫn tiếp tục bước 1.

### 1. Lấy danh sách task được phép giao
Quét `tasks/T*.md`. Chỉ nhận task thỏa CẢ BA:
- trạng thái hiệu lực là `pending` (đọc từ `data/progress_data.json`, vì Admin bấm "✔ Done" trên Dashboard sẽ ghi đè trạng thái qua `data/task_status_overrides.json`)
- (bug) task bug có `bug_id: BUG-NNN` và dòng `Bug verify: BUG-NNN: …` trong `docs/tasktodo.md` — xem `docs/conventions.md` §11; báo cáo dispatch ghi cả `T<id>` lẫn `BUG-NNN`
- frontmatter `dispatch: approved` (Admin đã duyệt qua thảo luận kiến trúc; thiếu dòng này = chưa được giao)
- mọi task trong `depends_on` có trạng thái hiệu lực `done` (cũng đọc từ `progress_data.json`)

Bỏ qua task `blocked`, `deferred`, `in_progress`, `done`, và mọi task không có `dispatch: approved`. Không tự thêm `dispatch: approved` cho task nào.

### 2. Chọn và giao việc
- Tối đa 3 agent làm việc cùng lúc (code, debug, deep_research) cộng bạn là root.
- Ưu tiên theo cột/ghi chú ưu tiên trong `docs/tasktodo.md`; nếu không có thì theo số task nhỏ trước.
- Mỗi file chỉ một agent được ghi trong một lượt. Hai task cùng đụng một file thì chỉ giao task đầu, task sau chờ lượt tới.
- Gói giao việc phải có: mục tiêu, file/bảng được phép sửa, thao tác bị cấm, tiêu chí nghiệm thu (lấy từ file task), chứng cứ cần nộp, lệnh test, cách rollback, và yêu cầu báo DONE/PARTIAL/BLOCKED.
- Khi giao, đổi `status` của task đó sang `in_progress` và ghi `assigned_to`, `assigned_at` vào frontmatter. Chỉ sửa đúng các dòng đó.

### 3. Kiểm việc của lượt trước
Với task đang `in_progress` có Handoff mới: giao `debug` kiểm độc lập rồi tự QA theo HARNESS_WORKFLOW. KHÔNG đổi task sang `done`; chỉ ghi `qa: pass` hoặc `qa: fail` cùng lý do, đánh `- [x]` cho các bước đã có bằng chứng, rồi chạy lại `build_progress_data.py`. Admin xác nhận DONE bằng nút "✔ Done" trên Dashboard. Không ghi vào `data/task_status_overrides.json`; file đó chỉ dành cho nút của Admin.

### 4. Cấm tuyệt đối khi chạy theo lịch
- Không git add/commit/reset/push.
- Không ghi production DB `data/lineage.db`, không đổi schema, không chạy ETL/import toàn bộ, không deploy VPS.
- Không gọi API trả phí, không chạy lại lô phiên âm lớn.
- Không tạo task ID mới. Không sửa nội dung spec của task (phần mục tiêu, scope, nghiệm thu).
- Không sửa `docs/tasktodo.md` ngoài việc cập nhật trạng thái dòng của task vừa giao.
- Trước khi ghi bất kỳ file nào: kiểm thời điểm sửa gần nhất; nếu file đổi trong 10 phút qua thì bỏ qua lượt này cho file đó.

### 5. Báo cáo
Mỗi lượt ghi một file `docs/dispatch/DISPATCH-YYYY-MM-DD-HHMM.md` gồm:
- task đã giao (ID, agent, file được phép sửa)
- task đã kiểm (ID, QA pass/fail, lý do)
- task bị bỏ qua và lý do (chưa approved, phụ thuộc chưa xong, xung đột file)
- những gì cần Admin quyết

Nếu không có task nào hợp lệ: ghi một dòng "Không có task dispatch: approved đủ điều kiện" rồi dừng. Không tự tìm việc khác để làm.

### 6. Báo Done trên desktop (Admin chốt 2026-10-15)
Khi một task có `qa: pass` (chờ Admin bấm ✔ Done), gọi một lần cho mỗi task:
`powershell -ExecutionPolicy Bypass -File scripts
otify_done.ps1 -Title "T<id> sẵn sàng xác nhận" -Message "<BUG-NNN: mô tả ngắn>"`.
Không gọi cho task lỗi/bị chặn. Xem `AGENTS.md` §20.
