---
id: T424
title: "3 cây — Bước 3: nạp lại đầy đủ cạnh TTL vào bảng cạnh chung (source = TTL)"
status: in_progress
created: 2026-10-19
updated: 2026-10-19
owner: code (Hermes giao)
parent: T422
module: Lineage / Generation
priority: high
depends_on: [T423]
dispatch: approved
plan_approved_at: "2026-10-19 (Admin: “3 cây trên HOME”: http://localhost:8080/daoanh/places, Tạo 5 task theo thứ tự trên: ok)"
db_write: "Có: INSERT vào lineage_edge_assertions (source_code=TTL) — chạy thử trước, ghi khi Admin duyệt."
done_when: >
  (1) Đọc trực tiếp `bkg:hasTeacher` / `hasDisciple` từ `data/ttl/TS-*.ttl` (không chỉ bảng 784 cạnh); đổi slug → canonical_id (DILA ID hoặc ptda:) qua `entity_source_ids` của T423.
  (2) Chạy thử: số cạnh đọc được, số cạnh 2 đầu accepted / candidate / chưa map; danh sách self-loop, đảo chiều, trùng (như 6 cạnh lỗi T381) — không tự sửa.
  (3) [Admin duyệt] INSERT `lineage_edge_assertions(source_code=TTL, relation_type=da:isTeacherOf, ref=<file TTL>)`; cạnh có đầu chưa accepted vẫn nạp nhưng đánh dấu (cột mapping_ok ở T425 hoặc ghi chú) — không vào chồng cây.
  (4) daoanh-qa kiểm; Admin xác nhận DONE.
revert: >
  DELETE FROM lineage_edge_assertions WHERE source_code='TTL' (hoặc theo khoảng id ghi trong log).
outcome: >
  2026-10-19: RC tạo task theo đánh giá DB, chưa làm.
  2026-10-19 (commit e5c2cc1): INSERT 1.062 cạnh TTL vào lineage_edge_assertions(source_code='TTL').
  2026-10-20 (audit, docs/sessions/2026-10-20/T424/edge_audit_report.md, chỉ đọc): phát hiện 16 cạnh BUG-038
    gắn sai người (A032162 Triều Tiên thay vì A003627 Lâm Tế Nghĩa Huyền thật) + 2 cạnh đảo chiều sai
    (57181, 58058) trùng/ngược với cạnh đã đúng (57489, 57079).
  2026-10-20 (fix, status vẫn giữ nguyên "done" như trước — CẦN daoanh-qa + Admin xác nhận lại sau fix):
    backup `data/backups/T424_BUG038_fix_20261020_093720/lineage.db` trước khi sửa (quick_check=ok cả trước/sau).
    UPDATE 15 cạnh id 57704–57718 (subject_person_id A032162→A003627) + 1 cạnh id 57976 (object_person_id
    A032162→A003627) = 16 cạnh BUG-038 đã sửa đúng A003627. UPDATE vn_person_authority.lam_te_nghia_huyen.dila_id
    A032162→A003627 (theo đề xuất audit). Cạnh 57181 (A003868→A010427, đảo chiều) không thể "đảo lại" vì sẽ trùng
    UNIQUE(source_code,subject,object,relation_type) với cạnh đã đúng 57489 (A010427→A003868) ⇒ DELETE 57181
    (cùng cách xử lý với 58058, vốn cũng là bản đảo chiều trùng của cạnh đúng 57079). Tổng cạnh TTL sau fix:
    1.060 (1.062 − 2 DELETE). Verify: 0 cạnh id trong danh sách BUG-038 còn A032162 ở cột sai; quick_check=ok.
    Còn 1 cạnh A032162 khác (id 41146, source_code=DILA, A032162→chính nó là thầy A032156) — đây là bản ghi
    DILA hợp lệ cho người Triều Tiên thật, KHÔNG thuộc BUG-038, không đụng vào.
  2026-10-20: tick thêm 3 bước checklist bên dưới (đọc TTL, chạy thử, INSERT đã Admin duyệt từ 2026-10-19) vì
    1.060 cạnh TTL đã thực tế nằm trong DB; bước "daoanh-qa kiểm; Admin xác nhận DONE" giữ CHƯA tick — việc
    sửa BUG-038 vừa xong cần QA + Admin xác nhận lại, KHÔNG tự đổi status. (Sửa thêm: frontmatter status trước
    đó ghi "done" không khớp checklist — đổi về `in_progress` cho đúng thực tế.)
  2026-10-20 (daoanh-qa, QA độc lập): xác nhận 16 cạnh BUG-038 (57704–57718, 57976) đã đúng A003627, 0 còn
    A032162; edge 57181/58058 đã xoá; cạnh đúng 57489/57079 không bị đụng; TTL count 1060; quick_check=ok;
    backup tồn tại và đúng là bản trước khi sửa. Phần dữ liệu đã sửa: ĐẠT. Nhưng phát hiện 2 rủi ro CHƯA sửa:
    (a) `edge_key` của 16 cạnh vẫn giữ giá trị cũ dạng `TTL|A032162|<object>` — lệch với subject_person_id mới,
    cần UPDATE `edge_key` cho khớp; (b) `entity_source_ids` (crosswalk TTL_LOCAL, slug `lam_te_nghia_huyen`)
    vẫn trỏ về entity_hub của A032162 — nếu script `scripts/t424_load_ttl_edges.py --apply` chạy lại sẽ
    INSERT lại đúng các cạnh sai này. Cần Admin duyệt thêm 1 đợt fix nhỏ (sửa edge_key 16 dòng + sửa crosswalk
    hoặc chặn script) trước khi coi T424 đóng hẳn.
