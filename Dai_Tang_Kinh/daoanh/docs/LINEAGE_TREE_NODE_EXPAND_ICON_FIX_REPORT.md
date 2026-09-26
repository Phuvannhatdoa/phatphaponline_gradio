# Audit / Bug Fix Report — LINEAGE_TREE_NODE_EXPAND_ICON_FIX (T146)

> Task: Tab Truyền Thừa → Pháp Mạch. Thêm icon "+"/"−" ở góc 1 giờ trên node có
> child để toggle subtree trực tiếp, tách khỏi hành vi mở panel Chi tiết.

## 1. Vị trí audit (thực tế, không đoán)

| Hạng mục | File / Schema / Endpoint thực tế |
|----------|----------------------------------|
| Data source | `lineage_edge_assertions` (SQLite `data/lineage.db`) — không đổi |
| API endpoint | `GET /daoanh/api/monk/<id>/lineage-tree?up=2&down=2` — không đổi, chỉ đọc |
| Renderer | `daoanh/places.html` — `_renderLineageChain()` (:5666), `_buildFtVisTree().visit()` (:5748), `_renderHierarchyTree()` (:5159) |
| Component (không đổi) | `_renderLineageNetwork()` (mode `expanded` = Phả hệ mở rộng) — chỉ dùng để xác nhận KHÔNG bị ảnh hưởng |

## 2. Root cause (đã xác minh)

- **Lớp gây lỗi:** renderer + interaction state (không phải data/API).
- **Nguyên nhân chính xác:** `_renderHierarchyTree()` chỉ có MỘT `network.on('click', ...)`
  handler dùng chung cho cả node. Với mode `lineage` (Pháp Mạch), mỗi click vào thân
  node vừa gọi `_renderLineageInspector(pid)` (mở panel Chi tiết) **vừa** gọi
  `options.onNodeClick(pid)` — và trong `_renderLineageChain`, `onNodeClick` chính là
  hàm toggle expand/collapse (:5897-5904). Hai hành vi bị hợp nhất vào 1 click, không
  có vùng bấm riêng cho toggle → user không có cách nào mở panel Chi tiết mà không vô
  tình toggle cây, và ngược lại. Không có icon "+/-" nào được vẽ trên node — chỉ có
  chữ gợi ý `▸ N hậu duệ` / `▾ N đệ tử` trong label (không phải hit target độc lập).
  Mode `expanded` (Phả hệ mở rộng) đã truyền `onNodeClick: () => {}` (no-op) nên
  không bị lỗi này.

## 3. Data/API contract trước → sau

Không đổi (đây là bug renderer/interaction thuần UI, không chạm data/API).

| | Trước | Sau |
|--|-------|-----|
| Click thân node (mode lineage) | Mở panel Chi tiết **và** toggle expand/collapse cùng lúc | Chỉ mở panel Chi tiết |
| Click icon +/- góc 1 giờ (mode lineage) | Không tồn tại | Chỉ toggle expand/collapse, không mở panel |
| Mode `expanded` (Phả hệ mở rộng) | Click thân node → chỉ mở panel (onNodeClick no-op) | Không đổi (mode gate `options.mode === 'lineage'`) |

## 4. Files changed

- `daoanh/places.html`:
  - `_buildFtVisTree().visit()` (~:5811) — thêm `_ftHasKids: kids.length > 0` và
    `_ftExpanded: isExp` vào object node (đánh dấu node có child + trạng thái hiện tại,
    chỉ dùng nội bộ, không phải dữ liệu truyền thừa).
  - `_renderHierarchyTree()` afterDrawing callback (~:5282-5309) — thêm 1 pass vẽ badge
    tròn +/- ở góc trên-phải (1 giờ) mỗi node có `_ftHasKids`, chỉ khi
    `options.mode === 'lineage'`; lưu hit-region (`{x,y,r}` theo canvas-space) vào
    `_lineageState._ftIconHit[nodeId]` để dùng cho hit-test khi click.
  - `network.on('click', ...)` (~:5311-5330) — thêm bước kiểm tra: nếu click nằm
    trong hit-region icon (theo `params.pointer.canvas`) của mode `lineage` → chỉ gọi
    `options.onNodeClick(pid)` (toggle), return ngay, không gọi inspector. Ngược lại
    (click thân node) → chỉ gọi `_renderLineageInspector(pid)`, và **không** gọi
    `onNodeClick` nữa khi `mode === 'lineage'` (giữ nguyên gọi cho mode khác — hiện tại
    `expanded` truyền no-op nên hành vi không đổi).

## 5. Migration / import / dry-run / rollback

Không chạm DB/Schema/API — không cần migration/dry-run.

- Backup trước khi sửa: `daoanh/docs/sessions/2026-09-16/places.html.bak-t142-lineage-expand-icon-115022.html`
- Rollback: revert riêng đoạn code trên trong `places.html` (đánh dấu bằng comment
  `T146` tại 2 vị trí, :5282 và :5315), hoặc khôi phục từ file backup nêu trên.
- **Lưu ý:** `places.html` tại thời điểm audit đã có nhiều thay đổi uncommitted khác
  từ các task trước (T144 nexus double-click, T145 bio-vi admin editor, BUG-011
  lineage refetch) — `git diff` xác nhận thay đổi của task này (2 khối `T146`) tách
  biệt, không đè lên các thay đổi đó. Không chạy `git add/commit` (theo quy tắc
  CLAUDE.md — repo có git-index anomaly, chỉ commit khi user yêu cầu rõ).

