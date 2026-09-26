# Session — T152 Pháp Mạch Ancestor Spine — Code Telemetry (2026-09-17)

> **Code closure — additive · endpoint read-only · 2 file (`app.py` + `places.html`) · 0 DB write · 0 ALTER · 0 Schema · 0 ALTER TABLE · mirror chuẩn T148/T140.**
> Frame: `docs/sessions/2026-09-17_t151-phap-mach-ancestor-spine-docs-closure.md` (acceptance A1..A8). Revert: `git revert --no-edit <sha_code_T152>` (chỉ 2 file, 0 DB write).

---

## 1. Root cause (đã verify thật)

| # | Vị trí | Vấn đề |
|---|--------|--------|
| 1 | `places.html:4865` (`loadLineageTree`) | fetch hardcode `?up=2&down=2` → chỉ xin 2 đời tổ |
| 2 | `places.html:5032` (`centerLineageOn`) | fetch hardcode `?up=2&down=2` |
| 3 | `app.py` `api_monk_lineage_tree` | clamp `up/down` về `[0,6]` → không thể trả spine dài |
| 4 | `places.html:6226` (network `keep`) | `gen[pid] >= -st._netExpand.above` cắt chuỗi tổ theo "2/3 đời" |
| — | `_renderLineageChain` / `_lineageBuildRows` | **ĐÃ ĐÚNG** — climb `parents` vô hạn, cycle-safe `seenUp` |

Kết luận: renderer sẵn sàng; bug ở **tầng dữ liệu + filter hiển thị**.

## 2. Thay đổi

### 2.1 `app.py` — endpoint mới (additive, read-only)
- `GET /daoanh/api/monk/<dila_id>/ancestor-spine?max_hops=80` (chèn sau `api_monk_root_ancestor`, trước `@app.route('/daoanh/api/lineage-ref/passage')`).
- Đi bộ teacher-chain bằng `_t86_neighbors(dila_id, 'up')`, lọc cạnh `rejected` qua `_t138_edge_assertions` (bảng DERIVED `lineage_edge_assertions`).
- Safety `max_hops` (mặc định 80). Cycle-safe bằng `seen`.
- Trả: `{ok, center, ancestors[] (gần→xa), nodes, edges, break_reason: 'root'|'rejected'|'safety', hops, max_hops, has_more_up}`.
- `has_more_up = break_reason in ('rejected','safety')`.

### 2.2 `places.html` — client merge + filter + label
1. `_lineageState` init: `up:2, down:2` → **`up:6, down:6`** + thêm `_spine: null`.
2. `loadLineageTree`: fetch `up=2&down=2` → **`up=6&down=6`** + `_lineageState._spine = null` + gọi `_lineageMergeAncestorSpine(dilaId)`.
3. **Helper mới `_lineageMergeAncestorSpine(pid)`** (sau `_linLoadAbort`): fetch `ancestor-spine`, merge `nodes/edges` vào `st.nodes/st.edges`, re-render khi có thay đổi.
4. `centerLineageOn`: bump fetch + `_spine = null` + merge.
5. `_lineageExpandRefetch`: thêm merge.
6. Network `keep` filter (≈6226): `gen[pid] < 0 || gen[pid] <= st._netExpand.below` → **chuỗi tổ (gen < 0) luôn giữ**, "2/3 đời" chỉ cắt ĐỆ TỬ phía dưới.
7. Network bar `'Thu gọn'` → **`'Thu gọn nhánh dưới'`** (≈6186/6202) + info text mới.
8. Chain bar `'Thu gọn'` → **`'Thu gọn nhánh dưới'`** + tooltip 2/3-đời (≈6111-6130).
9. `_renderLineageChain`: banner **stop-at-broken HONEST** (node `__spine_more_up__` + dashed edge) khi `has_more_up == true` — nói rõ lý do đứt, KHÔNG bịa cạnh.

## 3. Verify

- `python -m py_compile app.py` → **PY OK**.
- `@babel/parser` parse `places.html` → 5 script blocks, **0 error** (script#5 @line 847, 520784 chars).
- **Smoke test** Flask `test_client`: `A000958` → spine **48 đời** tới root `A004683`, `break_reason='root'`, `hops=48`, `has_more_up=False`, edges=48, nodes=49, **bad edges=0** (trước đây tối đa 2 đời).
- `npm run test` → ✅ Tests passed · `npm run e2e` (static) → ✅ All pages passed.
- `npm run tester:agent` → lint ✅ / test ✅ / e2e ✅; `e2e:runtime` **EPERM** khi unlink `test-results\.last-run.json` — **khóa tiền tồn tại** (không do thay đổi này); chạy `npx playwright test --output=.pw-tmp` → **2/2 PASS**.

## 4. Trụ SSOT

| Trụ SSOT | File | Trạng thái |
|----------|------|-----------|
| Canonical task | `tasks/T152-phap-mach-spine-code-telemetry.md` | **1 unique** ✓ |
| Canonical session | `docs/sessions/2026-09-17_t152-phap-mach-spine-code-telemetry.md` | **1 unique** ✓ (file này) |
| tasktodo row | `docs/tasktodo.md` T152 | **DONE** ✓ |
| ROLLBACK row | `docs/ROLLBACK.md` T152 | hash-fill real 2-pass (placeholder → real `git rev-parse`) |
| Dashboard | `data/progress_data.json` | regen real `build_progress_data.py` ✓ |
| Leftover | scripts/ `*t152*` | **0 cleaned** ✓ |

## 5. Revert

`git revert --no-edit <sha_code_T152>` → hoàn nguyên `app.py` + `places.html` về trước fix (0 DB write, nên không cần rollback DB).
