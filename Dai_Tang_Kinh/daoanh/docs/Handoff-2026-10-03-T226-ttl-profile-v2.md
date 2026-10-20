# Handoff — 2026-10-03 — T226 TTL học thuật v2

## 1. Bảng thông tin đọc nhanh

| Mục | Trạng thái / kiểm chứng |
|---|---|
| Ngày bàn giao | 2026-10-03 |
| HEAD đã quan sát | `9cdee5650c5d641709a52c34ee0821cfef0671c6` ở lần đọc gần cuối; HEAD đã dịch chuyển do session khác, T226 không tạo commit |
| Phạm vi phiên | Phân tích chuẩn, xây dựng profile/editor/API, roadmap, kiểm thử và audit corpus không apply |
| Build | Application profile 2.0.0; manifest rollback ghi 16 file, bốn file có backup gốc |
| Test | Unit/API/schema/SHACL 26/26; UI preview 14/14 PASS, không có lỗi trang; pipeline sau sửa chạy lại có quyền mạng đã PASS, exit 0, runtime 2/2 |
| Audit hiện tại | **1.038 file, gồm một template; 1.037 hồ sơ hợp lệ về cấu trúc, một lỗi template, 10.541 assertion** — `corpus-current/summary.json` |
| DB | API/CLI T226 chưa apply vào DB; preview dùng connection chỉ đọc; save có xác thực và chỉ lưu staging |
| TTL active | T226 không ghi sửa; hai file đã thay đổi ở workspace dùng chung, có bằng chứng SHA trước/sau riêng |
| Deploy | Main 5000 chưa nạp API v2; PID quan sát 22920, `Stop-Process` bị Windows từ chối với `Access denied` |
| Preview | `http://127.0.0.1:5006/daoanh/admin/monk_ttl_add.html`; PID hiện tại đọc từ `docs/reports/T226-ttl-profile-20261003/preview.pid` |
| Task | `in_progress`: build/test hoàn tất, deployment qua 8080 chờ quyền Administrator/UAC; migration và phát hành theo roadmap |

Bằng chứng tập trung tại [báo cáo kết quả](reports/T226-ttl-profile-20261003/README.md). `valid` trong audit là kết quả kiểm tra cấu trúc/chuyển đổi, không phải chứng nhận sự thật lịch sử.

## 2. Đọc trong 2 phút

Đã nâng cấu trúc từ tiểu sử và vài cạnh truyền thừa thành hồ sơ có URI, nguồn/version, assertion, chứng cứ, trạng thái và thông tin review. Reader giữ DILA XML 2026-09 và dữ liệu CBETA/Marcus local; luồng từ `person.html` giữ snapshot đầy đủ. Chỉ assertion `accepted` mới chiếu thành fact trực tiếp. Tên hiển thị và loại nhân vật dùng để điều hướng không tự trở thành thông tin đã xác minh.

Điểm học thuật cần giữ: DILA cung cấp định danh; CBETA cung cấp chứng cứ văn bản; Marcus cung cấp dữ liệu mạng. Không tự xem mọi cạnh mạng là truyền pháp. Ba URL từ cùng một văn bản hoặc dữ liệu dẫn xuất không được tính thành ba căn cứ độc lập. Số đời không được tự cộng từ đời thầy hoặc đổi hệ đếm bằng công thức.

Audit ban đầu phát hiện hai cạnh `hasDisciple` tự nối. SHA hai file đã thay đổi trong workspace dùng chung; audit hiện tại không còn hai cạnh đó và chỉ còn lỗi template. T226 không sửa TTL active, không suy đoán tác nhân thay đổi và không xác nhận rằng quan hệ thay thế đúng về lịch sử.

Ba việc Admin cần xử lý tiếp:

1. Xem form preview và cho phép quyền Administrator/UAC để nạp lại main; sau đó kiểm tra UI/API qua 8080.
2. Chốt URI/resolver của dự án, danh mục nguồn và quyền từng artifact. DB hiện có 14 nguồn, chưa phải 25 nguồn đã được xác minh tích hợp.
3. Chốt quy trình đối chiếu định danh và migration staging trước apply; không chuyển đổi hàng loạt trực tiếp vào DB chỉ vì kiểm tra cấu trúc đạt.

