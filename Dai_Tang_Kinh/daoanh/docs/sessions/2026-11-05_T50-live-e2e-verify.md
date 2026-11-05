# 2026-11-05 — T50: xác minh live sau restart (adopt job + chặn "Dịch" trùng)

**Phạm vi:** T50 (`vi_text` backfill) — phần còn lại sau phiên 2026-11-04: xác minh
code mới đã nạp vào `app.py` đang chạy, kiểm nhánh *adopt job mồ côi* và *chặn spawn
job thứ hai* trên server thật.

**Không đụng:** schema DB, prompt, logic dịch, dữ liệu Hán/Việt, quota Groq.

---

## 1. Trạng thái khi mở phiên (đo được)

| Mục | Giá trị |
|---|---|
| `app.py` đang chạy | PID **16160**, start `2026-11-04 20:13:54` (sau merge `254fb1d7` lúc 13:45) |
| Merge T50 | `254fb1d7` — 7 file: `app.py`, `scripts/process_alive.py`, test E, session, handoff, `ROLLBACK.md`, `tasktodo.md` |
| Job 22708 | **đã chết** — bị `/stop` chủ động lúc `2026-11-04 17:10:48` |
| Status file | `running=false`, `pid=22708`, `stopped_pid=22708`, `stopped_at=2026-11-04 10:10:48` (UTC) |
| `vi_text` toàn DB | **1766** / 44820 |
| `pid_alive` trong cây chính | `22708 → True`, `21660 → True`, `999999 → False` |

**Điểm quan trọng:** mục "sau restart `/job-status` phải trả `running=true, pid=22708`"
trong handoff 2026-11-04 **không còn áp dụng** — job đã được dừng có chủ đích trước khi
restart. Lúc này `running=false` là **đúng**, không phải bug tái phát. Bằng chứng code
mới đã chạy: status file có field `stopped_pid` — chỉ nhánh `/stop` mới ghi field này.

⇒ Không thể chứng minh nhánh adopt bằng cách quan sát job thật (không có job nào chạy),
nên phải kiểm có kiểm soát (mục 3).

## 2. Test tự động (cây chính, DB thật)

```
python -X utf8 tests/test_t50_startup_windows.py
→ T50-STARTUP-WINDOWS: 5/5 PASS, 0 FAIL
  (A import hanviet_normalization, B --dry-run, C --verify, D self-reconcile race-safe, E pid_alive)
```

## 3. E2E live có kiểm soát — PASS

Script: `scripts/t50_live_e2e_check.py` (mới). Cách làm: backup status file → spawn
1 tiến trình giả (`python -c sleep 120`) làm "job đang sống" → ghi status giả
`running=false, pid=<giả>` (không `stopped_pid`) → gọi API thật → luôn restore + kill
trong `finally`.

Kết quả chạy trên `app.py` PID 16160:

| Bước | Kỳ vọng | Đo được |
|---|---|---|
| `GET /job-status` | adopt: `running=true`, `pid` = PID giả | `running=True, pid=5348, sigla=T99nE2E` ✔ |
| `POST /run {sigla: T51n2076}` | `ok=false`, KHÔNG spawn | `ok=False`, `error="Đang chạy sigla 'T99nE2E' (PID 5348). Dừng trước khi chạy bộ khác."`, `pid=null` ✔ |
| status sau `/run` | vẫn PID giả | `pid=5348` ✔ (không có PID mới) |
| sau restore | về trạng thái thật | `running=False, pid=22708, sigla=T51n2076` ✔ |

Script có 2 guard: (a) nếu tiến trình giả không sống → **không** gọi `/run`;
(b) chỉ gọi `/run` khi bước adopt đã xác nhận `running=true`; (c) luôn restore status.

## 4. Sự cố trong phiên (ghi lại để không lặp)

Lần chạy thử **đầu tiên** dùng PowerShell `Start-Process ... -ArgumentList '-c','...'`
— tiến trình giả **chết ngay** (quoting của PowerShell), nên `pid_alive` trả `False`,
guard không kích hoạt và `POST /run` **spawn job dịch thật PID 12680** (`T51n2076`).

Xử lý: `Stop-Process -Id 12680 -Force` sau ~10 giây (job còn ở bước khởi động/gọi Groq).

Thiệt hại đo được:

| Mục | Kết quả |
|---|---|
| DB `vi_text` | **1766 → 1766** (không ghi passage nào) |
| Status file | khôi phục nguyên bản từ backup |
| `data/t50_job.log` | bị `/run` mở `'w'` ⇒ **truncate về 0 byte** — mất tail rate-limit cũ (các mốc 2443s/2554s/2843s/2534s/2603s/2585s/2518s chỉ còn trong session 2026-11-04 + transcript) |

Bài học: test "chặn spawn" chỉ được gọi `/run` **sau khi** đã xác nhận guard hoạt động;
và tiến trình giả phải được kiểm sống bằng chính `pid_alive()` (không tin "đã start").

## 5. Việc còn lại

1. **Quota Groq (Admin quyết):** job `T51n2076` dừng ở passage ~2283; 1766/44820 toàn bộ.
   Trước khi dừng, rate-limit đã lên 41–47 phút/lần ⇒ nếu giữ key hiện tại, ước tính
   ~1600 passage còn lại của T51n2076 mất hàng chục ngày. Chọn: tiếp tục chờ / đổi
   key-quota / để T50 tạm nghỉ.
2. **Chạy lại job (khi Admin đồng ý):** mở dashboard T50, bấm "Dịch" cho `T51n2076`
   (không còn job nào chạy nên sẽ start sạch, resume từ passage kế tiếp).
3. **Log tail cũ đã mất** (mục 4) — nếu cần đối chiếu tốc độ, dùng số liệu trong
   `docs/sessions/2026-11-04_T50-pid-alive-windows.md`.
4. **File `docs/Handoff-2026-11-03-T50-python314-windows.md`** vẫn chỉ tồn tại dạng
   untracked ở cây chính — cần Admin chốt: đưa vào git hay trỏ về session 2026-11-03.

## 6. File tạo/sửa trong phiên

| File | Loại | Ghi chú |
|---|---|---|
| `scripts/t50_live_e2e_check.py` | mới | E2E live có guard, chạy tay, không tốn Groq |
| `docs/sessions/2026-11-05_T50-live-e2e-verify.md` | mới | file này |
| `docs/ROLLBACK.md` | sửa | bổ sung merge SHA + E2E live + sự cố log |
| `docs/tasktodo.md` | sửa | mục T50 ngày 2026-11-05 |

**Revert:** `git revert --no-edit <sha_commit_này>` (docs + 1 script, không đụng DB).
Code T50 vẫn revert bằng `git revert --no-edit 254fb1d7` (merge) hoặc `ddb1ce2d` (nhánh).
