---
id: T486
title: "Catalog + work metadata: làm rõ quan hệ dữ liệu tác phẩm (5.747 bộ), nguồn chuẩn tiếng Việt, liên kết và quan hệ quyển"
status: in_progress
created: 2026-10-29
updated: 2026-10-29
owner: coordinator
module: Data / Catalog / Work metadata
priority: high
depends_on: [T482, T484, T485]
done_when: >
  (1) Sơ đồ quan hệ dữ liệu tác phẩm được viết và kiểm bằng số liệu thật: bảng dila_catalog_works,
      dila_catalog_contributors, dila_catalog_places, cbeta_catalog_vn, canon_catalog, kanripo_catalog,
      và bộ file gốc data/dila_import/authority_catalog.2026-10/ (json/ và vn_dila_authority_catalog/).
  (2) Admin chọn nguồn chuẩn cho tên Việt (title_vi, byline_vi, contributor name_vi) giữa DB hiện tại và
      file vn_dila_authority_catalog/*.vi.json. Chưa chọn thì không ghi đè.
  (3) Số liệu chồng lấp và lệch được đo lại và ghi báo cáo: 124 title_vi, 1.562 byline_vi, 1.870 contributor
      name_vi (DB khác file vi.json); 13 title_vi và 33 byline_vi còn chữ Hán sót.
  (4) Liên kết với cbeta_catalog_vn (Mục Lục NMT) và canon_catalog được đo bằng khớp tên Hán chuẩn hoá;
      báo số khớp một-một, khớp nhiều, không khớp. Không tự ghi liên kết khi còn mơ hồ.
  (5) Quan hệ quyển: vol có 68 dải (ví dụ A097..A098), juans thiếu 36 dòng. Xác định có nguồn nào cho danh
      sách quyển không. Nếu không có, nêu rõ thiếu gì và đề xuất bảng additive (chờ Admin duyệt schema).
  (6) Mọi thay đổi ghi DB: dry-run trước, backup trước, Admin --apply. Không git add/commit/reset.
  (7) QA (daoanh-qa) kiểm số liệu trước/sau. Admin xác nhận DONE.
---

## Mô tả

Catalog đã có 5.747 bộ, nhưng quan hệ giữa các bảng và các nguồn chưa được làm rõ. Task này đo đạc
quan hệ thật, chỉ ra chỗ lệch giữa DB và file gốc, và đề xuất cách nối dữ liệu. Không ghi DB trong pha đo.

## Kết quả đo ban đầu (2026-10-29, chỉ đọc)

### Khóa định danh
- `dila_catalog_works.cbeta_id`: khóa CBETA dạng T0785, X0989, B0005 (không phải A1057 như mẫu ban đầu).
- `dila_catalog_works.authority_id`: mã DILA CA0000745 (100% điền).
- `dila_catalog_works.vol`: tập Taisho/CBETA (T17), có 68 dải (C056..C057, A097..A098).
- `cbeta_catalog_vn` (Mục Lục NMT) và `canon_catalog`: không có cbeta_id, text_code, sigla hay cbeta_ref
  điền được. Liên kết phải dựa vào tên Hán.

### Quan hệ với bảng khác
| Bảng | Số dòng | Khóa nối | Ghi chú |
|---|---|---|---|
| dila_catalog_contributors | 5.589 (4.321 works) | cbeta_id + person_id (A…) | 7 dòng person_id null |
| dila_catalog_places | 765 (723 works) | cbeta_id + place_id (PL…) | lat/long điền sẵn |
| cbeta_catalog_vn | 3.122 | không có khóa, chỉ tên Hán | khớp title_vi 842 dòng |
| canon_catalog | 3.122 | cbeta_id toàn NULL trong mẫu | chưa nối được |
| kanripo_catalog | 101 | dila_ref, cbeta_ref | chưa đo |

### Nguồn tiếng Việt và chênh lệch
- File gốc: `data/dila_import/authority_catalog.2026-10/json/*.json` (26 nhóm, 5.747 bản ghi). Các trường
  khớp đúng với DB: authorityID, title, vol, type, juans, cjk_chars, category, byline, dynasty, time_from,
  time_to, contributors, places, orig_category, alt, en_words. Không có trường toàn văn (fulltext).
- File dịch: `vn_dila_authority_catalog/*.vi.json` (32 file, 26 nhóm). Có title_vi, byline_vi, dynasty_vi,
  category_vi, contributors[].name_vi, kèm trạng thái và nguồn từng trường (ai / table). Tất cả
  `unreviewed`.
- DB: vi_status = unreviewed cho 5.747 dòng. Khớp file vi.json ở dynasty_vi và category_vi (5.747/5.747).
  Lệch ở title_vi 124, byline_vi 1.562, contributor name_vi 1.870.
- Lệch có cả chữ hoa/dấu (ví dụ "đến" và "Đến") và lệch nội dung (ví dụ A004850: DB "Phạm Cổ Nông", file
  "Phạm Ký Đông"; A016340: DB "Phật Âm", file "Giác Âm"). Phải phân loại trước khi quyết định.
- Chữ Hán sót trong bản Việt: 13 title_vi, 33 byline_vi (ví dụ "Hạ 丏 Tôn").

### Quan hệ quyển
- Không có bảng quyển trong DB và không có danh sách quyển trong file gốc. `juans` chỉ là số quyển.
- 36 dòng juans null, 1 dòng type null, 116 dòng non-textbody.

## Phạm vi task

1. **Đo chi tiết** từng trường lệch: phân loại chữ hoa/dấu, chữ Hán sót, khác nội dung. Đầu ra là file CSV
   trong docs/sessions/2026-10-29/work-metadata/.
2. **Chọn nguồn chuẩn** (Admin quyết định): đề xuất file vi.json cho title/byline/contributor vì có
   trạng thái và nguồn từng trường; DB giữ nguyên cho đến khi Admin duyệt.
3. **Dọn chữ Hán sót** trong bản Việt: đưa danh sách 46 dòng cho Admin, không tự đoán âm.
4. **Liên kết cbeta_catalog_vn và canon_catalog** theo tên Hán chuẩn hoá (bỏ chú thích quyển trong ngoặc).
   Báo số một-một, nhiều-một, không khớp. Ghi bảng đề xuất, không ghi liên kết chính thức.
5. **Quan hệ quyển**: xác định dải vol có nghĩa gì (A097..A098 là hai tập), tách thành danh sách tập.
   Nếu cần bảng mới (ví dụ `dila_work_volume`), đề xuất schema additive và chờ Admin duyệt.
6. **Kiểm chứng**: đếm lại trước/sau; QA chạy lại các số liệu ở mục "Kết quả đo ban đầu".

## Quyết định cần Admin

- Nguồn chuẩn cho tên Việt: DB hiện tại hay file vn_dila_authority_catalog (đề xuất: file vi.json).
- 1.870 contributor name_vi lệch: chọn theo file, theo DB, hay Admin duyệt từng dòng.
- Có tạo bảng additive cho danh sách tập/quyển không (chỉ khi có nguồn quyển).

## Ràng buộc

- Chỉ đọc khi đo. Ghi DB chỉ sau dry-run và Admin --apply, có backup trước.
- Không đổi khóa cbeta_id hay authority_id.
- Không git add/commit/reset khi chưa có lệnh rõ ràng.
- Test bằng 127.0.0.1, không dùng localhost.
- Quy tắc nguồn: DILA=1 (tên Hán), ZQLOCAL=5 (tên Việt). Bản Việt từ file vi.json ghi nguồn "ai" hoặc
  "table" theo từng trường, giữ nguyên trong vi_json.

## Phần việc đang làm (2026-10-29) — Tab "Xác minh tác giả"

Triển khai cụ thể mục (2)/(3) của done_when: cho Admin xem và Pass từng người (contributor
name_vi lệch), thay vì ghi đè hàng loạt. Scope:

1. Endpoint chỉ đọc `GET /daoanh/api/admin/work-verify` (group=C|B|A|ALL, page, size, q) — gom
   từ `docs/sessions/2026-10-29/work-metadata/t486_dryrun.csv` hoặc tính lại từ DB + vi.json.
2. Endpoint `POST /daoanh/api/admin/work-verify/<person_id>/pass` — ghi tên Việt đã duyệt cho
   đúng person_id, theo đúng cơ chế ghi hiện có trong `routes_namevi.py` (không tự chế cột mới).
   Yêu cầu header `X-Session-Token`; approved_by/approved_at.
3. UI: thêm tab mới trong `admin/namevimap.html` (không sửa tab Catalog/ETL/Place hiện có),
   class dùng lại `etl-flag-pass`, `etl-ba-table`. Lọc nhóm + tìm kiếm + phân trang 50 dòng.
4. Backup trước khi sửa: `docs/sessions/2026-10-29/namevimap.html.before-t486-verify`,
   `docs/sessions/2026-10-29/routes_namevi.py.before-t486-verify` (hoặc file route mới).
5. Không bấm Pass thật trong lúc build — chỉ kiểm cú pháp + GET endpoint qua 127.0.0.1.

Giao cho `daoanh-debugger` thực hiện; `daoanh-qa` kiểm sau; Admin xác nhận DONE và tự thử Pass.

## Liên quan

- T482: tab Catalog và place_catalog.
- T484: tab Catalog cho tên Kinh (dila_catalog_works), HVDic, Gemini Free.
- T485: tích hợp Dila ID Person và Place vào tab Catalog.
- Kế hoạch chi tiết: docs/plans/T486-catalog-work-metadata-relations.md.
