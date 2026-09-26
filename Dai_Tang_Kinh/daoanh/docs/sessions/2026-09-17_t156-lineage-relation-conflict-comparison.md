# Session — T156 Lineage Relation Conflict Comparison (Phase 1 audit)

**Ngày:** 2026-09-17 · **Task:** `tasks/T156-lineage-relation-conflict-comparison.md`
**Audit doc:** `docs/lineage-relation-conflict-A004177-audit.md`

## Mục tiêu phiên
Tạo task T156 + chạy Phase 1 audit (read-only) cho case Đàm Dận A004177 trước khi làm UI conflict cluster; đính chính định danh sai trong spec gốc; cập nhật SSOT/dashboard.

## Verify thật đã chạy (SQL trên `data/lineage.db`, sqlite mode=ro)

1. `select id,name_zh,name_vi from people where id in (A004177,A009590)`:
   - `A004177 = 曇一 / Đàm Dận` (唐)
   - `A009590 = 法慎 / Tông Sư Hòa Thượng`
2. `select ... where id='A010825'` → `大亮 / Đại Lượng` → **spec gán nhầm ID** (大亮 = A010825, không phải A009590).
3. `select id,name_zh,name_vi from people where name_zh=?` với '大亮' → trả rỗng do encoding console khi truyền literal CJK qua PowerShell; kết quả xác thực bằng query theo ID (1 file trên). Tên "Đàm Nhất" → 0 hit.
4. `lineage_edge_assertions` quanh A004177 (42 raw rows, dedupe theo `(source,subject,object)`):
   - MARCUS unique = 14 (12 out `A004177→X` + 2 in `X→A004177`)
   - DILA unique = 14 (12 in + 2 out — ngược y hệt)
   - **reverse pairs = 14**
   - trust_level: MARCUS=L1 (ref CBETA có: 《宋高僧傳》卷14 …) · DILA=L2 (ref=None)
5. `lineage_conflicts_v2` A004177: `teacher_set (dila12/marcus2)`, `student_set (dila2/marcus12)`, is_conflict=1, resolved=0 → khớp 14 cặp đảo chiều.
6. Phân cụm: agreed=0 · reverse_conflict=14 · source_only=0 · unresolved_entity=0 · ZQ_published=0 (T150 docs-only, ngoài phạm vi).

## Kết luận
- Không "25 quan hệ độc lập": thực tế 14 quan hệ duy nhất, cả 2 nguồn vẽ ngược chiều → 1 conflict cluster ⚠.
- UI Phase 2 (gated, sau Admin duyệt audit): mở rộng `places.html` "Đối chiếu nguồn" (~:6431) → summary card + 2-lane + collapse + evidence drawer.
- 0 mutation DB trong toàn bộ phiên.

## SSOT cập nhật
- task `tasks/T156-lineage-relation-conflict-comparison.md` (status: in_progress)
- audit `docs/lineage-relation-conflict-A004177-audit.md`
- tasktodo row T156 🔨 IN_PROGRESS
- ROLLBACK row T156 (placeholder → hash-fill 2-pass)
- dashboard regen `scripts/build_progress_data.py`

## Revert
`git revert --no-edit <sha_phase1>` (docs-only).