---
id: T459
title: Nối kinh Hán (kinh lục DILA T453) ↔ kinh Pāli qua SuttaCentral parallels + link bản Việt
status: pending
created: 2026-10-22
updated: 2026-10-22
owner: tich-hop
module: Data / Crossref
priority: medium
parent: T453
plan_approved_at: "2026-10-22 (Admin phê chuẩn đề xuất deepsearch). Ghi DB: duyệt riêng ở bước apply."
done_when: >
  (1) Snapshot suttacentral/sc-data relationship/parallels.json (1,5 MB, CC0) + commit/SHA256; xác nhận giấy phép.
  (2) Ánh xạ mã SuttaCentral của kinh Hán (vd. t1, t26…) ↔ cbeta_id T453 (T0001…); báo % khớp.
  (3) Bảng additive `dila_catalog_parallels` (cbeta_id, sc_uid, loại full/partial/mention, nguồn).
  (4) UI thẻ kinh HOME thêm dòng 🔗 "Kinh tương đương" (vd. Trường A-hàm ↔ Dīgha Nikāya) + link SuttaCentral bản Việt nếu có.
  (5) Không chép nội dung bản dịch SuttaCentral vào DB (chỉ link). Backup + ROLLBACK; daoanh-qa ĐẠT; Admin DONE.
revert: >
  DROP TABLE dila_catalog_parallels; khôi phục app.py/index.html từ backup.
---

# T459 — SuttaCentral parallels (0 token)

Nguồn: https://github.com/suttacentral/sc-data — `relationship/parallels.json` (1.511.327 byte, đo 2026-10-22).
Giá trị: người dùng xem kinh Hán (A-hàm, Luật…) thấy ngay kinh Pāli tương ứng và bản Việt (HT. Thích Minh Châu trên SuttaCentral).
Liên quan: bảng `pali_cbeta_map` (6 dòng) và `toh_cbeta_crossref` (10) hiện có — đối chiếu, không ghi đè.
