# SESSION — Tạo TTL từ hồ sơ DILA

Đã xong nút và luồng chuyển/điền bản nháp, bổ sung source fields, escape RDF, guard ID/self-edge, sửa slugify cũ. Kiểm A000885 và fixture PASS. Pipeline dừng T203 do TTL khác. Không ghi DB hay tạo TTL thật.

Đang dở: bộ sync đầy đủ TTL → DB là luồng chưa có trong API lưu hiện tại. Todo: thiết kế sync riêng từng file có DILA ID, backup/transaction, giữ DILA/Marcus; không dùng ETL số đời thay cho sync. Báo cáo: docs/reports/person-ttl-draft-20261003/README.md.