## 3. Đề xuất và phần đã xây dựng

| Vấn đề | Cách sửa / bằng chứng | Kết quả và giới hạn |
|---|---|---|
| URI `ex:`/`bkg:` legacy | URI HTTP của dự án, prefix đúng; reader RDF giữ nguyên raw Turtle | 1.037 hồ sơ qua audit hiện tại; triple chưa ánh xạ còn trong `originalTurtle` |
| Nguồn bị gom vào ghi chú tự do | `SourceRecord`, RDF statement/PROV và snapshot XML/JSON | A000885: 45 mục nhắc đến trong CBETA, một crosswalk Marcus, 34 cạnh mạng gốc; chưa chuẩn hóa mọi trường chuyên ngành |
| Tự tính đời, mặc định giới tính/founder | Form v2 không gọi generation ETL; thông tin chưa rõ có thể để trống; số đời `accepted` cần quy ước, lập luận và ít nhất ba gốc chứng cứ độc lập | Unit tests kiểm tra ba gốc/mirror, số đời, tự nối, cycle và trạng thái |
| Luồng Tạo TTL từ trang person | Giữ contract sessionStorage v1 và snapshot `person`/`dila`/`vi`/`bio_zh` | UI kiểm tra luồng chuyển dữ liệu; số đời fixture 999 giữ trạng thái `legacy_unverified`, không cộng 37 |
| Nhầm cạnh mạng với truyền pháp | Cạnh Marcus nguyên bản nằm trong snapshot; mapping candidate giữ trạng thái draft | Unit test không tự tạo claim thầy truyền pháp từ mạng local |
| Quyền chia sẻ do client tự khai | Cổng public kiểm registry, version, license và redistribution | Cả 14 nguồn kiểm kê chưa xác minh license; chưa mở public export, không tự sửa metadata DB |
| Xung đột output test trên Windows | Runner có thư mục riêng; ảnh dùng `testInfo.outputPath` | Pipeline chạy đến runtime 2/2; không xóa kết quả của session khác |
| Process main cần quyền khác | `reload-ttl-v2-main.ps1` có guard port/API/process, encoding phù hợp PowerShell 5 | Kiểm cú pháp đạt; chưa triển khai vì cần quyền Administrator/UAC |

Application profile là thiết kế của dự án dựa trên các chuẩn đã đối chiếu, không phải tuyên bố đạt toàn bộ CIDOC CRM hay một “chuẩn Phật giáo quốc tế” duy nhất. Resource chuyên biệt cho event/place/work/review/counting scheme, citation selector và HTTP resolver còn theo [roadmap](reports/T226-academic-ttl-roadmap.md).

## 4. Cảnh báo bắt buộc

