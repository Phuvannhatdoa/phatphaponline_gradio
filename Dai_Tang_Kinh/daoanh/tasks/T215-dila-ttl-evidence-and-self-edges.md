---
id: T215
title: Xác minh TTL theo DILA ID và xử lý 9 cạnh tự nối
module: TTL Thiền Sư VN
priority: high
status: done
depends_on: [T204, T211]
created: 2026-10-02
updated: 2026-10-10
done_when: Có hồ sơ bằng chứng cho toàn corpus; chỉ sửa và sync case xác nhận được, case thiếu chứng cứ được bỏ qua và ghi rõ, audit DB/API sau áp dụng đạt yêu cầu.
---

> **Admin xác nhận DONE 2026-10-10.** Mục còn ghi nhận mở (không chặn DONE): 6 hồ sơ URI thiếu danh tính; 783 file có cờ chưa xác minh; 26 cặp đời cần đối chiếu.


# T215 — Xác minh TTL theo DILA ID

## Mục tiêu
DILA ID là định danh chuẩn. TTL chỉ tham chiếu bản Việt dịch của đúng nhân vật DILA, không ghi đè dữ liệu DILA theo suy đoán. Admin phê chuẩn kế hoạch ngày 2026-10-02; bắt đầu bằng 9 cạnh tự nối đã phát hiện trong audit toàn corpus.

## Quy tắc Admin đã phê chuẩn
- Xác minh tên chính/alias Hán trong DILA và bản Việt hóa TTL là cùng người; tên file hoặc tên lõi trùng không đủ để gán ID.
- Không tăng/giảm số đời theo công thức thầy + 1. Chỉ sửa khi có ít nhất 3 dữ liệu xác minh độc lập, chứng minh số cũ sai và số đúng theo một quy ước đếm được nêu rõ. Ba bản sao cùng nguồn không tính là ba chứng cứ.
- Phân biệt thầy truyền pháp, thầy xuất gia, người từng tham học và đồng môn. Không ép tất cả thành cạnh truyền pháp.
- Không xác nhận được thì bỏ qua và ghi lý do; giữ nguyên dữ liệu nguồn. Không tạo ID, quan hệ hoặc bản dịch tên bằng suy đoán.
- Mỗi thay đổi cần before/after, nguồn, SHA256 đầu vào, backup TTL và snapshot DB đúng phạm vi, rollback có guard; không sửa raw XML/docx.

## Phạm vi
1037 TTL local đã quét sơ bộ, không nạp toàn corpus vào RAM. Đợt1: 9 self-edge. Kết quả sơ bộ: 30 cặp đời cần review, 9 self-edge và 3 multi-node cycle witnesses. Đây là cờ kiểm tra, không phải danh sách được tự sửa.

## Kế hoạch chi tiết
1. Đóng dấu đầu vào từng file: subject, nhãn, P1, thầy/trò, đời, hệ truyền thừa, hash và dòng lỗi.
2. Kiểm RDF bằng rdflib trong môi trường hợp lệ; thiếu parser phải báo chưa kiểm, không báo sạch. Audit cả nhiều subject/file và subject trùng file.
3. Khóa danh tính theo DILA chính thức: ID + tên/alias Hán + địa điểm/niên đại/tiểu sử khi cần; so với ID local, không tin ánh xạ local tuyệt đối.
4. Xác minh quan hệ theo DILA và trích dẫn gốc; kiểm chứng hai chiều nếu có. Vắng cạnh DILA không đồng nghĩa TTL sai.
5. Số đời: lập 3 chứng cứ độc lập, chứng minh hệ đếm, số cũ sai, số đề xuất đúng; không đủ thì giữ nguyên.
6. Sinh change-set từng field, trạng thái confirmed/conditional/skipped, kèm tác động DB. Không replace URI toàn file vì cùng URI có thể đang chỉ một người khác ở target hoặc label.
7. Trước apply: backup có thể khôi phục + transaction + kiểm hash/old value; sửa riêng nguồn TTL, không ghi đè assertions DILA/Marcus hay dữ liệu đã duyệt. Cạnh rejected không được góp consensus. Không gọi full importer hiện đang skip file đã có và insert-only.
8. Sau apply: đọc TTL, DB và API hiển thị; audit self-edge, vòng, mapping; chạy test có ý nghĩa và pipeline; rollback khi lệch.
9. Cập nhật hồ sơ, Dashboard, session; ghi riêng case bỏ qua và lý do. Không đánh dấu task done khi còn bước xác minh/apply chưa hoàn tất.

