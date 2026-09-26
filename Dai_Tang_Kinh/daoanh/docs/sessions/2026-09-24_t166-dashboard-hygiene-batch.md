# Session 2026-09-24 — T166 Dashboard hygiene batch + T164 Lineage Tree UI Cleanup closure

**Ngày:** 2026-09-24
**Mode:** build (user "Đồng ý build, hãy lưu logs, gitcommit..." — loại T150 gõ nhầm, chỉ T166 + T164)
**SSOT repo-root:** `visjs-app` (git toplevel) — mọi commit từ đây.

## Mục tiêu
1. **T166 (docs-only):** đồng bộ frontmatter 9 task `tasks/*.md` tụt sau thực tế → regen `data/progress_data.json` → dashboard đếm đúng.
2. **T164 (docs closure):** code S1–S8 đã committed `77dec5e` (2026-09-23) — autoverify + browser QA → đóng task.

## Nguyên tắc áp dụng
- Additive, docs-first. T166/T164 đều 0 code/0 DB/0 API.
- Commit từ git toplevel (SSOT rule T155) — không `cd` vào daoanh chạy git.
- Không đụng file dirty pre-existing.
- Mọi fix revert được tiện lợi: `git revert --no-edit <sha>`.
- Rollback hash-fill 2-pass theo chuẩn T146 (placeholder `<sha>` → hash thật ở commit 2).

---

## 1. Phát hiện (pre-session analysis)
Cross-check `data/progress_data.json` (board 89 tasks) vs `docs/tasktodo.md` vs frontmatter `tasks/*.md`:

| # | File | Frontmatter (sai) | Thực tế (tasktodo.md) | Chữa |
|---|------|------|------|------|
| 1 | T131-b21-source-governance-refine | in_progress | DONE → `c686636` build additive (tasktodo:31, updated 2026-09-18) | `done` |
| 2 | T137-zen-lineage-integration-audit | in_progress | DONE (AUDIT-ONLY, tasktodo:37) | `done` |
| 3 | T138-zen-lineage-render-policy | in_progress | DONE + LIVE (tasktodo:36) | `done` |
| 4 | T110-glossary-vietnamese-pipeline | pending | DONE (T05 closure, tasktodo:210) | `done` |
| 5 | T52-doi-chieu-tam-tang | pending | DONE (T52a–e, tasktodo:161) | `done` |
| 6 | T97b-place-tu-si-timeline-events | **NO_STATUS** (không frontmatter YAML) | DONE (`ed03c86`, tasktodo:13) | thêm frontmatter `done` |
| 7 | T125-qa-tab-safe-fallback | **NO_STATUS** | DONE (tasktodo:157) | thêm frontmatter `done` |
| 8 | T126-qa-backend-real | **NO_STATUS** | DONE (tasktodo:156) | thêm frontmatter `done` |
| 9 | T139-zen-lineage-gateway | **NO_STATUS** | IN_PROGRESS Phase 2 completion, chờ HITL (tasktodo:35) | thêm frontmatter `in_progress` |

**Gốc rễ #6–9:** `scripts/build_progress_data.py` `parse_frontmatter()` yêu cầu file bắt đầu bằng `---`; 4 file này bắt đầu bằng `# T...` → meta rỗng → `status = 'pending'`. Cần thêm frontmatter YAML chứ không sửa code.

## 2. Sửa frontmatter (T166)
- 5 file edit trực tiếp `status:` (T131 → done + updated 2026-09-18; T137/T138 → done; T110 → done; T52 → done + updated 2026-09-11).
- 4 file thêm frontmatter YAML mới đầy đủ (id/title/priority/status/owner/module/created/updated) trước heading `# T...`:
  - T97b: `status: done`
  - T125: `status: done`
  - T126: `status: done`
  - T139: `status: in_progress`

## 3. Regen dashboard (T166)
```
python -X utf8 scripts/build_progress_data.py
```
→ 15 module · 235 endpoint đối chiếu · **89 task trên board (done=57, blocked=2)** · git 460 commits (2026-08-14 → 2026-09-24).

Verify JSON:
```
T110 done · T125 done · T126 done · T130 done · T131 done · T137 done · T138 done · T139 in_progress · T165 done · T52 done · T97b done
done=57 · in_progress=17 · pending=13 · total=89
```
(done 49→57 do +8: T131/T137/T138/T110/T52/T97b/T125/T126; T139 pending→in_progress chứ không thành done.)

