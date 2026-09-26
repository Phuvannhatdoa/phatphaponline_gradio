# Session — T109 rà đặc tả "Lineage Consensus Engine" (XÁC NHẬN ĐÃ PHỦ)

**Ngày:** 2026-09-09 · **Commit:** `6f6baca`

## Bối cảnh
Lee gửi đặc tả **"Task T115: Lineage Consensus Engine"** — nội dung thực chất là **"Đặc tả khái niệm T109: Conflict Engine Workflow"**
(header đề T115 nhưng toàn bộ bài viết/lệnh điều hành nhắc T109). Rà đối chiếu với thực trạng DB + UI (read-only).

## Ground truth (verified)
- `lineage_conflicts_v2` = **40,327** rows · cột `person_id,label,name_vi,conflict_type,dila_data,marcus_data,dila_count,marcus_count,is_conflict,resolved,notes,created_at`.
- `resolutions_log` **đã có** — `conflict_id,monk_id,chosen_source,previous_source,notes(=lý do),resolved_by(=người duyệt),resolved_at(=thời gian)` ✓ khớp đúng 3 trường đặc tả.
- `en_audit_log` **đã có** — `editor,evidence_sources,created_at` (sample: approve PL000000000314 name_vi).
- UI: `admin/conflicts.html` gọi `/daoanh/api/admin/lineage-conflicts` (+ `<id>/resolve`) ✓.
- `v_assertions` **không** tham chiếu conflicts → pooL tách biệt (Data Lock = hệ quả architecture additive).
- Tài liệu đã có: `docs/lineage-conflict-implementation.md` (90 dòng) + `docs/lineage-conflict-audit.md`.
- T109 task file: `status: done` (hash `243c490a`); T115 = Source Authority Matrix (done) — đặc tả không phải T115.

## Điểm lệch đặc tả
1. Nhãn task mâu thuẫn: "T115" vs nội dung "T109" → đặc tả mô tả lại **T109 đã DONE**.
2. Toàn bộ deliverable đã tồn tại (pool/UI/resolutions_log/en_audit_log) — không có gì để triển khai mới.
3. UI chưa render **Authority Score** (JOIN `source_authority` DILA=100/MARCUS=60 — additive).
4. Không cờ `lock` riêng — "Data Lock" là hệ quả additive (v_assertions tách pool).

## Quyết định
- **KHÔNG tạo** `docs/CONFLICT_ENGINE_SPEC.md` (trùng 2 file đã có — theo quyết định QA_COMPLIANCE_SPEC/A2).
- **KHÔNG re-open** T109/T115 (đã done).
- Đặc tả = **cam kết quản trị đã phủ** → ghi nhận vào `tasks/T109` + append gap vào `docs/lineage-conflict-implementation.md`.
- Task mới (T117, UI Authority Score) — **Track 2, để sau** (code additive).

## Thay đổi (docs-only, 0 code, 0 DB)
1. `tasks/T109-provenance-conflict-workflow.md` — mục "Rà đặc tả ... — XÁC NHẬN ĐÃ PHỦ".
2. `docs/lineage-conflict-implementation.md` — append "Rà đặc tả ... — Gap & xác nhận" (Zero-Loss).
3. `docs/tasktodo.md` — chú thích `[ráspec 2026-09-09]` ở dòng T109.
4. `docs/ROLLBACK.md` row `6f6baca`.
5. Session này.

## Rollback
- `git revert --no-edit 6f6baca` (docs-only, 0 DB).

## Việc kế tiếp
- (Sau/Tùy chọn) **T117 — Conflict UI Authority Score + History** (JOIN source_authority + en_audit_log history, additive) khi Lee duyệt Track 2.
- T113 alert #4/#5 chờ Lee review conflicts · T112 §5 chờ duyệt · T116 chờ duyệt registry.