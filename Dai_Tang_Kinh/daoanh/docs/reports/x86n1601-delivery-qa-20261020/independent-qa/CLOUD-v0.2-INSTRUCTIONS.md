# Chỉ thị Cloud v0.2 — 2026-10-21

Giữ nguyên package v0.1 và source; tạo v0.2 trong thư mục cách ly mới. Không ghi DB/TTL/legacy hoặc production.

1. Khóa source bằng URL/commit/version/hash, giữ header. Sửa kích thước thành số đo bytes thật. Tách retrieved_at và processed_at; hash mọi artifact.
2. Thay đường dẫn Cloud hardcode bằng CLI `--source --output --schema`. Ghi lệnh Windows/Linux và dependency version trong README.
3. Tách source person, mention, evidence và relationClaim. ID item XML không phải DILA ID. Giữ source label và generation nguyên bản; không tự gộp người hoặc tính đời PTDA.
4. Lưu xml:id/XPath, nguồn phân trang `ed`, khoảng dòng, raw snippet và lớp văn bản. Tách chính văn, note, lemma và reading; không nối mọi dị bản thành một câu. Giữ gaiji/ref và quy tắc hiển thị.
5. Xác minh riêng loại quan hệ, vai người truyền/người nhận và bằng chứng chiều. Chỉ đồng xuất hiện tên thì ghi mention/unresolved. Không dùng thứ tự kế tiếp hoặc tên giống nhau để gán truyền pháp. Phân biệt thọ giới, thế độ và học tập.
6. Bỏ giới hạn bảy tên và `break`; cho phép nhiều quan hệ có chứng cứ. Gặp phủ định không tự đảo chiều hoặc sinh cạnh phủ định asserted; giữ unresolved/skip kèm lý do. Chưa rõ chiều phải unknown.
7. Mỗi claim bắt buộc evidence ref; sourceRelationTerm giữ chữ Hán thực có, tách khỏi loại chuẩn hóa. Phân biệt chứng cứ câu chữ và sơ đồ. Sơ đồ chỉ dùng khi quy ước cấu trúc đã được khảo sát, không suy từ vị trí.
8. Đối soát riêng cả chín claim cũ, đặc biệt claim 4 và 8; ghi giữ/sửa/chưa đủ bằng chứng cùng lý do. Tất cả vẫn pending. Không ép đủ chín hoặc 33 cạnh.
9. Validator phải thực chạy XSD, so hash bytes nguồn, kiểm ID trùng/ref hỏng, locator tồn tại, quote khớp lớp text, schema/version/status. XSD phải ràng buộc evidence refs; không coi container rỗng là đủ chứng cứ.
10. Test thật gồm phủ định, nhắc tên không truyền pháp, thọ giới, chiều đảo, dị bản, tên viết tắt, nhiều trò, thiếu chứng cứ, ID trùng, evidence ref hỏng, source đổi, locator sai và replay. Fixture giả lập phải có nhãn rõ. Báo cả FAIL; không sửa fixture để tạo PASS giả.
11. Cùng source/rule phải cho claims ổn định. Timestamp chạy nằm run-manifest riêng hoặc công bố cách tính semantic digest. ID source-local ổn định theo source hash/locator; không accepted DILA identity.
12. Sửa README/scope/manifest theo output thật; không mô tả toàn quyển 001 khi chỉ xử lý mục 三十三祖. Quyền từng artifact giữ pending/unresolved, không áp license text máy móc sang scripts/XSD.

Bàn giao ZIP v0.2, SHA-256, manifest đủ file, log tests, bảng chín claim và changelog v0.1→v0.2. Chưa import hoặc phát hành HOME/API/export.
