# Audit / Bug Fix Report — ADMIN_PERSON_EDIT_BUTTON_MISSING

> Bug: Tab Admin → Person. Route `GET /daoanh/admin/person.html?id=A002233`.
> Triệu chứng: trang chi tiết Person không có nút Edit — admin không có entry point
> để chỉnh sửa record Person hiện tại.

## 1. Vị trí audit (thực tế, không đoán)

| Hạng mục | File / Schema / Endpoint thực tế |
|----------|----------------------------------|
| Data source | `people` table — cột `id, name_vi, name_zh, name_en, sect, dynasty, birth_year, death_year, bio, bio_vi`; `translation_cache` (source_type='person_bio') |
| API endpoint (đọc) | `GET /daoanh/api/persons/<person_id>` (app.py:15498) |
| API endpoint (ghi — ĐÃ CÓ SẴN, không tạo mới) | `POST /daoanh/api/admin/person/<person_id>/bio_vi` (app.py:15633), auth qua `verify_session(token)` + header `X-Session-Token` |
| Resolver / logic | Không có bug ở backend — endpoint ghi đã hoạt động đúng (dùng bởi T145 trong `places.html`, tab Truyền Thừa) |
| Component / renderer | `daoanh/admin/person.html` — **hoàn toàn thiếu UI để gọi endpoint ghi này** |

## 2. Root cause (đã xác minh)

- **Lớp gây lỗi:** renderer (UI component), KHÔNG phải data/API/resolver.
- **Nguyên nhân chính xác:** `admin/person.html` là trang read-only thuần —
  chỉ có nút "Dịch AI → Tiếng Việt" (gọi `POST /daoanh/api/person/<id>/translate`,
  chỉ tạo bản dịch máy mới) và nút "Báo lỗi dịch". Không có bất kỳ control nào
  gọi tới endpoint ghi `POST /daoanh/api/admin/person/<id>/bio_vi` — endpoint này
  đã tồn tại từ T145 nhưng **chỉ được wire vào `places.html`** (inspector Truyền Thừa),
  chưa bao giờ được wire vào `admin/person.html`. Do đó admin mở trực tiếp trang
  Person Admin không có cách nào lưu chỉnh sửa, dù backend đã hỗ trợ đầy đủ.
  Đây là gap thuần túy ở lớp component/renderer của `person.html`, không phải
  thiếu API, thiếu bảng, hay lỗi resolver.
- Xác minh: `grep "UPDATE people SET"` trong `app.py` chỉ có 2 chỗ, cả hai đều
  là endpoint bio_vi (dòng 15685, 17548) — không có endpoint ghi nào khác cho
  `name_vi/name_zh/sect/dynasty/birth_year/death_year`. Theo quy tắc
  "không tạo CRUD/API trùng lặp nếu hệ thống đã có flow edit", phạm vi sửa chỉ
  giới hạn ở field đã có flow ghi thật (bio_vi) — không mở rộng viết trực tiếp
  cột DILA-authority gốc (name_zh/dynasty/sect/năm sinh-mất) vì không có
  endpoint/provenance workflow nào cho các field đó và việc tự chế thêm sẽ vi
  phạm ranh giới "PTDA hợp nhất" ↔ "DILA authority gốc".

## 3. Data/API contract trước → sau

| | Trước | Sau |
|--|-------|-----|
| UI | `person.html` không có nút Edit, không có textarea/Lưu/Hủy | Nút "✏ Sửa" trong header actions; click → textarea inline trong card "TIỂU SỬ TIẾNG VIỆT" + nút "💾 Lưu"/"Hủy" |
| API | Endpoint `POST /daoanh/api/admin/person/<id>/bio_vi` đã tồn tại (T145), 0 UI caller trong `person.html` | Không đổi backend — chỉ wire UI mới gọi đúng endpoint sẵn có, cùng contract `{bio_vi, translation_id?}` → `{ok, status, translation_id}` |
| Auth | Trang gate bằng `admin_session` (redirect login nếu thiếu) nhưng save không tồn tại nên không kiểm thử được | Save request gửi `X-Session-Token: localStorage.admin_session`; server `verify_session()` xác thực độc lập — 403 nếu token sai/không có, bất kể UI |

## 4. Files changed

- `daoanh/admin/person.html` — thêm nút "✏ Sửa" trong header (`#hdr` actions row); thêm `<textarea id="bio-vi-textarea">` + nút Lưu/Hủy trong card "TIỂU SỬ TIẾNG VIỆT"; thêm JS `togglePersonEdit()/startPersonEdit()/cancelPersonEdit()/savePersonEdit()` gọi `POST /daoanh/api/admin/person/<id>/bio_vi` (endpoint có sẵn từ T145, không tạo API mới); track `_personBioZh` để biết có nội dung nguồn để sửa hay không (edge case empty).
- Không đổi `app.py` — không có thay đổi backend/DB/schema.

## 5. Migration / import / dry-run / rollback (nếu chạm DB)