## Đợt 1 — Hồ sơ 9 cạnh
- Hồ sơ: [T215-self-edges](../docs/reports/T215-self-edges/README.md).
- Dữ liệu có cấu trúc: ../docs/reports/T215-self-edges/cases.json.
- Dashboard: /daoanh/dashboard/t215-self-edges.html.
- Chín hồ sơ đã load; đã nêu đề xuất cụ thể hoặc lý do bỏ qua. Chưa áp dụng TTL/DB.
- DILA ID local có điểm khác nguồn chính thức: Vô Chuẩn Sư Phạm A045360 local vs A004697 chính thức; Động Sơn Trạch Ngôn/Phạm Ngôn cần kiểm A010985/A021072 local vs A020683/A020673 chính thức.
- T211 dùng replace URI toàn file: backup Diên Phúc và Vô Chuẩn cho thấy target thầy đã có self-edge từ trước; replace toàn file đổi luôn target và nhãn thầy. Cần sửa theo vai trò triple, không chỉ đếm triple không đổi.

## Acceptance criteria
- [x] Ghi quy tắc DILA/TTL/số đời đã được Admin phê chuẩn.
- [x] Hoàn tất audit sơ bộ toàn corpus, lưu danh sách theo file.
- [x] Load 9 hồ sơ với lỗi thực tế, nguồn đối chiếu, đề xuất và trạng thái chưa apply.
- [x] Admin xem được kế hoạch và 9 hồ sơ trên Dashboard.
- [x] RDF toàn corpus được kiểm trong môi trường đủ thư viện: audit mới1038/1038 PASS.
- [ ] Khóa danh tính các endpoint của change-set, kiểm tác động mapping local.
- [ ] Có change-set chỉ gồm trường đủ chứng cứ; số đời thiếu 3 chứng cứ giữ nguyên.
- [ ] Backup/rollback có guard và đồng bộ DB riêng nguồn TTL.
- [ ] DB/API + audit lại + pipeline đạt; case thiếu chứng cứ được ghi skipped.

## Hạn chế hiện tại
Trạng thái cũ đã được xử lý: rdflib/Flask có trong môi trường phụ thuộc riêng; Trí Tài đã xác minh bằng XML DILA2026-09 và đồng bộ. Hạn chế hiện tại: chưa xác minh toàn bộ endpoint/đệ tử và các cờ corpus. Số đời giữ nguyên khi thiếu3 chứng cứ. Task còn in_progress.


## Recheck Diên Phúc — 2026-10-02

Admin sửa TTL đã hết self-edge. Chưa submit DB: hasTeacher vẫn chứa3 đồng môn ngoài Đoan Dụ. DB row duc_vuong_doan_du đang chứa dữ liệu Tuệ Thăng và gán A045939; chưa có dien_phuc_tue_thang. Xem [recheck](../docs/reports/T215-self-edges/dien-phuc-recheck-2026-10-02.md). Số đời50 giữ nguyên.


## Đã đồng bộ Tuệ Thăng — 2026-10-02

Admin chốt Tuệ Thăng50/thầy Đoan Dụ49 và yêu cầu sync. DB_CASE_PASS + LIVE_API_CASE_PASS: A008431/延福慧升 riêng, thầy A007993/育王端裕; tiểu sử mỗi người theo TTL riêng. Rejected8 assertions TTL dùng sai A045939; giữ DILA/Marcus. Rollback thử trên DB mô phỏng PASS. Backup data/backups/T215-dien-phuc-sync-20261002. Chưa import các quan hệ bất thường trong TTL Đoan Dụ. Task toàn corpus vẫn in_progress,8 hồ sơ còn lại chưa apply.


## Kiểm lại 9 TTL sau Admin cập nhật — 2026-10-02
- Đọc lại 9 file thực tế: còn 2 self-edge, 1 nhãn thiếu quote.
- Tuệ Thăng: DB/API vẫn khớp, đời50.
- Phần Dương: sync metadata + hasTeacher A004983 → A004984, đời43 từ TTL; không chứng nhận/đổi ánh xạ đệ tử. Backup + rollback thử PASS.
- 7 case không sync: lỗi TTL hoặc chồng định danh DB. Xem [báo cáo từng case](../docs/reports/T215-self-edges/recheck-2026-10-02.md).
- Không sửa TTL; không đổi assertions DILA/Marcus. T215 tiếp tục in_progress.


## T215 sửa TTL + sync — 2026-10-02
Đã sửa7TTL, RDF12/12PASS, 9case selfedge0. 8case có metadata/thầy xácminh; TríTài chỉ bỏself, IDchờxácminh. TáchHưngHóa/CảnhPhương; khôiphụcĐạoBình, gỡIDA014617gánsaiPhổDung. KhôngđổisốđờiTTL. Backup/rollback: data/backups/T215-fix-sync-20261002. Chi tiết docs/reports/T215-self-edges/fix-sync-2026-10-02.md. T215 in_progress vì còn auditcorpus/IDđệ tử.


