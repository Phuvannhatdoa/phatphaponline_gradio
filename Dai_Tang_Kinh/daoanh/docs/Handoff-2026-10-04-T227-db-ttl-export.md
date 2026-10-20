# Handoff — T227 — 2026-10-04

## 1. Bảng thông tin đọc nhanh

| Mục | Kết quả đã kiểm |
|---|---|
| Task | T227 — Xuất TTL v2 từ DB — DONE |
| HEAD quan sát cuối | 0e78c4a3654a00f1d139ab834d8de4b325019064, do phiên khác; chưa commit T227 |
| Main | PID 6032, port 5000, ready lúc 14:17:58 +07:00; phục hồi sau PID 30900 mất listener |
| Gateway / Auth | 8080 / 5001 giữ nguyên; API và login HTTP 200 |
| Unit / hồi quy / governance | T227: 18/18; T226: 26/26; governance: 18/18 |
| UI 8080 | 13/13 PASS, không có lỗi JavaScript |
| Pipeline | pipeline-delivery exit 0; runtime 2/2. Click Mapping PlaceVN chưa kiểm vì không có nút |
| Kho nguồn mới | 49.361 XML DILA và 1.045 TTL; tổng 50.406 record |
| Gói xuất | 1.037 TTL v2 và 8 chứng cứ nguyên văn; ZIP 8.170.269 bytes |
| Kiểm toàn bộ gói | 1.037/1.037 RDF/profile/SHA; 8/8 chứng cứ; CRC sạch |
| Ngữ nghĩa | 0 nhận định tự chuyển sang accepted; 0 quan hệ typed tự nối; 0 khóa hồ sơ trùng |
| DB | WAL; quick_check=ok; importer chỉ ghi hai bảng nguồn mới |

## 2. Đọc trong 2 phút

Admin yêu cầu lấy dữ liệu đã có trong DB để xuất format TTL v2, không nhập lại bằng tay. Kiểm thực tế: people có 48.673 rows nhưng people_full rỗng; ttl_master chỉ có 2 rows. Import cũ chưa lưu đầy đủ record XML và nguyên văn TTL. Đã tạo SQLite backup nhất quán rồi bổ sung kho nguồn additive; XML/TTL gốc, tên, quan hệ và số đời đang chạy không bị importer sửa.

Trang monk_ttl_add có Nạp hồ sơ từ DB, Xuất TTL từ DB, Xuất bộ TTL đã nhập và Tải ZIP. Dùng DILA ID, ttl:filename.ttl hoặc slug:ten_slug. Tải TTL đang biên tập và Lưu bản nháp vẫn phục vụ biên tập/staging riêng.

Ba việc Admin cần xem tiếp: bốn source TTL tự nối tại mục 3; các crosswalk chưa verified; phiên bản và quyền đúng artifact trước khi công bố. Source Hub/LicenseGate T231 vừa được phiên khác cập nhật; T227 chưa review tương tác của task đó.

## 3. Phần đã sửa và đề xuất còn lại

| Vấn đề | Xử lý | Bằng chứng |
|---|---|---|
| Thiếu XML/raw TTL đầy đủ trong DB | Hai bảng ttl_v2_source_import_runs và ttl_v2_source_records; đọc streaming | source-import-summary.json, manifest 50.406 records |
| 1.045 nguồn không đều là hồ sơ hợp lệ | 1.038 active, 7 cách ly; xuất 1.037 hồ sơ, giữ 8 nguồn lỗi/cách ly ở phụ lục | export-summary.json và manifest ZIP |
| Mapping cũ có thể gán nhầm người | Chỉ ghép verified, đúng alias của chính XML ID, duy nhất một main verified | 21 hồ sơ ghép DILA; không gộp theo tên |
| Số tính sẵn dễ bị coi là đời đã xác minh | Giữ giá trị và hệ đếm trong nhận định tham chiếu | Unit và 0 accepted claims trong cả gói |
| Thầy chung dễ bị nâng thành truyền pháp | da:isTeacherOf giữ nghĩa thầy chung; raw_relation_type/ref/status còn nguyên | Unit kiểm hướng cạnh và không chuyển thành dharmaTeacher |
| Main app.py liên tục thay đổi | Hai lần guard chặn trước khi kill; bootstrap lại bên trong helper ngay trước restart | reload-attempt-history.json, bootstrap-inside-reload.log |

Bốn file nguồn hiện có hasTeacher trỏ về chính mình: TS-Dien-Phuc-Tue-Thang.ttl, TS-Dinh-Lam-Canh-Phuong.ttl, TS-Dong-Son-Trach-Ngon.ttl, TS-Vo-Chuan-Su-Pham.ttl. Đã đọc bằng rg và kiểm RDF. Trong v2, nguyên văn được giữ ở originalTurtle/sourceSnapshot và issue; không tạo assertion quan hệ typed từ cạnh đó. T227 không sửa những file này hoặc DB truyền thừa. Claim lịch sử T215 9/9 không thay thế kiểm chứng trạng thái hiện tại.

## 4. Cảnh báo bắt buộc

