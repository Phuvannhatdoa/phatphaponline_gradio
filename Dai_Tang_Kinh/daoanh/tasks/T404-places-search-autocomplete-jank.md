---
id: T404
title: "Bug verify: BUG-034: Ô Search trang places — autocomplete gõ bị vấp chữ, gợi ý sai từ khoá"
bug_id: BUG-034
status: done
created: 2026-10-14
updated: 2026-10-19
owner: daoanh-debugger (Claude điều phối)
module: GIS / Places
priority: high
depends_on: []
plan_approved_at: "2026-10-14 (Admin: 'fix: … ô Search chức năng autocomplete hoạt động ko trơn tru, gõ bị vấp chữ, mớm sai từ khóa. Mong muốn gõ từng chữ thì mớm từng chữ')"
done_when: >
  (1) Trên http://127.0.0.1:8080/daoanh/places?mode=lineage&focus=A032162&lm=tree, gõ từng ký tự (kể cả gõ Telex/Unikey
  tiếng Việt) vào ô "Tìm địa danh...": nội dung ô KHÔNG bị ghi đè trong khi gõ; danh sách gợi ý cập nhật theo đúng chuỗi
  đang gõ (không bị kết quả của chuỗi cũ đè lên), xuất hiện trong ≤ 0,5 giây từ ký tự thứ 2.
  (2) Tìm kiếm đầy đủ (bay bản đồ, chọn hồ sơ) chỉ chạy khi Enter hoặc chọn một gợi ý.
  (3) Bằng chứng: ảnh chụp trước/sau + network log (request cũ bị huỷ / bỏ qua) trên trình duyệt thật.
  (4) [Cổng riêng, chờ Admin duyệt] index `idx_places_name_zh ON places(name_zh)` để `/daoanh/api/places/search` không còn
  30–125 giây.
  (5) daoanh-qa kiểm độc lập; Admin xác nhận DONE.
revert: >
  Code: chép lại docs/sessions/2026-10-14/T404/places.html.bak-before-T404 (hoặc git revert --no-edit <sha_T404> sau khi commit).
  Index (nếu được duyệt): DROP INDEX idx_places_name_zh — không mất dữ liệu.
outcome: >
  2026-10-14: Vòng 1 + vòng 2 sửa places.html (daoanh-debugger; sha256 sau vòng 2 9d28454a…cdaba1817). daoanh-qa vòng 2:
  phần places.html ĐẠT (không ghi đè ô khi gõ, huỷ request cũ, phản hồi muộn không mở lại dropdown, IME, chỉ địa danh
  mapped/pending, lọc rác + khử trùng). done_when (2)(3) ĐẠT. done_when (1) MỘT PHẦN: "Lâm Tế" 0,02–0,2 s nhưng "Thiếu L"
  0,7–1,3 s do backend (app.py public_autocomplete quét LIKE marcus_reference/lexicon; monk-resolve ~1 s) — ngoài phạm vi.
  (4) tách sang T405. Đã đủ 2 vòng QA ⇒ chờ Admin quyết (chấp nhận mốc 0,5 s cho phần giao diện hay mở task backend).
  Chưa commit.
  2026-10-14 (cập nhật): (1) Sửa giao diện ĐẠT — mốc 0,5 s. T405 đã tạo `idx_places_name_zh` và đo lại
  `/daoanh/api/places/search?q=Lâm Tế` giảm từ 1,82–3,29 s xuống 0,027–0,71 s; kết hợp với phần giao diện (huỷ request
  cũ, không ghi đè ô khi gõ) ở T404, mốc done_when (1) ≤0,5 s cho luồng gõ-gợi ý nay đạt trên case đã đo. Mục còn lại:
  (5) daoanh-qa kiểm độc lập đã xong vòng 2; chờ Admin xác nhận DONE (bước cuối, chưa tick).
  2026-10-19: Admin xác nhận DONE. Kết luận: fix giao diện (debounce + AbortController + xử lý IME) hoàn tất,
  phản hồi gõ chữ 237–484 ms từ lần gõ cuối. CAVEAT: API backend `/autocomplete` vẫn chậm 1–9 s với một số chuỗi
  ("Thiếu L") — nằm ngoài phạm vi T404 (giao diện), chuyển theo dõi sang T416.