- Không có migration/DB schema change. Chỉ dùng endpoint ghi có sẵn (không ALTER, không bảng mới).
- Backup pre-edit: `docs/sessions/2026-09-16/person.html.bak-bug-admin-edit-button.html` (nguyên trạng trước khi sửa, tái tạo từ nội dung đọc lúc audit vì file chưa từng được commit vào git — repo person.html đang ở trạng thái untracked/staged-new).
- Revert: khôi phục `admin/person.html` từ file backup trên (`cp docs/sessions/2026-09-16/person.html.bak-bug-admin-edit-button.html admin/person.html`), hoặc `git checkout -- daoanh/admin/person.html` nếu đã commit.
- Dữ liệu test: đã restore `people.bio_vi` (A002233) và `translation_cache.id=1743` về đúng nội dung gốc sau khi test qua browser thật (verify bằng SQL query — xem case test bên dưới).

## 6. Test cases & kết quả

| Case | Input | Expected | Actual | PASS/FAIL |
|------|-------|----------|--------|-----------|
| Case yêu cầu — hiển thị + edit A002233 | Mở `/daoanh/admin/person.html?id=A002233` (đăng nhập admin `namthien@gmail.com`, whitelist trong `data/admin_emails.txt`) | Thấy nút "✏ Sửa"; click mở textarea; sửa text; Lưu → `POST .../bio_vi` 200, `people.bio_vi` cập nhật, UI hiển thị text mới | Screenshot xác nhận nút hiện; click → textarea + Lưu/Hủy hiện; sửa thêm `[TEST-EDIT-QA-A002233]`; Lưu → response `{"ok":true,"status":"edited","translation_id":1743}`; SQL xác nhận `people.bio_vi` và `translation_cache.id=1743` chứa text mới | ✅ |
| Cancel không đổi data | Sau khi mở edit, gõ thêm `[CANCEL-TEST-SHOULD-NOT-SAVE]`, bấm Hủy | Không có request mới gửi đi; UI hiển thị lại đúng text đã lưu lần trước (không có chuỗi CANCEL-TEST) | Network log: không có POST mới sau khi Hủy; `bio-vi-text.textContent` xác nhận không chứa chuỗi CANCEL-TEST | ✅ |
| Non-admin bị chặn API | Gọi `POST .../bio_vi` với `X-Session-Token: bogus-invalid-token` | 403 Unauthorized | `{"status":403,"body":{"error":"Unauthorized","ok":false}}` | ✅ |
| Non-admin bị chặn UI | Xóa `localStorage.admin_session`, mở lại `person.html?id=A002233` | Redirect thẳng về `login.html`, không render Person/Edit | Tab title đổi thành "Đạo Ảnh - Đăng nhập Admin", không có nội dung Person | ✅ |
| Edge case — Person không có bio_zh | Mở `person.html?id=A000011` (bio rỗng trong DB) | Nút Edit vẫn hiển thị (không hard-code theo ID cụ thể); click → thông báo rõ ràng "chưa có tiểu sử để sửa", không crash, không đổi state | Alert hiện đúng thông điệp; `card-bio-vi.hidden` vẫn `true`, `_editMode` vẫn `false`, không lỗi console mới | ✅ |
| Không hard-code ID | Toàn bộ code JS dùng `personId` lấy từ `new URLSearchParams(location.search).get('id')` — không có literal "A002233" trong code | Xác nhận qua đọc lại file: không có chuỗi `A002233` trong `person.html` | ✅ |

## 7. Limitation / data gap còn lại

- Edit hiện chỉ áp dụng cho field **bio_vi** (tiểu sử tiếng Việt) vì đây là field
  Person duy nhất có endpoint ghi + provenance workflow đã tồn tại
  (`translation_cache` status=`edited`). Các field cơ bản khác (`name_vi`,
  `name_zh`, `sect`, `dynasty`, `birth_year`, `death_year`) **chưa có bất kỳ
  API ghi nào trong toàn hệ thống** — nếu cần cho phép admin sửa các field này,
  cần một task riêng để thiết kế provenance/audit-trail phù hợp (một số field
  như `name_zh`/`dynasty` là dữ liệu DILA-authority gốc, không nên cho ghi tự
  do mà không qua workflow review như đã áp dụng cho `bio_vi`).
- Cơ chế gate phiên đăng nhập ở đầu `person.html` (IIFE kiểm tra
  `admin_session`) chạy bất đồng bộ (`fetch(...).then(...)`) và không `await`
  trước khi `load()` chạy — đây là hành vi có sẵn từ trước (áp dụng cho toàn bộ
  trang, không phải do fix này), có thể để lộ dữ liệu Person trong khoảnh khắc
  ngắn trước khi redirect nếu token đã hết hạn (khác với trường hợp hoàn toàn
  không có token, vốn đã chặn ngay lập tức). Không sửa trong phạm vi bug này vì
  đây là vấn đề toàn-site, ngoài phạm vi "thiếu nút Edit". Đã tách thành task
  riêng để không mở rộng phạm vi fix.
