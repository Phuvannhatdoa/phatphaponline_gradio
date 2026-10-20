---
id: T357
title: VNPA production ETL safety remediation
status: in_progress
doc_status: ready_for_debug_qa
module: Data / ETL Integrity
priority: critical
owner: code
created: 2026-10-11
updated: 2026-10-11
former_ids: [T223]
source_report: docs/Mimo-Flash/T223-VNPA-PRODUCTION-ETL-CONTROLLED-EXECUTION-01.md
related_tasks: [T217, T220, T222, T223, T253]
execution_scope: build-fixture-only
plan_approved_at: "2026-10-11 — docs-phase approval trước build"
build_approved_at: "2026-10-11 — controls/code/fixtures approved; no production migration/apply"
---

# T357 — VNPA production ETL safety remediation

## Mục tiêu

T357 xây safe VNPA ETL: read-only preflight với frozen scoped reference, staging và logical diff, atomic ledger/apply, guarded inverse rollback. Build/fixtures đã PASS27 tests; production migration/apply chưa thực hiện, Debug/root QA pending.

## 1. Mục tiêu, ID và phạm vi được giao

T357 tiếp nhận nhánh **T223 production ETL** để tránh trùng với [T223 phân loại 29 nhóm DILA-ID](T223-dila-id-29-nhom-phan-loai-va-quyet-tach.md). former_ids: [T223] lưu dấu nhánh ETL; không chuyển quyền quyết gộp/tách định danh của task T223. [Báo cáo ETL cũ](../docs/Mimo-Flash/T223-VNPA-PRODUCTION-ETL-CONTROLLED-EXECUTION-01.md) giữ nguyên đường dẫn và chứng cứ 2026-10-04, thêm trạng thái hiện hành/erratum.

**Lượt docs đã giao trước build:** kế hoạch, tài liệu ETL/rollback/SSOT trực tiếp liên quan, tasktodo, Dashboard qua generator, session và Handoff. Không sửa/chạy ETL, không query hoặc sửa DB, không sửa TTL/raw XML, không HTTP/LLM ngoài POST observation cuối phiên. Không stage/commit trước root QA. Code là writer; Debug kiểm độc lập; root QA và điều phối quyền triển khai tiếp.

**Kết quả hiện tại:** safety engine/code đã triển khai và fixtures27/27 PASS; Debug/root QA, production schema/data rehearsal và nghiệm thu dữ liệu chưa thực hiện, task vẫn in_progress. Docs-phase DONE chỉ khi links/frontmatter/guard/dup delta/Dashboard đã kiểm; không gọi đây là production ETL PASS.

## 2. Chứng cứ trước remediation và giới hạn lịch sử

Đọc tĩnh [importer](../scripts/etl_ttl_person_authority.py), SHA256 668d8fde05f6d639985541a11971cf4261fba99cfb06a8bb5d67f8d2188a197d:

| Locator | Phát hiện | Hệ quả cần chữa |
|---|---|---|
| dòng 334–337, 342–369 | Mở writable DB và executescript(SCHEMA) trước preflight; ImportError bị bỏ qua, --skip-preflight không bind manifest | Preflight phải read-only và fail-closed, trước mọi writable connection/DDL |
| dòng 413–420, 522, 565 | DELETE, INSERT, restore curate có ba commit | Không atomic cho toàn run; WAL serializes writers không tạo single transaction hoặc quiescence |
| dòng 428–472, 477–503 | Parse/insert exceptions chỉ in rồi tiếp tục; OR IGNORE tăng n kể cả không insert | Run có thể báo thành công/rowcount khác rows thực ghi |
| dòng 444–460 | Regex khoảng năm và min/max trong note gán birth/death | Đưa thành candidate quarantine; không nâng suy luận thành sinh/tử canonical |
| dòng 392–403, 524–565 | Guard curate hiện tập trung dila_id/status | Mở contract protected rowset/fields và lineage/identity, không chỉ tổng số |

