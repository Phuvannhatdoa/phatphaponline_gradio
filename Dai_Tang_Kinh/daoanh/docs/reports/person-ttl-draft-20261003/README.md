# Person → Tạo TTL (2026-10-03)

Đã thêm nút Tạo TTL ngay bên phải AI Dịch DILA trên admin/person.html. Nút chuyển trong cùng tab, giữ bản nháp riêng trong sessionStorage và mở monk_ttl_add.html với khóa bản nháp. Không gọi API dịch hoặc ghi TTL/DB khi chuyển.

Form nhận tên đang hiển thị/đang sửa, DILA ID, tên Hán, bản dịch Việt đang sửa, nguyên bản Hán, năm từ ngày DILA, toàn bộ thầy/học trò, tên khác, tác phẩm, xuất xứ, triều đại, trích dẫn và URL nguồn. Các phần không có ô chuyên biệt vào ô Thông tin bổ sung và nguồn tham khảo, được xuất thành bkg:sourceNote.

URI mặc định dila_aNNNNNN giúp tránh gộp người cùng tên. Main và endpoint có owl:sameAs tới trang DILA đúng ID. Không dùng tên Hán làm nhãn Việt khi chưa dịch. Không tự tăng đời hoặc suy từ số trang/niên đại. Khi chưa có gen_lamte, số đời trống. Hồ sơ DILA được lưu không có đời/tông phái; các triple thiếu dữ liệu được bỏ qua. Luồng nhập tay cũ giữ validation hiện có.

Dấu nháy/backslash/xuống dòng được escape bằng JSON.stringify để Turtle hợp lệ. Preview escape HTML. Reset xóa khóa/URL bản nháp; import file khác gỡ ID trước đó. Có guard slug, ID và self-edge trước lưu. Tên file DILA có ID và phần tên Việt bỏ dấu đúng, ví dụ TS-A000885-Trung-Hien.ttl.

## Kiểm chứng

- Luồng thật A000885: 980/1052, một thầy A015592, 34 học trò, đời trống; refresh giữ bản nháp, 0 page errors.
- Fixture: nội dung Việt đang sửa chưa lưu; nhiều thầy; quote/triple quote/backslash/HTML; payload lưu được mock, không ghi dữ liệu thật; Reset và draft thiếu xử lý được.
- RDF fixture: rdflib parse 122 triples PASS.
- Pipeline đã chạy, dừng ở T203: 5 TTL khác có 40 ký tự Ð và assertion corpus trong test thất bại. Không thay các TTL đó trong phiên UI này. Xem pipeline.log.

## Giới hạn DB cần phân biệt

Endpoint /daoanh/api/admin/monk_ttl hiện chỉ lưu file. run_etl_gen chạy etl_gen_compute.py để tính đời, chưa phải sync đầy đủ vn_person_authority, tiểu sử, assertions và consensus. Tính năng này hoàn tất chuyển bản nháp và lưu TTL; chưa bổ sung bộ đồng bộ DB mới. Admin không nên xem nút ETL là xác nhận toàn hồ sơ đã up DB. Các quan hệ DILA được giữ ID và nguồn để bước sync sau xác minh.

## File và khôi phục

Sửa admin/person.html, admin/monk_ttl_add.html; thêm admin/person-ttl-draft.js. Before ở data/backups/person-ttl-draft-20261003. Không sửa raw, TTL corpus hay DB. Không commit/stage. Handoff: docs/Handoff-2026-10-03-person-ttl-draft.md.
