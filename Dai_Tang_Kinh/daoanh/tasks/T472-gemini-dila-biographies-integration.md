---
id: T472
title: "Tích hợp Gemini cho DILA Biographies: dịch nexus (test free) nối kết quả Cloud, rồi dịch lại toàn bộ khi có API chuẩn"
status: pending
created: 2026-10-26
updated: 2026-10-26
owner: coordinator
module: Data / Biographies / Translation
priority: high
parent: T453
depends_on: [T457, T458]
done_when: >
  (1) Script dịch Gemini (translate_gemini.py) đọc khóa từ biến môi trường GEMINI_API_KEY; không commit file có khóa.
  (2) Chạy thử part07 lô 1–50 vào thư mục test; so với buxu07/buxu07_b01.json; không ghi đè bản Cloud.
  (3) Validator đạt: ký tự CJK không lẫn trong bản Việt, không có dấu "/", summary không quá dài, thẻ XML đúng, giữ nguyên mọi nexus id.
  (4) Nối bản Gemini với bản Cloud đã có (vn_bio_nexus/*.vi.xml) thành một bộ kết quả; không mất nexus id nào; ghi rõ nguồn từng nexus (cloud_session hoặc gemini_free).
  (5) Đọc tay 5 nexus ngẫu nhiên mỗi lô; ghi kết quả vào báo cáo.
  (6) XML DILA gốc không đổi (SHA256 trước = sau).
  (7) daoanh-qa ĐẠT; Admin xác nhận DONE.
revert: >
  Không ghi DB. Xoá thư mục kết quả test; bản Cloud trong vn_bio_nexus/ không bị đụng.
---

# T472 — Tích hợp Gemini cho DILA Biographies

## Mô tả
Dùng Gemini (gói free, để test) dịch tiếp các đoạn nexus còn lại của DILA Biographies, bắt đầu từ part07 của Buxu_GSZ. Nối kết quả Gemini với bản Cloud đã dịch (vn_bio_nexus/) thành một bộ kết quả thống nhất. Khi code và quy trình đã đạt, Admin sẽ mua API chuẩn và dịch lại toàn bộ từ Hán văn.

## Quyết định của Admin (2026-10-26)
- Duyệt kế hoạch `docs/plans/gemini_dila_ptda_integration_plan.md` cho phạm vi dịch nexus.
- Giai đoạn này dùng Gemini free. Khóa đang đặt cứng trong code vì là môi trường dev test.
- Sau khi quy trình ổn định, Admin mua API chuẩn để dịch lại toàn bộ DB từ Hán văn.

## Hiện trạng (đo 2026-10-26)
- Kết quả Cloud đã có: `data/dila_import/biographies.2024-01/vn_bio_nexus/` gồm `Buxu_GSZ.vi.xml`, `biQiuNi.vi.xml`, `Mingsengzhuanchao.vi.xml` và các zip đóng gói.
- Nguồn nexus: `nexus_src_parts/` gồm 48 file (`Buxu_GSZ.part01`…). Mỗi phần tối đa khoảng 500 nexus.
- Script `translate_gemini.py` và hướng dẫn `PLAN_GEMINI.md` hiện nằm trên máy cloud (`scratchpad/nexus2/`, `scratchpad/handoff/`), **chưa có trên máy này**.
- Lưu ý: `無見頂` (part07 nexus 18–19) và `無見覩` ở nexus khác có thể là hai người khác nhau. Phải kiểm trước khi thống nhất tên.

## Phạm vi
- Trong: dịch part07 (Buxu_GSZ) thử nghiệm; sau đó part07 b02–07, part05, part06, part08, part01–04; nối với bản Cloud; validator; báo cáo.
- Ngoài: dịch lại toàn bộ bằng API chuẩn (chờ Admin mua); import vào PTDA; ghi DB; commit khóa API.

## Chỉ thị điều phối
- **OpenCode (coder):** đưa script và hướng dẫn vào máy này trước. Sửa script để đọc khóa từ `GEMINI_API_KEY`. Không ghi khóa vào file.
- **OpenRouter (tester):** chạy validator và kiểm tra theo checklist trên, báo PASS/FAIL kèm bằng chứng.
- **Claude Code (QA/điều phối):** xác nhận DONE sau khi Admin duyệt đối chiếu 5 nexus ngẫu nhiên mỗi lô.

## Rủi ro
- Khóa cứng trong code có thể bị commit. Khuyến nghị dùng biến môi trường ngay cả khi test.
- Gemini free có giới hạn lượt gọi; script phải dừng và ghi lỗi, không ghi file nửa vời.
- Lệch nghĩa không máy kiểm được; chỉ bắt bằng đọc tay.
