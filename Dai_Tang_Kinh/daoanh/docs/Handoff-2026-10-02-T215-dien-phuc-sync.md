# Handoff-2026-10-02-T215-dien-phuc-sync

## 1. Đọc nhanh
T215 in_progress; riêng Tuệ Thăng đã sync. DB/API/rollback mô phỏng PASS. Pipeline exit1 thiếu flask T17867/68. RDF chưa validate thiếu rdflib. TTL không sửa, không commit.

## 2. Đọc trong2 phút
Đã tạo dien_phuc_tue_thang/A008431/延福慧升 đời50; trả metadata duc_vuong_doan_du/A007993/育王端裕 đời49. Tiểu sử mỗi người từ TTL riêng khớp API. Admin đã chốt số đời; không claim3 chứng cứ độc lập. 8 assertions TTL dùng A045939 rejected, giữ lịch sử và DILA/Marcus.

## 3. Thay đổi và căn cứ
TTL Tuệ Thăng chỉ còn Đoan Dụ làm thầy; ID Hán và quan hệ đã đối chiếu DILA. Một transaction:2authority rows; relation Tuệ Thăng→Đoan Dụ; sửa target_label row841 thành Diên Phúc Tuệ Thăng; thêm TTL|A007993|A008431; consensusTTL1/count3. Snapshot sourceDILA/Marcus trước/after không đổi.

## 4. Cảnh báo
TTL Đoan Dụ vẫn lặp an_hoa_van_nhat và gắn2nhãn vào dien_phuc_tue_thang; chỉ khôi phục metadata, KHÔNG full-import các quan hệ đó. 8 assertions sai đã truy sourceTTL dùng slug Đoan Dụ; chưa tự dựng lại các cạnh khác. Không chạy importer skip/insert-only hoặc rematch rộng.

## 5. Revert
Trong daoanh chạy:
```powershell
python -X utf8 data/backups/T215-dien-phuc-sync-20261002/sync_case.py --revert
```
Backup gồm2TTL, db-rows-before.json, sync-report.json before/after, sync_case.py, API/pipeline outputs. Guard so scoped DB hiện tại với after; có sửa mới thì dừng. Rollback thử SQLite in-memory PASS. Revert DB sẽ trả lại dữ liệu cũ bao gồm lỗi A045939; TTL không sửa nên không cần restore.

## 6. File
Tạo backup/report/script và Handoff. Sửa hồ sơ cases.json/README.md, dashboard t215-self-edges.html/t215-cases.json và dashboard_process.html, task T215. Các hồ sơ recheck cũ là lịch sử.

## 7. Bài học
Không chỉ đổi tên row cũ: sẽ nhập thầy và trò làm một. Ba đồng môn đã bị gán hasTeacher, Admin sửa rồi mới sync. Đọc lại evidence TTL mới khi cập nhật Dashboard, không dùng snapshot4thầy cũ.

## 8. Chưa xong
8hồ sơ khác; RDF toàn corpus; môi trường Flask test; review TTL Đoan Dụ trước expanded import. Các cạnh TTL phụ thuộc mappingA045939 vừa rejected cần xác minh endpoint để dựng lại. Không tự đổi mọi A045939 thành A007993. Các lỗi địa danh/name_vi nền từ nguồn khác ngoài scope này.

## 9. Kiểm nhanh
API /daoanh/api/monk/A008431/lineage-tree?up=1&down=1: Diên Phúc Tuệ Thăng50, bioVi đúngTTL, cạnh A007993→A008431 có3nguồn. APIA007993: Dục Vương Đoan Dụ49 và bio riêng. Dashboard hồ sơ1 đã sync. TTL assertions active liên quanA045939=0.

## 10. Agent tiếp
Đọc report/hash trước mutation; script chặn apply lại nếu report đã tồn tại. T215 toàn corpus còn in_progress. Không sửa số đời bằng suy luận; chỉ case có chứng cứ. Không ghi đè DILA/Marcus.

Validation cuối: DashboardHTTP200/9article/case1synced; E2E kiểm cú phápHTML hiện cóPASS (không phải browser runtimeE2E). tasktodo đã cập nhật qua quyền ghi reparsepoint. Memoryservice không kết nối được, handofflocal đã lưu.
