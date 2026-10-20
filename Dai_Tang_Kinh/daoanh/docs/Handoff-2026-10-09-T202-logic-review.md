# Handoff — 2026-10-09 — review logic T202

## 1. Bảng thông tin đọc nhanh

| Mục | Kết quả |
|---|---|
| HEAD | c5e3afba45a262afec0e104afbe1f48e60b99ce4 |
| Task | Review logic T202-POST-REVIEW-01 hoàn tất |
| Test | 18+23+25=66/66PASS; probe tái hiện lỗi |
| Pipeline/preflight | Chưa chạy lại; không claim full PASS |
| DB/TTL/app | DB mode=ro; không sửa |
| Git | Không stage/commit; report gốc giữ nguyên |

## 2. Đọc trong 2 phút

[Review và chứng cứ](reports/T202-logic-review-20261009/README.md). Deterministic đúng nhưng identity chưa chứng minh. A001984 bị PLACE; P8 OFF vẫn có Groq gốc; validator nhận tên hỏng; unit PASS dù fixture schema lỗi. Ba việc tiếp nối: contract/type/validator/test; refresh T223 có nguồn; xử lý local ID rỗng đúng consumer. Không dùng phân nhóm để duyệt gộp/xóa ngay.

## 3. Đề xuất chữa từng phần

T201/T166: bỏ PLACE hardcode, validator chất lượng và fixture schema, test assert đúng identity tuple/safe_errors. T200/T223:31nhóm/65row hiện tại, cùng tên không đủ alias; kiểm XML/TTL/mapping. P8: outbound gate riêng nếu no-external. Search: giữ local identity chưa ánh xạ, không chỉ đổi empty sang NULL. Bằng chứng định lượng và vị trí code trong README/JSON.

## 4. Cảnh báo bắt buộc

**Không gộp/tách/xóa từ phân nhóm T202. Không chạy full importer. Không đoán ID từ filename.** TTL không Git-track. Worktree chia sẻ; Git từ visjs-app, không stage WIP session khác. Không gọi API trả phí. DB có thể thay sau snapshot này.

## 5. Hoàn tác

Không có code/DB/TTL để revert. Artifact review mới có thể giữ hoặc xóa đúng file do session tạo sau kiểm path; xóa docs chỉ mất bản review, DB/TTL mất0dữliệu. Không cần restore DB, không chạy recursive delete chung cho docs.

## 6. File tạo

Thư mục docs/reports/T202-logic-review-20261009 chứa README.md; audit_t202_logic.py/db-evidence.json; probe_fixture_and_validator.py/probe-evidence.json/probe-stderr.log; test-canonical-lock.log/test-t166-matrix.log/test-t200.log; official-source-evidence.json; observation-request.json và log gửi observation. Hai file ngoài thư mục: Handoff này và docs/sessions/2026-10-09_T202-logic-review.md.

## 7. Sai lầm và bài học

Probe đầu PowerShell báo exit1 do warning stderr thành NativeCommandError dù JSON đã xuất. Chạy lại ErrorActionPreference=Continue và exit LASTEXITCODE:0. Lần tạo tài liệu đầu Node parse lỗi do Markdown backticks trong JS template; đổi sang chuỗi quoted, không có mutation từ lần parse lỗi. Log PowerShell UTF16 được chuyển UTF8 chỉ cho artifact review. Không kết luận file gốc corrupt vì console mojibake.

Bác bỏ T202: P8OFF=zerooutbound; non-ASCII=validVI; local duplicate chứng minh DILA gộp người; IDrỗng không ảnh hưởngUI. Các phạm vi được ghi rõ trong review.

## 8. Việc chưa xong

Các sửa code/data chỉ là đề xuất. A047679 trang chính thức chưa truy cập được, chưa kết luận identity. Chưa browser search/fullpipeline/preflight. Chưa xác minh lịch sử hai địa danh chỉ từ DB. Chưa curation31nhóm hoặc tính đời.

## 9. Kiểm tra nhanh

Chạy Python -B -X utf8 cho audit_t202_logic.py, dùng mode=ro. Đọc JSON/probe/66checklogs. SHA report gốc:801fd73c408193e6661b0562b54e4fbfff3c6588c53501a634f7f618120a67d4. Lệnh/đường dẫn trong README. GitHEAD kiểm từ root.

## 10. Ghi chú agent kế tiếp

Tiếp nối T201/T166 và T223; không cấp trùngID. Đọc chứng cứ, kiểm lại schema/snapshot. Nếu sửa code: tests có ngữ nghĩa và npm.cmd run pipeline trước review. Nếu sửa dữ liệu: mapping có nguồn, dryrun/backup/guard/rollback, giữ phần chưa xác nhận, không tự cộng đời. Không ghi đè report01/10 bằng số liệu09/10.


Lưu tasktodo vào claude-mem local đã thử theo AGENTS.md: curl exit7, service37700 không kết nối được. Request và exit code lưu trong thư mục review; trạng thái được giữ ở session/Handoff, chưa đồng bộ claude-mem.
