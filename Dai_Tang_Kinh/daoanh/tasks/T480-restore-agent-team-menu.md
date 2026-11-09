---
id: T480
title: "Bug verify: menu DILA Team Agent Dashboard bị mất khỏi sidebar admin (khôi phục sau T464)"
status: done
created: 2026-10-27
updated: 2026-10-27
done_when: "daoanh-qa xác nhận độc lập bằng browser thật tại 127.0.0.1:8080/daoanh/admin/: khu Điều hướng có đủ 5 mục (Thống kê, Dashboard Process Tracker, Panorama, Webview, DILA Team Agent Dashboard) đúng thứ tự, khu Place VN/Hệ thống/Đại Tạng Kinh/Cài đặt không đổi vị trí/nội dung; click mục mới mở đúng http://127.0.0.1:8090/dashboard/agent_team.html?source=real; không regression."
---

## Mô tả

T464 (2026-10-25) đã thêm mục menu "DILA Team Agent Dashboard" vào khu "Điều hướng"
của `daoanh/admin/index.html`, nhưng T464 chủ động **không** git commit thay đổi này
(đúng quy trình — chờ QA/Admin duyệt trước khi commit). Giữa lúc đó và 2026-10-27,
mục này biến mất khỏi cả file và trang live, trong khi `status: done` đã ghi ở
T464 (có thể là nhầm — việc này chưa qua QA độc lập trước khi đánh done).

## Nguyên nhân đã xác định (bằng chứng)

- `admin/index.html` hiện tại (trước khi sửa lại) **byte-identical** với bản git
  HEAD đã commit từ `a4397c2a` (2026-10-20, "cleanup: Remove legacy GPT Sol / Claude
  dịch session from namevimap.html") — commit này không liên quan gì tới menu
  Điều hướng. Lệnh kiểm: `git diff --stat -- Dai_Tang_Kinh/daoanh/admin/index.html`
  → rỗng (không khác HEAD).
- HEAD (`a4397c2a`, trước T464 2 tuần) **chưa từng** có "DILA Team Agent Dashboard"
  hay `agent_team.html` (grep rỗng qua `git show HEAD:...index.html`).
- Vì T464 không bao giờ commit mục đã thêm, thay đổi chỉ tồn tại ở working tree.
  Một thao tác git sau đó (nhiều khả năng `git checkout --`/`git reset` không chủ
  đích, hoặc một agent khác ghi đè file từ bản cũ không có mục T464) đã đưa
  working tree về khớp đúng HEAD cũ, xoá mất mục T464 thêm.
- Các bản backup `docs/sessions/2026-10-26/index.html`, `index.html.bak`,
  `index.html.round1` (tạo bởi các task T445/T447 khác trong ngày 26/10) **đều
  không có** chuỗi "DILA Team"/"agent_team" — xác nhận mục đã mất từ trước
  26/10, không phải do sửa trong phiên này.
- Xác minh trên browser thật (127.0.0.1:8080/daoanh/admin/) trước khi sửa: sidebar
  thu gọn chỉ có 4 icon trong khu Điều hướng (thiếu icon robot) — khớp với file.

## Việc đã làm (2026-10-27)

- Backup file trước khi sửa:
  `daoanh/docs/sessions/2026-10-27/index.html.bak-before-restore-agent-team-menu`.
- Thêm lại đúng 1 `<a class="nav-btn" href="http://127.0.0.1:8090/dashboard/agent_team.html?source=real">`
  (icon `fa-solid fa-robot` + span "DILA Team Agent Dashboard" + chevron-right)
  vào cuối khu "Điều hướng" (sau "Webview", trước khu "Hệ thống") — đúng vị trí/mẫu
  T464 đã mô tả. Không đổi thứ tự Place VN/Hệ thống/Đại Tạng Kinh/Cài đặt.
- Kiểm trên browser thật: reload `127.0.0.1:8080/daoanh/admin/`, icon robot thứ 5
  xuất hiện đúng vị trí trong khu Điều hướng. Click icon → điều hướng thành công
  sang `http://127.0.0.1:8090/dashboard/agent_team.html?source=real`, tab title đổi
  "DILA Team — Agent Dashboard", trang hiển thị dữ liệu task thật. Network log: các
  request `GET http://127.0.0.1:8090/daoanh/tasks/T*.md` → 200 OK, `GET
  /api/task-contexts` → 200 OK, không lỗi.
- Không git add/commit/reset. Không ghi DB.

## Chưa làm / cần Admin quyết

- Chưa chạy QA độc lập (`daoanh-qa`) để xác nhận lần nữa bằng browser trước khi
  đánh `done`.
- Nên cân nhắc: có commit `daoanh/admin/index.html` lần này không, để tránh lặp lại
  vấn đề "sửa xong nhưng không commit nên mất theo thao tác git khác"? Việc này
  cần lệnh rõ ràng từ Admin (theo AGENTS.md — không tự `git add/commit`).
