# Session: 2026-09-14 T138 — Zen Lineage Render Policy + Edge Assertion Model

## Mục tiêu
Xây mô hình render-rule (edge assertion multi-source + trust L1–L4) +代码化 cho Pháp mạch, theo thẩm định *"Quy tắc vẽ cây"* (2026-09-14). Đảm bảo: (1) không ingest Zen Lineage (BLOCKED) (2) grandfather Marcus zero-surprise (3) compute flow từ DB có thể revert.

## Kết quả thật

| Chỉ số | Giá trị |
|---|---|
| `scripts/etl_t138_edge_assertions.py` — py_compile + --dry-run | OK (Marcus 11,169 / DILA rows 31,513 → ~46,006 assertions / reject 0) |
| `--apply` trên DB | ✓ backup `lineage_t138_20260914_193711.db` 1.42 GB; CREATE TABLE + INDEX; MARCUS 11,169 L1; DILA 46,006 L2; ZEN 0 |
| `app.py` `_t138_edge_assertions()` helper | ✓ py_compile OK; verify cặp thật `A000005→A000668` = MARCUS L1; cặp giả = rỗng |
| `api_monk_lineage_tree` overlay (app.py) | ✓ edge có `sources[]`+`trust_level`+`rejected`; rejected edges filtered khỏi Pháp mạch chuẩn |
| `places.html` `_t127EdgeStyle` | ✓ L3 dashed [5,5] + tooltip ★Candidate; L1/L2 giữ nguyên |
| `places.html` `_applyLineageFilters` (filter "Chỉ cạnh L1–L2") | ✓ tl L1/L2 hoặc has_ref (legacy); behavior unchanged hiện tại |
| `places.html` `_renderLineageInspectorEdge` | ✓ block "Nguồn ghi nhận" MARCUS ✓/— / DILA ✓/— / ZENLINEAGE ✓/— + trust badge + display verdict |
| Filter label | Đổi "Chỉ quan hệ có dẫn chứng" → "Chỉ cạnh L1–L2 (đã xác nhận)" |
| `docs/ZEN_LINEAGE_INTEGRATION_AUDIT_V1.md` §11 + §13 | Update render-policy + G6a + link T138 |
| `docs/tasktodo.md` | T138 ACTIVE top; T137 → DONE |
| places.html JS syntax (node --check) | OK |
| **Live-verify :5000 (restart PID 9736)** | ✓ API cạnh có `sources[]`+`trust_level`+`rejected`; 415 edges all-with-sources |
| **DILA direction-mismatch fix (post-restart)** | ✓ `_t138_edge_assertions` kiểm tra 2 chiều; 22,326 DILA reversed → gắn `direction_mismatch=true`, không contribute trust; inspector "⚠ DILA — ngược chiều" |

## Files changed
- `scripts/etl_t138_edge_assertions.py` (mới)
- `app.py` (additive: +helper `_t138_edge_assertions`, overlay 2 edge-blocks, filter rejected)
- `places.html` (edge style L3, inspector sources, filter label+logic)
- `docs/ZEN_LINEAGE_INTEGRATION_AUDIT_V1.md` (§11 render policy, §13 UI update)
- `docs/tasktodo.md` (T138 ACTIVE, T137 DONE)

## Backups
- `data/backups/lineage_t138_20260914_193711.db`

## Rollback
- `python scripts/etl_t138_edge_assertions.py --revert` — DROP `lineage_edge_assertions` (0 ALTER base).
- Git revert commits (temp-index policy): TBD.

## Ghi chú
- DILA assertions xuất phát từ `lineage_conflicts_v2` (set thầy/trò = aggregate JSON) → không có ref riêng, trust L2.
- **DILA direction (data reality):** DILA lưu `student→teacher` ngược chiều Marcus `teacher→student`. Trong 22,326 DILA trùng cặp Marcus: 0 same-direction, 22,326 reversed. → L2 confirmation từ DILA không thể xuất hiện trên cạnh Marcus hiện tại (DILA luôn contest chiều). Fix: `_t138_edge_assertions` trả direction_mismatch, trust giữ L1 xác nhận từ Marcus.
- Zen Lineage = BLOCKED → 0 rows, schema sẵn sàng. Khi license mở + HITL approved → assertions ZENLINEAGE thêm vào + render tự nhiên.
- Conflict show+mark giữ nguyên (không ẩn) — đúng T109/T136.
- Bulk apply DILA assertion dùng `teacher_set` = "thầy của person" → subject=thầy, object=person; `student_set` = person→trò.