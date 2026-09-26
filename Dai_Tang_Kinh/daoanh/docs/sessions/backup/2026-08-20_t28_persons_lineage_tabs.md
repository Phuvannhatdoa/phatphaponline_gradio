# 2026-08-20 — T28: Nhân Vật + Truyền Thừa tabs

## Mô tả ngắn task

User yêu cầu: case Thiếu Lâm Tự phải trả về "Nhân Vật" liên quan (kỳ vọng cụ thể: Bồ Đề Đạt Ma,
Huệ Khả). Thêm tab "Nhân Vật" liệt kê Person ID liên quan tới 1 địa danh; thêm tab "Truyền Thừa"
vẽ cây phả hệ Marcus/DILA ID của 1 vị khi click từ tab Nhân Vật.

## Phân tích — theo đúng quy trình 3 bước bắt buộc (docs/trusted-sources.md, cập nhật 2026-08-19)

Trước khi build, research lại (không đoán) xem có nguồn nào trong 15 nguồn uy tín đã import chứa
liên kết person↔place hay không:

- Kiểm tra schema `places`, `places_dila`, `people`, `marcus_reference`, `marcus_networks`
  (`PRAGMA table_info`) — xác nhận **0 cột** nối person↔place ở bất kỳ bảng nào (lặp lại xác nhận
  đã làm ở T16, kiểm tra lần nữa cho chắc trước khi khẳng định với user).
- DILA `places_dila` — không có `persName` cấu trúc (chỉ placeName/location/note/listBibl).
- Marcus — chỉ person↔person (teacher/student), không có trường place.
- BDRC — ontology có `bdo:placeEvent` (đúng khái niệm) nhưng chưa populate cho địa danh Hán truyền
  trong DB (T18 adapter status inactive, 1 entry).

**Mở rộng ra ngoài (bước 2 trong quy trình):** dùng WebSearch + WebFetch tra Wikidata trực tiếp —
verify sống được: Thiếu Lâm Tự = Q232771, có property **P112 (founded by)** → Q1327614
(Bodhidharma). Đây là nguồn thật, có cấu trúc, đúng loại "mở rộng ra ngoài 15 nguồn" mà quy trình
cho phép — báo cáo phát hiện này công khai trong task file để admin duyệt.

**Vì sao KHÔNG tự seed Bồ Đề Đạt Ma/Huệ Khả ngay:**
1. Không có cầu nối DILA place_id ↔ Wikidata QID trong DB (kiểm tra xong, 0 cột liên quan) — nên
   không thể tự động hoá pipeline này ngay lập tức.
2. Xác định "DILA person ID nào là Bồ Đề Đạt Ma" trong `people` (48,673 dòng) là 1 dạng document
   interpretation: tìm thấy `A001573` (達摩菩提, dynasty 東魏) — tên bị đảo thứ tự chữ so với
   "菩提達摩" thường gặp, dynasty Đông Ngụy khớp khung thời gian truyền thống của Bồ Đề Đạt Ma
   nhưng KHÔNG đủ để tự khẳng định chắc chắn đây là cùng 1 người. Theo nguyên tắc đã thống nhất với
   admin ("document interpretation không tự làm mà không báo trước"), KHÔNG tự gán mà để admin xác
   nhận.
3. Huệ Khả (慧可) — tìm bằng LIKE trong `people.name_zh` không ra kết quả khớp trực tiếp (chỉ ra
   2 người khác có "慧可" là substring của tên dài hơn, không phải Huệ Khả thật) — cần tra thêm.

## Thiết kế đã build

1. Bảng mới `place_person_link(place_id, person_id, relation_type, source_name, source_url, note,
   added_by, created_at)` — additive, curated. `source_name`+`source_url` **bắt buộc** ở tầng API
   (từ chối insert nếu thiếu) — cùng mô hình tin cậy với `custom_hanviet_override` (T08): con người
   (admin hoặc AI có trích dẫn thật) chịu trách nhiệm từng dòng, không phải thuật toán đoán.
2. API `GET /daoanh/api/places/<id>/persons` — đọc bảng trên, JOIN `people` lấy tên/dynasty, check
   `marcus_people_link` để gắn badge "🌳 TRUYỀN THỪA" nếu person đó có dữ liệu Marcus. Rỗng → trả
   `status:"pending"` + `research_directions` (đúng convention endpoint `/timeline` T21 đã dùng),
   không giả vờ có dữ liệu.
3. API `POST /daoanh/api/admin/place-person-link` — thêm 1 dòng curated.
4. `places.html` — 2 tab mới: "🧑 Nhân Vật" (`renderPersonsTab`) và "🌳 Truyền Thừa"
   (`renderLineageTab`, tách khỏi "Đồ Thị" cho rõ vai trò: Đồ Thị = luôn về ĐỊA DANH, Truyền Thừa =
   luôn về 1 NHÂN VẬT). Refactor `_renderVisGraph()` dùng chung cho cả 2 tab (giảm trùng lặp code
   vis-network). Click person-row ở tab Nhân Vật → `selectPerson()` → tự chuyển tab Truyền Thừa +
   vẽ cây (click node thầy/trò trong cây → lazy load node kế tiếp, verify lại từ T17).

## Danh sách file đã tạo/sửa

