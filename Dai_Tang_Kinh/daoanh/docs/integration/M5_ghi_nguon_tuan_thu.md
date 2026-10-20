> Spec cho phiên Claude Code. Chỉ mô tả yêu cầu, không chứa mã. Đọc cùng CLAUDE.md. Tick `[ ]` khi đạt từng tiêu chí.

Spec M5 · P0

# M5 Ghi nguồn và Tuân thủ công khai

Mọi dữ liệu hiển thị cho người dùng đều có ghi nguồn đúng điều khoản, và nội dung phi thương mại không lọt vào đầu ra thương mại.

[Quay lại Plan Overview](00_PLAN_OVERVIEW.md)

## Mục đích

ZenQi là công ty. CBETA là phi thương mại và đã nằm trong site. DILA là CC BY-SA nên có nghĩa vụ ghi nguồn và chia sẻ tương tự. Module này làm cho hai điều đó thành hành vi có thể kiểm chứng của sản phẩm.

## UI/UX

- **Chân trang ghi nguồn** trên mọi trang có dữ liệu ngoài: dòng ngắn gồm tên nguồn, giấy phép, link. Bấm mở trang `/daoanh/credits.html`.
- **Trang Credits:** mỗi nguồn một mục: tổ chức, giấy phép, phiên bản dữ liệu, thay đổi đã làm, link gốc, thông báo bản quyền bắt buộc.
- **Badge nguồn** trên từng thẻ dữ liệu (DILA, ZQLOCAL, CBETA...) cùng cách hiển thị ở mọi nơi.
- **Trạng thái bị ẩn:** khi một nội dung bị gate chặn, hiện dòng giải thích ngắn thay vì để trống.

## Dữ liệu

| Nguồn      | Mẫu ghi nguồn (đề xuất, không phải lời văn chính thức)                                                                                                             |
|------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| DILA       | Dữ liệu địa danh và nhân vật: DILA Buddhist Authority Database, Dharma Drum Institute of Liberal Arts, CC BY-SA 3.0, authority.dila.edu.tw. Ghi chú nơi đã sửa đổi |
| GeoNames   | Tọa độ: GeoNames, CC BY, kèm link                                                                                                                                  |
| WHG        | World Historical Gazetteer, CC BY 4.0                                                                                                                              |
| CBETA      | Giữ nguyên thông báo bản quyền và thông tin phiên bản. Chỉ phi thương mại                                                                                          |
| Marcus SNA | Ghi theo README của repo, coi là BY-SA                                                                                                                             |

Nguồn dữ liệu lấy từ `data_sources` (trường tên chính tắc, tổ chức, giấy phép, URL) để không gõ tay từng nơi.

## Logic

- Đầu ra thương mại không chứa văn bản CBETA. Đầu ra nội bộ và học thuật thì được, nếu giữ nguyên thông báo bản quyền và không sửa nội dung. Cần xác nhận với CBETA bằng văn bản (liên hệ nằm trong phần đầu tệp TEI) rồi ghi tình trạng vào cổng.
- Điều khoản CBETA có chỗ mâu thuẫn: trang chính ghi CC BY-NC-SA 4.0, trang tiếng Anh cũ thêm điều kiện không sửa, nhóm tác giả hiện đại cần xin phép riêng. Phiên dev phải áp dụng điều khoản chặt nhất cho đến khi có văn bản xác nhận.
- DILA là chia sẻ tương tự: bản phái sinh phân phối ra ngoài phải cùng giấy phép. Giữ dữ liệu DILA tách được khỏi dữ liệu ZQLOCAL. Cần luật sư xác nhận, đây không phải tư vấn pháp lý.
- Nhãn `can_display` và `can_quote` của `LicenseGate` quyết định hiển thị hay ẩn.
- Xuất dữ liệu (nếu có) đính kèm tệp ghi nguồn và giấy phép.
- Hiệu năng: chân trang đọc từ cache, không truy vấn DB mỗi lần.

## Acceptance criteria

- [ ] Mỗi trang hiển thị dữ liệu DILA, GeoNames, WHG đều có dòng ghi nguồn.
- [ ] Trang `credits.html` liệt kê mọi nguồn ACTIVE hoặc REFERENCE, đúng giấy phép trong `data_sources`.
- [ ] Cấu hình chế độ thương mại: không có đoạn văn CBETA nào trong HTML trả về (kiểm bằng tìm kiếm tự động).
- [ ] Nguồn bị chặn: hiện dòng giải thích, không lỗi.
- [ ] Danh sách việc chờ xác nhận pháp lý (CBETA, DILA collection, MITRA, BDRC) có trong `docs/integration/DECISIONS.md`.
- [ ] Tên Việt luôn hiện badge ZQLOCAL.
- [ ] Không làm hỏng giao diện hiện có ở độ rộng điện thoại.
