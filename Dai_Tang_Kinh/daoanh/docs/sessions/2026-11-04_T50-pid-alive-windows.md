# T50 — Dò PID an toàn trên Windows (job "mồ côi" bị báo đã chết)

**Ngày:** 2026-11-04 | **Task:** T50 (CBETA vi_text backfill) | **Nhánh:** `wt/t50-python314-windows-fix`

## Bối cảnh

Bước còn lại của T50 sau phiên 2026-11-03 là restart `app.py` + E2E nút "Dịch"
trên `t50-progress.html`. Khi kiểm tra trạng thái thật trước khi bấm, phát hiện
mâu thuẫn:

| Nguồn | Đọc được |
|---|---|
| `GET /daoanh/api/admin/t50/job-status` | `running=false`, `pid=22708`, `translated_total=1761`, `remaining_total=43059` |
| `data/t50_job_status.json` | `running=false`, `stopped_at="2026-11-03 07:02:09"` (cũ) |
| `tasklist` / `Get-CimInstance Win32_Process` | PID **22708 vẫn sống**, chạy `t50_passage_vi_backfill.py --sigla T51n2076 --sleep 1.0` |
| `data/t50_job.log` | vẫn ghi passage 2278/2279, `rate_limit → retry sau 2843s` |
| Đếm DB (read-only) | 1761 → **1762** passage có `vi_text` (job có tiến triển, rất chậm vì rate limit) |

Nghĩa là: dashboard nói "chưa chạy", nhưng job vẫn đang dịch. Nếu Admin bấm
"Dịch" lúc này, `/run` chỉ kiểm cờ `running` (đang `false`) ⇒ **spawn job thứ
hai** chạy song song trên cùng DB và cùng quota Groq.

## Nguyên nhân gốc (đo được)

`_t50_pid_alive()` trong `app.py` dùng `os.kill(pid, 0)`.

Trên Windows, CPython cài `os.kill` bằng `OpenProcess` + `TerminateProcess`
(`Modules/posixmodule.c`, `os_kill_impl`): mọi `sig` khác
`CTRL_C_EVENT`/`CTRL_BREAK_EVENT` đều được dùng làm **mã thoát** của
`TerminateProcess`. Vì vậy `os.kill(pid, 0)` không phải phép "thử tồn tại".

Đo trực tiếp trên máy này (Python 3.14.3, Windows):

```
>>> os.kill(22708, 0)        # job T50 đang sống
OSError: [WinError 87] The parameter is incorrect
>>> os.kill(999999, 0)
OSError: [WinError 87] The parameter is incorrect
>>> tasklist /FI "PID eq 22708"
python.exe   22708   Console   1   58.864 K     ← vẫn sống
```

⇒ hàm cũ trả `False` cho tiến trình đang sống, `/job-status` ghi
`running=false` (giữ lại `stopped_at` cũ), từ đó UI sai và có nguy cơ spawn
trùng. Ngoài ra nếu `OpenProcess` thành công thì chính lệnh dò gọi
`TerminateProcess(handle, 0)` — tức "kiểm tra còn sống" lại có thể **giết**
job.

## Thay đổi

1. **`scripts/process_alive.py` (mới)** — `pid_alive(pid)`:
   - Windows: `OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION)` +
     `GetExitCodeProcess`, so với `STILL_ACTIVE = 259`. Chỉ quyền đọc, không
     bao giờ có `PROCESS_TERMINATE` ⇒ không thể giết nhầm.
   - POSIX: giữ `os.kill(pid, 0)` (ở đó đúng là phép dò tồn tại).
   - `None`/`''`/`0`/`-1`/chuỗi rác → `False`, không ném exception.

2. **`app.py`** (khối T50 job control ~dòng 10747):
   `from process_alive import pid_alive as _t50_pid_alive`, bỏ `os.kill`.
   - `/run`: chặn theo **PID thật**, không chỉ cờ `running`.
   - `/enqueue`: xét PID thật; job còn sống ⇒ coi là đang bận, sửa `running=true`.
   - `/job-status`: **adopt** job mồ côi (`running=false` + PID sống +
     PID ≠ `stopped_pid`) ⇒ `running=true`, xoá `stopped_at` cũ.
   - `/stop`: ghi thêm `stopped_pid` để không adopt lại job vừa dừng.

3. **`tests/test_t50_startup_windows.py`** — thêm case E:
   - E1: pid rỗng/rác (`None`, `''`, `0`, `-1`, `'abc'`, `'  '`) → `False`.
   - E2: PID tiến trình con đang sống → `True`.
   - E3: gọi xong tiến trình đó **vẫn sống** (khoá lại: không dùng `os.kill`).
   - E4: sau khi tiến trình thoát → `False`.

## Bằng chứng đo được

| Đo | Kết quả |
|---|---|
| `python tests/test_t50_startup_windows.py` (worktree, DB rỗng → fixture) | **5/5 PASS** |
| `py_compile` 3 file (`process_alive.py`, `app.py`, test) | OK |
| `pid_alive(22708)` (job thật đang chạy) | `True` |
| `pid_alive(21660)` (app.py đang chạy) | `True` |
| `pid_alive(999999)` | `False` |
| Sau khi gọi `pid_alive(22708)` | PID 22708 **vẫn sống** |
| Job T50 thật | vẫn chạy, `vi_text` 1761 → 1762 trong lúc kiểm tra; log có `rate_limit` chờ tới ~47 phút/lần |

## Không đụng gì

- Không đổi prompt, logic dịch, schema DB, giá trị Hán/Việt văn.
- Không chạy backfill, không gọi Groq, không ghi vào DB thật (chỉ đọc).
- Không restart `app.py`, không dừng/khởi động job thật (việc của Admin).
- Không sửa `data/t50_job_status.json` bằng tay — route `/job-status` sẽ adopt
  khi app nạp code mới.

## Rollback

```
git revert --no-edit ddb1ce2d
```

Mất dữ liệu: **không** — thuần code, 3 file, không migration.

## Còn lại

- Restart `app.py` (PID 21660) để nạp `process_alive.py`; sau restart gọi
  `GET /api/admin/t50/job-status` phải thấy `running=true`, `pid=22708`
  (adopt job đang chạy) thay vì `false`.
- E2E bấm "Dịch" sau restart: phải bị chặn với thông báo "Đang chạy sigla ...
  Dừng trước khi chạy bộ khác" (vì job 22708 còn sống), không spawn job thứ hai.
- Job T51n2076 đang bị Groq rate-limit rất nặng (retry 30–47 phút). Cần Admin
  quyết: để chạy tiếp, đổi key/quota, hay tạm dừng.
