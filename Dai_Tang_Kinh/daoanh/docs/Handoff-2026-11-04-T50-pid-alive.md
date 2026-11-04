# Handoff 2026-11-04 — T50: dò PID an toàn trên Windows

## 1. Bảng thông tin đọc nhanh

| Mục | Giá trị |
|---|---|
| Ngày bàn giao | 2026-11-04 |
| Nhánh | `wt/t50-python314-windows-fix` |
| HEAD trước phiên | `c5614ebf` (test-robustness 2026-11-03, đã merge vào `truyen-dang-the-pho-clean`) |
| Task | T50 (CBETA `vi_text` backfill) — bug phụ "dò PID" |
| Trạng thái test | `tests/test_t50_startup_windows.py` **5/5 PASS** (worktree, DB rỗng → fixture) |
| DB | Không ghi. Chỉ đọc `data/lineage.db` cây chính để đếm tiến độ |
| TTL | Không đụng |
| Job thật | PID 22708 (`T51n2076`) **vẫn sống**, bị Groq rate-limit nặng |

## 2. Đọc trong 2 phút

- **Đã làm:** phát hiện `_t50_pid_alive()` dùng `os.kill(pid, 0)` — trên Windows
  đó là `TerminateProcess`, không phải phép dò tồn tại. Đo thật: job T50 đang
  sống (PID 22708) bị báo `WinError 87` ⇒ `_t50_pid_alive` trả `False` ⇒
  dashboard ghi `running=false` trong khi job vẫn dịch.
- **Nguy cơ:** `/run` chỉ chặn theo cờ `running`, nên bấm "Dịch" lúc này sẽ
  spawn job thứ hai (cùng DB + cùng quota Groq).
- **Đã sửa:** thêm `scripts/process_alive.py` (ctypes `OpenProcess` +
  `GetExitCodeProcess`, chỉ quyền đọc), `/run` + `/enqueue` xét PID thật,
  `/job-status` tự adopt job mồ côi, `/stop` ghi `stopped_pid`.
- **3 việc Admin cần làm ngay:**
  1. Restart `app.py` (PID 21660) để nạp code mới.
  2. Sau restart, gọi `/daoanh/api/admin/t50/job-status` — phải thấy
     `running=true`, `pid=22708` (adopt job đang chạy).
  3. Bấm "Dịch" một lần để xác nhận bị chặn (không spawn job thứ hai).
- **Chưa quyết:** job `T51n2076` đang rate-limit 30–47 phút/lần — tiếp tục,
  đổi key/quota, hay tạm dừng?

## 3. Đề xuất phần chữa dựng (fix)

| Vấn đề | Cách sửa | Bằng chứng / đo được |
|---|---|---|
| `os.kill(pid, 0)` trên Windows gọi `TerminateProcess` | `scripts/process_alive.py` dùng `OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION)` + `GetExitCodeProcess` == 259 | `pid_alive(22708)=True`, `pid_alive(999999)=False`; gọi xong PID 22708 vẫn sống |
| Status ghi `running=false` dù job sống | `/job-status` adopt khi `running=false` + PID sống + PID ≠ `stopped_pid` | logic + test E; sẽ đo sau khi restart |
| Bấm "Dịch" có thể spawn trùng | `/run` + `/enqueue` kiểm PID thật thay vì cờ `running` | đọc code + test E |

## 4. Cảnh báo bắt buộc

- **`os.kill(pid, 0)` trên Windows KHÔNG phải phép dò tồn tại.** Đừng dùng lại
  ở bất kỳ script nào. CPython: `Modules/posixmodule.c`, `os_kill_impl`.
- **Không sửa tay `data/t50_job_status.json`.** Nếu job còn sống, `/job-status`
  (code mới) sẽ adopt và sửa `running=true`.
- **Restart `app.py` không làm chết job 22708** (tiến trình cha cũ đã chết, job
  được tách process-group nhờ `CREATE_NEW_PROCESS_GROUP`).
- Nếu bấm "Dừng" trước khi restart: app cũ dùng `_t50_pid_alive` lỗi nên có thể
  báo "Không có job nào đang chạy" dù job còn sống — đó là bug đang sửa, không
  phải job đã chết.

## 5. Lệnh revert

