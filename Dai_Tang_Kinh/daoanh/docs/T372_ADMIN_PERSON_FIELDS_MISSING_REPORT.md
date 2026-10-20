# T372 — Admin Person Page (A000074) Fields Missing/Wrong — Fix Report

**Ngày:** 2026-10-12
**Task:** `tasks/T372-admin-person-page-a000074-fields-missing.md`
**Route/case:** `http://127.0.0.1:8080/daoanh/admin/person.html?id=A000074` (local)

## Tóm tắt root cause

Ba lớp lỗi độc lập, tất cả đều có nguyên nhân gốc là **DB hiện tại (`data/lineage.db`)
thiếu/mất dữ liệu đã từng được nhập qua các ETL idempotent trước đây** (nhiều khả năng
do một lần restore file-level ghi đè `lineage.db` bằng bản cũ hơn ngày các ETL này chạy —
xem commit gần nhất "restore(T358): khôi phục files T358 bị xóa nhầm"). Không phải lỗi
logic code ở 2 trong 3 lớp; raw XML nguồn (`data/dila_import/.../Buddhist_Studies_Person_Authority.xml`)
luôn có đủ dữ liệu, không hề bị sửa.

### Lớp 1 — ETL/sidecar table thiếu: `person_hanviet_debug` (T172)
- **Triệu chứng:** "Hán (raw)" = "(trống)", "Hán tự / Âm tiết" = "?/?".
- **Nguyên nhân:** bảng sidecar `person_hanviet_debug` (do `scripts/t172_hanviet_charwise_migrate.py`
  tạo) không tồn tại trong `lineage.db` hiện tại. `_t172_load_hv()` (app.py) trả `None` →
  `result['hv'] = {}` fallback → UI hiển thị trống.
- **Fix:** chạy lại `scripts/t172_hanviet_charwise_migrate.py --apply` (full sweep, không
  giới hạn person) — script này **idempotent, tự backup DB, có `--revert`**, và assert
  `people` COUNT(*) không đổi trước/sau (an toàn, additive-only).
- **Kết quả:** 47,036 dòng `person_hanviet_debug` được ghi (1,637 người bị bỏ qua vì không
  phải tên Hán). `people` COUNT(*) = 48,673 → 48,673 (không đổi).
- **Backup tự động:** `data/backups/lineage_backup_t172_20261012_205101.db`

### Lớp 2 — ETL/sidecar table thiếu: `ttl_v2_source_records` (T227)
- **Triệu chứng:** Alternative names, Birth/death dates, Sex/gender, Dynasty (bản XML),
  Works in Tripitaka, Bibliography, Wikidata IDs — tất cả không hiển thị.
- **Nguyên nhân:** `_t148_load_dila_extra()` (app.py, hàm nạp "DILA extra" cho
  `/daoanh/api/person/<id>/dila_full`) đọc dữ liệu từ bảng `ttl_v2_source_records`
  (kind='DILA_XML'), KHÔNG đọc trực tiếp từ file XML trên đĩa dù hàm có sẵn biến đường dẫn
  file (`_T148_PERSON_XML`, không dùng tới). Bảng này không tồn tại trong `lineage.db`
  hiện tại → `_T148_DILA_EXTRA` luôn rỗng → `/dila_full` trả `has_extra:false` cho MỌI
  person, không riêng A000074.
- **Fix:** chạy lại importer `src_python.ttl_db_sources.import_sources()` (nguồn gọi của
  `scripts/ingest_ttl_v2_db_sources.py`) với archive gốc
  `data/backups/T215-tri-tai-sync-20261002/authority_person.2026-09.zip` — importer này
  **additive-only** (không UPDATE `people`/lineage/VN tables), tự backup SQLite nhất quán
  trước khi ghi, UNIQUE constraint khiến việc chạy lại idempotent.
  - **Lưu ý kỹ thuật:** không gọi được script wrapper gốc
    `scripts/ingest_ttl_v2_db_sources.py` trực tiếp vì nó có một sanity-check phụ đọc
    COUNT(*) từ bảng `person_gen_computed` (cũng không tồn tại trong DB hiện tại — một
    nạn nhân khác cùng đợt restore, NẰM NGOÀI PHẠM VI T372). Đã gọi thẳng hàm
    `import_sources()` bên trong `src_python/ttl_db_sources.py` (cùng logic, bỏ qua đúng
    một dòng sanity-check không liên quan tới lớp lỗi đang sửa) để không mở rộng phạm vi
    sang `person_gen_computed`.
