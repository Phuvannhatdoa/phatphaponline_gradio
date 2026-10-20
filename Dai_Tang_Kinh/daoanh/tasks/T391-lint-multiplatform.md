---
id: T391
title: "Thêm npm lint script chạy được trên cả PowerShell (Windows) và Node.js (CI ubuntu-latest)"
status: in_progress
created: 2026-10-14
updated: 2026-10-15
owner: code
parent: T385
module: Hạ tầng / CI
priority: medium
depends_on: []
done_when: >
  (1) `scripts/lint-check.js` — bản port Node.js của `lint-check.ps1`, kiểm cú pháp
  inline `<script>` trong `admin/*.html`, bỏ qua các block JSX.
  (2) `package.json` script `lint` gọi `scripts/lint-check.js` qua `node`, chạy được
  trên cả Windows (PowerShell) và GitHub Actions ubuntu-latest.
  (3) `.github/workflows/deploy.yml` job `test` có bước `npm run lint`.
  (4) Commit riêng tiền tố T391; progress_data.json cập nhật qua
  `scripts/build_progress_data.py`.
outcome: >
  2026-10-14: commit 608e7d7 "T391: Add npm lint script for cross-platform CI" —
  package.json "lint" trước đó gọi trực tiếp PowerShell (`lint-check.ps1`), không chạy
  được trên runner ubuntu-latest của GitHub Actions. Thêm scripts/lint-check.js (port
  Node.js logic của lint-check.ps1: kiểm cú pháp inline <script> trong admin/*.html, bỏ
  qua JSX), đổi package.json "lint" sang gọi node, wire vào deploy.yml test job như
  "npm run lint". Thêm scripts/verify_db_backups.py (commit 1a26e3a) hỗ trợ kiểm backup
  DB trong pipeline. progress_data.json cập nhật qua commit 2a4059a.
  2026-10-15 (revert điều phối, Decision 4): status trả về `in_progress` — tách rõ với T392 (dọn file tài liệu
  tháng 4/2026), vốn trước đó mang `former_ids: [T391]` gây nhầm là cùng một task. T391 (lint script) và T392
  (dọn docs) là hai việc khác nhau; giữ T391 `in_progress` chờ xác nhận lại độc lập với T392.
---

# T391 — npm lint script chạy đa nền tảng cho CI

## Mục tiêu

`package.json` script `lint` gọi trực tiếp `lint-check.ps1` bằng PowerShell — chỉ chạy
được trên máy Windows của Admin, không chạy được trên GitHub Actions runner
(`ubuntu-latest`) dùng trong `.github/workflows/deploy.yml` (xem T385). Cần bản lint
chạy được cả hai nơi.

## Phạm vi

Được sửa: `scripts/lint-check.js` (mới), `package.json`, `.github/workflows/deploy.yml`
(bước `npm run lint` trong job `test`). Không đổi logic kiểm tra — chỉ port sang Node.js.

## Các bước

- [x] Viết `scripts/lint-check.js` port từ `lint-check.ps1` (kiểm cú pháp inline
  `<script>` trong `admin/*.html`, bỏ qua block JSX)
- [x] Đổi `package.json` script `lint` sang gọi `node scripts/lint-check.js`
- [x] Thêm bước `npm run lint` vào job `test` của `deploy.yml`
- [x] Test local: `npm run lint` chạy xanh trên Windows
- [x] Commit riêng `T391: Add npm lint script for cross-platform CI` (608e7d7)
- [x] Cập nhật `data/progress_data.json` (2a4059a)
- [x] Thêm `scripts/verify_db_backups.py` hỗ trợ kiểm backup DB (1a26e3a)

## Liên quan

- T385 (`tasks/T385-pause-auto-deploy.md`) — job `test` trong `deploy.yml` mà lint này
  được wire vào.
