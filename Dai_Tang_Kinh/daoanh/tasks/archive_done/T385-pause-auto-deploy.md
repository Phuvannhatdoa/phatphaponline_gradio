---
id: T385
title: "Tắt deploy tự động theo push; deploy chỉ chạy tay sau khi test xanh"
status: done
created: 2026-10-13
updated: 2026-10-14
owner: code (Hermes giao)
parent: T382
module: Hạ tầng / Docs
priority: critical
depends_on: []
dispatch: approved
plan_approved_at: "2026-10-13 (Admin phê chuẩn đề xuất ARCHITECTURE-REVIEW-2026-10-13-VERIFY.md, bước 2)"
done_when: >
  (1) `.github/workflows/deploy.yml` (repo root visjs-app) chỉ còn trigger `workflow_dispatch` — bỏ `push: branches: [master]`.
  (2) Có job `test` chạy trước (`npm run guard`, `npm run dup:ids`, `python -m py_compile` cho app.py/server.py, các pytest
  không cần DB thật); job `deploy` có `needs: test`.
  (3) Bỏ `StrictHostKeyChecking=no`; host key lấy từ secret `VPS_KNOWN_HOSTS` (ghi hướng dẫn Admin thêm secret).
  (4) Sau restart: health check gọi API thật (ví dụ `GET /daoanh/api/dila/stats` qua curl trên VPS) — fail ⇒ job fail.
  (5) Ghi commit SHA đã deploy vào file trên VPS (`DEPLOYED_COMMIT`) để biết production chạy commit nào.
  (6) Commit riêng tiền tố T385; Admin xác nhận DONE.
revert: >
  git revert --no-edit <sha_T385> (chỉ file workflow).
outcome: >
  2026-10-13: tạo task, chưa làm.
  2026-10-14: commit 0b7ee28 "T385: Pause auto-deploy on push, require workflow_dispatch
  with health check" — .github/workflows/deploy.yml đổi trigger sang workflow_dispatch only,
  thêm job test (guard, lint, py_compile app.py/server.py, dup:ids, npm test) với deploy
  needs: [build, test], StrictHostKeyChecking=yes dùng secret VPS_KNOWN_HOSTS, health check
  gọi curl http://127.0.0.1:5000/daoanh/api/dila/stats thật trên VPS (retry 30x2s), ghi
  DEPLOYED_COMMIT. Admin xác nhận DONE 2026-10-14.
---

# T385 — Tắt deploy tự động theo push

## Mục tiêu

Hiện `deploy.yml` deploy **mỗi push lên master**, không chạy test, `StrictHostKeyChecking=no`, restart vô điều kiện.
`master` đang ahead 737 commit so với origin ⇒ một lần push sẽ đẩy cả 737 commit chưa kiểm lên production.
Bằng chứng: `docs/reports/ARCHITECTURE-REVIEW-2026-10-13-VERIFY.md` (C4).

## Phạm vi

Được sửa: `.github/workflows/deploy.yml`. Cấm: push, chạy workflow, SSH vào VPS, sửa secret (chỉ ghi hướng dẫn cho Admin).

## Các bước

- [x] Sao lưu deploy.yml vào docs/sessions/<ngày>/
- [x] Đổi trigger sang workflow_dispatch
- [x] Thêm job test + `needs: test`
- [x] Pin host key qua secret; health check API thật; ghi DEPLOYED_COMMIT
- [x] Kiểm cú pháp YAML (`python -c "import yaml,sys;yaml.safe_load(open(...))"`)
- [x] Ghi hướng dẫn thêm secret `VPS_KNOWN_HOSTS` cho Admin trong session log
- [x] Commit riêng `T385: …` (0b7ee28)
- [x] daoanh-qa kiểm độc lập
- [x] Admin xác nhận DONE
