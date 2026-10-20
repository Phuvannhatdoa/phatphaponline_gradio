# T381 Execution Log — 3-Source Dharma Lineage with Y-Fork Rendering (REVISED — Option A)

**Task**: T381 — Y-fork rendering (TTL + Marcus + DILA), reuse `lineage_edge_consensus`
**Date**: 2026-10-14
**Operator**: daoanh-debugger (Claude)
**Plan**: REVISED PLAN (2026-10-14) trong `tasks/T381-build-dharma-lineage-3sources.md`
— KHÔNG dùng ORIGINAL PLAN (3 bảng mới). Tái sử dụng `lineage_edge_consensus` (T158).
**Status**: ✓ DONE (3 bước chính đã implement + test bằng dữ liệu thật)

---

## Bước 1 — ETL TTL → `lineage_edge_consensus.ttl_asserted`

**Script**: `scripts/t381_etl_ttl_into_consensus.py` (mới, có `--dry-run` mặc định, `--apply`,
`--revert`).

**Crosswalk**: `dharma_lineage_ttl_vn.teacher_id/student_id` (`ex:monk/<slug>`) → bỏ prefix →
`vn_person_authority.id = <slug>` → `vn_person_authority.dila_id` → map vào
`lineage_edge_consensus.teacher_id/disciple_id` (relation_type='dharma_transmission').

**Kết quả thực tế (chạy `--apply` lúc 2026-10-14 08:41:25)**:

| Hạng mục | Số liệu thật |
|---|---|
| TTL edges tổng (`dharma_lineage_ttl_vn`) | 784 |
| Crosswalk khớp cả 2 đầu (có dila_id) | 553 |
| Mismatch teacher slug (không có trong `vn_person_authority` hoặc dila_id rỗng) | 101 |
| Mismatch student slug | 128 |
| Empty teacher slug (`ex:monk/` — khai tổ không có thầy) | 2 |
| **UPDATE `ttl_asserted=1` thực tế** | **149 dòng** |
| Đã `ttl_asserted=1` từ trước (no-op, idempotent — lần chạy 2) | 149 (= toàn bộ, xác nhận idempotent) |
| TTL có cạnh hợp lệ nhưng KHÔNG có dòng `lineage_edge_consensus` tương ứng (log, KHÔNG insert) | 399 |

Vì `ttl_asserted` là 1 trong 4 cột góp vào `agreeing_source_count`/`consensus_status`/
`source_badge` (theo công thức gốc trong `scripts/t158_consensus_migration.py`), script ETL
cũng **recompute 4 cột dẫn xuất đó** cho 149 dòng bị update (không chỉ set riêng `ttl_asserted`),
để tránh trạng thái "ttl_asserted=1 nhưng badge vẫn ghi 1 nguồn". Quyết định này được ghi rõ
trong docstring của script.

**Backup tự động**: `docs/sessions/2026-10-14/lineage.db.backup_t381_etl_20261014_084125`
(trước khi UPDATE thật).

**Idempotent**: chạy `--apply` lần 2 → "Sẽ UPDATE: 0 dòng / Đã ttl_asserted=1 từ trước: 149"
— xác nhận không ghi đè/không tăng đôi.

**PRAGMA quick_check sau UPDATE**: `ok`.

**Không fabricate**: 229 slug mismatch (101+128) được log ra stdout (không insert đoán), 399 TTL
edges không có dòng consensus tương ứng được log riêng, KHÔNG tự INSERT — admin quyết định sau.

---

## Bước 2 — `calculate_edge_color_and_divergence()` trong `app.py`

**Vị trí**: `app.py`, ngay trước route `/daoanh/api/monk/<dila_id>/lineage-tree`
(hàm `api_monk_lineage_tree`, dòng ~6493 gốc).

**Quy tắc màu** (đúng 5 quy tắc admin xác nhận + 2 fallback có ghi chú):

| Điều kiện | Màu | Dashed | is_divergence |
|---|---|---|---|
| DILA=1, Marcus=1, TTL=1 | GREEN `#22c55e` | false | false |
| TTL=1 + đúng 1 nguồn khác | GREEN `#22c55e` | false | false |
| DILA=1, Marcus=1, TTL=0 | PURPLE `#a855f7` | false | false |
| Chỉ Marcus=1 | YELLOW `#eab308` | true | **true** |
| Chỉ DILA=1 | BLUE `#3b82f6` | true | **true** |
| Chỉ TTL=1 (fallback, không có trong 5 quy tắc gốc — xử lý như trục chính thức) | GREEN | false | false |
| Không nguồn nào (không nên xảy ra) | GRAY `#6b7a8a` (fallback an toàn) | true | false |

