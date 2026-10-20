# Phiên 2026-10-10 — Minh Hải Pháp Bảo: hồ sơ gốc TTL PTDA

## Đã hoàn tất trong phạm vi local

Admin chỉ thị dùng TTL local làm hồ sơ gốc tiếng Việt, cùng nguồn tu học/pháp mạch Báo Tư với Nguyên Thiều Siêu Bạch (Thọ Tông), khai tổ Chúc Thánh Việt Nam, đời 71 tính từ Ma Ha Ca Diếp. Đã áp dụng riêng TS-Minh-Hai-Phap-Bao.ttl. Số 71 đã có trước sửa; không tăng số đời.

Đổi nhãn chính đang nhầm Nguyên Thiều thành Minh Hải Pháp Bảo, bổ sung tiểu sử/nhãn Hán/định danh PTDA/nguồn Admin và metadata countingScheme. URI/hasTeacher/khai tổ/birth-deathEvent giữ nguyên. Không gán A000662 hoặc DILA-ID khác.

## Bằng chứng và kiểm tra

[Báo cáo](../reports/Minh-Hai-local-TTL-20261010/README.md): bản đề xuất/active RDF PASS 12→36 triple, chỉ thay nhãn sai và tiểu sử trống; 0 tự nối/0 sameAs; Nguyên Thiều70→Minh Hải71, Ma Ha Ca Diếp1; hash hai file tham chiếu giữ nguyên. Reader T226 conforms=true, tên vi/zh đúng, DILA-ID rỗng, 12 cảnh báo legacy_unverified. Revert dry-run PASS.

preflight exit1: 23 cờ nhãn ở file khác, 24 cảnh báo ID L5; Minh Hải không bị flag. Pipeline: guard PASS, dup:ids FAIL 8 ID có sẵn, các bước sau chưa chạy. Không yêu cầu review bản build / không báo toàn dự án PASS. Không phát âm báo pipeline thành công khi pipeline đã fail.

## File và trạng thái

- TTL active: data/ttl/TS-Minh-Hai-Phap-Bao.ttl.
- Backup: data/backups/Minh-Hai-local-TTL-20261010-d60a0689/TS-Minh-Hai-Phap-Bao.ttl.
- tasks/T232-evidence-based-generation-engine.md và docs/tasktodo.md: thêm ghi nhận local, không đổi task ID/status chung.
- Báo cáo + manifest + before/dry-run + checks + logs + verifier/revert trong docs/reports/Minh-Hai-local-TTL-20261010/.
- [Handoff](../Handoff-2026-10-10-Minh-Hai-local-TTL.md) có 10 mục.
- Không commit/stage; HEAD lúc đo 03903d98055e00330a126fe5d851db8c4ab8c3bb, worktree dùng chung.

## Giới hạn và tiếp theo

Chưa import DB, chưa xác minh UI/API đọc nội dung mới, không đổi registry mốc v2 hay tính đệ quy. Số đời giữ dưới nguồn xác nhận Admin, chưa được nâng accepted bằng ba gốc sử liệu độc lập. Sync riêng hồ sơ local và duyệt mốc là công việc tiếp theo, không chạy full importer khi corpus còn flags.

## Lỗi thao tác / dịch vụ

Một lệnh rg dùng đường dẫn module tương đối app nhưng cwd repo root; đã chạy lại bằng đường dẫn từ repo root. Lần đầu kiểm validator đọc nhầm khóa valid; kết quả thực tế là conforms=true. Sửa kiểm sang conforms và chạy lại PASS; không sửa validator để làm test xanh. POST claude-mem theo AGENTS thất bại kết nối curl7/shell1; request/result lưu local, chưa có receipt dịch vụ.
