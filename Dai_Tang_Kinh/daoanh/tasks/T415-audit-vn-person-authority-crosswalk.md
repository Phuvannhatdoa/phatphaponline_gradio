---
id: T415
title: "T415: Audit vn_person_authority — fix DILA ID mapping (1:N slugs)"
status: in_progress
created: 2026-10-15
updated: 2026-10-15
owner: null
module: Data Integrity / Crosswalk
priority: medium
depends_on: [T381]
depends_note: "Phát sinh từ T381 QA round 2 — 6 cạnh lỗi (5 self-loop + 1 reversed-duplicate)
  do vn_person_authority có 1:N slug→dila_id, 229 slug TTL chưa crosswalk được."
dispatch: approved
plan_approved_at: "2026-10-19 (Admin: duyệt audit chỉ đọc bước 1-4, liệt kê lỗi)"
done_when: >
  (1) Liệt kê đầy đủ các trường hợp vn_person_authority.slug map ra nhiều dila_id khác nhau
  (1:N), hoặc nhiều slug khác nhau map vào cùng 1 dila_id (N:1 — nguồn gốc 5 self-loop ở T381).
  (2) Liệt kê 229 slug TTL (101 teacher + 128 student, ghi trong T381_EXECUTION_LOG.md Bước 1)
  không có dila_id tương ứng trong vn_person_authority.
  (3) Trình danh sách cho Admin — không tự sửa dila_id khi chưa có xác nhận.
  (4) Sau khi Admin duyệt, sửa đúng các dòng vn_person_authority bị map sai, có backup tự động
  trước khi UPDATE, PRAGMA quick_check=ok.
revert: >
  Khôi phục từ backup tự động được tạo trước UPDATE (đường dẫn ghi trong session log của lần
  sửa), hoặc git revert nếu chỉ sửa docs/scripts.
