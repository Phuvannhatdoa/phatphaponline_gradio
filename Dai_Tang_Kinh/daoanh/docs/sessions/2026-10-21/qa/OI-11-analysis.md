# OI-11 — Phân tích `scripts/ai_batch_transliterate_places_districts.py`

> Ngày: 2026-10-21 · Chế độ: CHỈ ĐỌC (không sửa code, không ghi DB, không git add/commit/reset/checkout/stash).
> Nguồn so sánh: worktree (`scripts/ai_batch_transliterate_places_districts.py`) và `git show HEAD:Dai_Tang_Kinh/daoanh/scripts/ai_batch_transliterate_places_districts.py`.

## Kết luận nhanh

- **Bản HEAD CÓ định nghĩa trùng**: `count_done`, `save_batch`, `reset_table` mỗi hàm định nghĩa **2 lần** (HEAD dòng 160/327, 171/338, 185/352). Hai bản trong mỗi cặp **nguyên văn giống nhau** (md5 khớp). Python lấy định nghĩa sau, nên hai bản giống nhau không đổi hành vi.
- **Worktree hiện tại**: mỗi hàm còn đúng **1 định nghĩa** (dòng 160, 171, 195). Nội dung 3 hàm khớp HEAD (md5 không đổi).
- **Thay đổi chưa commit so với HEAD**: (a) xoá 2 bản trùng ở cuối file; (b) thêm `_checkpoint()` (ép WAL checkpoint) và 4 dòng gọi trong `run()`.
- **Khuyến nghị: GIỮ cả hai thay đổi.** Lý do ở mục 3. Quyết định chốt thuộc Admin (OI-11 ghi "Admin cần quyết: có giữ thay đổi này trong commit hay không").

## 1. Số liệu đo được

| Hàm | HEAD (377 dòng) | Worktree (357 dòng) | md5 thân hàm |
|---|---|---|---|
| `count_done` | L160 **và** L327 | L160 | `d38ef76492` (cả 2 bản HEAD và worktree) |
| `save_batch` | L171 **và** L338 | L171 | `6d8d85d4ad` (cả 2 bản) |
| `reset_table` | L185 **và** L352 | L195 | `4e212cee1d` (cả 2 bản) |
| `_checkpoint` | không có | L185–193 (mới) | `b406339592` |

Diff `git diff HEAD` (chỉ đọc), 2 hunk:
- `@@ -182,6 +182,16 @@`: thêm `_checkpoint()` (10 dòng, gồm dòng trống).
- `@@ -316,48 +326,18 @@`: trong `run()` thêm 4 dòng gọi `_checkpoint()` (`if (batch_num % 20) == 0:` / `_checkpoint()` / dòng trống / `_checkpoint()` cuối hàm); xoá 34 dòng = 3 hàm trùng ở cuối file kèm dòng trống.

Phép kiểm: 34 dòng xoá = (count_done 9 + 2 trống) + (save_batch 12 + 2 trống) + (reset_table 7 + 2 trống) = 34. Khớp với hunk.

## 2. Cách kiểm chứng

- Script so sánh (chỉ đọc, `git show HEAD:` qua subprocess): `%TEMP%\opencode\oi11_cmp.py`. Tách từng khối `def` theo thụt lề, băm md5 thân hàm, liệt kê tên trùng.
- Kết quả script: với HEAD, cả 3 tên trùng đều báo `IDENTICAL`. Với worktree, không còn tên trùng.

## 3. Đánh giá từng thay đổi

**(a) Xoá 2 bản trùng cuối file — AN TOÀN, nên giữ.**
- Hai bản đã giống hệt nhau (md5 khớp), nên xoá bản sau không đổi hành vi. Bản đầu vẫn còn nguyên.
- Giảm rủi ro sửa nhầm một bản mà bản kia vẫn chạy (đây là lỗi kiểu cần tránh).

**(b) Thêm `_checkpoint()` — additive, nên giữ nhưng cần kiểm khi chạy thật.**
- Bọc `try/except`; lỗi chỉ ghi WARN, không dừng batch.
- Chạy mỗi 20 batch và một lần cuối `run()`. Mục đích (theo docstring): không mất WAL khi tiến trình bị kill.
- Điểm chưa đo: `PRAGMA wal_checkpoint(TRUNCATE)` có thể bị chặn nếu có reader đang giữ khoá, và `get_db()` có `timeout=30`. Theo tài liệu SQLite, lệnh này trả trạng thái busy thay vì raise (chưa kiểm trên DB thật). Không gây mất dữ liệu, nhưng có thể làm chậm vài giây.

## 4. Nếu Admin chọn HOÀN NGUYÊN

- Không dùng `git checkout`/`reset` khi chưa có lệnh (AGENTS §14).
- Cách an toàn: lấy nội dung từ `git show HEAD:<path>` và ghi lại bằng Python (`open(..., 'w', encoding='utf-8')`). **Không dùng toán tử `>` của PowerShell 5.1**: nó ghi UTF-16 LE và làm hỏng file.
- Sau khi hoàn nguyên, `git diff --cached --name-only` phải cho ra đúng danh sách file mong đợi.

## 5. Dư lượng KHÔNG thuộc OI-11 (ghi nhận, không sửa)

Các khai báo trùng còn lại trong worktree (không phải định nghĩa hàm, giá trị giống nhau nên vô hại):
- `MODEL_ID`, `BATCH_SIZE`, `SLEEP_SECONDS`, `MAX_RETRIES` khai báo 2 lần (dòng 38–41 và 63–66).
- `from google import genai` và `genai_types` import 2 lần (dòng 28–32 và 84–89).

Vấn đề khác (không liên quan trùng hàm):
- `LOG_FILE` khai báo nhưng không dùng.
- `log()` ghi vào đường dẫn tương đối `logs/ai_transliterate.log`, nên file log phụ thuộc thư mục làm việc khi chạy.

## 6. Giới hạn của phân tích

- Chỉ kiểm tra tĩnh (đọc code, so md5, diff). Không chạy script, không gọi Gemini, không ghi DB.
- Chưa đo hành vi `_checkpoint()` trên DB thật (xem 3b).
- Chưa xác định task sở hữu thay đổi (OI-11 nêu T444 pending nhưng chưa có bằng chứng liên kết).