Các số 1.507 authority / 2.013 relations / 453 curated IDs / 1.929 unmanaged relations, test PASS và hash DB trong báo cáo là **historical 2026-10-04**, không refresh ở lượt này. integrity_check + tổng hàng/spot checks không chứng minh toàn rowset bằng nhau. Hash main .db trong WAL không chứng minh 0 write. Lệnh bị cắt stdout và số tổng không chứng minh lần gọi thứ hai chưa ghi; không suy ngược đã hỏng dữ liệu khi chưa có bằng chứng.

## 3. Phase A — preflight read-only, writer policy và scope

- Resolve DB bằng đường dẫn tuyệt đối/canonical; DB thiếu, đường dẫn lệch hoặc input/code hash lệch thì dừng. Không để sqlite3 tự tạo DB rỗng. Đọc URI mode=ro và query_only; dùng SELECT/schema metadata trong snapshot nhất quán. Không gọi helper mở writable connection hoặc tự tạo schema.
- Manifest bind task/run_id, DB path, schema fingerprint, HEAD và code hash, input path/hash/RDF subject, extractor version, managed predicates, source ownership và exact warning set. Thiếu module preflight, parse lỗi, scope không kiểm đủ hoặc warning ngoài allowlist: exit nonzero trước ghi.
- Historical --skip-preflight 04-10 không là quyền bỏ cổng cho run mới. Nếu có ngoại lệ đã được duyệt, acknowledgment phải bind file/hash/code/version/warning/issuer/time/run_id; scope/hash đổi thì invalid. Không chấp nhận blanket skip.
- Một writer cho transaction; liệt kê app/routes/importers có thể ghi và chọn maintenance gate hoặc shared writer mutex được mọi writer tôn trọng. Giữ gate xuyên backup, baseline, apply, verify/rollback; lock timeout hữu hạn, drift thì fail. WAL là cơ chế SQLite, không thay gate hoặc bằng chứng app quiescent. Không tự dừng dịch vụ trong docs-phase.
- Freeze quản lý scope từ nguồn đã xác minh, không dựa tên gần giống. T217/T220/T222 preservation là đầu vào; 29 nhóm định danh của T223 vẫn cần quyết riêng. Không merge person, sửa DILA-ID, owl:sameAs, teacher/số đời hoặc khôi phục alias đã loại theo T212.

## 4. Phase B — staging trước production write

Parse từng TTL thuộc manifest bằng iterator/file-by-file, ghi staging/JSONL trên đĩa và giới hạn buffer; không giữ toàn corpus/graph trong RAM. Không tải full importer chỉ để sửa một hồ sơ. Raw TTL/XML bất biến. Stage không ghi production DB; schema staging riêng phải khai báo rõ, không tự migration production.

Validate toàn bộ stage trước apply: khóa/id deterministic, duplicates theo key nghiệp vụ, subject identity, FK, ownership của child tables, type/calendar/range và preserved fields. Duplicate tương thích được gộp có rule/hash/locator; duplicate mâu thuẫn bị quarantine hoặc dừng, không OR REPLACE/OR IGNORE để che lỗi. Mỗi staged row giữ source_file hash + RDF subject + locator và explicit/inferred classification. Stage lỗi bất kỳ => không mở production write.

## 5. Phase C — logical rowset manifest và diff

Trong một read snapshot dưới writer gate, lấy schema/columns/PK/order và canonical typed values: NULL khác empty, TEXT khác số, bytes được encode rõ. Stream theo stable key, hash từng row rồi aggregate theo thứ tự; lưu counts và before/expected-after diff insert/update/delete theo table/key/field. Không dùng total rows hoặc physical main-file hash thay logical proof.

