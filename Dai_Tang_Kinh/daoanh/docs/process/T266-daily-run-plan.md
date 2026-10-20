# T266 — Kế hoạch chạy Gemini dịch hàng ngày (DRAFT — CHƯA BẬT)

Ngày ghi: 2026-10-10
Liên quan: T266, T74b (`scripts/t74b_pilot_gemini_translate.py`)
Trạng thái: **CHƯA BẬT** — chỉ là kế hoạch, cần Admin duyệt trước khi tạo lịch
tự động thật trên máy.

## 1. Mục tiêu

Chạy đều đặn hàng ngày script dịch Gemini (`t74b_pilot_gemini_translate.py`)
để dịch dần tiểu sử DILA, không cần Claude ngồi canh từng lần, nhưng vẫn giữ
giới hạn an toàn (hạn mức Gemini free, số request mỗi lần chạy).

## 2. Cách chạy — Windows Task Scheduler (không cần Claude)

- Công cụ: **Windows Task Scheduler** trên máy local (không dùng schedule
  cloud — xem mục 3 vì sao).
- Lệnh chạy mỗi lần (trong thư mục `daoanh/`):
  ```
  python -X utf8 scripts/t74b_pilot_gemini_translate.py
  ```
- Script tự dừng khi hết hạn mức ngày (quota Gemini free) và tự tiếp tục từ
  state đã lưu ở lần chạy trước (không dịch lại từ đầu, không cần Claude theo
  dõi tiến độ).
- Điều kiện bắt buộc trước khi bật: khóa `GEMINI_API_KEY` phải có sẵn trong
  file `.env` tại thư mục `daoanh/` (script tự load qua `python-dotenv`, theo
  quy tắc tại `CLAUDE.md` mục "API keys"). Nếu `.env` không có key hoặc key
  hết hạn mức/bị revoke, task sẽ chạy nhưng không dịch được gì (cần kiểm log
  mỗi vài ngày).

## 3. Vì sao không dùng schedule cloud

- Schedule cloud (ví dụ task tự động của hạ tầng Claude/VPS ngoài máy local)
  **không truy cập được** DB (`data/lineage.db`) và các file state/`.env` nằm
  trên máy local của Admin. Script cần đọc/ghi trực tiếp các file này nên chỉ
  chạy được trên máy có sẵn dữ liệu — tức máy local, không phải cloud.

## 4. Giới hạn mỗi lần chạy

- Mỗi lần chạy: **giới hạn 20 yêu cầu HTTP** tới Gemini API (an toàn hạn mức
  free, tránh bị khóa key hoặc tốn hết quota ngày chỉ trong 1 lần chạy).
- Kết quả mỗi lần chạy: ghi vào **file nháp JSONL** (bản dịch chưa phải chính
  thức — vẫn cần người duyệt trước khi public, theo đúng cơ chế
  `style_constitution.py`/`translation_cache` đã có).
- Số liệu cần ghi vào log mỗi lần chạy: số request đã gửi, số thành công, số
  lỗi (đặc biệt lỗi 503 — xem mục 5), thời điểm chạy, số dòng còn lại trong
  hàng đợi dịch.

## 5. Rủi ro cần Admin biết trước khi duyệt

| Rủi ro | Mô tả |
|---|---|
| Tốn hạn mức mỗi ngày | Mỗi lần chạy dùng một phần quota free của Gemini; chạy hàng ngày cộng dồn có thể hết quota tháng sớm hơn dự kiến nếu dữ liệu dịch nhiều hơn ước tính. |
| Dữ liệu gửi đi Google | Nội dung tiểu sử (Hán/Việt nháp) được gửi qua API Gemini (gói **free** — cần Admin biết rõ gói free có điều khoản dữ liệu khác gói trả phí, Google có thể dùng dữ liệu theo chính sách gói free). |
| Lỗi 503 kéo dài | Nếu Gemini API trả lỗi 503 (quá tải) kéo dài nhiều ngày liên tiếp, task chạy mỗi ngày nhưng không tiến triển — cần người kiểm log định kỳ, không chạy "fire and forget" hoàn toàn. |

## 6. Lệnh thiết lập Task Scheduler (MẪU — chưa tự tạo task trên máy)

Lệnh mẫu dưới đây chỉ để Admin tham khảo/chạy thủ công nếu đồng ý; **agent
không tự chạy lệnh này để tạo task thật trên máy** (ngoài phạm vi "chỉ cập
nhật tài liệu" của phiên làm việc này).

```powershell
# Mẫu — Admin tự chạy nếu duyệt, đổi đường dẫn cho đúng máy thật
$action = New-ScheduledTaskAction -Execute "python.exe" `
  -Argument "-X utf8 scripts/t74b_pilot_gemini_translate.py" `
  -WorkingDirectory "E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh"
$trigger = New-ScheduledTaskTrigger -Daily -At 3:00AM
Register-ScheduledTask -TaskName "T266-Gemini-Daily-Translate" `
  -Action $action -Trigger $trigger `
  -Description "Chạy T74b Gemini pilot translate hàng ngày (quota giới hạn 20 request/lần)"
```

## 7. Chưa bật — cần Admin xác nhận

- [ ] Admin xác nhận đồng ý bật lịch tự động (hoặc giữ nguyên chạy tay như
      hiện tại).
- [ ] Admin xác nhận `.env` trên máy thật đã có `GEMINI_API_KEY` còn hạn mức
      trước khi bật.
- [ ] Admin xác nhận chấp nhận rủi ro ở mục 5 (đặc biệt điểm dữ liệu gửi
      Google qua gói free).
- [ ] Admin xác nhận giờ chạy mong muốn (mẫu ở mục 6 đang để 3:00 sáng — giả
      định, cần Admin chọn lại nếu không phù hợp).

Khi Admin xác nhận đủ 4 mục trên, mới tách task build/thiết lập thật (tạo
Scheduled Task trên máy, không phải chỉ ghi tài liệu như phiên này).
