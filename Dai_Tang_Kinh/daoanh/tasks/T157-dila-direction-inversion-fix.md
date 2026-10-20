---
id: T157
title: "Root-cause lật chiều DILA + fix ETL (lineage_edge_assertions) + UI Đối chiếu nguồn sau fix (B-1 minimal, hoãn B-2)"
module: lineage
priority: high
status: done
depends_on: [T138, T156]
created: 2026-09-17
updated: 2026-09-17
done_when:
  - "[x] Phase 2A: docs — T156 đóng (superseded), T157 canonical, §8 root-cause vào audit doc, session, tasktodo archive, ROLLBACK placeholder + hash-fill, dashboard regen"
  - "[x] Phase 2B: script ETL `scripts/etl_t156_dila_direction_fix.py` (backup → atomic DELETE DILA L2 → re-INSERT canonical) dry-run → apply → verify — PASS ✅ 11.165/11.165 (100%), A004177 0 mismatch, backup lineage_t157_20260917_135725.db"
  - "[x] Phase 2C: UI `places.html` 'Đối chiếu nguồn' post-fix (agreed-first + evidence drawer + Research mode + banner legacy conflicts_v2) — 9 hunk, render từ edge sources[].direction_mismatch (assertions) thay n.conflicts (legacy)"
  - "[x] QA: node --check/@babel/parser + npm run pipeline (e2e:runtime EPERM → .pw-tmp) + QA thật A004177 (14/14 đồng thuận, 0 mismatch, 0 console error) + QA spot-check case T128 A008874 (2/2 đồng thuận, 0 mismatch) + docs/lineage-relation-conflict-A004177-implementation.md"
  - "[x] Rollback: data/backups/lineage_t157_20260917_135725.db + docs/ROLLBACK.md row T157 hash-fill 2-pass (1e15694/68e422e) + git revert — Admin verify live UI ✅ + Admin ĐỒNG Ý BUILD 2026-09-17 → CLOSE"
  - "[x] Closure: commit 1e15694 (Phase 2C UI+docs) + e2fcc84 (ROLLBACK hash) + 68e422e (dashboard regen) → docs/taskdone.md prepend T157 + tasktodo T157 DONE + session QA closure"
---

# T157 — Root-cause Lật Chiều DILA + Fix ETL + UI Sau Fix

> **Module:** `lineage` · **Priority:** high · **Status:** done ✅
> **Depends on:** T138 (edge assertion model) · T156 (audit gốc, đã đóng superseded)
> **Created:** 2026-09-17 · **Updated:** 2026-09-17 · **Closed:** 2026-09-17 (Admin ĐỒNG Ý BUILD sau live QA)

---

## 1. Phát hiện (2026-09-17, investigate read-only — bằng chứng toàn cục)

Kết luận Phase 1 T156 ("14 reverse pairs = mâu thuẫn lịch sử thật") SAI. Phân tích bảng chính `lineage_edge_assertions` cho thấy đây là **artifact hệ thống — lật chiều trục DILA toàn cục** (đo reproducible 2026-09-17):

| Metric | Pre-flip (hiện trạng cũ) | Post-flip (hoán vị teacher↔student DILA) |
|---|---|---|
| DILA L2 raw rows / distinct | 46.006 / 23.014 (mỗi edge ×2) | 46.006 / 23.014 |
| MARCUS distinct | 11.169 | 11.169 |
| Cạnh MARCUS có DILA (1 trong 2 chiều) | 11.165 | 11.165 |
| **Cạnh CÙNG chiều** | **0** | **11.165 (100% matched)** |
| Persons ≥1 cạnh đồng thuận | 0 | 3.143 |
| Đảo ngược AGAIN (sanity) | — | 0 |

- **Side-effect hệ thống tuyệt đối:** 0 → 100% sau 1 phép hoán vị. Nếu là dữ liệu lịch sử hỗn độn sẽ có cả 2 chiều; thực tế MỌI cạnh MARCUS có DILA đều lệch chiều trước fix → một nguồn bị invert toàn bộ. Xác nhận lớp conflicts_v2: `dila_data ∩ marcus_data` per-row = 0 trên 40.327 rows.
- **Marcus = chiều văn bản chuẩn (14/14 anchor A004177):** Kết nối trực tiếp từ `authored_relations` ↔ `ref` ↔ CBETA:
  - 《宋高僧傳》卷14: 「**其門人…越州妙喜寺常照**」, 「**其上首曰會稽曇一**」, 「**依曇一隸南山律**」 → `A004177→常照(A004179)` (đệ tử) + `曇一(A004177)` là đệ tử của `法慎` = `A009590→A004177`.
  - `persons.json` A004177: `teacher` = 12 (gồm 常照 A004179 — chính là 12 đệ tử THẬT), `student` = [大亮 A010825, 法慎 A009590] (chính là 2 thầy THẬT) → **DILA axis bị lật nghịch với văn bản**.
