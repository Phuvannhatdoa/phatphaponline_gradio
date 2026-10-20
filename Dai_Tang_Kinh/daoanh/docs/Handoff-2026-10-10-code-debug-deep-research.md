# Handoff 2026-10-10 — Code, Debug, Deep Research

## 1. Bảng thông tin đọc nhanh

| Mục | Kết quả |
|---|---|
| Ngày / session | 2026-10-10 / [session](sessions/2026-10-10_code-debug-deep-research.md) |
| HEAD lúc đọc tại visjs-app | f0d58d3a83502d8b8642c22c44bdc4197be0eadd; có thể dịch do session khác |
| Trạng thái | DONE docs; root QA cuối PASS docs-only; Debug recheck cuối PASS docs-only |
| Test / preflight | Không chạy pipeline/tester/preflight; không claim PASS build |
| DB / TTL / raw XML | Không thao tác ghi hoặc đồng bộ |

## 2. Đọc trong 2 phút

Đội mới: code, debug, deep_research, root. Workflow ghi ba mapping cũ; agent cũ không nhận task mới; Debug chỉ sửa khi root giao rõ quyền. Root đã QA cuối PASS docs-only; Debug phát hiện thiếu cổng tối thiểu 3 chứng cứ và Code đã sửa. Debug kiểm lại workflow PASS docs-only. Việc tiếp: root tiếp nhận ưu tiên Admin và giao task cụ thể. Không có quyết định dữ liệu mới.

## 3. Phần sửa và chứng cứ

Scope: một workflow, hai docs mới. [Workflow](SUBAGENT-WORKFLOW.md) thêm mapping/quyền/gói task; đủ bốn vai trò và giới hạn 4 active kể cả root. Giữ cổng A000662/ba nguồn/backup/QA, bổ sung raw XML bất biến và cổng tối thiểu 3 chứng cứ độc lập cho sửa/tăng số đời (số cũ sai, số đúng, hệ đếm, đúng nhân vật/ID). Task đơn giản có thể code → debug → root QA, Deep Research được giao khi cần xác minh. SHA256 trước = `c0116e3575bc5691d27d19904fa9ea276ef36ca241b48b3e84d96f80d2219e99`; sau = `d76d6dad362d02c4aa3e74a763f197d46793431480e2eb2f925c4af0c4dac4e5`. Root QA read-only cả ba docs trước sửa cổng: UTF-8 không U+FFFD, sáu link Markdown trỏ file có thật, Handoff đủ mục 1–10 và hash workflow/backup khớp. Debug phát hiện thiếu tối thiểu 3 chứng cứ; đã sửa. Root kiểm lại workflow PASS: hash d76d6dad... khớp và chỉ dòng 33/42 thay đổi; Debug recheck cuối PASS docs-only. Đây là kiểm docs, không phải pipeline/build/corpus PASS.

Debug độc lập xác nhận workflow 8299 bytes/hash d76d6dad... và backup c0116e... khớp; dòng 42 đủ cổng ≥3 chứng cứ độc lập, số cũ sai/số đúng/hệ đếm/đúng entity, insufficient skip/accepted gate/cấm nguồn giả; dòng 33 Research conditional. Phục dựng hai dòng từ snapshot ra hash c0b56e... xác nhận chỉ hai đoạn thay đổi; UTF-8/NFC/không mojibake và hai link workflow PASS. Không chạy pipeline/build/corpus check.

## 4. Cảnh báo bắt buộc

**Một writer mỗi file/transaction; không giao task mới cho agent cũ.** HEAD có thể dịch trong worktree chung. Git chạy tại visjs-app; không stage/commit lượt này; quyền rename/index Windows theo AGENTS §§14/17. TTL không được Git bảo vệ, task dữ liệu cần backup riêng. Phiên mới kiểm agent hiện có; không coi vai trò là tiến trình nền vĩnh viễn.

## 5. Rollback có hash guard

| Phần | Hoàn tác | Mất dữ liệu? |
|---|---|---|
| Workflow | Phục hồi byte backup sau kiểm hai hash | Không mất corpus; bỏ thay đổi vai trò lượt này |
| Hai docs mới | Giữ nguyên làm chứng cứ, không xóa | Không |

Chạy PowerShell từ daoanh. Hash lệch phải dừng để root điều phối.