**Không chạy ETL TTL cũ hoặc tính lại đời để xuất dữ liệu.** Exporter chỉ đọc DB. Năm bảng nền people/VN authority/VN relations/lineage assertions/computed generations có số rows trước/sau importer không đổi.

**TTL và data không được Git track.** Giữ backup file-level, SQLite snapshot và manifest. Không suy ID từ filename/tên gần giống, không cộng 37 hoặc dùng thầy + 1 để sửa đời.

**Worktree/HEAD dùng chung.** app.py được phiên khác sửa ngay trong lần kiểm này. Không git add theo thư mục, không restore WIP của phiên khác. SHA rollback phải còn khớp.

Batch dùng read transaction trên WAL, từng hồ sơ mỗi vòng. Job đang chạy nằm trong memory; job hoàn tất được đọc lại từ summary trên disk sau restart. Admin batch/save dùng X-Session-Token. Không tạo token giả trên production. Gói public v2 vẫn yêu cầu quyền đúng artifact; LEGACY pass-through ở task khác không tự chứng minh giấy phép đã verified.

## 5. Lệnh revert từng phần

Chạy từ daoanh:

~~~powershell
python -X utf8 scripts/t227_rollback.py --code
python -X utf8 scripts/t227_rollback.py --sources-db
# Sau khi guard PASS và có yêu cầu hoàn tác:
python -X utf8 scripts/t227_rollback.py --code --apply
python -X utf8 scripts/t227_rollback.py --sources-db --apply
~~~

| Phần | Dữ liệu ảnh hưởng | Guard |
|---|---|---|
| Code | Khôi phục 5 file cũ, xóa 8 file mới; giữ docs/backup/staging/ZIP | SHA của 13 file và backup phải khớp |
| Kho nguồn DB | Xóa đúng 50.406 records của run T227; giữ bảng nền | Không có run import khác, count phải khớp |
| Restore whole DB | Có thể mất cập nhật của phiên khác sau snapshot | Không dùng mặc định |

Dry-run đã PASS 13 files/50.406 records; chưa apply rollback. Sau rollback code cần restart main với API schema T226. Helper T227 yêu cầu from_db nên không dùng nguyên trạng sau khi API này đã bị hoàn tác. Có thể chạy đoạn sau bằng PowerShell Administrator từ daoanh; kiểm lại PID và hash trước khi dừng:

~~~powershell
$ErrorActionPreference='Stop'
$env:PYTHONPATH='data/backups/T226-ttl-profile-20261003/python-deps;data/backups/T215-fix-sync-20261002/python-deps'
$mainPort227=Get-NetTCPConnection -State Listen -LocalPort 5000 | Select-Object -First 1
$mainProcess227=Get-CimInstance Win32_Process -Filter "ProcessId=$($mainPort227.OwningProcess)"
if ($mainProcess227.CommandLine -notmatch 'app\.py') {throw 'Không đúng main app.py'}
$hashBefore227=(Get-FileHash app.py).Hash
python -X utf8 -c "import app; assert app.app.test_client().get('/daoanh/api/admin/ttl_v2/schema').status_code == 200"
if ($LASTEXITCODE -ne 0 -or (Get-FileHash app.py).Hash -ne $hashBefore227) {throw 'Bootstrap/hash không đạt; giữ main cũ'}
Stop-Process -Id $mainProcess227.ProcessId -Force
$env:APP_PORT='5000'
Start-Process -FilePath (Get-Command python).Source -ArgumentList @('-X','utf8','app.py') -WorkingDirectory (Get-Location).Path -WindowStyle Hidden
# Sau khi main ready, kiểm schema và lineages HTTP 200; giữ 8080/5001.
~~~

Đoạn restart dành cho lần rollback được yêu cầu, chưa chạy trong session này. Nếu guard phát hiện file đã đổi, chuẩn bị diff revert trên HEAD mới; không force overwrite.

## 6. Bảng file tạo/sửa

| File | Vai trò |
|---|---|
| api_ttl_profile_v2.py | API DB/single TTL/batch/status/download; đọc cache XML; khôi phục job done |
| admin/monk_ttl_add.html, admin/ttl-profile-v2.js | Nạp DB, xuất DB/ZIP, giữ form biên tập và snapshot chuyển trang |
| src_python/ttl_db_sources.py | Kho nguồn, stream import, SHA và completed-run guard |
| src_python/ttl_db_export.py | Adapter exact ID, provenance và trạng thái tham chiếu |
| src_python/ttl_db_batch.py | Readonly iterator, ZIP, manifest và phụ lục nguồn |
| scripts/ingest_ttl_v2_db_sources.py | Backup SQLite trước backfill |
| scripts/export_ttl_v2_from_db.py | CLI scope ttl/dila, thư mục output mới |
| scripts/reload-ttl-db-main.ps1 | Bootstrap/PID/hash guard cho main 5000 |
| scripts/t227_rollback.py | Hoàn tác riêng code/kho nguồn, mặc định dry-run |
| tests/test_t227_db_ttl_export.py, tests/t227-ui-check.cjs | 18 unit và 11 UI |
| tests/test_b25_authority_contract.py | Fixture governance AUDITING/LEGACY tương thích T231 trên DB copy nhất quán |
| package.json | test:t227 nối vào pipeline |
| tasks/T227-db-ttl-v2-export.md, docs/tasktodo.md | Trạng thái DONE |
| docs/reports/T227-db-ttl-export-20261004/ | README, JSON/log, SHA, bootstrap/verify/rollback và UI artifacts |
| docs/sessions/2026-10-04-T227-db-ttl-export.md | Log session |
| data/progress_data.json | Dashboard đã regenerate |