Hàm được gọi tại cả 2 nhánh BFS (lên/thầy và xuống/trò) trong `api_monk_lineage_tree`, dùng
trực tiếp `dila_asserted/marcus_asserted/ttl_asserted` đã có sẵn trong kết quả
`_t158_neighbors_consensus()` (không query thêm).

**Response JSON mới** (cộng thêm, KHÔNG đổi field cũ):
- Mỗi edge: `edge_color`, `edge_dashed`, `is_divergence`.
- Top-level: `tree_status: {has_divergence, divergence_count}`.

**Phân bố màu thật trên toàn bảng `lineage_edge_consensus` (23,018 dòng, sau ETL)**:

| Màu | Số cạnh |
|---|---|
| GREEN — cả 3 nguồn | 133 |
| GREEN — TTL + 1 nguồn khác | 16 |
| PURPLE — Marcus+DILA, không TTL | 11,032 |
| YELLOW — chỉ Marcus | 4 |
| BLUE — chỉ DILA | 11,833 |

---

## Bước 3 — Frontend VisJS (`places.html`)

**Vị trí xác nhận**: không có `static/js/lineage-tree.js`; render nằm inline trong
`places.html`, chia sẻ qua `_t127EdgeStyle()` (style) + `_renderHierarchyTree()` (canvas vẽ
orthogonal edges thủ công qua `ctx`, KHÔNG dùng màu của vis.js DataSet trực tiếp).

**Phát hiện quan trọng khi code**: `_t127EdgeStyle()` chỉ set `color/dashes/title` cho object
trả về, nhưng `_renderHierarchyTree()` strip toàn bộ style trước khi tạo `vis.DataSet` (dòng
`cleanEdges = visEdges.map(... {id,from,to,title})`) rồi tự vẽ cạnh bằng canvas `ctx`, đọc trực
tiếp các field `edge._hasRef/_isSingle/_conflict` từ `visEdges` gốc — **không đọc `color` trả
về từ `_t127EdgeStyle()`**. Vì vậy, ngoài việc sửa `_t127EdgeStyle()` để trả Y-fork color khi có
`edge_color`, còn phải:
1. Gắn `_edgeColor/_edgeDashed/_isDivergence` vào từng phần tử `visEdges` tại 2 nơi build cây
   (Pháp mạch mặc định + Phả hệ mở rộng).
2. Sửa canvas `afterDrawing` routine để ưu tiên `edge._edgeColor` (khi không phải trục tổ sư
   chính `isMain`) thay cho phân loại single/confirmed cũ.

Việc này được phát hiện qua browser-verify thực tế (xem bên dưới) — nếu bỏ qua, API đã đúng
nhưng canvas vẫn vẽ màu cam/vàng cũ, không khớp dữ liệu.

**Thay đổi**:
- `_t127EdgeStyle(e, hasRef, conflictTouched)`: nếu `e.edge_color` có → dùng màu/dashed đó
  (ưu tiên hơn phân loại single_source/candidate cũ); nếu không có (ví dụ cạnh từ
  `/ancestor-spine`, chưa gắn T381) → fallback logic cũ nguyên vẹn.
- `_renderHierarchyTree()` canvas routine: thêm `hasYFork = !isMain && edge._edgeColor`,
  dùng màu/dash/opacity theo Y-fork khi có, giữ nguyên màu cam đậm `#e8941a` cho trục tổ sư
  chính (`isMain`) — không đổi semantics ancestor-spine hiện có.
- Legend mới `#lineage-yfork-legend` (tĩnh trong sidebar, ẩn mặc định) — hiện khi
  `tree_status.has_divergence=true`, hiển thị cả 4 màu GREEN/PURPLE/YELLOW/BLUE + dòng cảnh báo
  số cạnh phân kỳ. Hàm `_t381RenderYForkLegend(treeStatus)` được gọi ở cả 3 nơi fetch
  `lineage-tree` (load ban đầu, `centerLineageOn`, `_lineageExpandRefetch`).
