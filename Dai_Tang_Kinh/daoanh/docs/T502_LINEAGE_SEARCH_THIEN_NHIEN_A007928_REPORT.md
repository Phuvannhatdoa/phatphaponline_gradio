# Audit / Bug Fix Report — T502 Places Pháp hệ: search "Thiên Nhiên" (focus=A007928) không ra tree/generation

> Route/case: `http://127.0.0.1:8080/daoanh/places?mode=lineage&focus=A007928&lm=tree`
> Ngày audit: 2026-10-30. **Audit + fix + verify — CHƯA đánh DONE**, chờ Admin xác nhận.

## 1. Vị trí audit (thực tế, không đoán)

| Hạng mục | File / Schema / Endpoint thực tế |
|----------|----------------------------------|
| Data source | `data/lineage.db`: `lineage_edge_consensus`, `lineage_edge_assertions`, `v_tree_dila`, `v_tree_marcus`, `v_tree_ttl` |
| API endpoint | `GET /daoanh/api/monk/<dila_id>/lineage-tree` (`routes_lineage.py:601`), `GET /daoanh/api/admin/search_all?q=` (quicklist search), `GET /daoanh/api/admin/ttl_v2/generation/calculate/<id>` (generation) |
| Resolver / logic | `routes_lineage.py:601-900` (`api_monk_lineage_tree`), `core.py` (`_t426_neighbors_view`, `calculate_edge_color_and_divergence`) |
| Component / renderer | `places.html` — `loadLineageTree()` (dòng 6274), nút chọn nguồn cây `#lineage-tree-source` (dòng 711-716, wiring ~8799-8835), quicklist search `#lineage-search` (dòng 8851-8902), empty-state `#lineage-empty` (dòng 757), generation panel `admin/places-generation-v2.js` |
| Schema contract | API `lineage-tree` nhận `up/down/include_single/trees/overlay`; không đổi |

## 2. Root cause (đã xác minh)

Phát hiện **2 nguyên nhân khác lớp**, cả hai đã kiểm chứng trực tiếp bằng DB + browser thật:

### (A) Trường hợp literal được report — KHÔNG phải bug, là dữ liệu thật

DILA ID `A007928` ("天然" / Thiên Nhiên, nhà Minh) là **orphan thật trong DB** — 0 cạnh pháp hệ
ở MỌI nguồn, không riêng gì "Marcus":

```sql
SELECT * FROM lineage_edge_consensus WHERE teacher_id='A007928' OR disciple_id='A007928';  -- 0 rows
SELECT * FROM lineage_edge_assertions WHERE subject_person_id='A007928' OR object_person_id='A007928'; -- 0 rows
SELECT * FROM v_tree_dila   WHERE subject_person_id='A007928' OR object_person_id='A007928'; -- 0 rows
SELECT * FROM v_tree_marcus WHERE subject_person_id='A007928' OR object_person_id='A007928'; -- 0 rows
SELECT * FROM v_tree_ttl    WHERE subject_person_id='A007928' OR object_person_id='A007928'; -- 0 rows
```

API `/daoanh/api/monk/A007928/lineage-tree` trả `"edges":[]`, `"has_more_up":false,"has_more_down":false` —
đúng theo dữ liệu, không hard-code. API generation (`ttl_v2/generation/calculate/A007928`) trả cả 3 scheme
với `"status":"unreachable"`, `"issues":[{"type":"orphan_outside_root"}]` — tức DAG có tồn tại người này
nhưng **không có cạnh nào nối tới mốc đếm đời**, khác với "không tìm thấy người".

UI hiện đang hiển thị ĐÚNG, phân biệt rõ 2 case theo đúng yêu cầu task:
- Canvas cây: ẩn (không vẽ cây giả), thay bằng empty-state.
- Panel "Pháp mạch · theo từng hệ truyền thừa" (trái): **"Chưa xác định số đời: 8 tông chưa nối tới mốc,
  1 tông thiếu mốc."** — câu honest, build động từ `results[].status` (xem `admin/places-generation-v2.js:20-39`,
  đặc biệt dòng 22 comment "BUG-027" đã xử lý case này từ trước), **không phải số giả**.
- Quicklist "Tìm trong pháp hệ": gõ "Thiên Nhiên" → gọi `GET /api/admin/search_all?q=Thiên Nhiên` → trả về
  16 tăng nhân trùng tên "Thiên Nhiên" (gồm cả A007928 đang xem lẫn Đan Hà Thiên Nhiên A009460 nổi tiếng) —
  **search hoạt động đúng**, đây là tính năng đã fix trước đó (comment "BUG-041", task `T417`, 2026-10-19).

