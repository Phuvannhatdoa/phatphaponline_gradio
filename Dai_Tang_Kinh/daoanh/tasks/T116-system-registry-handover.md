---
id: T116
title: "System Registry & Handover Protocol — Roadmap Meta-Update (Self-documenting)"
module: Project Management / Docs / Governance
priority: medium
depends_on: [T114, T115]
created: 2026-09-09
updated: 2026-09-10
status: done
done_when: >
  docs/ROADMAP_META_UPDATE.md tồn tại (bản v1.0) gồm: Version Snapshot thật, Data Traps Map,
  Navigation Index trỏ SSOT (KHÔNG copy), Meta-Governance; task này được Lee Tổng phê duyệt
  → status done + ROLLBACK row hash-fill + regen dashboard.
---

# T116 — System Registry & Handover Protocol

## Bối cảnh
Lee đưa "Đặc tả khái niệm T114 (Roadmap Meta-Update)" yêu cầu file `/docs/ROADMAP_META_UPDATE.md`
là "bản đồ di sản" Self-documenting. **T114 đã DONE** (task đóng, commits `e822336`/`b15678e`/`ba57c039`)
→ phần Registry này là **T116** (docs-only, không re-open T114).

## Rà đối chiếu đặc tả (2026-09-09)
| # | Đặc tả | Thực trạng (verified) | Quyết định |
|---|---|---|---|
| C1 | Cập nhật `/docs/PROJECT_STATUS.md` | File KHÔNG tồn tại — SSOT = tasktodo/roadmap/dashboard/tasks | KHÔNG tạo (quyết định A1/T113 giữ nguyên); đính chính bảng STATUS bên dưới |
| C2 | Tạo `/docs/ROADMAP_META_UPDATE.md` nguyên khối | 2/4 nội dung trùng SSOT (Dependency ≡ SOURCE_REGISTRY/AUTHORITY_MATRIX; Baseline ≡ design_compliance+M7.2) | Tạo đúng tên file nhưng nội dung = **Registry điều hướng + Handover** (no-copy) |
| C3 | "Kích hoạt Task T114" | T114 đã done | Nội dung registry = **T116** |
| C4 | Version Snapshot "phiên bản lineage.db + schema" | DB **không** có bảng schema_version/migrations → version = git HEAD | Ghi trung thực: git HEAD `23660b6` |
| C5 | "tổng số Assertion" | 447,885 claims · 3,530 events · assertion_level 0% | Ghi số thật làm baseline |
| C6 | Provenance "Audit ID (SHA-256)" | `entity_claims_audit.audit_id` = 64 hex SHA-256 ✓ | ĐÚNG khớp — giữ nguyên tiêu chí |

### Bảng STATUS đính chính (đặc tả ghi sai)
| Task | Đặc tả ghi | Thực tế | Nguồn |
|---|---|---|---|
| T111 | "Doctrine Retrieval Engine" / Done | **Persona Display Layer + ZenQ Disclaimer** / done | `tasks/T111-...md`; "3 cấp" = L1/L2/L3 |
| T113 | Done | **in_progress** (Phần A PASS · Phần B DONE · alert #4/#5 mở) | `tasks/T113-...md` |
| T114 | Doing | **done** | `tasks/T114-...md` |
| — | Cột "Người phụ trách" | Repo không track người — thay bằng **commit hash** | — |

## Deliverable
- `docs/ROADMAP_META_UPDATE.md` (v1.0): §1 Mục tiêu · §2 Version Snapshot · §3 Data Traps Map ·
  §4 Navigation Index (SSOT) · §5 Meta-Governance. Append-only, no-copy.
- `docs/tasktodo.md` · `docs/roadmap.md` (row T116, header T108–T116) · `docs/ROLLBACK.md` (row).
- Session `docs/sessions/2026-09-09_t116-system-registry.md` · regen `data/progress_data.json`.

## Rollback
- `git revert --no-edit <hash A>` (docs-only, 0 code, 0 DB).

## Việc kế tiếp
- ⏳ Lee Tổng duyệt bản Registry → T116 `status: done` + hash-fill.
- T113 alert #4/#5: chờ Lee review conflicts.
- T112 §5: chờ Lee duyệt activation 8 nguồn.

## D-Ops (ráspec6 2026-09-09 — từ đặc tả nhầm "T119 Production Deployment & Support")
Thêm deliverable vận hành thuộc task này (spec-holder Deployment/Ops; **KHÔNG tạo DEPLOYMENT_SPEC.md**):

### O1 — Daily Database Snapshot (genuine delta: chưa có DB backup)
- Lệnh backup: `sqlite3 lineage.db ".backup 'snap/lineage_YYYYMMDD.db'"` hoặc `VACUUM INTO`,
  nén `.gz`, giữ **N=14 ngày** (xoá cũ), chạy cron đêm (0 2 * * *).
- `scripts/daily_backup.py` (Zero-RAM copy qua sqlite backup API, không lock DB trong thời gian dài;
  **read-only** đối với lineage.db; an toàn lúc đang chạy).
- Trạng thái backup → `docs/OPS_LOG.md` (append-only) hoặc bảng `ops_log` additive.
- Restore: doc `git revert` cho code; **DB restore** = copy snapshot+gz về → xác minh
  `verify_design_compliance.py` lại sau restore.

### O2 — Go-live Runbook (Beta · Data Freeze · Disaster Recovery)
- **Beta Phase:** chỉ Pilot (nhóm Tăng Ni nhỏ) — nginx cho phép by allowlist; keep read-only.
- **Data Freeze:** giai đoạn Canonical chốt (T116) — mọi thay đổi phải theo lệnh Admin;
  `source_authority` không đổi ngoài T112 activation được duyệt.
- **Disaster Recovery:** 3 lớp — git (code/docs) + `daily_backup.py` (DB) + `docs/OPS_LOG.md`
  (manual runbook last-resort).

### O3 — Maintenance cadence
- Chạy lại **`scripts/verify_design_compliance.py` (T113, không phải T117)** định kỳ tháng/quý →
  ghi kết quả vào `docs/OPS_LOG.md` + `design_compliance.json` regen → báo Lee nếu metric lệch chuẩn.
- `query_log` (đặc tả DEPLOYMENT) = **T112 D-Feedback** (`data_gap_requests`) — KHÔNG bảng trùng.

### Cam kết
- Additive docs + script; 0 ALTER bảng base; backup read-only với lineage.db; revert = git revert.

## X?y d?ng Batch B + Lee ph? duy?t (2026-09-10)
- **D-Ops O1 IMPLEMENTED**: `scripts/daily_backup.py` (sqlite online `backup()` API + gzip +
  sha256 verify + gi? 14 ng?y + prune; ghi `docs/OPS_LOG.md` append-only). Verified OK ??m ??u.
- Cron ?? ngh?: `0 2 * * * python scripts/daily_backup.py >> data/backup.log 2>&1`.
- O2 (Go-live runbook Beta/Data Freeze/DR) + O3 (maintenance cadence) ?? l? docs trong m?c D-Ops.
- **? Lee ph? duy?t Registry (Batch A, 2026-09-10) ? task ??ng.**
