---
id: T388
title: "Dashboard JSON bị nginx chặn trên VPS + allowlist file tĩnh cho local_gateway"
status: deferred
created: 2026-10-13
updated: 2026-10-13
owner: code (Hermes giao)
parent: T382
module: Hạ tầng / Docs
priority: medium
depends_on: []
dispatch: deferred
plan_approved_at: "2026-10-13 (Admin phê chuẩn đề xuất ARCHITECTURE-REVIEW-2026-10-13-VERIFY.md, mục C1 + P1-5)"
done_when: >
  (1) `dashboard/dashboard_process.html` không còn fetch trực tiếp `../data/*.json` (dòng ~644, 1718, 1860, 1967, 2047): đọc qua
  route API chỉ-đọc trong app.py (ví dụ `GET /daoanh/api/dashboard/data/<name>` với allowlist tên file cố định:
  t263_h3_status, task_directives, directives_progress), hoặc thêm `location =` cụ thể trong `deploy/nginx.conf` cho đúng các
  file đó. Chọn một cách, ghi lý do. Không nới regex chặn `.json` chung.
  (2) `local_gateway.py` chỉ phục vụ file tĩnh theo allowlist đuôi (.html .js .css .png .jpg .svg .ico .woff2 .ttl? — chốt
  trong session log) và thư mục cho phép; từ chối `.db`, `.env`, `.log`, `.bak*`, `.py`, `data/` (trừ `data/ttl/` và các JSON
  dashboard nếu chọn cách nginx), `docs/sessions/`.
  (3) Test: gateway trả 403/404 cho `/daoanh/.env`, `/daoanh/data/lineage.db`, `/daoanh/app.py`; vẫn trả 200 cho
  `/daoanh/places`, `/dashboard/dashboard_process.html`. Dashboard local tải đủ panel (ảnh chụp).
  (4) Commit riêng tiền tố T388; Admin xác nhận DONE.
revert: >
  git revert --no-edit <sha_T388>. Bản sao 3 file vào docs/sessions/<ngày>/*.bak-before-T388.
deferred: "Admin 2026-10-13: 'ngừng các giao thức bảo mật, acc test dùng duy nhất gmail để login, khi nào ver chính thức ra mắt trên Net ta sẽ config task security sau'"
undone_reason: "Admin hoãn phần bảo mật tới khi bản chính thức ra mắt trên Internet; giai đoạn test chỉ dùng tài khoản Gmail để đăng nhập."
undone_until: "Trước khi ra mắt bản chính thức trên Internet."
undone_action: "ADMIN: khi chuẩn bị ra mắt, đổi status về pending và dispatch về approved."
outcome: >
  2026-10-13: tạo task, chưa làm.
---

# T388 — Dashboard JSON + allowlist gateway

## Mục tiêu

- Trên VPS, `deploy/nginx.conf:48` chặn mọi `^/daoanh/data/.*\.json` ⇒ 5 panel dashboard fetch `../data/*.json` nhận 403.
- `local_gateway.py:65-88` phục vụ mọi file trong `daoanh/` (kể cả `.env`, `lineage.db`). Mặc định chỉ bind 127.0.0.1 nên
  mức P2, nhưng nguy hiểm khi chạy `--lan`.
Bằng chứng: `docs/reports/ARCHITECTURE-REVIEW-2026-10-13-VERIFY.md` (P1-5, C1).

## Phạm vi

Được sửa: `dashboard/dashboard_process.html`, `local_gateway.py`, `deploy/nginx.conf` (chỉ file trong repo), `app.py` nếu thêm
route đọc. Cấm: sửa nginx thật trên VPS, deploy, push.

## Các bước

- [ ] Sao lưu file sẽ sửa
- [ ] Chọn cách phục vụ JSON dashboard (API hoặc nginx location cụ thể), ghi lý do
- [ ] Sửa dashboard fetch
- [ ] Allowlist local_gateway + test
- [ ] Kiểm dashboard local đủ panel (ảnh chụp)
- [ ] Commit riêng `T388: …`
- [ ] daoanh-qa kiểm độc lập
- [ ] Admin xác nhận DONE