outcome: >
  Audit chỉ đọc hoàn tất 2026-10-19 (bước 1-4), CHƯA sửa DB. Kết quả: 36 case N:1 (nhiều slug
  -> 1 dila_id), 0 case 1:N (cấu trúc không thể xảy ra, id là PRIMARY KEY), 229 dòng cạnh TTL
  thiếu dila_id (158 slug duy nhất, khớp 100% với T381_EXECUTION_LOG.md Bước 1). Phát hiện quan
  trọng: trong 6 case self-loop/reversed đã xóa ở T381 QA round 2, chỉ 2/6 (A000108, A014491) là
  do N:1 crosswalk thật; 4/6 còn lại do nguyên nhân khác (3 case raw dharma_lineage_ttl_vn có
  dòng tự tham chiếu teacher_id=student_id; 1 case là 2 cạnh ngược hướng hợp lệ giữa 2 người
  thật A003868/A010427) — không sửa được bằng cách đổi dila_id trong vn_person_authority. Chi
  tiết: docs/sessions/2026-10-19/T415_audit_phase/T415_AUDIT_SUMMARY.md. Chờ Admin duyệt bước
  5-6 (sửa DB từng case cụ thể).

  **2026-10-19 (tiếp, sau khi Admin duyệt Option 1):** Đã thử sửa 2 case N:1 (A000108,
  A014491) theo Option 1 nhưng KHÔNG thực hiện UPDATE nào — 0 thay đổi DB, không cần backup.
  Lý do: đi tìm dila_id đúng cho 2 dòng 'pending' bằng dila_reference, entity/entity_claims,
  person_display_names, person_refs, và đọc raw TTL gốc (data/ttl/TS-Nguyet-Chuong-Tri-Uyen.ttl,
  TS-Bao-Ninh-Nhan-Dung.ttl, TS-Long-Khanh-Khanh-Nhan.ttl, TS-An-Hoa-Van-Nhat.ttl) + vn_person_relations
  thì phát hiện giả định "status=auto_ttl luôn đúng, status=pending luôn sai" KHÔNG đúng cho cả
  2 case:

  - **A000108**: xác nhận `bao_ninh_nhan_dung` (auto_ttl) ĐÚNG là A000108 (entity.alias_zh=
    '保寧勇' khớp TTL + dila_reference.name_zh='保寧勇', dynasty 北宋). `nguyet_chuong_tri_uyen`
    (pending) là một vị tăng khác hẳn (đệ tử của bao_ninh_nhan_dung theo TTL, tên/địa danh khác
    hoàn toàn — "Nguyệt Chưởng" ≠ "Bảo Ninh") cần dila_id riêng — nhưng KHÔNG tìm được: không có
    trong dila_reference (chỉ 1000 dòng mẫu, không phải full DILA), không có owl:sameAs/dila URI
    trong raw TTL, không có entry trong person_display_names/person_refs/ai_person_name theo
    tên này. → DỪNG, không UPDATE `nguyet_chuong_tri_uyen`.

  - **A014491**: NGƯỢC với giả định ban đầu. Đọc kỹ raw TTL phát hiện `TS-An-Hoa-Van-Nhat.ttl`
    (nguồn của slug `an_hoa_van_nhat`, status hiện 'auto_ttl') có BUG tự thân: `rdfs:label` ghi
    sai thành "Long Khánh Khánh Nhàn" (dòng 7) trong khi toàn bộ biographicalNote + slug URI đều
    về "Thiền sư Văn Nhất ở An Hóa" — một người khác. Ngược lại, `long_khanh_khanh_nhan`
    (status 'pending') có bio khớp chính xác nhân vật lịch sử Thiền sư Khánh Nhàn ở Long Khánh
    (đệ tử Hoàng Long Huệ Nam, tịch năm Nguyên Phong thứ 4 / 1081 Bắc Tống), và `entity` table
    có alias_zh='隆慶閑' cho A014491 — khớp tên "Long Khánh" (隆慶) + "Nhàn" (閑) với nội dung TTL
    của `long_khanh_khanh_nhan`, không khớp với `an_hoa_van_nhat`. Tức là A014491 nhiều khả năng
    THUỘC VỀ `long_khanh_khanh_nhan` (dòng 'pending'), còn `an_hoa_van_nhat` (dòng 'auto_ttl')
    mới là dòng bị gán sai — do kế thừa nhãn lỗi từ raw TTL, không phải lỗi crosswalk đơn thuần
    trong vn_person_authority. Không tìm được dila_id riêng cho `an_hoa_van_nhat` trong bất kỳ
    nguồn nào đã tra (dila_reference không có A014491 dù đã dùng trong entity table; không có
    tên "An Hóa"/"安化" nào khớp). → DỪNG, không UPDATE cả 2 dòng của case này. Ghi chú: nếu Admin
    sau này xác nhận hướng ngược này, việc sửa đúng sẽ là đổi `an_hoa_van_nhat.dila_id` (không
    phải `long_khanh_khanh_nhan`) sang ID mới — nhưng cần tìm được ID đó trước, hoặc set rỗng/NULL
    thay vì giữ A014491 trùng.

  **Kết luận**: Không có UPDATE nào chạy trên `data/lineage.db` trong phiên này (SELECT/PRAGMA
  table_info only qua kết nối thường, không mở mode=ro riêng nhưng không ghi). Không tạo backup
  vì không có thay đổi. 4 case còn lại (A008431, A026988, A010985, A003868/A010427) theo audit
  trước đó vẫn chuyển sang T419, không đụng ở đây. Cần Admin cung cấp thêm nguồn xác thực (DILA
  gốc đầy đủ, không phải bảng mẫu 1000 dòng) hoặc quyết định hướng xử lý mới cho A014491 trước
  khi có thể apply bất kỳ UPDATE nào.
---

# T415 — Audit `vn_person_authority` crosswalk (slug → dila_id)

## Nguồn gốc

Phát sinh từ T381 (Build 3-Source Dharma Lineage). QA round 2 phát hiện 6/399 cạnh
`ttl_only` vừa insert bị lỗi:
- 5 self-loop (`teacher_id = disciple_id`): do 2 slug TTL khác nhau trong
  `dharma_lineage_ttl_vn` bị crosswalk nhầm vào **cùng một** `dila_id` trong
  `vn_person_authority` (N:1 sai).
- 1 cạnh đảo chiều tạo vòng 2 nút (`A003868 ↔ A010427`) — nghi ngờ cùng gốc crosswalk.

