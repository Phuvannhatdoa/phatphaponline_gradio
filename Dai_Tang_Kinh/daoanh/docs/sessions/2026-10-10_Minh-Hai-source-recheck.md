# Phiên 2026-10-10 — đối chiếu Minh Hải Pháp Bảo, DILA/CBETA/Báo Tư

## Đã làm

- Trả lời yêu cầu kiểm lại nhận định DILA/CBETA không có Minh Hải Pháp Bảo. Kết luận chính xác là chưa xác minh được ID trong phạm vi tra cứu; không kết luận vắng thông tin ở mọi kho.
- Quét hai artifact DILA: 49.361 và 19.034 person; CBETA local: 5.017 XML, lỗi đọc 0. Kết quả chi tiết: [báo cáo](../reports/Minh-Hai-source-recheck-20261010/README.md).
- Đọc hồ sơ A000662 và X0613 local; thấy niên đại đề tựa 1630, giữ nguyên quyết định Admin loại trừ khỏi Minh Hải Pháp Bảo Chúc Thánh.
- Đối chiếu metadata/mục lục luận án Thành Công 2015 về 明海法寶; đọc PDF nghiên cứu Khoáng Viên 2017 và bài ký 報資禪院記 được công bố trong đó.
- Lưu báo cáo, log quét, script tái lập, manifest SHA-256, hồ sơ bàn giao.

## Phạm vi thay đổi

Không cập nhật DB, TTL, raw XML, UI, danh tính, quan hệ, số đời hay job dịch tên. Không commit/stage. Không chạy pipeline và không tuyên bố PASS của application; không yêu cầu Admin review bản build. HEAD khi ghi nhận: c75d99eca0c2d23dbe927174a11b10a4b4e49261.

## Đang dở / Todo tiếp theo

- Nghiên cứu nhận diện Minh Hải vẫn thiếu toàn văn luận án, ảnh sử liệu và locator liên quan từng quan hệ.
- Phải phân biệt Báo Tư cũ/Báo Tư Tân Tự; chưa tìm được mục địa phương chí trực tiếp ghi Minh Hải Pháp Bảo.
- Không biến nhiều bài dẫn cùng tư liệu thành ba nguồn độc lập; không tái gắn A000662.

## Lỗi thao tác và dịch vụ

- Lệnh Python -c tải PDF bị PowerShell làm mất dấu quote: SyntaxError, không tải được. Sửa bằng file Python riêng; tải 934.339 byte và đọc bằng pdfplumber thành công.
- Sau khi viết README/request, gọi nhầm store trong node_repl: store is not defined. Các file đã ghi vẫn tồn tại; đã xác nhận bằng stat/hash, không chạy lại để ghi đè.
- POST claude-mem theo AGENTS.md thất bại: curl error 7, shell exit 1, không kết nối port 37700. Request/result lưu trong thư mục report; không tuyên bố đã lưu lên dịch vụ.

## Bàn giao

[Handoff](../Handoff-2026-10-10-Minh-Hai-source-recheck.md) ghi 10 mục, nguồn, giới hạn và bước tiếp theo.
