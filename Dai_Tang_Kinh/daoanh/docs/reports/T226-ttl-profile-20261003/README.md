# T226 — kết quả xây dựng và triển khai, chốt ngày 2026-10-04

Đã xây dựng và triển khai application profile TTL 2.0.0 trên [trang tạo TTL chính](http://localhost:8080/daoanh/admin/monk_ttl_add.html). **T226 DONE:** unit 26/26, UI trên 8080 14/14, toàn pipeline PASS. T226 chỉ tạo bản nháp staging; chưa apply dữ liệu vào DB hoặc TTL active. Đọc [phân tích và roadmap](../T226-academic-ttl-roadmap.md), [task](../../../tasks/T226-academic-ttl-profile-v2.md) và [Handoff](../../Handoff-2026-10-04-T226-ttl-profile-v2.md).

## Phần đã xây dựng

- Model/renderer/parser: `src_python/ttl_profile_v2.py`.
- API Blueprint: `api_ttl_profile_v2.py`, được đăng ký bổ sung trong `app.py`.
- Editor: `admin/monk_ttl_add.html` và `admin/ttl-profile-v2.js`.
- Contract: `ontology/ttl-profile-v2/schema.json`, `ontology.ttl`, `shapes.ttl`.
- Reader DILA XML 2026-09 đọc từng record bằng `iterparse`, giữ XML và snapshot tên, biệt danh, ngày, tác phẩm, quan hệ nguyên bản. Release DILA 2026-10 trên web chưa được import.
- Reader CBETA/Marcus đọc dữ liệu đã index theo ID. Ví dụ A000885 có 45 mục nhắc đến trong CBETA, một crosswalk Marcus và 34 cạnh mạng gốc. Cạnh mạng không tự trở thành quan hệ truyền pháp.
- Save yêu cầu session Admin hợp lệ; lưu revision bản nháp theo nội dung ở staging. API/CLI T226 không apply DB và không gọi ETL tính đời.
- Cổng xuất bản kiểm quyền từ registry, không tin checkbox phía client. Cả 14 nguồn trong bản kiểm kê đang `license_verified=0`; chưa đủ điều kiện mở xuất bản công khai.

Các trường chuyên sâu được bảo toàn trong snapshot XML/JSON nhưng chưa phải tất cả đều được ánh xạ thành ontology chuyên ngành. Application profile này là thiết kế của dự án dựa trên các chuẩn đã đối chiếu; không tuyên bố đạt toàn bộ CIDOC CRM hoặc một chuẩn Phật giáo quốc tế duy nhất.

## Kiểm chứng hiện tại

| Kiểm tra | Kết quả / artifact |
|---|---|
| Unit/API/schema/SHACL | 26/26 PASS; bước `test:t226` trong `pipeline-review-fixes.log` (unit đã hoàn tất; pipeline chạy lại có quyền mạng cũng đạt exit 0) |
| UI preview | 14/14 PASS, không có lỗi trang; `ui-result.json` liệt kê đủ 14 thao tác, log ở `ui-review-fixes.log` |
| Pipeline | Bản trước review: exit 0, runtime 2/2. Sau sửa: `pipeline-review-fixes.log` exit 1 chỉ ở runtime do CDN bị chặn; cả pipeline chạy lại với quyền mạng đọc đã PASS, exit 0, runtime 2/2 ở `pipeline-review-fixes-network.log` |
| Main process | Reload qua Windows Administrator/UAC thành công: PID 22920 → 17212, schema 2.0.0; `reload-status.json` |
| Form qua 8080 | Đã nạp API v2: schema/lineages/login HTTP 200; UI 14/14 PASS, 0 lỗi trang; `deployment-verified.json`, `ui-deployed-8080.log` |
| Preview | Đã dùng để kiểm thử trước deployment; server tạm 5006 đã dừng đúng PID sau khi UI8080 PASS. Khi kiểm lại dùng T226_UI_BASE_URL=http://localhost:8080 |
| Audit corpus hiện tại | 1.038 file, gồm một template; 1.037 hồ sơ hợp lệ về cấu trúc, một lỗi template, 10.541 assertion; `corpus-20261004-final/summary.json` và `manifest.jsonl`; input hash đối chiếu lại 1038 file, 0 mismatch |
| Apply của T226 | Chưa apply vào DB hoặc corpus TTL active; xem `production_modified: false` trong summary và manifest rollback |

`valid` trong audit chỉ xác nhận việc parse/chuyển đổi và các ràng buộc đã kiểm tra. Kết quả không xác minh toàn bộ danh tính, thầy/trò, số đời hay sự độc lập học thuật của các chứng cứ.

## Audit ban đầu và thay đổi trong workspace

Audit ban đầu ghi nhận 1.038 file, 1.035 file hợp lệ, ba lỗi và 10.510 assertion. Hai lỗi là cạnh `hasDisciple` tự nối trong `TS-Hung-Duong-Hien.ttl` và `TS-Thach-Suong-Khanh-Chu.ttl`. Kết luận cũ “không còn tự nối toàn corpus” khi đó không bao phủ đầy đủ chiều `hasDisciple`.

SHA hai file đã thay đổi trong workspace dùng chung. Audit **hiện tại** không còn hai cạnh tự nối này và chỉ còn lỗi `0-template.ttl`. T226 không ghi sửa TTL active; không suy đoán tác nhân thay đổi. Bằng chứng SHA trước/sau, số đo ban đầu/hiện tại và kết quả đối chiếu hash nằm trong [shared-workspace-ttl-diff.json](shared-workspace-ttl-diff.json).

`0-template.ttl` có `generationOrder` rỗng và URI tham chiếu rỗng; đây là template chưa điền, không phải hồ sơ Person sẵn sàng import. Không tự điền ID, thầy/trò hoặc số đời để làm template qua kiểm tra. Việc hai lỗi cấu trúc đã hết cũng không chứng minh các quan hệ thay thế là đúng về lịch sử.

## Giới hạn kiểm thử và hạ tầng

Đã kiểm chứng lỗi ghi chung `.last-run.json` và ảnh `tests/screenshots/placevn-load.png` trên Windows. Runner tạo output riêng cho từng lần chạy; screenshot dùng `testInfo.outputPath`. Không xóa kết quả của session khác.

Lần pipeline sau review gặp `ERR_NETWORK_ACCESS_DENIED` khi tải font/Tailwind/CDN trang PlaceVN; runtime một test fail, một test pass. Không sửa code để né lỗi. Cả pipeline chạy lại với quyền mạng đọc đã PASS, exit 0; runtime 2/2. Bằng chứng: `pipeline-review-fixes-network.log` và `pipeline-status.json`.

Runtime PlaceVN không tìm thấy nút “Mapping Tên Việt”, nên nhánh click đó chưa được kiểm tra. Hai runtime test PlaceVN xác nhận tải trang/API trong phạm vi test; UI TTL v2 có bộ thao tác kiểm tra riêng. Audit T166 còn một cảnh báo baseline về credential trong code; T226 không sửa cấu hình credential hoặc công bố giá trị.

## Lệnh kiểm tra

Chạy tại thư mục `daoanh`:

~~~powershell
$env:PYTHONPATH='data/backups/T226-ttl-profile-20261003/python-deps;data/backups/T215-fix-sync-20261002/python-deps'
npm.cmd run test:t226
$env:T226_UI_BASE_URL='http://localhost:8080'
node tests/t226-ui-check.cjs
npm.cmd run pipeline
python -X utf8 scripts/t226_rollback.py
~~~

Dev dependencies được pin ở `requirements-ttl-v2-dev.txt`; môi trường test cài riêng dưới backup T226, không thay Python hệ thống. Các log PowerShell gốc có thể là UTF-16LE; ưu tiên bản `*-utf8.log` khi đã có.

## Triển khai và hoàn tác

Lần restart trực tiếp ban đầu bị Windows Access denied. Sau đó đã mở RunAs/UAC và chạy script có guard app hash/process đúng main 5000; reload thành công. Gateway 8080, login và API lineages cũ đều HTTP 200. UI v2 trên origin chính đã PASS 14/14; save cần session Admin hợp lệ và chỉ lưu staging. Không copy lại app.py từ backup để nạp server.

Rollback code dùng `rollback-manifest.json` và `scripts/t226_rollback.py`: kiểm hash trước, chỉ apply khi guard đạt. Manifest ghi 16 file, trong đó bốn file có backup gốc. Staging giữ nguyên; T226 không có DB/TTL active cần restore. Trong workspace dùng chung, không bulk `git add` và không restore backup khi checksum hiện tại khác manifest. Git phải chạy từ repo top-level `visjs-app`.

Migration toàn corpus, đối chiếu định danh, resource cho event/place/work/review/counting scheme, resolver HTTP và phát hành học thuật còn theo roadmap P0–P6; chưa được thay thế bởi việc xây dựng editor v2.


### Xác minh bổ sung ngày 2026-10-04

Admin xác nhận đã tự xóa cạnh `hasDisciple` trỏ về chính mình trong `TS-Hung-Duong-Hien.ttl` và `TS-Thach-Suong-Khanh-Chu.ttl`. Kiểm tra RDF lại: cả hai file parse được, 0 cạnh tự nối `hasTeacher`/`hasDisciple`; SHA khớp lần audit hiện tại. Bằng chứng: `docs/reports/T226-ttl-profile-20261003/admin-self-edge-removal-verified.json` (đường dẫn từ daoanh). Đây là xác minh lỗi tự nối; chưa chứng nhận toàn bộ quan hệ lịch sử. Pipeline sau review đã PASS với quyền mạng (exit 0), unit 26/26, UI 14/14; main bootstrap cũng PASS.
