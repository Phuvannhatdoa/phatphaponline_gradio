---
id: T232
title: Tính số đời đa hệ từ mốc sử liệu và đường truyền DILA
status: in_progress
priority: high
created: 2026-10-04
---

# T232 — Số đời có căn cứ, đa hệ đếm

## Yêu cầu đã được Admin giao

Tự tính từ mốc khai tổ và đường truyền, không buộc Admin cộng tay. Một người có thể có đời Thiền Tông, Lâm Tế, Dương Kỳ, Chúc Thánh riêng. Không dùng năm 2026 hay một offset cố định để đoán số đời.

## Kế hoạch triển khai

1. Khóa ID/tên gốc bằng record DILA trong DB; lưu định vị sử liệu, phiên bản và hash. Phân biệt quy ước Ca Diếp=1/Thích Ca=0 với Thích Ca=1.
2. Engine duyệt tổ tiên với memoization, cộng một cho cạnh trực tiếp, phát hiện chu trình, nhiều đường khác số, mốc mâu thuẫn, đứt đường và giới hạn tài nguyên. Teacher chung chỉ tính dự kiến; truyền pháp đã duyệt mới đủ điều kiện xác lập.
3. Registry đa hệ và mốc có phiên bản; Admin thêm/sửa bằng UI/API có xác thực. Duyệt mốc số đời cần ba gốc chứng cứ độc lập, rationale, người/ngày duyệt. Không sửa TTL legacy/person_gen_computed.
4. UI tự tính nhiều hệ, hiển thị đường dẫn và cảnh báo; kết quả đi vào TTL v2 dưới dạng nhận định suy dẫn, không tự thành fact được duyệt. TTL giữ nguồn và trạng thái.
5. CLI đọc DB theo từng người, báo cáo JSONL; API/thuật toán/schema/RDF/UI regression; chạy pipeline. Backup, rollback, Handoff 10 mục, tasktodo và Dashboard.

## Các mốc cần kiểm

- Thiền Tông theo danh sách tổ: Đạt Ma 28, Huệ Năng 33 (Ca Diếp=1).
- Lâm Tế: Nghĩa Huyền 1, Hưng Hóa **Tồn Tưởng** (存獎) 2. Admin trước gọi Nghĩa Tồn; không gán tên đó cho ID 存獎.
- Dương Kỳ/Chúc Thánh: đời khai tổ=1 trong hệ riêng; cần khóa ID và chứng cứ trước khi tự đưa vào registry.
- Các ví dụ 85/12/13 là ví dụ hiển thị, không là số gán sẵn; một người chỉ có số nếu có đường tới mốc trong hệ đó.

## Hoàn thành khi

Engine/API/UI/TTL có nguồn và trạng thái; test chứng minh không chọn đường ngắn nhất hoặc một thầy tùy ý để che xung đột; pipeline PASS; DB/TTL cũ nguyên trạng. Những mốc chưa đủ ba chứng cứ vẫn tính dự kiến và ghi rõ cần duyệt.

## Triển khai 2026-10-04

Engine/API/TTL/form/panel cây đã chạy trên8080,9 hệ (8 có mốc dự kiến,Chúc Thánh chưa khóa ID),unit20/20 và UI realPASS. Không ghi số vào person_gen_computed/TTL nguồn. Năm bảng authority/quan hệ/số đời có hash trước=sau. Nguyên Thiều generic teacher conflict, A000662 chưa đồng nhất Minh Hải Pháp Bảo. Pipeline cuối/rollback và scope xem [report](../docs/reports/T232-generation-engine-20261004/README.md) và [Handoff](../docs/Handoff-2026-10-04-T232-T233-name-generation.md). Chưa tính toàn corpus, chưa duyệt mốc lịch sử, chưa xuất lại gói1.037 TTL.

## Quyết định định danh 2026-10-05 — Admin đã xác nhận

**A000662 明海 và Minh Hải Pháp Bảo, khai tổ Chúc Thánh, là hai nhân vật khác nhau thuộc hai thời đại.** Loại trừ A000662 khỏi ứng viên định danh khai tổ Chúc Thánh; giữ hồ sơ DILA nguyên trạng, không sameAs hai người. Registry linji_chucthanh revision1→2 lưu xác nhận Admin và XML hash, root/anchors vẫn trống. Tám hệ khác giữ hash, không sửa TTL/số đời. ID riêng Minh Hải Pháp Bảo vẫn cần xác minh. [Quyết định và kiểm chứng](../docs/reports/T232-A000662-distinct-20261005/README.md).

### Cập nhật hồ sơ PTDA local — 2026-10-10

Admin chỉ thị dùng TTL Minh Hải Pháp Bảo làm hồ sơ gốc tiếng Việt local khi chưa có DILA-ID đã xác minh. Đã sửa nhãn đang nhầm Nguyên Thiều, bổ sung tiểu sử, nguồn tu học/pháp mạch Báo Tư và provenance Admin; giữ generationOrder **71**, làm rõ Ma Ha Ca Diếp=1. Không thay URI/hasTeacher, không gắn A000662, không nâng mốc lên accepted hay kích hoạt registry/tính đệ quy; không import DB. RDF active PASS; preflight corpus còn 23 cờ ở file khác, pipeline dừng dup:ids 8 ID trùng. [Báo cáo và backup/revert](../docs/reports/Minh-Hai-local-TTL-20261010/README.md).
