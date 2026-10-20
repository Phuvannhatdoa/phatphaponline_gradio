# Long Hoa Tề Nhạc — đồng bộ riêng TTL và DB

Hoàn thành: sửa P1_is_identified_by về long_hoa_te_nhac; Tây Du → Tây Dư. Đồng bộ vn_person_authority A020497: file nguồn, tông phái, đời 44, giới tính, tiểu sử trống. Thay quan hệ có nguồn TS-Long-Hoa-Te-Nhac; rejected assertion cũ A003518 → A014495; thêm TTL A003907 → A020497. Giữ nguồn khác và consensus ngoài các cặp liên quan.

Kiểm tra: parser importer PASS; DB so khớp TTL PASS; API localhost:8080 lineage-tree PASS tên, file nguồn, tông phái, đời, tiểu sử và cạnh thầy/trò. A026103 vẫn được hiển thị theo DILA/Marcus, không tự thêm vào TTL.

Chưa hoàn tất: rdflib không có trong Python CLI; pipeline guard/lint/test PASS, dừng tại T178 67/68 vì thiếu flask. Không khẳng định toàn hệ thống hết bugs. Full importer chỉ skip file tồn tại và insert cạnh, không tự refresh file sửa.

Todo: luồng refresh từng TTL có backup/revert; môi trường kiểm thử đủ Flask/rdflib.

Backup: data/backups/long_hoa_te_nhac_1790929257113 gồm TTL trước sửa, db-rows-before.json và sync-report.json, sync_case.py. lineage.db trong folder này là bản sao toàn DB chưa hoàn tất, KHÔNG dùng phục hồi.
