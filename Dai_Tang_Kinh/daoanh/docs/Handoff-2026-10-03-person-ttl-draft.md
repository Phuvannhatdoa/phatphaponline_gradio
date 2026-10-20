# Handoff — Person → Tạo TTL (2026-10-03)

## 1. Thông tin đọc nhanh

Đã hoàn tất nút Tạo TTL và luồng điền bản nháp. DB/raw/corpus TTL không đổi; chỉ thử request lưu bằng mock. Không stage/commit. HEAD biến động do phiên khác, tra git log từ repo root. Browser A000885/fixture, RDF 122 triples và E2E syntax PASS. Pipeline exit1 tại T203 do TTL khác (5 file, 40 ký tự Ð; test corpus cũng thất bại). Log: reports/person-ttl-draft-20261003/pipeline.log.

## 2. Đọc trong 2 phút

Nút ở bên phải AI Dịch DILA. Mở form trong cùng tab, điền dữ liệu hiện có, giữ nội dung đang sửa chưa lưu. A000885: 980/1052, thầy A015592, 34 học trò; chưa có bản Việt và số đời nên để trống. Admin kiểm tên Việt, nguồn và quan hệ trước lưu. Không tự dịch/tự tạo file/tự ghi DB khi chuyển.

## 3. Sửa và bằng chứng

Shared script person-ttl-draft.js giữ DILA ID trên main và từng endpoint bằng URI riêng và owl:sameAs. Không gộp người theo tên. Thông tin chưa có ô riêng vào source_notes, xuất bkg:sourceNote. Tên Hán không gắn nhãn Việt khi chưa có tên Việt. Chỉ lấy năm từ ngày có định dạng rõ ràng, không regex số trong tiểu sử. gen_lamte mới được điền, không suy đời. Save DILA cho phép thiếu đời/dòng phái; save nhập tay giữ validation cũ. Đã sửa slugify cũ thiếu join gây TypeError. Escape RDF/HTML; guard ID, slug và self-edge.

## 4. Quy tắc cần biết

Các file admin bị Windows chặn ghi thường; dùng WriteAllText đã được auto-review chấp thuận. Có backup hai trang. Workspace nhiều phiên, không ghi đè WIP khác. Lưu TTL hiện lưu file; Chạy ETL tính đời, chưa sync đầy đủ metadata/tiểu sử/quan hệ/consensus vào DB. Không nói rằng nhấn chuyển hoặc ETL đã up DB toàn hồ sơ.

## 5. Revert

Từ daoanh: python -X utf8 data/backups/person-ttl-draft-20261003/revert.py

Script kiểm hash tất cả ba file trước sửa; nếu đã có thay đổi tiếp thì dừng. Khôi phục hai trang, xóa đúng script mới. Mất thay đổi UI của phiên này, không mất dữ liệu DB/raw. Manifest ghi SHA256 sau sửa. Không chạy revert khi muốn giữ tính năng.

## 6. File tạo/sửa

- admin/person.html: nút, snapshot hồ sơ, cập nhật tên Việt vừa lưu, load script.
- admin/monk_ttl_add.html: notice, DILA ID, giới tính, thêm thầy, nguyên bản và nguồn, load script.
- admin/person-ttl-draft.js: chuyển/điền/generator/validation.
- data/backups/person-ttl-draft-20261003/: before, manifest, revert.
- docs/reports/person-ttl-draft-20261003/: README, browser scripts, actual-draft.json, RDF fixture, pipeline log, validation.
- docs/sessions/2026-10-03-person-ttl-draft.md và Handoff này; tasktodo ghi tiếp nối.

## 7. Sai lầm và bài học

Node --check file .new báo extension không hỗ trợ; kiểm file .js thật PASS. Kiểm save phát hiện slugify cũ map trả array rồi gọi replace; sửa NFD + lọc dấu + đ. Test có lỗi ban đầu giữ browser sống; đã dừng đúng process thử và sửa catch thoát test. Không kết luận UI smoke là toàn pipeline PASS.

## 8. Chưa xong

Bộ sync đầy đủ file TTL mới vào DB là luồng riêng chưa được bổ sung trong request nút chuyển này. API lưu file và ETL hiện tại không làm việc đó. Nếu triển khai sau cần authenticated route, DILA identity, backup/transaction, chỉ nguồn TTL, giữ assertions DILA/Marcus và kiểm API sau sync. Pipeline chung T203 còn lỗi corpus ngoài phiên. Không cần quyết định Admin để sử dụng nút chuyển.

## 9. Kiểm nhanh

Từ daoanh:

- node --check admin/person-ttl-draft.js
- node docs/reports/person-ttl-draft-20261003/verify-browser.cjs
- node docs/reports/person-ttl-draft-20261003/verify-advanced.cjs

Hai script dùng Chromium, mock login và mock save, không ghi TTL/DB thật. Test advanced thử nhiều thầy, nội dung chưa lưu, HTML/quote, save thiếu gen, Reset, draft thiếu. RDF fixture parse bằng rdflib 122 triples. Trang: http://localhost:8080/daoanh/admin/person.html?id=A000885.

## 10. Agent tiếp theo

Đọc AGENTS và README báo cáo. Chỉ claim bản nháp/lưu file đã làm, không claim sync DB. Giữ ID endpoint khi đổi nhãn Việt. Không đoán đời; không tăng từ thầy +1. Không tự chạy ETL toàn corpus để chứng nhận sync. Kiểm hash trước sửa và cập nhật session sau build. Memory service có thể chưa chạy, giữ log local.