Manifests tách managed rows và protected rowsets: authority aliases; curated dila_id/status/name/date/identity fields đã xác minh; ngoài-scope events/works/places/relations; canonical decisions; tombstones/aliases T212. Xác định chính xác column/key/predicate từ schema trong build-phase, không đoán cột tồn tại. Schema không hỗ trợ audit/run ledger => báo conflict và xin root giao thiết kế additive riêng; không tự CREATE/ALTER trong apply. Backup SQLite snapshot nhất quán phải đối chiếu logical manifest từ cùng snapshot; backup API không đồng nghĩa checkpoint live WAL.

## 6. Phase D — atomic apply, strict error và rowcount

Một connection, BEGIN IMMEDIATE, DELETE scoped + INSERT validated + preserve curate + kiểm rowset/protected diff + run ledger cùng **một COMMIT cuối**. Helpers nhận connection, không mở connection mới/hidden commits; không executescript/DDL trong transaction apply. Parse/staging đã xong trước lock apply. Baseline/schema/input/code hash được kiểm lại trước mutation; mismatch thì rollback/dừng.

Bất kỳ parse/constraint/rowcount/FK/protected-manifest conflict đều raise và rollback toàn transaction, exit nonzero, không catch-and-continue. Phân biệt attempted/affected/unchanged/rejected; affected phải khớp diff expected ở từng table/key. Không tăng insert count vì execute OR IGNORE trả về mà không insert. Status committed chỉ sau COMMIT thành công và verify contract; lỗi ghi report sau commit phải recover bằng durable run ledger, không chạy lại mutation mù.

## 7. Phase E — provenance, idempotency và dates quarantine

run_id bất biến; ledger ghi task T357, source scope, DB path/schema/hash baseline, input/code/HEAD hash, extractor version, authorization/warning acknowledgment, timestamps, before/after logical manifests và outcome. Filesystem report không thay atomic DB commit marker. Nếu hiện chưa có durable ledger, chốt schema additive trong build plan riêng trước apply, không invent cột hoặc migration ở lượt này.

Cùng run_id + cùng inputs đã committed => 0 mutation và trả outcome cũ. run_id lặp nhưng inputs khác => fail. Run_id mới cùng inputs phải cho cùng semantic rowset, không nhân bản event/relation; delta audit metadata được báo riêng. Chỉ retry trước commit đã xác nhận rollback; trạng thái commit chưa rõ phải reconcile ledger.

**No inferred birth/death:** regex khoảng năm, min/max, tên niên hiệu/năm xuất gia/trùng tu hoặc năm của người khác không gán canonical birth/death. Giữ candidate sidecar: excerpt/locator/hash, extraction rule, date_kind/calendar/range, uncertainty, reason và person identity. TTL typed event giữ source_asserted theo chứng cứ; không tự accepted khi mâu thuẫn. Không xóa date curate vì incoming NULL; cần field-level preservation và conflict review. Teacher/số đời/semantic identity giữ cổng nguồn độc lập theo SUBAGENT-WORKFLOW, ngoài scope approve ETL transport này.

## 8. Phase F — guarded rollback

Trước commit: transaction rollback phục hồi toàn rowset, không phục hồi từng table sau các subcommit. Sau commit: inverse diff theo run_id, key và before/after values/revision, trong một transaction dưới writer gate. CAS current row/field với expected-after; drift thì dừng và đưa conflict review, không đè thay đổi app/session khác. Chỉ xóa row do run tạo khi row vẫn đúng expected; phục hồi scoped deleted rows/key/source chính xác; giữ protected aliases/ngoài-scope. Log rollback run_id và logical manifest.

Full DB restore là phương án cuối: coordinate toàn bộ writers, dừng write, backup trạng thái hiện tại và kiểm scope/authorization riêng; không chép .db sống bỏ qua WAL/SHM. T253 person-import manifest là pattern tham khảo, không gọi --restore-db để chữa TTL importer trong lượt này. [ROLLBACK](../docs/ROLLBACK.md) ghi rollback docs-phase và liên kết contract này.

## 9. Phase G — tests và nghiệm thu build tương lai