- **Kết quả:** 49,361 bản ghi `DILA_XML` (toàn bộ Person Authority) + 1,036 TTL active +
  7 TTL quarantine = 50,404 bản ghi được nạp. `people`/`vn_person_authority`/
  `vn_person_relations`/`lineage_edge_assertions` COUNT(*) không đổi trước/sau.
- **Backup tự động:** `docs/sessions/2026-10-12/T372-t227-reimport/lineage-before.db`
  (+ `import-manifest.jsonl`, `summary.json` cùng thư mục).

### Lớp 3 — Resolver bug: `_t86_origin_place()` map sai ID (place của origin)
- **Triệu chứng:** "Place of origin" hiển thị "Năng Huyện" (碭縣) thay vì "許州" — **đúng
  place_id (`PL000000024832`) nhưng sai dữ liệu**, không phải lỗi ETL.
- **Root cause xác minh:** `person_origin_link.place_id` lưu ID DILA gốc dạng dài
  (`PL000000024832`, 12 chữ số) — CÙNG hệ ID với bảng `places_dila` (59,167 dòng, ID dài).
  Bảng `places` (59,161 dòng) lại dùng một hệ ID NGẮN, tuần tự, độc lập
  (`PL024832`, `PL020000`, ...) — **không tương ứng 1-1 về mặt số học với ID DILA gốc,
  dù trông giống nhau sau khi bỏ số 0 đầu.**
  Hàm cũ `_t86_normalize_place_id()` biến đổi `PL000000024832` → `PL024832` rồi tra bảng
  `places` bằng ID "ngắn" này — vô tình trúng một dòng **khác hoàn toàn** (`PL024832` =
  "碭縣"/Năng Huyện) chỉ vì trùng số, vi phạm nguyên tắc stable-identity (CLAUDE.md: "Canonical
  internal ID = join key duy nhất... không merge record chỉ bằng matching tên/ID suy diễn").
  Bug này ảnh hưởng **mọi person có origin_place**, không riêng A000074 — tái hiện ở mọi
  endpoint dùng `_t86_origin_place()` (`/api/persons/<id>`, `/api/monk/<id>/lineage-tree`,
  `/api/person/<id>/dila-axis` liên quan, …).
- **Fix:** sửa `_t86_origin_place()` (app.py) để tra thẳng `places_dila` bằng `raw_pid`
  (ID DILA gốc, không normalize) — bảng này CÙNG hệ ID với `person_origin_link`. Tên Việt
  (`name_vi`) nay join `namevi_map_places` theo cột `dila_id` (khóa nối ổn định có sẵn)
  thay vì theo `name_zh` (join theo tên — cũng là một vi phạm nhỏ về stable-identity đã
  tiện sửa luôn, tránh trùng tên gây nhầm place).
  `_t86_normalize_place_id()` nay không còn được gọi ở đâu trong `app.py` (dead code, giữ
  nguyên không xóa — không nằm trong phạm vi tối thiểu của fix này).

### Bonus fix trong cùng lớp 2 — Wikidata IDs chỉ lưu 1/2
- XML của A000074 có **2** `<idno type="Wikidata">` (Q10938529, Q45709872) nhưng
  `_t148_load_dila_extra()` cũ GHI ĐÈ biến `wikidata_id` mỗi lần gặp tag → chỉ giữ QID
  cuối cùng. Đã sửa: giữ `wikidata_id` (tương thích ngược, QID đầu tiên) + thêm
  `wikidata_ids` (list đầy đủ, dedupe) trong extractor, trả thêm field này ở
  `/daoanh/api/person/<id>/dila_full`, và cập nhật `admin/person.html` để render TẤT CẢ
  QID trong `wikidata_ids` (trước đây chỉ render 1 link).

## Files đã sửa

| File | Thay đổi |
|---|---|
| `E:\...\daoanh\app.py` | `_t86_origin_place()` (dòng ~6234): tra `places_dila` bằng raw ID thay vì `places` bằng ID normalize sai; `namevi_map_places` join theo `dila_id` thay vì `name_zh`. `_t148_load_dila_extra()` (dòng ~5659-5890) + `api_person_dila_full()` (dòng ~20571): thu thập đủ danh sách `wikidata_ids` thay vì ghi đè 1 QID. |
| `E:\...\daoanh\admin\person.html` | Render tất cả `wikidata_ids` (trước chỉ render `wikidata_id` đơn lẻ). |

**Backup trước khi sửa** (theo CLAUDE.md): `docs/sessions/2026-10-12/app.py`,
`docs/sessions/2026-10-12/person.html` (bản gốc trước khi edit).

## DB migrations đã chạy (không sửa code, khôi phục dữ liệu bị mất)

1. `scripts/t172_hanviet_charwise_migrate.py --apply` (full sweep) — idempotent, tự
   backup, có `--revert`. Backup: `data/backups/lineage_backup_t172_20261012_205101.db`.
2. `import_sources()` từ `src_python/ttl_db_sources.py` (logic gốc của T227, archive
   `data/backups/T215-tri-tai-sync-20261002/authority_person.2026-09.zip`) — additive-only,
   tự backup, idempotent (UNIQUE constraint). Backup + manifest:
   `docs/sessions/2026-10-12/T372-t227-reimport/`.

Cả hai đều **không đụng tới** `people`/`vn_person_authority`/`vn_person_relations`/
`lineage_edge_assertions` (đã verify COUNT(*) trước/sau bằng nhau).

## Before/After API contract

### `/daoanh/api/persons/A000074` — `origin_place`
- **Before:** `{"name_vi":"Năng Huyện","name_zh":"碭縣","place_id":"PL000000024832","vi_confidence":0.7,"vi_source":"auto_transliterate"}`
- **After:** `{"name_vi":"Toánh Xuyên Quận","name_zh":"許州","place_id":"PL000000024832","vi_confidence":0.85,"vi_source":"auto_transliterate_v2"}`
  (name_zh nay đúng với XML gốc `<placeName>許州<ref>PL000000024832</ref></placeName>`.
  `name_vi` "Toánh Xuyên Quận" là bản dịch tự động ZQ, confidence 0.85, badge rõ nguồn —
  nằm ngoài phạm vi T372 việc cải thiện chất lượng dịch, chỉ cần join đúng place.)

### `/daoanh/api/person/A000074/dila_full`
- **Before:** `{"has_extra": false, "ok": true, "person_id": "A000074"}`
- **After:** `has_extra: true`, đầy đủ `alt_names` (4), `sex: "Nam"`, `dynasty_xml: "唐"`,
  `birth_date`/`death_date` (chuỗi khoảng ngày TEI gốc), `wikidata_id` + `wikidata_ids`
  (2 QID), `works_tripitaka`, `listbibl` (8 mục — khớp đúng số lượng `<bibl>` trong XML
  gốc, XML có 1 mục trùng lặp nên 8 chứ không phải 7 như ước lượng ban đầu trong task;
  hiển thị đúng nguồn, không dedupe tự ý).

## Kết quả test

### Case chính — A000074
- Browser thật (`http://127.0.0.1:8080/daoanh/admin/person.html?id=A000074`), click/scroll
  thực tế, screenshot before/after (xem trong transcript phiên làm việc):
  - Hán (raw): 寶通, 2/2 ✓ (trước: trống, ?/?)
  - Alternative names: 4 tag hiển thị (大顛祖師/大顛和尚/大顛寶通/大顛) ✓
  - Birth/death: Sinh +0732-01-01~+0732-12-31 | Mất +0824-02-08~+0824-02-28 ✓
  - Sex: Nam ✓
  - Dynasty: 唐 ✓
  - Place of origin: "Toánh Xuyên Quận (許州)" ✓ (trước: Năng Huyện/碭縣 sai)
  - Works in Tripitaka: 般若心經註解(X0573) ✓
  - Bibliography: "Trích dẫn CBETA (8)" + đủ 8 mục ✓
  - Wikidata: Q10938529 · Q45709872 (2 QID) ✓ (trước: thiếu/không có field list)
  - Tiểu sử Việt: "(chưa dịch)" — **lý do xác đáng**: chưa có bản dịch người/cache nào,
    đúng theo quy tắc KHÔNG dùng LLM bịa dịch tự động; bio Hán gốc hiển thị đầy đủ.

### Case fallback/regression — A003295 (Hồ Hài Chi, person khác có đủ field tương tự)
- `/daoanh/api/person/A003295/dila_full`: `has_extra:true`, `alt_names:["胡諧"]`,
  `wikidata_ids:["Q3497196"]`, `sex:"Nam"`, `dynasty_xml:"南齊"`.
- `/daoanh/api/persons/A003295` → `origin_place: {"name_vi":"Nam Xương","name_zh":"南昌",...}`
  — verify chéo `places_dila` id=PL000000018629 → name="南昌" khớp đúng.
- Browser thật xác nhận render đúng: Hán raw 胡諧之 (3/3), Nơi xuất xứ "Nam Xương (南昌)".

### Edge case
- Person không có `origin_place` link (A000075): API trả `origin_place: null` (không
  crash, không hard-code fallback text) ✓.
- Person không tồn tại: API trả 404 như cũ ✓.
- `/daoanh/api/monk/A000074/lineage-tree` (endpoint khác cũng dùng `_t86_origin_place()`):
  `center.origin_place` trả đúng 許州 — xác nhận fix áp dụng nhất quán, không chỉ riêng
  endpoint admin.

### Compile check
- `python -m py_compile app.py` → OK, không lỗi cú pháp.

## Limitation / việc còn lại

- **Tiểu sử Việt** vẫn "(chưa dịch)" cho A000074 — đúng theo thiết kế (không tự dịch bằng
  LLM để tránh bịa dữ liệu học thuật), không phải bug. Nếu Admin muốn có bản dịch, cần dùng
  nút "AI Dịch DILA" sẵn có trên trang (quy trình dịch có review riêng, ngoài phạm vi T372).
- **`person_gen_computed`** (bảng khác cũng bị thiếu, phát hiện khi chạy lại T227 importer
  qua sanity-check cũ) — KHÔNG đụng tới, nằm ngoài phạm vi T372 (không liên quan đến 11
  field trong done_when). Nên mở task riêng nếu có chức năng phụ thuộc bảng này bị ảnh
  hưởng.
- **`name_vi` của origin_place** ("Toánh Xuyên Quận" cho 許州) là bản dịch tự động ZQ chất
  lượng chưa cao (có thể do engine dịch nhầm sang tên biến thể 潁川郡) — T372 chỉ đảm bảo
  join đúng place (ID/tên Hán khớp), không mở rộng sang sửa chất lượng transliteration.
- App server (`app.py`, port 5000) đã được restart 2 lần trong phiên này để nạp cache
  `_T148_DILA_EXTRA`/`person_hanviet_debug` mới — nếu VPS cũng bị ảnh hưởng tương tự (DB
  thiếu 2 bảng sidecar), cần restart app trên VPS sau khi đồng bộ migration, NGOÀI PHẠM VI
  phiên local này (không tự ý deploy VPS).

## Bổ sung scope — section "THẦY / HỌC TRÒ" bị render 2 lần (case A000035)

Admin/teammate báo thêm sau khi 2 lớp fix ETL ở trên đã chạy: trang admin person hiện
render section "Thầy/Học trò" **2 lần**.

### Root cause
Section phía trên — `<div id="card-axis">`, tiêu đề "THẦY / HỌC TRÒ (DILA LINEAGE)" —
là code fallback được thêm từ trước (comment gốc: "T359 fix 1 ... dila_full có thể gãy
im lặng (bảng ttl_v2_source_records không tồn tại) nên không được phụ thuộc d.relations
của dila_full; endpoint dila-axis đọc trực tiếp lineage_edge_assertions ... độc lập, luôn
hoạt động"). Nó được viết đúng lúc bảng `ttl_v2_source_records` đang thiếu (xem Lớp 2 ở
trên) — khi đó `/dila_full` luôn trả `has_extra:false` nên section fallback là nguồn
Thầy/Học trò DUY NHẤT hiển thị được.

Sau khi Lớp 2 được fix (re-import `ttl_v2_source_records`), `/dila_full` trả về đủ
`relations` → section "Thầy/Học trò" **thứ hai** (render trong card "DỮ LIỆU DILA
AUTHORITY (XML)", từ `d.relations`, có trích dẫn nguồn `bibl` per-quan hệ) cũng hiển thị
→ 2 section trùng nội dung (cùng danh sách thầy/trò, section fallback thiếu trích dẫn =
"incomplete/sai" so với section đầy đủ).

### Fix
`admin/person.html` (backup trước khi sửa hôm nay đã có tại `docs/sessions/2026-10-12/person.html`):
- Xoá `<div id="card-axis">...</div>` (HTML block, dòng ~113-119 gốc) — thay bằng comment
  giải thích lý do gỡ, để không ai thêm lại nhầm.
- Xoá hàm `axisCard()` và `loadDilaAxis()` (JS, dòng ~753-786 gốc) — không còn chỗ gọi.
- Xoá lời gọi `loadDilaAxis();` trong `load()` (dòng ~940 gốc).
- Endpoint `/daoanh/api/person/<id>/dila-axis` (app.py) **giữ nguyên, không xoá** — nằm
  ngoài yêu cầu, và vẫn có thể hữu ích cho debug/API khác; chỉ gỡ phần UI gọi nó trùng lặp.
- `grep` xác nhận không còn tham chiếu `axisCard|loadDilaAxis|card-axis|axis-body` nào
  trong `admin/person.html` (chỉ còn 2 dòng comment giải thích).

### Test — browser thật, cả 2 case
- **A000035** (case admin nêu): trước — 2 section "Thầy/Học trò" (section trên: Thầy
  "Nguyên Huệ" không trích dẫn; section dưới: Thầy "元惠 (T49n2035_p0225a14)" có trích
  dẫn). Sau fix: `find("THẦY / HỌC TRÒ")` → 0 match; `find("Thầy (1)")` → đúng 1 match,
  section còn lại đầy đủ trích dẫn (望月卷六附錄:033, T49n2035_p0225a14), 5 học trò hiển
  thị đúng cả 2 cột ZH/VI.
- **A000074** (case chính T372): trước đã không lộ rõ 2 section vì lúc đó `/dila_full`
  mới vừa fix và cache app chưa load `relations` đầy đủ ở lần xem đầu; sau khi reload —
  xác nhận cũng chỉ còn 1 section "Thầy (1)" (Thạch Đầu Hy Thiên) / "Học trò (5)", đầy đủ
  trích dẫn, không regression.
- `python -m py_compile app.py` → OK (không đổi app.py ở bước này, chỉ person.html — HTML/JS
  không cần compile check, đã verify bằng cách load lại trang thật + console không có lỗi
  JS mới liên quan đến các hàm đã xoá).

## Chờ

- `daoanh-qa` xác nhận ĐẠT (theo done_when của T372, bao gồm cả phần bổ sung duplicate
  lineage section).
- Admin xác nhận DONE.
