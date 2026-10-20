# Session 2026-09-24 — T130 Session 4: Deep-link + pushState/popstate state sync Pháp Mạch

**Task:** `tasks/T130-phap-mach-direct-lineage.md` P2.6 · **👑 Lee** · Commit: `74ef34c`

## Công việc đã làm

### 1. Audit block deep-link cũ → TÁN THÀNH rewrite (chết hoàn toàn)
- `#t130-chain-box` KHÔNG tồn tại trong HTML — chỉ 2 tham chiếu JS trong block cũ (dòng ~9933-9934).
- Block cũ gọi `/api/lineage/expand` — route đã được T130 Session 1 (`f07d8cb`) RENAME thành `/api/lineage/expand-primary` → **luôn 404**.
- ⇒ Block không chạy được, không có người dùng nào phụ thuộc → thay bằng module Session 4 (giữ tên `T130.deepLink` cho tương thích).

### 2. Module Session 4 (additive, thay block cũ: +99 dòng)
| Hàm | Chức năng |
|-----|----------|
| `T130.serialize()` | Đọc `_lineageState` → `?mode=lineage&focus=<canonical pid>&lm=<mode>&chain=<expanded ids>`; key = canonical id, KHÔNG position index (spec P2.6) |
| `_t130SyncUrl()` | pushState khi user gesture (pointerdown capture `<800ms`), replaceState khi programmatic; dedupe theo `location.search` + `T130.lastUrl` |
| `restoreFromUrl(q)` | Same-focus → click tab lineage + `applyChain` + `_renderLineageMode(lm)`; khác focus → `window._t130Pending` + `selectPerson(focus)` |
| `deepLink()` | `mode=lineage` (mới) + legacy `?expand=<id>` → map `mode=lineage&focus=<id>&lm=tree` |
| popstate | URL `mode=lineage` → `restoreFromUrl(q)` |

### 3. Guard hooks (additive 0 ALTER, chỉ thêm dòng mới)
1. `_renderLineageChain` ~6402: consume `window._t130Pending` hợp focus → set `st._ftExpanded` = `[center].concat(chain)` TRƯỚC auto-expand (override 3-đời mặc định) + set `st._t130PendingLm` nếu khác mode.
2. `_renderLineageChain` end ~6711: switch `st._t130PendingLm` → `_renderLineageMode(lm)`; else `_t130SyncUrl()`.
3. `_renderLineageNetwork` end ~6875: `_t130SyncUrl()` (caption mode switch + expand).
4. `_renderLineageTimeline` end ~6894: `_t130SyncUrl()`.
5. `rerender` (tree): `_renderLineageChain()` + `_t130SyncUrl()` — mọi expand/collapse/pick user đều đồng bộ URL.

## Quyết định thiết kế / giới hạn (documented)
- `pick`/`tup` (spec P2.6) KHÔNG có state riêng trong Session 2 — tương đương "node đang mở" ⇒ serialize gọn về `chain` (danh sách expanded ids). Không phát sinh param riêng.
- Network expand depth (`_netExpand{above,below}`) KHÔNG đưa vào URL (giữ scope Session 4 = focus + mode + chain). Nếu cần có thể thêm `&net=above:below` ở Session 5.
- `?select=`, `?fly=`, `?nexus_root=`, `?nexus_type=` (window.onload legacy) giữ nguyên — module chỉ đọc khi `mode=lineage`/`expand` xuất hiện, không chặn flow cũ.
- `_lineageState` là `let` top-level classic script ⇒ đọc bằng bare name `_lineageState` (KHÔNG `window._lineageState` — sẽ undefined).

## Verify
- `node --check` places.html **3/3 script blocks PASS** (extract script → temp .js → check).
- `npm run guard` **PASS** (SSOT root = visjs-app, không `.git` trong daoanh).
- `npm run e2e` **PASS** (4/4 pages).
- Sạch tham chiếu: `#t130-chain-box` 0 · `t130-node` 0 · `t130-gate` 0 · `/api/lineage/expand?` 0.
- app.py KHÔNG đụng (backup `places.html.backup_t130_s4`, git diff chỉ 1 file).

## Session trước
`docs/sessions/2026-09-24_t130_session2_frontend_core.md`

## Tasktodo
- T130 Session 1 ✅ `f07d8cb` · Session 2+3 ✅ `f125c44` · Session 4 ✅ `74ef34c` · **PENDING Session 5: T129 regression + browser QA.**