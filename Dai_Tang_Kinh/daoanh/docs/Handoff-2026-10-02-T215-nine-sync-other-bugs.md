# Handoff — T215: đồng bộ 9 hồ sơ và audit TTL còn lại

## 1. Thông tin đọc nhanh

Ngày: 2026-10-02. Chín case chính hoàn tất phạm vi metadata và thầy đã xác minh; T215 toàn corpus vẫn in_progress. Phiên này sửa một TTL, không ghi DB, không commit/stage. HEAD thay đổi do phiên khác; đọc git log tại repo root trước commit. Kiểm tra: DB/API 9/9 PASS, RDF 1038/1038 PASS, self-edge 0. Pipeline exit 1 do EPERM file kết quả; E2E retry 2/2 PASS. Chi tiết: reports/T215-post-sync-audit-20261002/validation.json.

## 2. Đọc trong 2 phút

TTL Nguyên Liên quay lại tự làm thầy trong khi DB vẫn đúng. Đã phục hồi thầy Thủ Sơn Tỉnh Niệm A004983, giữ đời 43. Cả 9 hồ sơ khớp tên, DILA ID, tiểu sử, đời và cạnh thầy trên DB/API. Audit mới có 3 đường vòng, 6 nhóm URI trùng, 3 file có khối chủ thể lặp và 1 file chủ thể rỗng. Admin xem Dashboard lỗi; ưu tiên Di Phong/Đột Không, tiếp đến nhóm Phong Huyệt và Trường Viễn/Đại An.

## 3. Vấn đề, đề xuất và bằng chứng

Nguyên Liên: hasTeacher từ chính mình thành thu_son_tinh_niem. Hồ sơ DILA A014349/A004983 lưu tại T215-self-edges; API có cạnh DILA/Marcus/TTL active. DB đã đúng nên không ghi lặp.

Di Phong/Đột Không dùng URI Bạch Vân; Trường Viễn dùng Phật Ý; Đại Xá/Minh Hoằng/Tuyết Giàu dùng Phong Huyệt. File Phuc-Chau-Dai-An còn URI và nhãn rỗng, khác file Phuoc-Chau-Dai-An đang chứa Bách Trượng. Chỉ báo cáo các file khác, chưa sửa theo suy đoán. Báo cáo có SHA256, số dòng, từng cạnh tạo vòng: reports/T215-post-sync-audit-20261002/README.md và other-files.json. 812 file có cờ không có nghĩa 812 file đã chứng minh sai.

## 4. Quy tắc cần biết

Workspace có nhiều phiên làm đồng thời; không stage/commit WIP người khác. Raw XML/docx bất biến. Không gọi importer toàn bộ hoặc ánh xạ chỉ theo tên. Không sửa số đời khi thiếu 3 chứng cứ độc lập. RDF hợp lệ không chứng minh nội dung đúng. Cờ P1, tên file và DILA cần đối chiếu quy ước. test-results bị Windows khóa; dùng thư mục kết quả riêng.

## 5. Revert

Chạy từ daoanh:

```powershell
python -X utf8 data/backups/T215-nine-final-sync-20261002/revert_ttl.py
```

Guard kiểm nội dung sau sửa và dừng nếu file đã bị sửa tiếp. Lệnh trả Nguyên Liên về self-edge trước phiên, chỉ dùng khi thực sự muốn hoàn tác. Phạm vi mất thay đổi: bản sửa của một TTL; không mất raw. DB không ghi nên phiên này không có rollback DB. Các đợt sync trước dùng đúng snapshot riêng Diên Phúc/fix-sync/Trí Tài; không restore toàn DB bừa.

## 6. File tạo/sửa

- data/ttl/TS-Quang-Tue-Nguyen-Lien.ttl: phục hồi thầy.
- data/backups/T215-nine-final-sync-20261002/: bản trước sửa, log, revert guard, runtime-results.
- docs/reports/T215-post-sync-audit-20261002/: audit, DB/API readback, chu trình, danh sách từng file, README, logs, validation; giữ cả audit trước sửa Nguyên Liên.
- dashboard/t215-other-ttl-bugs.html và .json: báo cáo mới.
- dashboard/dashboard_process.html, t215-self-edges.html, t215-cases.json; docs/reports/T215-self-edges/cases.json: cập nhật trạng thái và link.
- tasks/T215-dila-ttl-evidence-and-self-edges.md; docs/progress.md, roadmap.md, tasktodo.md; docs/sessions/2026-10-02-T215-nine-sync-other-bugs.md: ghi tiến độ.
- data/progress_data.json: sinh lại bằng build_progress_data.py.

## 7. Sai lầm và bài học

AGENTS.md tại workspace root không tồn tại; bản áp dụng ở daoanh/AGENTS.md. Đã đọc bản này trước cập nhật. Kết quả done trước đây không bảo đảm file không hồi quy: kiểm hash và nội dung thực bắt được Nguyên Liên. MULTIPLE_MAIN ở đây có thể là hai khối cùng URI, không phải hai người riêng. Không cộng các finding thành số file sai.

## 8. Chưa xong

1. Khóa DILA và tiểu sử các URI trùng; kiểm những cạnh đóng vòng trước.
2. Kiểm nhóm alias Đại/Đạo Ninh và Thạch/Linh Cưu trước kết luận lỗi.
3. Đối chiếu 101 cờ P1 khác subject, 85 cờ tên file, 214 unresolved và 474 not confirmed.
4. Xác minh 26 cặp đời; không suy đời bằng thầy + 1. Các endpoint thiếu và đệ tử của 9 case chưa chứng nhận toàn bộ.
5. Pipeline mặc định chưa xanh do EPERM; compliance báo 2 metric fail nhưng script không chặn exit. Không chứng nhận toàn hệ thống.

Không có quyết định Admin bắt buộc để tiếp tục đọc bằng chứng.

## 9. Kiểm nhanh

```powershell
Get-Content docs/reports/T215-post-sync-audit-20261002/validation.json
Get-Content docs/reports/T215-post-sync-audit-20261002/nine-db-api-check.json
Select-String -Path data/ttl/TS-Quang-Tue-Nguyen-Lien.ttl -Pattern hasTeacher
npx playwright test tests/e2e-runtime.spec.js --reporter=list --output=data/backups/T215-nine-final-sync-20261002/runtime-results-next
```

Dashboard: http://localhost:8080/daoanh/dashboard/t215-other-ttl-bugs.html. HTTP 200; Chromium mở được 815 details, 0 page errors. Spec runtime hiện có không tìm thấy nút Mapping Tên Việt nên không kiểm luồng click đó.

## 10. Agent kế tiếp

Đọc AGENTS, task T215 và hồ sơ nguồn. Kiểm hash và DB trước mutation. Audit SQLite mode=ro, đọc từng TTL; không nạp raw corpus vào RAM. Không chạy lại apply script cũ bừa. Audit mới dùng thư mục output mới để giữ baseline. Backup có guard, transaction và sửa theo vai trò triple. Bỏ qua trường thiếu bằng chứng, cập nhật Dashboard/session. Memory localhost:37700 không kết nối; trạng thái đã lưu local.
