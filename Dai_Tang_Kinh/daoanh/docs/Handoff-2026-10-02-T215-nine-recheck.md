# Handoff — T215 kiểm lại 9 TTL

## 1. Thông tin đọc nhanh
2026-10-02; HEAD không thay đổi/không commit trong phiên. TTL không sửa; DB mới sync riêng metadata + thầy Phần Dương. Tuệ Thăng recheck PASS. Pipeline chưa hoàn tất tại thời điểm lập log; cập nhật cuối file.

## 2. Đọc trong 2 phút
Còn 2 self-edge và lỗi quote. 7 case chưa sync. Báo cáo chi tiết: docs/reports/T215-self-edges/recheck-2026-10-02.md. Admin kiểm Dashboard, đối chiếu báo cáo, xử lý các file chưa đạt.

## 3. Thay đổi có bằng chứng
A004984 汾陽善昭 có thầy A004983 首山省念 trên DILA chính thức; TTL đã sửa đúng teacher. Copy tiểu sử Việt/metadata từ đúng TTL, thêm hasTeacher, reject assertion58021 tự nối. API200 tên/tiểu sử khớp TTL và đời43, cạnh thầy đúng. Nguồn và snapshot trong sync-report.json. Các ánh xạ đệ tử còn chưa chứng nhận, giữ nguyên.

## 4. Cảnh báo bắt buộc
Không chạy full import TTL. Hưng Hóa collision với TS-Dinh-Lam-Canh-Phuong; Tịnh Nhân có thầy A014617 bị tang_chu_pho_dung claim. Không sửa đời thầy+1. TTL không được git track mặc định; có thể có phiên khác đang sửa task T216, tránh ghi đè.

## 5. Revert
Từ thư mục daoanh: `python -X utf8 data/backups/T215-nine-recheck-20261002/sync_case.py --revert`. Khôi phục đúng row snapshot; guard dừng nếu row đã đổi sau sync. Rollback đã thử SQLite in-memory PASS. Không mất dữ liệu ngoài phạm vi. Không hoàn tác Tuệ Thăng của phiên trước.

## 6. File tạo/sửa
Backupdir data/backups/T215-nine-recheck-20261002: script, before/after, TTL copy, API snapshots, pipeline log. Report cases.json + recheck markdown; dashboard page + JSON + main banner; task T215, progress, roadmap, session và Handoff này. Không sửa file TTL hoặc code app.

## 7. Sai lầm và bài học
Không coi tất cả 9 đã sửa đúng theo thông báo; đọc trực tiếp mới phát hiện 2 self-edge còn nguyên. Không đánh dấu toàn bộ Phần Dương sạch vì chỉ xác minh metadata/thầy; ID đệ tử vẫn có mâu thuẫn cần audit sau.

## 8. Chưa xong
7 case không sync và ánh xạ đệ tử Phần Dương. Đọc lý do từng case trong recheck report. Thiếu rdflib; chưa chứng nhận RDF đầy đủ.

## 9. Kiểm tra nhanh
API `/daoanh/api/monk/A004984/lineage-tree?up=1&down=1`: tên/tiểu sử Việt đúng TTL, generation43, teacherA004983. A008431: đời50, teacherA007993. Dashboard `/daoanh/dashboard/t215-self-edges.html` có 9case trạng thái mới.

## 10. Agent kế tiếp
Đọc task215 + cases.json + sync-report.json; xử lý lỗi quote/self-edge và collision có bằng chứng; không suy đoán A026976. Có bảo vệ nguồn ngoài phạm vi so equality before/after. Kiểm pipeline log và RDF parser trước tuyên bố sạch.


### Kết quả kiểm tra cuối phiên
DB scope PASS; rollback mô phỏng PASS; API200 và tiểu sử khớp TTL cho A008431/A004984, cạnh thầy đúng. Cả9 TTL giữ nguyên hash trong phiên. Dashboard live9case PASS; kiểm cú pháp HTML/JS5page PASS (không phải kiểm UI runtime). `npm run pipeline` FAIL tại T17867/68 vì Python CLI thiếu Flask (`No module named flask`); không tuyên bố pipeline đạt. Log tại data/backups/T215-nine-recheck-20261002/pipeline.log. Memory37700 không kết nối được; tasktodo và session/Handoff đã lưu local.
