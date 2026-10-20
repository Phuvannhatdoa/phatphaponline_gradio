# T360 — Badge nguồn/độ tin cậy cho tên tiếng Việt (person + places)

Ngày: 2026-10-12

## 1. Audit DB thực tế (khác với giả định trong task file)

Task file giả định cột `people.source_id`/`places.confidence` phản ánh trực tiếp
nguồn của `name_vi`. Thực tế sau khi audit `daoanh/data/lineage.db`:

- `people.source_origin` = `'DILA'` và `people.source_id` = `1` cho **TẤT CẢ**
  48,673 dòng — đây là nguồn của **bản ghi danh tính** (tên Hán/metadata DILA),
  KHÔNG phải nguồn riêng của `name_vi`. Không dùng được để phân biệt ZQ vs xác nhận.
- `entity_claims.source_id` (DILA=1, ZQLOCAL=5 — đúng như CLAUDE.md) chỉ tồn tại
  cho **PLACE** entities (`entity_id` 100001–218328, claim_type=`NAME`,
  predicate=`vietnameseName`/`canonicalNameZh`). Phạm vi `entity_id` của PERSON
  (218329–267001) chỉ có `NETWORK_EVIDENCE` (Marcus), **không có** claim `NAME`
  nào cho person — CLAUDE.md's "entity_claims.source_id: ZQLOCAL=5 (tên Việt)"
  áp dụng cho **places**, không áp dụng trực tiếp cho **people**.
- Nguồn thật của `places.name_vi`: bảng `places.name_vi` hầu như luôn **rỗng**
  (chỉ 2/59,161 dòng có giá trị). >99.9% tên Việt của địa danh đến từ
  `namevi_map_places` — bảng này có cột `source` (TEXT, giá trị thật:
  `auto_transliterate`, `auto_transliterate_v2`, `auto_transliterate_t49`,
  `auto_generated`, `manual`, `manual_fix`, `ttl_confirmed`) và `confidence`
  (REAL, thực tế 0.5–1.0) — đây mới là cột nguồn/độ tin cậy đúng nghĩa.
- Nguồn thật của `people.name_vi`: không có bảng claim phủ hết 48,673 người.
  Chỉ có 2 bảng authority phủ một phần nhỏ:
  - `person_display_names` (8 dòng) — có `verification_status`
    (`verified_direct`/`verified_crosswalk`) + `source_type` (`manual`/`ttl`).
  - `vn_person_authority` (1,074 dòng, khớp qua `dila_id`) — có `status`
    (`verified`, `auto_ttl`, `alias_vi_suffix`, `alias_zh_match`, `pending`),
    không có cột confidence số.
  47,591/48,673 người (~97.8%) không có record trong cả hai bảng → đúng như
  CLAUDE.md §"ZQ — nguồn tên tiếng Việt": mặc định coi là ZQ tự động,
  confidence 0.5.

**Kết luận khác biệt với task file:** task file giả định cột `source_id`/`confidence`
có sẵn trực tiếp trên `people`/`places` và chỉ cần SELECT ra. Thực tế phải viết
2 hàm resolver riêng (`_t360_resolve_person_name_vi_source`,
`_t360_resolve_place_name_vi_source`) đọc đúng bảng/cột đã audit ở trên, có
phân cấp ưu tiên nguồn, và fallback đúng theo quy tắc CLAUDE.md khi không có
authority record.

## 2. Route thực tế đang dùng (khác với task file)

- Person detail: `/daoanh/api/persons/<person_id>` (app.py) ← dùng bởi
  `daoanh/admin/person.html` (route thật, khớp giả định của task file).
