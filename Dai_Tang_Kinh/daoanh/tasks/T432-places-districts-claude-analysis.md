---
id: T429
title: "T428 Part 0: Phân tích XML/TSV places + districts (chỉ đọc)"
status: pending
created: 2026-10-20
updated: 2026-10-20
owner: null
module: Data / Places / Analysis
priority: high
depends_on: []
dispatch: approved
plan_approved_at: "2026-10-20 (Admin phê chuẩn T428 plan, quyết định mặc định)"
done_when: >
  (1) Tải 2 XML + 2 TSV từ GitHub nhánh claude/sleepy-tesla-qsx17b (commit mới nhất):
      - vn_place_name_vi.xml (59.353 places)
      - vn_district_name_vi.xml (16.907 districts)
      - review_needed_places.tsv
      - review_needed_districts.tsv
  (2) Phân tích XML: cấu trúc thẻ, thuộc tính ID (dạng nào), có tier không, district định danh như thế nào.
  (3) So khớp với DB:
      - places_dila.id (59.167, ID dài PL000000000001): khớp bao nhiêu?
      - places.id (59.161, ID ngắn PL000000): khớp bao nhiêu?
      - places_dila.district (4.322 chuỗi khác nhau): khớp bao nhiêu?
      - Số orphan (không khớp) + số lệch chữ Hán.
  (4) Review import_name_vi.py: ghi vào bảng nào, có UPDATE bảng gốc không, phần nào là CLI args.
  (5) Ghi báo cáo: docs/sessions/2026-10-20/T429_analysis_report.md (con số khớp/orphan/lệch, commit SHA, khóa district dùng).
  (6) Không ghi DB, không chạy script, chỉ phân tích.
outcome: null
---

# T429 — Part 0: Phân tích XML/TSV places + districts

## Mục tiêu

Phân tích dữ liệu XML/TSV từ nhánh Claude trước khi viết script import. Chỉ đọc, không ghi DB.

## Công việc

1. **Tải từ GitHub** (nhánh claude/sleepy-tesla-qsx17b, commit mới nhất)
2. **Phân tích XML:**
   - Cấu trúc thẻ, ID, tier, district định danh
3. **So khớp DB:**
   - places_dila (59.167, ID dài)
   - places (59.161, ID ngắn)
   - places_dila.district (4.322 chuỗi)
   - Con số khớp / orphan / lệch chữ Hán
4. **Review script:** import_name_vi.py
5. **Ghi báo cáo:** docs/sessions/2026-10-20/T429_analysis_report.md

## Output

- Báo cáo: số khớp, số orphan, số lệch chữ Hán
- Commit SHA XML
- Quyết định khóa district: theo place_id hay chuỗi Hán?

---

id: T429