Kiểm chứng end-to-end: chọn kết quả khác cùng tên — **A009460 (丹霞天然 / Đan Hà Thiên Nhiên, nhà Đường)**
— cây pháp hệ render đầy đủ (node 希遷, cạnh, badge nguồn) + header "7 đời từ trục tổ sư" + generation
"TTL 36" hiển thị đúng. Pipeline search→select→tree→generation **chạy đúng khi dữ liệu tồn tại**.

→ Kết luận: route/case cụ thể trong task **không phải bug code**. Dữ liệu A007928 genuinely không có
pháp hệ; hệ thống đã honest-report đúng quy tắc "phân biệt rõ 'không tìm thấy' vs 'tìm thấy nhưng thiếu
dữ liệu generation'".

### (B) Bug thật tìm thấy trong lúc audit — **đã sửa**: nút chọn nguồn cây không hoạt động

**Lớp gây lỗi: `state` (JS scope).**

`places.html` có 4 nút chọn nguồn cây "Cây DILA / Cây Marcus / Cây TTL / Chồng cây" (`#lineage-tree-source`,
dòng 711-716). Nút "Cây DILA" được style **active sẵn trong HTML tĩnh** (dòng 712, nền xanh `--edge-dila`,
bold) ngay từ khi tải trang.

Biến điều khiển query thật, `_currentTreeSource`, được khai báo bằng `let` **cục bộ bên trong 1 IIFE khác**
(wiring nút bấm, dòng cũ ~8801) — trong khi `loadLineageTree()` (dòng 6274), hàm `centerLineageOn()`
(dòng ~6566) và hàm mở rộng node (dòng ~6620) là 3 hàm top-level **KHÔNG cùng scope lexical** với IIFE đó.
Cả 3 nơi đọc biến này qua `typeof _currentTreeSource !== 'undefined'` — do khác scope, `typeof` luôn trả
`'undefined'`, nhánh gắn `&trees=`/`&overlay=` **không bao giờ chạy**, bất kể người dùng bấm nút nào.

**Bằng chứng trước khi sửa** (network log thật, route `focus=A007928&lm=tree`):

```
GET /daoanh/api/monk/A007928/lineage-tree?up=2&down=2&include_single=1          (tải trang, nút "Cây DILA" hiện active)
GET /daoanh/api/monk/A007928/lineage-tree?up=2&down=2&include_single=1          (sau khi bấm "Cây Marcus" — KHÔNG đổi!)
```
→ Dù bấm "Cây Marcus"/"Cây TTL"/"Chồng cây", query gửi lên server **y hệt nhau**, luôn là consensus mặc
định (`T158`, ≥2/4 nguồn đồng thuận), không bao giờ là view nguồn đơn (`T425` VIEW) như UI hiển thị.

Đã kiểm DB: với sample hiện có, `v_tree_dila` không có record nào mà người đó lại 0 record trong
`lineage_edge_consensus` (consensus table đã include cả single-source vì request luôn gửi `include_single=1`),
nên với dữ liệu hiện tại bug này **chưa gây mất cạnh thực tế** cho các case đã kiểm — nhưng đây vẫn là lỗi
state thật: nút UI nói dối người dùng đang xem nguồn nào, và 3/4 nút hoàn toàn chết (click vô tác dụng).

## 3. Data/API contract trước → sau

| | Trước | Sau |
|--|-------|-----|
| Query khi bấm "Cây Marcus"/"Cây TTL"/"Chồng cây" | luôn `up=2&down=2&include_single=1` (bỏ qua lựa chọn) | thêm đúng `&trees=marcus` / `&trees=ttl` / `&overlay=1` |
| Mặc định khi tải trang | JS state thật = `'consensus'`, nhưng UI hiển thị "Cây DILA" active (lệch) | JS state thật = `'dila'`, khớp đúng nút đang hiển thị active |
| Biến state | `let _currentTreeSource` cục bộ trong 1 IIFE, 3 nơi đọc khác scope luôn thấy `undefined` | `window._currentTreeSource`, dùng chung 1 nguồn sự thật ở cả 4 vị trí đọc/ghi |

## 4. Files changed

- `daoanh/places.html`
  - Dòng ~6298-6313 (`loadLineageTree`): `_currentTreeSource` → `window._currentTreeSource`.
  - Dòng ~6568-6582 (`centerLineageOn`): tương tự.
  - Dòng ~6621-6635 (hàm mở rộng/thu gọn node, up/down): tương tự.
  - Dòng ~8799-8820 (wiring nút `#lineage-tree-source`): `let _currentTreeSource='consensus'` →
    `window._currentTreeSource = window._currentTreeSource || 'dila'`; click handler ghi vào
    `window._currentTreeSource` thay vì biến cục bộ.
  - Không đổi field/response API, không đổi DOM/CSS, không đổi hành vi khi KHÔNG bấm nút chọn nguồn.

