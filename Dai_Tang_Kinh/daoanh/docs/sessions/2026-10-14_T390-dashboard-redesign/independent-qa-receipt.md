# T390 independent QA receipt

## QA độc lập và quyết định commit — 2026-10-14

Root chuyển kết quả Debug và phê chuẩn scoped commit. **18/18 PASS (48.4s) + final snapshot 2/2 PASS (9.4s), tổng 20 checks**; không trình bày như một suite 20 test. Lệnh independent: node node_modules/@playwright/test/cli.js test, config/output riêng tại C:/Users/NAMTHI~1/AppData/Local/Temp/t390-independent-qa-W6rcTb; config lần 1 playwright.config.cjs, lần 2 final-snapshot.config.cjs. Receipt gốc independent-results.json và final-snapshot-results.json được sao nguyên vào session; hash SHA256 lần lượt 32847b70810859498d7a8edca497f673ba335f36dc3e28757fb30dba5d889ec7 và 2ecb304402d5f5c7b089a91cc0df515f0396412d723fca756caa5454ad0b5cd5.

QA xác nhận T3906 + T3588 + 4 probe; final JSON 2 checks riêng. Counts 311=162+34+87+28, risks 50 waiting / 1 SCC / 5 JSON duplicate groups; sáu scalar |, |-, |+, >, >-, >+ fallback về mở task gốc; 375px keyboard/receipt/reload và T358 byte-equivalent. Snapshot kiểm có SHA256 1309242a7d9bdf94631382de9f202a6966dfd6a6be625273ab59209dd6a13cf9.

Common gates vẫn giữ giới hạn: guard PASS; dup/pipeline FAIL 9 ID lịch sử; tester runtime 2/2 ERR_CONNECTION_REFUSED localhost:5000, lint stderr ProgramFiles null bị exit mask. Không chứng nhận full pipeline hoặc production runtime.

**data/progress_data.json không đưa vào commit**: diff có T380 status, T381 record/route/module và git-history ngoài T390. Giữ nguyên snapshot working tree đã regenerate, không stage cả file hoặc sửa tay generated JSON. Task T390 vẫn in_progress chờ Admin nghiệm thu; Debug/root QA scoped đã PASS. Không DB/TTL/ETL mutation.

Passed cases:
- t358-regression.spec.cjs: T358 actual source is integrated; audited report locks every incomplete row
- t358-regression.spec.cjs: DONE requires typed confirmation; cancel/Escape no write; persist only local review
- t358-regression.spec.cjs: changed revision/evidence/prerequisite makes stored review stale
- t358-regression.spec.cjs: readiness fails closed for missing QA/proof, false completion, blocked or ambiguous task
- t358-regression.spec.cjs: untrusted report text and links are inert
- t358-regression.spec.cjs: corrupt or unavailable storage never reports a successful review
- t358-regression.spec.cjs: reload failure closes a pending confirmation and fails closed
- t358-regression.spec.cjs: mobile overflow stays in table; dialog is labelled and keyboard accessible
- t390-independent.spec.cjs: T390 actual full page renders source-derived totals with accessible local charts
- t390-independent.spec.cjs: T390 disjoint statuses and overlapping risks handle dependencies, cycles, duplicates and aliases
- t390-independent.spec.cjs: T390 empty snapshot is zero; invalid/missing snapshot fails closed and retry recovers
- t390-independent.spec.cjs: T390 untrusted new-panel fields and unsafe filenames remain inert
- t390-independent.spec.cjs: T390 mobile full page is contained, keyboard navigable and preserves T358 gate
- t390-independent.spec.cjs: T390 existing API-render event refreshes chart without changing task data or local review
- t390-independent.spec.cjs: independent actual risk values equal separately calculated graph results
- t390-independent.spec.cjs: independent forged summary fields cannot override task-derived chart
- t390-independent.spec.cjs: independent all six YAML scalar markers render source fallback
- t390-independent.spec.cjs: independent 375px full dashboard preserves typed local T358 review receipt
- t390-independent.spec.cjs: T390 actual full page renders source-derived totals with accessible local charts
- t390-independent.spec.cjs: independent actual risk values equal separately calculated graph results
