# Handoff — 2026-10-09 — đề xuất thống nhất identity/evidence/TTL

## 1. Bảng thông tin đọc nhanh

| Mục | Trạng thái |
|---|---|
| Phạm vi | Đề xuất theo toàn bộ ràng buộc Admin |
| Build/app/DB/TTL | Không thay đổi |
| Tests/pipeline/preflight | Không chạy lại; chỉ tài liệu |
| Task mới | Không cấp ID |
| Git | Không stage/commit; HEAD ghi ở session log |

## 2. Đọc trong 2 phút

[Proposal đầy đủ](plans/identity-evidence-remediation-20261009.md). Tận dụng Flask/SQLite/profile v2 và engine hiện có. Luồng nguồn→assertion→review theo từng trường→view dùng chung→API/cây/TTL. Admin duyệt tên không tự duyệt identity/bio/quan hệ/đời. Ba ưu tiên: sửa type/validator/fixture; typed decisions/resolver và rejection theo cặp; refresh T223 có chứng cứ.

## 3. Đề xuất chữa dựng cụ thể

T166/T201 sửa PLACE hardcode/schema fixture/validator. T256/T257 hiện gate tên trả kèm generation/bio và verified_direct; tách status từng trường, scope từng local-person/DILA pair. T223 phân nhóm ứng viên, không gộp/xóa từ trùng tên. T232 chỉ suy số có hệ/mốc/path, giữ dự kiến. T233 subscription-only/cache/resume, không paid fallback. T226/T227 giữ nguồn/revision/accepted projections, quyền release kiểm artifact.

## 4. Cảnh báo bắt buộc

Proposal chưa là build. Không auto-accept mapping/đời; không đổi URI hoặc xóa người local/alias. ID A000662 đã chốt khác Minh Hải Pháp Bảo phải được enforcement theo cặp. Worktree nhiều session, Git root visjs-app. Không chạy full importer/API LLM để làm proposal. Metadata LEGACY ingest không đủ chứng minh quyền công bố.

## 5. Rollback

Không mutation app/DB/TTL để rollback. Chỉ có tài liệu proposal/Handoff/session và observation artifacts. Xóa đúng file mới chỉ mất đề xuất; DB/TTL mất0 dữ liệu. Bản build tương lai phải additive, snapshot/run/revision guard, inverse có guard và rollback rehearsal; không restore toàn DB khi session khác có thay đổi.

## 6. File tạo

docs/plans/identity-evidence-remediation-20261009.md; docs/Handoff-2026-10-09-T202-solution-proposal.md; docs/sessions/2026-10-09_T202-solution-proposal.md; proposal-observation-* trong docs/reports/T202-logic-review-20261009.

## 7. Sai lầm và bài học

Search đầu thử ttl_profile_v2.py/generation_engine.py ở root, không tồn tại. Đọc import xác nhận file ở src_python/ttl_profile_v2.py và src_python/generation_engine_v2.py; không tạo module trùng. Không gọi trạng thái trong task docs là runtime hiện tại. Số31nhóm là snapshot review trước, proposal không đo lại.

## 8. Chưa xong

Chưa triển khai bất kỳ bước sửa nào; chưa inventory đủ consumers/schema/gates trong bước0. Chưa kiểm runtime browser/export của kiến trúc đề xuất. Không xác minh hay quyết gộp/tách31nhóm. Domain resolver và quyền từng artifact phải chốt trước release công khai.

## 9. Kiểm tra nhanh

Đọc proposal14 mục và review T202 liền trước. Kiểm app.py6125–6187 cho field gate; profile STATUSES và accepted projection; generation_engine_v2 rules. Không import app.py vì có side effects. Mọi Git từ root. Khi build chạy tests ngữ nghĩa và npm.cmd run pipeline trước review.

## 10. Agent kế tiếp

Tiếp nối task đã có, kiểm duplicate IDs/prose nếu cần task mới. Bắt đầu inventory + gold cases rồi type/validator/fixture; không bắt đầu bằng full ETL. Duyệt mapping và tên là hai quyết định. Proposal có schema-level contract nhưng chưa ấn định bảng mới: kiểm schema thật, tái sử dụng entity_hub/claims/source records, chỉ additive phần thiếu. Giữ unresolved, không tự cộng đời hoặc gọi API trả phí.

Lưu observation vào claude-mem local đã thử: curl exit7, service37700 không kết nối được; request/exit lưu trong thư mục report. Bàn giao và trạng thái đã lưu bằng file local.