Backup trước khi sửa: `daoanh/docs/sessions/2026-10-30/places.html.before_T502lineage_backup`.

## 5. Migration / import / dry-run / rollback

- **Không chạm DB.** Chỉ sửa JS trong `places.html` (frontend, không ghi dữ liệu).
- Revert: `cp docs/sessions/2026-10-30/places.html.before_T502lineage_backup places.html` hoặc
  `git diff -- daoanh/places.html` rồi `git checkout -- daoanh/places.html` (chưa commit gì, user chưa yêu cầu commit).

## 6. Test cases & kết quả (bằng chứng browser thật, 127.0.0.1:8080)

| Case | Input | Expected | Actual (trước fix) | Actual (sau fix) | PASS/FAIL |
|------|-------|----------|---------------------|-------------------|-----------|
| Case yêu cầu | focus=A007928, gõ "Thiên Nhiên" vào `#lineage-search` | search trả danh sách, canh rõ có/không dữ liệu | search đã trả đúng 16 kết quả (fix cũ T417); tree/generation show honest empty-state | giống hệt, không đổi (đúng per data) | ✅ |
| Fallback — entity có dữ liệu | click kết quả A009460 (Đan Hà Thiên Nhiên) | tree + generation hiện đúng | render đúng (7 đời, TTL 36) | render đúng, không regression | ✅ |
| Bug mới phát hiện — nút chọn nguồn cây | bấm "Cây Marcus" trên focus=A007928 | query phải đổi `&trees=marcus` | **FAIL** — query không đổi (luôn `up=2&down=2&include_single=1`) | **PASS** — `...&trees=marcus` | ✅ (đã fix) |
| Regression — route map mặc định | `/daoanh/places` (không mode=lineage) | không lỗi console, map load bình thường | — | load OK, 0 console error | ✅ |
| Regression — syntax toàn bộ `<script>` trong `places.html` | `node -e "new Function(...)"` từng block | không throw | — | "ALL SCRIPT BLOCKS OK" | ✅ |

## 7. Limitation / data gap còn lại

- **A007928 ("Thiên Nhiên" nhà Minh) genuinely không có dữ liệu pháp hệ** trong DILA/Marcus/TTL —
  đây là data gap thật, không phải lỗi code. Nếu Admin muốn tra "Thiên Nhiên" có nghĩa là vị tổ sư
  Đan Hà Thiên Nhiên nổi tiếng (唐/Đường), ID đúng là **A009460**, không phải A007928. Route test case
  trong task có thể đã trỏ nhầm ID — Admin xác nhận lại nếu route gốc muốn test người khác.
- Thông điệp empty-state tĩnh ở `#lineage-empty` (dòng 757, "Chưa tìm thấy quan hệ truyền thừa Marcus
  cho nhân vật này...") hơi lệch tên nguồn — API consensus mặc định gộp cả 4 nguồn (DILA/Marcus/TTL/
  Lineage), không riêng Marcus. Đây là message tĩnh có từ trước, **chưa sửa trong session này** (ngoài
  phạm vi bug chính, cosmetic, không ảnh hưởng dữ liệu) — đề xuất follow-up task riêng nếu Admin muốn
  chỉnh câu chữ cho chính xác hơn.
- Bug (B) đã sửa chỉ có bằng chứng tác động rõ trên **test đã chạy** (A007928, A009460). Chưa quét toàn
  bộ DB xem có person nào mà `v_tree_marcus`/`v_tree_ttl` có cạnh nhưng consensus-combined không có —
  nếu Admin muốn, có thể chạy thêm 1 query kiểm tra diện rộng trước khi đóng task.

## 8. Phần Admin cần xác nhận trước khi đánh DONE

1. Xác nhận route test case `focus=A007928` trong task đúng là ID admin muốn kiểm (hay nhầm với
   A009460 Đan Hà Thiên Nhiên).
2. Xác nhận fix (B) — đổi `window._currentTreeSource` — không có tác dụng phụ ngoài ý muốn (đã test 2
   case + full syntax check + 1 regression route, chưa test hết toàn bộ 4 nút trên nhiều entity khác).
3. Quyết định có cần follow-up task sửa message tĩnh `#lineage-empty` (dòng 757) hay không.