- Detail panel khi click person (`_renderLineageInspector`): thêm block
  `_t381PersonYForkBadges(pid)` — liệt kê từng cạnh thầy/trò chạm người đó kèm chấm màu +
  tên màu + source_badge, và cảnh báo "⚠ Y-fork: N cạnh chỉ 1 nguồn..." nếu có cạnh
  `is_divergence=true`.

---

## Test thật (không fabricate)

### Case PURPLE (Marcus+DILA, TTL chưa có) — `A000005`
`GET /daoanh/api/monk/A000005/lineage-tree?up=1&down=1&include_single=1`
→ `A000153→A000005`, `A000005→A000668/A003958/A003960/A004000/A004014/A037639`: tất cả
`edge_color=#a855f7, edge_dashed=false, is_divergence=false` — khớp DB
(`dila_asserted=1, marcus_asserted=1, ttl_asserted=0`).

### Case BLUE dashed (chỉ DILA) — `A000006`
`GET /daoanh/api/monk/A000006/lineage-tree?up=1&down=1&include_single=1`
→ `tree_status: {has_divergence: true, divergence_count: 17}`; 17 cạnh con
`A000006→A028085...A035502` đều `edge_color=#3b82f6, edge_dashed=true, is_divergence=true`.
Xem browser thật (xem bên dưới): đúng 17 cạnh xanh dương nét đứt trong cả 2 chế độ xem
"Pháp mạch" và "Phả hệ mở rộng".

### Case GREEN (3 nguồn / TTL-confirmed) — `A000108`
`GET /daoanh/api/monk/A000108/lineage-tree?up=1&down=1&include_single=1`
→ `A000108→A021261`, `A000108→A021262`: `edge_color=#22c55e, source_badge="3/4: Marcus,
DILA, TTL", consensus_status=confirmed_2plus` (2 dòng này nằm trong 149 dòng ETL vừa update) —
các cạnh anh em khác của cùng node (`A000108→A021259/A021260/...`) không có TTL nên vẫn
`edge_color=#a855f7` (PURPLE) — đúng Y-fork thật giữa các con của cùng 1 thầy.

### Browser-verify thật (bắt buộc theo quy trình, không JS inject claim done)
Mở `http://127.0.0.1:8080/daoanh/places?mode=lineage&focus=A000006&lm=tree` (và `lm=network`)
qua gateway local đang chạy (port 8080) + `app.py` (port 5000, khởi động tạm để test, đã dừng
sau khi xong):
- Sidebar hiện section mới "Y-FORK · 3 NGUỒN" với 4 màu đúng thiết kế + dòng cảnh báo
  "⚠ Y-fork: 57 cạnh phân kỳ nguồn trong pháp hệ đang xem" (tổng cạnh phân kỳ trong cây đã
  tải, bao gồm cả nhánh mở rộng).
- Panel "Chi tiết tăng nhân" khi click node "Nhất Ninh" (A000006) hiện block "NGUỒN TRUYỀN
  THỪA (Y-FORK)" với cảnh báo "⚠ Y-fork: 17 cạnh chỉ 1 nguồn..." + danh sách 17 dòng
  "truyền cho ... · Xanh dương (chỉ DILA) (1/4: DILA)".
- Canvas (cả 2 mode "Pháp mạch" và "Phả hệ mở rộng") vẽ đúng màu tím/xanh dương theo dữ liệu
  — xác nhận bằng `_lineageNetwork.body.data.edges` qua `javascript_tool` (đọc dữ liệu đã
  render, không phải claim bằng cách tự inject đổi DOM) và bằng zoom screenshot thực tế.
- Trục tổ sư chính (ancestor spine, node "Nhất Ninh" lên "Hành Di") vẫn giữ màu cam đậm
  `#e8941a` như cũ — không bị Y-fork ghi đè (đúng thiết kế giữ nguyên semantics cũ).

---

## Regression check

- `python -m py_compile app.py` → OK (không lỗi cú pháp).
- `node --check` trên toàn bộ 8 block `<script>` inline của `places.html` (extract bằng regex,
  check 3 lần sau mỗi đợt sửa) → OK cả 3 lần.
