---
id: T386
title: "Login admin bằng Google ID token (thay đăng nhập bằng chuỗi email)"
status: deferred
created: 2026-10-13
updated: 2026-10-13
owner: code (Hermes giao khi hết blocked)
parent: T382
module: Hạ tầng / Docs
priority: critical
depends_on: [T383]
dispatch: deferred
blocked_reason: "Chờ Admin tạo Google OAuth Client ID (Google Cloud Console → Credentials → OAuth client ID, loại Web, origin https://phatphaponline.org + http://127.0.0.1:8080) và ghi GOOGLE_CLIENT_ID vào .env. Có Client ID thì Admin đổi status sang pending."
plan_approved_at: "2026-10-13 (Admin phê chuẩn đề xuất ARCHITECTURE-REVIEW-2026-10-13-VERIFY.md, bước 3 — chọn Google ID token)"
done_when: >
  (1) `admin/login.html` dùng Google Identity Services (nút Sign in with Google), gửi `credential` (ID token) thay vì email.
  (2) `server.py` `/api/login/verify` kiểm ID token phía server (`google.oauth2.id_token.verify_oauth2_token` hoặc kiểm chữ
  ký JWKS): `aud == GOOGLE_CLIENT_ID`, `iss` là accounts.google.com, `email_verified == true`, email ∈ admin list. Gửi
  `{"email": ...}` trần ⇒ bị từ chối.
  (3) `verify_session` / `require_admin` kiểm lại email còn trong admin list mỗi lần (cache ngắn ≤ 60 giây). Xoá admin ⇒
  token cũ bị từ chối trong ≤ 60 giây.
  (4) Email admin không còn viết cứng trong `server.py` (đọc từ `data/admin_emails.txt` hoặc `.env`).
  (5) Test: token giả / aud sai / email_verified=false / email ngoài danh sách ⇒ từ chối (mock verify, không gọi Google thật).
  (6) Đăng nhập thật thành công trên local (ảnh chụp). Commit riêng tiền tố T386; Admin xác nhận DONE.
revert: >
  git revert --no-edit <sha_T386>. Bản sao server.py, admin/login.html, app.py vào docs/sessions/<ngày>/*.bak-before-T386.
  Nếu revert: đăng nhập quay về cách cũ (email trần) — chỉ dùng tạm khi khẩn cấp.
deferred: "Admin 2026-10-13: 'ngừng các giao thức bảo mật, acc test dùng duy nhất gmail để login, khi nào ver chính thức ra mắt trên Net ta sẽ config task security sau'"
undone_reason: "Admin hoãn phần bảo mật tới khi bản chính thức ra mắt trên Internet; giai đoạn test chỉ dùng tài khoản Gmail để đăng nhập."
undone_until: "Trước khi ra mắt bản chính thức trên Internet."
undone_action: "ADMIN: khi chuẩn bị ra mắt, đổi status về pending và dispatch về approved."
outcome: >
  2026-10-13: tạo task, blocked chờ Google Client ID.
---

# T386 — Login bằng Google ID token

## Mục tiêu

`server.py:108-122` cấp `session_token` cho bất kỳ ai POST đúng email admin — không chứng minh sở hữu email. Email admin
mặc định viết cứng ở `server.py:46`. Admin đã chọn Google ID token (dự án dùng Gmail sẵn).
Bằng chứng: `docs/reports/ARCHITECTURE-REVIEW-2026-10-13-VERIFY.md` (P0-1, C4).

## Phạm vi

Được sửa: `server.py`, `admin/login.html`, `app.py` (chỉ `verify_session`), `requirements.txt` (thêm `google-auth` nếu dùng),
tạo `tests/test_t386_google_login.py`. Cấm: commit `.env`/Client secret, deploy VPS, push.

## Các bước

- [ ] (Admin) Tạo OAuth Client ID, ghi `GOOGLE_CLIENT_ID` vào `.env` → đổi status sang pending
- [ ] Sao lưu 3 file
- [ ] login.html: Google Identity Services, gửi credential
- [ ] server.py: verify ID token + bỏ email viết cứng
- [ ] verify_session/require_admin: kiểm lại admin list có cache ngắn
- [ ] Test mock 4 trường hợp từ chối + 1 chấp nhận
- [ ] Đăng nhập thật trên local (ảnh chụp)
- [ ] Commit riêng `T386: …`
- [ ] daoanh-qa kiểm độc lập
- [ ] Admin xác nhận DONE