| Test bằng temp SQLite/input fixture | Oracle bắt buộc |
|---|---|
| missing DB/preflight import; parse bad; hash/scope/warning drift | Nonzero; không writable connection/schema/data change |
| Fault sau DELETE, từng child insert, preserve, verify và trước COMMIT | Full logical rowset = before, mọi table; kiểm code path thật |
| constraint, duplicate conflict, ignored insert, affected count mismatch | Rollback toàn run; không success vì stdout/tổng rows |
| alias/curated/nonmanaged/tombstone fixtures | Protected values/key sets bằng nhau; không resurrection |
| birth/death ambiguous range/min/max/third-person year | Candidate quarantine; canonical fields không bị suy ra |
| rerun committed run_id; same inputs new run; report I/O failure | 0 repeat mutation / stable semantic rowset / ledger recovery |
| concurrent writer, lock timeout, baseline drift; rollback after drift | Fail an toàn; không mất update khác; scoped CAS rollback |

Không viết tests giả chỉ mô phỏng lại thuật toán mới; instrument actual importer transaction boundaries bằng fault injection trên fixture. Tests hiện có T217/T220/T222 là regression cần giữ và mở contract, số PASS lịch sử không dùng làm PASS hiện tại. Sau build phải targeted tests + read-only dry-run/copy-DB diff/rollback rehearsal + Debug độc lập + root QA; production apply chỉ theo scope được giao tiếp, không tự chạy full ETL.

## 10. Acceptance của lượt docs và bàn giao

- Một task T357 có former_ids:[T223], report cũ task-bound T357; T223 ontology giữ ID/status và quyết định riêng. Two-level check trước cấp ID, exclusive new file, backup/hash-CAS cho docs chung.
- Phases A–G có mục tiêu/scope/chứng cứ/test/rollback và gates đo được; phân rõ approval kế hoạch với thực thi chưa làm.
- tasktodo/SSOT/rollback liên kết đúng; Dashboard chỉ qua build_progress_data.py. Guard/dup/targeted doc checks có output và hạn chế rõ; dup lịch sử không gọi PASS/full pipeline.
- [Session](../docs/sessions/2026-10-11_T357/README.md) và [Handoff](../docs/Handoff-2026-10-11-T357-vnpa-etl-safety.md) lưu file/hash/commands/status DONE/PARTIAL/BLOCKED, backup và việc còn lại. Không DB/TTL/API/ETL apply, không commit ở docs-phase.


## 11. Build 2026-10-11 — fixture-tested, production deferred

Admin/root giao build controls + fixtures; cho phép additive control schema trong code/fixture, không migration/apply production. Importer main đã delegate sang [safe engine](../scripts/t357_vnpa_safe_etl.py), default plan; parser giữ behavior với year/subject validation chặt hơn. Không còn biography regex/min-max gán canonical birth/death. Control schema vnpa_etl_runs/vnpa_etl_changes phải chuẩn bị riêng bằng initialize-controls; command từ chối DB production mặc định/hardlink. Apply không auto-DDL.

Frozen label reference explicit được review là bắt buộc: JSON definition_version=T357-label-reference-v1, reviewed=true, issuer, source_locators và index đúng toàn scope. Engine clone T203.classify globals với authoritative_index đóng băng và scoped_read chỉ đọc input manifest; không gọi corpus scanner hay thay global module. Lần thử đầu phát hiện classifier cũ scan TTL ngoài fixture: đã dừng, không sửa TTL/DB production; bản cô lập có regression monkeypatch authoritative_index→raise và plan/apply vẫn PASS. Không chạy legacy integration/copy production.

