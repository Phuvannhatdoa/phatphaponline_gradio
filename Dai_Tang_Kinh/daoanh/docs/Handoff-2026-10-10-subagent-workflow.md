# Handoff 2026-10-10 — subagent workflow

## 1. Bảng thông tin đọc nhanh

| Mục | Trạng thái |
|---|---|
| Ngày | 2026-10-10 |
| HEAD đọc tại visjs-app | 03903d98055e00330a126fe5d851db8c4ab8c3bb; không cố định HEAD phiên khác |
| Session | docs/sessions/2026-10-10_subagent-workflow.md |
| Phạm vi | Tổ chức root QA + ba vai trò, ba docs mới |
| Test/preflight | Không chạy trong lượt docs-only; không yêu cầu review build |
| DB/TTL/code/rawXML | Không cập nhật; DB/API không kiểm |
| Commit/stage/tasktodo/dashboard | Không thay đổi |

## 2. Đọc trong 2 phút

Admin đã yêu cầu root chỉ QA/điều phối và tạo subagent theo mục đích. Đã ghi quy trình nhận việc, quyền sửa mỗi file, đầu ra, QA, backup/dry-run và giới hạn chạy trong docs/SUBAGENT-WORKFLOW.md.

Điểm dễ nhầm: tạo đội agent không đồng nghĩa hệ thống đã sync DB, chạy nền hoặc cài Hermes. Tối đa bốn agent cùng hoạt động gồm root; tên vai trò trong docs không giữ tiến trình vĩnh viễn.

Ba hướng Admin có thể giao tiếp: đồng bộ scoped hồ sơ local; đối chiếu sử liệu còn thiếu; sửa một API/UI theo tiêu chí cụ thể. Chưa chọn hoặc thực hiện một hướng mới thay Admin.

Admin chốt: từ nay Admin và root giữ QA, quyết định ưu tiên; root chia từng task cụ thể và giao phần triển khai cho các agent. Mỗi giao việc ghi mục tiêu, scope/file, tiêu chí nghiệm thu, chứng cứ, kiểm thử/rollback và báo cáo DONE/PARTIAL/BLOCKED. Ba tác vụ khởi động của source_research, ttl_data và app_integration đã hoàn tất; nhiệm vụ triển khai tiếp theo được root giao theo ưu tiên Admin.

## 3. Vấn đề, cách xử lý, bằng chứng

| Việc | Cách xử lý và kết quả | Bằng chứng/giới hạn |
|---|---|---|
| Chia việc | root QA; source_research nghiên cứu; ttl_data dữ liệu; app_integration code/sync/tests | Yêu cầu Admin; quy trình trong SUBAGENT-WORKFLOW.md |
| Minh Hải local | ttl_data báo RDF/verifier read-only PASS, hash active bad70763da261a07ed0736f06cab7599c45046f22e6f1eab9a03cfff0e3856d8 giữ nguyên; self-edge0, đời71 | Agent ttl_data kiểm; source_asserted chưa accepted v2; không DB/API |
| Định danh/sử liệu | source_research đọc X0613 dòng12/149/200, trích nghiên cứu2017: A000662 khác nhân vật Chúc Thánh; BáoTư cũ/TânTự không gộp | Không web/corpus/PDF thân văn lượt này; chưa ba sử liệu độc lập cho quan hệ/đời71 |
| Đường app | /import=parse+validate; /save=staging; /from_db và /export_db=đọc DB; monk_ttl legacy tạo file mới | api_ttl_profile_v2.py:132/189/211/219; app.py:24466/24505. Không gọi API; chưa xác minh sync đầy đủ một hồ sơ |

## 4. Cảnh báo bắt buộc

**Dễ bỏ sót nhất: TTL đúng ở local chưa chứng minh DB/API đúng; generic teacher không tự thành truyền pháp; không gắn A000662 cho Minh Hải Chúc Thánh.** Không tăng đời hoặc accepted mốc tự động khi thiếu chứng cứ. DILA chưa tìm thấy ID phù hợp không có nghĩa chắc chắn toàn bộ DILA/CBETA không có nhân vật.

Worktree dùng chung: một writer mỗi file/giao dịch; bảo toàn WIP khác, kiểm đầu vào trước ghi. TTL không được bảo vệ bằng Git như code: phải backup file-level. Git từ visjs-app; không stage/commit trong lượt này, không lấy cây docs/tasks để stage chung. Lượt build xin review tiếp phải chạy pipeline bắt buộc và báo đúng bước lỗi.

## 5. Hoàn tác từng phần

| Phần | Mất dữ liệu? | Hoàn tác |
|---|---|---|
| Ba docs mới | Không khi đổi tên giữ bản gốc | Lệnh dưới giữ file ở đuôi .disabled; không ghi đè đích |
| DB/TTL/code | Không thay đổi trong lượt này | Không cần rollback |

Chạy từ daoanh sau khi kiểm các file vẫn thuộc đợt này; lệnh không được thực thi trong phiên:

