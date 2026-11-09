# QA độc lập X86n1601 — 2026-10-21

**Kết luận: đọc được bằng Python và hợp XSD được giao; chưa đạt chất lượng trích quan hệ để nhập DB hoặc mở rộng tự động.**

- ZIP SHA-256 khớp `e2506b23422a4c8371e17eaf2205ae5ab1743c471bc6e653dec04a9bfa9c8c09`.
- Source SHA-256 khớp `60a282bf78795048395dfdb6ab2ac0d7912bbd6b527338d9664f58994e84f178`; 796393 bytes, khác manifest 798720.
- XSD thật qua lxml PASS; validator đóng gói không gọi XSD.
- Bộ test đóng gói: 8/8 PASS sau khi chỉ thay input path trong AST bộ nhớ.
- Replay: 34 persons, 34 mentions, 9 claims; giống bản giao sau chuẩn hóa downloadTime.
- Test phủ định độc lập FAIL: câu phủ nhận truyền pháp vẫn sinh cạnh truyền pháp có hướng.
- Hash toàn bộ file package trước/sau không đổi.

Extractor chỉ tìm tên trong bảy mục kế tiếp rồi dừng ở kết quả đầu. Nó không chứng minh loại quan hệ hoặc chiều. Chín claim có đoạn chữ nhưng `<evidence/>` rỗng, thiếu evidence refs và locator xuất ra. Không kết luận cả chín quan hệ sai; tất cả giữ candidate/pending.

QA phục hồi source item và khoảng dòng `lb ed=X` cho cả chín claim trong `nine-claims-audit.json`. Đây là khoảng toàn item, chưa phải span chính xác từng câu. Claim 4 và 8 cần duyệt chủ ngữ lược/dấu câu. Không quy đổi generation sang PTDA và không xác minh thêm DILA ID.

`runtime-log.txt` đã chạy lại ngày 2026-10-21. Exit code 0 của harness nghĩa là hoàn tất đo kiểm; **không có nghĩa mọi acceptance test đều đạt**. `NEGATIVE_SEMANTIC_TEST_PASS` vẫn False.

Không sửa DB/TTL/legacy/production, không commit. Pipeline ứng dụng chưa chạy vì đây là audit gói ngoài, không phải bản build xin duyệt. Quyền giữ pending; không có kết luận pháp lý mới.

Chi tiết: [QA-REPORT-VI.md](../QA-REPORT-VI.md). Bước tiếp: giao [chỉ thị v0.2](CLOUD-v0.2-INSTRUCTIONS.md) cho Cloud, nhận gói mới để QA trước mọi import.
