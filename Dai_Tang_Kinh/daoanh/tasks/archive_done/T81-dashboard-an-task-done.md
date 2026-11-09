---
id: T81
title: "Dashboard — ẩn task DONE khỏi board, bỏ gạch ngang"
module: Dashboard / Harness
priority: medium
status: done
depends_on: []
created: 2026-10-11
updated: 2026-10-20
done_when: >
  Board chỉ còn cột Pending / In-progress / Blocked;
  bug/task được Admin PASSED bị ẩn khỏi bảng bug (không gạch ngang), cả khi tải lại trang;
  thống kê tổng vẫn đếm đủ task DONE;
  Admin xác nhận trên dashboard.
---

# T81 — Dashboard: ẩn task DONE

## Triệu chứng / yêu cầu

Admin: "task nào passed DONE thì remove khỏi board luôn, không cần gạch ngang tên task nữa".

## Phạm vi đã sửa (`daoanh/dashboard/dashboard_process.html`)

- `renderTaskBoard`: bỏ cột Done khỏi board. Thống kê tổng vẫn giữ nguyên.
- `adminBugDone` và khôi phục từ localStorage: đặt `display:none` thay vì gạch ngang.
- Bảng "ĐÃ DONE" tĩnh (T112, T34): xóa khỏi trang.

Backup trước khi sửa: `daoanh/docs/sessions/2026-10-11/dashboard_process.html`.

## Kiểm chứng

Chờ `daoanh-qa` và bằng chứng screenshot trên dashboard.
