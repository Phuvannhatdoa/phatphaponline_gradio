---
id: T482
title: "Thêm tab Catalog (namevimap.html) — danh mục địa danh DILA đầy đủ 59.373, additive"
status: in_progress
created: 2026-10-28
updated: 2026-10-28
owner: coordinator
module: Admin UI / Places / Identity
priority: medium
depends_on: [T477, T465, T466]
done_when: >
  (1) Bảng additive `place_catalog` tạo và nạp đủ 59.373 dòng (59.167 places_dila +
      206 dila_place_authority, 0 trùng id), có backup trước khi ghi + dry-run trước --apply.
  (2) API mới `/daoanh/api/places/catalog` (GET) trả place_id/Hán tự/name_vi hiện tại
      (namevi_map_places)/Claude (codex_place_name)/Gemini (ai_place_name)/Từ điển
      (đa nguồn, nội dung đầy đủ)/Kết luận — không đổi API/route cũ của Tab Place.
  (3) Tab "Catalog" trong admin/namevimap.html hiển thị đúng 8 cột yêu cầu; nút Kết luận/
      Sửa gọi lại ĐÚNG /daoanh/api/places/vi-map/<id>/approve và /edit hiện có (không tạo
      cơ chế mới).
  (4) Cột Từ điển: tra lexicon (166.278 dòng, 20 nguồn) theo name_zh khớp chính xác (term)
      + substring (definition, sau khi bỏ khoảng trắng OCR giữa ký tự Hán); ưu tiên nguồn
      "Tu Dien Thien Tong Han Viet - Han Man - Thong Thien" (Thông Thiền); hiển thị TOÀN BỘ
      nội dung tra được kèm tên nguồn (không chỉ dấu ✓).
  (5) Đã tìm "Từ Điển Đại Tạng Kinh của Nguyễn Minh Tiến" trong translation_glossary (79),
      term_glossaries (18.127, source='marcus' duy nhất), glossary_term/glossary_vi
      (248.095, source_id=6='Wikidata'), monk_dict (2), dila_reference (1.000),
      data_sources (16 nguồn) — KHÔNG thấy bộ từ điển này. Có `cbeta_catalog_vn` ghi chú
      "Nguyễn Minh Tiến" nhưng đó là MỤC LỤC sutra (Mục lục Đại Tạng Kinh, 3.122 dòng,
      khoá theo title_vi/translator, KHÔNG phải từ điển thuật ngữ theo name_zh) — không
      dùng được cho cột Từ điển. Ghi rõ trong report, không bịa dữ liệu.
  (6) Browser verify thật (127.0.0.1:8080): mở namevimap.html, click tab Catalog, chụp
      before/after, lấy network log của API catalog.
  (7) docs/tasktodo.md cập nhật; daoanh-qa / Admin xác nhận DONE sau.
revert: >
  `python -X utf8 scripts/t482_build_place_catalog.py --revert` (DROP TABLE place_catalog,
  additive nên 0 mất dữ liệu bảng gốc). Khôi phục code namevimap.html/routes_places.py qua
  git diff nếu cần (chưa commit, giữ trong working tree theo yêu cầu).
---

## Mô tả
Tab Place hiện tại (namevimap.html) chỉ liệt kê 59.167 địa danh từ `places_dila`. Admin cần
xem và duyệt được TOÀN BỘ danh mục DILA, bao gồm 206 địa danh mới nạp ở `dila_place_authority`
(T453/T477) chưa có trong `places_dila`. Task này thêm tab "Catalog" riêng (additive), không
đổi DB/API/UI của Tab Place.

## Thiết kế
- Bảng mới `place_catalog` (place_id PK 12 số, name_zh, source_table, created_at) — chỉ là
  khoá canonical hợp nhất, KHÔNG denormalize Claude/Gemini/Từ điển/name_vi (các giá trị này
  đổi khi Admin Pass/Sửa, denormalize sẽ lệch).
- API `/daoanh/api/places/catalog` JOIN SỐNG `place_catalog` với `namevi_map_places`
  (name_vi hiện tại), `codex_place_name` (Claude), `ai_place_name` (Gemini), tra `lexicon`
  (Từ điển, đa nguồn ưu tiên Thông Thiền).
- Nút Kết luận/Sửa dùng lại `/daoanh/api/places/vi-map/<id>/approve` và `/edit` (không tạo
  endpoint approve/edit riêng cho Catalog).

## Giới hạn đã biết
- 206 dòng `dila_place_authority` CHƯA có dòng tương ứng trong `namevi_map_places` ⇒
  /approve và /edit trả 404 ("chưa thể Pass... Dùng Sửa để tạo trước" / "giai đoạn 1 chỉ
  UPDATE, không tạo dòng mới") cho tới khi có dòng `namevi_map_places` cho các ID này — đây
  là hành vi THẬT của 2 endpoint cũ (không sửa), ghi rõ trong report, không patch endpoint.
- Không tìm thấy "Từ Điển Đại Tạng Kinh của Nguyễn Minh Tiến" trong DB (xem done_when #5).
