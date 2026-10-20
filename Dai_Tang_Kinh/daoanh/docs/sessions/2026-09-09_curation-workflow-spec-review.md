# Session — Rà đặc tả "Curation & Editor Workflow" (HITL ĐÃ CÓ + TẠO T119)

**Ngày:** 2026-09-09 · **Commit:** `bac72e9`

## Bối cảnh
Lee gửi đặc tả tiêu đề **"Task T118: Curation & Editor Workflow"**; bên trong ghi **"ĐẶC TẢ KHÁI
NIỆM T116"** và lệnh vận hành gọi **"Task T116"** — T116 (repo) = System Registry docs-only, hoàn toàn
khác. Yêu cầu tạo `CURATION_WORKFLOW_SPEC.md` + update `PROJECT_STATUS.md` (= lặp lỗi SSOT đã tránh).

## Kết luận (read-only, verified)
**Cơ chế HITL đã xây dựng xong bởi T100 + T109 + bio-review + T221 + namevi-approve.** Đặc tả mô tả lại
công việc đã có; phần thiếu chỉ là **tiện ích giao diện**.

### Phủ (verified)
| Đặc tả | Hiện trạng |
|---|---|
| HITL 3 bước (Review→Acceptance→Commit) | `entity_claims.verification_status` + `POST /claims/<id>/review` (reviewed_by/at) |
| Audit Log (ai/lúc nào/lý do) | `en_audit_log` (editor·evidence·created_at·old/new) + `resolutions_log` (resolved_by/at·notes) |
| Dispute Resolution UI side-by-side | `admin/conflicts.html` (DILA vs Marcus) |
| Không tự động Canonical | 447,885 claim = 100% `unverified`; L1 clips verified (=0→honest empty) |
| Bio-review pattern (approve/reject/bulk) | ✅ `admin/bio-review.html` + 4 endpoints |
| T221 staged approval + namevi-approve | ✅ |

### 4 UI gaps (→ T119, Track 2)
1. `GET /api/admin/verification/list` load JSON — không query `entity_claims` (447,885).
2. Chỉ per-claim review — thiếu bulk endpoint.
3. 24 trang admin riêng lẻ — thiếu unified editor dashboard.
4. `resolutions_log` = 0 rows — thiếu history viewer.

## Cam kết
- KHÔNG tạo `CURATION_WORKFLOW_SPEC.md` (trùng T109 + SCHEMA_DESIGN + PROVENANCE_POLICY +
  lineage-conflict-implementation.md + SOURCE_AUTHORITY_MATRIX).
- KHÔNG update `PROJECT_STATUS.md` (SSOT = tasktodo/roadmap); KHÔNG re-open T109.
- Ghi nhận ráspec2 ở T109 + task mới **T119**.

## Thay đổi (docs-only, 0 code, 0 DB)
1. `tasks/T109-provenance-conflict-workflow.md` — mục "Rà đặc tả Curation & Editor Workflow".
2. `tasks/T119-editor-dashboard-bulk-review.md` — task mới (pending, Track 2, ~1,5 ngày).
3. `docs/ROADMAP_META_UPDATE.md` §5 — luật Curation workflow = T100+T109 infra + 4 gaps → T119.
4. `docs/tasktodo.md` — `ráspec2` ở T109 + dòng T119.
5. `docs/roadmap.md` — 2 bảng + rows T119.
6. `docs/ROLLBACK.md` — row `bac72e9`.
7. Session này.

## Rollback
- `git revert --no-edit bac72e9` (docs-only, 0 DB).