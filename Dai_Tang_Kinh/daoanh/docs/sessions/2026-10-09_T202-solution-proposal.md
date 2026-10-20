# 2026-10-09 — đề xuất giải pháp identity/evidence/TTL

HEAD quan sát c5e3afba45a262afec0e104afbe1f48e60b99ce4. User yêu cầu giải pháp phù hợp toàn bộ điều kiện dự án.

Đã tạo [proposal](../plans/identity-evidence-remediation-20261009.md) và [Handoff](../Handoff-2026-10-09-T202-solution-proposal.md). Luồng nguồn→assertions→review từng trường→view→API/TTL, tái sử dụng tasks hiện có; negative mapping theo cặp, số đời đa hệ có chứng cứ, subscription-only và provenance/quyền artifact.

Đọc code/task/roadmap hiện có, đối chiếu W3C PROV-O/SHACL/OWL2. Không sửa app/DB/TTL/tasktodo/Dashboard, không tạo task ID, không chạy tests/pipeline hoặc gọi LLM. Trạng thái proposal hoàn tất; build chưa triển khai. Next đề xuất: phase0 inventory/gold cases, phase1 type/validator/fixture, phase2 typed decision/shared resolver, rồi refresh T223.

Lưu observation vào claude-mem local đã thử: curl exit7, service37700 không kết nối được; request/exit lưu trong thư mục report. Bàn giao và trạng thái đã lưu bằng file local.
