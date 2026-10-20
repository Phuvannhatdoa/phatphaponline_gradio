# Handoff — 2026-10-05 — T233 dùng gói Codex

## 1. Bảng thông tin đọc nhanh

| Mục | Trạng thái đã kiểm tra |
|---|---|
| Ngày | 2026-10-05, Asia/Bangkok |
| HEAD quan sát | 3bedc6c9ac09d3e530138357f9d40a6745dcc970; HEAD của worktree dùng chung có thể tiếp tục đổi |
| Task | T233 in_progress; chuyển Batch API sang Codex đăng nhập ChatGPT theo yêu cầu Admin |
| Kiểm tra | T233 unit26/26; rollback fixture3/3; UI exit0, không có pageerror; pipeline exit0, governance18/18, runtime2/2 |
| Chất lượng dữ liệu | Compliance còn hai metric FAIL: claims_assertion_level và conflicts_resolved |
| DB Codex | Snapshot08:00 Bangkok:800/48.673 ID đã xử lý,47needs_review; runner tiếp tục chạy nền |
| Dữ liệu gốc | Code Codex không sửa TTL, people, tên chuẩn, Gemini, quan hệ hay số đời |
| Shared DB | Hai people.name_vi thay đổi và Gemini tiếp tục tăng so với backup; bốn bảng VNPA/quan hệ/số đời giữ hash |
| Backend | Yêu cầu Windows RunAs để reload đã bị hủy; chưa xác nhận API subscription trên server live |
| Git | Không stage/commit trong phiên này; mọi lệnh git đọc chạy tại visjs-app |

## 2. Đọc trong 2 phút

Admin xác nhận không dùng API trả phí, chỉ có Codex và Claude Cloud Session. Máy đã có codex-cli0.159.2 và login status trả Logged in using ChatGPT. Phép thử thật với gpt-6.1-sol xử lý32ID thành công. Job tiếp theo chia48.641ID còn lại thành191nhóm, tối đa256ID/nhóm; đã nhập nhóm0,1,2, tổng800ID ở snapshot08:00 Bangkok. Audit0 unknown IDs/0 stale input/0 bad provenance. Runner hidden tiếp tục chạy, kết quả lưu sau từng nhóm. Khi lỗi hoặc hết hạn mức gói, dừng để resume, không chuyển sang API.

Ba bước tiếp: theo dõi runner/quota; Admin nạp main backend bằng quyền Windows để kích hoạt controls mới; khi đủ48.673ID, đối soát mọi request/hash và review các tên cần kiểm. Không đóng T233 chỉ vì đã có full manifest. [Report](reports/T233-codex-session-20261005/README.md).

## 3. Vấn đề, cách sửa, bằng chứng và kết quả

**Nguồn truy cập:** cách Batch API ngày04/10 không phù hợp với quyền truy cập Admin. Đã thêm scripts/codex_namevi_session.py. Runner kiểm tra login ChatGPT, bỏ khóa API khỏi child environment, bỏ user config và bắt forced_login_method=chatgpt. Dùng sandbox read-only, JSON schema và output file; không trích auth.json/token. CLI version, model_requested, thread ID và SHA artifact được lưu. probe-status.json exit0; first-group.exit0; session-full.out.log xác nhận nhóm1 nhập thêm256ID.

**Nhập DB:** ingest_session dùng chung kiểm tra ID/chữ Hán/input hash và giao dịch của engine cũ. Thiếu/trùng/lạ ID hoặc chữ Hán đổi thì từ chối cả nhóm. Nguồn đổi lúc nhập thì rollback cả nhóm. Mỗi gợi ý có before/after revision; uncertain/không Hán là needs_review. Không tạo Responses API giả để nhập tên từ CLI. Unit26/26 xác nhận auth, provenance, hash, idempotency, stale source và giữ canonical.

**Admin UI/API:** cột Codex vẫn nằm ngay sau DILA name_vi, giữ Gemini và các chức năng cũ. Controls mới: chuẩn bị, chạy/tiếp tục bằng Codex, dừng sau nhóm hiện tại, tải lại. API quản lý folder/job và cần Admin session. Paid submit/collect trả409, kể cả khi môi trường có API key. UI test kiểm phân trang, linkID, hơn200row hydration và XSS textContent. Tên Codex trong browser test là fixture, không được ghi DB thật. Bootstrap code mới PASS; UI fixture PASS không chứng minh backend live đã reload.

