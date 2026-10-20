# T215 — Đại Ninh Đạo Khoan: đồng bộ DB và kiểm chứng CBETA

Ngày2026-10-03; nối tiếp tasks/T215-dila-ttl-evidence-and-self-edges.md. Admin xác nhận thầy và yêu cầu update DB.

## Kết quả Đại Ninh

**Đã sync DB và kiểm API PASS.** Đại Ninh Đạo Khoan A020545 大寧道寬; thầy Thạch Sương Sở Viên A001439 楚圓. XML DILA2026-09 có teacher/student đối chiếu hai chiều; trang DILA chính thức hiện cũng ghi quan hệ.

- Metadata được cập nhật từ TTL: name_zh, dharma_lineage, gender, status.
- Nhãn quan hệ local được bổ sung thành Thạch Sương Sở Viên.
- Số đời45 giữ nguyên. Cạnh quốc tế và TTL đã đúng trước sync, không chèn cạnh mới. Không sửa people, assertions, consensus hoặc raw XML.
- API trả một cạnh A001439 → A020545, nguồn DILA/Marcus/TTL; tên Việt/Hán, tiểu sử và dòng phái khớp TTL/DB.
- RDF30triples, DB đọc lại, hashTTL không đổi trong lượt sync và mô phỏng rollback PASS. Xem verification.json, api-before.json, api-after.json.

Nguồn: [DILA A020545](https://authority.dila.edu.tw/person/search.php?aid=A020545), [DILA A001439](https://authority.dila.edu.tw/person/search.php?aid=A001439). Evidence XML/archive hash lưu ở data/backups/T215-dai-ninh-sync-20261003/dila-evidence.json.

## Đối chiếu X1667

[XML chính thức CBETA](https://raw.githubusercontent.com/cbeta-org/xml-p5/master/X/X88/X88n1667.xml) xác nhận tên 突空智板 và16chữ diễn phái. Đoạn X88n1667_p0560a04 ghi Lâm Tế25, Bích Phong7; bài kệ ở0560a06–07. Đây là căn cứ văn bản, không phải Authority ID. Không suy lý do DILA chưa có ID hoặc sửa đời61 của TTL từ số25 khác hệ đếm.

**Tham chiếu Đại Xa tại0560a03 không đúng:** dòng đó là phần cuối đoạn phái箬庵通問, không phải Đại Xa. Không tìm 如長 trong XML X1667.

[Bài Giác Ngộ21/11/2025](https://giacngo.vn/chanh-phap-nhan-tang-lien-quan-den-to-su-thiet-vinh-buu-hanh-post77677.html) công bố tư liệu Chánh pháp nhãn tạng1748 với chuỗi tên 雪梪真發 → 大沙如長 → 明弘子融. Bài dẫn tư liệu này, không dẫn X1667. Các biến thể tên Việt/Hán chưa đủ để gán cùng người với A000960 雪槱真樸; giữ trạng thái cần đối chiếu. Bằng chứng mới đã bổ sung vào8case JSON/Dashboard, chưa sửa TTL/DB các vị này.

## Backup và rollback

Backup: data/backups/T215-dai-ninh-sync-20261003 gồm TTL nguyên trạng, XML evidence, db-before và sync-report before/after. Transaction chỉ cập nhật1authority row và1local relation row.

Từ daoanh chạy: python -X utf8 data/backups/T215-dai-ninh-sync-20261003/sync_case.py --revert. Guard dừng nếu DB/TTL đã đổi sau sync. Mô phỏng rollback đã PASS trước commit. Không hoàn tác toàn DB, không ghi đè phiên khác. Script không --apply chỉ preflight.

## Kiểm tra và giới hạn

DB/API/RDF/rollback PASS. Pipeline đã kết thúc exit1 tại T203:25PASS/2FAIL;5 TTL khác còn40 ký tựÐ. Corpus hiện tại1044 file parseOK,0 lỗi cú pháp. Xem pipeline.log; không coi toàn bộ pipeline PASS. Hai file Đại Ninh cùng URI còn chưa hợp nhất; phiên này không đổi URI hoặc xóa file. Case Phước Châu chưa sync trong lượt này. Di Phong đã gỡ candidate ID theo yêu cầu Admin. Trí Bản/Đại Xa/Tuyết Giàu chưa gán ID mới.

Lượt tải XML CBETA trực tiếp lỗi TLS; chứng cứ trích từ web tool đọc XML chính thức, không tuyên bố có file tải về hoặc SHA256 của X1667. Không tắt TLSverify.
