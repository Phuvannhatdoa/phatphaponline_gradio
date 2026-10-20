> Spec cho phiên Claude Code. Chỉ mô tả yêu cầu, không chứa mã. Đọc cùng CLAUDE.md. Tick `[ ]` khi đạt từng tiêu chí.

Spec M1 · P0

# M1 Source Hub và License Gate

Một trang admin để xem, duyệt và điều khiển 25 nguồn, và một cổng giấy phép mà mọi đường nạp dữ liệu bắt buộc đi qua.

[Quay lại Plan Overview](00_PLAN_OVERVIEW.md)

## Mục đích

Hiện `gate/license.py` và `adapters/*` chưa được nối vào đường nạp thật, mọi nguồn đều `license_verified=0`. Module này biến chính sách trên giấy thành thứ có hiệu lực: không nguồn nào được ghi vào `entity_claims` nếu cổng không cho phép.

## UI/UX

Trang mới `/daoanh/admin/sources.html`, mở rộng từ trang Legal Check `source_check.html` đang có (giữ nguyên trang cũ).

- **Hàng đầu:** 4 chỉ số: số nguồn, số nguồn ACTIVE, số nguồn chưa xác minh giấy phép, số quyết định đang chờ.
- **Bảng nguồn:** mỗi dòng một nguồn: tên, vai trò, authority score, `legal_status`, `integration_mode`, giấy phép dữ liệu, giấy phép mã, ngày xác minh, số claims. Lọc theo trạng thái, vai trò. Dòng cần chú ý có thanh màu.
- **Panel chi tiết** (mở bên phải, trên điện thoại mở toàn màn hình): trích văn bản giấy phép kèm URL gốc, thao tác cho phép (đọc, đối chiếu, nạp, phân phối lại, thương mại), lịch sử thay đổi, nút Đổi trạng thái.
- **Đổi trạng thái:** hộp xác nhận ngay trong trang, bắt nhập lý do và nguồn bằng chứng. Không dùng hộp thoại hệ thống.
- **Thêm nguồn:** mẫu nhập tên, URL repo, hệ thống gợi ý giấy phép (đã có ở Legal Check), admin xác nhận, nguồn mới vào trạng thái AUDITING và mode BLOCKED.
- **Hàng đợi quyết định:** tab liệt kê việc chờ admin (ví dụ BDRC, CBETA thương mại, 84000), mỗi việc có địa chỉ liên hệ để xin phép.

## Dữ liệu

| Thành phần         | Chi tiết                                                                                                                                                                                  |
|--------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Bảng có sẵn        | `data_sources`, `source_authority`, `en_audit_log`. Điểm tham chiếu: `docs/SOURCE_REGISTRY.md`, `SOURCE_AUTHORITY_MATRIX.md`                                                              |
| Cổng               | `gate/license.py` (`LicenseGate`: can_display, can_quote, can_ingest, redistribute, commercial) và `gate/status.py`                                                                       |
| API cần có         | Liệt kê nguồn, chi tiết nguồn, đổi trạng thái (ghi audit), thêm nguồn (đã có `/daoanh/api/admin/source-add`), hàng đợi quyết định                                                         |
| Trạng thái pháp lý | ACTIVE, AUDITING, UNKNOWN, BLOCKED, REFERENCE_ONLY, FROZEN. Đề xuất thêm nhãn mức dùng: OPEN-SA, OPEN-NC, CUSTOM-NC, LINK-ONLY, UNVERIFIED. **Thêm cột là đổi schema, cần xin xác nhận.** |
| Nạp 25 nguồn       | Đối chiếu với bảng trong Plan Overview. Nguồn chưa có hàng thì thêm hàng, mặc định BLOCKED. Làm theo hướng hoàn tác được như script `build2_register_crossref_sources.py --undo`          |

## Logic

- Mọi ETL và adapter gọi cổng trước khi ghi. Cổng từ chối thì ghi một dòng audit và dừng, không im lặng bỏ qua.
- Quy tắc mặc định: nguồn mới là BLOCKED, `license_verified=0`. Không bao giờ tự đặt thương mại hoặc phân phối lại bằng 1 khi chưa xác minh.
- Năm nguồn historical (DILA, CBETA, MARCUS, ZQLOCAL, Wikidata) giữ nguyên dữ liệu, gắn `legal_status_at_ingest=LEGACY`. Không xóa, không đóng băng.
- Hành vi theo thao tác: đối chiếu cần legal_status không BLOCKED, UNKNOWN, FROZEN. Nạp cần ACTIVE và mode INGEST. Phân phối lại cần `data_redistribution=1`. Thương mại cần `data_commercial=1`.
- Precedence khi hai nguồn mâu thuẫn theo `source_authority`: DILA 100, CBETA 80, SAT 75, Kanripo 70, MARCUS 60. Chú ý `precedence_order` đánh số từ 0.
- Tín hiệu tự động: World Historical Gazetteer trả HTTP 451 và cờ `redistributable` cho nguồn không phân phối lại được. Cổng nên đọc cờ này.
- Khi giấy phép thay đổi (đọc lại trang gốc), nguồn tự chuyển về AUDITING cho đến khi admin duyệt.
- Edge case: nguồn có nhiều giấy phép theo phần (SAT, CBETA nhóm B, BDRC theo tác phẩm) cần cấp quyền theo phần, không chỉ theo nguồn.

## Acceptance criteria

- [ ] Trang `sources.html` liệt kê đủ 25 nguồn đúng trạng thái đề xuất trong Plan Overview.
- [ ] Đổi trạng thái một nguồn tạo đúng một dòng trong `en_audit_log`, có lý do và người thực hiện.
- [ ] Chạy thử một ETL cho nguồn BLOCKED: bị từ chối và có dòng audit. Chạy cho nguồn ACTIVE: thành công.
- [ ] Không còn ETL nào ghi `entity_claims` mà không đi qua cổng (liệt kê script đã rà).
- [ ] Dữ liệu đã nạp của năm nguồn historical không đổi (so số claims trước và sau).
- [ ] Thêm một nguồn thử qua giao diện rồi hoàn tác sạch.
- [ ] Trang dùng được ở độ rộng điện thoại, bảng cuộn ngang trong khung riêng.
- [ ] Có bản sao lưu trong `docs/sessions/` cho mọi tệp đã sửa, và `docs/SOURCE_REGISTRY.md` được cập nhật.

## Việc cần user quyết

- Cho phép thêm cột nhãn mức dùng vào `data_sources`.
- Có tiếp tục dùng nhãn REFERENCE_ONLY hay chuẩn hóa sang LINK-ONLY.
