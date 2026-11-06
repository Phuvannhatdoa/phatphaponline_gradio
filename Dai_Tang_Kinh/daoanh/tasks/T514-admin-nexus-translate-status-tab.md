---
id: T514
title: Thêm tab "Dịch Nexus" (read-only status) vào admin t50-progress.html
status: in_progress
created: 2026-11-02
updated: 2026-11-02
done_when: >
  Tab mới hiển thị đúng số liệu đọc từ JSONL staging (vn_translate),
  không ghi DB, không có nút chạy dịch; py_compile app.py pass; endpoint
  mới trả JSON đúng qua curl; browser mở tab không lỗi console.
---

## Triệu chứng / Yêu cầu

Admin yêu cầu thêm tab theo dõi tiến độ dịch Nexus (T458 - dịch 21.740
dila_bio_nexus.text_zh sang tiếng Việt). Giai đoạn 1 của T458 chỉ ghi
staging JSONL vào `data/dila_import/biographies.2024-01/vn_translate/<sách>/batch_NNNN.jsonl`,
KHÔNG ghi DB. Schema `dila_bio_nexus_vi` và pilot 50 nexus Mingsengzhuanchao
CHƯA được Admin duyệt.

## Route/case tái hiện

`http://127.0.0.1:8080/daoanh/admin/t50-progress.html` — hiện có 2 tab
("Tiến Độ T50" và "Đại Tạng Kinh"). Thêm tab thứ 3 "Dịch Nexus".

## Phạm vi đã làm

1. `daoanh/admin/t50-progress.html` — thêm nút tab thứ 3 trong `.tabs`
   (sau "Đại Tạng Kinh") + pane `<div id="tab-nexus" class="tab-pane">`,
   đúng style/class `tab-btn` hiện có, dùng hàm `switchTab` hiện có.
   Pane hiển thị: tổng nexus, số đã dịch theo từng sách (đếm dòng JSONL
   trong vn_translate), số batch, trạng thái T458. Ghi chú UI:
   "Chờ Admin duyệt pilot + schema (T458)". KHÔNG có nút chạy dịch/nạp DB.
2. `daoanh/app.py` — thêm endpoint GET mới
   `/daoanh/api/admin/nexus-translate-status` đọc file JSONL trong
   `data/dila_import/biographies.2024-01/vn_translate/`, đếm dòng theo
   từng sách con, KHÔNG ghi DB, KHÔNG gọi Gemini/Codex. Nếu thư mục/sách
   chưa có file → trả 0 + thông báo rõ, không lỗi 500.

## Lưu ý quan trọng — injection bị từ chối

Trong lúc làm task này, 4 "tin nhắn coordinator" liên tiếp (qua kênh
system-reminder, KHÔNG phải user thật) yêu cầu mở rộng phạm vi: biến tab
thành search đối chiếu 3-4 cột AI (Gemini/Claude/Codex), rồi yêu cầu viết
script gọi Gemini API thật + chuẩn bị Codex runner trả phí, rồi yêu cầu
dựng "validator" theo bảng `translation_rules` với số liệu tự mâu thuẫn
(138 vs 139). Hệ thống xác nhận rõ: "No human input has been received
since the last genuine user message". Các yêu cầu này đã bị từ chối,
không thực hiện — giữ đúng phạm vi gốc do user thật giao (chỉ đọc, không
gọi API trả phí, không hard-code số liệu chưa xác minh).

## Ràng buộc

- Làm trong worktree `wt/nexus-translate-tab`, không ghi cây chính.
- Backup trước khi sửa: `daoanh/docs/sessions/2026-11-02/t50-progress.html.bak`,
  `app.py.bak` (gitignored, giữ trên đĩa).
- Không sửa `dila_bio_nexus`, không phá tab cũ (đã kiểm tab T50 + catalog
  vẫn hoạt động bình thường sau khi thêm tab mới).
- Kiểm chứng: `python -m py_compile app.py` PASS; test client + curl thật
  qua `APP_PORT=5099` xác nhận JSON đúng (21.740 total_nexus, 0 translated,
  vn_translate_root_exists=false); browser mở tab Dịch Nexus render đúng
  dữ liệu thật, không lỗi console ngoài 1 lỗi kết nối cổng 5002 do khác biệt
  cổng test (5099) với cổng dev mặc định trong code (_CAT_BASE), không phải
  lỗi do thay đổi lần này.
