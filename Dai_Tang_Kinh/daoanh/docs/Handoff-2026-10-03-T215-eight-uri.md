# Handoff — 2026-10-03 — T215 đối chiếu 8 URI TTL

## 1. Bảng thông tin đọc nhanh

| Mục | Kết quả |
|---|---|
| HEAD quan sát | 742ce2b19b4e752eaab28fe62031865f81bc5d67; phiên này không commit |
| Phạm vi | 8 URI Admin nêu, nối tiếp T215 |
| TTL | Sửa2 file;5 file chưa xác minh;Linh Cưu không tồn tại |
| DB / đời | Chỉ đọc, chưa sync; không đổi số đời |
| RDF | 7/7 file hiện có và3/3 bản chuẩn bị/ứng viên PASS |
| Pipeline | T20325PASS/2FAIL;5 TTL khác còn40 ký tự Ð |
| Tester | lint/test/E2E static PASS;PlaceVN runtime FAIL |
| HTTP / revert | 3 URL200;rollback dry-run PASS |

## 2. Đọc trong2 phút

Đã kiểm cả8 hồ sơ;chưa hoàn tất sửa8/8. Phước Châu A003636 và Đại Ninh A020545 được bổ sung nhãn Hán, owl:sameAs, nguồn và định danh thầy. Phước Châu có tóm tắt Việt từ DILA;Đại Ninh giữ toàn tiểu sử Việt và sửa dòng phái về Lâm Tế theo DILA. Không đổi URI, thầy hoặc số đời37/45.

Tiếp theo: khóa5 danh tính còn lại;hợp nhất2 file Đại Ninh;sửa provenance DB Thạch Cữu trỏ filename Linh Cưu đã thiếu. Dashboard:/daoanh/dashboard/t215-eight-uri.html.

## 3. Đề xuất từng case và bằng chứng

Chi tiết đầy đủ từng dòng tại docs/reports/T215-eight-uri-20261003/README.md và cases.json. Phước Châu A003636→A001897, Đại Ninh A020545→A001439 đã xác nhận. Di Phong có ứng viên A015708 夷峯方寧 nhưng tên Phương Ninh khác Kính Ninh, chưa gán. Đột Không Trí Bản chưa ID;không dùng Đột Không Thăng A020174. Đại Xá/Minh Hoằng chưa ID và có hai khối Phong Huyệt trộn. Tuyết Giàu chưa chứng minh cùng người với A000960 雪槱真樸. Linh Cưu không thể dựng từ Thạch Cữu A019919. Hai file Đại Ninh cùng người/cùng URI, không phải người khác chiếm URI.

## 4. Cảnh báo bắt buộc

Worktree nhiều session:không stage cây thư mục hoặc revert HEAD chung. Không import toàn bộ các file trộn Phong Huyệt. Chưa quarantine thật hoặc sửa importer. No-match trong XML2026-09 không chứng minh người không tồn tại trong mọi phiên bản DILA. Giữ cú pháp legacy để tương thích regex importer;chưa migrate toàn corpus sang pth:.

## 5. Hoàn tác

Trong daoanh,chạy python -X utf8 data/backups/T215-eight-uri-20261003/rollback.py để kiểm khô;thêm --apply khi muốn khôi phục2 TTL. Script bảo vệ hash trước ghi, dừng nếu session khác đã sửa. DB không có thay đổi. Dashboard chính chỉ thêm link:t215-eight-uri.html;hoàn tác bằng gỡ riêng link,không restore toàn file khi có WIP khác.

## 6. File tạo/sửa

Hai TTL:TS-Phuoc-Chau-Dai-An và TS-Dai-Ninh-Dao-Khoan. Báo cáo/evidence/scripts/validation/log ở docs/reports/T215-eight-uri-20261003. Backup7 TTL,manifest2changes,rollback và Dashboard trước patch ở data/backups/T215-eight-uri-20261003. Dashboard mới:t215-eight-uri.html và t215-eight-uri-cases.json. Append tasktodo và task T215;log session và Handoff này.

## 7. Sai lầm và bài học

Lượt lọc đầu thiếu tên rút gọn夷峰/夷峯;đã mở rộng, phát hiện A015708 nhưng không gán tên khác. Bản chuẩn bị đầu đi qua Python write_text tạo CRCRLF;parser raw phát hiện. Đã sửa về LF,cập nhật manifest và kiểm byte sau ghi PASS. Cần kiểm raw byte thay vì chỉ read_text tự chuẩn xuống dòng.

## 8. Việc chưa xong

Khóa5 danh tính và quan hệ;Tuyết Giàu↔雪槱;hợp nhất Đại Ninh;sửa provenance Thạch Cữu. Thiếu3 chứng cứ độc lập để thay đời. Chưa sync2 TTL vào DB,chưa tạo Linh Cưu. Không chốt8/8 Done. Pipeline và PlaceVN runtime còn fail,chưa yêu cầu duyệt triển khai.

## 9. Kiểm tra nhanh

Từ Dai_Tang_Kinh:python -X utf8 daoanh/docs/reports/T215-eight-uri-20261003/verify_prepared.py;python -X utf8 daoanh/data/backups/T215-eight-uri-20261003/rollback.py. postcheck.py kiểm hash7file và DB snapshot;nếu session khác đã đổi,cần đọc diff. Xem validation.json,postcheck.json,http-checks.json. Không chạy lại build_report.py để ghi đè snapshot trước sửa.

## 10. Ghi chú agent kế tiếp

Đọc README/cases/dila-evidence trước. A000960/A015708 vẫn là ứng viên. Không thêm owl:sameAs hay thầy/trò chỉ do tên hiệu gần giống. DB provenance chưa sửa. Memory localhost37700 ghi thất bại(fetch failed);đã lưu bàn giao local. Tiếp tục T215,không cấp ID trùng hoặc commit WIP của session khác.


### Quyết định Admin bổ sung — 2026-10-03
Đã gỡ candidate_id A015708 khỏi đề xuất case Di Phong Kính Ninh; DILA ID null, không sync. Quyết định và backup ở reports/T215-eight-uri-20261003/di-phong-id-withdrawal/decision.md. Phần mô tả ứng viên phía trên là lịch sử đã bị thay thế. Trí Bản Đột Không chỉ kết luận chưa tìm ID phù hợp, không khẳng định DILA tuyệt đối không có.


### Hiển thị rút gọn theo yêu cầu Admin — 2026-10-03
Dashboard8URI và README chỉ hiện filename/status. ĐạiNinh DONE vì đãsyncDB/API;7filecòn lại đểstatusrỗng. JSONpublic cũngchỉfilename/status;cases.jsonnộibộ giữbằngchứng vàdisplay_status. Bảnhiểnthị/báocáo trướcđược giữtại history-before-compact-20261003. KhôngđổiTTL/DB. HTTP200,8rows,1DONE,7blankđãkiểm.


### Admin yêu cầu lưu chứng cứ dưới filename — 2026-10-03
Thay thế yêu cầu để trống nội dung trước đó:7filename chưaDONE có details chứa chứng cứ, vẫn để statustrống. evidence/TS-*.ttl.md lưu7hồ sơ nguồn/điều chưa rõ/điều bác bỏ/hướng tạoTTL. JSONpublic có evidence; JSONnội bộ giữ đầyđủ lịch sử và reconstruction_evidence. Phần đã bác bỏ không được dùng để gánID hoặc quan hệ. KhôngđổiTTL/DB/sốđời. ĐạiNinh giữDONE.
