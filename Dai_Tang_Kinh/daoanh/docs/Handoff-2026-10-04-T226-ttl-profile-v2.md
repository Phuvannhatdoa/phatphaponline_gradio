# Handoff — 2026-10-04 — T226 TTL học thuật v2

## 1. Bảng thông tin đọc nhanh

| Mục | Trạng thái / bằng chứng |
|---|---|
| Task | **T226 DONE**: phân tích, profile, editor/API staging, audit và roadmap; chưa thực hiện migration/apply toàn corpus |
| HEAD đã quan sát | 9cdee5650c5d641709a52c34ee0821cfef0671c6; HEAD dịch chuyển trong workspace chung, T226 không tạo commit |
| Test | Unit/API/schema/SHACL 26/26; UI preview và UI trên 8080 14/14, 0 page errors; pipeline exit 0, runtime 2/2 |
| Main | Windows RunAs/UAC reload thành công, PID 22920 → 17212; schema 2.0.0 HTTP 200 |
| Gateway/auth | API lineages cũ và login qua 8080 đều HTTP 200; không restart gateway hoặc auth |
| Audit | Audit Oct4 hoàn tất: 1038 file gồm 1 template, 1037 structurally valid, 10541 assertions; corpus-20261004-final và input-unchanged-20261004.json (0 mismatch) |
| DB/TTL | Không apply dữ liệu TTL vào DB, không ghi đè TTL active; save chỉ revision staging |
| Hai cạnh tự nối | Admin xác nhận đã xóa; RDF kiểm lại 2 file parse được, 0 hasTeacher/hasDisciple tự nối, SHA khớp audit hiện tại |
| Rollback | Dry-run PASS 16 file; 4 file có backup, guard SHA trước mọi restore; DB/TTL/staging không xóa |

Đọc [report](reports/T226-ttl-profile-20261003/README.md), [roadmap](reports/T226-academic-ttl-roadmap.md), [task](../tasks/T226-academic-ttl-profile-v2.md). Artifact triển khai: deployment-verified.json, reload-status.json, ui-deployed-8080.log trong docs/reports/T226-ttl-profile-20261003.

## 2. Đọc trong 2 phút

