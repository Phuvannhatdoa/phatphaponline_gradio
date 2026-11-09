# Handoff 2026-10-21 — QA pilot X86n1601 v0.1

## 1. Thông tin đọc nhanh

- Session: kiểm chứng độc lập ZIP Cloud; trạng thái QA hoàn tất, dataset cần sửa v0.2.
- HEAD: không đo trong subtask; chưa commit. Agent kế tiếp dùng git log từ visjs-app.
- Preflight: đã đọc scripts trước chạy; source/package bất biến qua hash toàn bộ file trước/sau.
- Tests: XSD thật PASS; validator PASS; bộ test path-adapted 8/8 PASS; negative semantic FAIL.
- DB/TTL/legacy/production: không đọc/ghi qua script QA, không migration.

## 2. Đọc trong 2 phút

Python đọc được XML nhưng bộ trích chưa đủ tin cậy: câu giả lập phủ nhận truyền pháp vẫn bị biến thành cạnh truyền pháp có hướng. Chín cạnh có đoạn chữ, nhưng thiếu evidence refs/locator trong XML. Không kết luận cả chín sai. Admin: (1) chuyển mục 5 báo cáo QA cho Cloud, (2) yêu cầu v0.2 và giữ v0.1 nguyên trạng, (3) chưa nhập DB hoặc chạy toàn bộ sách.

## 3. Vấn đề và cách sửa có chứng cứ

Báo cáo đầy đủ: [QA-REPORT-VI.md](reports/x86n1601-delivery-qa-20261020/QA-REPORT-VI.md). Bao gồm đủ chín claim, mã source item, khoảng lb ed=X, các lỗi chặn và 10 bước sửa Cloud. `independent-qa/runtime-log.txt` ghi phản ví dụ, XSD, 8 tests và replay. Khoảng dòng là toàn source item, không được quảng bá là span chính xác từng câu.

## 4. Cảnh báo bắt buộc

Không sửa artifact v0.1, không chuyển pending thành accepted. Quyền vẫn cần duyệt theo từng artifact; không dùng báo cáo này làm kết luận pháp lý. Schema PASS không chứng minh quan hệ lịch sử. Không suy DILA ID/tăng đời hoặc dùng thứ tự danh sách làm bằng chứng truyền pháp. Không chạy pipeline toàn app cho audit ngoài ứng dụng vì có thể sinh file chung; pipeline chưa chạy, đây không phải bản build xin duyệt.

## 5. Revert

Không có thay đổi production/DB/TTL nên không cần restore/revert dữ liệu. Chỉ có artifact QA trong `docs/reports/x86n1601-delivery-qa-20261020/independent-qa`, báo cáo và handoff. Chưa commit nên không có SHA revert. Nếu muốn bỏ báo cáo, chỉ xóa đúng các file QA mới sau khi xem danh sách; tuyệt đối không xóa source/package hoặc thư mục chung cả task. Mất dữ liệu production: không.

## 6. File tạo trong subtask

- reports/x86n1601-delivery-qa-20261020/independent-qa/QA-report.md
- reports/x86n1601-delivery-qa-20261020/independent-qa/CLOUD-v0.2-INSTRUCTIONS.md

- reports/x86n1601-delivery-qa-20261020/QA-REPORT-VI.md
- reports/x86n1601-delivery-qa-20261020/independent-qa/run_independent_qa.py
- reports/x86n1601-delivery-qa-20261020/independent-qa/runtime-log.txt
- reports/x86n1601-delivery-qa-20261020/independent-qa/package-hashes.json
- reports/x86n1601-delivery-qa-20261020/independent-qa/nine-claims-audit.json
- reports/x86n1601-delivery-qa-20261020/independent-qa/replay.claims.xml
- reports/x86n1601-delivery-qa-20261020/independent-qa/synthetic-negative-fixture.xml
- Handoff này.

## 7. Sai lầm QA đã sửa

Lần đầu lấy mọi lb khiến lẫn hệ phân trang khác; đã kiểm chứng không dùng được làm locator X. Đã sửa script chỉ chọn ed=X và chạy lại cả log/JSON. Lần đầu hash map dùng Windows backslash khác SHA file forward slash gây KeyError; sửa as_posix, chạy lại. Một lệnh XPath bị PowerShell phá dấu nháy và một tên encoding utf8-sig không hợp lệ; đã sửa, không sửa package. Không dùng output các lần lỗi để kết luận.

## 8. Chưa xong

P0: Cloud sửa trích/ngữ nghĩa/evidence và test thực theo report. P1: metadata/CLI/replay/hash/rights attribution. P2: kiểm chứng v0.2 trước nghiên cứu corpus 9 quyển. Chưa chạy nguyên CLI của gói vì hardcode Cloud; test rerun thay duy nhất input path trong AST bộ nhớ, không che giấu sự thích nghi này. Chưa đối chiếu DILA ID, không import. Không cần Admin quyết thêm để giao sửa v0.2; cần gói mới để QA lại.

## 9. Kiểm tra nhanh

Từ Dai_Tang_Kinh:

```powershell
python -X utf8 daoanh/docs/reports/x86n1601-delivery-qa-20261020/independent-qa/run_independent_qa.py
```

Yêu cầu lxml có sẵn (đã chạy 6.0.2). Lệnh chỉ ghi artifact trong independent-qa, đọc package; kết quả mong đợi hiện tại: XSD True, 8 PASS, NEGATIVE_SEMANTIC_TEST_PASS False, PACKAGE_UNCHANGED True. Đây là xác nhận phát hiện lỗi, không phải test release xanh.

## 10. Ghi chú agent tiếp theo

Đọc QA report trước; giữ all claims pending. Nhận v0.2 bằng folder khác; so hashes và semantic diff; không tự sửa v0.1 để khiến tests xanh. Root đã thử POST tasktodo vào localhost:37700 nhưng WinError10061 connection refused; observation chưa lưu. Bàn giao này lưu nối phiên local. Không phát thông báo Done cho dataset/build; chỉ QA audit hoàn tất.