- Place detail: **task file ghi `daoanh/admin/places.html`, nhưng file đó là
  trang review `places_pending` của admin, không gọi endpoint chi tiết địa danh
  nào cả** (đã grep xác nhận không có `api/places/` trong file). Trang chi
  tiết địa danh thật là **`daoanh/places.html`** (file gốc, không phải
  `admin/`), được serve qua `local_gateway.py` tại route `/daoanh/places`.
  Trang này gọi **2 endpoint theo thứ tự ưu tiên**:
  1. `/daoanh/api/entity/<id>/unified` (được thử trước — xác nhận bằng network
     log khi test trên browser: mọi lần chọn địa danh đều gọi endpoint này).
  2. `/daoanh/api/places/<place_id>` (chỉ dùng khi (1) thất bại — legacy fallback).

  Vì vậy đã sửa **cả hai** endpoint để badge hiển thị đúng trong thực tế, không
  chỉ endpoint legacy mà task file nêu.

## 3. Files đã sửa

- `daoanh/app.py`
  - Thêm 3 hàm helper (sau `_t86_origin_place`, dòng ~6250):
    `_t360_classify_name_vi_source(raw_source, confidence)`,
    `_t360_resolve_place_name_vi_source(detail)`,
    `_t360_resolve_person_name_vi_source(conn, person_id)`.
  - `/daoanh/api/places/<place_id>` (`api_places_detail`, dòng ~4435): giữ lại
    cột `source`/`confidence` thật của `namevi_map_places` trước khi bị ghi đè
    bởi nhãn đánh dấu bảng gốc (`detail['source'] = 'places'|'namevi_map'`);
    thêm `source_of_name_vi`/`confidence_name_vi`/`badge_color_name_vi` vào
    response, bọc try/except, dọn field nội bộ `_namevi_*` trước khi trả JSON.
  - `/daoanh/api/entity/<entity_id>/unified` (`entity_unified`, dòng ~17262):
    mở rộng query `namevi_map_places` lấy thêm `confidence, source`; thêm
    `source_of_name_vi`/`confidence_name_vi`/`badge_color_name_vi` vào
    `entity{}`, bọc try/except.
  - `/daoanh/api/persons/<person_id>` (`api_person_by_id`, dòng ~19322): thêm
    `source_of_name_vi`/`confidence_name_vi`/`badge_color_name_vi` vào response,
    bọc try/except.

- `daoanh/admin/person.html`
  - Thêm `<span id="name-vi-badge">` cạnh tiêu đề tên (`hdr-name`) +
    `<div id="name-vi-badge-info">` (giải thích, ẩn/hiện khi click).
  - Thêm JS `renderNameViBadge(label, confidence, color)` +
    `toggleNameViBadgeInfo()`; gọi `renderNameViBadge(...)` ngay sau khi nhận
    response từ `/daoanh/api/persons/<id>`.

- `daoanh/places.html` (KHÔNG phải `admin/places.html` — xem mục 2)
  - Thêm `<span id="nameViSourceBadge">` cạnh `#itemNameVi` +
    `<div id="nameViSourceInfo">`.
  - Thêm JS `renderNameViSourceBadge(label, confidence, color)`; gọi ở cả 2
    nhánh fetch dữ liệu (unified path dòng ~1258, legacy fallback dòng ~1389)
    và ở các điểm chọn thực thể khác (`selectItem` reset đầu hàm, `selectPerson`,
    `_nexusLoadPersonProfile`, `_nexusLoadPlaceProfile`, nhánh "unknown/text/time"
    trong `openEntityProfileFromNode`) để tránh badge của địa danh trước đó còn
    sót lại khi người dùng chuyển sang xem một Tăng nhân hoặc thực thể khác
    (phát hiện khi test trên browser — xem mục 5).

## 4. Before/After contract

**`/daoanh/api/persons/A033489`** (before → after, chỉ phần liên quan):
```
# before: không có field này
# after:
"source_of_name_vi": "TTL xác nhận",
"confidence_name_vi": 0.95,
"badge_color_name_vi": "green"
```

**`/daoanh/api/places/PL000000023255`** (`data` object, before → after):
```
# before: không có field này
# after:
"source_of_name_vi": "Admin chỉnh sửa",
"confidence_name_vi": 0.72,
"badge_color_name_vi": "gray"
```

**`/daoanh/api/entity/PL000000023255/unified`** (`entity` object, after):
```
"source_of_name_vi": "Admin chỉnh sửa",
"confidence_name_vi": 0.72,
"badge_color_name_vi": "gray"
```

