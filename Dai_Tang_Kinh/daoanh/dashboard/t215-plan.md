---
id: T215
title: Xác minh TTL theo DILA ID và xử lý 9 cạnh tự nối
module: TTL Thiền Sư VN
priority: high
status: in_progress
depends_on: [T204, T211]
created: 2026-10-02
updated: 2026-10-02
done_when: Có hồ sơ bằng chứng cho toàn corpus; chỉ sửa và sync case xác nhận được, case thiếu chứng cứ được bỏ qua và ghi rõ, audit DB/API sau áp dụng đạt yêu cầu.
---

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
- [ ] RDF toàn corpus được kiểm trong môi trường đủ thư viện.
- [ ] Khóa danh tính các endpoint của change-set, kiểm tác động mapping local.
- [ ] Có change-set chỉ gồm trường đủ chứng cứ; số đời thiếu 3 chứng cứ giữ nguyên.
- [ ] Backup/rollback có guard và đồng bộ DB riêng nguồn TTL.
- [ ] DB/API + audit lại + pipeline đạt; case thiếu chứng cứ được ghi skipped.

## Hạn chế hiện tại
Python CLI thiếu rdflib và flask; pipeline chung dừng T178 67/68 PASS. Thụy Nham Trí Tài chưa xác minh được DILA chính thức, bỏ qua cập nhật. Các đề xuất subject cần đối chiếu tiểu sử trước apply. Task còn in_progress.