## T215 — Case7 Trí Tài đã xác minh/sync (2026-10-02)
- Gói XML DILA chính thức2026-09 xác nhận A026976瑞巖智才, teacherA013875石門守進; hai chiều khớp.
- TTLTríTàiAdminđãsửa đúng. TTLThủTấn sửa subject rỗng/deathEvent; DB/API tiểu sử và thầy đúng, đời44/43giữ nguyên.
- Xóa processed birth1556/death693 do trích sốkinh/trang, XMLkhôngcódates.
- RDF2/DB/API/rollbackPASS. Chi tiết docs/reports/T215-self-edges/tri-tai-sync-2026-10-02.md; backup data/backups/T215-tri-tai-sync-20261002.
-9case định danh/thầy xác minh; không tuyên bố toàn bộ quan hệ đệ tử/corpus sạch. T215 in_progress.


## T215 — Kiểm đồng bộ9 và audit phần còn lại (2026-10-02)
9/9 metadata/DILA/tiểu sử/số đời/thầy đã xác minh khớp DB/API; không cần ghi lặp DB. Phục hồi TTL Nguyên Liên bị quay lại tự làm thầy → Thủ Sơn Tỉnh Niệm A004983, backup có guard: data/backups/T215-nine-final-sync-20261002. Audit mới1038/1038 RDF, self0, cycle witnesses3, subject collisions6, khối chủ thể lặp3file, URI rỗng1file. 26cặp đời chỉ review, không đổi. [Báo cáo](../docs/reports/T215-post-sync-audit-20261002/README.md); Dashboard /daoanh/dashboard/t215-other-ttl-bugs.html. Chín case chính hoàn tất, T215 toàn corpus vẫn in_progress; chưa xác minh toàn bộ đệ tử/ID còn lại.


## T215 — 8 URI TTL (2026-10-03)

8/8 hồ sơ đã kiểm; 2 TTL (Phước Châu A003636 / Đại Ninh A020545) đã bổ sung định danh DILA; 5 file chưa khóa ID; Linh Cưu không tồn tại. Giữ mọi số đời; DB chỉ đọc, chưa sync. RDF 7/7 file đích hiện có và 3/3 bản chuẩn bị/ứng viên PASS; rollback dry-run PASS. Pipeline T203: 25 PASS / 2 FAIL; Tester PlaceVN runtime FAIL. Dashboard: /daoanh/dashboard/t215-eight-uri.html. Báo cáo: docs/reports/T215-eight-uri-20261003/README.md; bàn giao: docs/Handoff-2026-10-03-T215-eight-uri.md. T215 in_progress; chưa chốt 8/8 sửa xong.


## T215 — Đại Ninh đồng bộ DB (2026-10-03)

Đại Ninh A020545 / thầy Thạch Sương A001439 đã sync metadata và nhãn quan hệ local, DB/API/RDF/rollback PASS. Giữ đời45; cạnh DILA/Marcus/TTL đã đúng nên không ghi lặp. Case4 đã update Dashboard. X1667 xác nhận Trí Bản tại0560a04;0560a03 không phải ĐạiXa. Các case này chưa ID mới. Báo cáo docs/reports/T215-dai-ninh-sync-20261003/README.md; Handoff-2026-10-03-T215-dai-ninh-sync.md. T215 toàn corpus in_progress.

## T215 — closeout có chứng cứ, 2026-10-03

Đã sync Phước Châu, hợp nhất Đại Ninh, sửa provenance Thạch Cữu và ID Mã Tổ/Phong Huyệt, phục hồi Phật Ý. Cách ly7file, sửa40ký tự/5TTL. Audit 1037/1037 RDF;0 tự nối/URI trùng/vòng. Giữ nguyên26cặp đời. Rút142 TTL assertion sai, bổ sung72assertion/36 cặp;44 đề xuất chưa chứng minh bỏ qua. DB/API/rollback/Dashboard PASS. Pipeline đã chạy; runtime retry có mạng2/2 PASS (nhánh click Mapping chưa được suite thực thi).

T215 in_progress ở chứng cứ học thuật:6 hồ sơ URI thiếu danh tính giữ status trống,783 filecó cờ và26 cặp đời cầnđối chiếu. Không suy ID/đời. [Report và rollback](../docs/reports/T215-closeout-20261003/README.md).

