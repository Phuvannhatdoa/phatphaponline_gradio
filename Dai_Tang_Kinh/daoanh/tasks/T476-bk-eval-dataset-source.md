---
id: T476
title: "BK-EVAL (bộ dữ liệu đánh giá tri thức kinh điển Phật giáo, DILA): xác minh nguồn trên web, để sau"
status: deferred
created: 2026-10-26
updated: 2026-10-26
owner: coordinator
module: Data / Evaluation
priority: low
depends_on: []
done_when: >
  (1) Admin xác nhận BK-EVAL có tồn tại công khai; ghi đường dẫn repo chính thức, ngày cập nhật, giấy phép và định dạng dữ liệu.
  (2) Nếu có và có nhu cầu cụ thể (ví dụ dùng để đánh giá chất lượng bản dịch): tải về vào data/dila_import/ kèm SHA256; không ghi DB.
  (3) Đề xuất có dùng hay không; chờ Admin duyệt.
  (4) daoanh-qa ĐẠT; Admin xác nhận DONE.
revert: >
  Xoá thư mục tải về. Không đụng DB.
---

## Mô tả
BK-EVAL là bộ dữ liệu đánh giá tri thức kinh điển Phật giáo (Buddhist Canon Knowledge Evaluation Dataset). Được liệt kê trong tổ chức GitHub của DILA. Task này để sau, chỉ kích hoạt khi có nhu cầu cụ thể.

## Căn cứ hiện có
- Tìm kiếm WebSearch ngày 2026-10-26 cho biết: trang [github.com/DILA-edu](https://github.com/DILA-edu) liệt kê repo **BK-EVAL**, mô tả là "Buddhist Canon Knowledge Evaluation Dataset", cập nhật lần cuối **2026-05-21**. Đây là kết quả tìm kiếm, chưa mở trực tiếp để kiểm tra.
- Tìm theo tên "DILA-edu BK-EVAL" không cho kết quả trực tiếp.

## Hướng dẫn tìm trên web (cho Admin)
1. Mở [github.com/DILA-edu](https://github.com/DILA-edu). Tìm repo có tên chứa "BK-EVAL" hoặc "eval".
2. Ghi lại: đường dẫn repo, ngày commit gần nhất, phần mô tả, giấy phép (mục LICENSE hoặc README), số file, định dạng (JSON, CSV, Parquet…).
3. Đọc README để biết bộ dữ liệu có gì: câu hỏi, đáp án, nguồn kinh điển nào, cách chấm.
4. Nếu không thấy repo tên đó, tìm lại bằng từ khóa "knowledge evaluation" hoặc "Buddhist canon benchmark" trong tổ chức DILA-edu.
5. Gửi lại cho coordinator: đường dẫn và các mục trên. Chưa tải về cho đến khi có nhu cầu.

## Điều kiện kích hoạt
- Có nhu cầu đánh giá chất lượng bản dịch Gemini/Claude bằng bộ chuẩn, hoặc Admin yêu cầu cụ thể.

## Phạm vi
- Trong: xác minh nguồn, tải về khi được kích hoạt, đề xuất sử dụng.
- Ngoài: tích hợp vào PTDA; ghi DB.
