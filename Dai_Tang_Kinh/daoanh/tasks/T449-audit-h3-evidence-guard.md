---
id: T449
title: "Guard cho audit_h3_conflicts.py: không ghi đè evidence khi kết quả rỗng/bất thường"
status: pending
created: 2026-10-21
updated: 2026-10-21
owner: null
module: Scripts / T263 evidence
priority: high
depends_on: []
done_when: >
  (1) scripts/audit_h3_conflicts.py TỪ CHỐI ghi đè file evidence đích khi số dòng
      dữ liệu mới < 50% số dòng dữ liệu của file cũ đang tồn tại (thoát khác 0, in
      cảnh báo, KHÔNG ghi file).
  (2) Có cờ --force để ghi đè có chủ đích (mặc định KHÔNG bật).
  (3) Test tự động: chạy script 2 lần với dữ liệu rỗng/bất thường → file evidence
      cũ còn nguyên (so SHA256 trước/sau = giống nhau).
  (4) Test edge: chạy với dữ liệu bình thường lần đầu (file chưa tồn tại) → ghi được;
      chạy lại với --force → ghi đè đúng.
  (5) Tên file evidence không bị đổi (vẫn theo DATE hard-code hiện tại, trừ khi Admin
      duyệt đổi riêng).
  (6) Không đổi dữ liệu DB, không đổi file raw (DILA TTL, Marcus RDF, CBETA XML).
---

# T449 — Guard cho `audit_h3_conflicts.py`

## Nguyên nhân

- `scripts/audit_h3_conflicts.py:216` và `:222` mở file đích bằng `io.open(..., "w")`
  rồi ghi trực tiếp. Không có kiểm tra "kết quả mới có rỗng/bất thường không" và
  không có kiểm tra "file cũ đang có dữ liệu".
- Tên file hard-code theo ngày (`"%s_T263_h3_conflicts.tsv" % DATE`,
  `scripts/audit_h3_conflicts.py:214-215`). Chạy lại trong ngày sẽ nhắm đúng file
  evidence đã commit (`docs/evidence/2026-10-08_T263_...`) nếu DATE trùng → ghi đè.

## Sự cố 2026-10-21 (bằng chứng)

- `docs/evidence/2026-10-08_T263_h3_conflicts.tsv`: **407 dòng → 1 dòng** (chỉ header,
  57 byte). Bản hỏng đã lưu tại `docs/sessions/2026-10-21/T263-damaged/`.
- `docs/evidence/2026-10-08_T263_h3_conflicts_summary.tsv`: **47/79/280 → 0/0/0**
  (nhóm A/B/C).
- Khôi phục bằng `git show HEAD:<path>` (blob `46ff20f0…` = 44331 byte, 407 dòng;
  summary blob `df9d0c46…` = 226 byte, 47/79/280). SHA256 file khôi phục = SHA256 blob HEAD.
- Đây là ghi đè không có cảnh báo; script không báo lỗi khi kết quả rỗng.

## Phạm vi

- CHỈ sửa `scripts/audit_h3_conflicts.py` + thêm test cho nó (`tests/`).
- Thêm kiểm: đọc số dòng dữ liệu của file đích (nếu tồn tại) → so với số dòng mới →
  từ chối nếu < 50%. Cờ `--force` bỏ qua kiểm tra này.
- Ghi bằng file tạm + `os.replace` sau khi qua kiểm tra (tránh file nửa vời).

## KHÔNG làm

- KHÔNG đổi dữ liệu DB, KHÔNG chạy migration.
- KHÔNG sửa file raw (DILA TTL, Marcus RDF, CBETA XML).
- KHÔNG đổi logic phân nhóm A/B/C (ngoài phạm vi guard).
- KHÔNG git reset/stash; commit theo AGENTS §14/§17 (temp index, file đích danh).

## Trạng thái

- `pending`. Sửa code để sau QA (Admin duyệt 2026-10-21: "việc sửa code để sau, sau QA").
- Khi làm: backup script vào `docs/sessions/<ngày>/` trước khi sửa; QA độc lập bằng
  `daoanh-qa`; Admin xác nhận DONE.

## Liên quan

- Khôi phục evidence: commit ghi trong `docs/sessions/2026-10-21/` (xem git log).
- Revert code (khi làm): `git revert <sha>`. Không có thay đổi DB → không cần ROLLBACK DB.