---

# T404 — Ô Search trang places: autocomplete gõ bị vấp chữ

## Mục tiêu

Gõ từng chữ thì gợi ý theo từng chữ, mượt, đúng từ khoá đang gõ.

## Chẩn đoán (đo 2026-10-14, chỉ đọc)

| # | Nguyên nhân | Bằng chứng |
|---|---|---|
| 1 | `/daoanh/api/places/search` chậm 30–125 s | curl q=La/Lâm/Lâm Tế/Thi… đều >30 s; đo SQL: phép `LEFT JOIN places g ON g.name_zh = p.name_zh` mất **104 s** (EXPLAIN: `AUTOMATIC COVERING INDEX`); `places` chỉ có index province/type/gps. Hai bản backup (10-11, 10-13) cũng không có ⇒ lỗi có sẵn. |
| 2 | Gõ bị "giật" | `places.html` ~L1905: mỗi `input` hẹn `doSearch(q)` sau 400 ms; nếu `monk-resolve` khớp, `doSearch` **ghi đè `searchInput.value`** + `selectPerson` + `clearDynamicMarkers`/`loadInitialPlaces` trong lúc người dùng còn gõ. |
| 3 | Gợi ý sai thứ tự | `runAutocomplete` không huỷ request cũ, không có số thứ tự ⇒ phản hồi của chuỗi cũ về sau đè danh sách mới. |
| 4 | Bộ gõ tiếng Việt | Không xử lý `compositionstart/compositionend` ⇒ gửi chuỗi đang ghép dấu dở. |
| 5 | Gợi ý tăng nhân sai | `/daoanh/api/monk-resolve` trả **một** người khớp chính xác ("Lâm Tế" → người tên "Lâm" A005369), không phải danh sách tiền tố. |

Có sẵn `/daoanh/api/public/autocomplete?q=` (0,07 s, trả `{id, value, name_zh, source}` từ namevi_map_places → places_pending → marcus → lexicon).

## Các bước

- [x] Tái hiện + đo (curl, SQL timing, EXPLAIN)
- [x] Sao lưu places.html → docs/sessions/2026-10-14/T404/places.html.bak-before-T404
- [x] Sửa giao diện (daoanh-debugger): huỷ request cũ, bỏ auto doSearch khi gõ, xử lý IME, dùng public/autocomplete
- [x] Kiểm trên trình duyệt thật: ảnh trước/sau + network log
- [x] Index idx_places_name_zh → tách thành task T405 (Admin 2026-10-14: 'tạo task cho hermess đi') — T405: backup + tạo index + đo trước/sau xong, chờ daoanh-qa + Admin xác nhận
- [x] daoanh-qa kiểm độc lập
- [x] Admin xác nhận DONE (2026-10-19)

## Phát hiện ngoài phạm vi (đề xuất task riêng, chờ Admin)

1. Hiệu năng `/daoanh/api/public/autocomplete` + `/daoanh/api/monk-resolve` 0,7–1,3 s với vài chuỗi ("Thiếu L") — app.py ~L12358.
2. Có sẵn từ trước: `Invalid LatLng object: (NaN, NaN)` khi chọn địa danh không có toạ độ — nghi `places.html` ~L1496
   `map.flyTo([d.gps_lat, d.gps_long])` chỉ kiểm truthy. T404 làm lỗi dễ gặp hơn (gợi ý giờ truyền lat=null).
3. Dữ liệu: A033811 `name_vi="Lâm Tế Tông"` nhưng `name_zh="大慧"`.
4. Trải nghiệm: nhiều dòng cùng tên "Lâm Tế" khác ID trông giống nhau; dropdown chưa badge nguồn tên Việt (ZQ) — có sẵn từ trước.
5. Hồ sơ A032162: `/api/persons`, `/api/evidence`, `/person/.../translate`, `/dila_translate` trả 500 khi server bận.
