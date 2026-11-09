# Audit (read-only) — A000001 Kim Tổng Trì

Ngày: 2026-10-26 · Mode: sqlite `mode=ro`, không ghi DB, không sửa code.

## 1. Bảng chứa A000001 trong `data/lineage.db`

`dila_reference`, `people`, `entity`, `person_origin_link`, `dila_catalog_contributors`,
`codex_person_name`, `canon_catalog.author_dila_id` (56 dòng), `marcus_people_link`
(qua `people.id`). Không thấy trong `cbeta_person_mentions`, `passage_entity_mention`,
`event_text_link`, `dila_catalog_works.authority_id`.

## 2. Đối chiếu từng nhóm

| Nhóm | CÓ/THIẾU | Bảng/cột | Giá trị DB (rút gọn) |
|---|---|---|---|
| dynasty | CÓ | `people.dynasty`, `dila_reference.dynasty` | `北宋` |
| concise_bio (Hán) | CÓ, khớp nguyên văn | `people.bio`, `dila_reference.bio` | "北宋譯經僧。西天竺人。皇祐五年…" khớp 100% text user đưa |
| places_of_origin | CÓ | `person_origin_link` (person_id='A000001', place_id='PL000000055425', confidence=1.0) | map tới place record, không lưu chuỗi "西天竺" trực tiếp nhưng resolver trả đúng |
| works_in_tripitaka | CÓ (một phần) | `dila_catalog_contributors` (3 dòng: A1504, T0763, T1188, role=contributor, name_vi="Kim Tổng Trì") | khớp 3/3 mã CBETA user liệt kê |
| cbeta_citations (passage-level) | THIẾU | — | không có dòng nào trong `cbeta_person_mentions`/`passage_entity_mention` cho A000001; 3 ref (T15n0634, T17n0763, X77n1524) không có trong DB |
| xml_sha256 | CÓ | `codex_person_name.xml_sha256` | `c21bf281…1004fa8c`, nguồn `claude-xml-import@0d2ea40`, status=`suggested` |

## 3. XML nguồn

`data/dila_import/authority_person.2026-10/Buddhist_Studies_Person_Authority.xml`
(và 2 bản sao cũ ở `Authority-Databases*`). `grep -c "A000001"` = 3 lần xuất hiện —
xác nhận nguồn gốc import đúng.

## 4. API / UI

Route `/daoanh/api/person/<dila_id>/profile` (app.py:8273). Test thực tế qua
`curl http://127.0.0.1:5000/daoanh/api/person/A000001/profile` (server đang chạy) —
trả `ok:true`, `profile.bio/dynasty/name_vi` đúng; `places` có 1 mục
("sinh tại / 籍貫" → PL000000055425, nguồn DILA Person Authority); nhưng
`texts: []` và `mentions.text_count: 0`.

**Nguyên nhân texts rỗng:** route chỉ query `place_person_bibl` (0 dòng cho
A000001) và `cbeta_person_mentions` (0 dòng) — **không query** `dila_catalog_contributors`
hay `canon_catalog`, nên 3 tác phẩm (A1504/T0763/T1188) tồn tại trong DB nhưng
API/UI không bao giờ trả về → trang person không hiển thị works_in_tripitaka,
không phải vì thiếu data mà vì **API contract thiếu field này**.

**cbeta_citations thiếu ở gốc**: không có trong DB, không có trong ETL import
hiện tại (chỉ `dila_catalog_contributors` lưu work code, không lưu passage-level
citation như T15n0634_p0485c11). Cần tích hợp thêm nguồn CBETA citation riêng,
không phải lỗi API/UI.

## 5. Phát hiện ngoài phạm vi (ghi nhận, không sửa)

`canon_catalog` có 56 dòng `author_dila_id='A000001'` nhưng `author_vi`/`author_zh`
= **An Thế Cao (安世高, 後漢)** — khác hoàn toàn Kim Tổng Trì (北宋). Nghi ngờ
sai mapping `author_dila_id` trong `canon_catalog` (có thể do import cũ gán nhầm
ID dùng tên, hoặc trùng ID do nguồn khác). Không sửa trong audit này — cần task
riêng để xác minh & dry-run fix.

## Kết luận

- dynasty, concise_bio, places_of_origin, xml_sha256: CÓ đầy đủ trong DB, hiển
  thị đúng qua API/UI đã test.
- works_in_tripitaka: CÓ trong DB (`dila_catalog_contributors`) nhưng **API
  không trả, UI không hiển thị** — lỗi ở lớp API contract (thiếu query), không
  phải data.
- cbeta_citations (passage-level): **thiếu từ gốc**, chưa có import nguồn này
  vào DB — cần đề xuất ETL mới, Admin duyệt dry-run trước khi nạp.
- Phát hiện thêm: khả năng sai `author_dila_id` cho 56 dòng `canon_catalog`
  (An Thế Cao bị gán ID của Kim Tổng Trì) — đề nghị mở task riêng kiểm tra.
