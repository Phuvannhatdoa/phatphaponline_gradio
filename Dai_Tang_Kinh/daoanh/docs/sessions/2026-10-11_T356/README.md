# Session 2026-10-11 — T356 (former T355), T224 audit contract

**PARTIAL nghiệm thu:** triển khai script/tests/docs/Dashboard đã xong; root QA docs và commit còn pending. Debug PASS script trước rename T355; 13/13 test sau rename T356 PASS. Task T356 giữ in_progress. Không claim full pipeline/Admin build review.

## Mục tiêu, scope và tiêu chí

Audit stdlib + fixture, task T356, sáu tài liệu T224/tasktodo và Dashboard qua generator. DB chỉ đọc; không TTL/raw XML/note/API/ETL/importer/NLP/schema mutation. Một CASE A1>A2>C>B>D>E, một membership mỗi ID, tổng trong cùng read transaction; flags any/founding/dissolved/xref/marker riêng, ref/confidence syntax, baseline55, history/current và schema/command/output manifest.

## Kết quả cuối

Current snapshot [summary](audit-current-t356/summary.json), [manifest](audit-current-t356/manifest.json): **2026-10-11T02:11:48.789914+00:00**, definition t356-t224-legacy-partition-v2. places_dila 59.167 / places 59.161 / events 4.386 / xref 190; buckets A1/A2/C/B/D/E = 249/3.295/85/196/13.353/41.989, membership tổng59.167, đúng một bucket/ID. Source×type cộng độc lập4.386, wikidata155 tách p571146.

Any-event3.544 / founding2.502 / dissolved41; 1.042 place any-event nhưng không founding, 4 dissolved-only ở A1. Marker-without-founding282 qua các bucket, B196 do precedence. Baseline T22 vẫn55 (50 founding+5 era_mention), empty_label_vi0/self_ref0; không trừ totals/sửa lại. Marker candidate/QID syntax/score label không accepted.

Proof: URI mode=ro, query_only1, authorizer chỉ đọc, total_changes0, một read transaction/fetchmany256. Schema SHA699a3374ed0a02ade671ace68cb3cdf3d793856f605c644e9d837431addaec38 chỉ fingerprint schema, không hash toàn DB/WAL. No production mutation. Fixture test write rejection chỉ trên SQLite tạm.

| Artifact | SHA256 |
|---|---|
| Script | a8d7850cb6fdeca8ce135b5aaca4fb2f524f4b6abe4bce7f0d154c4f57930b63 |
| membership.csv | 2d2dee4bfdc8ac4486b8363289c8c0b33161636f612df046cf8096657c929f0e |
| events_audit.csv | c58f68128d9344ec32f13bad79459b6746c72ce3ceb2ceac4566e7901b6491de |
| summary.json | a3aaa61324bc6cb13705cb021fb44df05120741bc1eb85e9ea4f6e22e3b80155 |

Archive T355 v1/v2 ở audit-current/ và audit-current-final/ giữ nguyên timestamp/command/hash. Source trước đổi ID ở *.before-rename.txt; v1 trước qid_property ở script-before-qid-property.txt. Chúng là provenance, không snapshot cuối T356.

## Docs / ownership / drift

G0–G2 T224 done lịch sử, không blocked do SPEC/PROMPT mất; T356 executable tự chứa. G3 deferred. Sửa phép cộng historical thiếu146 p571 và3372/3688=91,43%;≈93% là place A2. Token458.633/8k phải ceil58 trước overhead/output, không một prompt rẻ/quyền LLM. Local DILA evidence có excerpt/locator/version/hash; parser TEI tương lai dùng namespace URI, không prefixns0. QID/name/geo không auto-accept semantic identity hay teacher/số đời. T22/T121/T230/T231 giữ ownership.

Sáu input docs backup/hash trước trong inputs-before.json. tasktodo drift đã backup bản live tasktodo-rebased-before.md, chỉ thay entry T224 và thêm T356, phần ngoài giữ nguyên byte. Backup task T224 đổi .md.txt để guard không nhận nhầm duplicate. Dashboard backup trước sinh, không sửa tay generated file.

## Commands / kết quả / logs

| Lệnh | Kết quả | Log |
|---|---|---|
| python -B -X utf8 -m unittest discover -s tests -p test_t356_t224_readonly_audit.py -v | PASS13/13,2.454s, exit0; CLIhelp/fixture dry-run trong test | 07-unit-after-rename.log |
| python -B -X utf8 scripts/t356_t224_readonly_audit.py --out-dir docs/sessions/2026-10-11_T356/audit-current-t356 | READ_ONLY_AUDIT_PASS, exit0 | 08-audit-after-rename.log |
| npm.cmd run guard | PASS, root visjs-app/no nested .git, exit0 | 10-guard.log |
| npm.cmd run dup:ids | FAIL exit1, chỉ8 historical IDs T158/T168/T169/T170/T171/T177/T206/T215; T224/T356 không duplicate | 09-dup-after-rename.log |
| python -B -X utf8 scripts/build_progress_data.py | exit0,15modules/312endpoints/275tasks/72%; WARN gitlog rỗng/lỗi, timeline không có ở run cuối | 11-dashboard.log |
| git rev-parse HEAD từ visjs-app | 0fa04487e9d808b10652049fc1c0153979b8fc00, snapshot có thể drift | session này |

Hai tầng rename: rg --files tasks -g 'T35*.md' không có T356; rg -n -P --glob '!**/_book/**' '(?<![A-Za-z0-9_-])T35[6-9](?![0-9])' docs/tasktodo.md docs/Mimo-Flash tasks không T356 (chỉT359 kinh văn ởT55). T355 race xuất hiện ở task phiên khác; root giao đổi T356 former_ids[T355], không sửa task kia. Dup trước rename10 gồm8history+backupT224+raceT355, saurename8. No stage/commit. Pipeline/lint/e2e không chạy; không xin Admin build review.

## Sai lầm và giới hạn

JS quoting với backtick SyntaxError trước ghi, đổi sang JSON. rg thiếu-P lỗi lookaround, không coi là no-hit. npm shim lần đầu exit0 rỗng không proof; npm.cmd lấy output thật. Backup .md tạo duplicate giả, đã đổi .txt. T355 đãchecked đầu nhưngrace, đãrecheck/rename. Không sửa duplicate lịch sử/generator ngoài scope hoặc nhận git timeline WARN thành PASS.

## Rollback / việc còn lại

[Handoff](../../Handoff-2026-10-11-T356-t224-audit.md) và after-files.json có mapping/hash trước/sau. Chỉ restore khi live=after_sha256 và backup=before_sha256; dừng nếu drift. Không xóa artifacts mới. Root có thể git revert scoped commit sau QA; không DB restore vì0writes.

Root QA docs/hash/rename, commit scoped còn pending. Observation AGENTS§0 thử POST loopback 37700 với timeout5s: fetch failed, ECONNREFUSED, remote_saved=false; [kết quả local](observation-result.json). Memory quick-pass T224/T355 không hit; không dùng rollout memory cho implementation.
