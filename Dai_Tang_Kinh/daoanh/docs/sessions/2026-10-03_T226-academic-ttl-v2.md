# T226 — phiên làm việc 2026-10-03

Đã xây dựng application profile TTL 2.0.0, trình tạo/import TTL, API bản nháp, schema/ontology/SHACL và công cụ kiểm tra corpus từng file. Unit/API/schema/SHACL đạt 26/26; kiểm thử UI preview đạt 14/14, không có lỗi trang — `ui-review-fixes.log` và `ui-result.json`. Pipeline trước review đạt exit 0, runtime 2/2; `pipeline-review-fixes.log` sau sửa exit 1 chỉ ở runtime do `ERR_NETWORK_ACCESS_DENIED` với CDN PlaceVN. Cả pipeline chạy lại với quyền mạng đọc đã PASS, exit 0, runtime 2/2 ở `pipeline-review-fixes-network.log`. Xem log và giới hạn kiểm thử trong [báo cáo kết quả](../reports/T226-ttl-profile-20261003/README.md).

**Triển khai còn chờ:** process chính ở cổng 5000 chưa nạp API v2. Windows từ chối dừng process với `Access denied`; cần quyền Administrator/UAC. Form preview ở cổng 5006 đã được kiểm tra. PID preview phải đọc từ `docs/reports/T226-ttl-profile-20261003/preview.pid`, không dùng PID ghi nhớ từ phiên trước.

**Audit hiện tại:** 1.038 file, gồm một template; 1.037 hồ sơ qua kiểm tra cấu trúc, một lỗi template, 10.541 assertion tham chiếu được giữ lại. Bằng chứng: `corpus-current/summary.json` và `corpus-current/manifest.jsonl` trong thư mục báo cáo T226. Kết quả này chưa xác nhận tính đúng đắn lịch sử của các assertion.

Audit ban đầu ghi nhận 1.035 file hợp lệ, ba lỗi và 10.510 assertion, trong đó hai file tự nối bằng `hasDisciple`. SHA hai file đã thay đổi trong workspace dùng chung; audit hiện tại không còn hai cạnh tự nối đó. T226 không ghi sửa vào TTL active và không suy đoán tác nhân thay đổi. Bằng chứng trước/sau nằm trong `shared-workspace-ttl-diff.json`; không tiếp tục trình bày hai lỗi này như lỗi hiện hành.

API/CLI T226 chưa apply vào DB hoặc corpus TTL active. Nguồn được nạp vẫn có trạng thái và chứng cứ riêng; không tự duyệt ID, quan hệ truyền pháp hoặc số đời. DILA local dùng artifact 2026-09, không được gọi là release mới nhất trên web.

Đọc [Handoff đủ 10 mục](../Handoff-2026-10-03-T226-ttl-profile-v2.md), [phân tích và roadmap](../reports/T226-academic-ttl-roadmap.md), [task T226](../../tasks/T226-academic-ttl-profile-v2.md). Việc tiếp theo: nạp lại main bằng quyền phù hợp và kiểm tra qua 8080; sau đó chốt catalog nguồn/quyền từng artifact và đối chiếu định danh toàn corpus trước migration. Các giai đoạn hoàn thiện học thuật và xuất bản vẫn theo roadmap, chưa được tính là hoàn thành.


### Xác minh bổ sung ngày 2026-10-04

Admin xác nhận đã tự xóa cạnh `hasDisciple` trỏ về chính mình trong `TS-Hung-Duong-Hien.ttl` và `TS-Thach-Suong-Khanh-Chu.ttl`. Kiểm tra RDF lại: cả hai file parse được, 0 cạnh tự nối `hasTeacher`/`hasDisciple`; SHA khớp lần audit hiện tại. Bằng chứng: `docs/reports/T226-ttl-profile-20261003/admin-self-edge-removal-verified.json` (đường dẫn từ daoanh). Đây là xác minh lỗi tự nối; chưa chứng nhận toàn bộ quan hệ lịch sử. Pipeline sau review đã PASS với quyền mạng (exit 0), unit 26/26, UI 14/14; main bootstrap cũng PASS.


### Chốt triển khai ngày 2026-10-04 — T226 DONE

Đã mở Windows RunAs/UAC và reload đúng main 5000: PID 22920 → 17212. Schema 2.0.0, API lineages cũ và login qua 8080 đều HTTP 200; UI trên 8080 đạt 14/14, 0 lỗi trang. Bằng chứng `deployment-verified.json`, `reload-status.json`, `ui-deployed-8080.log`; [Handoff mới](../Handoff-2026-10-04-T226-ttl-profile-v2.md). Chưa apply DB/TTL. Các đoạn deployment pending phía trên là trạng thái trước khi reload.