| Task | Lệnh | Mất dữ liệu? |
|---|---|---|
| T50 — dò PID an toàn (2026-11-04) | `git revert --no-edit <sha>` | Không — 3 file code, không migration DB |

## 6. File tạo/sửa trong phiên

| File | Loại | Ghi chú |
|---|---|---|
| `scripts/process_alive.py` | mới | helper `pid_alive()` an toàn Windows |
| `app.py` | sửa | import helper; guard `/run`, `/enqueue`; adopt `/job-status`; `stopped_pid` ở `/stop` |
| `tests/test_t50_startup_windows.py` | sửa | thêm case E |
| `docs/sessions/2026-11-04_T50-pid-alive-windows.md` | mới | nhật ký phiên |
| `docs/ROLLBACK.md` | sửa | mục T50 ngày 2026-11-04 |
| `docs/tasktodo.md` | sửa | cập nhật dòng T50 |
| `docs/Handoff-2026-11-04-T50-pid-alive.md` | mới | file này |

## 7. Sai lầm / bài học

- Phiên trước kết luận "còn lại chỉ là restart + click E2E", nhưng không kiểm
  PID thật trước khi tin status file. **Bài học:** trước khi kết luận job đã
  chết, phải đối chiếu `tasklist`/`Get-CimInstance` và log tail, không tin
  riêng JSON status.
- Suýt kết luận sai "job đã dừng" chỉ vì API trả `running=false`. Đếm DB hai
  lần (1761 → 1762) và log mtime mới chứng minh job còn sống.
- Đã kiểm chứng `os.kill(pid, 0)` trên **tiến trình con tự spawn** (không chết)
  và trên **job thật** (WinError 87) — hành vi không ổn định giữa các tiến
  trình, nên tuyệt đối không dùng để dò.

## 8. Việc CHƯA xong (theo thứ tự ưu tiên)

1. **Restart `app.py`** (Admin) — chưa làm, cần Admin quyết thời điểm.
2. **E2E sau restart:** `/job-status` phải `running=true, pid=22708`; bấm
   "Dịch" phải bị chặn; nếu job 22708 chết thì bấm "Dịch" phải khởi động sạch.
3. **Quota Groq:** job `T51n2076` đang rate-limit 30–47 phút/lần
   (1762/44820 passage toàn bộ; 1731/3917 của T51n2076). Cần Admin chọn:
   tiếp tục chờ / đổi key / tạm dừng.
4. **File handoff 2026-11-03 bị thiếu:** `docs/ROLLBACK.md` và code nhắc
   `docs/Handoff-2026-11-03-T50-python314-windows.md` nhưng file này **không
   tồn tại** trong git (mọi nhánh). Cần Admin xác nhận có dựng lại hay chỉ trỏ
   về `docs/sessions/2026-11-03_T50-test-db-robustness.md`.

## 9. Lệnh kiểm tra nhanh (1 phút)

```powershell
cd Dai_Tang_Kinh/daoanh
python tests/test_t50_startup_windows.py          # phải 5/5 PASS
python -c "import sys; sys.path.insert(0,'scripts'); from process_alive import pid_alive; print(pid_alive(22708))"
```

```powershell
# trạng thái job thật
Invoke-RestMethod http://127.0.0.1:5000/daoanh/api/admin/t50/job-status | ConvertTo-Json -Depth 4
Get-Process -Id 22708 -ErrorAction SilentlyContinue | Select-Object Id,CPU
```

## 10. Ghi chú cho agent kế tiếp

- Đọc mục 4 trước khi làm bất cứ điều gì với T50.
- Nếu `job-status` vẫn trả `running=false` sau restart: kiểm `python -c "... pid_alive(22708)"`.
  Nếu helper trả `True` mà API vẫn `false` ⇒ app chưa nạp code mới (restart lại).
- Không chạy `pip install` thêm; helper chỉ dùng `ctypes` chuẩn.
- Nếu phải dừng job: gọi `POST /api/admin/t50/stop` (sau restart) — app cũ có
  thể lỗi vì `_t50_pid_alive` cũ; cách chắc chắn là `Stop-Process -Id 22708`
  rồi ghi status `running=false` qua route khi app mới đã chạy.