- **Không ghi đè TTL legacy, không chạy full ETL tính đời, không nâng số đời thiếu ít nhất ba căn cứ độc lập và quy ước đếm rõ.** Endpoint legacy `/daoanh/api/admin/run_etl_gen` còn tồn tại; form v2 không gọi endpoint này. Không dùng nó cho migration mới.
- Hai lỗi `hasDisciple` tự nối là kết quả **audit ban đầu**, không còn là lỗi hiện hành trong `corpus-current`. Không quy việc sửa chúng cho T226. Xem `shared-workspace-ttl-diff.json` và kiểm SHA hiện tại trước apply; thay đổi cấu trúc không xác minh quan hệ lịch sử.
- Main 5000 chạy với quyền khác. `require_escalated` của agent không đồng nghĩa Windows Administrator. Lỗi đang gặp là OS `Access denied`, không phải auto-review rejection. Không dừng gateway/auth hoặc mọi process Python.
- Preview 5006 là server kiểm tra tạm. Storage và session khác origin 8080; save vẫn cần session Admin hợp lệ. Không dùng token fixture để thao tác production.
- Schema/SHACL và các semantic gate không chứng minh danh tính hoặc sự độc lập học thuật của chứng cứ. Public release còn cần review quyền theo artifact và khả năng phối hợp license.
- DILA đang nạp từ artifact local 2026-09; web có 2026-10. Không trộn `source_version` DB 2026.03 với artifact 2026-09 hoặc gọi đây là dữ liệu DILA mới nhất.
- URI mới chưa có HTTP resolver. Global crosswalk, lịch sử merge/split và quyền từng artifact phải hoàn thiện trước apply/release. Không tự gộp các URI legacy.
- Lần đọc git gần cuối từ top-level ghi nhận `app.py` có trạng thái `MM` và các file v2 mới chưa được track. Không stage hoặc revert phần WIP chung; trạng thái git không thay thế manifest checksum.
- TTL thường không được git track; giữ backup theo file. Workspace có WIP/commit song song: git chỉ chạy từ top-level `visjs-app`, không bulk add hoặc restore backup khi hash khác manifest.
- Runtime PlaceVN không tìm thấy nút “Mapping Tên Việt”, nên nhánh click đó chưa được kiểm tra. Không dùng hai runtime test này để tuyên bố mọi UI hoạt động; TTL v2 có bộ kiểm tra riêng.
- Audit T166 còn một cảnh báo baseline về credential trong code. Không công bố giá trị credential hoặc sửa cấu hình credential ngoài phạm vi T226.

## 5. Lệnh revert từng phần

| Phần | Lệnh / điều kiện | Mất dữ liệu? |
|---|---|---|
| Code/editor/schema/test infrastructure | Chạy `python -X utf8 scripts/t226_rollback.py`; chỉ thêm `--apply` nếu guard đạt và danh sách đúng | Không restore DB/TTL; bốn file gốc phục hồi, 12 file mới của manifest được xóa riêng; staging giữ nguyên |
| File có WIP mới | Guard phải dừng; review diff và chỉ hoàn tác hunks T226 | Tránh ghi đè WIP của session khác |
| Main đã deploy | Sau rollback, nạp lại main bằng quyền Admin theo script restart phù hợp | Không restore DB |
| Draft revision | Giữ nguyên, chọn revision cần dùng | Không |
| Batch migration | Chưa apply; không có DB revert/DDL của T226 | Không |

Checksum và backup nằm trong `docs/reports/T226-ttl-profile-20261003/rollback-manifest.json`. Không xóa Handoff hoặc báo cáo lịch sử khi revert. Cập nhật task/docs/Dashboard sau khi hoàn tác. Chưa tạo commit riêng cho phiên này; tra lịch sử hiện tại bằng git log tại top-level.

## 6. Bảng file tạo/sửa

| File/nhóm | Vai trò |
|---|---|
| `app.py` | Đăng ký Blueprint bổ sung |
| `api_ttl_profile_v2.py` | schema/from_dila/local_sources/import/render/validate/save |
| `src_python/ttl_profile_v2.py` | Contract, semantic gate, RDF renderer/parser |
| `admin/monk_ttl_add.html`, `admin/ttl-profile-v2.js` | Form mới, thẻ chứng cứ và chuyển snapshot từ trang person |
| `ontology/ttl-profile-v2/schema.json`, `ontology.ttl`, `shapes.ttl` | Contract, vocabulary và ràng buộc RDF |
| `scripts/migrate_ttl_profile_v2.py` | Audit/stage legacy từng file; chưa apply |
| `scripts/reload-ttl-v2-main.ps1` | Script nạp main có guard; chờ quyền phù hợp |
| `scripts/t226_rollback.py` | Hoàn tác theo checksum manifest, mặc định dry-run |
| `scripts/run-runtime-tests.cjs`, `tests/e2e-runtime.spec.js`, `package.json` | Output riêng và nối `test:t226` vào pipeline |
| `tests/test_t226_ttl_profile.py`, `tests/t226-ui-check.cjs` | Kiểm unit/API/schema/SHACL và UI |
| `requirements-ttl-v2-dev.txt` | Pin công cụ validation cho môi trường test riêng |
| `tasks/T226-academic-ttl-profile-v2.md` | Kế hoạch trước build và trạng thái deployment còn chờ |
| `docs/reports/T226-academic-ttl-roadmap.md` | Phân tích học thuật và roadmap P0–P6 |
| `docs/reports/T226-ttl-profile-20261003/` | Logs, kiểm kê nguồn, mẫu nội bộ, audit manifests và rollback |
| `docs/tasktodo.md`, `docs/ROLLBACK.md`, `docs/sessions/`, `data/progress_data.json` | Bàn giao phiên và Dashboard |