[Form chính](http://localhost:8080/daoanh/admin/monk_ttl_add.html) đã dùng profile 2.0.0. DILA/CBETA/Marcus là nguồn dẫn riêng; từng tên, tiểu sử, quan hệ và số đời có assertion, chứng cứ, phiên bản và trạng thái duyệt. Chỉ accepted mới chiếu thành triple fact trực tiếp. Tên điều hướng và loại chọn trên UI không tự trở thành chứng nhận lịch sử.

Ba việc Admin nên làm tiếp: thử một hồ sơ thật qua nút Tạo TTL và phiên đăng nhập hiện có; chốt danh mục nguồn/giấy phép đúng artifact cho P1; ưu tiên các mapping mâu thuẫn để review P2 trước batch migration. Không chạy ETL tính đời cũ cho hồ sơ v2.

## 3. Đề xuất và phần đã xây dựng

| Vấn đề | Giải pháp và bằng chứng |
|---|---|
| Tiểu sử dài thiếu chứng cứ từng trường | Person + SourceRecord + Assertion; evidence theo trường, version/SHA, reviewer/date/rationale; renderer chỉ project accepted; unit tests |
| ID/tên khác nhau giữa nguồn | DILA local 2026-09 giữ XML toàn record; accepted DILA ID kiểm exact Hán alias, ID/version/SHA; không đoán từ Việt dịch; test sai tên bị chặn |
| Cạnh mạng bị hiểu là truyền pháp | Loại quan hệ riêng và hướng thầy → trò; snapshots Marcus giữ relation_type/source_data/ref; không project mạng thành dharmaTeacherOf |
| Số đời thiếu căn cứ | Không cộng 37/thầy+1; accepted cần ít nhất 3 independence roots, hệ đếm, lập luận và review; máy kiểm metadata không thay học giả xác nhận độc lập |
| Mất lời văn/triple legacy | RDF parser + originalTurtle + SHA + graph/payload roundtrip; triple chưa ánh xạ vẫn giữ nguyên bản |
| Nạp lại làm mất review | DILA đã nạp được chặn reload; CBETA/Marcus chỉ bổ sung ID mới, không thay assertion/source đã sửa; UI 14 cases có 2 regression |
| owl:sameAs nhận literal | Validator và SHACL bắt buộc IRI; negative test ứng dụng/SHACL PASS |
| Runtime Windows ghi chung output | Runner tạo thư mục riêng, ảnh testInfo.outputPath; pipeline runtime 2/2 PASS |
| Main chạy quyền Administrator | Script guard API/process/app hash, RunAs/UAC chỉ main5000, Hidden start và health check; schema/lineages/login 200, UI8080 14/14 |

Snapshot bảo toàn record không có nghĩa mọi trường đã chuẩn hóa thành Event/Place/Work/Review resource. URI resolution, crosswalk toàn corpus, assertion revision graphs, quyền artifact và release FAIR còn theo P1–P6. Đây là application profile của dự án, chưa phải chuẩn Phật giáo quốc tế được phê chuẩn.

## 4. Cảnh báo bắt buộc

Workspace dùng chung; không bulk git add, không restore khi hash khác manifest, không quy tất cả thay đổi cho T226. Git luôn chạy từ visjs-app toplevel. app.py có staged/WIP chung; T226 chưa commit. TTL active có thể không được git track, nên dùng SHA/file-level backup.

Audit đầu có 2 selfhasDisciple; Admin sau đó xác nhận tự xóa. TS-Hung-Duong-Hien.ttl SHA hiện tại 24018f515a283101fd7d108a794cb4beda9d7e2e3516a58286cf0249700ebde0; TS-Thach-Suong-Khanh-Chu.ttl SHA d68117a5bd79ee57cee6962ccd9d94e9831707120ca2f5f96b79f8e791b9a1bd. Xem admin-self-edge-removal-verified.json. Xác minh này chỉ cho lỗi tự nối, không chứng nhận toàn bộ truyền thừa lịch sử và chưa đồng bộ hai thay đổi vào DB trong T226.

0-template.ttl chứa placeholder Turtle không parse được; không tự điền số đời/ID để làm template đạt. Registry kiểm kê có 14/14/10 row trong ba bảng, chưa xác minh đủ 25 nguồn; cả 14 data_sources chưa duyệt license. Không mở public export bằng metadata do client tự khai. T166 audit còn warning credential baseline; không in giá trị và không rotate trong T226.

Endpoint run_etl_gen cũ vẫn tồn tại để bảo toàn code; form v2 không gọi nó. Không dùng để apply v2 hoặc tự tăng đời. Main startup có FTS/cache của app cũ; T226 không apply assertion/person/lineage từ TTL vào DB.

## 5. Lệnh revert từng phần

Chạy ở daoanh:

~~~powershell
python -X utf8 scripts/t226_rollback.py
python -X utf8 scripts/t226_rollback.py --apply
~~~

Lệnh đầu chỉ dry-run; apply chỉ khi toàn bộ hash guard PASS. Restore 4 file có backup, bỏ 12 file code mới trong manifest; không xóa staging, report, DB hoặc TTL active. Sau rollback cần agent nạp lại main có guard theo app.py đã khôi phục; script reload v2 nằm trong nhóm file bị bỏ nên không dùng lại đường dẫn đó sau apply. Không restore toàn cây hoặc dùng git revert khi T226 chưa có commit riêng.

| Phần | Mất dữ liệu? |
|---|---|
| Code theo manifest | Thay đúng bản backup sau guard; không nuốt WIP khác nếu hash đổi |
| DB/TTL active | Không có migration T226 cần restore |
| Staging/history/report | Giữ nguyên |

## 6. Bảng file tạo/sửa

| File/nhóm | Mục đích |
|---|---|
| app.py, api_ttl_profile_v2.py, src_python/ttl_profile_v2.py | Blueprint, schema model, renderer/validator/parser |
| admin/monk_ttl_add.html, admin/ttl-profile-v2.js | Form v2 và chuyển dữ liệu từ person page; person-ttl-draft.js giữ hợp đồng cũ |
| ontology/ttl-profile-v2/* | JSON Schema, ontology, SHACL |
| scripts/migrate_ttl_profile_v2.py | Audit/stage từng file, manifest/hash, không apply |
| scripts/reload-ttl-v2-main.ps1 | Guarded Windows reload main5000, health/status |
| tests/test_t226_ttl_profile.py, tests/t226-ui-check.cjs | 26 unit/API/schema tests, 14 UI cases |
| requirements-ttl-v2-dev.txt | Deps test pin, cài riêng trong backup |
| scripts/run-runtime-tests.cjs, tests/e2e-runtime.spec.js, package.json | Output runtime riêng và nối test:t226 vào pipeline |
| tasks/T226-*, roadmap, README, tasktodo, progress_data.json, sessions/Handoff | Kế hoạch, bằng chứng, Dashboard và bàn giao |

Danh sách code/backup chính xác nằm ở rollback-manifest.json; không dùng bảng này để stage cả thư mục.

## 7. Sai lầm tự mình làm và bài học

Nested JavaScript template từng gây SyntaxError; tách text trước khi ghi file. Copy-Item có lần báo success nhưng nội dung HTML chưa đổi; luôn verify bytes/SHA. UI chờ timeout/status quá sớm từng báo fail giả; đổi sang chờ response thực tế. Runtime dùng chung ảnh/.last-run.json bị Windows chặn; dùng output riêng thay vì xóa artifact khác. PowerShell 5 cần UTF-8 BOM cho script có tiếng Việt; script reload đã parse syntax PASS.

Review phát hiện literal owl:sameAs và reload ghi mất metadata; cả hai đã sửa, test hồi quy PASS. Bản đầu từng tự project type Monastic/CRM E21 và nhãn điều hướng; đã bác bỏ cách đó, chuyển thành source_asserted/assertion accepted riêng. Không gọi metadata 3 independence keys là chứng minh học thuật tự động.

Pipeline sandbox sau review exit 1 do CDN/font/Tailwind bị ERR_NETWORK_ACCESS_DENIED ở PlaceVN; không đổi code để né test. Rerun cả pipeline có quyền mạng đọc đã exit 0, runtime 2/2: pipeline-review-fixes-network.log và pipeline-status.json. UI result ban đầu thiếu nhãn một ca dù console đếm 12; đã sửa danh sách và thêm regression, artifact hiện liệt kê đúng 14.

## 8. Việc chưa xong theo ưu tiên

T226 DONE trong phạm vi tạo profile/form/API staging và roadmap. Chưa normalize toàn bộ source snapshots, chưa xác minh toàn bộ lịch sử, chưa migrate/apply DB, chưa mở public release.

P1 kiểm kê nguồn25 và artifact-level rights/version; P2 identity crosswalk/merge-split và canonical person URI templates; P3 evidence Passage/selectors, Event/Place/Work/Review/CountingScheme và immutable assertion revisions; P4 importer v2 + review + snapshot + TTL-scoped apply + API/tree/rollback; P5 resolver/catalog/distribution/DOI; P6 incremental review và governance. Cấp task mới phải kiểm trùng ID cả hai tầng.

Save authenticated được kiểm bằng fixture token và storage idempotency; UI origin chính kiểm 401 khi thiếu session. Admin nên thử lưu một bản nháp bằng phiên thật; không giả mạo session hoặc lấy token từ DB để kiểm thay Admin.

## 9. Lệnh kiểm tra nhanh

~~~powershell
$env:PYTHONPATH='data/backups/T226-ttl-profile-20261003/python-deps;data/backups/T215-fix-sync-20261002/python-deps'
$env:T226_UI_BASE_URL='http://localhost:8080'
npm.cmd run test:t226
node tests/t226-ui-check.cjs
python -X utf8 scripts/t226_rollback.py
~~~

Pipeline đầy đủ npm.cmd run pipeline; runtime cần CDN access. Evidence: pipeline-status.json, deployment-verified.json, ui-result.json, ui-deployed-8080.log, admin-self-edge-removal-verified.json và manifest/summary của corpus. Log PowerShell gốc UTF-16LE, các bản .utf8.log đã chuyển encoding đúng.

## 10. Ghi chú cho agent kế tiếp

Đọc task/roadmap/report và tasktodo trước. Kiểm HEAD/status từ repo top-level, xác minh SHA hiện tại trước sửa/apply/rollback. Lấy PID từ reload-status.json/port/process thực tế, không dùng PID ghi nhớ để kill. Không khởi động server trùng port khi main đang chạy. Không thay raw XML/DOCX, không tính đời theo công thức, không tự nâng cạnh mạng thành truyền pháp.

Preview 5006 đã dừng sau deployment. Khi kiểm UI dùng origin8080 như lệnh ở mục9, không giả định helper cũ còn chạy. Dashboard API HTTP200 trả T226 status done; bằng chứng dashboard-verified.json.

Tạo task P1/P2 theo guard hai tầng; xây catalog/crosswalk trước batch P4. Khi stage cần thư mục output mới ngoài input, manifest và backup theo file. Chỉ accepted đi vào fact; các assertion legacy/unverified phải còn có thể truy lại nguyên văn. Giữ phân biệt DONE của T226 với việc hoàn thiện công bố dataset dài hạn.


Memory cuối phiên: đã POST tasktodo theo protocol; localhost:37700 không chạy, curl exit7. Không tuyên bố memory từ xa đã lưu. Request và fallback giữ ở tasktodo-memory-request.json / tasktodo-memory-fallback.json; docs/tasktodo.md, session04 và Dashboard đã ghi T226 DONE. Agent sau có thể gửi lại request khi memory service hoạt động.
