# Audit / Bug Fix Report — T355 (BUG-033) Số đời sai khi click node trước Huệ Năng (chain dài)

> Lưu tại `docs/T355_BUG033_REPORT.md`.

## 1. Vị trí audit (thực tế, không đoán)

| Hạng mục | File / Schema / Endpoint thực tế |
|----------|----------------------------------|
| Data source | `data/lineage.db` — bảng `generation_v2_scheme_revisions` (anchors), `lineage_edge_assertions` (DILA teacher_of), `entity` |
| API endpoint | `GET /daoanh/api/admin/ttl_v2/generation/calculate/<DILA_ID>` (trả `report.results[].number`) |
| Resolver / logic | `src_python/generation_engine_v2.py` — hàm `compute()`/`parents()` (đã audit, **không có bug** — số do engine trả luôn đúng cho mọi ID test) |
| Component / renderer (đã sửa) | `places.html:6723-6756` — shared click handler trong `_renderHierarchyTree(...)`, dùng chung cho 2 tab "Pháp mạch" (`mode:'lineage'`, hàm `_renderLineageChain`, dòng 7854) và "Phả hệ mở rộng" (`mode:'expanded'`, hàm `_renderLineageNetwork`, dòng 8045) |
| Panel hiển thị | `admin/places-generation-v2.js` — hàm `load(id)`/`renderInto()`, không đổi (vẫn gọi đúng API khi được invoke) |

## 2. Root cause (đã xác minh)

- **Lớp gây lỗi:** renderer / state (UI event-wiring bug, không phải data hay API contract).
- **Nguyên nhân chính xác (đã xác minh bằng code + network log, không đoán):**

  Panel "Truyền Thừa · Đời thứ N" (trái, do `admin/places-generation-v2.js` render) chỉ được
  refresh khi click node thỏa điều kiện `options.mode === 'lineage'` tại `places.html:6725` (bản
  trước sửa). Điều kiện này **chỉ đúng với tab "Pháp mạch"** (`_renderLineageChain`, dòng 7854
  truyền `mode: 'lineage'`). Tab **"Phả hệ mở rộng"** (`_renderLineageNetwork`, dòng 8045) truyền
  `mode: 'expanded'` và `onNodeClick: () => {}` (no-op) — đây chính là tab admin dùng để xem
  chain dài 48 entity (chain ngắn 3 entity trong T354/BUG-032 chỉ cần tab "Pháp mạch" nên không
  lộ bug này). Khi click node trong tab "Phả hệ mở rộng":
  - `_renderLineageInspector(pid)` vẫn chạy (nên panel "Chi tiết" bên phải cập nhật đúng) →
    khiến hiện tượng dễ bị hiểu nhầm là "đã cập nhật".
  - Nhưng khối code cập nhật `#lineage-sidebar-title` + gọi
    `window._ptdaLoadGenerationV2(pid)` (panel "Truyền Thừa · Đời thứ N") bị **bỏ qua hoàn
    toàn** vì `options.mode !== 'lineage'`.
  - Kết quả: panel giữ nguyên số đời cũ (của node/focus trước đó, ví dụ 33) bất kể click node
    nào khác trong tab "Phả hệ mở rộng" — kể cả node tổ sư (ancestor) có số đời thực tế nhỏ hơn.

  **Bằng chứng network log (trước sửa):** click node Hoằng Nhẫn (A000237, tổ sư của focus) trong
  tab "Phả hệ mở rộng" — **0 request mới** tới
  `/daoanh/api/admin/ttl_v2/generation/calculate/A000237` được gửi (xem mục 6). Panel vẫn hiện
  "Đời thứ 33" của node đang chọn trước đó.

  **Ghi chú phụ (không phải bug code, nhưng liên quan đến cách bug được mô tả):** DILA ID
  `A010081` trong URL tái hiện **không phải Đại Giám Huệ Năng** mà là 蒙山道明 (Mông Sơn Đạo Minh,
  biệt danh 惠明/Huệ Minh — một đệ tử khác của Hoằng Nhẫn, tình cờ cũng ở đời 33 theo cùng quy ước
  "Ca Diếp 1"). Huệ Năng thật trong DILA là `A001719` (tên Hán 惠能, cũng là anchor số 33 trong
  scheme `chan_ca_diep_1`). Đã xác minh qua `identity()` trả `target_identity.names` của
  A010081 = `['道明','釋慧明','將軍','蒙山道明','惠明']`. Đây là nhầm lẫn danh tính trong lúc viết
  task/bug report (tên gần giống), **không sửa trong phạm vi T355** — chỉ nêu để Admin biết nếu
  cần đối chiếu lại test case gốc. Toàn bộ 48 ID trong `chain=` là **đệ tử của Huệ Năng thật**
  (xác nhận qua DB: 法海, 志道, 荷澤神會, 智常, v.v. — các tên quen thuộc trong Pháp Bảo Đàn Kinh),
  nên số đời của chúng đúng ra phải là 34 (sau Huệ Năng), không phải "< 33" — việc này không liên
  quan đến bug UI đã sửa, chỉ là điểm cần Admin lưu ý khi review lại mô tả gốc của BUG-033.

