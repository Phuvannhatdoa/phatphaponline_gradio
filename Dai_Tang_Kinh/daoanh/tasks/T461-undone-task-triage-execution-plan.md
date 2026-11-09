---
id: T461
title: "Điều phối xử lý task undone và QA theo lô"
status: in_progress
owner: coordinator
module: Harness / Điều phối
created: 2026-10-24
updated: 2026-10-24
done_when: >
  Mỗi lô task theo thứ tự giao việc có bằng chứng test và QA độc lập; mọi thay đổi có mutation đều có backup hoặc artifact rollback;
  task file, docs/tasktodo.md, session log và Dashboard được cập nhật; không task nào được đóng chỉ vì code đã tồn tại; Admin xác nhận DONE từng task.
---

## Mô tả

Điều phối các task còn dang dở (undone) thành lô theo thứ tự ưu tiên: QA các task đã build, sửa UI không ghi DB, tối ưu backend, ETL có kiểm soát, audit mapping, rồi hạ tầng an toàn. Mỗi lô phải có bằng chứng và QA độc lập trước khi xin Admin xác nhận. Task này chỉ điều phối tài liệu và Dashboard, không có thay đổi DB hay TTL.

# T461 — Điều phối task chưa hoàn tất

## Mục tiêu

Tập trung các task còn dang dở vào các lô có thể kiểm chứng, không tự đóng task
chỉ vì code đã tồn tại. Mỗi lô phải có bằng chứng, QA độc lập và xác nhận Admin.

## Thứ tự giao việc

1. **QA/đóng task đã build:** T417, T410, T453, T424, T425.
2. **Sửa UI độc lập, không ghi DB:** T406, T408.
3. **Profile rồi tối ưu backend:** T416.
4. **Tiếp tục ETL/dịch có kiểm soát:** T418 và T429/T458; giữ source bất biến,
   candidate/pending, chưa nhập production.
5. **Audit mapping và dữ liệu cần review:** T415, T275, T273.
6. **Hạ tầng an toàn có thể triển khai riêng:** T385, T387.

## Điều kiện DONE chung

- Có backup hoặc artifact rollback nếu có mutation.
- Có test cụ thể và log kết quả; không gọi `pipeline PASS` khi gate không chạy.
- Với dữ liệu danh tính, truyền thừa, số đời hoặc bản dịch: giữ `candidate`/
  `unreviewed`/`pending` cho tới khi Admin duyệt.
- Cập nhật task file, `docs/tasktodo.md`, session log và Dashboard.
- Không tự suy DILA ID, không tăng số đời, không nhập DB từ pilot chưa QA.

## Phạm vi không tự thực hiện

T200/T223/T233/T274 và các task blocked cần quyết định học thuật; T412/T413
phần mapping DB; T389 trước khi T232 chốt schema số đời; các task deferred về
bảo mật theo quyết định phát hành.

## Revert

Task này chỉ điều phối tài liệu và Dashboard. Không có DB/TTL mutation. Hoàn tác
bằng `git revert` commit tài liệu sau khi commit scoped; không xóa backup nguồn.
