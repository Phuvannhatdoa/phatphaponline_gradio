# PTDA — phân công subagent và QA

Ngày thiết lập: 2026-10-10. Căn cứ: Admin yêu cầu tạo subagent theo mục đích cụ thể, root chỉ QA và điều phối với Admin.

Admin chốt: từ nay Admin và root giữ QA, quyết định ưu tiên; root chia từng task cụ thể và giao phần triển khai cho các agent. Mỗi giao việc ghi mục tiêu, scope/file, tiêu chí nghiệm thu, chứng cứ, kiểm thử/rollback và báo cáo DONE/PARTIAL/BLOCKED. Đội hiện hành gồm code, debug, deep_research và root. Root giao nhiệm vụ cụ thể theo ưu tiên Admin; tên vai trò không cấp quyền sửa ngoài scope đã giao.

## Vai trò và trách nhiệm

| Vai trò | Phạm vi | Đầu vào | Đầu ra bàn giao cho root |
|---|---|---|---|
| root | Tiếp nhận yêu cầu; chia việc; kiểm tra phạm vi, bằng chứng, diff, tests; giải quyết mâu thuẫn; báo cáo với Admin | Yêu cầu Admin và kết quả các agent | Kết luận QA có giới hạn xác minh; giao việc tiếp hoặc thông báo hoàn tất |
| deep_research | Điều tra kỹ tài liệu kỹ thuật và sử liệu gốc DILA/CBETA/Marcus; đối chiếu định danh, nguồn và mâu thuẫn | Câu hỏi kỹ thuật/sử liệu, nhân vật/ID ứng viên, nguồn được phép | Source/locator chính xác, trích dẫn có vị trí, chứng cứ ủng hộ/bác bỏ, mâu thuẫn, mức chắc chắn và điều chưa xác định |
| debug | Tái hiện lỗi, xác định root-cause, kiểm regression/tests và kiểm độc lập code/ETL/schema/TTL/DB/API; chỉ sửa khi root giao rõ quyền | Triệu chứng, bước tái hiện, file/hash, patch của code, tiêu chí nghiệm thu | Kết quả tái hiện, nguyên nhân với chứng cứ, kiểm regression/ngoài scope, PASS/FAIL có giới hạn; bản sửa chỉ khi được giao quyền writer |
| code | Viết và triển khai code/backend/API/UI, ETL/schema, TTL/DB và tài liệu trong scope được giao; tuân thủ cổng dữ liệu | Đặc tả đã QA, chứng cứ nghiên cứu, file/bảng được phép sửa, tiêu chí nghiệm thu | Patch, dry-run/diff, backup/manifest khi có dữ liệu, kiểm thử phù hợp, kết quả đồng bộ và lệnh rollback |

Root không trực tiếp triển khai thay đổi code/TTL/DB trong mô hình này. Root có thể đọc file, chạy kiểm tra độc lập và điều phối. Quyết định QA không biến dữ liệu còn thiếu chứng cứ thành sự thật lịch sử.

## Chuyển vai trò cũ sang đội hiện hành

| Vai trò cũ | Vai trò hiện hành | Thay đổi phạm vi |
|---|---|---|
| app_integration | code | Mở rộng phần triển khai sang code/ETL/schema/TTL/DB có scope và chứng cứ |
| ttl_data | debug | Mở rộng sang tái hiện, root-cause, regression/tests và kiểm độc lập; không mặc định giữ quyền sửa TTL/DB |
| source_research | deep_research | Điều tra kỹ cả tài liệu kỹ thuật và sử liệu gốc |

Các agent cũ không tiếp tục nhận task mới. Root dùng agent mang vai trò hiện hành; nếu agent không còn trong phiên thì tạo lại theo quyền đã được Admin giao. Kết quả cũ là đầu vào lịch sử, cần kiểm tra hiện hành trước khi nhận claim PASS/DONE.

## Vòng giao việc