- `GET /daoanh/api/monk/A000005/root-ancestor` → HTTP 200 (không đổi).
- `GET /daoanh/api/monk/A000005/ancestor-spine` → HTTP 200 (không đổi).
- Response JSON của `api_monk_lineage_tree` giữ nguyên toàn bộ field cũ (`sources`,
  `trust_level`, `rejected`, `source_badge`, `agreeing_source_count`, `consensus_status`) —
  chỉ cộng thêm `edge_color/edge_dashed/is_divergence` (per-edge) và `tree_status` (top-level).
- Không có `ALTER TABLE`, không `DROP TABLE`, không đổi cột nào trong
  `lineage_edge_consensus` — chỉ `UPDATE` giá trị của các cột đã tồn tại
  (`ttl_asserted`, `agreeing_source_count`, `consensus_status`, `is_default_visible`,
  `source_badge`, `updated_at`).

---

## Files changed

- `scripts/t381_etl_ttl_into_consensus.py` (mới)
- `app.py` — thêm `calculate_edge_color_and_divergence()`, gắn vào 2 nhánh BFS của
  `api_monk_lineage_tree`, thêm `tree_status` vào response.
- `places.html` — `_t127EdgeStyle()`, `_renderHierarchyTree()` (canvas afterDrawing),
  2 nơi build `visEdges` (Pháp mạch + Phả hệ mở rộng), `_renderLineageInspector()`,
  thêm `_t381RenderYForkLegend()`, `_t381PersonYForkBadges()`, block legend tĩnh trong HTML.
- `docs/sessions/2026-10-14/lineage.db.backup_t381_etl_20261014_084125` (backup tự động, mới)

## Limitation / việc còn treo cho admin quyết định

- ~~399 TTL edges có teacher/disciple hợp lệ (đã crosswalk ra DILA id) nhưng
  `lineage_edge_consensus` CHƯA có dòng tương ứng — KHÔNG tự INSERT.~~ **Đã quyết định và
  thực hiện — xem "Bước 4 (Decision 5, 2026-10-15)" bên dưới.**
- 229 slug TTL (101 teacher + 128 student) không crosswalk được do `vn_person_authority`
  thiếu `dila_id` tương ứng — out of scope T381 (thuộc về chất lượng dữ liệu
  `vn_person_authority`, không phải lỗi ETL).
- Quy tắc "chỉ TTL=1" (không DILA, không Marcus) không nằm trong 5 quy tắc màu admin liệt kê
  gốc — xử lý fallback GREEN (ghi chú rõ trong code), nên xác nhận lại với admin nếu có case
  thật phát sinh.

---

## Bước 4 (Decision 5, 2026-10-15) — Insert 399 TTL-only edges vào consensus

**Admin quyết định**: ghi nhận 399 cạnh TTL đã crosswalk được nhưng chưa có dòng
`lineage_edge_consensus` tương ứng (nêu ở "Limitation" phía trên) — INSERT dòng mới, đánh dấu
rõ `consensus_status='ttl_only'` để tách biệt khỏi cạnh đã có ≥2 nguồn, dễ review sau.

**Script**: `scripts/t381_insert_ttl_only_edges.py` (mới, có `--dry-run` mặc định, `--apply`).
Import trực tiếp `classify_ttl_edges()`/`plan_updates()`/`_rebuild_badge()` từ
`t381_etl_ttl_into_consensus.py` — không viết lại logic crosswalk đã validate.

**Backup trước khi sửa**:
- `data/lineage.db.backup_before_ttl_insert_t381` (copy tay theo yêu cầu, trước mọi thay đổi).
- `docs/sessions/2026-10-15/lineage.db.backup_t381_ttlonly_20261015_102543` (backup tự động
  của script, ngay trước khi UPDATE/INSERT thật trong `--apply`).

**Số liệu before/after `--apply` (chạy 2026-10-15 10:25:43)**:

| Hạng mục | Số liệu |
|---|---|
| Candidates khớp `no_consensus_row` tại thời điểm chạy | 399 (khớp đúng số đã ghi ở Bước 1) |
| `lineage_edge_consensus` tổng dòng — trước | 23,018 |
| `lineage_edge_consensus` tổng dòng — sau | 23,417 (delta +399) |
| `consensus_status='ttl_only'` — trước | 0 |
| `consensus_status='ttl_only'` — sau | 399 (delta +399) |
| Duplicate theo (teacher_id, disciple_id, relation_type) | 0 |
| `PRAGMA quick_check` | `ok` |

