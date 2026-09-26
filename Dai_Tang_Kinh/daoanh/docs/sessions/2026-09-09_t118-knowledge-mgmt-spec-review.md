# Session — Rà đặc tả nhầm "T118 Knowledge Base Management & User Training" (ráspec5)

**Ngày:** 2026-09-09 · **Commit:** `f608da9a`

## Bối cảnh
Lee gửi đặc tả **header "T118 (Dành cho ClaudeCode)"** — "KNOWLEDGE_MGMT_SPEC.md / Learning Path /
Academic Scaffolding / Curation Registry / Feedback Loop / cập nhật PROJECT_STATUS.md".
**Header nhầm:** task T118 trong repo = Research Audit Tier API (pending, Track 2). "Knowledge
Base Management & User Training" là feature khác → phân mảnh đúng chủ sở hữu.

## Phân mảnh (read-only, verified)
| Đặc tả | Chủ sở hữu | Trạng thái |
|---|---|---|
| Academic Scaffolding (Cử nhân→Tiến sĩ) | **T111** persona `?level=L1/L2/L3` | ✅ DONE |
| Tách Canonical / Draft | **T100/T108** `verification_status` + assertions gating | ✅ kiến trúc |
| Learning Path (đi theo truyền thừa) | **T59** (Giáo Dục) — nền: `lineage_chronology` 49,560 · Nexus graph · events 3,530 | 🟡 data có, UI chưa |
| Curation Registry / Knowledge Packages | **T59** + **T119** (editor đóng gói) | 🔴 UI chưa |
| **Feedback Loop** (NOT INDEXED → yêu cầu bổ sung → admin → T112) | **T112** D-Feedback | 🔴 chưa logging |

Criterion Lee duyệt:
- **Tính sư phạm**: Learning Path → T59 (có home) · scaffolding → T111 ✓
- **Tính chủ động**: `data_gap_requests` + admin report (delta thật) ✅
- **Tính an toàn**: learner public read-only + level-filter (T111); draft/canonical tách rõ ✓

## Cam kết
- KHÔNG tạo `KNOWLEDGE_MGMT_SPEC.md` / `LEARNING_PATH_SPEC.md` (A2: SSOT = SCHEMA_DESIGN +
  tasktodo/roadmap; T59 = spec-holder cho Learning Path/Curation).
- KHÔNG update `PROJECT_STATUS.md` (không tồn tại; SSOT = tasktodo/roadmap).
- KHÔNG gán "Knowledge Mgmt" cho T118; 0 code phiên này.

## Thay đổi (docs-only, 0 code, 0 DB)
1. `tasks/T118-research-audit-tier-api.md` — mục ráspec5 (bảng phân mảnh).
2. `tasks/T112-source-pending-activation.md` — D-Feedback D1/D2/D3 (`data_gap_requests` + admin
   report + ánh xạ gap→8 nguồn).
3. `tasks/T59-giao-duc.md` — mở rộng scope: Learning Path + Curation Registry.
4. `docs/tasktodo.md` — ráspec5 ở T118 + note D-Feedback ở T112.
5. `docs/ROADMAP_META_UPDATE.md` §5 luật.
6. `docs/ROLLBACK.md` — row `f608da9a`.
7. Session này.

## Rollback
- `git revert --no-edit f608da9a` (docs-only, 0 DB).