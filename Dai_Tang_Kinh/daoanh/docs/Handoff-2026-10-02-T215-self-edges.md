# Handoff-2026-10-02-T215-self-edges

## 1. Đọc nhanh
Ngày: 2026-10-02. Task T215 in_progress. TTL/DB: không sửa. Dashboard/API live HTTP200, đủ9 article; task criteria4/9. E2E HTML hiện có PASS. Pipeline đang chạy, kết quả bổ sung cuối file. HEAD chưa kiểm; không commit trong phiên này.

## 2. Đọc trong 2 phút
Đã ghi kế hoạch Admin phê chuẩn, tạo task T215 và docs, load9 hồ sơ, gắn trang trên Dashboard. Số đời giữ nguyên tất cả. Quan trọng: ID local cho Vô Chuẩn/Động Sơn khác DILA chính thức; không tin name_zh local là bằng chứng ID đúng. Admin mở /daoanh/dashboard/t215-self-edges.html để xem lỗi/căn cứ/đề xuất, ưu tiên case danh tính rõ, để nguyên case Thụy Nham chưa xác minh. Chưa cần quyết định số đời.

## 3. Đề xuất từng task
T215: docs/reports/T215-self-edges/README.md và cases.json là hồ sơ 9 case; có field lỗi, dòng gốc, SHA256, nguồn DILA và đề xuất. Task tasks/T215-dila-ttl-evidence-and-self-edges.md là SSOT kế hoạch. DILA chính thức xác nhận Phần Dương/Quảng Tuệ có thầy 首山省念 A004983. Vô Chuẩn chính thức A004697, thầy A004696; local đang A045360. Động Sơn đề xuất A020683/A020673, local A010985/A021072; cần kiểm ảnh hưởng mapping trước apply. Thụy Nham skipped, không đoán trò. Các hồ sơ khác có điều kiện ghi riêng.

## 4. Cảnh báo bắt buộc
TTL không git track; backup file-level trước apply. Có WIP trước phiên, không ghi đè. tasktodo.md là reparse point: write sandbox EPERM; đã dùng lệnh Add-Content require_escalated được chấp nhận để bổ sung mục T215. Không replace URI toàn file: target và nhãn của thầy có thể khác vai trò subject. DILA tham học không nhất thiết pháp tự. Ba chứng cứ số đời phải độc lập và cùng quy ước đếm; không tự thầy+1.

## 5. Revert
Không có thay đổi dữ liệu học thuật: không cần restore TTL/DB. Docs cũ đã backup trong docs/sessions/backups/T215-docs-20261002/ (tên path ngăn cách bằng __). Trước restore phải so với thay đổi sau phiên, không ghi đè WIP; tasktodo.md có thể cần quyền escalated vì reparse. Task/docs/trang mới chỉ là artifact review, có thể bỏ sau khi kiểm chưa ai chỉnh. Chưa commit nên không cung cấp SHA git revert giả.

| Phạm vi | Mất dữ liệu khi rollback? |
|---|---|
| TTL/lineage.db | Không thay đổi |
| Docs/dashboard | Restore backup có thể mất chỉnh sửa sau phiên; phải kiểm diff trước |

## 6. File tạo/sửa
Tạo tasks/T215-dila-ttl-evidence-and-self-edges.md; docs/plans/T215-dila-ttl-evidence-plan.md; docs/reports/T215-self-edges/{README.md,cases.json}; dashboard/{t215-self-edges.html,t215-plan.md,t215-cases.json}; Handoff này. Sửa docs/{tasktodo.md,progress.md,roadmap.md}, SUMMARY.md, tasks/README.md, dashboard/dashboard_process.html; regenerate data/progress_data.json.

## 7. Sai lầm và bài học
Lần ghi tasktodo bằng fs bị EPERM; apply_patch báo reparse point, không phải lỗi nội dung. Đã dùng escalation đúng phạm vi, không đổi ACL. Backup T211 cho thấy Diên Phúc/Vô Chuẩn đã có self-edge từ trước; KHÔNG nói T211 mới tạo self-edge. T211 replace toàn file còn đổi target và nhãn thầy, nên kiểm số triple không đủ phát hiện lỗi danh tính. Không dùng A045360 local để gọi trang Vô Chuẩn là đúng.

## 8. Chưa xong
1. Khóa identity của proposed endpoint bằng DILA chính thức và nội dung tiểu sử TTL.
2. Validate RDF với rdflib; CLI hiện thiếu thư viện.
3. Change-set scoped + snapshot/guard/revert, chỉ case xác nhận được; bỏ qua case thiếu nguồn.
4. Đồng bộ riêng nguồn TTL, không chạy full importer insert-only hoặc rebuild rộng.
5. API/audit hậu kỳ; số đời chỉ sửa khi đạt gate3 chứng cứ.

## 9. Kiểm tra nhanh
Mở http://localhost:8080/daoanh/dashboard/t215-self-edges.html — 9 hồ sơ; http://localhost:8080/daoanh/api/progress/dashboard — tasks chứa T215/in_progress,4/9. Chạy node scripts/e2e-test.js trong daoanh để kiểm cú pháp HTML hiện có. cases.json tất cả applied=false; generation_action giữ nguyên.

## 10. Agent kế tiếp
Đọc task T215 và hồ sơ9 trước. Kiểm hash hiện tại, không apply đề xuất khi identity còn conditional. Tiếp tục DILA/tiểu sử, không xin lại phê chuẩn kế hoạch. Quyền phê chuẩn kế hoạch không biến ứng viên thiếu chứng cứ thành verified. Cập nhật status thật, không đánh dấu done vì docs đã hoàn thành.


## Validation kết thúc
- Pipeline exit1, T178 67/68 PASS; thiếu flask khi import app. Không claim pipeline PASS.
- E2E script kiểm cú pháp HTML hiện có PASS; không phải browser runtime E2E.
- Live Dashboard/detail/API: HTTP200,9 article,T215/in_progress,4/9.
- Hash9 TTL khớp lúc load,0 TTL apply,0 DB apply.
- Memory service localhost37700 không kết nối được; đã lưu handoff/session local.
