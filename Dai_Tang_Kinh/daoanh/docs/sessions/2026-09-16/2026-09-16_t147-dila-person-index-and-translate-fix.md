# Session — 2026-09-16 — T147: DILA Person Index + fix AI-translate persist bug

**Task:** `tasks/T147-dila-person-index-and-translate-persist-fix.md`
**Trạng thái:** DONE — code + browser verify xong, **chưa commit** (chờ lệnh user,
đúng quy tắc `CLAUDE.md` §"Git — KHÔNG tự ý chạy").

## Files changed

- `Dai_Tang_Kinh/daoanh/app.py` — thêm 2 route mới (additive, 0 ALTER):
  `GET /daoanh/api/dila/persons`, `GET /daoanh/api/dila/persons/stats`.
  Backup pre-edit: `docs/sessions/2026-09-16/app.py.bak-dila-person-index.py`.
- `Dai_Tang_Kinh/daoanh/admin/index.html` — thêm nav-btn "DILA Person Index".
  Backup: `docs/sessions/2026-09-16/admin_index.html.bak-dila-person-index.html`.
- `Dai_Tang_Kinh/daoanh/admin/dila_person_index.html` — **file mới**, clone UX
  của `dila_index.html`.
- `Dai_Tang_Kinh/daoanh/admin/person.html` — thêm 1 CSS rule
  `[hidden]{display:none!important}` fix bug Tailwind hidden/flex.
  Backup: `docs/sessions/2026-09-16/person.html.bak-hidden-css-fix.html`.
- `Dai_Tang_Kinh/daoanh/tasks/T147-dila-person-index-and-translate-persist-fix.md` — task file mới.
- `Dai_Tang_Kinh/daoanh/docs/tasktodo.md` — thêm entry T147.
- `Dai_Tang_Kinh/daoanh/data/progress_data.json` — regen qua
  `scripts/build_progress_data.py` (tự động, không sửa tay).

## Root cause đã xác minh

1. Chưa có trang browse Person tương đương DILA Place Index → thiếu feature,
   không phải bug.
2. AI draft translate (`POST /api/person/<id>/translate`) và Save chính thức
   (`POST /api/admin/person/<id>/bio_vi`, T145) **backend đã persist đúng**
   từ trước (translation_cache + people.bio_vi).
3. **Bug thật**: `admin/person.html` — `#bio-vi-edit-actions` và `#report-bar`
   dùng `hidden class="... flex ..."`. Tailwind CDN nạp utility layer sau base
   layer, cùng specificity (0,1,0) cho `.flex` vs `[hidden]` → utility thắng
   theo thứ tự cascade → nút 💾 Lưu/Hủy hiện SẴN dù `editMode=false` (JS set
   `hidden=true` không có tác dụng thị giác). Nếu admin bấm nhầm nút Lưu "ma"
   này (textarea rỗng vì chưa vào edit mode), request bị chặn bởi validation
   client-side → cảm giác "Lưu không hoạt động" dù backend hoàn toàn ổn.
4. Bug phụ tự phát hiện khi code endpoint mới: filter `status` nối chuỗi
   `AND ...` ngay sau `ON tc.entity_id=p.id` khi không có `WHERE` khác → SQLite
   hiểu thành mở rộng điều kiện JOIN thay vì lọc kết quả → filter vô hiệu.
   Đã sửa bằng cách đưa status-condition vào cùng danh sách `where` trước khi
   build `WHERE` clause.

## Thay đổi API/UI chính (before/after)

- **Trước**: không có endpoint/list nào cho Person tương đương
  `/api/dila/places`. **Sau**: `GET /api/dila/persons` + `/persons/stats`
  (contract mirror `/api/dila/places` + `/api/dila/stats`, thêm field
  `has_bio_zh/bio_vi_saved/draft_status`).
- **Trước**: `person.html` — `#bio-vi-edit-actions` render `display:flex`
  bất kể `hidden` attribute. **Sau**: `[hidden]` luôn thắng
  (`display:none!important`), JS state (editMode/textarea toggling) không đổi.

## Kết quả test

- `python -m py_compile app.py` — PASS (2 lần, trước và sau fix SQL filter).
- curl trực tiếp 5 case (list mặc định, search q=A009462, status=translated,
  status=draft, status=none) — số liệu đúng logic, tổng cộng khớp DB
  (48,673 total; draft=1 trước khi save → 0 sau khi save chuyển sang
  translated; translated 1→2 sau khi lưu A009462).
- Browser thật (Claude Browser tool) case yêu cầu **A009462**:
  - Admin dashboard → click "DILA Person Index" → load đúng (screenshot).
  - Search A009462 → badge "✎ Nháp AI (auto)" đúng trạng thái ban đầu.
  - Mở `person.html?id=A009462` → xác nhận bug bằng
    `getComputedStyle(#bio-vi-edit-actions).display === 'flex'` trong khi
    `hasAttribute('hidden') === true` (trước fix).
  - Sau fix CSS: reload → Lưu/Hủy không hiện ở view mode (đúng).
  - Bấm "✏ Sửa" thật (click tọa độ tính từ `getBoundingClientRect`) → sửa
    text chèn marker `[QA-T146-verify]` (đặt trước khi phát hiện T146 đã bị
    dùng, xem ghi chú trong task file) → bấm "💾 Lưu" thật →
    network `POST /api/admin/person/A009462/bio_vi` → **200**
    `{"ok":true,"status":"edited","translation_id":1744}`.
  - Query DB trực tiếp: `people.bio_vi` chứa marker; `translation_cache.id=1744`
    `status='edited'`.
  - **Reload trang** `person.html?id=A009462` → nội dung đã lưu (kèm marker)
    hiển thị lại đúng từ DB — xác nhận persist thật, không phải state JS tạm.
  - Quay lại DILA Person Index, search A009462 → badge "✓ Đã lưu".
- Fallback/edge case: `status=none` trả 48,671 (= 48,673 − 2 đã dịch) đúng số
  học; search rỗng vẫn trả full list phân trang bình thường (không lỗi khi
  `where` rỗng sau khi sửa bug SQL).
- Regression: DILA Place Index (`dila_index.html`) vẫn load 59,167 records
  bình thường sau khi thêm nav-btn cạnh nó; toàn bộ network request trong
  phiên test browser đều 200 (0 lỗi 4xx/5xx mới do thay đổi của session này).
  Có 1 console error tiền tồn tại tại `admin/index.html:756`
  (`Cannot read properties of undefined (reading 'replace')`, trong
  `loadDashboard()`/dashboard stat cards) — xác minh nằm ngoài vùng code đã
  sửa (chỉ thêm 1 thẻ `<a>` nav-btn, không đụng JS dashboard).

## Limitation / blocker còn lại

- Console error `admin/index.html:756` là bug tiền tồn tại, ngoài phạm vi
  T147 — nên audit riêng (đã cân nhắc spawn task riêng nhưng không tự ý mở
  vì chưa được yêu cầu).
- `admin/dila_index.html` (Place, cũ) không có auth guard client-side;
  `admin/dila_person_index.html` (mới) có. Không sửa file cũ để tránh
  regression ngoài phạm vi yêu cầu — cần quyết định của admin nếu muốn đồng
  bộ.
- Chưa `git add/commit` — theo đúng quy tắc `CLAUDE.md` (không tự ý chạy git
  khi chưa có lệnh rõ ràng từ user, git index repo đang có anomaly mass
  staged-deletion cần cẩn trọng).