- `app.py` — bảng `place_person_link`, API `api_places_persons`, `api_admin_place_person_link_add`
- `places.html` — 2 tab mới + panel, `renderPersonsTab`, `renderLineageTab`, `_renderVisGraph`
  (refactor dùng chung), `renderGraphTab` rút gọn lại place-only, cập nhật reset loop/loadTabData
- `tasks/T28-place-person-lineage.md` (mới)
- `docs/tasktodo.md` — thêm Task 28
- `docs/sessions/2026-08-20_t28_persons_lineage_tabs.md` — session log này

## Test đã chạy

```
GET /daoanh/api/places/PL000000023255/persons
  -> status=pending, persons=[], research_directions gồm 3 hướng (Wikidata/BDRC/admin curation)
GET /daoanh/api/places/PL000000023255/graph   -> không đổi, vẫn đúng (place-only)
GET /daoanh/api/monk/A000005/graph            -> không đổi, vẫn đúng (person lineage)
```

Browser thật (Claude Browser tool):
- `node --check` trên toàn bộ script JS trước khi test — pass, không lỗi cú pháp.
- `selectItem('PL000000023255')` → tab Nhân Vật hiện đúng trạng thái pending + 3 hướng nghiên cứu.
- Tab Đồ Thị vẫn vẽ graph địa danh đúng (437 ký tự HTML canvas, không hồi quy).
- Tab Truyền Thừa khi đang ở place mode → placeholder đúng ("Chọn 1 tăng nhân...").
- `selectPerson('A000005', '鑑堂一')` → tự chuyển active tab sang "lineage", header đổi
  "· TĂNG NHÂN · DILA", canvas Truyền Thừa vẽ đúng (437 ký tự).
- Không có console error mới sau toàn bộ luồng test.

## Việc cần làm tiếp — chờ admin quyết định

1. Xác nhận `A001573` (達摩菩提, 東魏) có phải Bồ Đề Đạt Ma không — nếu có, sẽ thêm dòng
   `place_person_link` cho Thiếu Lâm Tự với `source_url` trỏ Wikidata Q232771.
2. Tìm ID thật của Huệ Khả trong `people` (chưa match bằng LIKE trực tiếp).
3. Nếu muốn tự động hoá quy mô lớn hơn thay vì curate thủ công từng dòng: cần xây bridge DILA
   place_id ↔ Wikidata QID — 1 task ETL riêng, không nhỏ (đòi hỏi chuẩn hoá tên + verify tránh
   trùng), ngoài scope của T28 hôm nay.
4. `docs/trusted-sources.md` — đề xuất admin duyệt bổ sung dòng "Wikidata — place↔person founding
   relation" vào ma trận tích hợp (hiện chỉ ghi Wikidata cho mục đích timeline).

## Liên hệ ROADMAP

- Phụ thuộc: T04 (Marcus link), T17 (graph tab + vis-network hạ tầng)
- Liên quan: T16 (Nexus Points — vẫn là hướng "đúng" dài hạn để có person↔place từ CBETA TEI thật,
  không qua Wikidata bridge)

## Cập nhật (cùng ngày, sau khi hội thoại bị gián đoạn do usage limit) — build xong bridge + ĐÍNH CHÍNH

User chọn hướng "ưu tiên xây bridge Wikidata thật" (không gán tạm A001573). Đã build xong:
`geo_cross_ref` (bridge table, đúng schema T21 đã duyệt sẵn — phát hiện phiên dev khác đã seed
song song 148 dòng qua SPARQL batch trong lúc tôi làm việc khác), `_fetch_wikidata_founders()`
(fetch sống P112, cache 24h), gộp vào `GET /daoanh/api/places/<id>/persons`.

**Bug gặp khi test sống:** Wikidata trả 403 do thiếu header `User-Agent` (chính sách Wikimedia bắt
buộc) — đã sửa, verify lại 200 OK.

**Đính chính quan trọng — tự phát hiện sai sót trong research trước đó của chính tôi:** dòng 22-25
ở trên ghi "P112 → Q1327614 (Bodhidharma)" — **SAI**. Test sống (không phải đoán) xác nhận
`Q1327614` = **Bắc Ngụy Hiếu Văn Đế** (Emperor Xiaowen, vị hoàng đế đã cho xây Thiếu Lâm Tự năm 495
CE), không phải Bồ Đề Đạt Ma. Đã rà toàn bộ property khác của Q232771 — không property nào trỏ tới
Bồ Đề Đạt Ma. Kết luận: bridge Wikidata hoạt động đúng và trả dữ liệu thật, nhưng dữ liệu thật đó
**không phải** thứ user kỳ vọng (Đạt Ma/Huệ Khả) — Wikidata không có quan hệ này ở dạng cấu trúc.
Case Thiếu Lâm Tự với Đạt Ma/Huệ Khả giờ chỉ còn 1 đường: admin curate thủ công qua
`place_person_link` với 1 nguồn trích dẫn khác (không phải P112). Chi tiết đầy đủ + acceptance
criteria cập nhật: `tasks/T28-place-person-lineage.md`.

Test browser: chọn Thiếu Lâm Tự → tab Nhân Vật hiện đúng "Bắc Ngụy Hiếu Văn Đế" với link Wikidata
thật, nhãn rõ "chưa xác minh DILA ID nên chưa xem được Truyền Thừa" — không console error mới.
