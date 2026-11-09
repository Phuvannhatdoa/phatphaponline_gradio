---
id: T422
title: "3 cây — Bước 1: khử trùng cạnh DILA (46.006 → 23.014) + ràng buộc chống trùng"
status: done
created: 2026-10-19
updated: 2026-10-20
owner: code (Hermes giao)
module: Lineage / Generation
priority: high
depends_on: []
dispatch: approved
plan_approved_at: "2026-10-19 (Admin: “3 cây trên HOME”: http://localhost:8080/daoanh/places, Tạo 5 task theo thứ tự trên: ok)"
db_write: "Có: DELETE dòng trùng + CREATE UNIQUE INDEX — chạy thử trước, ghi DB khi Admin duyệt kết quả chạy thử."
done_when: >
  (1) Script `scripts/t422_dedupe_dila_edges.py --dry-run` liệt kê nhóm trùng theo `(source_code, subject_person_id, object_person_id, relation_type)`, chọn dòng giữ (id nhỏ nhất, gộp `ref` nếu khác) — xuất TSV + số đếm.
  (2) [Admin duyệt] `--apply`: backup SQLite API + quick_check; xoá dòng trùng; `CREATE UNIQUE INDEX uq_lea_src_pair ON lineage_edge_assertions(source_code, subject_person_id, object_person_id, relation_type)`.
  (3) Sau: DILA = 23.014 dòng; MARCUS không đổi (11.169); các bảng khác không đổi; cây trên /daoanh/places hiển thị như trước (ảnh trước/sau 1 nhân vật).
  (4) daoanh-qa kiểm; Admin xác nhận DONE.
revert: >
  Khôi phục backup (bảng lineage_edge_assertions) + DROP INDEX uq_lea_src_pair.
outcome: >
  2026-10-19: RC tạo task theo đánh giá DB, chưa làm.
  2026-10-19 (RC, cùng phiên T410): Script `scripts/t422_dedupe_dila_edges.py` đã viết xong (--dry-run / --apply / --revert).
  Đã chạy DRY RUN (chỉ đọc, mode=ro): DILA 46.006 rows → 23.014 distinct pairs; 22.992 nhóm trùng, xoá 22.992 dòng.
  MARCUS 11.169 rows = 11.169 pairs (KHÔNG có trùng). relation_type duy nhất: da:isTeacherOf.
  Quan trọng: mọi cặp trùng DILA đều GIỐNG HỆT NHAU ở mọi cột trừ `id` (ref=NULL, edge_key, created_at, trust_level='L2', mapping_verified=1 đều y hệt) → giữ id nhỏ nhất, KHÔNG cần gộp ref (0 nhóm cần gộp).
  Index hiện có: chỉ `idx_lea_edgekey` (không unique). UNIQUE index `uq_lea_src_pair` sẽ tạo ở bước --apply.
  Bằng chứng: `docs/sessions/2026-10-19/T422/t422_duplicate_groups.tsv` (22.992 dòng) + `t422_dry_run_report.txt`.
  2026-10-19 (RC) — Admin DUYỆT --apply. ĐÃ GHI DB:
    - Backup: `data/backups/T422_20261019_201110/lineage.db` (1.535,6 MB, PRAGMA quick_check = OK).
    - Xoá 22.992 dòng trùng; 0 nhóm cần gộp ref.
    - Tạo `uq_lea_src_pair` UNIQUE (source_code, subject_person_id, object_person_id, relation_type) — OK.
    - SAU: DILA 23.014 (= distinct pairs), MARCUS 11.169 (không đổi), TOTAL 34.183; nhóm trùng còn lại = 0.
    - Manifest: `data/backups/T422_20261019_201110/t422_apply_manifest.txt`.
  VERIFY độc lập (kết nối ro mới): counts khớp; spot-check 3 cặp (A000005→A000668, A000005→A003958, A049062→A025043) đều còn đúng 1 dòng.
  REGRESSION cây: API `/daoanh/api/monk/A003623/lineage-tree` → 200 (415 edges / 416 nodes);
    so ảnh TRƯỚC (T410) vs SAU (T422) cho 3 nhân vật × 2 theme = **6/6 ảnh PIXEL-IDENTICAL** (PIL ImageChops, khác 0 px).
    Kết luận: khử trùng chỉ xoá dòng byte-identical → cây truyền thừa giữ nguyên 100%.
  Còn lại: daoanh-qa kiểm độc lập + Admin xác nhận DONE → đổi status: done.
---

# T422 — 3 cây — Bước 1: khử trùng cạnh DILA (46.006 → 23.014) + ràng buộc chống trùng

## Mục tiêu

Cây DILA hiện lưu mỗi cặp thầy–trò 2 lần trong `lineage_edge_assertions` (46.006 dòng / 23.014 cặp). Khử trùng và chặn trùng về sau.

Màn hình đích: http://127.0.0.1:8080/daoanh/places (chế độ Pháp hệ). Đặc tả: `docs/reports/DB-READINESS-3-TREES-2026-10-19.md` + `docs/reports/DILA-CANONICAL-MULTI-TREE-REVIEW-2026-10-19.md`.
Chuỗi 5 bước: T422 → T423 → T424 → T425 → T426. Liên quan: T410 (màu/nét), T412 (tên TTL), T413 (BUG-038), T414 (nối pháp), T415 (audit mapping TTL).

## Ràng buộc chung

Không xoá bảng cũ. Mọi ghi DB: chạy thử trước → Admin duyệt → backup SQLite API + quick_check → ghi → kiểm lại. Không tự gộp người, không tự tạo cạnh, không dùng bảng gộp / SNA làm nguồn. Không deploy, không push.

## Các bước

- [x] Script `scripts/t422_dedupe_dila_edges.py --dry-run` liệt kê nhóm trùng theo `(source_code, subject_person_id, object_person_id, relation_type)`, chọn dòng giữ (id nhỏ nhất, gộp `ref` nếu khác) — xuất TSV + số đếm. **(2026-10-19: 22.992 nhóm, xoá 22.992 dòng; 0 nhóm cần gộp ref; MARCUS không trùng)**
- [x] `--apply` (Admin duyệt 2026-10-19): backup SQLite API + quick_check; xoá dòng trùng; `CREATE UNIQUE INDEX uq_lea_src_pair ON lineage_edge_assertions(source_code, subject_person_id, object_person_id, relation_type)`. **(ĐÃ GHI DB: backup `data/backups/T422_20261019_201110/`; xoá 22.992 dòng; index unique=1)**
- [x] Sau: DILA = 23.014 dòng; MARCUS không đổi (11.169); các bảng khác không đổi; cây trên /daoanh/places hiển thị như trước. **(6/6 ảnh trước/sau PIXEL-IDENTICAL; API 200)**
- [ ] daoanh-qa kiểm; Admin xác nhận DONE.
