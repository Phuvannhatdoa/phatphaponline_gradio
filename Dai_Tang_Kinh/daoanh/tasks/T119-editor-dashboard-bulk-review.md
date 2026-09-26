---
id: T119
title: "Unified Editor Dashboard + Bulk Review + History Viewer"
module: Admin / HITL Workflow
priority: medium
depends_on: [T100, T109, T111]
created: 2026-09-09
updated: 2026-09-10
status: in_progress
---

# T119 — Unified Editor Dashboard + Bulk Review + History Viewer

## Bối cảnh
Rà đặc tả "Curation & Editor Workflow" (2026-09-09): cơ chế HITL đã xây dựng xong
(T100 claim review + T109 conflict resolution + bio-review approve/reject/bulk). 4 UI
gaps còn thiếu — convenience, KHÔNG phải lỗi hồi quy.

## 4 gaps cần xử lý

### Gap 1: Unverified claims list endpoint
- **Hiện tại:** `GET /api/admin/verification/list` load từ JSON file, KHÔNG query `entity_claims`.
- **Yêu cầu:** `GET /daoanh/api/admin/claims/unverified?page=&per_page=` — query
  `SELECT * FROM entity_claims WHERE verification_status='unverified' ORDER BY created_at DESC`
  + pagination + total count.
- **Zero-RAM:** không load toàn bộ 447,885; dùng LIMIT/OFFSET.

### Gap 2: Bulk claim review endpoint
- **Hiện tại:** chỉ `POST /daoanh/api/admin/claims/<id>/review` (per-claim).
- **Yêu cầu:** `POST /daoanh/api/admin/claims/bulk-review` — body:
  `{"claim_ids":[1,2,3],"verdict":"verified","editor":"admin","assertion_level":"medium"}`.
  Iterate → UPDATE `verification_status/reviewed_by/at` + INSERT `en_audit_log` per claim.
- **Pattern mẫu:** `admin/bio-review.html` đã có `POST .../bulk-approve`.

### Gap 3: Unified Editor Dashboard
- **Hiện tại:** 24 trang admin riêng lẻ, không trang tổng hợp.
- **Yêu cầu:** `admin/editor-dashboard.html` — tổng hợp 3 hàng chờ:
  1. Unverified claims (count + paginated list + bulk approve)
  2. Conflict queue (40,327 open — link tới `admin/conflicts.html`)
  3. Bio-review pending (link tới `admin/bio-review.html`)
  + Stats bar: total claims, verified %, conflict open, bios pending.
- **Pattern:** `admin/bio-review.html` (fetch API + table + pagination).

### Gap 4: Resolution History viewer
- **Hiện tại:** `resolutions_log` = 0 rows, không UI browse lịch sử.
- **Yêu cầu:** `GET /daoanh/api/admin/resolutions/history?page=&per_page=` — query
  `resolutions_log JOIN lineage_conflicts_v2` + render timeline trong dashboard.

## Ràng buộc
- KHÔNG ALTER bảng base; 0 migration; 0 bảng mới.
- Chỉ đọc + UPDATE `verification_status/reviewed_by/at` trên `entity_claims` (đã có sẵn).
- Revert = git revert (0 DB thay đổi schema; data revert theo `en_audit_log` old/new_value).
- `npm run pipeline` PASS trước review.

## Acceptance (dự kiến)
- 3 endpoints mới (claims/unverified, claims/bulk-review, resolutions/history) hoạt động.
- `admin/editor-dashboard.html` render 3 hàng chờ + stats.
- Zero-RAM: query OFFSET/LIMIT, không load toàn bộ 447,885.
- Pipeline PASS. Verify: bio-review.html vẫn hoạt động hồi quy.

## Trạng thái
- **pending** — Track 2, chờ Lee duyệt sau Track 1 (docs). ~1,5 ngày.

## Rà đặc tả nhầm "T119 Production Deployment & Support" (ráspec6 2026-09-09)
Lee gửi đặc tả **header "T119 (Dành cho ClaudeCode)"** — "DEPLOYMENT_SPEC.md / Live Monitoring /
Support Feedback / System Hardening / Maintenance / Beta / Data Freeze / Disaster Recovery / query_log /
PROJECT_STATUS.md → T119 Doing". **Header nhầm** (task này = Unified Editor Dashboard). Phân mảnh:

| Đặc tả | Chủ sở hữu | Trạng thái |
|---|---|---|
| Live Monitoring (NOT INDEXED → report) | **T112 D-Feedback** (ráspec5: `data_gap_requests`) | ✅ phủ; KHÔNG tạo `query_log` trùng |
| Maintenance định kỳ `verify_design_compliance.py` | **T113** (đặc tả ghi "T117" SAI) | ✅ script có; cadence tháng/quý |
| Beta Phase · Data Freeze · Disaster Recovery · Daily Backup | **T116 D-Ops** (ráspec6) | 🟡 runbook + snapshot backup thêm |
| System Hardening (Auth) | **server.py :5001 + login/check + deploy/nginx.conf** | 🟡 có; policy: public read-only không auth |
| `DEPLOYMENT_SPEC.md` | ⛔ **A2: KHÔNG tạo** (SSOT = T116 + nginx.conf) | — |
| `PROJECT_STATUS.md` → "Doing" | ⛔ không tồn tại (SSOT = tasktodo/roadmap) | — |
| **Support Feedback Inbox** (Tăng Ni báo lỗi sai/thiếu nguồn) | **task này (T119)** — DELTA THẬT | 🔴 chưa có general endpoint |

### Mở rộng T119 — Gap 5: General User Feedback Inbox
- **Bảng additive `user_feedback`**: `id` · `entity_id` · `entity_type` · `feedback_type`
  ('sai_dữ_liệu'|'thiếu_nguồn'|'lỗi_hiển_thị'|'khác') · `note_plain` · `user_level` ·
  `created_at` · `status` ('new'|'ack'|'closed'). 0 ALTER base, chỉ INSERT.
- `POST /daoanh/api/feedback` (public, rate-limit đơn giản — không cần login, tái dùng pattern
  `/report` ×7 sẵn có).
- `GET /daoanh/api/admin/feedback?status=new&page=` + inbox trong `editor-dashboard.html`
  (hàng chờ thứ 4, cạnh unverified/bulk-review/history) → Lee trả lời treat trong en_audit_log.
- KHÔNG tạo bảng `query_log` riêng (khớp = T112 `data_gap_requests`; feedback = báo lỗi chủ động).

## X?y d?ng Batch B (2026-09-10) ? IMPLEMENTED
- `admin/editor-dashboard.html` (tabs: Claims / Feedback / Data Gaps / Resolutions / Audit / Geo Enrichment; stats bar).
- Endpoints m?i:
  - `GET /daoanh/api/admin/entity-claims/unverified?page=&per_page=&entity_type=&status=`
  - `POST /daoanh/api/admin/claims/bulk-review` ? {ids[], verdict, assertion_level, editor} ? m?i claim 1 d?ng en_audit_log.
  - `GET /daoanh/api/admin/resolutions/history` (resolutions_log JOIN lineage_conflicts_v2).
  - `GET /daoanh/api/admin/feedback?status=` + `POST /daoanh/api/feedback` (Gap 5, public) + `POST .../feedback/<id>/status`.
  - `GET /daoanh/api/admin/editor-stats` (th?ng k? thanh ??u trang).
- Zero-RAM: LIMIT/OFFSET, kh?ng load 447,885 claims.
- Tr?ng th?i: **in_progress** ? ch? Lee review h?i quy ? done.