## 6. Test cases & kết quả

Test qua local server (`local_gateway.py:8080`, `app.py:5000` đang chạy) — dùng
`places.html?select=A000475` (Đại Huệ Tông Cảo, 143 đệ tử trực tiếp trong DB) để có
subtree đủ lớn cho test. Do vis-network dùng Hammer.js cho gesture, click pixel giả
lập qua công cụ browser automation không kích hoạt được sự kiện `click` nội bộ của
vis-network (đã xác minh: cả native `MouseEvent` dispatch và click pixel thật đều
không tới được handler — đây là giới hạn của môi trường automation, không phải lỗi
code) → verify bằng cách gọi trực tiếp `_lineageNetwork.emit('click', {nodes, pointer})`
— đúng interface mà Hammer.js nội bộ dùng để phát sự kiện `click` cho các listener
đăng ký qua `network.on('click', ...)`, nên đây là test chính xác cho toàn bộ logic
handler đã sửa. Xác nhận thêm bằng zoom canvas lớn + `computer.screenshot` cho thấy
badge tròn +/- render đúng vị trí, đúng màu theo trạng thái.

| Case | Input | Expected | Actual | PASS/FAIL |
|------|-------|----------|--------|-----------|
| Node có child hiện icon | node A000475 (143 đệ tử, đã fetch subtree) | icon +/- xuất hiện góc 1 giờ | `st._ftIconHit` có 9/9 node có `_ftHasKids` trong subtree hiện render; screenshot xác nhận badge đỏ "−" đúng vị trí góc trên-phải node trung tâm | ✅ |
| Click icon → toggle, không mở panel | icon node A001561 (đang expanded) | `_ftExpanded` mất id đó; `selectedNode`/inspector giữ nguyên | `expandedHas: true→false`, `selectedNode` không đổi (`A000475`) | ✅ |
| Click icon 2 lần → toggle qua lại | icon node A001561 | expand→collapse→expand | `false→true→false` qua 2 lần click liên tiếp, `selectedNode` không đổi trong suốt | ✅ |
| Click thân node → mở panel, không toggle | thân node A007385 (đang expanded) | `selectedNode`→A007385, inspector hiện chi tiết; `_ftExpanded` giữ nguyên | `selectedNode: A000475→A007385`, inspector "Dục Vương Đức Quang" đúng; `expandedHas` vẫn `true` (không đổi) | ✅ |
| Node không có child → không icon | node lá bất kỳ (VD `A001411`) trong `st.nodes` nhưng không nằm trong `st._ftIconHit` | không có icon | Xác nhận: 161 node trong subtree, chỉ 9 node có `_ftHasKids`/icon (đúng số node có child trong depth hiện render) | ✅ |
| Mode `expanded` (Phả hệ mở rộng) không bị ảnh hưởng | click node với toạ độ trùng icon-hit cũ (stale) trong mode `expanded` | click vẫn mở panel bình thường (hành vi cũ, không toggle vì onNodeClick vốn no-op) | `selectedNode` đổi đúng sang node được click, inspector hiện đúng chi tiết — mode-gate `options.mode==='lineage'` chặn interference | ✅ (fallback/regression case) |
| JS syntax | toàn bộ `<script>` không-src trong `places.html` | 0 lỗi parse | `@babel/parser` — 1 block, 506370 chars, 0 lỗi | ✅ |
| Test suite | `npm run test` (node tests/run-tests.js) | PASS | `✅ Tests passed` | ✅ |
| Console | toàn bộ phiên test trên | không có `[error]` | `read_console_messages(onlyErrors:true)` → rỗng trong suốt test | ✅ |

## 7. Limitation / data gap còn lại

- Không test được bằng click pixel thật qua công cụ browser automation (giới hạn
  Hammer.js/canvas gesture của vis-network trong môi trường CDP-driven automation —
  đã xác nhận cả click thân node cũ, KHÔNG liên quan thay đổi của task này, cũng
  không kích hoạt được qua automation). Đã bù bằng test qua `network.emit('click', ...)`
  — chính xác interface nội bộ mà Hammer.js dùng để phát event tới handler đã đăng ký,
  nên bao phủ đúng toàn bộ logic đã sửa. Khuyến nghị: admin xác nhận thủ công 1 lần
  bằng chuột thật trên trình duyệt desktop bình thường (không qua automation) trước
  khi đánh dấu DONE, theo quy tắc `feedback_debug_done_workflow.md`.
- Test mobile (theo yêu cầu "Kiểm tra desktop và mobile") chỉ verify được ở mức
  logic: `params.pointer.canvas` do vis-network cung cấp giống nhau cho cả mouse và
  touch/tap (cùng 1 code path `network.on('click', ...)`), nên về mặt code không cần
  nhánh riêng cho mobile. Chưa test được trên thiết bị cảm ứng thật.
- Phát hiện phụ (không thuộc scope task, không sửa): trong lúc test phát hiện
  `centerLineageOn(pid)` (:5023) sẽ throw nếu gọi khi `_lineageState` chưa được khởi
  tạo bởi `loadLineageTree()` trước đó (`const st = _lineageState; if (!st) return;`
  — an toàn, có guard, không phải bug) — chỉ là lưu ý khi test thủ công cần gọi đúng
  thứ tự `loadLineageTree` trước `centerLineageOn`.
