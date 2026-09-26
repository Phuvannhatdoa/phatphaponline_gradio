# Session — 2026-09-14 T137 Zen Lineage Integration Audit (AUDIT-ONLY)

> Task: `tasks/T137-zen-lineage-integration-audit.md` · Doc: `docs/ZEN_LINEAGE_INTEGRATION_AUDIT_V1.md`
> Clone: `%TEMP%\opencode\zenlineage_t137` @ commit `ec8357eda153ba442ef86f360299f23f01e5c8ce` (master 2026-08-17)

## Bối cảnh
Admin phê chuẩn audit-only tích hợp Zen Lineage (echojoel/zenlineage · zenlineage.org) làm nguồn đối chiếu Pháp mạch Đạo Ảnh. Đường dẫn doc: `docs/ZEN_LINEAGE_INTEGRATION_AUDIT_V1.md` (không folder con). License chưa xác minh → import gated.

## Phương pháp thực thi
1. Clone nông → checkout ec8357ed vào `%TEMP%\opencode\zenlineage_t137` (ngoài production tree).
2. `npm install` (885 pkgs) → `drizzle-kit migrate` (8 migrations 0000–0007) → chạy data-seed chain (25 scripts, bỏ 3 image scripts). Zen.db rebuilt thành công: 35 tables.
3. Đếm SQL trực tiếp (Python sqlite3) — kết quả dùng trong doc §5–§9.

## Kết quả audit (số liệu verified)
- **556 masters** · 25 schools · **578 transmissions** · **8,684 citations** · 1,699 temples · 206 sources.
- **Citation cấp relation: YES** — 578/578 transmissions có evidence row (tier A 194 · B 342 · C 25 · D 17) + 1,195 citation rows entity_type='master_transmission' + 1,659 transmission_sources rows. human_review_needed = 41.
- **Relation semantics**: teacher_id + student_id (directional), type primary 508 · secondary 42 · dharma 19 · disputed 9. **Không phải edge vô nghĩa.**
- **IDs**: slug unique YES; **external IDs DILA/BDRC/Marcus KHÔNG CÓ**.
- **Vietnamese overlap**: 18 Thiền-school masters, 17 vi-locale names; đối chiếu lineage.db → **không exact match** (tên trùng là homonym khác).
- **License**: NOT VERIFIED — LICENSE 404, GitHub license null. Import BLOCKED.

## Files
- Tạo mới:
  - `tasks/T137-zen-lineage-integration-audit.md`
  - `docs/ZEN_LINEAGE_INTEGRATION_AUDIT_V1.md`
  - `docs/sessions/2026-09-14_t137-zen-lineage-integration-audit.md`
- Sửa: `docs/tasktodo.md` (T137 ACTIVE đầu mục), `data/progress_data.json` (regen dashboard → 58 tasks).
- Clone (thuần temp, ephemeral): `%TEMP%\opencode\zenlineage_t137` — KHÔNG nằm trong production tree.

## Tiếp theo
- **Chờ APPROVED** doc audit này trước khi thực hiện Phase 2 (M1 link-out · M2 staging · M3 candidate · M4 HITL).
- Admin quyết hướng license (hỏi chủ repo / link-out / internal-only).