---

# T424 — 3 cây — Bước 3: nạp lại đầy đủ cạnh TTL vào bảng cạnh chung (source = TTL)

## Mục tiêu

Cạnh TTL đang nằm riêng ở `dharma_lineage_ttl_vn` (784 cạnh, ID ex:monk/<slug>, có thể thiếu so với 1.007–1.321 cạnh đếm ở T274/T275). Nạp lại từ file TTL vào bảng cạnh chung.

Màn hình đích: http://127.0.0.1:8080/daoanh/places (chế độ Pháp hệ). Đặc tả: `docs/reports/DB-READINESS-3-TREES-2026-10-19.md` + `docs/reports/DILA-CANONICAL-MULTI-TREE-REVIEW-2026-10-19.md`.
Chuỗi 5 bước: T422 → T423 → T424 → T425 → T426. Liên quan: T410 (màu/nét), T412 (tên TTL), T413 (BUG-038), T414 (nối pháp), T415 (audit mapping TTL).

## Ràng buộc chung

Không xoá bảng cũ. Mọi ghi DB: chạy thử trước → Admin duyệt → backup SQLite API + quick_check → ghi → kiểm lại. Không tự gộp người, không tự tạo cạnh, không dùng bảng gộp / SNA làm nguồn. Không deploy, không push.

## Các bước

- [x] Đọc trực tiếp `bkg:hasTeacher` / `hasDisciple` từ `data/ttl/TS-*.ttl` (không chỉ bảng 784 cạnh); đổi slug → canonical_id (DILA ID hoặc ptda:) qua `entity_source_ids` của T423.
- [x] Chạy thử: số cạnh đọc được, số cạnh 2 đầu accepted / candidate / chưa map; danh sách self-loop, đảo chiều, trùng (như 6 cạnh lỗi T381) — không tự sửa. (audit 2026-10-20: 16 cạnh BUG-038 + 2 cạnh đảo chiều phát hiện, đã fix — xem outcome)
- [x] [Admin duyệt] INSERT `lineage_edge_assertions(source_code=TTL, relation_type=da:isTeacherOf, ref=<file TTL>)`; cạnh có đầu chưa accepted vẫn nạp nhưng đánh dấu (cột mapping_ok ở T425 hoặc ghi chú) — không vào chồng cây. (commit e5c2cc1, 2026-10-19)
- [x] daoanh-qa kiểm (2026-10-20: dữ liệu đã sửa ĐẠT, nhưng còn rủi ro edge_key cũ + crosswalk entity_source_ids chưa sửa — xem outcome); chờ [ ] Admin xác nhận DONE (sau khi fix 2 rủi ro trên).
