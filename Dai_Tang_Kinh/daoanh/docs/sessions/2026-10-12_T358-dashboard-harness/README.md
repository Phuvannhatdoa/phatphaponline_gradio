# T358 session — 2026-10-12

Status: BUILD COMPLETE (focused scope), chờ Debug/root QA; task in_progress. HEAD lúc bắt đầu 82bd04876ea0e6046730e040ff820ad430f3f8b1. Không stage/commit, production DB/TTL/ETL write hoặc external API.

## Scope và bằng chứng

Panel 15 rows/0 ready, exact sequences/blockers và local admin-review contract theo [task](../../../tasks/T358-dashboard-harness-agent-execution-panel.md) + [contract](../../T358-dashboard-harness-execution.md). Backup wx/hash trước sửa ở before-manifest.json. Root cấp ID T358 sau hai tầng; dup baseline 9 ID có sẵn. Audit local trước build được phản ánh report snapshot, không corpus/DB scan.

## Commands và outcomes

- exec_command ban đầu trả exit 0/output rỗng nhưng không tạo Playwright artifact: không dùng làm bằng chứng PASS. Chuyển Node child_process.execFile capture stdout/stderr/exit và lưu JSON.
- node --check dashboard/triage_execution.js lần đầu FAIL do escape regex; sửa allowlist segments, node-check-2.json PASS exit 0.
- Focused tests lần 1/2 FAIL, timeout runner; source syntax rồi fixture UTF-8 meta đã sửa. Giữ focused-tests-1/2.json/artifacts cho nguyên nhân, không coi PASS.
- node node_modules/@playwright/test/cli.js test tests/t358-dashboard-harness.spec.js --reporter=list --max-failures=1 --output=docs/sessions/2026-10-12_T358-dashboard-harness/playwright-artifacts-3: **8/8 PASS, exit 0, 43.2s** (focused-tests-3.json).
- Fixture route/mock toàn bộ HTTP; GET only, không /api/ request; namespace riêng, zero task/prod mutation. Screenshot mobile là ready fixture.
- Tasktodo CAS phát hiện concurrent T366 block: hash đầu 33b090f7… → c893a139…. Backup live mới tasktodo.concurrent-T366.before.txt; giữ entry T366, chỉ thêm T358. Không sửa T366.

Validation generator/guard/dup/tester/pipeline sẽ được append đúng output sau chạy. QA độc lập chưa hoàn tất khi ghi snapshot này.

## Tiếp nối và rollback

Root giao Debug QA source/report/test; không mở DONE cho task triage chỉ vì T358 UI pass. Rollback theo manifest/hash guard, giữ WIP ngoài scope. Handoff 10 mục lưu riêng; observation §0 thử timeout ngắn khi bàn giao, ghi kết quả thật.

## Validation hiện hành

- Generator exit 0, generated_at 2026-10-12T16:35:58; 291 task (160 done, 26 in_progress, 77 pending, 28 blocked). T358 đúng 1 record/in_progress; selected task status không bị đổi. Artifact generator.json. Đây là snapshot generated hiện tại, không 277 row historical trước build.
- npm.cmd run pipeline exit 1: guard PASS, dup:ids FAIL 9 ID cũ T158/T168/T169/T170/T171/T177/T206/T215/T274; T358 không trùng. Bước honesty/H3/DB tests sau dup chưa chạy. pipeline.json giữ output đầy đủ.
- node scripts/tester-agent.mjs exit 1: static lint/test/e2e runner báo PASS; lint stderr có ProgramFiles/LOCALAPPDATA null và package script || exit 0 nên không khẳng định lint sạch. Runtime PlaceVN 1 fail/1 pass (32.8s), CDN ERR_NETWORK_ACCESS_DENIED + L is not defined ngoài scope. tester.json. Không ALL TESTS PASSED, không xin Admin build review.
- Đã xem mobile screenshot fixture 375px: dialog vừa màn hình, chữ rõ, focus input vàng và nút confirm khóa. Panel table được giới hạn 680px, sticky header, scroll region có nhãn cả dòng/cột; chạy lại focused suite trên snapshot final.

## Snapshot cuối để Debug QA

Focused suite trên HTML/CSS final (table height cap/sticky header): **8/8 PASS, exit 0, 24.1s**, focused-tests-final.json. T358 vẫn in_progress, chờ independent QA; không xin Admin review khi gates chung FAIL.

Targeted docs/JSON/links/frontmatter/Handoff 10 mục PASS theo targeted-doc-checks-final.json. Check đầu phát hiện U+FFFD trong shared tasktodo: đối chiếu concurrent before chứng minh count không đổi, block T358 không có U+FFFD, giữ lịch sử ngoài scope; không tuyên bố toàn tasktodo UTF-8 sạch.

Observation §0 POST localhost:37700 timeout 1800ms đã thử, **ECONNREFUSED**, observation.json. Chưa save memory remote; local session là bàn giao. Live localhost:8080 GET và asset statuses ở live-http-get.json; không click DONE live hoặc gọi API ghi.

Memory chỉ dùng định hướng trong audit trước: MEMORY.md:98–104; rollout_summaries/2026-10-02T07-12-23-QnSf-daoanh_t203_ttl_survey_and_model_guidance.md:15–32; rollout id 01a0fb74-ff01-7450-acd3-9fffc8abf70f. Các claim status/source được đọc live riêng; memory không dùng làm bằng chứng PASS hiện hành.

## Shared HEAD drift / commit boundary

HEAD cuối f0025b895b5ffc9c2e62aa3355ddc982558643a8 (T366 commit session khác); git show HEAD filtered T358 paths rỗng. git diff HEAD chỉ còn 6 tracked paths, source/task T358 đã được track trong một commit khác giữa phiên: b46f81b fix: biography không load + AI dịch báo lỗi sai (person.html). Agent Code **không chạy stage/commit** trong T358. Root phải kiểm các commit/session khác và phần patch còn lại, không giả định toàn feature còn untracked. head-drift-note.json có git metadata/line map.

## QA và commit được root giao

2026-10-12: root xác nhận T358 QA PASS, giao commit exact remaining scope. Code không thay source/test sau QA; chỉ ghi kết quả QA và commit boundary trong docs. Temp index tạo bằng git read-tree HEAD, danh sách paths cụ thể, không đổi default index. data/progress_data.json live 291 rows giữ nguyên ngoài index: remaining diff chỉ T366–T371 (6 task) và module/history khác, T358 record đã ở HEAD và giống live. Các video/error-context Playwright giữ local; committed evidence dùng JSON logs và screenshot, không add cả thư mục.