Backup năm file cũ ở data/backups/T227-db-ttl-export-20261004; SQLite backup và import manifest ở source-import/. Không stage/commit file dùng chung trong session này.

## 7. Sai lầm và cách sửa

- SQL UPSERT ban đầu sai quote; đã đổi trạng thái failed sang parameter, unit PASS.
- API template sai cú pháp ban đầu trả 500 vì RDF BadSyntax không phải ValueError; đã kiểm error metadata trước parse và trả 422, unit 17 PASS.
- Fixture unit 17 nhầm tên file active với bad.ttl trong quarantine; sửa thành 0-template.ttl. Pipeline đầu FAIL, lần cuối exit 0.
- Bootstrap bên ngoài helper hai lần bị stale vì app.py đổi trước kill; guard chặn đúng. Chuyển bootstrap vào helper với hash trước/sau.
- Thay tên T226 sang T227 làm đường dependency bị sai; đã trả về T226 python-deps trước restart thật.
- Ảnh QA phát hiện CSS .btn làm nút ZIP hiện trước khi job hoàn tất. Đã sửa rule hidden theo ID và thêm kiểm trạng thái trước/sau, pipeline-delivery đã PASS sau sửa.
- Node REPL reset bindings sau user hi; đã khởi tạo lại. Đọc artifact UI quá sớm dẫn đến chạy lại dù 11 checks vừa hoàn tất; không phải lỗi UI.
- Log PowerShell UTF-16 cần decode đúng. NativeCommandError chứa stderr của unittest không đồng nghĩa test FAIL: kiểm exit và summary thực tế.

- Pipeline-release bị lỗi governance sau T231: fixture cũ dựa vào trạng thái live DILA đã chuyển LEGACY. Giữ test AUDITING deny bằng fixture riêng; thêm LEGACY quote không nâng cờ rights. Không sửa gate hoặc dữ liệu production. Governance 18/18 PASS.
- Backend mất listener trong QA; log không có exception. Đã phục hồi PID6032 sau bootstrap/port guard, không quy kết nguyên nhân chưa rõ.

## 8. Việc chưa xong theo ưu tiên

1. Review bốn source TTL self-teacher; sửa theo chứng cứ T215, exact ID, backup và kiểm DB/API. T227 không tự áp.
2. Identity crosswalk chưa verified: 1.016 hồ sơ xuất còn giữ định danh legacy. Không đoán ID từ tên file.
3. Khóa edition/license artifact; đối chiếu Source Hub/LicenseGate T231 đang do phiên khác cập nhật.
4. Semantic hóa VN events/places/works khi có schema/chứng cứ; hiện dữ liệu đầy đủ còn trong snapshots.
5. Chưa click batch full với token Admin thật trên 8080. Đã kiểm CLI full, worker/auth/download bằng fixture và auth gate UI thật. Chưa xuất toàn bộ 49.361 DILA; CLI hỗ trợ streaming, báo lỗi nếu hồ sơ vượt 500 records liên quan thay vì cắt mất nguồn.

## 9. Lệnh kiểm tra nhanh

~~~powershell
$env:PYTHONPATH='data/backups/T226-ttl-profile-20261003/python-deps;data/backups/T215-fix-sync-20261002/python-deps'
Invoke-RestMethod http://localhost:8080/daoanh/api/admin/ttl_v2/db_stats
Invoke-RestMethod http://localhost:8080/daoanh/api/admin/ttl_v2/from_db/A008431
npm.cmd run test:t227
python -X utf8 scripts/t227_rollback.py --code
python -X utf8 scripts/build_progress_data.py --check-dup-ids
~~~

Đọc export-verification.json, pipeline-delivery.exit, live-api.json, live-ui/ui-result.json và reload-status.json. Full ZIP đã được kiểm; chỉ chạy lại khi code/data thay đổi hoặc có nghi vấn. Gói nằm ở data/ttl_v2/db_exports/T227-db-export-v2-20261004/ttl-v2.zip.

## 10. Ghi chú agent kế tiếp

Load tasktodo, Handoff và task T227. Git từ visjs-app toplevel; cấp task mới sau hai tầng kiểm dup/prose. Nguồn export nằm trong hai bảng v2; không cần đọc XML/TTL file gốc trong luồng export. Không sửa legacy DB chỉ để xuất, không tạo chứng cứ giả để duyệt số đời.

app.py có thể tiếp tục khác bản đã nạp vì session song song; bootstrap/hash guard trước restart. T227 chưa commit; xem git log thật. POST claude-mem 37700 bị fetch failed; tasktodo/session và tasktodo-memory-observation.json giữ trạng thái DONE để retry sau. Việc này không chặn chức năng đã hoàn thành.