**Hoàn tác:** scripts/rollback_codex_session.py dry-run mẫu32PASS và fixture3/3PASS. Chỉ khôi phục/xóa tên của đúngrun, chặn nếu row đã được sửa sau đó hoặc run còn chạy. Giữ revision audit và các bảng nguồn. Manifest rollback chung ngày04/10 nay phải chặn vì Codex đã có dữ liệu mới; không reseal để bỏ guard.

**T232:** engine9hệ, form TTL và panel cây đã triển khai; unit20/20, UI thực và pipeline PASS. Mốc vẫn là dự kiến nếu chưa đủ ba nguồn độc lập. Nguyên Thiều DILA có nhiều đường khác số nên conflict. Không gán A000662 cho Minh Hải Pháp Bảo Chúc Thánh. Duyệt mốc, xác minh truyền pháp và chạy toàn corpus còn tiếp.

## 4. Cảnh báo bắt buộc

- **Không gọi API trả phí hay yêu cầu OPENAI_API_KEY.** Runner dùng hạn mức Codex hiện có; không hứa gói có hạn mức vô tận. Quota/lỗi → blocked_session, giữ tiến độ để resume.
- **Không restore toàn lineage.db.** Gemini đã tăng125→24.625 ở lúc đo. people.name_vi đổi đúng hairow: A001411 Vô Trước→Khắc Cần, A002125 Lệnh Tuân→Linh Tuân. Các trường people khác không đổi ở lần đối soát. Báo cáo đọc này chưa quy được writer; SQL Codex không ghi people. Bốn bảng VNPA, VNrelations, lineage_edge_assertions, person_gen_computed còn khớp backup.
- TTL bị Git ignore; giữ file-level backups. Phiên này không sửa TTL local.
- Git root là visjs-app. HEAD di chuyển do phiên khác; không add cả cây hoặc stage WIP ngoài phạm vi.
- Windows RunAs trả The operation was canceled by the user. Đây không phải auto-review rejection. Không lặp UAC hay kill main khi chưa xác minh PID. Helper yêu cầu Administrator và có bootstrap/app.py-SHA/PID guard.
- OS lock ngăn hai runner cùngjob. Khi runner đang chạy, session-summary.json có thể vẫn là summary của lượt trước; đọc DBjob/log/PID để biết trạng thái hiện tại.

## 5. Lệnh hoàn tác và phạm vi mất dữ liệu

Chạy tại daoanh, mặc định chỉ dry-run:

```powershell
python -B -X utf8 scripts/rollback_codex_session.py --run cb3c56daeb984032860e7aeadab7fd58
# Muốn áp dụng mới thêm --apply, sau khi dry-run PASS.
# Full run cần dừng nhẹ và chờ nhóm hiện tại xong trước:
Set-Content -LiteralPath data/codex_names/23300000000000000000000000000002/stop-requested -Value 'Admin pause'
python -B -X utf8 scripts/rollback_codex_session.py --run 39836c390adf4e9993649eacca7a546c
```

| Phần | Mất dữ liệu? |
|---|---|
| Codex run rollback | Xóa/khôi phục gợi ý đúngrun; giữ revision audit; chặn nếu có sửa saurun |
| DILA/TTL/Gemini/quan hệ/số đời | Không bị script rollback sửa |
| Backup code05/10 | Giữ để đối chiếu; không blind restore code API trả phí cũ, trái chỉ thị Admin |
| Whole-feature rollback04/10 | Guard chặn khi bảng/code đổi; không reseal hay restore toànDB |

Chưa áp rollback thật lần nào. Run đã rollback không được resume; chuẩn bị job mới nếu cần.

## 6. Bảng file tạo/sửa

