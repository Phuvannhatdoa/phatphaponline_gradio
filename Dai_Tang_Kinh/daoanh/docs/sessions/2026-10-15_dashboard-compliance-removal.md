# Session 2026-10-15 — Gỡ Dashboard Compliance Meter

- Phạm vi được root giao: gỡ riêng section `Data Quality — Compliance Meter (SCHEMA_DESIGN M7.2)` và dependency frontend. Không cấp task ID mới.
- Chỉ sửa `dashboard/dashboard_process.html`: +0/-68 dòng, 3544 byte worktree; bỏ title/card, `complianceSummary`, `complianceTable`, `COMPLIANCE_API`, `_cqColor`, `_cqLabel`, `loadCompliance`, `renderCompliance` và lời gọi tải đầu tiên.
- Các byte còn lại giữ nguyên so với backup trước removal; marker T358 SHA256 `0f880f0e9608f560813bc1e57be44f4a9efdfff6215e00689e98f330e3cd87a3`. Không xóa backup/data hoặc sửa backend, DB, TTL.
- Worktree SHA256 trước: `22ccb87106e9e702f3f32c5ad3cadb40ec042abf385083e7fa81ca97406a3cf6`; sau: `5cc38db58039a4315cfdbb17e6b32fe94d47550d35561ae258218c735a27e54b`. Git có thể chuẩn hóa CRLF/LF nên blob Git khác hash byte worktree.

## Kiểm chứng đã chạy

- `node --check` trên 3 script inline trích ra TEMP: **3/3 PASS**.
- Playwright fixture toàn trang: **1/1 PASS, 9.2 giây**, log UTC `2026-10-14T14:12:25.469Z`; 0 pageerror, 0 request compliance; 5 KPI/chart, 3 cột Task Board, 15 dòng T358 và DONE khóa còn hoạt động. Toàn bộ HTTP được mock; không chạy app/DB.
- `python -B -X utf8 scripts/repo_guard.py`: **PASS**.
- `npm run pipeline`: **exit 1 tại dup:ids**, còn một ID T274 trùng giữa `tasks/T274-ttl-rule-design.md` và `tasks/T274-vn-lineage-ttl-rule.md`; các bước sau chưa chạy. Không tuyên bố full pipeline PASS.
- Backup, diff và JSON fixture nằm tại `%TEMP%/dashboard-remove-compliance-nhdykv`; không đưa artifact TEMP/data vào commit.

## Git và nối tiếp

Root cho phép commit đúng dashboard cùng session/Handoff mới, dùng index riêng khởi tạo bằng `git read-tree HEAD`; kiểm cached đúng 3 file, không D/unrelated và kiểm HEAD trước commit. Giữ WIP của phiên khác. HEAD đo lúc chuẩn bị: `dab4bdc405dd81fec4e63f0c6ffdf7de9b479401`. SHA kết quả tra `git log -1 --oneline -- Dai_Tang_Kinh/daoanh/docs/sessions/2026-10-15_dashboard-compliance-removal.md` từ visjs-app root.

Revert code/docs sau commit: `git revert --no-edit <SHA_commit_removal>` từ visjs-app root, kiểm đúng SHA trước chạy. Không cần restore DB/TTL vì không mutation.

[Handoff](../Handoff-2026-10-15-dashboard-compliance-removal.md). Việc kế tiếp: root QA commit; xử lý T274 bằng task riêng trước nghiệm thu full pipeline.
