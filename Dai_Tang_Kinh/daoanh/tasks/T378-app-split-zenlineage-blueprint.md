---
id: T378
title: "Tách app.py bước 1: nhóm route zenlineage (5 route) sang blueprint api_zenlineage.py"
status: in_progress
created: 2026-10-13
updated: 2026-10-13
owner: claude-code (phiên housekeeping 2026-10-13)
parent: T364
plan_approved_at: "2026-10-13 (Admin duyệt qua chat)"
dispatch: approved
done_when: >
  (1) 5 route /daoanh/api/admin/zenlineage/* chuyển sang api_zenlineage.py theo mẫu factory
  có sẵn (api_ttl_anchor.py: create_*_blueprint), đăng ký trong app.py.
  (2) Danh sách route (rule + method) từ app.url_map trước = sau (363 rule).
  (3) `import app` chạy sạch; test client gọi /daoanh/api/admin/zenlineage/stats trả cùng
  kết quả như trước (chỉ đọc).
  (4) Commit riêng, revert được bằng `git revert <sha>`.
  (5) Admin xác nhận DONE.
revert: >
  git revert --no-edit <sha_T378>. Bản sao trước khi sửa:
  docs/sessions/2026-10-13/housekeeping/app.py.bak-before-T378.
outcome: >
  2026-10-13: Tách app.py dòng 2445–2749 (305 dòng) sang api_zenlineage.py (325 dòng, factory
  create_zenlineage_blueprint(get_db_connection)), đăng ký cạnh api_ttl_anchor ở cuối app.py. Route map
  (rule+method) trước = sau: 363 = 363 (diff rỗng). 3 GET (stats, candidates approved, candidates q=mazu) trả
  JSON giống hệt. Tên endpoint đổi thành zenlineage.* (không có url_for nào dùng). py_compile + pyflakes OK
  (1 cảnh báo `cur` không dùng có sẵn từ trước). Dashboard build không đổi. Server đang chạy (PID app.py) vẫn
  chạy bản cũ trong RAM tới khi restart. Commit: <sha_T378>. Chờ daoanh-qa + Admin.
---

# T378 — Tách app.py bước 1 (zenlineage blueprint)

T364 chưa định nghĩa "pha an toàn đầu tiên" nên chọn phương án dự phòng đã được duyệt: tách một
nhóm route nhỏ, tự chứa sang Flask blueprint. Chọn nhóm **zenlineage** (T139 Phase 2, 5 route,
`app.py` ~dòng 2443–2747) vì chỉ phụ thuộc `get_db_connection` và 2 helper riêng `_zen_*`; không
có `url_for` nào trong app.py trỏ tới endpoint này.

## Các bước

- [x] Ghi baseline route map (`app.url_map`) + kết quả `/zenlineage/stats`
- [x] Sao lưu app.py
- [x] Tạo `api_zenlineage.py` (`create_zenlineage_blueprint(get_db_connection)`)
- [x] Gỡ khối zenlineage khỏi app.py, đăng ký blueprint
- [x] So route map trước/sau; gọi lại `/zenlineage/stats` bằng test client
- [ ] Commit riêng, tiền tố `T378`
- [ ] Admin xác nhận DONE