| File | Vai trò |
|---|---|
| src_python/codex_namevi.py | Session metadata, ingest_session, persistence nguyên tử, nhóm256 |
| scripts/codex_namevi_session.py | Auth/env guard, schema, runner tuần tự, pause/resume, OS lock |
| scripts/codex_namevi_batch.py | Chặn paid API; giữ metadata cũ |
| api_codex_namevi.py | Subscription status, managed run/pause, paid409 |
| admin/codex-namevi.js, admin/namevimap.html | Controls gói Codex, giữ vị trí cột và chức năng cũ |
| tests/test_t233_codex_namevi.py |26tests, tám kiểm tra session mới |
| scripts/rollback_codex_session.py | Hoàn tác theo row/revision, có guard |
| scripts/test-name-generation-ui.cjs | Hợp đồng UI mới, không ghi fixture vào DB |
| scripts/reload-codex-session-main.ps1 | Helper reload có guard; chưa chạy được do Windows |
| docs/tasktodo.md, tasks/T233-codex-han-viet-names.md, docs/ROLLBACK.md | Kế hoạch và trạng thái subscription-only |
| data/progress_data.json | Dashboard build exit0,152task |
| docs/reports/T233-codex-session-20261005/* | Output thật, provenance, unit/UI/pipeline/DBdiff/logs |
| docs/sessions/2026-10-05_T233-codex-session.md | Trạng thái để nối tiếp |
| data/backups/T233-codex-session-20261005/* | Backup file/hash và bằng chứng trước sửa |

## 7. Sai lầm và bài học

Cách dựng Batch API ngày04/10 chưa đúng nguồn truy cập Admin. Đã sửa theo chỉ thị05/10; không nhầm hạn mức ChatGPT/Codex với API credit.

Lần đầu chạy lại DB verifier dùng path report04/10, làm ghi đè historical JSON. Đã lưu output mới vào05/10 và khôi phục JSON cũ từ backup trước lượt chạy. Lần sau phải đổi report path trước khi chạy.

Không được chứng minh an toàn bằng câu toàn DB giữ nguyên trên shared DB. people/Gemini đã đổi trong các lượt khác. Chỉ nêu hash thật, diff từng trường và scope mutationSQL/tests; không quy writer khi chưa có audit.

## 8. Việc chưa xong theo ưu tiên

1. Admin nạp main backend mới bằng quyền Windows; kiểm actual subscription status và paid_api_enabled=false. CLI hiện chạy độc lập, không cần API key.
2. Full runner chưa DONE. Theo dõi quota/lỗi, resume request còn thiếu, đối soát đủID/hash/staleness trước đóngtask.
3. Review needs_review, chữ hiếm và đa âm trước chuẩn hóa tên chính.
4. T232: mốcaccepted, identity Chúc Thánh, cạnh truyền pháp và tính corpus còn mở; hai metric chất lượng dữ liệu cũng chưa đạt.
5. Chưa commit. Review exact diff với HEAD mới, safe staging theo AGENTS, không nuốt WIP của phiên khác.
6. Claude-mem37700 không truy cập được; observationJSON/error đã lưu local, retry khi dịch vụ sẵn sàng.

## 9. Lệnh kiểm tra nhanh

```powershell
python -B -X utf8 scripts/codex_namevi_session.py status
Get-Content docs/reports/T233-codex-session-20261005/session-full.out.log -Tail 5
Get-Content docs/reports/T233-codex-session-20261005/session-full.err.log -Tail 5
python -B -X utf8 -m unittest tests.test_t233_codex_namevi -v
python -B -X utf8 scripts/rollback_codex_session.py --run cb3c56daeb984032860e7aeadab7fd58
npm.cmd run pipeline
```

Pipeline exit0 không có nghĩa hai metric chất lượng dữ liệu đã đạt. Kiểm PIDjob trước khi chạy/resume hoặc hoàn tác.

## 10. Ghi chú agent kế tiếp

Đọc tasktodo/Handoff/report này; kiểm PIDjob và login status, không đọc token/auth.json. Full folder23300000000000000000000000000002, run39836c390adf4e9993649eacca7a546c. Nếu đang chạy thì theo dõi, không launch duplicate. Pause bằng cờ trước rollback/reload. Khi blocked, đọc stderr/events đúnggroup, không API fallback. Chỉ đóngtask khi đủ48.673ID và request/hash được đối soát. UI fixture PASS không thay live backendcheck. Giữ DILA/TTL nguồn và identity A000662 chưa chắc. Không cập nhật memoryfolder trừ Admin yêu cầu; observationlocal là continuation theo AGENTS.
