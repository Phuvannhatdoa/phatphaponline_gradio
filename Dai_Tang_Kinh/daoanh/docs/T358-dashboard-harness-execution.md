---
task: tasks/T358-dashboard-harness-agent-execution-panel.md
---

# T358 — Harness triage và execution review

Ngày audit/build: 2026-10-12. Nguồn local code/docs/task/Dashboard; không kiểm production DB, không external historical verification. Root đã cấp T358 sau kiểm hai tầng. Task vẫn in_progress; root đã xác nhận QA PASS và giao commit scoped. Cổng chung vẫn FAIL như logs, không đổi trạng thái các task triage.

## Màn hình và thứ tự

Panel nằm trong “🧭 Harness Đạo Ảnh & T263 — H3 Conflicts”, trước KPI H3. Nó có 15 dòng: 11 task và 4 nhóm blocker. Thứ tự ưu tiên T283→T284/T290; T287→T288; song song T319/T322/T323/T81/T277/T328. Mỗi dòng ghi specialty, prerequisite, dev acceptance, evidence/locator và việc Admin làm tiếp. Các task cũ không bị tự đổi trạng thái.

Report tách bằng chứng audit hiện trạng khỏi bằng chứng dev hoàn tất. T283 scan chỉ in tên file, 6 path chứ không phải số 18 cũ; không in key. T287 phải xử lý đúng writer wire_evidence_into_entity_claims và ImportError fail-open của etl_entity_claims; etl_t109_provenance chỉ là audit output. T81 code đã có, cần UI QA; T277 archive 230 file chỉ là phần đã xong; T328 còn P0 closure cần chứng minh.

T274 có 2 footprint ID, coverage parsed 499/1036 là claim session 11-10, không phải audit production mới. T200/T223 identity còn cần quyết định và sử liệu, khác T357 remediation ETL/former T223. Graph depends_on chuỗi YAML hiện cho T22→T22 và T50→T73→T59→T53→T50. dup:ids baseline fail 9 ID cũ; không gỡ tự động hoặc khóa toàn bộ task không liên quan chỉ vì duplicate khác.

## Nguồn và quyền ghi

- dashboard/dashboard_process.html: chỉ hook panel/asset và sửa nhãn flow vai trò hiện hành.
- dashboard/triage_execution.js/.css: renderer/gate/confirmation độc lập; không dùng API DONE của board cũ.
- data/triage_execution_report.json: derived snapshot có definition_version, revision, audited_at và provenance; writer cập nhật sau evidence + QA.
- data/progress_data.json: trạng thái task hiện hành từ generator build_progress_data.py. Chỉ đọc trong UI; regenerated qua script, không sửa tay.

## Gate và confirmation

Gate chỉ mở cho kind=task, mỗi task ID có đúng một record Dashboard, status không blocked, prerequisites explicit satisfied=true. development.completed phải true; implementation/tests/independent_qa mỗi loại đúng một PASS có evidence link nội bộ hợp lệ, và mọi check bổ sung cũng PASS. Không suy từ status=done, receipt cũ hoặc checkbox Admin. Report hiện 0 ready; 15 DONE đều disabled.

Khi dev gate đủ, Admin mở dialog có nhãn, focus input, nhập chính xác row/task ID rồi xác nhận; Cancel/Escape không ghi. Gate được kiểm lại trước write. Receipt chỉ có review_status=admin_reviewed và exact evidence token/revision/task metadata trong localStorage key ptda:harness:admin-review:v1:<row_id>. Đổi evidence/prerequisite/revision/status/file sẽ làm receipt cũ stale. Review không ẩn task, đổi KPI, frontmatter, overrides hoặc production.

Đây là local tiện ích review, không phải authentication, chữ ký hay task SSOT. User có thể xóa/chỉnh localStorage của mình; không tác động repo/server. Storage lỗi không báo thành công. Reload hủy dialog đang mở; thiếu/sai report thì fail-closed.

## Accessibility và XSS

Table có caption, scope headers và region cuộn ngang có tabindex. Nút có disabled + aria-describedby lý do; dialog có label/description, keyboard/Escape/focus return. Mobile cuộn trong table, không kéo rộng trang. Dữ liệu dùng createElement/textContent, không innerHTML; links chỉ allowlist relative tasks/docs/scripts/admin với từng segment hợp lệ. Các phần Dashboard cũ nằm ngoài claim XSS của T358.

## Kiểm thử và giới hạn

Focused tests/t358-dashboard-harness.spec.js phục vụ panel markup/JS/CSS thật trong fixture HTTP bị route/mock toàn bộ, không app.py hoặc DB. 8/8 PASS trong focused-tests-3.json: disabled gate, typed confirmation/cancel/Escape, receipt reload/stale, blocked/duplicate task, XSS, storage failure, load failure, mobile/keyboard. node --check source PASS. Screenshot mobile-review-fixture.png là fixture ready, không phải task T283 đã hoàn tất thật.

Hai lỗi ban đầu được kiểm chứng và sửa: escape regex khi ghi source; fixture thiếu meta charset UTF-8. Logs lỗi vẫn giữ, không ghi như PASS. Validation generator/guard/dup/tester/pipeline và QA cuối được ghi trong session; không suy full pipeline từ focused tests. Không production DB/TTL/ETL write, external API hay commit trong build này.

## Rollback và tiếp nối

Before-manifest.json lưu hash/backup của 3 file có sẵn. Restore chỉ scope T358 sau hash guard đối chiếu after-manifest, giữ WIP khác và tài liệu; không dùng git checkout toàn file khi session khác đã sửa. Source mới có thể bỏ hook khỏi HTML khi revert patch, không cần xóa logs. Khi có commit được root giao, git revert --no-edit <SHA> từ visjs-app root; SHA chưa có lúc build.

[Task](../tasks/T358-dashboard-harness-agent-execution-panel.md), [session](sessions/2026-10-12_T358-dashboard-harness/README.md), [Handoff](Handoff-2026-10-12-T358-dashboard-harness.md).