- **Chuỗi lật (source→DB):** `data/persons.json` (`teacher`=marcus-student / `student`=marcus-teacher — invert) → TTL `bkg:hasTeacher` (build_master_json) → `people` → `lineage_conflicts_v2.dila_data` (`teacher_set`/`student_set` swap) → `deep_conflict_analysis.py` → `lineage_edge_assertions` DILA L2 (46.006 edges, ref=None).
- **Phân loại cụm:** `pipeline_inversion` — KHÔNG phải conflict lịch sử, KHÔNG phải nguồn coverage gap, KHÔNG phải unresolved entity.

## 2. Phạm vi fix (Admin phê chuẩn 2026-09-17)

### B-1 (LÀM) — Tối thiểu, an toàn, revert được
- **Target:** 46.006 cạnh DILA L2 trong `lineage_edge_assertions` (BẢNG CHÍNH LÀM UI, đọc bởi `get_lineage_assertions`/renderer).
- **Thao tác:** backup DB → atomic `DELETE` cạnh DILA L2 → re-`INSERT` theo chiều canonical (lấy từ `persons.json`: `teacher_set → cạnh person→student`, `student_set → cạnh teacher→person`) — idempotent, additive, 0 ALTER bảng base.
- **Verify:** ~22.326 cạnh DILA L2 khớp chiều Marcus; A004177 0 direction mismatch; `lineage_edge_assertions` count giữ nguyên (57.175).
- **Bỏ qua (channel không nằm trong scope này):** `lineage_conflicts_v2` giữ nguyên (legacy), TTL `bkg:hasTeacher`, generator persons.json gốc — ghi nợ follow-up.

### B-2 (HOÃN — ghi nợ docs)
- Tái tạo `lineage_conflicts_v2` post-fix (re-snapshot từ `lineage_edge_assertions` mới). UI gắn banner **LEGACY** cho mọi nguồn đọc `lineage_conflicts_v2` cho tới khi B-2 chạy.

## 3. Phase 2C — UI "Đối chiếu nguồn" SAU fix (kế thừa T156 Phase 2 đã supersede)

> ✅ **ĐÃ HOÀN THÀNH 2026-09-17** — chi tiết: `docs/lineage-relation-conflict-A004177-implementation.md`.

1. Card summaries, **ưu tiên `agreed`**: "N cạnh đồng thuận" tích cực + card ⚠ amber "Mâu thuẫn chiều quan hệ" CHỈ khi còn mismatch thật post-fix. ✅
2. Hai-làn Marcus | DILA mũi tên chiều rõ ràng + collapse nhóm "+N vị" (🔬 Research mở toàn bộ). ✅
3. Evidence drawer: source · dataset version · ref/link → Đại Tạng · trust level — trung thực. ✅
4. DILA L2 chưa ref = badge "○ Cần khảo cứu". ✅
5. **Research mode** cho mỗi cạnh (giữ nguyên tương tác hiện có). ✅
6. Banner **LEGACY** cho nguồn `lineage_conflicts_v2` (chờ B-2). ✅
7. UI nguồn chuyển sang `lineage_edge_assertions` (post-fix) — mọi render conflict dùng `edge.sources[].direction_mismatch`, KHÔNG đọc conflicts_v2 cho render này. ✅

## 4. Ràng buộc bất biến

- 0 ALTER bảng base · additive/idempotent · backup + revert phải chạy được.
- `git revert --no-edit` khôi phục DB? KHÔNG — DB backup riêng `data/backups/lineage_t157_<ts>.db` (data quý hơn code).
- Không sửa `data/persons.json` (golden input) trong B-1; generator gốc = follow-up.
- Không đụng file Admin modified (`places.html`, `app.py` chưa commit của Admin) — làm trên nền 0 diff Admin hoặc báo trước.
- Test: `npm run pipeline` (e2e:runtime EPERM → bypass `.pw-tmp`).

## 5. Deliverables

- `scripts/etl_t156_dila_direction_fix.py` (+ `--dry-run/--apply/--revert` + bảng báo cáo).
- `docs/lineage-relation-conflict-A004177-audit.md` §8 ROOT-CAUSE ADDENDUM.
- `docs/lineage-relation-conflict-A004177-implementation.md` (post-fix QA).
- Session `docs/sessions/2026-09-17_t157-dila-direction-inversion-fix.md`.
- Follow-up nợ: generator gốc persons.json/TTL (**B-3 ✅ DONE 2026-09-22**), re-snapshot conflicts_v2 (**B-2 ✅ DONE 2026-09-22**), banner legacy (chờ QA), tab lineage Profile DILA-axis (**B-4 ✅ DONE 2026-09-22, commit `b1d364e` + docs `7d60d01`** — endpoint `GET /daoanh/api/person/<person_id>/dila-axis` + inspector section "Truyền Thừa (DILA L2)"; verified A004177 = 12 đệ tử / 2 thầy chiều canonical, Flask smoke 200, @babel/parser 3/3 blocks).

## 6. Revert

- Docs: `git revert --no-edit <sha_T157_docs>`.
- ETL+UI: `git revert --no-edit <sha_T157_code>`; DB restore `data/backups/lineage_t157_<ts>.db`.
- ROLLBACK row T157: hash-fill 2-pass bằng `git rev-parse` (KHÔNG gõ hash tay).