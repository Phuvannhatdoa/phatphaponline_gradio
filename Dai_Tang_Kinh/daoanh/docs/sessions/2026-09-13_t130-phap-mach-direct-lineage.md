# Session 2026-09-13 — T130 Pháp Mạch: direct-lineage projection (trực hệ 1 nhánh)

**Task:** `tasks/T130-phap-mach-direct-lineage.md` | **Status:** plan phê chuẩn, CHỜ implement
**Ngày:** 2026-09-13 | **Phạm vi:** app.py (additive param) + places.html (chain rewrite)

## Yêu cầu (spec FIX Truyền thừa > Menu Pháp Mạch)
Pháp Mạch chỉ hiển thị **chuỗi trực hệ** thầy→trò (Đạt-ma → Huệ Khả → Tăng Xán → Đạo Tín); mở rộng thế hệ sau bằng **icon +/− trên node**; không sibling mặc định; khi >1 successor chưa xác lập primary → badge `+N nhánh` + chooser + CTA "Mở Phả hệ mở rộng"; routing `?mode=lineage&chain=...`; controls Chuẩn (Fit/Tâm/Thu gọn tất cả/Mở 1 đời tiếp). → 8 mục + acceptance A–I.

## Verify spec vs logic hiện tại (KQ: chỉ khớp ~20%)
Đối chiếu chi tiết:
| Mục spec | Hiện tại (T127/T128/T129) | Verdict |
|---|---|---|
| 1 Projection trực hệ | `_renderLineageChain` full-subtree BFS, auto-expand 3 đời, chính-mạch heuristic `descCounts` (L5350-5366, 5403-5417) | ✗ |
| 1a Primary/canonical | DB không có field (chỉ da:isTeacherOf + ref); canonical_decision = tên; source_authority tồn tại (7 nguồn) | ✗ (derive) |
| 1b Uncertain → +N/chooser | không có | ✗ |
| 2 Icon +/- (DOM button) | node vẽ canvas ctx; micro-label `▸/▾`; click body = toggle | ✗ |
| 3 Expand 1 đời, single-path | "Mở 2/3 đời/toàn nhánh", không 1 successor/click | ✗ |
| 4 Sibling ẩn | sibling hiện đầy đủ + overflow `__ov__` | ✗ |
| 5 Visual shared | `_renderHierarchyTree`/palette/connector/arrowhead | ✓ (thêm icon/outline) |
| 6 Routing | in-memory `_ftExpanded`; không URL/history | ✗ |
| 7 Controls | có "Mở toàn nhánh" (cấm), thiếu "Mở 1 đời tiếp"/CTA | ✗ |
| 8 Acceptance A–I | hầu như trượt; G✓ (network full) I✓ | ✗ |

## Data facts (verified)
- `marcus_networks` 11,169 edge, 1 relation_type, source MARCUS. Schema: id/teacher_id/student_id/relation_type/teacher_label/student_label/source_data/ref/created_at.
- `canonical_decision(entity_ref, canonical_name_vi, ...)` = KHÔNG succession. `source_authority` 7 nguồn (D-E-U-I = MARCUS, CBETA…).
- `lineage_conflicts_v2` 40,327 open → nguồn uncertain/need-research.
- A008874 (應真): 1 trò A009491 + 1 thầy A001707 → chain sạch (case mẫu). Mã Tổ Đạo Nhất 141 trò. 無演/澄觀 7 thầy.
- Endpoint `/lineage-tree` (app.py 5225-5329) setup up/down clamp, `has_more_up/down`, display_name; `?expand=` trong docstring nhưng KHÔNG có trong code.

## Kế hoạch (task `tasks/T130-...md`)
- **Pha 1 backend:** B1 implement `?expand=<id>&dir=up|down` (lazy merge 1 tầng, dedupe); B2 source_authority→confidence DEFER.
- **Pha 2 client:** 8 mục (P2.1 chain projection/chooser → P2.2 icon overlay → P2.3 expand 1 đời + lazy ?expand → P2.4 bỏ sibling/overflow → P2.5 icon style → P2.6 routing → P2.7 controls → P2.8 acceptance+test). Phả hệ mở rộng GIỮ NGUYÊN.

## Trạng thái
- [x] Verify spec vs code (bảng trên).
- [x] Task file + tasktodo.md + session doc + (dashboard regen).
- [ ] Implement Pha 1 (B1) + smoke.
- [ ] Implement Pha 2 (P2.1–P2.7).
- [ ] Algorithm unit test + node --check + pipeline + live QA.

## Rollback
- Backup app.py/places.html trước mỗi phase; `?expand` additive vô hại. Real git index không đụng (temp-index).