1. Root giao việc bằng followup_task cho vai trò phù hợp, hoặc tạo lại agent khi phiên không còn agent đó. Mỗi gói giao việc phải có mục tiêu; scope/file hoặc bảng được phép sửa; thao tác bị cấm; tiêu chí nghiệm thu; chứng cứ cần có và source/locator; test/rollback; đầu ra và báo cáo DONE/PARTIAL/BLOCKED. DONE chỉ dùng khi tiêu chí đã được kiểm đủ; PARTIAL ghi phần đã kiểm/phần còn thiếu; BLOCKED ghi nguyên nhân và điều kiện gỡ.
2. Mỗi file chỉ có một agent được giao quyền sửa trong một lượt. Agent khác chỉ đọc hoặc đề xuất; root cấp lại quyền khi bàn giao đã xong. Một giao dịch DB chỉ có một writer.
3. Agent đọc hướng dẫn áp dụng và dữ liệu hiện hành, kiểm tra hash/trạng thái trước khi ghi. Thay đổi từ session khác phải được giữ nguyên; có lệch đầu vào thì báo root và lập lại kế hoạch.
4. Khi cần xác minh tài liệu kỹ thuật, định danh hoặc sử liệu gốc, root giao deep_research đưa chứng cứ; code lập dry-run và triển khai phần được giao; debug tái hiện và kiểm độc lập trước khi root QA. Task kỹ thuật đơn giản có thể đi trực tiếp code → debug → root QA; không giao nghiên cứu thừa. Debug chỉ triển khai sửa khi root giao rõ scope và quyền writer; không vừa sửa vừa coi kiểm của mình là kiểm độc lập. Các việc độc lập có thể chạy song song; thao tác phụ thuộc phải chờ kết quả và QA.
5. Root kiểm tra độc lập kết quả, mâu thuẫn, giới hạn nguồn và nghiệm thu; trả lại agent nếu chưa đạt. Root cập nhật Admin bằng kết quả có bằng chứng.

Không tự cấp task ID mới hoặc đổi trạng thái task. Nếu cần task mới, root kiểm tra hai tầng theo AGENTS.md rồi mới điều phối cấp ID. Không tự commit/stage; mọi commit phải được giao riêng và tuân thủ SSOT repo root cùng quy trình worktree dùng chung.

## Cổng kiểm soát thay đổi dữ liệu

Trước cập nhật: chứng cứ định danh → diff/dry-run rõ phạm vi → backup file/DB và manifest → QA → kiểm thử cần thiết. Sau cập nhật: kiểm lại file/DB/API tương ứng, so vùng ngoài phạm vi và lưu lệnh hoàn tác. Raw XML bất biến. Không chạy full importer chỉ để sửa một hồ sơ. File TTL đã sửa không đồng nghĩa DB/API đã đồng bộ.

Số đời phải gắn hệ đếm và nguồn. Không tự tăng số đời từ generic teacher, tên giống nhau hay cùng chùa. Chỉ sửa/tăng số đời khi có ít nhất 3 chứng cứ độc lập, chứng minh số hiện tại sai và nêu rõ căn cứ số đúng, hệ đếm, cùng đúng nhân vật/ID. Chưa đủ thì bỏ qua/giữ source_asserted; không nâng accepted hoặc kích hoạt mốc tự động khi chưa đủ bằng chứng cho giá trị và hệ đếm. Ba nguồn không được dựng giả hoặc lấy ba bản sao của cùng một nguồn làm ba chứng cứ độc lập.

A000662 明海 là nhân vật khác Minh Hải Pháp Bảo Chúc Thánh theo quyết định Admin; không gắn owl:sameAs hoặc DILA-ID này cho Minh Hải Pháp Bảo. Hồ sơ Minh Hải hiện dùng định danh PTDA local; đời 71 với Ma Ha Ca Diếp=1 được giữ ở mức source_asserted, chưa tự thành mốc accepted v2.

Với bản build xin review, chạy pipeline/tester bắt buộc theo AGENTS.md; báo đúng bước dừng và tests chưa chạy. Không sử dụng API trả phí, tự chạy lại lô phiên âm 48,6k ID hay thay hạn mức tài khoản nếu chưa được giao. Không cài Hermes trong đợt thiết lập này.

## Khả năng chạy và tính liên tục

Tối đa 4 agent hoạt động cùng lúc, kể cả root: root + code + debug + deep_research. Đây là giới hạn phiên hiện tại. Tên vai trò được lưu trong tài liệu không có nghĩa tiến trình sống vĩnh viễn, lịch chạy tự động hay dịch vụ nền. Khi mở phiên mới, đọc tài liệu, kiểm tra agent hiện có và tạo lại/giao followup theo yêu cầu đã được ủy quyền.

## Giới hạn của đợt thiết lập

Đợt 2026-10-10 chỉ tổ chức đội agent và tạo tài liệu. Không sửa code/TTL/DB, không đổi dashboard/tasktodo, không đồng bộ hồ sơ hoặc hoàn tất build T232/T233. Lượt đổi vai trò hiện hành được ghi trong [session](sessions/2026-10-10_code-debug-deep-research.md) và [Handoff](Handoff-2026-10-10-code-debug-deep-research.md); tài liệu thiết lập trước đó được giữ nguyên.
