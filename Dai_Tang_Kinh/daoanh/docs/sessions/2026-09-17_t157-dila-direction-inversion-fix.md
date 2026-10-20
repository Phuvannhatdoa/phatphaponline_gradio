# Session — T157 Root-cause Lật Chiều DILA + Fix ETL + UI Sau Fix

**Ngày:** 2026-09-17 · **Task:** `tasks/T157-dila-direction-inversion-fix.md`
**Audit doc:** `docs/lineage-relation-conflict-A004177-audit.md` (§8 ROOT-CAUSE ADDENDUM)

## Mục tiêu phiên
Phản định kết luận T156 ("14 reverse pairs = mâu thuẫn lịch sử") bằng chứng cứ toàn cục; pivot T156 → root-cause + fix ETL (B-1) + UI sau fix (Phase 2C); đóng T156 superseded; lập kế hoạch T157; cập nhật SSOT/dashboard; đảm bảo mọi bước revert được tiện lợi.

## Bằng chứng đã verify (read-only, data/lineage.db + data/persons.json)

1. Bảng chính `lineage_edge_assertions` (đo reproducible 2026-09-17):
   - DILA L2 raw 46.006 / distinct **23.014** (mỗi edge ×2 — quan hệ sinh ở `teacher_set` thầy lẫn `student_set` trò) · MARCUS distinct 11.169
   - Cạnh MARCUS có DILA (1 trong 2 chiều) = 11.165
   - Pre-flip CÙNG chiều = **0** · Post-flip CÙNG chiều = **11.165 = 100% matched** · persons ≥1 = 3.143
   - Sanity: sau fix mà đảo ngược AGAIN = 0 (hướng fix đúng)
2. Xác nhận lớp `lineage_conflicts_v2`: `dila_data ∩ marcus_data` per-row = **0** trên 40.327 rows (cả 2 dùng id-space A-codes) — mọi cặp teacher/student set đối nghịch tuần hoàn.
3. Anchor văn bản A004177 (14/14) — Marcus khớp nguyên văn CBETA:
   - 《宋高僧傳》卷14 「其門人…越州妙喜寺常照」 → `A004177→A004179(常照)`.
   - 「其上首曰會稽曇一」 + 「依曇一隸南山律」 → `A009590(法慎)→A004177`.
   - `data/persons.json` A004177: `teacher`=12 (gồm 常照 A004179) + `student`=[大亮 A010825, 法慎 A009590] → **DILA axis lật nghịch văn bản**.
4. Chuỗi lật: persons.json → TTL `bkg:hasTeacher` → people → conflicts_v2.dila_data → deep_conflict_analysis → `lineage_edge_assertions` DILA L2 (46.006, ref=None).
5. Phân loại cụm chính thức = **`pipeline_inversion`**.

## Quyết định phê duyệt (Admin 2026-09-17)
- Đổi T156 → root-cause + fix ETL (Recommended). B-1 minimal (re-INSERT 46.006 DILA L2 canonical). **Hoãn B-2** (re-snapshot conflicts_v2).
- **Có làm UI sau fix** (Phase 2C) — kế thừa T156 Phase 2 đã supersede.
- Tạo task mới T157 (free — real max tasks glob = T156), T156 đóng → `docs/taskdone.md`.
- Ràng buộc: backup/revert tiện lợi, 0 ALTER, additive/idempotent, đảm bảo 0 leftover, không đụng file Admin (`places.html`, `app.py` ` M`).

