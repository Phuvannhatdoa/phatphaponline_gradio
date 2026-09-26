# Session — Rà đặc tả nhầm "T119 Production Deployment & Support" (ráspec6)

**Ngày:** 2026-09-09 · **Commit:** `7d9b092f`

## Bối cảnh
Lee gửi đặc tả **header "T119 (Dành cho ClaudeCode)"** — "DEPLOYMENT_SPEC.md / Live Monitoring /
Support Feedback Loop / System Hardening / Maintenance / Beta / Data Freeze / Disaster Recovery /
query_log / PROJECT_STATUS.md → T119 Doing". **Header nhầm:** task T119 trong repo = Unified Editor
Dashboard (pending). "Production Deployment & Support" ≠ T119 → phân mảnh đúng chủ sở hữu.

## Phân mảnh (read-only, verified)
| Đặc tả | Chủ sở hữu | Trạng thái |
|---|---|---|
| Live Monitoring (NOT INDEXED → report) | **T112 D-Feedback** (`data_gap_requests`, ráspec5) | ✅ phủ; KHÔNG tạo `query_log` trùng |
| Maintenance `verify_design_compliance.py` | **T113** (đặc tả ghi "T117" SAI) | ✅ script có; cadence tháng/quý |
| System Hardening (Auth) | server.py :5001 + login/check + `deploy/nginx.conf` | 🟡 policy: public read-only không auth |
| Beta Phase · Data Freeze · Disaster Recovery · **Daily DB Snapshot** | **T116 D-Ops** (O1/O2/O3) | 🔴 backup chưa có → delta O1 |
| Support Feedback Inbox (Tăng Ni báo lỗi) | **T119 Gap 5** | 🔴 chưa có general endpoint → delta |
| `DEPLOYMENT_SPEC.md` / `PROJECT_STATUS.md` | ⛔ **A2: KHÔNG tạo** | — |

Delta thật (additive, nhỏ):
1. **T116 D-Ops**: `scripts/daily_backup.py` (sqlite `.backup`/`VACUUM INTO` → .gz, giữ 14 ngày, cron
   đêm) + Go-live runbook (Beta/Data Freeze/Disaster Recovery) + maintenance cadence → `docs/OPS_LOG.md`.
2. **T119 Gap 5**: bảng `user_feedback` (additive) + `POST /daoanh/api/feedback` (pattern `/report` ×7)
   + inbox trong `editor-dashboard.html`.

## Criterion Lee duyệt
- **Tính sư phạm**: T59 Learning Path + T111 scaffolding ✓
- **Tính chủ động**: T112 `data_gap_requests` + T119 `user_feedback` (2 kênh) ✓
- **Tính an toàn**: public read-only; admin qua login/check; backup + DR runbook (T116) ✓

## Cam kết
- KHÔNG tạo `DEPLOYMENT_SPEC.md`/`PROJECT_STATUS.md` (A2); KHÔNG bảng `query_log` trùng.
- 0 code, 0 DB phiên này; backup script = Track 2 (T116).

## Thay đổi (docs-only, 0 code, 0 DB)
1. `tasks/T119-editor-dashboard-bulk-review.md` — ráspec6 + Gap 5 (feedback inbox).
2. `tasks/T116-system-registry-handover.md` — D-Ops O1/O2/O3.
3. `tasks/T112-source-pending-activation.md` — note ráspec6 (query_log phủ).
4. `tasks/T113-qa-uat-compliance-meter.md` — note ráspec6 (maintenance owner, "T117" sai).
5. `docs/tasktodo.md` — ráspec6 ở T119 + note T116.
6. `docs/ROADMAP_META_UPDATE.md` §5 luật + §2 line (41 tasks).
7. `docs/ROLLBACK.md` — row `7d9b092f`.
8. Session này.

## Rollback
- `git revert --no-edit 7d9b092f` (docs-only, 0 DB).