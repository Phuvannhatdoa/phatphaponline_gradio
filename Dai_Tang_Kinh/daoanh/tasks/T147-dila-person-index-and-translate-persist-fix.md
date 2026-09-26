---
id: T147
title: "DILA Person Index (mirror DILA Place Index) + fix bug hidden/flex CSS chặn AI translate persist trong person.html"
module: admin
priority: high
status: done
depends_on: [T145, T73, T123]
created: 2026-09-16
updated: 2026-09-16
done_when:
  - "[x] Tab/nav-btn 'DILA Person Index' nằm cạnh 'DILA Place Index' trong admin/index.html"
  - "[x] admin/dila_person_index.html: search/filter (tông phái, triều đại, trạng thái dịch)/pagination/CSV/JSON export — UX tương đương dila_index.html"
  - "[x] Backend GET /daoanh/api/dila/persons + GET /daoanh/api/dila/persons/stats (additive, 0 ALTER, đọc people + translation_cache)"
  - "[x] Click record trong Person Index mở đúng /daoanh/admin/person.html?id=<PERSON_ID>"
  - "[x] Root cause xác nhận: CSS bug [hidden]+flex utility (Tailwind CDN) trong person.html khiến #bio-vi-edit-actions/#report-bar luôn hiện dù JS set hidden=true"
  - "[x] Fix: thêm rule [hidden]{display:none!important} vào <style> person.html"
  - "[x] Test A009462: Dịch AI (draft, translation_cache status=auto) → Sửa → Lưu (status=edited + people.bio_vi) → refresh → vẫn hiển thị đúng nội dung đã lưu"
  - "[x] DILA Person Index phản ánh đúng trạng thái sau lưu (badge '✓ Đã lưu')"
  - "[x] DILA Place Index + person editor cũ không regression (browser verify, network 200, 0 lỗi console mới)"
---

## Bối cảnh

Admin cần một trang duyệt Person tương đương DILA Place Index (`admin/dila_index.html`)
để theo dõi tiến độ dịch Hán→Việt của 48,673 person records, và xác nhận bug
báo cáo "AI tạm dịch tại person.html không lưu bền vững vào DB".

## Audit / Root cause

1. **DILA Person Index chưa tồn tại** — `admin/index.html` chỉ có nav-btn
   "DILA Place Index" (dòng 424), không có tương đương cho Person.
2. **AI translate draft**: `POST /daoanh/api/person/<id>/translate` (app.py:15565)
   ĐÃ ghi draft vào `translation_cache` (status='auto') ngay khi gọi — persist
   đúng thiết kế (T123/T73), KHÔNG phải bug.
3. **Save/Apply chính thức**: `POST /daoanh/api/admin/person/<id>/bio_vi`
   (app.py:15633, T145) ĐÃ ghi `translation_cache.status='edited'` +
   `people.bio_vi` — logic backend đúng.
4. **Bug thật nằm ở frontend `admin/person.html`**: `#bio-vi-edit-actions`
   (nút 💾 Lưu / Hủy) và `#report-bar` dùng `hidden class="... flex ..."`.
   Tailwind CDN load utility layer (`.flex{display:flex}`) SAU base layer
   (`[hidden]{display:none}`) trong cùng cascade layer order → cùng specificity
   (0,1,0) → utility thắng theo thứ tự nguồn → **`hidden` attribute bị vô hiệu
   hoá bất cứ khi nào element có class display-utility cùng lúc**.
   Hệ quả quan sát được: nút "💾 Lưu" hiện SẴN ngay cả khi chưa bấm "✏ Sửa"
   (editMode=false), textarea vẫn hidden đúng (không có class display-utility
   compete) → nếu admin bấm nhầm nút Lưu "ma" này trước khi vào edit mode,
   `bio-vi-textarea.value` rỗng → save bị chặn bởi validation
   ("Nội dung không được để trống") — tạo cảm giác "AI dịch xong nhưng Lưu
   không có tác dụng / không thấy lưu được".

## Fix

### Backend (`app.py`, additive, 0 ALTER)

- `GET /daoanh/api/dila/persons?q=&sect=&dynasty=&status=&limit=&offset=&format=`
  — mirror `/daoanh/api/dila/places`; status ∈ `translated|draft|none` lọc theo
  `people.bio_vi` + `translation_cache` (subquery lấy status mới nhất per
  entity_id, source_type='person_bio', loại 'invalidated').
- `GET /daoanh/api/dila/persons/stats` — mirror `/daoanh/api/dila/stats`;
  trả `total/with_bio_zh/translated_saved/translated_draft/by_category
  (sect)/by_country (dynasty)`.
- **Bug tự phát hiện khi code**: filter `status` ban đầu nối chuỗi
  `f"...ON tc.entity_id=p.id {where_sql}{status_having}"` — khi `where_sql`
  rỗng, `AND ...` bị SQLite hiểu là mở rộng điều kiện `ON` của LEFT JOIN thay
  vì `WHERE`, khiến filter vô hiệu (LEFT JOIN vẫn giữ toàn bộ dòng trái).
  Sửa: đưa toàn bộ status filter vào cùng `where` list trước khi build
  `where_sql`, đảm bảo luôn có `WHERE` thật. Verify: `status=translated` →
  total=1 (đúng, A002233), `status=draft` → total=1 (đúng, A009462),
  `status=none` → total=48671 = 48673-2.

