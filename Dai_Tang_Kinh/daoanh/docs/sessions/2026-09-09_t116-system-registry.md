# Session — T116 System Registry & Handover (đặc tả "T114 cũ" → deliverable)

**Ngày:** 2026-09-09 · **Commit:** `f64d798`

## Bối cảnh
Lee đưa "Đặc tả khái niệm T114 — Roadmap Meta-Update" yêu cầu tạo `/docs/ROADMAP_META_UPDATE.md`
("bản đồ di sản" Self-documenting) + cập nhật `/docs/PROJECT_STATUS.md` + "kích hoạt T114".
Đã rà đối chiếu với thực trạng và chốt phương án tối ưu.

## Các quyết định thiết kế (phan phê chuẩn)
| # | Đặc tả | Quyết định tối ưu |
|---|---|---|
| A. File `ROADMAP_META_UPDATE.md` | Giữ đúng tên file nhưng nội dung = **Registry điều hướng (no-copy)** — không nhân bản SSOT |
| B. `PROJECT_STATUS.md` | **KHÔNG tạo** (giữ quyết định A1/T113 — SSOT = tasktodo/roadmap/dashboard/tasks) |
| C. "Re-activate T114" | **KHÔNG** — T114 đã done; nội dung mới = **T116** (docs-only) |
| D. Version Snapshot | Trung thực: **git HEAD = phiên bản** (`23660b6`); DB không lưu schema_version → không bịa v1.0 |
| E. Baseline | Số thật: 447,885 claims · 3,530 events · assertion_level **0%** · audit SHA-256 64hex · 133 bảng |

## Ground truth đã verify (read-only)
- `entity_claims` = **447,885** · `events` = **3,530** · `events_provenance` 3,530/3,530 (100%)
- `assertion_level`: **0 claim** có giá trị (cả 447,885 là NULL) — khớp metric M7.2 fail
- `entity_claims_audit.audit_id` = **hash SHA-256 64 hex** ✓ (tiêu chí "Audit ID (SHA-256)" ĐÚNG)
- No `schema_version`/`system_registry`/`meta`/`migrations` tables → version chân lý = git
- `PROJECT_STATUS.md` / `ROADMAP_META_UPDATE.md` không tồn tại trước đó; `SOURCE_REGISTRY.md`(13 nguồn)
  + `SOURCE_AUTHORITY_MATRIX.md` + `SCHEMA_DESIGN.md` M7.2 đã là SSOT
- Bảng STATUS của đặc tả ghi sai: T111="Doctrine Retrieval Engine" (thật=Persona Display),
  T113="Done" (thật=in_progress), T114="Doing" (thật=done); cột "Người phụ trách" không có trong repo

## Deliverable (docs-only, 0 code, 0 DB)
1. `docs/ROADMAP_META_UPDATE.md` (v1.0): §1 Mục tiêu · §2 Version Snapshot · §3 Data Traps Map ·
   §4 Navigation Index (trỏ SSOT, không copy) · §5 Meta-Governance.
2. `tasks/T116-system-registry-handover.md` (in_progress): rà C1–C6 + bảng đính chính STATUS + done_when.
3. `docs/tasktodo.md` (dòng T116) · `docs/roadmap.md` (header T108–T116, 2 bảng, label 9 tasks).
4. `docs/ROLLBACK.md` row `f64d798`.
5. Regen `data/progress_data.json`.

## Lệnh điều hành Lee đưa (đặc tả) → thực thi
"Đọc đặc tả · tổng hợp cấu trúc sống · tạo System Registry (bảng Adapter T109, thông số DB, bẫy
T108–T113) · trình Lee chấm điểm" → đã hoàn thành qua `ROADMAP_META_UPDATE.md` + task file T116.

## Rollback
- `git revert --no-edit f64d798` (docs-only, 0 DB).

## Việc kế tiếp
- ⏳ Lee duyệt bản Registry → T116 `done` + hash-fill + regen.
- T113 alert #4/#5: chờ Lee review conflicts (admin/conflicts.html).
- T112 §5 (8 nguồn pending): chờ Lee duyệt activation.