## Công việc phiên này
- **Phase 2A (docs, DONE — commit `31ae903` + hash-fill `950a669`):** đóng T156 (status done + superseded_by T157) · canonical `tasks/T157-dila-direction-inversion-fix.md` · §8 addendum audit · session này · tasktodo archive T156 → taskdone.md + row T157 🔨 · ROLLBACK row T157 placeholder → hash-fill 2-pass · dashboard regen (78 tasks, done=35).
- **Phase 2B (ETL, DONE — commit `8bf257e` + hash-fill `36f676a`):** `scripts/etl_t156_dila_direction_fix.py` (`--mode dry-run/apply/verify/--revert`) — backup `data/backups/lineage_t157_20260917_135725.db` → atomic DELETE 46.006 DILA L2 → re-INSERT canonical; verify **PASS ✅** (cùng chiều 0→11.165=100%, A004177 out=12/in=2 == cả 2 nguồn, đảo AGAIN=0). Số reproducible thay thế con số aggregation cũ trong §8/task/session/tasktodo.
- **Admin WIP (DONE — commit `3df635b`):** Admin chọn "Admin commit WIP trước" → commit sạch `places.html` (alias-resolve banner) + `app.py` (dila_translate, 397 dòng) + `admin/person.html` + `admin/translation_rules.html` để base Phase 2C = 0 diff Admin. Secret-scan OK.
- **Phase 2C (UI, DONE — chờ commit bước này):** 9 hunk `places.html` — helper `_t86EdgeMismatch`/`_t86NodeDirMismatchCount`/`_t86SrcChip`/`_linToggleResearch`; mọi render conflict (title badge, header confl, filter conflict, edge marker conflictTouched, node color hasConflict, network hasDirDis, fallback inspector) đổi từ `n.conflicts` (legacy lineages_conflicts_v2) sang `edge.sources[].direction_mismatch` (assertions post-fix); inspector "Đối chiếu nguồn" viết lại agreed-first (card ✓ đồng thuận + card ⚠ chỉ khi mismatch thật + dòng only-1-nguồn) + 2-lane Marcus|DILA (+N vị ẩn / 🔬 Research) + banner LEGACY conflicts_v2. Chi tiết: `docs/lineage-relation-conflict-A004177-implementation.md`.
- **QA (DONE):** `node --check` toàn inline script places.html OK · `npm run pipeline` PASS (guard · design compliance · lint · test · e2e; e2e:runtime pass qua `.pw-tmp` — EPERM `.last-run.json` pre-existing) · **QA live playwright (:8080) A004177:** 14 cạnh kề, MARCUS+DILA đồng thuận **14/14**, mismatch **0**, inspector "✓ 14 quan hệ hai nguồn cùng chiều" + thầy Pháp Thận (法慎)/Đại Lượng (大亮) + trò Trạm Nhiên…, **0 console error**.
- **Phase 2C commit (DONE — `1e15694` + hash-fill `e2fcc84` + dashboard `68e422e`):** 9 hunk places.html + docs implementation `docs/lineage-relation-conflict-A004177-implementation.md` + audit §8.7 + ROLLBACK row placeholder → hash-fill 2-pass (git rev-parse). Leftover = 0.
- **Spot-check post-fix case chuẩn T128 — A008874 (DONE):** playwright (:8080) `loadLineageTree('A008874')` + `_renderLineageInspector` → inspector "Đối chiếu nguồn": **dc=2, agreed=2, mism=0, only=0**, lane MARCUS 2 / DILA 2; text: "✓ 2 quan hệ hai nguồn cùng chiều (Marcus + DILA đồng thuận)" + lane "thầy: Nam Dương Huệ Trung ✓ MARCUS L1 ↗ / ✓ DILA L2 ○ Cần khảo cứu" + "trò: Ngưỡng Sơn Huệ Tịch ✓ MARCUS L1 ↗ / ✓ DILA L2 ○ Cần khảo cứu" + banner LEGACY; bio khớp văn bản ("南陽慧忠…法嗣 …仰山慧寂…曾參謁之") → **xác nhận UI post-fix đúng trên chính case mà QA 09-15 không thể kiểm** (data còn inverted lúc đó). **0 console error.** API đồng bộ: lineage-tree up=3/down=3 → 26 nodes/25 edges, **0 mismatch**, MARCUS+DILA đều trên 25/25.
- **CLOSE T157 (2026-09-17, Admin ĐỒNG Ý BUILD):** T157 status → done · taskdone.md prepend · tasktodo T157 🎯 DONE · session closure · dashboard regen (done=36). Nợ có chủ đích: **B-2** (re-snapshot `lineage_conflicts_v2`), **B-3** (`data/persons.json` + TTL `bkg:hasTeacher` generator, vẫn invert — verify A008874 `teacher=[慧寂]`), **B-4** (tab lineage Profile DILA-axis) — theo dõi trong tasktodo.

## SSOT cập nhật
- `tasks/T156-lineage-relation-conflict-comparison.md` (status: done, superseded_by T157)
- `tasks/T157-dila-direction-inversion-fix.md` (status: done) → `docs/taskdone.md`
- `docs/lineage-relation-conflict-A004177-audit.md` (§8 + §8.6 + §8.7)
- `docs/lineage-relation-conflict-A004177-implementation.md` (Phase 2C implementation)
- `docs/tasktodo.md` · `docs/taskdone.md` · `docs/ROLLBACK.md`
- dashboard regen `scripts/build_progress_data.py`

## Revert
- Docs 2A: `git revert --no-edit 31ae903a6b36768958a10debefe61360c107a7cc`.
- ETL 2B: `git revert --no-edit 8bf257e3aff39fcec12f7fb87aed8c29f335e7fa` + DB restore `data/backups/lineage_t157_20260917_135725.db`.
- UI 2C: `git revert --no-edit 1e156940fd35f4edc8468c88404fe4c2964a9cff` (0 DB — DB đã chuẩn từ ETL).
- Cuối cùng: `git revert --no-edit e2fcc84` + `68e422e` (ROLLBACK hash-fill + dashboard regen) rồi revert tới điểm mong muốn.