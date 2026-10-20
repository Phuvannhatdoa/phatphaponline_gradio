---
id: T384
title: "Đóng endpoint nguy hiểm: tắt run_etl_gen, sửa path traversal /api/update_file"
status: deferred
created: 2026-10-13
updated: 2026-10-13
owner: code (Hermes giao)
parent: T382
module: Hạ tầng / Docs
priority: critical
depends_on: [T383]
dispatch: deferred
plan_approved_at: "2026-10-13 (Admin phê chuẩn đề xuất ARCHITECTURE-REVIEW-2026-10-13-VERIFY.md, bước 2)"
done_when: >
  (1) `POST /daoanh/api/admin/run_etl_gen` trả 410 (Gone) kèm thông báo "tạm khoá — chờ T389/T232", không chạy
  subprocess; UI nút gọi endpoint này (tìm trong admin/*.html, places.html) hiển thị đúng thông báo.
  (2) `POST /api/update_file`: `id` chỉ nhận regex `^[A-Za-z0-9_.-]{1,120}$`, không chứa `..`; `realpath` của file đích
  phải nằm trong `TTL_MASTER_DIR`; vi phạm ⇒ 400. Có test cho `../x`, `..\\x`, đường dẫn tuyệt đối, id hợp lệ (dùng thư
  mục tạm, không ghi TTL thật).
  (3) Rà các route ghi file khác có ghép đường dẫn từ input (`/api/save-ttl`, `/api/save_ttl_v2`, `/api/rebuild/save_master`,
  `/daoanh/api/admin/monk_ttl`): áp cùng kiểm tra; liệt kê kết quả trong session log.
  (4) py_compile + guard + test PASS; commit riêng tiền tố T384; Admin xác nhận DONE.
revert: >
  git revert --no-edit <sha_T384>. Bản sao: docs/sessions/<ngày>/app.py.bak-before-T384.
deferred: "Admin 2026-10-13: 'ngừng các giao thức bảo mật, acc test dùng duy nhất gmail để login, khi nào ver chính thức ra mắt trên Net ta sẽ config task security sau'"
undone_reason: "Admin hoãn phần bảo mật tới khi bản chính thức ra mắt trên Internet; giai đoạn test chỉ dùng tài khoản Gmail để đăng nhập."
undone_until: "Trước khi ra mắt bản chính thức trên Internet."
undone_action: "ADMIN: khi chuẩn bị ra mắt, đổi status về pending và dispatch về approved."
outcome: >
  2026-10-13: tạo task, chưa làm.
---

# T384 — Đóng endpoint nguy hiểm

## Mục tiêu

- `run_etl_gen` (`app.py` ~L24787) chạy `scripts/etl_gen_compute.py` có `DROP TABLE person_gen_computed`,
  `DELETE FROM lineage_founders`, offset cứng `+37` — công khai, không auth. Khoá lại cho tới khi T389/T232 xong.
- `/api/update_file` (`app.py` ~L14261) ghép `id` thẳng vào đường dẫn ⇒ ghi file `.ttl` ra ngoài thư mục.

Bằng chứng: `docs/reports/ARCHITECTURE-REVIEW-2026-10-13-VERIFY.md` (P1-2, C2, C4).

## Phạm vi

Được sửa: `app.py` (2 route trên + các route ghi file liệt kê ở done_when), tạo `tests/test_t384_dangerous_endpoints.py`.
Cấm: chạy `etl_gen_compute.py`, ghi DB, sửa TTL thật, deploy, push. Không xoá script.

## Các bước

- [ ] Sao lưu app.py
- [ ] Tìm UI gọi run_etl_gen; đổi endpoint về 410 + thông báo
- [ ] Viết helper `_safe_child_path(base, name)` (regex + realpath) và áp vào update_file
- [ ] Rà 4 route ghi file còn lại, áp helper nếu ghép đường dẫn từ input
- [ ] Test traversal trên thư mục tạm
- [ ] py_compile, guard, test PASS
- [ ] Commit riêng `T384: …`; SHA vào revert + docs/ROLLBACK.md
- [ ] daoanh-qa kiểm độc lập
- [ ] Admin xác nhận DONE