`admin/person-ttl-draft.js` được backup nhưng không sửa. T226 không cần đưa corpus TTL hoặc DB vào git để thực hiện thay đổi này. Danh sách code rollback chính xác nằm trong manifest, không suy từ toàn bộ trạng thái git của workspace dùng chung.

## 7. Sai lầm tự mình làm và bài học

- Backtick/triple quote lồng trong JS orchestration gây `SyntaxError`; sửa bằng structured JSON string hoặc `apply_patch`. Không in toàn bộ `app.py` vì code baseline có credential.
- `Copy-Item` trả exit 0 nhưng file đích vẫn là HTML cũ: đã kiểm chứng thao tác copy không áp dụng. Sửa bằng `write_bytes`, kiểm byte equality và hash.
- UI test chờ status/200 ms trước khi response render hoàn tất nên báo fail sai. Sửa bằng chờ response trực tiếp; kiểm thử sau đó đạt yêu cầu.
- Chỉ tách `.last-run.json` chưa đủ vì ảnh output cũ cũng bị Windows từ chối ghi. Chuyển screenshot sang `testInfo.outputPath`; pipeline chạy đạt.
- PowerShell 5 đọc UTF-8 không BOM làm script có ký tự Unicode bị parse sai. Thêm UTF-8 BOM và kiểm bằng `Parser.ParseFile`.
- Không đồng nhất nhãn điều hướng hoặc type của UI với fact `accepted`. Đã bỏ việc chiếu mặc định Monastic/CRM E21 Person; phân loại từ nguồn là assertion chờ review.
- Review phát hiện `owl:sameAs` có thể nhận object literal, chưa phù hợp ý nghĩa đồng nhất thực thể. Đã bổ sung điều kiện object phải là IRI ở validator và SHACL; unit 26/26 và UI 14/14 sau sửa đã PASS.
- Review phát hiện nạp lại nguồn có thể ghi mất metadata của assertion/source đã chỉnh. Đã chặn nạp lại DILA sau khi nạp; CBETA/Marcus chỉ bổ sung ID mới và giữ nguyên metadata cũ. Bộ regression sau sửa đã PASS; log UI ở `ui-review-fixes.log`.
- Pipeline sau review gặp `ERR_NETWORK_ACCESS_DENIED` khi PlaceVN tải font/Tailwind/CDN: runtime một test fail, một test pass. Đây là giới hạn môi trường; không sửa code để né kiểm thử. Cả pipeline được chạy lại với quyền truy cập mạng đọc; kết quả ở `pipeline-review-fixes-network.log` đã xác nhận exit 0, runtime 2/2 PASS.
- Bản nháp báo cáo từng trình bày hai lỗi tự nối ban đầu như lỗi hiện tại, rồi nối thêm cập nhật ở cuối. Đã thay bằng một trạng thái hiện tại thống nhất và giữ số đo ban đầu trong mục lịch sử audit riêng.

## 8. Việc chưa xong theo ưu tiên

1. **Deployment:** cần quyền Administrator/UAC để nạp main 5000. Sau đó kiểm API/schema và UI qua 8080, ghi bằng chứng triển khai; chưa đánh dấu T226 hoàn thành.
2. **Catalog và quyền:** chốt URI/resolver, danh mục 25 nguồn Admin nhắc tới và quyền từng artifact. 14 nguồn trong DB không đồng nghĩa 25 nguồn đã tích hợp.
3. **Định danh:** đối chiếu global crosswalk DILA/legacy URI, các collision/alias và lịch sử merge/split trước migration.
4. **Template:** giữ `0-template.ttl` ngoài tập hồ sơ sẵn sàng nhập. Hai lỗi tự nối ban đầu đã hết trong audit hiện tại; không mở lại việc sửa nếu chưa có phát hiện mới.
5. **Migration:** stage corpus, xây importer v2 có scope TTL, snapshot DB, đối chiếu API/cycle toàn corpus và diễn tập rollback. CLI hiện mới audit/stage, chưa apply.
6. **Hoàn thiện học thuật/xuất bản:** event/date/place/work/review/counting scheme/selector; adapter incremental; FAIR/DCAT release, quyền chia sẻ, DOI và kiểm thử bên thứ ba.

