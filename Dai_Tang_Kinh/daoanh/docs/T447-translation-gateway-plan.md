# T447 — Cổng dịch AI thống nhất theo quy tắc hàn lâm

Trạng thái: Admin đã phê chuẩn đề xuất (2026-10-21). Chưa sửa code.

## Mục tiêu (bằng lời thường)

- User bấm nút **DỊCH AI** trên trang để chuyển đoạn Hán văn sang Việt văn.
- Kết quả được **lưu vào DB**, người đọc sau xem ngay, không phải dịch lại.
- Mọi lệnh dịch AI đều đi qua **một cổng quy tắc duy nhất**, để quy tắc trong trang
  `translation_rules` luôn được áp dụng, kể cả khi quy tắc được cập nhật liên tục.
- Nếu văn phong bản cũ chưa tốt, **admin dịch lại trong Cpanel**; không tự dịch lại.

## Hiện trạng

- Đã có cổng một phần: `_t73_style_lock` và `_t73_build_style_prompt` (`app.py`) đọc
  bảng `translation_rules`. Endpoint dịch đoạn văn dùng cổng này.
- Nhiều chỗ gọi AI đi thẳng, không qua cổng: `_call_gemini`, Groq trực tiếp ở nhiều
  endpoint, Claude (`ANTHROPIC_KEY`), Gemini trực tiếp, `_suggest_name` (chỉ nạp
  20 quy tắc). Đây là lỗ hổng cần đóng.

## Giải pháp đã phê chuẩn

### 1. Một hàm cổng duy nhất
`translate_han_vi(source_text, purpose)` là đường vào duy nhất cho mọi lệnh dịch
Hán→Việt: nút DỊCH AI, endpoint dịch đoạn văn, nút "Dịch lại" của admin.
Hàm này nạp đầy đủ quy tắc đang `active` từ `translation_rules` qua `_t73_style_lock`,
rồi dựng prompt bằng `_t73_build_style_prompt`. Các hàm gọi trực tiếp cũ được giữ
lại làm dự phòng khi cổng lỗi (không xóa chức năng cũ).

### 2. Phiên bản quy tắc (`rules_version`)
- Tính bằng hash của tập quy tắc active kèm `MAX(updated_at)`.
- Quy tắc đổi thì hash đổi; cache quy tắc trong bộ nhớ ngắn (vài phút) theo hash này,
  nên đổi quy tắc có hiệu lực ngay mà không phải khởi động lại.

### 3. Lưu kết quả kèm phiên bản
- Khóa cache = hash(đoạn Hán) + `rules_version` + model. Lưu vào bảng cache dịch hiện có
  (`translation_cache`, đã có nút Invalidate trong Cpanel). **Cần kiểm tra schema trước khi làm.**
- Người đọc sau:
  - Bản khớp `rules_version` hiện tại → trả về ngay, **không gọi AI**.
  - Bản theo quy tắc cũ → hiển thị kèm nhãn "dịch theo quy tắc cũ", **không tự dịch lại**.

### 4. Admin dịch lại trong Cpanel
- Nút "Dịch lại" bỏ qua cache, gọi cổng với quy tắc hiện tại, ghi bản mới.
- Bản cũ được giữ trong lịch sử để có thể hoàn tác.

### 5. Gợi ý tên (JSON)
- `_suggest_name` vẫn đi qua cổng để nhận đủ quy tắc, nhưng **giữ nguyên định dạng JSON**
  đầu ra. Có một test kiểm tra định dạng sau khi nạp đầy đủ quy tắc.

## Hai điểm đã chốt

**Điểm 1 — Ghi bản dịch vào DB có phải ghi DB nguy hiểm không?**
Không phải ghi dữ liệu gốc. Đây là cache do đúng chức năng DỊCH AI yêu cầu, và mỗi
lần ghi có phiên bản quy tắc đi kèm để truy vết. Vẫn ghi lệnh khôi phục vào
`docs/ROLLBACK.md`, và backup `lineage.db` trước khi chạy migration schema nếu có.

**Điểm 2 — Gợi ý tên có đi qua cổng không?**
Có. Nhưng chỉ nhận thêm quy tắc, định dạng đầu ra giữ nguyên, để không làm hỏng
các chỗ đọc kết quả JSON.

## Các bước

- [x] Kiểm tra schema `translation_cache` và liệt kê mọi chỗ gọi AI trong `app.py`.
      (Phát hiện thêm: DB local CHƯA chạy migration T165/T166 — xem ROLLBACK.md §T447.)
- [x] Sao lưu `app.py` và file liên quan vào `docs/sessions/<ngày>/`.
- [x] Viết `translate_han_vi` và hàm tính `rules_version` có cache ngắn.
      (Dùng trực tiếp `_t73_style_lock`/`style_constitution.py` SSOT đã có từ T165 —
      không viết lại rules_version hash, chỉ thêm lớp policy cache "không tự dịch lại".)
- [x] Chuyển các endpoint dịch sang cổng; giữ hàm cũ làm dự phòng.
      (`_suggest_name` đã chuyển qua `_t73_style_lock` + cache `translation_cache`.
      CHƯA chuyển: pipeline CBETA passage "DỊCH MƯỢT" (`_call_gemini` dòng ~3496/3680/3823) —
      xem mục Limitation trong báo cáo cuối, out-of-scope phiên này vì khung prompt
      build_style_prompt không khớp tác vụ polish/explain, rủi ro phá tính năng cũ.)
- [x] Ghi cache kèm `rules_version`; đọc cache khớp phiên bản thì không gọi AI.
- [x] Thêm nút "Dịch lại" trong Cpanel (bỏ qua cache, giữ lịch sử).
      (Cột `history_json` mới trong `translation_cache` — migration additive có backup.)
- [x] Test: đổi một quy tắc → bản cũ được đánh dấu, bản mới dịch lại đúng quy tắc.
      (Script test trực tiếp qua translate_han_vi — xem báo cáo cuối, 5/5 case pass.)
- [x] Test: `_suggest_name` vẫn trả JSON đúng định dạng.
      (Qua HTTP thật `/api/admin/namevi/suggest` — contract {"vietnamese_name": ...} giữ nguyên.)
- [x] `py_compile app.py`, kiểm trên trình duyệt thật (127.0.0.1 qua Flask thật, port thay thế
      do cổng 5000 đang bị process khác chiếm — xem báo cáo).
      `npm run lint`: lint-check.js hiện chỉ quét danh sách file cố định (không có
      translation_cache.html) — đã syntax-check riêng bằng `node --check` (OK).
- [ ] daoanh-qa kiểm độc lập; Admin xác nhận DONE.

## Hoàn tác

Khôi phục từ bản sao `docs/sessions/<ngày>/app.py.bak-T447`. Lệnh hoàn tác chi tiết
sẽ ghi vào `docs/ROLLBACK.md` khi bắt đầu thực hiện.