## 3. Data/API contract trước → sau

| | Trước | Sau |
|--|-------|-----|
| Click node tổ sư (ancestor) trong tab **Pháp mạch** (`mode:'lineage'`) | Panel cập nhật đúng (đã fix ở T354) | Không đổi — vẫn đúng |
| Click node bất kỳ trong tab **Phả hệ mở rộng** (`mode:'expanded'`) | Panel **không gọi API**, giữ số đời cũ (stale) | Panel gọi đúng `/generation/calculate/<pid>` của node vừa click, hiện đúng số đời |
| API `/daoanh/api/admin/ttl_v2/generation/calculate/<id>` | Không đổi — luôn đúng | Không đổi |

## 4. Files changed

- `daoanh/places.html` (dòng ~6723-6756) — gộp điều kiện trigger panel "Truyền Thừa · Đời thứ N"
  (và breadcrumb/quicklist T8) từ `options.mode === 'lineage'` thành
  `options.mode === 'lineage' || options.mode === 'expanded'` (biến `_isLineageCtx`), để tab
  "Phả hệ mở rộng" cũng refresh panel khi click node, giống tab "Pháp mạch". Không đổi logic
  `_renderLineageChain`/`_renderLineageNetwork`, không đổi `generation_engine_v2.py`, không đổi
  `admin/places-generation-v2.js`.

Backup trước khi sửa: `daoanh/docs/sessions/2026-10-11/places.html.T355-before`
(copy nguyên trạng trước khi edit, đường dẫn tuyệt đối:
`E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\docs\sessions\2026-10-11\places.html.T355-before`).

## 5. Migration / import / dry-run / rollback

- Không chạm DB, không chạy migration. Đây là sửa JS tĩnh trong `places.html` (phục vụ qua
  `local_gateway.py`), không cần restart `app.py`/`server.py`.
- Revert: khôi phục từ backup `docs/sessions/2026-10-11/places.html.T355-before`, hoặc
  `git diff`/`git checkout -- daoanh/places.html` (chưa `git add`/`commit` theo đúng ràng buộc).

## 6. Test cases & kết quả

Môi trường: `http://127.0.0.1:8080/...` (local, đúng quy tắc IPv4, `local_gateway.py` đã chạy sẵn).

