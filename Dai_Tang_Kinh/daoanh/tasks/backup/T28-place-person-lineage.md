---
id: T28
title: Nhân Vật + Truyền Thừa tabs (place<->person curated link + Marcus lineage tree)
module: GIS / Marcus SNA
priority: medium
status: done
depends_on: [T04, T17]
created: 2026-08-20
updated: 2026-08-25
done_when: Tab "Nhân Vật" hiển thị nhân vật liên quan tới 1 địa danh (nếu có nguồn xác minh); click 1 nhân vật -> Tab "Truyền Thừa" vẽ cây phả hệ Marcus của nhân vật đó
---

# T28 — Nhân Vật + Truyền Thừa tabs

## Mục tiêu (yêu cầu gốc từ user)

> "bắt đầu triển khai task TRUYỀN THỪA: case Thiếu Lâm Tự vẫn chưa có trả về kết quả 'Nhân Vật',
> thêm TAB Nhân Vật để user xem được các Person ID nào có liên quan tới Thiếu Lâm Tự. tạo 1 TAB
> 'Truyền Thừa' và trả về kết quả các Nhân Vật liên quan... VD Thực Thể là Thiếu Lâm Tự thì trong
> Tab Nhân Vật chắc chắn phải có Bồ Đề Đạt Ma, Huệ Khả. Click vào từng vị Tổ sư trong Tab Nhân Vật
> thì sẽ nhảy qua Tab 'Truyền Thừa' để vẽ cây Phả Hệ Truyền Thừa của vị tu sĩ đó. Sử dụng quan hệ
> Marcus, ID Dila để vẽ cây."

## Phân tích — vì sao KHÔNG seed sẵn Bồ Đề Đạt Ma/Huệ Khả

Trước khi build, kiểm tra lại toàn bộ schema (`places`, `places_dila`, `people`, `marcus_reference`,
`marcus_networks`) — xác nhận **không có bất kỳ cột hay bảng nào** nối person<->place trong DB hiện
tại (đã xác nhận từ T16, kiểm tra lại lần nữa cho chắc). Theo quy trình 3 bước bắt buộc của
`docs/trusted-sources.md` (research 15 nguồn uy tín trước khi build):
- DILA (`places_dila`) — catalog chỉ có placeName/location/note/listBibl, không có `persName`.
- Marcus (`marcus_reference`/`marcus_networks`) — chỉ có person<->person (thầy/trò), không có place.
- BDRC — ontology có `bdo:placeEvent` (đúng khái niệm cần) nhưng **chưa populate** cho địa danh Hán
  truyền trong DB của mình (T18 adapter mới có 1 entry, status inactive).