## 4. T164 — Autoverify
### Static (places.html HEAD, code committed `77dec5e` 2026-09-23)
| Step | Kiểm tra | Kết quả |
|------|----------|---------|
| S1 | count decorator trong `_buildFtVisTree` | L6498/6499 giữ `▸`/`▾` thuần (không `N hậu duệ`/`N đệ tử`) ✓ |
| S2 | ancestor bar | 0 tham chiếu (`ancestor-bar|ancestorChain|lineage-ancestors` = 0) ✓ |
| S3 | zoom buttons | `lineage-zoom-in/out` = 0 trong places.html ✓ |
| S4 | legend row | `lineage-legend-row` ×3 (HTML + JS) ✓ |
| S5 | evidence wrap | `lineage-inspector-evidence-wrap` ×2; `flex 0 0 0px`↔`1 1 50%` ở `_setLineageEvidence` L5794-5802 ✓ |
| S6 | overflow ellipse | L6533 `shape:'ellipse'` ✓ |
| S7 | footer details | L6754-6766 `<details>/<summary>` + `return null` khi không warnings ✓ |
| S8 | heightConstraint | `minimum: 52` ✓ |

### Browser QA (Playwright live :8080)
Script driver: `scripts/qa_t164_browser*.js` (tạm, sinh từ temp — KHÔNG commit, chỉ để QA).
| Check | Kết quả |
|-------|---------|
| `#lineage-zoom-in/out` absent | ✓ true |
| `#lineage-legend-row` present + visible | ✓ (rect 980×21, display block) |
| evidence wrap khởi tạo | ✓ `flex: 0 0 0px` (collapsed) |
| `openPersonLineage('A000958')` → network render | ✓ canvas=1, 0 JS error |
| select node → evidence expand | ✓ `flex: 1 1 50%`, evidence visible, tiểu sử + nguồn DILA hiển thị |
| JS console errors toàn phiên | ✓ none |
| Footer warnings | ✓ details collapsed; `_t129NetFooter` trả null khi không có dropped/cycle (0 cảnh báo giả) |
| API probe `A000958` lineage-tree | ✓ 200, 4 nodes sample [A000958, A031380, A022489] |

**Kết luận T164:** PASS. Đóng task file `status: in_progress → done`, đánh dấu 4/5 mục verify thủ công → checked (browser QA), giữ mục "Admin QA ×1" open cho Lee confirm live sau restart :5000.

## 5. Docs updated
- `tasks/T166-dashboard-hygiene-batch.md` (mới, status done)
- `tasks/T164-lineage-tree-ui-cleanup.md` (status done + verify checked + Status body)
- 9 file task frontmatter staged (section §2)
- `data/progress_data.json` (regen)
- `docs/tasktodo.md` (rows T166 + T164 đầu ACTIVE)
- `docs/ROLLBACK.md` (row T166 `14412bf`, row T164 `77dec5e`)
- `docs/sessions/2026-09-24_t166-dashboard-hygiene-batch.md` (này, chung T166+T164)

## 6. Commit plan
Từ toplevel `visjs-app` (SSOT T155):
1. **Commit 1 (`14412bf`):** `docs: T166 — dashboard hygiene batch (frontmatter 9 task sync + regen) + T164 UI cleanup docs closure` — stage đúng 15 file của mình (9 task + T166 + T164 + progress_data.json + tasktodo + ROLLBACK + session). 15 files changed · 277 insertions · 66 deletions.
2. **Commit 2 (hash-fill 2-pass chuẩn T146):** điền hash thật `14412bf` vào `docs/ROLLBACK.md` row T166 + `tasks/T166` body + tasktodo row T166 Revert.
3. Verify: `npm run guard` PASS · `git status` còn lại chỉ file dirty pre-existing (about.html, *.bak, scratch).

## Notes / Blocker
- `python -X utf8 scripts/build_progress_data.py` chạy OK (workdir daoanh).
- PowerShell: bash tool = PowerShell; tránh `&&`/`head`; `python -c` nhiều dòng fail → dùng script file hoặc one-liner.
- `qa_t164_browser*.js` để ở temp — KHÔNG stage (tránh commit file QA phế).
- git auto-gc permission warning pre-existing (commit vẫn thành công).