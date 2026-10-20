---
id: T383
title: "Chặn auth tập trung: before_request cho mọi route ghi và /admin/ + test quét url_map"
status: deferred
created: 2026-10-13
updated: 2026-10-13
owner: code (Hermes giao)
parent: T382
module: Hạ tầng / Docs
priority: critical
depends_on: []
dispatch: deferred
plan_approved_at: "2026-10-13 (Admin phê chuẩn đề xuất ARCHITECTURE-REVIEW-2026-10-13-VERIFY.md, bước 1)"
done_when: >
  (1) app.py có một hook `@app.before_request` trả 401 cho mọi request method POST/PUT/DELETE/PATCH và mọi
  path chứa `/admin/` (kể cả GET) khi không có token admin hợp lệ — trừ allowlist tường minh.
  (2) Allowlist nằm ở một hằng số duy nhất, mỗi mục có comment lý do; mặc định không có gì.
  (3) Test `tests/test_t383_admin_write_guard.py` (pytest, Flask test client, không ghi DB thật) quét
  `app.url_map`: mọi rule ghi hoặc `/admin/` ngoài allowlist mà gọi không token ⇒ 401; có token giả lập hợp lệ ⇒ không 401.
  Test phải FAIL nếu ai đó thêm route ghi mới mà không có auth.
  (4) Route đọc công khai (GET không /admin/) vẫn trả như cũ: so trước/sau 20 GET công khai mẫu.
  (5) `npm run guard` PASS; `python -m py_compile app.py` PASS; route map trước = sau.
  (6) Commit riêng tiền tố T383; Admin xác nhận DONE.
revert: >
  git revert --no-edit <sha_T383>. Bản sao trước khi sửa: docs/sessions/<ngày>/app.py.bak-before-T383.
deferred: "Admin 2026-10-13: 'ngừng các giao thức bảo mật, acc test dùng duy nhất gmail để login, khi nào ver chính thức ra mắt trên Net ta sẽ config task security sau'"
undone_reason: "Admin hoãn phần bảo mật tới khi bản chính thức ra mắt trên Internet; giai đoạn test chỉ dùng tài khoản Gmail để đăng nhập."
undone_until: "Trước khi ra mắt bản chính thức trên Internet."
undone_action: "ADMIN: khi chuẩn bị ra mắt, đổi status về pending và dispatch về approved."
outcome: >
  2026-10-13: tạo task, chưa làm.
---

# T383 — Chặn auth tập trung cho route ghi

## Mục tiêu

Đóng 95 route ghi không có auth trong `app.py` bằng **một** chỗ kiểm tra thay vì sửa từng route.
Hiện trạng đo 2026-10-13 (AST scan): 311 route, 111 route ghi, chỉ 16 có `verify_session`; không có `before_request`;
nginx `location /daoanh/api/` proxy thẳng vào app.py. Chi tiết: `docs/reports/ARCHITECTURE-REVIEW-2026-10-13-VERIFY.md` (P0-2).

## Phạm vi

- Được sửa: `app.py` (thêm hook + allowlist + helper `_is_admin_request()`), tạo `tests/test_t383_admin_write_guard.py`,
  thêm script `test:t383` vào `package.json`.
- Token: header `Authorization: Bearer <token>` (cách admin pages đang gửi — kiểm lại trong `admin/*.html` trước khi viết).
  Kiểm bằng `verify_session()` hiện có (`app.py:91`). Cache kết quả kiểm theo token ~30 giây để không gọi server.py mỗi request.
- Ứng viên allowlist cần đọc code xác nhận rồi mới thêm (không đoán): `POST /daoanh/api/feedback`, `POST /daoanh/api/translate`,
  `POST /api/translate/hvdic`, `POST /daoanh/api/daitang/qa`, các route `*/translate/report`. Route nào gọi LLM trả phí thì
  KHÔNG đưa vào allowlist — báo Admin.
- Không đổi hành vi bên trong route; các `verify_session` cũ giữ nguyên.

## Cấm

Ghi DB, đổi schema, sửa server.py (thuộc T386), deploy VPS, git push. Không xoá route.

## Các bước

- [ ] Sao lưu app.py vào docs/sessions/<ngày>/app.py.bak-before-T383
- [ ] Liệt kê route ghi + /admin/ (AST hoặc url_map) → lưu danh sách vào session log
- [ ] Đọc frontend gọi các POST công khai, chốt allowlist (ghi lý do từng mục)
- [ ] Viết hook + helper + cache
- [ ] Viết test quét url_map + test 20 GET công khai trước/sau
- [ ] py_compile, guard, test PASS; route map trước = sau
- [ ] Kiểm thật trên local: trang admin vẫn lưu được khi đăng nhập; gọi không token ⇒ 401 (ảnh chụp/network log)
- [ ] Commit riêng `T383: …`; ghi SHA vào revert + docs/ROLLBACK.md
- [ ] daoanh-qa kiểm độc lập
- [ ] Admin xác nhận DONE
