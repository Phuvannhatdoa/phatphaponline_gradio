# Phase4 — Preview đối chiếu cô lập tại máy

Ngày: 2026-10-17. Chỉ đọc nội bộ; không commit, không đưa ra public hoặc export. Toàn bộ file mới ở analysis/phase4. Không sửa Phase1–3, DB, TTL, legacy, HOME hoặc API.

## Mở preview

Mở preview.html trực tiếp bằng trình duyệt (file://). Giữ preview.html, preview.css, model.js, preview.js và preview-data.js cùng thư mục. Không cần server, mạng, tài khoản, token hoặc API.

1. Chỉ nguồn: xem 15 nhân vật, tìm ID/nhãn, chọn CSV/GEXF và đọc từng observation.
2. Đối chiếu tác phẩm: dữ liệu thực chỉ có một cụm Tổ Đường Tập. Các ca thêm đều ghi SIMULATED, dùng người/tác phẩm hư cấu.
3. Chi tiết chứng cứ: hai witness, cảnh báo CSV UUID/locator, ba mã đời 0/?, 41 linkGrp cert=low, toàn bộ 71 mục bất định, notice quyền và JSON chứng cứ.

## Cảnh báo integrity bắt buộc

**Preview dựa trên observed Phase4 snapshot, pending investigation.** Byte đầu vào hiện tại không khớp một số hash được ghi trong artifact upstream. Không phải chỉ CRLF/LF ở sáu trường hợp Phase2 đã kiểm. phase4-manifest.json giữ riêng recorded_sha256, observed_sha256 và tình trạng từng mục.

Không chuẩn hóa hoặc sửa input, không ghi lại manifest Phase1–3 và không tuyên bố frozen-chain PASS. Phiên bản snapshot Phase4 được định danh bằng hash của toàn bộ mười một input hiện tại. Builder --verify chỉ chứng minh khả năng tái tạo output từ các byte hiện tại; không chứng nhận chuỗi lịch sử đã được xác minh.

## Mô hình và ranh giới

- Dataset, source version, representation, source identity, observation và evidence là các lớp riêng. CSV/GEXF/TEI/XLSX cùng cụm ZTJ không là các nguồn lịch sử độc lập.
- Source label và raw source record giữ nguyên. Mọi mapping là proposed / unreviewed. proposed_ptda_person_id, vietnamese_label và vietnamese_label_source để null khi chưa được cung cấp; không tự tra production hoặc tự dịch để lấp thiếu.
- Nhãn Việt chỉ có ở lớp mapping của fixture và được ghi simulated. Không nâng kết quả đối chiếu nhãn DILA được dẫn lại thành accepted identity.
- Gom trên màn hình chỉ khi cùng định danh nguồn hoặc tương đương hư cấu được khai báo trong fixture, cùng loại quan hệ và cùng chiều. Không xóa/gộp bản ghi nguồn. Chiều không có chứng cứ không thành directed; số đời không là khóa nhân vật.
- Tất cả quan hệ thực giữ undirected và source_graph_association. Endpoint Source/Target không được hiểu là thầy/trò. Một cạnh vắng trong mẫu/biểu diễn không phủ định lịch sử.
- Giữ hai GEXF 0300b07 và 0412a05 cho A004166–A000587; CSV mang UUID khớp bản trước và locator khớp bản sau. Không chọn bản thắng.
- Giữ ba CSV “0” / workbook “?” và hệ nguồn; không cộng đời hoặc chuyển hệ. Fixture khác hệ số đời chỉ thêm annotation cho cùng một người.
- Bốn TEI có notice CC BY-NC-SA 4.0 khác khai báo CC BY 4.0 cấp record/thư mục. Chưa clearance; nội dung/JSON/ảnh dẫn xuất cũng chỉ dùng tại máy. License nguồn không cấp quyền cho PTDA/DILA/CBETA.
- Không có bộ quan hệ DILA/Marcus độc lập trong các input đã giao. Attribution lưu trữ Marcus không được tính thành tác phẩm độc lập; không tạo claim vắng mặt trong toàn bộ DILA/Marcus.

## File dẫn xuất

| File | Vai trò |
|---|---|
| datasets.json / source_versions.json | Dataset và snapshot có hash đầu vào |
| representations.json | File/định dạng và cụm tác phẩm nguồn |
| source_identity.json / source_person.json | 15 identity nguồn, nhãn/raw nguyên văn |
| mapping_candidates.json | Bảy trường ứng viên tách riêng, chưa duyệt |
| source_relation.json / source_observation.json | Quan hệ quan sát và 23 bản nguồn riêng |
| source_evidence.json | Chứng cứ chọn từ P3, gồm đầy đủ 41 mục bất định linkGrp |
| uncertainty-inventory.json | 41 linkGrp và toàn bộ inventory 71 mục |
| generation-unknowns.json / rights.json | Ba 0/? và rights matrix nguyên trạng |
| fixtures.json | Năm ca giả lập, không claim lịch sử |
| preview-data.js | Bundle của dữ liệu dẫn xuất để mở file://; không là nguồn độc lập |
| phase4-manifest.json | Hash 11 input, integrity mismatch và hash output dữ liệu |
| delivery-files.json | Danh mục/hash toàn bộ file bàn giao, trừ chính file danh mục |
| model.js / build_phase4.mjs | Logic so sánh thuần và builder có allowlist ghi Phase4 |
| preview.html / preview.css / preview.js | Giao diện local, không CDN/fetch/storage |
| test_phase4.cjs / test-results.json | Kiểm thử mô hình, dữ liệu và UI; xem kết quả thực tế trong JSON |
| desktop-preview.png / mobile-preview.png | Ảnh kiểm local; không công bố |
| TEST-MATRIX.md / CHANGE-AND-NO-PRODUCTION.md | Ma trận và báo cáo phạm vi |
| SESSION.md / Handoff-2026-10-17-phase4-local-preview.md | Bàn giao |

Manifest không tự hash chính nó; UI/test/docs và ảnh được liệt kê ở đây, không giả là output dữ liệu đã hash trong manifest.

## Kiểm tra lại

Trong chính thư mục Phase4:

    node build_phase4.mjs --verify
    node test_phase4.cjs

--verify không ghi output. Test runner chỉ ghi test-results.json và hai ảnh ở Phase4; dùng Chromium/Playwright đã có, không cài package hoặc gọi nguồn trả phí. --write chỉ tái tạo các output allowlist Phase4. Không chạy builder/runner Phase1–3.

Nguồn được dẫn lại từ input: Zenodo record 10004109; Laurent Van Cutsem; vai trò biên tập/lưu trữ Marcus Bingenheimer; DOI 10.5281/zenodo.10004109 và 10.3390/rel14020205. Chưa thực hiện tra cứu mới hoặc clearance pháp lý.

## Kết quả Phase4 đã chạy

25/25 kiểm PASS, 0 FAIL tại UTC 2026-10-17T06:16:43.942Z. Builder --verify exit 0 trên observed snapshot; 11 input không đổi. 6 hash upstream không khớp vẫn có cảnh báo và đang chờ điều tra. Không lấy PASS kỹ thuật làm accepted mapping, lịch sử đúng hoặc clearance quyền.