```powershell
$docsBase = (Resolve-Path -LiteralPath '.\docs').Path
$docItems = @('SUBAGENT-WORKFLOW.md','sessions\2026-10-10_subagent-workflow.md','Handoff-2026-10-10-subagent-workflow.md')
foreach ($docItem in $docItems) {
    $docPath = (Resolve-Path -LiteralPath (Join-Path $docsBase $docItem)).Path
    if (-not $docPath.StartsWith($docsBase + '\', [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Đường dẫn ngoài docs' }
    $docDisabled = $docPath + '.disabled'
    if (Test-Path -LiteralPath $docDisabled) { throw 'Đích hoàn tác đã tồn tại; giữ nguyên' }
    Move-Item -LiteralPath $docPath -Destination $docDisabled
}
```

## 6. File tạo/sửa

| File | Thao tác | Writer |
|---|---|---|
| docs/SUBAGENT-WORKFLOW.md | Tạo mới độc quyền, không ghi đè file khác | app_integration |
| docs/sessions/2026-10-10_subagent-workflow.md | Tạo mới | app_integration |
| docs/Handoff-2026-10-10-subagent-workflow.md | Tạo mới, đủ10mục | app_integration |

Không sửa tasktodo, dashboard, task T232/T233 hoặc các report trước.

## 7. Sai lầm đã gặp và bài học

app_integration có lần tìm nhầm AGENTS ở Dai_Tang_Kinh và rg đường dẫn tương đối khi cwd là visjs-app. Những lượt đọc đó báo không tìm thấy, không phải bằng chứng file dự án mất. Đã đọc trực tiếp daoanh/AGENTS.md qua fs và truy vết code theo root tuyệt đối. PowerShell đọc UTF8 không chỉ định encoding tạo hiển thị mojibake; chuyển đọc UTF8 qua fs, không sửa file nguồn.

Không coi tên nguồn giống nhau/cùng chùa là định danh hoặc quan hệ đã được xác minh; không dùng log pipeline cũ để báo PASS hiện tại.

## 8. Việc chưa xong

1. DONE — root đã đọc đầy đủ ba docs và QA phân vai/phạm vi, Handoff đủ 10 mục, payload JSON/tool_response parse được và UTF-8 không U+FFFD. Root tự đo hash TTL active bad70763da261a07ed0736f06cab7599c45046f22e6f1eab9a03cfff0e3856d8 khớp manifest, không sửa TTL. Đây là QA tài liệu và đối chiếu hash, không phải pipeline/build PASS.
2. Chờ Admin giao mục tiêu cụ thể tiếp theo; không tự sync Minh Hải hoặc chạy toàn corpus từ yêu cầu tổ chức subagent.
3. Nếu mục tiêu là sync local: xác minh DB read-only, đề xuất transaction chỉ phạm vi hồ sơ, backup/diff/tests và post-verify API. Hiện chưa chạy.
4. Nếu mục tiêu là accepted đời/mốc v2: thu thập đủ sử liệu độc lập và xác minh từng cạnh; local+Admin chưa thay thế tiêu chuẩn chứng cứ.

## 9. Lệnh kiểm tra nhanh

Từ daoanh, chỉ đọc:

```powershell
Get-Content -Encoding UTF8 -LiteralPath docs/SUBAGENT-WORKFLOW.md
rg -n '^## [0-9]+\.' docs/Handoff-2026-10-10-subagent-workflow.md
rg -n 'source_research|ttl_data|app_integration|A000662|followup_task|4 agent' docs/SUBAGENT-WORKFLOW.md
```

Muốn kiểm Git: chuyển về visjs-app và chạy git rev-parse HEAD hoặc git log; không mặc nhiên HEAD vẫn ở số ghi đầu phiên. Không chạy pipeline chỉ để lặp lại kiểm tra docs này; pipeline bắt buộc khi xin review build theo AGENTS.

## 10. Ghi chú cho agent kế tiếp

Đọc SUBAGENT-WORKFLOW trước; kiểm agent sống và giới hạn bốn slot; nhận followup có scope; không tự mở batch paid/model; một writer mỗi file; giữ quyết định A000662 exclusion; tách source_asserted/accepted; báo từng ranh giới file/DB/API đã kiểm. Không cài Hermes nếu chưa được yêu cầu. File handoff này tổ chức quy trình, không khẳng định T232/T233/build/DB sync hoàn tất.

POST tasktodo cuối phiên sẽ được ghi dưới đây sau lần thử; chỉ báo đã lưu nếu có phản hồi thành công.

### Kết quả POST tasktodo cuối phiên

Đã thử POST http://127.0.0.1:37700/api/sessions/observations; thất bại: fetch failed / ECONNREFUSED. Không claim đã lưu claude-mem. Trạng thái hiện nằm trong session/Handoff local.

Payload: {"contentSessionId":"daoanh-master","tool_name":"tasktodo","tool_input":{},"tool_response":"{\"current_task\":\"subagent-workflow\",\"status\":\"done\",\"next_task\":\"assignment-by-admin\"}","cwd":"/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh"}
