# T520 — Tab Dịch ID Person và Dịch ID Place trong T50

**Status:** PROPOSED  
**Priority:** P1  
**Owner:** OpenCode  
**Created:** 2026-11-06

## Mục tiêu

Mở rộng trang Admin:

`http://127.0.0.1:8080/daoanh/admin/translation_progress.html#t50`

Thêm hai tab:

1. **Dịch ID Person**
2. **Dịch ID Place**

Tab Person phải đọc danh sách/thông tin ID từ luồng hiện có của
`admin/dila_person_index.html`, cho phép dịch tuần tự từng ID bằng Gemini,
hiển thị thống kê cho Admin và mở trang chi tiết:

`/daoanh/admin/person.html?id=A000003`

## Phạm vi chức năng

### Tab Dịch ID Person

- Lazy-load danh sách ID Person và thông tin nguồn từ API/logic hiện có.
- Hiển thị ID, tên Hán/Việt, trạng thái dịch, thời điểm cập nhật và lỗi gần nhất.
- Click một ID mở `person.html?id=<ID>`.
- Có nút `Start`, `Pause/Stop`, `Resume` và giới hạn số lượng.
- Dịch tuần tự từng ID bằng cấu hình Gemini hiện có; không chạy song song.
- Resume-safe, chống dịch trùng và không ghi đè bản đã duyệt.
- Hiển thị: tổng số, đã dịch, đang chờ, đang chạy, lỗi, rate-limit, lần chạy cuối.

### Tab Dịch ID Place

- Chuẩn bị cùng cơ chế hiển thị, điều khiển, tuần tự, resume và thống kê.
- Reuse API/logic Place hiện có.
- Nếu chưa có endpoint hoặc schema đủ an toàn, báo `BLOCKED` rõ ràng; không tạo
  dữ liệu giả và không tự suy đoán mapping.

## Ràng buộc an toàn

- Không tự chạy dịch khi Admin chỉ mở trang.
- Không gọi song song hoặc chạy toàn corpus mặc định.
- Không giả định Gemini là miễn phí; phải tôn trọng quota/rate-limit và báo lỗi.
- Không ghi đè bản đã duyệt; phải có trạng thái lỗi và khả năng resume.
- Không sửa dữ liệu DILA gốc, TTL, lineage hoặc các tab hiện có.
- Không tạo API/DB/schema mới nếu endpoint hiện có đáp ứng.
- Mọi thay đổi DB nếu có phải additive, có dry-run, backup và rollback rõ ràng.

## Phạm vi file dự kiến

- `admin/translation_progress.html`
- `admin/dila_person_index.html` chỉ khi cần tương thích link/API
- `admin/person.html` chỉ khi cần giữ deep-link
- Endpoint/backend hiện có phục vụ Person/Place/Gemini
- Test và log trong `docs/sessions/2026-11-06/`

Không được sửa ngoài phạm vi nếu chưa báo Admin.

## Acceptance criteria

- Hai tab mới hiển thị đúng trong `#t50`; các tab T50, Nexus, Tiến Độ và Catalog
  vẫn hoạt động.
- Person list lấy đúng ID/thông tin từ nguồn DILA hiện có.
- Click ID mở đúng `person.html?id=<ID>`.
- Start/Stop/Resume hoạt động; dịch tuần tự, không trùng, không ghi đè bản duyệt.
- Thống kê khớp dữ liệu thực tế và cập nhật sau mỗi ID.
- Place tab có contract/API rõ ràng; thiếu endpoint thì báo `BLOCKED` trung thực.
- Không có lỗi console nghiêm trọng.
- Có static test, API smoke test và browser QA; phân biệt rõ live/stub.
- Báo cáo cuối có diff, test output, file backup, DB/API impact và giới hạn xác minh.

## Không làm

- Không tự publish bản dịch.
- Không tự merge Person/Place identity.
- Không rebuild T50 hoặc thay đổi kiến trúc dịch hiện có.
- Không commit, merge hoặc push khi chưa được Admin duyệt.

## Deliverable report

Báo cáo JSON gồm: `status`, `files_changed`, `api_endpoints_reused`,
`new_endpoints`, `tabs_verified`, `person_source_verified`,
`place_source_verified`, `translation_mode`, `run_controls`, `stats_verified`,
`tests`, `live_vs_stub`, `db_changes`, `backup_files`, `known_limitations`,
`next_action`.
