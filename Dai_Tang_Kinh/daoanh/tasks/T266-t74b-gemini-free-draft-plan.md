---
id: T266
title: "T74b giai đoạn thử — dịch bản nháp tiểu sử DILA bằng Gemini free (gộp 5 tiểu sử/yêu cầu)"
module: DILA Authority
priority: high
status: in_progress
created: 2026-10-09
updated: 2026-10-09
owner: claude-code
parent: T74b
plan_approved_at: "2026-10-09 (Admin phê chuẩn đề xuất: Gemini free, gộp 5 tiểu sử/yêu cầu, chất lượng đánh giá sau)"
done_when: >
  Bản nháp JSONL có ≥200 tiểu sử (lô thử) với số liệu đầy đủ (thành công, lỗi, còn chữ Hán).
  KHÔNG ghi bio_vi hay bảng DB nào. Chất lượng và việc chuyển sang API trả phí do Admin quyết sau.
revert: >
  Không đổi DB. Xóa file nháp JSONL nếu cần làm lại. Script có sao lưu trước khi sửa.
outcome: >
  2026-10-09: đã lập kế hoạch. Pilot trước (T74b, 15 yêu cầu, 10 OK) cho thấy hạn mức
  20 yêu cầu/ngày/model với gemini-3.8-flash.
  2026-10-09 15:57-16:04: chạy lô thật lần 1 (20 yêu cầu HTTP = giới hạn cứng/ngày).
  Kết quả: 5 batch gọi được, 1 thành công (5 dila_id dịch xong, 0 còn chữ Hán),
  4 batch lỗi HTTP 503 (model quá tải, KHÔNG phải 429 quota) -> 20 dila_id vào retry_queue.
  quota_exhausted vẫn null (503 != hết hạn mức ngày). DB data/lineage.db không bị đụng
  (mtime 15:25:02, trước lúc script chạy). Ngày mai chạy lại để resume retry_queue.
---

# T266 — T74b giai đoạn thử (Gemini free)

Task con của **T74b**. Mục tiêu: có bản nháp cho nhiều tiểu sử nhất trong hạn mức miễn phí. Chất lượng đánh giá sau.

## 1. Ràng buộc đã biết

- Model: `gemini-3.8-flash`. Model cũ `gemini-3.6-flash` trả lỗi 503.
- Hạn mức free: 20 yêu cầu mỗi ngày mỗi model. Lỗi 429 ghi rõ quota theo ngày, phải chờ khoảng 20 giờ.
- Dữ liệu gửi đến Google theo gói free có thể được dùng để cải thiện dịch vụ.
- Không ghi DB. Không git. Không deploy.

## 2. Các bước

