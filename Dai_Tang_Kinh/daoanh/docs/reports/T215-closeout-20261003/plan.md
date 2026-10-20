# T215 — Đợt hoàn tất có chứng cứ, 2026-10-03

1. Khóa hash file và snapshot DB trước sửa; giữ nguyên raw XML và mọi cạnh không thuộc nguồn TTL.
2. Đồng bộ Phước Châu A003636, sửa provenance Thạch Cữu A019919; sửa ánh xạ Mã Tổ A003623 và Phong Huyệt A004982 theo record DILA.
3. Rút các cạnh TTL dựa trên ánh xạ sai; chỉ dựng lại khi cặp thầy–trò có record DILA xác nhận. Không suy đời và không sửa đời đang có.
4. Lưu nguyên file lỗi vào ttl_quarantine, gộp bản Đại Ninh trùng; giữ hồ sơ chứng cứ ở tên file trên Dashboard.
5. Sửa ký tự Ð trong literal Việt có guard RDF, URI, chữ Hán và quan hệ.
6. Quét từng file sau sửa, xuất danh sách bỏ qua/đời cần chứng cứ; kiểm DB, API, rollback và pipeline.
7. Cập nhật báo cáo, Dashboard, tasktodo, session và Handoff. T215 chưa DONE học thuật nếu danh tính/đời còn chờ chứng cứ.