Màu badge theo ngưỡng confidence (không hard-code theo ID):
`>= 0.95` → green (DILA/chính thức), `0.8–0.94` → yellow (TTL/Admin),
`< 0.8` → gray (ZQ tự động hoặc chưa xác nhận).

## 5. Kết quả test

**Case yêu cầu (route/case nêu trong prompt):**
- `/daoanh/places` → tìm "Thiếu Lâm Tự" (PL000000023255): badge hiển thị
  `[Admin chỉnh sửa] confidence: 0.7` màu xám, click vào badge hiện dòng giải
  thích "Tên Việt này đã được Admin kiểm tra và chỉnh sửa trực tiếp. Độ tin
  cậy: 0.7." — xác nhận bằng screenshot trên browser thật (không chỉ JS inject).
- `/daoanh/admin/person.html?id=A033489`: badge `[TTL xác nhận] confidence: 1.0`
  (test thêm A000035: `[TTL (alias_vi_suffix)] confidence: 0.7`).

**Case fallback/edge đã test:**
- `/daoanh/admin/person.html?id=A000001` (người không có record trong
  `person_display_names` lẫn `vn_person_authority`): badge
  `[ZQ tự động] confidence: 0.5` màu xám — đúng fallback mặc định theo CLAUDE.md.
- `places.html` — PHÁT HIỆN REGRESSION khi test trên browser thật: chuyển từ
  một địa danh (có badge) sang một Tăng nhân qua danh sách gợi ý tìm kiếm →
  badge cũ của địa danh **còn sót lại** trên UI (không có field name_vi source
  cho person ở trang này). Đã sửa bằng cách gọi `renderNameViSourceBadge(null,
  null, null)` ở mọi điểm chuyển sang thực thể khác loại; verify lại bằng
  `window.selectPerson(...)` rồi `window.selectItem(...)` qua lại — badge ẩn/hiện
  đúng, không còn sót dữ liệu cũ.
- Place không có DB record nào (namevi_map_places rỗng, places.confidence mặc
  định 1.0 khi `places.name_vi` tự nó có giá trị): badge trả `None` → ẩn hoàn
  toàn (không hiển thị badge rác).

## 6. Trạng thái py_compile

```
python -m py_compile app.py
COMPILE_OK
```

## 7. Limitation / việc chưa làm (ngoài phạm vi được giao)

- `daoanh/admin/places.html` (file task gốc nêu tên) **không** được sửa vì nó
  không phải trang hiển thị chi tiết địa danh (không gọi endpoint place detail)
  — đã sửa đúng file thật (`daoanh/places.html`) thay vào, có ghi rõ lý do ở
  mục 2. Coordinator/Admin cần xác nhận lại nếu ý định ban đầu là khác.
- Chưa cập nhật `AGENTS.md §2` / viết `docs/integration/SOURCE_TAGGING.md` như
  mục "4. Documentation" trong task file — phần này không nằm trong phạm vi
  route/case cụ thể được giao trong prompt (chỉ yêu cầu sửa app.py +
  person.html + places.html + report), nên để coordinator quyết định có cần
  thêm một task con hay không.
- Hàm `_nexusLoadPlaceProfile` trong `places.html` gọi
  `/daoanh/api/places/<id>` và đọc field thẳng từ response gốc (`d.name_vi`,
  `d.dila_id`) thay vì `d.data.name_vi` — đây là bug tiền nhiệm (route trả về
  `{ok, data:{...}}`) đã có từ trước, không thuộc phạm vi T360. Đã né bug này
  cho riêng field badge mới (đọc qua `d.data || d`) để badge hoạt động đúng,
  nhưng không sửa bug `name_vi`/`dila_id` bị undefined ở nhánh đó vì ngoài
  phạm vi task.
- Server dev local (app.py, server.py, local_gateway.py) hiện vẫn đang chạy
  trên 127.0.0.1:5000/5001/8080 để coordinator/QA kiểm tra tiếp; log test tại
  `daoanh/app_local_t360.log` / `.err`.