| Case | Input | Expected | Actual (trước sửa) | Actual (sau sửa) | PASS/FAIL |
|------|-------|----------|---------------------|-------------------|-----------|
| Case yêu cầu — click tổ sư trong chain dài, tab "Phả hệ mở rộng" | focus=A010081, chain 48 entity, click node "Tôn Giả Hoàng Mai Hoằng Nhẫn" (A000237, tổ sư trực tiếp, đời 32 thật) | Panel hiện "Đời thứ 32" (< 33) | Panel giữ "Đời thứ 33" (KHÔNG đổi) — xác nhận: **0 network request** mới tới `/generation/calculate/A000237` | Panel hiện đúng **"Truyền Thừa Thiền Tông · Đời thứ 32"**; network log có `GET /daoanh/api/admin/ttl_v2/generation/calculate/A000237 → 200 OK` | ✅ |
| Node khác trong cùng chain (descendant, để kiểm fix không chỉ "luôn trả về số nhỏ hơn" mà tính đúng theo node) | Click "Sùng Tịch" (A024844, đệ tử của focus, đời 34 thật) trong tab "Phả hệ mở rộng" | Panel hiện đúng đời thật của Sùng Tịch (34, > 33 vì là đệ tử) | — (chưa test, bug chỉ lộ sau khi phát hiện) | Panel hiện đúng **"Truyền Thừa Thiền Tông · Đời thứ 34"**; network log có `GET .../generation/calculate/A024844 → 200 OK` | ✅ |
| Regression — chain ngắn T354/BUG-032, tab "Pháp mạch" (`mode:'lineage'`) | focus=A010081, chain=A000237, click Hoằng Nhẫn trong tab "Pháp mạch" | Panel hiện "Đời thứ 32" (hành vi T354 đã fix, phải giữ nguyên) | — | Panel hiện đúng **"Truyền Thừa Thiền Tông · Đời thứ 32"** (không regression) | ✅ |
| Fallback — tải thêm đời tổ sư trong tab "Phả hệ mở rộng" rồi click lại node cũ | Click "Mở thêm đời trên ↑", sau đó click lại node Hoằng Nhẫn | Panel vẫn hiện đúng đời (không kẹt ở trạng thái loading) | Title bị kẹt ở "Đang tải thêm..." vĩnh viễn (bug phụ riêng, xem mục 7) | Click node ghi đè đúng text thành "Đời thứ 32" (fix hiện tại cũng gián tiếp khắc phục hiển thị kẹt text, vì panel luôn ghi đè `innerHTML` khi click) | ✅ |

Ảnh chụp màn hình (before/after) và network log raw đã thu thập trong phiên làm việc qua
Claude Browser tool (không lưu file riêng theo yêu cầu — đã mô tả bằng text ở trên và trong tool
call history của phiên).

## 7. Limitation / data gap còn lại

