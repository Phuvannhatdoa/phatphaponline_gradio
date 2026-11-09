---
id: T390
former_ids: []
title: "T390: Dashboard Redesign — Restore files + Playwright fixtures"
module: Dashboard
priority: high
status: done
owner: code
created: 2026-10-14
updated: 2026-10-15
depends_on: [T358]
done_when: |
  KPI/chart đếm từ tasks[] và ghi rõ snapshot, trạng thái khác không bị mất.
  Priority/blocked/in_progress, dependencies và owner có nguồn; thiếu không tự suy.
  T358/DONE local-review giữ nguyên; không ghi task/data production.
  Focused UI + T358 regression PASS; responsive/keyboard/XSS/empty/failure được kiểm.
  Debug/root QA độc lập và Admin nghiệm thu; common gate báo đúng giới hạn.
undone_reason: "Focused 14/14 và independent 18/18 + 2/2 PASS; Admin đã nghiệm thu (Decision 7, 2026-10-15)."
undone_action: "Đã DONE. Common gates (dup:ids 9 ID lịch sử, tester runtime localhost:5000) là giới hạn đã biết, ngoài scope T390 — không block DONE của task này."
---

# T390 — Dashboard Redesign — Restore files + Playwright fixtures

Root giao T390 sau kiểm hai tầng 2026-10-14: ID chưa có file/prose; dup:ids có 9 xung đột lịch sử ngoài scope.

**Hai phần việc:**
1. **Restore (commit 85d5075)** — commit T381 trước đó đã làm rơi 33 file của T390 dashboard
   redesign (gốc từ commit 35f497b): `dashboard_process.html`, `process_overview.css/js`,
   tài liệu/session logs, và `t390-dashboard-redesign.spec.js`. Khôi phục đủ 33 file, giữ
   nguyên nội dung gốc, status giữ `in_progress` chờ Admin QA.
2. **Playwright fixtures (commit 47671bc)** — bổ sung fixture cho dữ liệu đã gitignore để
   test chạy được trên máy không có `data/lineage.db` thật; 14/14 test pass.

## Scope

Dashboard HTML + process_overview.js/.css; tests/t390-dashboard-redesign.spec.js; tài liệu/tasktodo/session/Handoff; regenerate data/progress_data.json bằng generator hiện có. Giữ các sửa từ phiên khác và toàn bộ nội dung legacy/T358. Không DB/TTL/ETL/API mutation hoặc commit.

## Thực thi và bằng chứng

- Tổng quan đầu trang, KPI, donut SVG và risk bars native; font/icon fallback local, không CDN.
- Đếm mỗi record tasks[] theo status; status khác có bucket riêng. Không dùng checklist làm chứng nhận QA.
- Risk groups có thể giao nhau: blocked, chưa done chờ dependency không tồn tại/trùng/chưa done/format chưa đọc, SCC cycles, duplicated ID trong JSON. Không đồng nhất với 9 duplicate ID của repo guard.
- Action cards chọn tối đa 5 hồ sơ mỗi nhóm, P0/P1/high/critical; owner thiếu ghi chưa giao, source link allowlist basename, textContent.
- Nguồn local progress JSON và event render API hiện có; không write hay storage mới. T358 vẫn có gate dev/typed confirmation/local admin_reviewed.

## Test và rollback

Fixture full-page route/mock HTTP toàn bộ; không chạy app.py/DB. Kiểm tổng chart, unknown/duplicate/cycle/alias, zero vs missing, unsafe text/link, mobile overflow/keyboard, T358 regression.

Backup/hash guard tại session before-manifest.json. Trước restore đối chiếu after-manifest; restore chỉ owned patch khi không có drift, giữ tài liệu/logs và WIP khác. Khi root giao commit, revert SHA từ visjs-app root; hiện chưa commit.

[Contract](../docs/T390-dashboard-process-redesign.md) · [Session](../docs/sessions/2026-10-14_T390-dashboard-redesign/README.md) · [Handoff](../docs/Handoff-2026-10-14-T390-dashboard-redesign.md)

## Validation 2026-10-14

Focused T3906/6 + T3588/8 = 14/14 PASS (final2: 1.1m). Generator PASS (311 hồ sơ, done162/blocked28). guard PASS; dup:ids FAIL 9 ID lịch sử, pipeline dừng tại dup (không chạy các bước sau). Source Node syntax PASS. Không suy full pipeline từ focused tests; tester-agent FAIL runtime 2/2 ERR_CONNECTION_REFUSED localhost:5000; lint stderr ProgramFiles null bị exit mask. Log có trong session.

## QA độc lập và quyết định commit — 2026-10-14

Root chuyển kết quả Debug và phê chuẩn scoped commit. **18/18 PASS (48.4s) + final snapshot 2/2 PASS (9.4s), tổng 20 checks**; không trình bày như một suite 20 test. Lệnh independent: node node_modules/@playwright/test/cli.js test, config/output riêng tại C:/Users/NAMTHI~1/AppData/Local/Temp/t390-independent-qa-W6rcTb; config lần 1 playwright.config.cjs, lần 2 final-snapshot.config.cjs. Receipt gốc independent-results.json và final-snapshot-results.json được sao nguyên vào session; hash SHA256 lần lượt 32847b70810859498d7a8edca497f673ba335f36dc3e28757fb30dba5d889ec7 và 2ecb304402d5f5c7b089a91cc0df515f0396412d723fca756caa5454ad0b5cd5.

QA xác nhận T3906 + T3588 + 4 probe; final JSON 2 checks riêng. Counts 311=162+34+87+28, risks 50 waiting / 1 SCC / 5 JSON duplicate groups; sáu scalar |, |-, |+, >, >-, >+ fallback về mở task gốc; 375px keyboard/receipt/reload và T358 byte-equivalent. Snapshot kiểm có SHA256 1309242a7d9bdf94631382de9f202a6966dfd6a6be625273ab59209dd6a13cf9.

Common gates vẫn giữ giới hạn: guard PASS; dup/pipeline FAIL 9 ID lịch sử; tester runtime 2/2 ERR_CONNECTION_REFUSED localhost:5000, lint stderr ProgramFiles null bị exit mask. Không chứng nhận full pipeline hoặc production runtime.

**data/progress_data.json không đưa vào commit**: diff có T380 status, T381 record/route/module và git-history ngoài T390. Giữ nguyên snapshot working tree đã regenerate, không stage cả file hoặc sửa tay generated JSON. Task T390 vẫn in_progress chờ Admin nghiệm thu; Debug/root QA scoped đã PASS. Không DB/TTL/ETL mutation.

## Scoped follow-up — remove endpoint comparison section (2026-10-14)

Admin clarified that “session” meant the live bottom section titled “Đối chiếu endpoints (docs claim vs code thật)”. Removed that section and its endpointTable renderer from dashboard_process.html. Other section IDs/buttons and T358 markup remain identical; the summary endpoint counter still uses existing JSON. No report/generator change is needed: this HTML section is authored directly. Historical backups and progress JSON are unchanged.

Focused Node regression proves the former renderer throws when endpointTable is absent, while the current render succeeds, invokes the other renderers, and parses all five inline scripts. This is scoped renderer/syntax coverage, not a new browser/full-pipeline PASS. Session: docs/sessions/2026-10-14_T390-endpoint-section-removal/README.md; Handoff: docs/Handoff-2026-10-14-T390-remove-endpoint-section.md.