Ngoài ra, trong lúc ETL T381 (Bước 1), 229 slug TTL (101 teacher + 128 student) không có
`dila_id` trong `vn_person_authority` — bị log mismatch, không fabricate, nhưng chưa ai audit
tại sao thiếu (data entry thiếu, hay slug đánh sai).

## Scope

1. **Audit 1:N / N:1 mapping ambiguities** trong `vn_person_authority`:
   - Ví dụ dạng lỗi: `"Viên Ngộ"` (tên hiển thị) → nhiều `dila_id` khác nhau (`A000453`,
     `A000999`, …) — cần phân biệt bằng `slug` (join key thật), không phải tên.
   - Tìm toàn bộ cặp `(slug_A, slug_B)` khác nhau nhưng cùng `dila_id` (N:1 — nguồn gây
     self-loop khi ETL join ngược từ dila_id).
   - Dùng SQL trực tiếp trên `data/lineage.db`, không đoán qua tên hiển thị.
2. **Audit 229 slug thiếu `dila_id`** (danh sách đầy đủ, không phải chỉ đếm số lượng) — để
   Admin quyết định bổ sung hay bỏ qua từng trường hợp.
3. **Trình danh sách cho Admin** — KHÔNG tự sửa `dila_id` hàng loạt khi chưa có xác nhận
   từng trường hợp (naming-and-identity.md: không merge/sửa identity chỉ bằng matching tên).
4. Sau khi Admin duyệt từng trường hợp cụ thể: script sửa có `--dry-run`/`--apply`, backup tự
   động trước UPDATE, idempotent, `PRAGMA quick_check=ok`.

## Ràng buộc

- Không tự merge/sửa `dila_id` bằng tên hiển thị — chỉ dùng `slug` (join key) + xác nhận
  Admin cho từng trường hợp cụ thể.
- Không re-run lại 393/399 edges đã insert ở T381 (đã qua QA, giữ nguyên) — T415 chỉ audit
  bảng gốc `vn_person_authority`, không đụng `lineage_edge_consensus` trừ khi Admin yêu cầu
  re-ETL sau khi sửa crosswalk.
- Backup DB tự động trước mọi UPDATE.

## Các bước

- [x] Query tìm toàn bộ N:1 (nhiều slug → 1 dila_id) trong `vn_person_authority` — 36 case
- [x] Query tìm toàn bộ 1:N (1 slug → nhiều dila_id, nếu schema cho phép duplicate slug) — 0 case
  (`id` là PRIMARY KEY, về cấu trúc không thể có 1:N; đã verify bằng query, không chỉ suy luận)
- [x] Liệt kê đầy đủ 229 slug TTL thiếu `dila_id` (từ `dharma_lineage_ttl_vn` + crosswalk) —
  đo lại khớp 100% với T381 (101 teacher + 128 student dòng cạnh = 158 slug duy nhất)
- [x] Viết báo cáo audit, trình Admin — `docs/sessions/2026-10-19/T415_audit_phase/T415_AUDIT_SUMMARY.md`
- [x] Chờ Admin duyệt từng trường hợp sửa — Admin đã duyệt "Option 1" (2026-10-19) cho 2 case
  A000108/A014491, 4 case còn lại tách sang T419.
- [ ] Script sửa (`--dry-run`/`--apply`, backup tự động, idempotent) — **CHƯA chạy UPDATE nào**.
  Đã điều tra sâu bằng raw TTL + entity/entity_claims (xem `outcome` 2026-10-19 phần 2): phát
  hiện giả định "pending=sai, auto_ttl=đúng" sai cho case A014491 (bằng chứng cho thấy có thể
  ngược lại — `an_hoa_van_nhat` mới là dòng sai, không phải `long_khanh_khanh_nhan`), và không
  tìm được dila_id thay thế đáng tin cho `nguyet_chuong_tri_uyen` lẫn `an_hoa_van_nhat`. Theo
  đúng chỉ dẫn "không tự bịa ID, không giữ nguyên ID trùng khi không chắc" — dừng, không UPDATE.
  Cần Admin xem lại hướng xử lý (đặc biệt case A014491 đã đảo ngược) trước khi tiếp tục.
- [ ] daoanh-qa kiểm độc lập
- [ ] Admin xác nhận DONE

## Attribution

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