Plan stages SQLite/JSONL trên disk, ro/query_only baseline, typed full/protected/managed rowsets, input/code/ref/mapping/schema hashes và source/RDF subjects. Managed membership hash là tổng SHA256 typed rows modulo2^256 kèm count; full/protected hash stream theo PK. accepted count nghĩa validated staged rows, không nâng evidence/identity/date lên accepted học thuật. Exact diff giữ ID/created_at và protected curate; INSERT/UPDATE/DELETE đều affected=1, no OR IGNORE/REPLACE. BEGIN IMMEDIATE duy nhất + một COMMIT gồm business rows và durable inverse ledger. Postcondition so expected managed rowset và protected rowsets; any error rollback. CLI báo committed_artifact_failed exit2 nếu ledger đã commit mà report lỗi, để không reapply mù.

Apply explicit cần acknowledgment issuer/expires_at/run_id/db_path/plan_hash/external_writers_quiesced=true. Cooperative .t357-writer.lock chỉ bảo vệ ETL cùng engine; gate của app writers chưa được tích hợp, vì vậy quiescence là attestation phải kiểm vận hành riêng trước production. Rollback thêm diff_hash từ plan đã review, kiểm toàn ledger hash và per-row CAS trước inverse; drift dừng, giữ unrelated writes. Schema đặc biệt/triggers/columns chưa hỗ trợ sẽ fail-closed, không tự đoán migration.

Tests [test_t357_vnpa_safe_etl.py](../tests/test_t357_vnpa_safe_etl.py):27/27 PASS, bao gồm9fault locations, ignored inserts/control rowcount, protected/unplanned trigger writes, missing preflight/DB/control/ref, exact waiver, rowset/input/schema/mapping drift, frozen corpus isolation, idempotency/replay, inverse tamper và scoped rollback. T217/T220 unit33PASS/12Integration deselected; --help PASS. Full pipeline/tester status đọc [build session](../docs/sessions/2026-10-11_T357-build/README.md), không đổi baseline dup để giả PASS.

Usage fixture only:

~~~powershell
python -B -X utf8 scripts/t357_vnpa_safe_etl.py --mode initialize-controls --db <existing-fixture.db>
python -B -X utf8 scripts/etl_ttl_person_authority.py --db <fixture.db> --ttl-dir <fixture-ttl-dir> --label-reference <reviewed-scoped-reference.json> --out-dir <new-plan-dir>
python -B -X utf8 scripts/t357_vnpa_safe_etl.py --mode apply --db <fixture.db> --out-dir <plan-dir> --authorization <fixture-authorization.json>
python -B -X utf8 scripts/t357_vnpa_safe_etl.py --mode rollback --db <fixture.db> --run-id <run-id> --authorization <fixture-authorization-with-diff-hash.json>
~~~

Debug phát hiện hai lỗi ở snapshot23 tests: rollback trigger ngoài scope vẫn trả success, và generation=-1/self teacher chưa bị chặn. Bản sửa kiểm full untouched logical rowsets của cả5tables và mọi expected-before row sau inverse trước COMMIT; drift/trigger effect làm rollback transaction và trả rollback_blocked. Incoming generation chỉ chấp nhận integer1..200 như safety bound, không xác nhận số đời; existing curated giữ nguyên. Self teacher/disciple bị reject trước RW. Hai regression đúng probe trên fixture PASS trong suite27/27,11.966s; Debug recheck/root QA pending.

Overall in_progress; Debug/root QA pending. Production schema preparation, frozen reference review, writer inventory/quiescence, copy-DB rehearsal and any production run remain unperformed and require next scoped delegation. [Build Handoff](../docs/Handoff-2026-10-11-T357-build.md).

Final Debug blocker: AFTER UPDATE ON vnpa_etl_runs could mutate an outside authority row after the last business-row verification. The authorizer now denies every trigger-origin INSERT/UPDATE/DELETE in both apply and rollback; unsupported trigger writes fail closed. Exact late-ledger apply and rollback regressions PASS in final27 tests (11.966s), with complete fixture business/control/sqlite_sequence rowsets unchanged on rejection. Earlier25-test PASS is a prior snapshot, not final acceptance. Independent recheck/root QA pending.