Roadmap P0–P6 có deliverable và acceptance criteria. Không tự cấp hàng loạt ID task mới khi chưa kiểm tra hai tầng theo AGENTS.

## 9. Lệnh kiểm tra nhanh

Chạy tại thư mục `daoanh`; mọi lệnh git riêng phải chạy từ `visjs-app`:

~~~powershell
$env:PYTHONPATH='data/backups/T226-ttl-profile-20261003/python-deps;data/backups/T215-fix-sync-20261002/python-deps'
npm run test:t226
node tests/t226-ui-check.cjs
python -X utf8 scripts/t226_rollback.py
npm run dup:ids
~~~

Đọc `corpus-current/summary.json`, `shared-workspace-ttl-diff.json` và `ui-result.json` để đối chiếu số đo hiện tại. Pipeline đầy đủ là `npm run pipeline`. `pipeline-review-fixes.log` ghi lần fail ở runtime do CDN bị môi trường chặn; lần chạy lại toàn bộ có quyền mạng đã đạt exit 0 ở `pipeline-review-fixes-network.log`. Bản trước review đạt exit 0 ở `pipeline-complete.log`; không dùng kết quả cũ thay cho xác nhận lần chạy mới. Log PowerShell gốc có thể là UTF-16LE; dùng bản UTF-8 nếu đã có. Không suy kết quả từ log bị đọc sai encoding.

## 10. Ghi chú cho agent kế tiếp

Đọc roadmap, task và README báo cáo trước. Kiểm tra HEAD/status từ top-level `visjs-app`, đọc manifest và hash file trước mọi edit/revert. Không commit WIP của session khác. Khi đã có quyền phù hợp, dùng script reload có guard chỉ cho main 5000, kiểm `GET /daoanh/api/admin/ttl_v2/schema` qua 8080 và chạy UI với `T226_UI_BASE_URL=http://localhost:8080`. Save phải dùng session Admin thật và vẫn chỉ vào staging. Cập nhật tasktodo/Handoff/memory/Dashboard sau deployment.

Nếu thiếu artifact ZIP, version hoặc license, giữ trạng thái draft; không đoán hoặc tự activate nguồn/public export. Snapshot bảo toàn record không đồng nghĩa tất cả trường đã được chuẩn hóa ngữ nghĩa. Không chuyển quan hệ mạng thành truyền pháp và không tính số đời tự động.

Dùng `corpus-current` làm số đo hiện tại; audit ban đầu chỉ là lịch sử phát hiện. Kiểm lại SHA trước migration vì corpus có thể tiếp tục thay đổi trong workspace chung. Các giai đoạn P1–P6 vẫn còn, không được xem là đã hoàn thành bởi bản editor v2 hiện tại.


### Xác minh bổ sung ngày 2026-10-04

Admin xác nhận đã tự xóa cạnh `hasDisciple` trỏ về chính mình trong `TS-Hung-Duong-Hien.ttl` và `TS-Thach-Suong-Khanh-Chu.ttl`. Kiểm tra RDF lại: cả hai file parse được, 0 cạnh tự nối `hasTeacher`/`hasDisciple`; SHA khớp lần audit hiện tại. Bằng chứng: `docs/reports/T226-ttl-profile-20261003/admin-self-edge-removal-verified.json` (đường dẫn từ daoanh). Đây là xác minh lỗi tự nối; chưa chứng nhận toàn bộ quan hệ lịch sử. Pipeline sau review đã PASS với quyền mạng (exit 0), unit 26/26, UI 14/14; main bootstrap cũng PASS.