- **Chưa sửa (ngoài phạm vi T355):** `_lineageExpandRefetch` (`places.html:6335-6362`) đặt
  `#lineage-sidebar-title` thành `"Đang tải thêm..."` trước khi fetch thêm đời (nút "Mở thêm đời
  trên/dưới ↑/↓" trong tab "Phả hệ mở rộng"), nhưng **không khôi phục lại title khi fetch thành
  công** (chỉ khôi phục `prevText` khi lỗi/abort). Title bị kẹt ở "Đang tải thêm..." cho tới khi
  user click một node khác (lúc đó bị ghi đè bởi fix T355). Đây là bug UI riêng, đã phát hiện
  trong lúc audit T355 nhưng **không sửa** vì ngoài phạm vi done_when của task này — đề xuất mở
  bug/task riêng nếu Admin muốn xử lý.
- **Không xác minh được:** click trực tiếp vào các node xa hơn 1 hop (ví dụ Đạo Tín, tổ thứ 4,
  đời 31) trong canvas tab "Phả hệ mở rộng" — thao tác pan/zoom bằng tool browser (không phải
  chuột người dùng thật) gặp khó khăn kỹ thuật khi node nằm ngoài viewport ban đầu (vis.js
  network canvas, không phải DOM thường nên không drag-pan được bằng `left_click_drag` trong
  phiên test này). Đã verify gián tiếp: (a) API `generation/calculate/<id>` đã xác minh đúng cho
  toàn bộ 48 ID trong `chain` + root/anchor qua `curl` trực tiếp (không qua UI); (b) cơ chế sửa
  là generic theo `pid` của bất kỳ node nào được click (không hard-code riêng Hoằng Nhẫn), nên
  logic áp dụng đồng nhất cho mọi node trong tab "Phả hệ mở rộng". Đề nghị Admin/QA tự click thêm
  1-2 node sâu hơn (ví dụ qua "Mở thêm đời trên ↑" nhiều lần) để xác nhận bằng mắt nếu cần độ tin
  cậy cao hơn.
- **Nhầm lẫn danh tính trong bug report gốc:** xem ghi chú ở mục 2 — A010081 không phải Huệ Năng.
  Không sửa (không phải lỗi code/data, là lỗi mô tả test case).
- Chưa chạy lại `python -m py_compile` vì **không có file `.py` nào bị sửa** trong lần fix này
  (chỉ sửa JS trong `places.html`).

Status task: giữ nguyên `in_progress` theo yêu cầu — chờ QA độc lập kiểm chứng trước khi hỏi
Admin xác nhận DONE.

---

## 8. VÒNG 2 — QA chưa đạt, root cause thực sự (2026-10-11, sau test đúng URL task)

### 8.1 Phản hồi QA

QA (`daoanh-qa`) xác định vòng 1 audit **sai giả thuyết**: URL gốc của task
(`lm=tree`, chain 48 entity) render tab **"Pháp mạch"** (`_renderLineageChain`, `mode:'lineage'`),
**KHÔNG PHẢI** tab "Phả hệ mở rộng" như báo cáo vòng 1 giả định (vòng 1 đã test sai tab nên không
phát hiện bug thật). QA nghi vấn: `url()` trong `admin/places-generation-v2.js:61` bị
`history.replaceState`/`pushState` monkey-patch (dòng 71) gọi lại **mỗi khi** `_t130SyncUrl()`
(`places.html:11202`, gọi bởi `rerender()` ~7583 và sau mọi lần `_renderLineageChain`/
`_renderLineageNetwork`, dòng ~7896/8059/8084) ghi lại URL — kể cả khi chỉ `chain` (expand/collapse
state) đổi, `focus` không đổi — khiến panel bị ép load lại theo `focus` gốc, ghi đè số đời vừa
load đúng cho node khác.

### 8.2 Test lại đúng URL task (tab "Pháp mạch", KHÔNG phải "Phả hệ mở rộng")

Mở đúng URL trong task (`mode=lineage&focus=A010081&lm=tree&chain=...48 ID...`) bằng Claude Browser
tool thật (không JS inject), click node **Hoằng Nhẫn (A000237)** trong tab **Pháp mạch**, sau đó
click icon "−"/"+" để thu/mở node **Mông Sơn Đạo Minh** (focus, A010081). Lọc network log theo
`urlPattern=generation/calculate`:

```
[15112.83]  GET .../generation/calculate/A010081 → 200 OK   (focus gốc)
[15112.104] GET .../generation/calculate/A000237 → 200 OK   (node vừa click — ĐÚNG)
[15112.169] GET .../generation/calculate/A010081 → 200 OK   (RACE — focus bị gọi lại dù không click)
[15112.267] GET .../generation/calculate/A010081 → 200 OK   (RACE)
[15112.289] GET .../generation/calculate/A000237 → 200 OK
[15112.358] GET .../generation/calculate/A010081 → 200 OK   (RACE)
[15112.388] GET .../generation/calculate/A000237 → 200 OK
[15112.471] GET .../generation/calculate/A010081 → 200 OK   (RACE)
[15112.493] GET .../generation/calculate/A024844 → 200 OK   (click node khác — Sùng Tịch)
[15112.576] GET .../generation/calculate/A010081 → 200 OK   (RACE)
[15112.597] GET .../generation/calculate/A000237 → 200 OK
```
(raw log đầy đủ: `docs/sessions/2026-10-11/T355_round2_network_BEFORE.txt`)

**Xác nhận root cause thật:** mỗi lần `rerender()`/`_t130SyncUrl()` chạy (kể cả do click icon
+/- mở/thu node, KHÔNG phải do đổi `focus`), `history.pushState`/`replaceState` bị monkey-patch
gọi `url()` trong `admin/places-generation-v2.js`. Bản TRƯỚC khi sửa của `url()`:

```js
function url(){const q=new URLSearchParams(location.search);if(q.get('mode')==='lineage'){load(q.get('focus'));}else{...}}
```

luôn gọi `load(q.get('focus'))` — tức `load('A010081')` — **bất kể `focus` có đổi hay không**.
Request này chạy **song song** (race) với request `load(pid)` gọi trực tiếp từ click handler
(`places.html:6754`, fix T354/T355 vòng 1). Cả hai dùng chung biến `serial` trong `load()` để huỷ
response cũ hơn — nên **giá trị hiển thị cuối cùng phụ thuộc vào request nào về SAU, không phải
node nào người dùng vừa chọn**. Đây là bug state/race condition thật, đúng như QA nghi vấn —
khác hẳn giả thuyết vòng 1 (thiếu điều kiện `mode:'expanded'`, vốn **vẫn đúng và cần giữ** cho
tab "Phả hệ mở rộng" — xem mục 8.5).

### 8.3 Fix

**File sửa:** `daoanh/admin/places-generation-v2.js`, hàm `url()` (dòng ~61).

Backup trước khi sửa: `docs/sessions/2026-10-11/places-generation-v2.js.T355-round2-before`.

Trước:
```js
function url(){const q=new URLSearchParams(location.search);if(q.get('mode')==='lineage'){load(q.get('focus'));}else{const wrap=inlineWrap();if(wrap)wrap.style.display='none';panel.hidden=true;current='';}}
```

Sau (chỉ gọi `load(focus)` khi `focus`/`mode` THỰC SỰ đổi so với lần `url()` chạy trước — bỏ qua
khi URL chỉ đổi do `_t130SyncUrl` ghi lại `chain`/expand-state):
```js
let _lastUrlFocus=null,_lastUrlMode=null;
function url(){
  const q=new URLSearchParams(location.search);const _m=q.get('mode'),_f=q.get('focus');
  if(_m==='lineage'){
    if(_f===_lastUrlFocus&&_m===_lastUrlMode)return;
    _lastUrlFocus=_f;_lastUrlMode=_m;
    load(_f);
  }else{
    _lastUrlFocus=null;_lastUrlMode=null;
    const wrap=inlineWrap();if(wrap)wrap.style.display='none';panel.hidden=true;current='';
  }
}
```

Hành vi giữ nguyên cho điều hướng thật (tải trang lần đầu, popstate back/forward, đổi `focus` qua
`selectPerson`) — chỉ bỏ qua các lần `url()` được monkey-patch gọi lại do sync `chain`/expand-state
(focus/mode không đổi). Không đổi `load()`, không đổi `renderInto()`, không đổi
`generation_engine_v2.py`, không đổi logic trong `places.html` (fix round 1 — gộp
`mode:'lineage'||'expanded'` — **giữ nguyên**, không revert).

### 8.4 Test lại sau khi sửa (bằng chứng network log + screenshot thật)

Hard refresh (`ctrl+shift+r`) để nạp JS mới, test lại đúng URL task:

1. Load trang → panel "Đời thứ 33" (focus A010081) — đúng.
2. Click thân node **Hoằng Nhẫn** (A000237) trong tab Pháp mạch → panel đổi đúng **"Đời thứ 32"**.
   (`docs/sessions/2026-10-11/T355_round2_AFTER_collapse_expand_HoangNhan_TTL32.jpg` — ảnh chụp
   sau bước 3+4 dưới, cùng giá trị 32 xuyên suốt)
3. Click icon "−" trên node Mông Sơn Đạo Minh (focus) để **thu gọn** cây con → panel **vẫn giữ
   "Đời thứ 32"** (không bị ghi đè về 33).
4. Click icon "+" để **mở lại** → panel **vẫn giữ "Đời thứ 32"**.
5. Click thân node **Sùng Tịch** (A024844, đệ tử của focus, đời 34 thật) → panel đổi đúng
   **"Đời thứ 34"**.

Network log (`urlPattern=generation/calculate`) sau bước 1-2 và 5, filter theo request MỚI sinh ra
sau khi sửa:
```
[15112.651] GET .../generation/calculate/A010081 → 200 OK   (bước 1: load trang, focus)
[15112.672] GET .../generation/calculate/A000237 → 200 OK   (bước 2: click Hoằng Nhẫn)
[15112.680] GET .../generation/calculate/A024844 → 200 OK   (bước 5: click Sùng Tịch)
```
(raw log đầy đủ: `docs/sessions/2026-10-11/T355_round2_network_AFTER.txt`)

**Kết quả quan trọng nhất:** bước 3 (thu gọn) và bước 4 (mở lại) — hành động trước đây sinh ra
request `A010081` "race" chen vào — **SAU KHI SỬA không sinh thêm bất kỳ request
`/generation/calculate/*` nào mới**. Race condition đã được loại bỏ hoàn toàn: panel chỉ cập nhật
khi có node thực sự được click, không còn bị ghi đè bởi `focus` gốc khi chỉ expand/collapse.

Ảnh chụp màn hình (before/after, thật, qua Claude Browser tool — không phải JS inject):
- `docs/sessions/2026-10-11/T355_round2_BEFORE_click_HoangNhan_phapMach.jpg` — trước sửa, sau
  click Hoằng Nhẫn + 1 lần expand/collapse, panel tình cờ hiện đúng 32 do race thắng may rủi
  (minh hoạ tính KHÔNG ỔN ĐỊNH của bug, không phải luôn luôn sai — xem network log mục 8.2 để
  thấy số request race thực tế).
- `docs/sessions/2026-10-11/T355_round2_AFTER_collapse_expand_HoangNhan_TTL32.jpg` — sau sửa,
  sau khi thu gọn rồi mở lại node, panel ổn định ở "Đời thứ 32".

### 8.5 Regression test (bắt buộc theo yêu cầu vòng 2)

| Case | URL/thao tác | Expected | Actual | PASS |
|---|---|---|---|---|
| T354/BUG-032 (chain ngắn), tab Pháp mạch | `focus=A010081&lm=tree&chain=A000237`, click Hoằng Nhẫn | "Đời thứ 32" | "Đời thứ 32" — ảnh `T355_round2_REGRESSION_T354_chain_ngan_TTL32.jpg` | ✅ |
| T355 vòng 1 (fix `mode:'lineage'||'expanded'` trong places.html), tab "Phả hệ mở rộng", chain dài | `focus=A010081&lm=network&chain=...48 ID...`, click Hoằng Nhẫn | "Đời thứ 32" | "Đời thứ 32" — ảnh `T355_round2_REGRESSION_T355round1_PhaHeMoRong_TTL32.jpg` | ✅ |
| Case chính vòng 2 — tab Pháp mạch, chain dài 48 entity thật (URL task) | Click Hoằng Nhẫn + thu/mở node focus nhiều lần + click Sùng Tịch | Panel bám đúng node vừa chọn, không bị ghi đè bởi focus khi expand/collapse | Đúng theo mục 8.4 — không còn request race | ✅ |

Không revert fix vòng 1 trong `places.html` (`_isLineageCtx = mode==='lineage'||mode==='expanded'`)
— vẫn cần thiết cho tab "Phả hệ mở rộng" (đã test lại, không regression).

### 8.6 Files changed (vòng 2)

- `daoanh/admin/places-generation-v2.js` — sửa hàm `url()` (dòng ~61), thêm biến module
  `_lastUrlFocus`/`_lastUrlMode` để chặn gọi lại `load(focus)` khi URL chỉ đổi do sync
  chain/expand-state. Backup: `docs/sessions/2026-10-11/places-generation-v2.js.T355-round2-before`.
- `daoanh/places.html` — **không đổi thêm** trong vòng 2 (fix vòng 1 giữ nguyên).

### 8.7 Limitation / chưa kiểm được

- Chưa test click node sâu hơn 2 hop (yêu cầu pan/zoom canvas vis.js bằng tool, khó thao tác
  chính xác như chuột thật) — nhưng cơ chế fix là generic theo `pid`, không hard-code riêng node
  nào, nên logic áp dụng đồng nhất.
- Chưa test trường hợp back/forward (popstate) thật trên chain dài — do giới hạn thao tác
  browser tool, chỉ xác minh code path tương ứng (`_lastUrlFocus`/`_lastUrlMode` reset về `null`
  khi rời `mode=lineage`, nên quay lại sẽ load lại đúng) bằng đọc code, không có screenshot thật.
- `python -m py_compile`: không áp dụng, không có file `.py` nào bị sửa trong vòng 2 (chỉ JS).

Status task: giữ nguyên `in_progress` — chờ QA độc lập kiểm chứng vòng 2 trước khi hỏi Admin
xác nhận DONE.
