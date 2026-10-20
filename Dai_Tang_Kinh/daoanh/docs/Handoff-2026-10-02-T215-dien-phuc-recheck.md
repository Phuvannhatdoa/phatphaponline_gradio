# Handoff-2026-10-02-T215-dien-phuc-recheck

## 1. Đọc nhanh
T215 in_progress. Kiểm lại file Admin sửa. TTL/DB không sửa. Dashboard HTTP200,9 article, trạng thái mới đúng. Pipeline đang chạy, ghi kết quả bổ sung sau.

## 2. Đọc trong2 phút
Đã hết self-edge; chưa submit vì hasTeacher liệt kê4 người trong khi DILA chỉ xác nhận Đoan Dụ là thầy truyền pháp. Ba target khác là đồng môn cùng thầy Đoan Dụ. DB còn gán dữ liệu Tuệ Thăng vào slug thầy và ID A045939.

## 3. Đề xuất
Đọc docs/reports/T215-self-edges/dien-phuc-recheck-2026-10-02.md. hasTeacher chỉ giữ duc_vuong_doan_du. Giữ nhãn3 đồng môn tham chiếu. Số đời50 giữ nguyên, chưa xác minh đúng. Chưa tự sửa TTL vì chỉ được submit khi đạt điều kiện, file hiện chưa đạt.

## 4. Cảnh báo
Không dùng regex parser lấy chỉ target đầu để kết luận file đúng. Không submit3 đồng môn thành thầy. Không update row duc_vuong_doan_du sang tên Tuệ Thăng vì khác người; cần scoped identity migration có snapshot/guard. Không ghi đè DILA assertions.

## 5. Revert
TTL/DB0 mutation nên không cần rollback học thuật. Review JSON trước recheck lưu dien-phuc-before-recheck.json. Hồ sơ md gốc còn nguyên snapshot và đã thêm liên kết recheck; muốn revert trạng thái Dashboard phải dựng lại từ snapshot, không ghi đè thay đổi sau. Không commit nên không có SHA revert mới.

## 6. File
Tạo dien-phuc-recheck-2026-10-02.md, dien-phuc-before-recheck.json và Handoff này. Sửa cases.json, README.md hồ sơ, dashboard/t215-{cases.json,self-edges.html}, task T215.

## 7. Bài học
Self-edge biến mất không chứng minh toàn bộ relation đúng. Bản proposal trước chưa phát hiện đủ danh sách đồng môn; recheck đã đọc toàn bộ4 target và trang DILA từng người.

## 8. Chưa xong
Sửa3 target đồng môn khỏi hasTeacher theo evidence; validate RDF; identity migration scoped cho Tuệ Thăng A008431/thầy A007993, snapshot/rollback; verify API; không sửa đời thiếu3 chứng cứ.

## 9. Kiểm nhanh
Mở /daoanh/dashboard/t215-self-edges.html: hồ sơ1 đã hết tự nối nhưng còn3 đồng môn và chưa submit DB. Recheckmd có5 link DILA chính thức và đề xuất triple.

## 10. Agent tiếp
Đọc evidence mới trước apply. Kiểm hash TTL hiện tại. DILA đã đọc A008431/A007993/A008424/A008429/A008421, dùng đúngID. DB read-only xác nhận người chính chưa có row, row thầy đang sai; không áp dụng importer skip/insert-only.


Validation: pipeline exit1 vì thiếu flask, T17867/68 PASS. RDF chưa validate do thiếu rdflib. Memory service không kết nối được. TTL/DB không sửa, Dashboard review HTTP200.