**Mỗi dòng insert có**: `ttl_asserted=1`, `dila_asserted=0`, `marcus_asserted=0`,
`lineage_asserted=0`, `agreeing_source_count=1`, `opposite_source_count=0`,
`consensus_status='ttl_only'` (ghi đè công thức tự động của `t158_consensus_migration.py` —
công thức gốc với n_sources=1 sẽ cho `'single_source'`, ở đây dùng `'ttl_only'` theo yêu cầu
admin để nhóm tách biệt), `is_default_visible=0`, `source_badge='1/4: TTL'`,
`relation_type='dharma_transmission'`, `migration_marker='T381_TTL_ONLY_INSERT_20261015'`.

**Idempotent test**: chạy `--apply` lần 2 ngay sau đó → script tính lại tập `matched` (dedup)
= 548 cạnh = 149 (đã có từ Bước 1) + 399 (vừa insert) đều đã có dòng trong consensus →
`to_insert=0` → in "Không có dòng nào cần INSERT ... Không ghi DB." (không UPDATE/INSERT gì
thêm, không backup lần 2, exit code 0) — xác nhận không ghi đè/không tăng đôi.

**Lưu ý kỹ thuật phát hiện khi viết script**: không thể dùng lại trực tiếp
`plan_updates().no_consensus_row` làm "candidate set" lâu dài, vì tập đó tự thu hẹp dần theo
trạng thái hiện tại của `lineage_edge_consensus` (sau khi insert, cặp đó không còn là
"no_consensus_row" nữa) — dùng nó cho lần chạy thứ 2 sẽ cho ra 0 và dễ bị hiểu nhầm là lỗi dữ
liệu. Script mới dùng tập `classify_ttl_edges().matched` (553 cạnh, chỉ phụ thuộc
`dharma_lineage_ttl_vn` + `vn_person_authority`, không phụ thuộc trạng thái `lineage_edge_consensus`)
làm cơ sở cố định, rồi tự kiểm tra "đã có dòng consensus chưa" tại mỗi lần chạy — cách này cho
kết quả đúng và ổn định ở cả lần chạy đầu và các lần chạy lại.

**Không sửa các số liệu lịch sử** đã ghi ở Bước 1 (149 dòng update, 399 không có dòng consensus,
229 lệch, 2 thầy trống) — mục này chỉ bổ sung bước xử lý tiếp theo cho riêng 399 cạnh đó.

**Files**:
- `scripts/t381_insert_ttl_only_edges.py` (mới)
- `data/lineage.db.backup_before_ttl_insert_t381` (backup tay, mới)
- `docs/sessions/2026-10-15/lineage.db.backup_t381_ttlonly_20261015_102543` (backup tự động của
  script, mới)

---

## Bước 4b (QA round 2 fix, 2026-10-15)

**Nguồn**: `daoanh-qa` kiểm chứng kết quả insert 399 dòng ở Bước 4, báo CHƯA ĐẠT vì
6/399 dòng lỗi.

**Lý do xóa 6 dòng**:
- **LỖI A — 5 cạnh self-loop** (`teacher_id = disciple_id`): do crosswalk gộp nhầm 2
  slug TTL khác nhau vào cùng 1 DILA id trong `vn_person_authority`. Về mặt dữ liệu,
  đây là lỗi crosswalk đầu nguồn (2 người khác nhau trong TTL bị map sai thành 1 DILA
  id), không phải lỗi script insert — script chỉ trung thực ghi lại cặp crosswalk sai.
- **LỖI B — 1 cạnh đảo chiều tạo vòng 2 nút**: `id=23159` (`A003868 → A010427`,
  `ttl_only`, vừa insert ở Bước 4) ngược chiều với `id=6913` (`A010427 → A003868`,
  `confirmed_2plus`, 3/4 nguồn Marcus+DILA+TTL) đã tồn tại từ trước. Chiều
  multi-source (`A010427 → A003868`) được giữ; chiều `ttl_only` một nguồn bị xóa vì
  tạo vòng lặp 2 nút trong graph truyền thừa.

**Danh sách 6 id đã xóa khỏi `lineage_edge_consensus`** (verify trước khi xóa:
`consensus_status='ttl_only'` VÀ `migration_marker='T381_TTL_ONLY_INSERT_20261015'`
— cả 6 id đều khớp đúng 2 điều kiện, không có bất thường):

