---
id: T382
title: "Bảo mật & phát hành an toàn — kế hoạch từ Architecture Review 2026-10-13 (task cha)"
status: pending
created: 2026-10-13
updated: 2026-10-13
owner: Admin + root (điều phối)
module: Hạ tầng / Docs
priority: critical
depends_on: []
plan_approved_at: "2026-10-13 (Admin: 'phê chuẩn đề xuất này' — đề xuất trong ARCHITECTURE-REVIEW-2026-10-13-VERIFY.md)"
done_when: >
  T383–T389 đều được Admin xác nhận DONE (hoặc Admin chủ động deferred). Task cha không giao agent;
  root chỉ theo dõi.
revert: >
  Mỗi task con revert độc lập bằng `git revert --no-edit <sha>` của chính nó (một task = một commit,
  xem docs/process/REVERT_ONE_FIX.md). Task cha không có thay đổi code.
undone_reason: "Phần bảo mật (T383, T384, T386, T388) hoãn theo Admin 2026-10-13 tới khi ra mắt bản chính thức; T385, T387, T389 (an toàn deploy/backup/dữ liệu) vẫn làm."
undone_until: "Trước khi ra mắt bản chính thức trên Internet."
undone_action: "ADMIN: khi chuẩn bị ra mắt, đổi status về pending và dispatch về approved."
outcome: >
  2026-10-13: tạo kế hoạch + 7 task con. Cùng ngày Admin hoãn phần bảo mật: T383/T384/T386/T388 = deferred
  (dispatch: deferred). Còn giao Hermes: T385, T387, T389.
---

# T382 — Bảo mật & phát hành an toàn (task cha)

## Mục tiêu

Đóng các lỗ P0/P1 đã kiểm chứng trong `docs/reports/ARCHITECTURE-REVIEW-2026-10-13-VERIFY.md`
trước khi mở rộng dữ liệu hoặc thêm tính năng: login không chứng minh sở hữu email, 95/111 route ghi
không auth, endpoint ETL công khai, path traversal, deploy tự động không qua test, backup copy file WAL.

## Nguồn

- Báo cáo gốc: [`docs/reports/ARCHITECTURE-REVIEW-2026-10-13.md`](../docs/reports/ARCHITECTURE-REVIEW-2026-10-13.md)
- Kiểm chứng + đề xuất đã duyệt: [`docs/reports/ARCHITECTURE-REVIEW-2026-10-13-VERIFY.md`](../docs/reports/ARCHITECTURE-REVIEW-2026-10-13-VERIFY.md)
- Kế hoạch chi tiết: [`docs/plans/T382-security-release-hardening-PLAN.md`](../docs/plans/T382-security-release-hardening-PLAN.md)

## Task con (thứ tự giao)

| Task | Việc | Mức | depends_on | File chính |
|---|---|---|---|---|
| [T383](T383-admin-write-guard.md) | Chặn auth tập trung cho mọi route ghi + `/admin/` (before_request + allowlist + test quét url_map) | P0 | — | `app.py`, `tests/` |
| [T384](T384-close-dangerous-endpoints.md) | Tắt `run_etl_gen`; sửa path traversal `/api/update_file` | P0 | T383 | `app.py` |
| [T385](T385-pause-auto-deploy.md) | Tắt deploy tự động theo push; gate test + pin host key + health check | P0 | — | `.github/workflows/deploy.yml` |
| [T386](T386-google-id-token-login.md) | Login bằng Google ID token thay email trần; kiểm lại admin mỗi request | P0 | T383 | `server.py`, `admin/login.html`, `app.py` |
| [T387](T387-sqlite-backup-api-and-safe-sync.md) | Backup bằng SQLite backup API; sync VPS upload tên mới + kiểm + swap nguyên tử | P1 | — | `scripts/backup_db_daily.py`, `sync_to_vps.ps1`, script restore |
| [T388](T388-dashboard-json-and-gateway-allowlist.md) | Dashboard JSON bị nginx 403 trên VPS; allowlist file tĩnh cho local gateway | P1/P2 | — | `dashboard/dashboard_process.html`, `local_gateway.py`, `deploy/nginx.conf` |
| [T389](T389-legacy-generation-scheme-label.md) | Engine số đời cũ (`+37`): backup trước DROP, gắn nhãn scheme, chờ T232 thay | P1 | T384 | `scripts/etl_gen_compute.py` |

## Các bước

- [x] Kiểm chứng báo cáo kiến trúc (read-only) — `ARCHITECTURE-REVIEW-2026-10-13-VERIFY.md`
- [x] Admin phê chuẩn đề xuất (2026-10-13)
- [x] Tạo kế hoạch + task con T383–T389 (`dispatch: approved`)
- [ ] T383 DONE
- [ ] T384 DONE
- [ ] T385 DONE
- [ ] T386 DONE
- [ ] T387 DONE
- [ ] T388 DONE
- [ ] T389 DONE