### Frontend

- **`admin/dila_person_index.html`** (mới) — clone cấu trúc/CSS/JS pattern
  của `dila_index.html` (topbar, filter-row, stats-row, table, pagination,
  export CSV/JSON), đổi cột: DILA ID/Tên Hán/Tên Việt/Tông phái/Triều đại/
  Năm sinh–mất/**Trạng thái dịch** (badge Đã lưu / Nháp AI / Chưa dịch /
  Không có Hán văn). Link row → `/daoanh/admin/person.html?id=<id>`. Có auth
  guard giống `person.html` (admin_session + `/api/login/check`).
- **`admin/index.html`** — thêm nav-btn "DILA Person Index" ngay sau
  "DILA Place Index" (dòng ~424-436).
- **`admin/person.html`** — thêm 1 CSS rule `[hidden]{display:none!important}`
  đầu `<style>` để khôi phục đúng ngữ nghĩa `hidden` bất kể class Tailwind nào
  đi kèm. Không đổi JS logic (state machine editMode/textarea/edit-actions
  giữ nguyên, chỉ là rendering giờ khớp đúng state).

## Test

- `python -m py_compile app.py` — PASS.
- curl trực tiếp `/api/dila/persons` (list/search/status filter) +
  `/api/dila/persons/stats` — PASS, số liệu khớp DB (xem session log).
- Browser thật (Claude Browser tool), case A009462:
  1. `admin/index.html` → click "DILA Person Index" → load đúng danh sách,
     stats, filter dropdown (tông phái/triều đại) populate từ API.
  2. Search "A009462" → 1 kết quả, badge "✎ Nháp AI (auto)" (draft đã có sẵn
     từ trước — status=auto trong translation_cache).
  3. Click ID → mở `person.html?id=A009462` — bio Hán + bio Việt (draft) hiện
     đúng, nút "🔄 Dịch lại (rules mới)".
  4. Trước fix CSS: `#bio-vi-edit-actions` (Lưu/Hủy) HIỆN SẴN dù `editMode=false`
     — confirm bug bằng `getComputedStyle(el).display === 'flex'` trong khi
     `hasAttribute('hidden') === true`.
  5. Sau fix: reload — Lưu/Hủy KHÔNG hiện ở view mode; chỉ hiện đúng lúc bấm
     "✏ Sửa".
  6. Bấm "✏ Sửa" → sửa text (chèn marker `[QA-T146-verify]` — đặt trước khi
     phát hiện T146 đã bị dùng bởi task khác nên đổi số thành T147; marker
     text trong DB giữ nguyên chuỗi gốc đã lưu, không sửa lại) → bấm "💾 Lưu"
     (real click, tọa độ tính từ `getBoundingClientRect()`) → network
     `POST /daoanh/api/admin/person/A009462/bio_vi` → 200
     `{"ok":true,"status":"edited","translation_id":1744}`.
  7. Query DB trực tiếp: `people.bio_vi` chứa đúng text có marker;
     `translation_cache.id=1744.status='edited'`.
  8. Reload `person.html?id=A009462` — text đã lưu (kèm marker) hiển thị lại
     đúng từ DB (không phải state JS tạm) — **persist qua refresh xác nhận**.
  9. Quay lại DILA Person Index, search A009462 → badge đổi thành
     "✓ Đã lưu" (bio_vi_saved=1).
  10. Regression check: DILA Place Index (`dila_index.html`) vẫn load 59,167
      records bình thường; toàn bộ network request trong phiên test đều 200
      (0 lỗi 4xx/5xx mới). 1 console error tiền tồn tại ở `admin/index.html:756`
      (`animateValue`/`fetchDashboardStats`, dashboard stat card) — xác minh
      KHÔNG liên quan tới thay đổi của task này (nằm ngoài vùng code đã sửa).

## Limitation / theo dõi thêm

- Console error `admin/index.html:756` (`Cannot read properties of undefined
  (reading 'replace')`, trong `loadDashboard()`/dashboard cards) là bug tiền
  tồn tại, ngoài phạm vi T147 — nên audit riêng.
- Authorization: `admin/dila_index.html` (Place, cũ) hiện KHÔNG có client-side
  auth guard; `admin/dila_person_index.html` (mới) có thêm guard giống
  `person.html`. Không sửa `dila_index.html` cũ vì ngoài phạm vi yêu cầu (fix
  nhỏ nhất, tránh regression trang khác) — flag riêng nếu cần đồng bộ.
- API `/daoanh/api/dila/persons*` (đọc) chưa gate `verify_session` — đồng bộ
  với `/daoanh/api/dila/places*` hiện có (không có gate). Ghi write
  (`/api/admin/person/<id>/bio_vi`) đã có gate `verify_session` sẵn (T145).
