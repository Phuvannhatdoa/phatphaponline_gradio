# Session 2026-10-10 — Code, Debug, Deep Research

- Mục tiêu: chuyển workflow sang code, debug, deep_research và root QA/điều phối với Admin.
- Trạng thái: DONE docs; root QA cuối PASS docs-only; Debug recheck cuối PASS docs-only. Không xin review build.
- Scope/writer: Code viết workflow và hai docs mới; không sửa session/Handoff cũ, tasktodo/dashboard, code/TTL/DB; không cấp ID, stage hoặc commit.
- Nghiệm thu: đủ bốn vai trò, ba mapping cũ, quyền writer, gói task đủ mục tiêu/scope/nghiệm thu/chứng cứ/test/rollback/trạng thái và giới hạn 4 agent kể cả root.

## Kết quả và chứng cứ

[Workflow](../SUBAGENT-WORKFLOW.md) ghi app_integration → code; ttl_data → debug mở rộng kiểm độc lập; source_research → deep_research. Agent cũ không nhận task mới; phiên mới có thể cần tạo lại. Debug chỉ sửa khi root giao rõ quyền writer. Root giao task và QA.

Giữ nguyên cổng A000662/Minh Hải, ba nguồn độc lập, source_asserted, dry-run/backup/rollback/QA và không full importer cho một hồ sơ. Bổ sung raw XML bất biến; sau phát hiện của Debug, ghi rõ tối thiểu 3 chứng cứ độc lập để sửa/tăng số đời, chứng minh số cũ sai/số đúng/hệ đếm/đúng nhân vật-ID và chặn accepted/mốc tự động khi thiếu chứng cứ. Đây là quy tắc được giữ lại; lượt này không xác minh sử liệu hay corpus.

| Đối tượng | SHA256 |
|---|---|
| Workflow trước / backup byte gốc | c0116e3575bc5691d27d19904fa9ea276ef36ca241b48b3e84d96f80d2219e99 |
| Workflow sau | d76d6dad362d02c4aa3e74a763f197d46793431480e2eb2f925c4af0c4dac4e5 |

Backup: `data/backups/subagent-roles-20261010/SUBAGENT-WORKFLOW.before.md`. Đã kiểm hash đầu vào trước ghi; hai docs mới dùng `wx` để không ghi đè.

## Đã đọc/chạy và giới hạn

- Đọc `daoanh/AGENTS.md`, workflow; memory quick-pass chỉ nhắc repo root/không nhận PASS cũ.
- Git đọc tại visjs-app: `git rev-parse --show-toplevel`, `git rev-parse HEAD`; HEAD lúc đọc `f0d58d3a83502d8b8642c22c44bdc4197be0eadd`.
- Get-FileHash/Python/Node SHA256 kiểm backup/workflow; apply_patch sửa workflow; Node fs UTF-8 và `wx` tạo docs.
- Không chạy pipeline/tester/preflight, API/DB hay corpus check; không claim PASS build. Root đã QA read-only cả ba docs trước sửa cổng: UTF-8 không U+FFFD, sáu link Markdown trỏ file có thật, Handoff đủ mục 1–10 và hash workflow/backup khớp. Debug phát hiện thiếu cổng tối thiểu 3 chứng cứ; đã sửa workflow dòng 42 và thêm đường task đơn giản code → debug → root QA ở dòng 33. Root kiểm lại workflow PASS: hash d76d6dad... khớp và chỉ dòng 33/42 thay đổi; Debug recheck cuối PASS docs-only.

## Sai lầm và sửa cách ghi

Python thiếu -X utf8 lỗi console cp1252. Pipe PowerShell đổi tiếng Việt thành dấu ?, assertion chặn trước ghi workflow; chỉ backup byte gốc đã tạo. apply_patch sửa thành công; Node đọc lại hash sau sửa. Một lệnh Node tạo docs lỗi parse do backticks lồng nhau, chưa ghi; đổi sang chuỗi JSON an toàn. Không lặp cách pipe encoding đó. Sai sót nội dung: giữ diễn đạt tiêu chuẩn chứng cứ chung nhưng chưa ghi số tối thiểu 3; Debug phát hiện và root giao bổ sung. Root đã kiểm lại cổng PASS docs-only; Debug recheck cuối PASS docs-only.

Debug độc lập xác nhận workflow 8299 bytes/hash d76d6dad... và backup c0116e... khớp; dòng 42 đủ cổng ≥3 chứng cứ độc lập, số cũ sai/số đúng/hệ đếm/đúng entity, insufficient skip/accepted gate/cấm nguồn giả; dòng 33 Research conditional. Phục dựng hai dòng từ snapshot ra hash c0b56e... xác nhận chỉ hai đoạn thay đổi; UTF-8/NFC/không mojibake và hai link workflow PASS. Không chạy pipeline/build/corpus check.

## Observation cuối phiên

POST http://127.0.0.1:37700/api/sessions/observations; timeout 5 giây; thất bại: fetch failed; cause: ECONNREFUSED. Chỉ có bản ghi local; không xác nhận đã lưu remote.

## Rollback và tiếp nối

[Handoff](../Handoff-2026-10-10-code-debug-deep-research.md) mục 5 có rollback workflow kiểm hash hiện hành và backup. Giữ hai docs làm chứng cứ. Root QA cuối đã PASS docs-only; Debug đã kiểm lại workflow bổ sung PASS docs-only theo scope read-only; task triển khai tiếp chờ root giao, không tự nghiên cứu Minh Hải/toàn corpus.