```powershell
$roleWorkflow = Join-Path $PWD 'docs\SUBAGENT-WORKFLOW.md'
$roleBackup = Join-Path $PWD 'data\backups\subagent-roles-20261010\SUBAGENT-WORKFLOW.before.md'
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $roleWorkflow).Hash -ne 'd76d6dad362d02c4aa3e74a763f197d46793431480e2eb2f925c4af0c4dac4e5') { throw 'Workflow da doi; dung rollback' }
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $roleBackup).Hash -ne 'c0116e3575bc5691d27d19904fa9ea276ef36ca241b48b3e84d96f80d2219e99') { throw 'Backup sai hash; dung rollback' }
[System.IO.File]::WriteAllBytes($roleWorkflow, [System.IO.File]::ReadAllBytes($roleBackup))
Get-FileHash -Algorithm SHA256 -LiteralPath $roleWorkflow
```

## 6. Bảng file tạo/sửa

| File tương đối daoanh | Thao tác |
|---|---|
| docs/SUBAGENT-WORKFLOW.md | Sửa vai trò/quyền/mapping/gói task/link |
| docs/sessions/2026-10-10_code-debug-deep-research.md | Tạo mới bằng wx |
| docs/Handoff-2026-10-10-code-debug-deep-research.md | Tạo mới bằng wx; đủ 10 mục |
| data/backups/subagent-roles-20261010/SUBAGENT-WORKFLOW.before.md | Backup byte gốc bằng xb; hash bằng workflow trước |

## 7. Sai lầm và bài học

Python thiếu -X utf8 lỗi cp1252; pipe PowerShell đổi tiếng Việt thành dấu ?, assertion dừng trước ghi workflow. Cách pipe đó đã bị kiểm chứng không phù hợp; đổi sang apply_patch/Node fs UTF-8. Node tạo docs lần đầu lỗi parse backticks, chưa ghi; dùng chuỗi JSON rồi tạo bằng wx. Backup gốc đúng hash; không có sửa dữ liệu phải hoàn tác. Sai sót nội dung: chưa ghi số tối thiểu 3 chứng cứ ở cổng số đời; Debug phát hiện và root giao sửa tối thiểu. Đã cập nhật workflow/hash/guard; root kiểm lại PASS docs-only; Debug recheck cuối PASS docs-only.

## 8. Việc chưa xong theo ưu tiên

QA docs đã xong: root QA và Debug recheck đều PASS docs-only.

1. Root nhận ưu tiên Admin và giao task triển khai cụ thể; không tự mở task/ID.
2. Observation bị ECONNREFUSED: giữ kết quả local, thử lại khi service có. Không báo đã lưu remote.

## 9. Lệnh kiểm nhanh

Từ daoanh, chỉ đọc:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath 'docs\SUBAGENT-WORKFLOW.md','data\backups\subagent-roles-20261010\SUBAGENT-WORKFLOW.before.md'
rg -n 'code|debug|deep_research|DONE/PARTIAL/BLOCKED|A000662|Tối đa 4|không tiếp tục nhận task mới' docs/SUBAGENT-WORKFLOW.md
rg -n '^## [0-9]+\.' docs/Handoff-2026-10-10-code-debug-deep-research.md
```

Đọc lịch sử Git: chuyển tới visjs-app, chạy `git log --oneline -5`; không coi HEAD snapshot là chứng cứ đã commit.

## 10. Ghi chú agent kế tiếp

Đọc AGENTS/workflow/session mới; kiểm agent và hash đầu vào; xác nhận một writer. Task phải có mục tiêu, scope/file, nghiệm thu, chứng cứ/source/locator, test/rollback và DONE/PARTIAL/BLOCKED. Code triển khai; Debug tái hiện/root-cause/regression/kiểm độc lập, chỉ sửa khi được root giao rõ quyền; Deep Research báo nguồn/mâu thuẫn/mức chắc chắn; root QA/điều phối Admin. Đợt này docs-only, không sửa tasktodo/dashboard/code/TTL/DB.

Observation cuối phiên: POST http://127.0.0.1:37700/api/sessions/observations; timeout 5 giây; thất bại: fetch failed; cause: ECONNREFUSED. Chỉ có bản ghi local; không xác nhận đã lưu remote.