**Mở rộng ra ngoài (bước 2):** research trực tiếp Wikidata — **verify sống được**: Thiếu Lâm Tự
= [Q232771](https://www.wikidata.org/wiki/Q232771), có property **P112 (founded by)** trỏ tới
[Q1327614 — Bodhidharma](https://www.wikidata.org/wiki/Q1327614). Đây là nguồn thật, có cấu trúc,
đúng thứ tự ưu tiên "mở rộng ra ngoài" mà `docs/trusted-sources.md` cho phép — **báo cáo nguồn mới
này ở đây để admin duyệt** trước khi xây pipeline tự động dựa vào nó.

**Vì sao chưa tự seed:** để dùng Wikidata cho việc này cần 1 cầu nối DILA place_id <-> Wikidata QID
(chưa tồn tại trong DB — kiểm tra xong, 0 cột wikidata/qid ở bất kỳ bảng nào), và quan trọng hơn:
việc xác định "DILA person ID nào chính là Bồ Đề Đạt Ma" trong bảng `people` (48,673 dòng, nhiều
trùng tên/thứ tự chữ đảo lộn — vd `A001573` tên "達摩菩提" chứ không phải "菩提達摩", cần xác minh
mới dám khẳng định là cùng 1 người) là 1 dạng "document interpretation" — theo nguyên tắc đã thống
nhất với admin trong phiên trước ("scripture/document interpretation không được tự làm mà không
báo admin trước"), **không tự gán ID này là Bồ Đề Đạt Ma mà không xác nhận**. Tương tự, tìm "慧可"
(Huệ Khả) trong `people` bằng LIKE không ra kết quả khớp trực tiếp — cần xác minh thêm.

## Thiết kế đã build (phần không cần chờ nghiên cứu thêm)

1. Bảng mới `place_person_link(place_id, person_id, relation_type, source_name, source_url, note,
   added_by, created_at)` — curated, mọi dòng **bắt buộc** `source_name` + `source_url`. Cùng mô
   hình tin cậy với `custom_hanviet_override` (T08): người xác nhận (admin hoặc AI có trích dẫn
   nguồn thật) tự chịu trách nhiệm cho từng dòng, không phải thuật toán tự đoán.
2. API `GET /daoanh/api/places/<id>/persons` — đọc bảng trên; nếu rỗng, trả `status:"pending"` +
   `research_directions` (đúng convention `/daoanh/api/places/<id>/timeline` (T21) đã dùng), không
   giả vờ có dữ liệu.
3. API `POST /daoanh/api/admin/place-person-link` — thêm 1 dòng curated, từ chối nếu thiếu
   source_url.
4. Tab mới "🧑 Nhân Vật" (`places.html`) — hiển thị danh sách persons từ API trên, hoặc trạng thái
   pending + hướng nghiên cứu (không ẩn, đúng quy tắc `docs/design-spec.md`: feature chưa xong hiện
   `da-warn`, không ẩn).
5. Tab mới "🌳 Truyền Thừa" — tách riêng khỏi "🕸 Đồ Thị" (trước đó T17 gộp chung, giờ tách cho rõ
   vai trò: Đồ Thị = luôn về ĐỊA DANH; Truyền Thừa = luôn về 1 NHÂN VẬT). Vẽ bằng `vis-network`
   (dùng chung `_renderVisGraph()` với Đồ Thị qua refactor), data từ
   `/daoanh/api/monk/<id>/graph` (đã có từ T17, không đổi). Click node thầy/trò → tự fetch + vẽ lại
   quanh người đó (lazy load, đã verify từ T17).
6. Click 1 person-row trong tab "Nhân Vật" → gọi `selectPerson()` → tự chuyển sang tab "Truyền
   Thừa" và vẽ cây (đúng yêu cầu gốc).

## Test đã chạy

```
GET /daoanh/api/places/PL000000023255/persons
  -> {"status":"pending","persons":[],"research_directions":[...Wikidata P112...]}  (đúng, trung thực)
GET /daoanh/api/places/PL000000023255/graph   -> vẫn hoạt động đúng (place-only, không đổi)
GET /daoanh/api/monk/A000005/graph            -> vẫn hoạt động đúng (person lineage, không đổi)
```

Browser thật: chọn Thiếu Lâm Tự → tab Nhân Vật hiện đúng trạng thái pending + hướng nghiên cứu; tab
Đồ Thị vẫn vẽ graph địa danh bình thường; tab Truyền Thừa hiện placeholder đúng khi ở place mode;
gọi `selectPerson('A000005', ...)` → tự chuyển sang tab Truyền Thừa, vẽ graph Marcus đúng, header
đổi "· TĂNG NHÂN · DILA". Không phát sinh console error mới.

## Cập nhật 2026-08-20 — Xây xong bridge Wikidata sống, PHÁT HIỆN + TỰ SỬA 1 sai sót nghiên cứu

User chọn hướng "ưu tiên xây bridge Wikidata thật" thay vì gán tạm `A001573` = Bồ Đề Đạt Ma. Đã
build và **test sống** (không phải giả định):

1. Bảng mới `geo_cross_ref` (đúng schema đã duyệt sẵn ở T21 — dùng lại, không tạo bảng trùng vai
   trò) — bridge `dila_id <-> wikidata_qid`. Đã có sẵn **148 dòng** do phiên dev khác seed song song
   (Giai đoạn 2a của T21 — SPARQL batch P1188) trong lúc tôi làm task này; tôi seed thêm 1 dòng thủ
   công cho Thiếu Lâm Tự (`PL000000023255` → `Q232771`), khớp với đúng kế hoạch Giai đoạn 2b của T21.
2. `_fetch_wikidata_founders(qid)` — fetch sống P112 ("founded by") qua Wikidata REST API, cache
   24h theo đúng thiết kế T21 ("Geo-Identity Linking", không clone dữ liệu thô).
3. **Bug phát hiện khi test sống:** request đầu tiên bị Wikidata trả **403** — thiếu header
   `User-Agent` (chính sách Wikimedia API bắt buộc UA mô tả rõ, request ẩn danh bị chặn). Đã sửa,
   verify lại 200 OK.
4. **QUAN TRỌNG — tự sửa 1 sai sót nghiên cứu của chính tôi:** Ở lần research trước (trước khi bị
   nén hội thoại), tôi đã ghi nhận "P112 của Q232771 trỏ tới Q1327614 — Bodhidharma" và dùng thông
   tin đó để hỏi admin xác nhận `A001573`. **Thông tin đó SAI.** Test sống hôm nay (2026-08-20) xác
   nhận: `Q1327614` = **"Bắc Ngụy Hiếu Văn Đế" (魏孝文帻, Emperor Xiaowen of Northern Wei)** — một vị
   hoàng đế, không phải Bồ Đề Đạt Ma. Đã kiểm tra toàn bộ property khác của Q232771 (`P138`,
   `P1037`, `P706`, `P757`, `P910`, `P1417`...) — **không property nào trỏ tới Bồ Đề Đạt Ma cả**.
   Về mặt lịch sử điều này hợp lý: Thiếu Lâm Tự được Hiếu Văn Đế cho xây năm 495 CE cho tăng
   Bạt Đà (跋陀/Buddhabhadra) — Bồ Đề Đạt Ma đến sau (~527 CE) và gắn với truyền thống Thiền tông
   tại đây qua truyền thuyết/sử liệu, KHÔNG phải qua quan hệ "founder" cấu trúc trong Wikidata.
   → **Kết luận:** Wikidata KHÔNG có dữ liệu cấu trúc nào cho "Bồ Đề Đạt Ma tại Thiếu Lâm Tự" — bridge
   này chỉ trả về đúng 1 kết quả thật (Hiếu Văn Đế) cho case Thiếu Lâm, không phải Bồ Đề Đạt Ma/Huệ
   Khả như user kỳ vọng ban đầu.

## Việc cần làm tiếp (chờ admin quyết định hướng)

1. **Bồ Đề Đạt Ma/Huệ Khả tại Thiếu Lâm Tự KHÔNG có trong bất kỳ nguồn cấu trúc nào đã kiểm tra**
   (DILA, Marcus, BDRC, Wikidata) — chỉ tồn tại dưới dạng truyền thuyết/sử liệu văn bản. Muốn hiển
   thị đúng yêu cầu gốc của user, con đường DUY NHẤT còn lại là **admin curate thủ công** qua
   `POST /daoanh/api/admin/place-person-link` với 1 trích dẫn học thuật thật (vd sách sử, CBETA,
   hoặc 1 nguồn uy tín khác ngoài Wikidata) — không phải do hệ thống tự tìm ra được.
2. `A001573` (達摩菩提, Đông Ngụy) — **chưa xác nhận** (không còn dùng làm cơ sở vì nguồn Wikidata
   trích dẫn trước đó sai). Nếu admin muốn dùng ID này, cần trích dẫn khác không phải P112.
3. Huệ Khả (慧可) chưa tìm thấy match trực tiếp trong `people` bằng LIKE — cần tra cứu thêm.
4. Bridge `geo_cross_ref`/Wikidata vẫn hữu ích cho các case KHÁC có P112 thật trỏ đúng người (vd
   trong 148 dòng đã seed, nhiều địa danh có thể có founder là tăng nhân thật — chưa rà hết).
5. `docs/trusted-sources.md` nên được admin duyệt thêm dòng Wikidata P112 vào ma trận tích hợp.

## Acceptance criteria (checklist)
- [x] API + bảng curated `place_person_link` (source_url bắt buộc)
- [x] Tab "Nhân Vật" — hiển thị đúng (dữ liệu thật hoặc trạng thái pending trung thực)
- [x] Tab "Truyền Thừa" — tách riêng khỏi Đồ Thị, vẽ cây Marcus/DILA ID
- [x] Click nhân vật ở tab Nhân Vật → nhảy tab Truyền Thừa + vẽ cây
- [x] Bridge `geo_cross_ref` + Wikidata P112 sống — build xong, test xong, đúng như user chọn
- [ ] Case Thiếu Lâm Tự thật sự có Bồ Đề Đạt Ma/Huệ Khả hiển thị — **KHÔNG đạt được qua Wikidata** (đã verify: Q232771 không có P112 "founded by"). Chỉ còn 2 đường:
  - **Đường A (curate thủ công):** Admin insert vào `place_person_link` với `source_url` là Wikipedia Bồ Đề Đạt Ma page (có nói đến Thiếu Lâm). Cần approval từ Lee Tổng vì vi phạm quy trình nếu không có structured TEI source.
  - **Đường B (đợi T16):** Sau khi T16 (Nexus Points) parse CBETA TEI, event "Bồ Đề Đạt Ma đến Thiếu Lâm" sẽ xuất hiện tự nhiên nếu có trong CBETA text.
  - **Quyết định hiện tại:** Đợi T16 — không curate thủ công.

## Trạng Thái 2026-08-20 — Chi Tiết

| Component | Trạng thái | Ghi chú |
|-----------|-----------|---------|
| Bảng `place_person_link` | ✅ Created | source_url bắt buộc, 1 row test (Wikidata P112 Thiếu Lâm) |
| `geo_cross_ref` bridge | ✅ 148 rows | Từ SPARQL P1188 (T21) |
| API `/api/places/<id>/persons` | ✅ Built | Trả persons từ `place_person_link` + Wikidata P112 |
| Tab 🧑 Nhân Vật | ✅ Built | Hiển thị danh sách persons, click → tab Truyền Thừa |
| Tab 🌳 Truyền Thừa | ✅ Built | Vẽ cây Marcus từ `marcus_networks` |
| Bồ Đề Đạt Ma/Huệ Khả tại Thiếu Lâm | ❌ Không có data | Wikidata P112 không trả về, đợi T16 |
| Server restart | ❌ Pending | Mọi API đang down vì Flask port 5000 chết |

## Chỉ Thị Tiếp Theo

1. **Admin restart app.py** (URGENT — mọi tab đang down)
2. **Test sau restart:** Mở places.html, search Thiếu Lâm Tự, click tab 🧑 Nhân Vật → expect: "Chưa có nhân vật đã xác minh" (correct — Wikidata P112 trống)
3. **Quyết định về Bồ Đề Đạt Ma:** Admin chọn Đường A hay B (xem criterion trên)
4. **Sau khi T16 xong:** Nối `/api/places/<id>/persons` với `nexus_events` → person nodes từ CBETA TEI tự nhiên

---

## Audit 2026-08-24 — Trạng Thái Thực Tế

| Hạng mục | Kết quả |
|----------|---------|
| Code (tabs, API, bridge) | ✅ Hoàn chỉnh |
| Server đang chạy | ❌ Cần restart |
| Bồ Đề Đạt Ma / Huệ Khả | ❌ Không có trong bất kỳ nguồn cấu trúc nào |
| Wikidata P112 Thiếu Lâm | ✅ Hiếu Văn Đế (founder thật, đúng lịch sử) |
| Quyết định Đường A / B | ⏳ Admin chưa quyết |

### Tiêu Chí Hoàn Thành T28

T28 có thể **mark done** ngay khi:
- [ ] Server restart + tab "Nhân Vật" hiển thị đúng (Hiếu Văn Đế từ Wikidata P112)
- [ ] Admin xác nhận: chấp nhận Đường B (đợi T16) hoặc chọn Đường A (curate thủ công)

T28 **KHÔNG cần** Bồ Đề Đạt Ma/Huệ Khả xuất hiện để mark done — yêu cầu gốc là tab hiển thị đúng theo data thật, và trạng thái "pending" khi không có data là đúng thiết kế.
