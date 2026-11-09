# QA độc lập — PTDA X86n1601 pilot v0.1

Cập nhật 2026-10-21. **XML hợp XSD được giao, nhưng pipeline trích quan hệ chưa đủ tin cậy để nhập dữ liệu hoặc mở rộng tự động.** Không sửa package, DB, TTL, legacy hoặc production.

## Kết quả đo kiểm

ZIP checksum khớp `e2506b23422a4c8371e17eaf2205ae5ab1743c471bc6e653dec04a9bfa9c8c09`. Source checksum khớp `60a282bf78795048395dfdb6ab2ac0d7912bbd6b527338d9664f58994e84f178`. Source có 796393 bytes, khác manifest 798720.

XSD thật qua lxml PASS. Validator được giao PASS nhưng không gọi XSD. Tám test chạy lại PASS sau thay duy nhất đường dẫn input trong AST bộ nhớ; package không bị sửa. Replay tạo 34 persons, 34 mentions, 9 claims và giống bản giao sau chuẩn hóa downloadTime. Hash toàn bộ file package trước/sau không đổi.

Test phủ định độc lập FAIL: câu giả lập `甲師未曾傳法予乙師，乙師不是其弟子。` vẫn sinh cạnh truyền pháp Giáp → Ất. Đây là fixture thử lỗi, không phải nhân vật hay khẳng định lịch sử. Exit 0 của harness chỉ biểu thị hoàn thành đo kiểm, không phải acceptance PASS.

## Lỗi chặn và cách sửa

- Extractor tìm tên trong bảy mục kế tiếp rồi `break`, không kiểm động từ, phủ định hoặc vai nghĩa. Phải tách chứng minh loại quan hệ và chiều; đồng xuất hiện tên chỉ là mention/unresolved.
- Chín claim có evidenceFragment nhưng `<evidence/>` rỗng; serializer bỏ xml_path. Thiếu evidence ID/ref, locator, span và lớp văn bản. Cần xuất các trường này, không chỉ giữ trong bộ nhớ Python.
- sourceRelationTerm luôn là tiếng Anh do code gán. Cần giữ chữ Hán nguồn và trường loại chuẩn hóa riêng.
- Hàm nối mọi text hậu duệ không tách note/app/lem/rdg, có nguy cơ trộn dị bản. Cần renderer có provenance và chính sách gaiji.
- XSD cho evidence rỗng; PASS schema không chứng minh hợp đồng nghiên cứu. Validator phải kiểm hash nguồn thật, ID/ref, quote và locator.
- Test số 8 dựa khoảng cách chỉ mục và độ dài đoạn chữ, không kiểm ngữ nghĩa. Cần phản ví dụ thật như fixture vừa chạy.
- Script/test hardcode đường dẫn Cloud; downloadTime thực là thời điểm trích; SHA256SUMS chỉ có source. Cần CLI, timestamp đúng nghĩa và hashes đủ artifact.

## Đối soát chín claim

Tất cả đoạn chữ có trong tiểu sử replay. [nine-claims-audit.json](independent-qa/nine-claims-audit.json) chứa đủ chín cặp tên, đoạn chữ, source item và khoảng dòng được QA phục hồi. Đây không phải locator có sẵn trong XML giao. Khoảng dòng chỉ toàn source item theo `lb ed=X`, chưa phải span chính xác của câu; không ghép các hệ phân trang khác.

Claim 4 và 8 ưu tiên duyệt chủ ngữ lược/dấu câu. Không kết luận cả chín sai và không tự accepted hướng/người/sự kiện lịch sử. Tất cả vẫn candidate/pending.

## Phạm vi và quyền

Code chọn mục 三十三祖, chưa chứng minh xử lý toàn quyển 001; 002–009 chưa làm. Số 34/9 không phải thước đo recall. README đặt người cuối là 菩提達摩 nhưng XML person_033 là 慧能; mô tả 33 Tổ Ấn Độ không phù hợp danh sách có Tổ Trung Hoa. Sơ đồ tài liệu phải phân biệt cạnh đã trích và hình minh họa.

Giữ generationLabel nguyên bản. SourcePersonId là ID item XML, không phải DILA authority. Chưa có đối soát DILA ID trong pilot này.

Header gốc ghi “Available for non-commercial use when distributed with this header intact.”, version date 2025-08-28 16:43:44 +0800. PublicationStmt không tự ghi URI CC4. Báo cáo quyền cần dẫn chính sách cụ thể; không tự áp kết luận license text cho scripts/XSD do Cloud tạo. Quyết định quyền vẫn pending/unresolved; audit này không đưa kết luận pháp lý mới.

## Bàn giao

Log hiện hành: [runtime-log.txt](independent-qa/runtime-log.txt). Script: [run_independent_qa.py](independent-qa/run_independent_qa.py). Chỉ thị: [CLOUD-v0.2-INSTRUCTIONS.md](independent-qa/CLOUD-v0.2-INSTRUCTIONS.md).

Không commit, không chạy pipeline ứng dụng vì không có bản build. POST tasktodo localhost:37700 thất bại do connection refused; chưa lưu observation. Bước tiếp: Cloud tạo v0.2 trong folder riêng, QA lại trước mọi import.
