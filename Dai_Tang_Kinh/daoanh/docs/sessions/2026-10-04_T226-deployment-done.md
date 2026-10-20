---
task: tasks/T226-academic-ttl-profile-v2.md
date: 2026-10-04
---

# T226 — chốt triển khai TTL học thuật v2

T226 DONE. Main 5000 reload qua Windows RunAs/UAC thành công, PID 22920 → 17212. Schema 2.0.0 / API lineages / login qua 8080 HTTP 200; UI origin chính 14/14, 0 page errors; unit 26/26 và toàn pipeline exit 0 / runtime 2/2. Không apply dữ liệu TTL vào DB hoặc file TTL active. Admin xác nhận xóa 2 selfhasDisciple; RDF và SHA kiểm lại đều đạt.

Evidence: deployment-verified.json, reload-status.json, ui-deployed-8080.log, pipeline-status.json, admin-self-edge-removal-verified.json trong docs/reports/T226-ttl-profile-20261003. Quét bổ sung Oct4 nằm ở corpus-20261004-final. [Bàn giao 10 mục](../Handoff-2026-10-04-T226-ttl-profile-v2.md), [roadmap](../reports/T226-academic-ttl-roadmap.md).

Next: chốt P1 catalog/rights và P2 mapping trước P3–P6. Chưa cấp ID task mới, chưa xác minh đủ danh mục 25 nguồn, chưa mở public release. Admin nên thử lưu bản nháp bằng phiên thật; tests đã kiểm fixture auth/storage và 401 khi thiếu session.

Memory POST tasktodo đã thử nhưng localhost:37700 không chạy (curl exit7); trạng thái DONE và next P1–P2 được giữ trong docs/tasktodo.md cùng request/fallback ở report để gửi lại sau.
