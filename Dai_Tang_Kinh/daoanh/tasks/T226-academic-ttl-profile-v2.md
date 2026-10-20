---
id: T226
title: Hồ sơ TTL học thuật v2 cho Phật Tổ Đạo Ảnh
module: TTL Thiền Sư VN
priority: high
status: done
depends_on: [T215, T217, T223]
created: 2026-10-03
updated: 2026-10-04
done_when: Có application profile/version, schema/ontology/shapes, form tạo nhập TTL v2, validation/export nguồn và kế hoạch migration có kiểm chứng; API v2 hoạt động trên server chính qua 8080.
---

# T226 — TTL học thuật v2

Admin yêu cầu phân tích mô hình đa nguồn, nâng cấp trang `monk_ttl_add.html` và lập roadmap. T226 xây dựng cấu trúc và luồng bản nháp; chưa apply chuyển đổi vào DB hoặc corpus TTL active. Không tự suy số đời, thầy truyền pháp hoặc đồng nhất nhân vật chỉ từ tên.

## Kế hoạch trước build

1. Đối chiếu W3C RDF 1.1, PROV-O, SHACL, DCAT, CIDOC CRM và các nguồn chính thức DILA/CBETA/Marcus.
2. Thiết kế mô hình Person / IdentifierAssignment / SourceRecord / Assertion / Review / CountingScheme / Dataset. URI của dự án ổn định; DILA là authority chính trong phạm vi Hán truyền. Mapping sang bộ định danh khác phải có trạng thái và chứng cứ. Các thành phần chưa có resource chuyên biệt được phân kỳ trong roadmap.
3. Viết JSON contract, vocabulary ontology, SHACL, renderer/validator và reader legacy dùng RDF. Assertion chưa được chấp nhận không chiếu thành fact trực tiếp.
4. Nâng form với nguồn dẫn, citation, phiên bản, quyền dùng, loại quan hệ rõ và quy ước đếm đời. Khi chấp nhận số đời, yêu cầu ít nhất ba gốc chứng cứ độc lập; giữ luồng Tạo TTL từ `person.html`.
5. Viết API render/import/validate và save bản nháp có xác thực, chỉ lưu staging v2. Không gọi full ETL hoặc tự tính đời. Công cụ chuyển đổi đọc từng file, tạo manifest/hash và đối chiếu trước apply.
6. Kiểm tra ngữ nghĩa, roundtrip, bảo toàn triple chưa ánh xạ, định danh, quyền chia sẻ và UI; chạy pipeline; cập nhật docs, Dashboard, Handoff và session.

## Phạm vi nguồn

Tài liệu cũ ghi 20 nguồn; kiểm kê DB ghi nhận 14 `data_sources`, 14 `source_authority` và 10 `dataset_sources`. Chưa xác minh đủ danh mục 25 nguồn Admin nhắc đến. Cấu trúc mở để bổ sung bộ định danh sau này, không hard-code số 25 hoặc tuyên bố tất cả đã tích hợp.

DILA trên web có release 2026-10; artifact local đang nạp là 2026-09. Phải ghi đúng phiên bản và checksum, không gọi bản local là mới nhất. Quyền sử dụng cần xét theo từng artifact; không tự chọn một license chung cho tất cả nguồn.

## Kết quả hiện tại

- Đã xây dựng profile 2.0.0, editor/API, schema/ontology/SHACL và công cụ kiểm tra/chuyển đổi legacy. Unit/API/schema/SHACL: 26/26 PASS; UI preview 14/14 PASS, không có lỗi trang. Pipeline trước review đạt exit 0, runtime 2/2; pipeline sau sửa exit 1 ở runtime vì môi trường chặn CDN PlaceVN. Cả pipeline chạy lại với quyền mạng đọc đã PASS, exit 0, runtime 2/2 trong `pipeline-review-fixes-network.log`. Bằng chứng và giới hạn nằm trong báo cáo kết quả.
- Giữ snapshot DILA 2026-09 và dữ liệu CBETA/Marcus đã index ở local. Ví dụ A000885: 45 mục nhắc đến trong CBETA, một crosswalk Marcus và 34 cạnh mạng nguyên bản. Không tự chấp nhận mapping hoặc chuyển cạnh mạng thành truyền pháp.
- Audit hiện tại: **1.038 file, 1.037 hồ sơ qua kiểm tra cấu trúc, một lỗi template, 10.541 assertion**. `valid` ở đây không chứng nhận sự thật lịch sử.
- Audit ban đầu có 1.035 file hợp lệ, ba lỗi và 10.510 assertion. Hai lỗi `hasDisciple` tự nối không còn trong audit hiện tại sau khi SHA hai file thay đổi ở workspace dùng chung. T226 không sửa các file TTL active; không quy kết tác nhân thay đổi. Đối chiếu `shared-workspace-ttl-diff.json` trước migration.
- Đã nạp main 5000 bằng Windows Administrator/UAC: PID 22920 → 17212. Schema v2.0.0, API lineages cũ và trang login qua 8080 đều HTTP 200. UI trên chính localhost:8080 đạt 14/14, 0 lỗi trang; bằng chứng `deployment-verified.json` và `ui-deployed-8080.log`. Chưa apply dữ liệu vào DB hoặc TTL active.

## T226 DONE — việc tiếp theo theo roadmap

Phần profile, editor, API staging, kiểm thử, triển khai và roadmap của T226 đã hoàn tất. Trước migration/công bố phải chốt catalog nguồn và quyền theo artifact (P1), crosswalk/định danh (P2), chứng cứ và các resource chuyên sâu (P3). P4 mới xây importer v2 rồi review/snapshot/apply riêng TTL; không apply chỉ vì audit cấu trúc đạt. P5–P6 là công bố và vận hành dài hạn.

Đọc [phân tích và roadmap](../docs/reports/T226-academic-ttl-roadmap.md), [báo cáo kết quả](../docs/reports/T226-ttl-profile-20261003/README.md), [Handoff](../docs/Handoff-2026-10-04-T226-ttl-profile-v2.md).


### Xác minh bổ sung ngày 2026-10-04

Admin xác nhận đã tự xóa cạnh `hasDisciple` trỏ về chính mình trong `TS-Hung-Duong-Hien.ttl` và `TS-Thach-Suong-Khanh-Chu.ttl`. Kiểm tra RDF lại: cả hai file parse được, 0 cạnh tự nối `hasTeacher`/`hasDisciple`; SHA khớp lần audit hiện tại. Bằng chứng: `docs/reports/T226-ttl-profile-20261003/admin-self-edge-removal-verified.json` (đường dẫn từ daoanh). Đây là xác minh lỗi tự nối; chưa chứng nhận toàn bộ quan hệ lịch sử. Pipeline sau review đã PASS với quyền mạng (exit 0), unit 26/26, UI 14/14; main bootstrap cũng PASS.

Audit lại ngày 2026-10-04 hoàn tất: 1038 file, 1037 valid, 1 template lỗi, 10541 assertions; đối chiếu input SHA sau quét 0 mismatch. Audit exit1 chỉ vì 0-template.ttl chứa placeholder, không phải pipeline fail. Không xuất stage hoặc apply. Dashboard API trả T226 status done.
