---
task: tasks/T232-evidence-based-generation-engine.md
---

# A000662 明海 và Minh Hải Pháp Bảo Chúc Thánh — hai nhân vật khác nhau

Ngày 2026-10-05 Admin xác nhận: **A000662 明海 là nhân vật khác Minh Hải Pháp Bảo, khai tổ Lâm Tế Chúc Thánh; khác thời đại, hai nhân vật riêng.** Quyết định này thay trạng thái trước đây còn là ứng viên chưa chắc chắn.

## Quyết định áp dụng

- Giữ A000662 cho hồ sơ DILA 明海 của chính ID đó. Không gắn tên đầy đủ Minh Hải Pháp Bảo hoặc vai trò khai tổ Chúc Thánh vào ID này.
- Loại trừ A000662 khỏi ứng viên định danh khai tổ Chúc Thánh; không tạo owl:sameAs giữa hai người.
- Chưa xác minh ID DILA riêng cho Minh Hải Pháp Bảo. Hệ Chúc Thánh tiếp tục để root_id rỗng, anchors rỗng; không dùng A000662 để tính đời khai tổ hay hậu duệ.
- Quan hệ với X0613 của hồ sơ 明海, nếu có bằng chứng riêng, phải thuộc chính hồ sơ đó; không chuyển qua khai tổ Chúc Thánh vì trùng tên. Phiên này không kiểm chứng lại tác phẩm trên web.

## Chứng cứ và mức độ

decision.json lưu nguyên văn xác nhận của Admin, ngày/người xác nhận, provenance_kind=admin_confirmation và dấu record DILA local. Không trình bày xác nhận Admin như ba nguồn sử liệu độc lập cho số đời.

Local DB: people A000662, name_zh明海, name_viMinh Hải, dynasty明. Năm sinh/mất đều NULL; không điền niên đại chính xác từ suy đoán. XML record version2026-09, SHA256 aeba756c48aa5dee06a20c4987cc1e9154fd44453b95e7fb6b053af3e903c4ea.

## Đối soát và cập nhật DB

inspection.json và mapping-inspection.json xác nhận mốc Chúc Thánh trước sửa chưa có root/anchor. Không có row ttl_mapping hoặc ttl_master trỏ A000662 và không có row filename Minh-Hai trong hai bảng đó; name_vi_map có đúng Minh Hải, không Pháp Bảo; canon_author_mapping không có row A000662. Không có ánh xạ sai trong những bảng này cần xóa.

Đã append revision **1→2** của generation_v2_scheme_revisions cho linji_chucthanh qua save_scheme có expected_revision/CAS. Thêm identity_decisions resolution=distinct_person và convention hiển thị xác nhận. Đây là metadata quyết định trong registry; không bổ sung thuật toán chặn chọn ID hoặc API mới. Các thao tác tương lai phải giữ quyết định này; nếu cần cơ chế hard guard sẽ là thay đổi code riêng.

apply-result.json xác nhận: tám hệ khác giữ hash; people/name_vi_map của A000662 giữ nguyên; root/anchors vẫn trống; compute(A000662,ChúcThánh) có numberNULL/statusmissing_anchor. Không sửa TTL local, tác phẩm, quan hệ hay số đời cũ. Không tạo ID mới.

## Backup và hoàn tác

Backup chỉ cấu hình trước sửa: data/backups/T232-A000662-distinct-20261005/scheme-before.json. Không restore toàn DB có các phiên khác đang ghi.

```powershell
# Tại daoanh; mặc định dry-run, không sửa DB.
python -B -X utf8 docs/reports/T232-A000662-distinct-20261005/revert_decision.py
# Chỉ thêm --apply khi Admin chủ động quyết hoàn tác xác nhận này.
```

Hoàn tác bằng một revision mới, giữ lịch sử quyết định cũ. Guard chặn nếu registry đã có revision mới của phiên khác. Phiên này chưa apply revert.

## Kiểm tra và việc tiếp theo

Dry-run/apply/verify đều có output JSON lưu; pipeline đang chạy theo AGENTS.md, kết quả xem pipeline.exit và pipeline.log. Dashboard cập nhật từ tasktodo/T232; không cấp taskID mới. Việc còn mở: chứng minh ID riêng hoặc thực thể local cho Minh Hải Pháp Bảo Chúc Thánh, sau đó xác minh mốc số đời và truyền pháp theo quy tắc ba nguồn. Không quay lại ghép A000662 từ tên 明海.

## Kết quả hoàn tất và kiểm tra lại 2026-10-09

Pipeline retry ngày05/10 đã hoàn tất exit0, runtime2/2. Lượt đầu bị guard chặn vì tệp chuẩn bị tài liệu .md chứa frontmatter ID của task; đã đổi các artifact chuẩn bị thành .md.prepared, giữ SHA/nội dung và cập nhật manifest. dup:ids hết trùng, pipeline retry PASS. Compliance còn hai metric FAIL; không diễn giải pipeline exit0 thành chất lượng dữ liệu hoàn toàn đạt.

Kiểm tra read-only ngày09/10: Chúc Thánh vẫn revision2, identity_decisions giữ distinct_person cho A000662, root/anchors rỗng; không có mốc A000662 sai. Hồ sơ DILA vẫn 明海/Minh Hải/triều明. [Snapshot hiện tại](../T232-A000662-followup-20261009/current-state.json). Không sửa lại DB trong lượt kiểm tra09/10.