| id | teacher_id | disciple_id | Loại lỗi |
|---|---|---|---|
| 23030 | A000108 | A000108 | self-loop |
| 23145 | A008431 | A008431 | self-loop |
| 23150 | A026988 | A026988 | self-loop |
| 23158 | A010985 | A010985 | self-loop |
| 23305 | A014491 | A014491 | self-loop |
| 23159 | A003868 | A010427 | reversed-duplicate (ngược id=6913) |

**Backup trước khi sửa**:
`docs/sessions/2026-10-15/lineage.db.backup_before_fix_qa_round2_t381` (copy tay
toàn bộ DB, trước khi DELETE).

**Logic skip mới thêm vào `scripts/t381_insert_ttl_only_edges.py` (`build_plan()`)**:
trước khi coi một cặp crosswalk là "to_insert", script giờ kiểm tra thêm 2 điều kiện,
cả 2 đều log rõ ra console khi xảy ra (không âm thầm bỏ qua):
1. **Self-loop**: nếu `teacher_dila == disciple_dila` → SKIP, in rõ id DILA bị trùng.
2. **Reversed-duplicate**: nếu `lineage_edge_consensus` đã có dòng
   `(disciple_dila, teacher_dila, relation_type)` — bất kể `consensus_status` nào
   (không chỉ `ttl_only`) — → SKIP, in rõ id + consensus_status của dòng ngược chiều
   đã tồn tại.

Toàn bộ logic `--dry-run`/`--apply`/idempotent/backup tự động cũ giữ nguyên; `plan`
trả thêm 2 danh sách `skipped_self_loop` và `skipped_reversed_duplicate` để báo cáo.

**Số liệu before/after (xóa 6 dòng, 2026-10-15)**:

| Hạng mục | Trước | Sau |
|---|---|---|
| `lineage_edge_consensus` tổng dòng | 23,417 | 23,411 (delta -6) |
| `consensus_status='ttl_only'` | 399 | 393 (delta -6) |
| Self-loop (`teacher_id = disciple_id`) | 5 | 0 |
| Reversed-duplicate pair toàn bảng (self-join `(teacher,disciple,relation_type)` ↔ `(disciple,teacher,relation_type)`) | 1 | 0 |
| `PRAGMA quick_check` | — | `ok` |

**Idempotent re-run (`--apply` lần nữa trên DB hiện tại, sau khi sửa script)**:
dry-run trước cho thấy script tự phát hiện và SKIP đúng cả 6 cặp lỗi cũ (5 self-loop +
1 reversed-duplicate, log đầy đủ ra console), `to_insert=0` → chạy `--apply` tiếp theo
in "Không có dòng nào cần INSERT ... Không ghi DB." — xác nhận 0 dòng mới được thêm,
không backup lần 2, exit code 0. Verify lại DB sau đó: tổng 23,411 / `ttl_only` 393 /
self-loop 0 — không đổi, khớp số liệu trước khi chạy `--apply` idempotent.

**`python -m py_compile scripts/t381_insert_ttl_only_edges.py`**: không lỗi.

**Files**:
- `scripts/t381_insert_ttl_only_edges.py` (sửa — thêm 2 điều kiện skip trong
  `build_plan()`, cập nhật log ở `do_dry_run()`)
- `docs/sessions/2026-10-15/lineage.db.backup_before_fix_qa_round2_t381` (mới, backup
  trước khi DELETE)
- `data/lineage.db` (sửa — xóa 6 dòng lỗi khỏi `lineage_edge_consensus`)

---

## Final note (2026-10-15)

**T381 done** — 393/399 TTL-only edges insert thành công vào `lineage_edge_consensus`
(`consensus_status='ttl_only'`), 6 dòng lỗi (5 self-loop + 1 reversed-duplicate) đã được
QA round 2 xác nhận xóa đúng. Task file: `tasks/T381-build-dharma-lineage-3sources.md`
(status → `done`).

**→ T415** tạo mới để audit nguồn gốc 1:N (slug→dila_id) trong `vn_person_authority` gây ra
6 lỗi trên, cùng với 229 slug TTL chưa crosswalk được (log ở Bước 1) — chưa sửa, chỉ audit
và trình Admin quyết định. Task file: `tasks/T415-audit-vn-person-authority-crosswalk.md`
(status: `pending`, dispatch: chưa giao).

---

## Attribution

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
