---
id: T464
title: "Bug verify: BUG-051: thêm menu DILA Team Agent Dashboard vào Điều hướng"
status: done
created: 2026-10-25
updated: 2026-10-25
done_when: "Sidebar trang /daoanh/admin/ (file daoanh/admin/index.html) có thêm 1 mục <a class=\"nav-btn\"> tên 'DILA Team Agent Dashboard' trong khu 'Điều hướng' (không tạo khu mới, không đổi thứ tự Place VN/Hệ thống/Đại Tạng Kinh/Cài đặt), href mở đúng http://127.0.0.1:8090/dashboard/agent_team.html?source=real; daoanh-qa xác nhận bằng browser thật tại 127.0.0.1:8080/daoanh/admin/ (screenshot sidebar, đọc href, click thử ghi lại kết quả mở được hay lỗi)."
---

## Mô tả

Thêm mục menu "DILA Team Agent Dashboard" vào khu Điều hướng của sidebar trang admin, mở trang Agent Dashboard (cổng 8090). Phạm vi: chỉ thêm một mục vào `daoanh/admin/index.html`, không đổi các khu khác. Trang Agent Dashboard có nút quay về Statistics Dashboard (`admin/placevn.html`).

## Triệu chứng / Yêu cầu

Route: `http://127.0.0.1:8080/daoanh/admin/` (file thật: `daoanh/admin/index.html`).

Admin yêu cầu thêm 1 mục menu mới vào khu "Điều hướng" của sidebar:
- Tên hiển thị: **DILA Team Agent Dashboard**
- Khi click mở: `http://127.0.0.1:8090/dashboard/agent_team.html?source=real`
  (giữ đúng URL, kể cả query `?source=real`)

## Bối cảnh / Ràng buộc

- Sidebar hiện tại có thứ tự: Điều hướng → Place VN → Hệ thống → Đại Tạng Kinh → Cài đặt.
  KHÔNG đổi thứ tự các khu khác, KHÔNG tạo khu mới — chỉ thêm 1 `<a>` vào khu "Điều hướng".
- Mẫu mục sidebar hiện có: `<a class="nav-btn">` chứa `<div style="display:flex;...">`
  với icon Font Awesome + `<span>` tên + `<i class="fa-solid fa-chevron-right">`.
  Mục mới phải bám đúng mẫu này để đồng nhất giao diện.
- Port đích 8090 khác với app chính (5000/8080). Cần kiểm tra port 8090 có đang chạy
  không trước khi báo done. Nếu KHÔNG chạy: vẫn thêm menu đúng, nhưng phải ghi rõ
  trong báo cáo "trang đích hiện không mở được" — KHÔNG tự bật server 8090 nếu
  không rõ nó là gì.

## Phạm vi dự kiến

- `daoanh/admin/index.html` — thêm 1 `<a>` vào khu "Điều hướng". Không sửa file khác.

## Việc cần làm

1. daoanh-debugger:
   - Backup `daoanh/admin/index.html` vào
     `daoanh/docs/sessions/2026-10-25/index.html.bak-before-agent-team-menu`.
   - Đọc cấu trúc khu "Điều hướng" hiện tại, xác định đúng icon/markup mẫu.
   - Thêm 1 `<a class="nav-btn" href="http://127.0.0.1:8090/dashboard/agent_team.html?source=real">`
     theo đúng mẫu (icon + span tên "DILA Team Agent Dashboard" + chevron-right).
   - Kiểm tra port 8090 có đang listen không (không tự bật nếu không rõ).
   - Mở browser thật tại `127.0.0.1:8080/daoanh/admin/`, screenshot sidebar cho thấy
     menu mới đúng vị trí trong khu Điều hướng, đọc href thực tế, click thử và ghi
     lại kết quả (mở được trang đích hay lỗi kết nối/404), kèm network log nếu có.
   - Không git add/commit/reset. Để status `in_progress` chờ QA.
2. daoanh-qa: kiểm chứng độc lập bằng browser thật — xác nhận vị trí menu, href
   đúng URL, kết quả click, không regression các mục menu khác trong Điều hướng
   và các khu Place VN/Hệ thống/Đại Tạng Kinh/Cài đặt (thứ tự và nội dung giữ nguyên).

## Kết quả thực hiện (daoanh-debugger, 2026-10-25)

- Backup: `daoanh/docs/sessions/2026-10-25/index.html.bak-before-agent-team-menu` (tạo trước khi sửa).
- File sửa: `daoanh/admin/index.html` — thêm 1 `<a class="nav-btn">` vào cuối khu
  "Điều hướng" (sau "Webview", trước khi đóng `</div>` của section, trước khu
  "Place VN"). Không đổi thứ tự Place VN/Hệ thống/Đại Tạng Kinh/Cài đặt, không tạo
  khu mới. Markup bám đúng mẫu hiện có (`<div style="display:flex;align-items:center;gap:8px">`
  + icon Font Awesome `fa-solid fa-robot` + `<span>DILA Team Agent Dashboard</span>`
  + `<i class="fa-solid fa-chevron-right" style="font-size:8px"></i>`).
- href thực tế (đọc bằng JS trên trang live, không phải source): 
  `http://127.0.0.1:8090/dashboard/agent_team.html?source=real` — khớp 100% yêu cầu.
- Port 8090: **đang chạy** (xác nhận `Get-NetTCPConnection -LocalPort 8090 -State Listen`
  → LISTEN, PID 1036). Không tự bật server, chỉ xác nhận trạng thái.
- Browser thật: mở `http://127.0.0.1:8080/daoanh/admin/`, chụp screenshot sidebar
  (`daoanh/docs/sessions/2026-10-25/T464/sidebar_menu_added.jpg`) — thấy menu
  "DILA Team Agent Dashboard" đúng vị trí cuối khu Điều hướng, khu Place VN vẫn
  nguyên vị trí/nội dung ngay sau đó.
- Click thử bằng `computer.left_click` thật (không phải JS inject): tab điều hướng
  thành công sang `http://127.0.0.1:8090/dashboard/agent_team.html?source=real`,
  tiêu đề tab đổi thành "DILA Team — Agent Dashboard", trang hiển thị dữ liệu thật
  (danh sách task `daoanh/tasks/*.md`, kể cả thấy T464 đang `in_progress` trong
  danh sách). Screenshot kết quả click:
  `daoanh/docs/sessions/2026-10-25/T464/click_result_8090.jpg`.
- Network log (20 request gần nhất lọc theo "8090"): hàng loạt `GET
  http://127.0.0.1:8090/daoanh/tasks/T*.md → 200 OK`; 1 request phụ
  `GET /api/task-contexts → 404` (endpoint phụ của trang đích, không liên quan
  menu/href vừa thêm).
- Không regression: quay lại `127.0.0.1:8080/daoanh/admin/`, chụp lại sidebar —
  khu Điều hướng đủ 5 mục đúng thứ tự (Thống kê, Dashboard Process Tracker,
  Panorama, Webview, DILA Team Agent Dashboard), khu Place VN/Hệ thống/Đại Tạng
  Kinh/Cài đặt không đổi.
- Không `git add/commit/reset`. Status giữ `in_progress`, chờ `daoanh-qa` kiểm
  chứng độc lập.
