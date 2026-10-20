---
task: tasks/T390-dashboard-process-executive-redesign.md
---

# T390 — Tổng quan Dashboard Process

Build 2026-10-14. Trang dashboard/dashboard_process.html giữ nội dung legacy và nguyên block/logic T358; thêm hierarchy điều hành bằng process_overview.js/.css. Mọi metric mới là snapshot tài liệu từ progress_data.json, không phải audit production.

## Định nghĩa số liệu

KPI tổng = tasks[].length, đếm record (không giả định ID duy nhất). Status done/in_progress/pending/blocked là bốn nhóm rời nhau; mọi status khác vào other trong donut/legend. Tổng các lát chart bằng tổng record, snapshot rỗng hợp lệ là 0; tải lỗi/malformed không hiển thị 0 thay dữ liệu thiếu.

Risk groups không rời nhau: blocked; task chưa done chờ dependency chưa done/không tồn tại/ambiguous hoặc format chưa đọc; số SCC chu trình; số nhóm ID trùng trong JSON. Chu trình chỉ dựng từ ID hoặc file-stem được phân giải duy nhất, nhãn liệt kê thành viên không giả làm thứ tự đường đi. Snapshot JSON có thể không chứa đủ footprint dup:ids của repo; hai số phải phân biệt.

Danh sách hành động: tối đa 5 record mỗi nhóm priority cao (P0/P1/high/critical), blocked, in_progress; sắp priority rồi ID. Hiện đủ bao nhiêu ghi x/y. Owner dùng trường owner, thiếu ghi chưa ghi owner. Prerequisite/checklist/next action đều từ task metadata; không suy dev đã PASS, không tự đổi status. T358 bên dưới giữ chuyên môn agent, chứng cứ dev, typed confirmation và receipt admin_reviewed cục bộ.

## Nguồn và freshness

GET ../data/progress_data.json với cache:no-store + timeout 12s; event ptda:progress-snapshot từ render API Dashboard hiện có cập nhật cùng model. Nhãn ghi generated_at/source; timestamp thiếu timezone được nói rõ, không tự đoán múi giờ hoặc hiện nhãn live. T358 dùng report audited_at riêng, có provenance lịch sử 2026-10-12. Data sinh lại qua scripts/build_progress_data.py; không sửa tay generated JSON.

Native SVG donut và CSS bars có title/desc + legend số/text; không thêm chart/CDN dependency. Google Fonts/FontAwesome của trang bỏ phụ thuộc remote, giữ local font fallbacks và glyph cho 4 icon legacy. Details Integration mở bằng bàn phím, nav/skip links/focus/reduced-motion và mobile grids hỗ trợ đọc. Tất cả text mới dùng textContent, task links chỉ basename .md hợp lệ. Claim XSS này chỉ phần mới, không sửa renderer legacy ngoài scope.

## Nghiệm thu/giới hạn

Focused fixture phục vụ HTML/JS/CSS/local JSON thật qua route mocked toàn bộ, không app.py hoặc DB; kiểm counts/graphs/mobile/keyboard/XSS/missing data + T358 regression. Kết quả và common gates trong session/Handoff. Debug/root QA scoped PASS (18 + 2 checks); root đã giao commit sau QA, task giữ in_progress chờ Admin nghiệm thu. Những API và DONE legacy bên ngoài T358 được giữ nguyên, không bị control mới gọi.

## Rollback

Session before-manifest lưu hash và backup của HTML/tasktodo/progress. Sau build after-manifest ghi scope/hash. Restore owned patch chỉ khi hash guard đúng, không ghi đè concurrent WIP; giữ logs/docs. Khi có commit được root giao, dùng git revert SHA từ visjs-app root. Không DB/TTL rollback vì không mutation.

[Task](../tasks/T390-dashboard-process-executive-redesign.md) · [Session](sessions/2026-10-14_T390-dashboard-redesign/README.md) · [Handoff](Handoff-2026-10-14-T390-dashboard-redesign.md)

## QA độc lập và quyết định commit — 2026-10-14

Root chuyển kết quả Debug và phê chuẩn scoped commit. **18/18 PASS (48.4s) + final snapshot 2/2 PASS (9.4s), tổng 20 checks**; không trình bày như một suite 20 test. Lệnh independent: node node_modules/@playwright/test/cli.js test, config/output riêng tại C:/Users/NAMTHI~1/AppData/Local/Temp/t390-independent-qa-W6rcTb; config lần 1 playwright.config.cjs, lần 2 final-snapshot.config.cjs. Receipt gốc independent-results.json và final-snapshot-results.json được sao nguyên vào session; hash SHA256 lần lượt 32847b70810859498d7a8edca497f673ba335f36dc3e28757fb30dba5d889ec7 và 2ecb304402d5f5c7b089a91cc0df515f0396412d723fca756caa5454ad0b5cd5.

QA xác nhận T3906 + T3588 + 4 probe; final JSON 2 checks riêng. Counts 311=162+34+87+28, risks 50 waiting / 1 SCC / 5 JSON duplicate groups; sáu scalar |, |-, |+, >, >-, >+ fallback về mở task gốc; 375px keyboard/receipt/reload và T358 byte-equivalent. Snapshot kiểm có SHA256 1309242a7d9bdf94631382de9f202a6966dfd6a6be625273ab59209dd6a13cf9.

Common gates vẫn giữ giới hạn: guard PASS; dup/pipeline FAIL 9 ID lịch sử; tester runtime 2/2 ERR_CONNECTION_REFUSED localhost:5000, lint stderr ProgramFiles null bị exit mask. Không chứng nhận full pipeline hoặc production runtime.

**data/progress_data.json không đưa vào commit**: diff có T380 status, T381 record/route/module và git-history ngoài T390. Giữ nguyên snapshot working tree đã regenerate, không stage cả file hoặc sửa tay generated JSON. Task T390 vẫn in_progress chờ Admin nghiệm thu; Debug/root QA scoped đã PASS. Không DB/TTL/ETL mutation.
