---
id: T156
title: "Lineage Relation Conflict Comparison (Đối chiếu truyền thừa — biến raw source comparison thành conflict cluster dễ hiểu; case Đàm Dận A004177)"
module: lineage
priority: medium
status: done
depends_on: [T138]
created: 2026-09-17
updated: 2026-09-17
superseded_by: T157
done_when:
  - "[x] Phase 1: audit định danh case A004177 (đúng canonical ID, không theo tên hiển thị)"
  - "[x] Phase 1: đếm động reverse pairs từ lineage_edge_assertions (không hardcode)"
  - "[x] Phase 1: báo cáo docs/lineage-relation-conflict-A004177-audit.md"
  - "[x] ROOT-CAUSE (T157): 'mâu thuẫn' = artifact LẬT CHIỀU DILA toàn cục, không phải conflict lịch sử thật"
  - "[x] T156 Phase 2 (UI conflict cluster) SUPERSEDED → T157 (fix chiều DILA trước, UI sau fix)"
---

# T156 — Lineage Relation Conflict Comparison

> **Module:** `lineage` · **Priority:** medium · **Status:** done (Phase 1 audit + root-cause redirect; Phase 2 UI → T157)
> **Type:** UI/UX refinement của T138 (0 API, 0 DB, 0 ALTER, 0 Schema — presentation only) — **SUPERSEDED bởi T157**
> **Depends on:** T138 (render policy + edge assertion model) · T140 (legend/lanes đã có)
> **Created:** 2026-09-17 · **Updated:** 2026-09-17
> **Superseded by:** `tasks/T157-dila-direction-inversion-fix.md` — QUAN TRỌNG: kết luận Phase 1 ("14 reverse pairs = mâu thuẫn lịch sử") SAI. Investigate T157 chứng minh đây là **artifact lật chiều trục DILA toàn cục** (0/23.139 khớp chiều pre-flip → 22.326/23.139 khớp post-flip). Chiều văn bản chuẩn = Marcus (14/14 ref-authored từ CBETA). Xem §6 addendum audit.

---

## 1. Bối cảnh (đã verify thật 2026-09-17)

| Yêu cầu spec gốc | Sự thật trong DB (lineage.db, read-only) |
|---|---|
| Case "Đàm Nhất (曇一) A004177" | `A004177 = 曇一 / **Đàm Dận**` (唐). KHÔNG có tên "Đàm Nhất" trong `people` |
| "A009590 / 大亮 / Đại Lượng" | `A009590 = **法慎 / Tông Sư Hòa Thượng**`; `A010825 = **大亮 / Đại Lượng**` — spec **gán nhầm ID** cho 大亮 |
| "ui đang lặp 2 danh sách dài" | places.html ĐÃ có section "Đối chiếu nguồn" (~:6431) in `direction_disagreement` dạng list — chưa gom cluster |
| "verify count, đừng hardcode 13" | số thật = **14 reverse pairs unique** (12 out + 2 in), đếm động từ `lineage_edge_assertions` |

**Luồng data thật:**
- `lineage_edge_assertions` (57,175 rows) — assertion chuẩn hóa `source_code ∈ {MARCUS(L1), DILA(L2)}`, chỉ 2 relation vocab `da:isTeacherOf` / `dila:teacher_of`.
- `lineage_conflicts_v2` (40,327 rows) — snapshot `teacher_set`/`student_set` với `dila_data`/`marcus_data` (count so sánh DILA vs Marcus).

## 2. Ràng buộc (bất biến)

- **Match theo canonical person ID, KHÔNG theo tên hiển thị** (tên là nguồn gây ambiguity).
- **Không mutate DB / raw DILA XML / Marcus imports / canonical IDs / ZQ decisions.**
- Không tạo module UI song song — mở rộng `places.html` "Đối chiếu nguồn" (~:6431) hiện có.
- Không tạo duplicate SPEC — tham chiếu `docs/lineage-conflict-audit.md`, `docs/lineage-conflict-implementation.md`, `docs/CONFLICT_ENGINE_SPEC.md`.
- **Không thực thi "Pháp Mạch mặc định chỉ đọc published lineage view"** — T150 (ZQ Review / view `published_lineage_relation`) mới là docs design, chưa phê duyệt code → ngoài phạm vi T156.
- Mọi bug khi fix phải revert được: `git revert --no-edit <sha_T156>`.

## 3. Phase 1 — Audit (DONE, docs/lineage-relation-conflict-A004177-audit.md)

- Đính chính định danh (bảng ID ↔ tên).
- Đếm động: MARCUS 14 unique · DILA 14 unique · **reverse pairs = 14** · 0 agreed · 0 source_only · 0 unresolved_entity · 0 ZQ_published.
- Khớp snapshot `lineage_conflicts_v2`: `teacher_set DILA12/MARCUS2` + `student_set DILA2/MARCUS12`.
- 0 mutation DB trong toàn bộ audit (chỉ SELECT mode=ro).

## 4. Phase 2 — UI (SUPERSEDED → Chuyển sang T157)

> Đã chuyển hướng: Phase 2 UI **không còn hợp lệ trên bản vẽ "14 mâu thuẫn lịch sử"**. Root-cause (T157) phát hiện mâu thuẫn = DILA axis lật toàn cục → **fix ETL trước (T157 B-1), UI "Đối chiếu nguồn" sau fix (T157 Phase 2C)**.

1. ~~Gom các cạnh thành cluster: `agreed / reverse_conflict / source_only / unresolved_entity → (skip ZQ_published)`.~~
2. ~~Summary card nếu có reverse: icon ⚠ + "Mâu thuẫn chiều quan hệ" + số cạnh + số nguồn + [So sánh đồ thị] [Xem các cạnh].~~
3. ~~Hai-làn Marcus | DILA, mũi tên chỉ chiều rõ ràng, collapse nhóm lớn "3 + +N vị", click → evidence drawer (source · dataset version · record id · ref/link CBETA · ZQ state).~~
4. ~~Tiered summary đầu hồ sơ: "Pháp Mạch ZQ: … · Nguồn quan hệ: … · Mâu thuẫn: N clusters/N edges".~~
5. ~~Verify: node --check / @babel/parser · npm run pipeline (e2e:runtime EPERM = PASS WITH KNOWN INFRASTRUCTURE LIMITATION) · QA thật A004177.~~

→ Phần render cụ thể được kế thừa, điều chỉnh theo kết quả fix T157 — xem `tasks/T157-dila-direction-inversion-fix.md` Phase 2C.

## 5. Revert

- Phase 1 (docs-only): `git revert --no-edit <sha_T156_phase1>`.
- Phase 2: đã hoãn — UI final theo T157, revert theo `docs/ROLLBACK.md` row T157.