- [x] **Sửa script** `scripts/t74b_pilot_gemini_translate.py`: ghép toàn bộ phần của phản hồi (sửa lỗi cắt câu). (`_extract_full_text` đã có trong code, xác nhận qua các lần fix trước — fix..fix5).
- [x] **Gộp 5 tiểu sử mỗi yêu cầu**, có đánh số và mã định danh. Kiểm tra mã trong phản hồi; mã thiếu hoặc không khớp đưa vào hàng đợi thử lại, không gán nhầm. (`build_batch_prompt`/`parse_batch_response`, batch=5 xác nhận qua output chạy thật 2026-10-09).
- [x] **Đánh dấu còn chữ Hán** (không loại bỏ bản dịch). (`cjk_flag` xác nhận trong JSONL và output aggregate: "co chu Han sau dich: 0").
- [x] **Lưu tiến độ** để chạy tiếp từ chỗ dừng. Gặp hạn mức theo ngày thì dừng sạch và báo rõ. (`save_state`/`load_state`, `docs/evidence/T74b_pilot_state.json` đã ghi retry_queue sau lần chạy 2026-10-09; `quota_exhausted` field có nhưng chưa test thực tế vì lần này chỉ gặp lỗi 503, không phải 429).
- [x] **Giới hạn cứng**: tối đa 20 yêu cầu mỗi lần chạy. (`MAX_REQUESTS_HARD_CAP = 20`, xác nhận output: "da dat gioi han 20 yeu cau HTTP").
- [ ] **Kiểm thử không gọi API thật** (dùng phản hồi giả lập) để không tốn hạn mức. Script có self-test mock (`_consume_mock_budget` + phần "Self-test (mock)") nhưng CHƯA tự chạy lại bộ test này trong phiên này (nhiệm vụ chỉ cho phép chạy, không sửa/test code).
- [ ] **Lô ngày 1**: 100 tiểu sử (20 yêu cầu × 5). CHƯA đạt — lần chạy 2026-10-09 chỉ có 1/5 batch thành công (5 dila_id) do 4 batch lỗi HTTP 503 (model quá tải, không phải hết quota). Tổng dòng JSONL hợp lệ hiện tại: 5.
- [ ] **Lô thử 200 tiểu sử**: hoàn thành trong khoảng 2 ngày. CHƯA đạt, còn 20 dila_id trong retry_queue + phần chưa xử lý.
- [ ] **QA** (`daoanh-qa`) kiểm tra định dạng JSONL, số liệu, và xác nhận không có ghi DB. Chưa gọi QA trong phiên này.
- [ ] **Admin xem mẫu** ngẫu nhiên khoảng 20 bản khi đến lúc đánh giá chất lượng. Chưa tới lúc (mới 5 dòng).

### Log chạy 2026-10-09 15:57–16:04

- Lệnh: `python -X utf8 scripts/t74b_pilot_gemini_translate.py`
- Số yêu cầu HTTP đã dùng: 20/20 (giới hạn ngày đã chạm — KHÔNG chạy lại trong ngày hôm nay).
- Thành công: 5 (batch 1: A000421, A000574, A000686, A000691, A001018 — Hàng Sách, Tông Hoà, Ba La Phả Ca La Mật Đa La, Pháp Nguyệt, Kiên Tuệ).
- Lỗi: 4 batch (20 dila_id) — toàn bộ lỗi HTTP 503 "model đang quá tải", KHÔNG phải lỗi 429 hạn mức ngày.
- `quota_exhausted`: null (chưa chạm quota 429, chỉ chạm giới hạn cứng 20 request/lần).
- `retry_queue` còn lại: 20 dila_id (A000135, A000164, A000218, A000305, A000398, A001061, A001063, A001113, A001118, A001178, A001202, A001382, A001387, A001471, A001560, A001592, A001649, A001711, A001713, A001724).
- `gave_up`: rỗng (0).
- `stopped_reason`: `max_requests_reached`.
- Thời gian chạy: 6.2 phút. Ký tự đầu vào ~563, đầu ra ~2.098.
- Aggregate (`--aggregate`): 1 file JSONL, 5 dòng đọc được (0 lỗi JSON), 5 dila_id duy nhất, 0 dòng trùng, 0 dòng còn chữ Hán.
- Kiểm tra DB (`data/lineage.db`, mode=ro): `people.bio_vi` không rỗng = 10/48673 dòng (không đổi, có từ trước); `person_bio_vi_draft` = 2093 dòng. mtime file DB = 2026-10-09 15:25:02, TRƯỚC khi script chạy (15:57) — xác nhận script không ghi DB.
- **Chạy tiếp**: để ngày mai (2026-10-10) vì đã dùng hết 20 yêu cầu/ngày hôm nay. Khi chạy lại, script sẽ resume từ `retry_queue` (20 dila_id còn lại) + tiếp tục các dòng pilot chưa xử lý.

## 3. Ước tính

- Lô thử 200 tiểu sử: khoảng 2 ngày.
- Toàn bộ 5.790 tiểu sử đủ điều kiện: khoảng 58 ngày với free tier.

## 4. Khi dự án ổn định

Đổi cấu hình model sang API trả phí và chạy lại script. Quyết định này do Admin đưa ra.
