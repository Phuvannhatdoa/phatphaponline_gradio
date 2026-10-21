---
id: T429
title: "[Thiền Đăng Thế Phổ] 禪燈世譜 (CBETA X86n1601) — dataset phả hệ, lượt 1: Giai đoạn 0–2 (khảo sát, đóng băng nguồn, giải mã cấu trúc sơ đồ)"
status: pending
created: 2026-10-20
updated: 2026-10-20
owner: code (Hermes giao)
module: Lineage / Research / CBETA
priority: medium
depends_on: []
dispatch: approved
plan_approved_at: "2026-10-20 03:46 (Admin: 'phê chuẩn đề xuất này … tạo task mới … cho kế hoạch chi tiết này')"
db_write: "Không. Chỉ tạo file trong research/thiendang-thepho/ và docs/. Không ghi DB / TTL / legacy / HOME; không gọi API trả phí."
plan: docs/plans/T429-thiendang-thepho-plan.md
review: docs/reports/THIENDANG-THEPHO-PLAN-REVIEW-2026-10-20.md
done_when: >
  (1) Giai đoạn 0: docs/reports/thiendang-thepho/phase0/{environment-audit,reuse-map,scope-and-boundaries}.md — phân biệt code thật với chức năng chỉ có trong docs; đề xuất tái sử dụng (entity_source_ids, lineage_edge_assertions, chuỗi T422–T426) trước khi viết mới.
  (2) Giai đoạn 1: research/thiendang-thepho/manifests/{source-manifest.json,source-header.xml,SHA256SUMS.txt} + rights-assessment.md; xác nhận từ header thật: 禪燈世譜, X86n1601, 9 quyển; quyền non-commercial + giữ header; hash tái tính khớp.
  (3) Giai đoạn 2: structure-inventory.json, structure-analysis.md, extraction-rules.md, sample-source-fragments/ — chứng minh hoặc bác bỏ R01–R07 bằng locator item/@xml:id thật (đầu / giữa / cuối tác phẩm), gồm cả ví dụ KHÔNG được trích; kết luận rõ XML có đủ để tái tạo quan hệ hay cần ảnh trang.
  (4) Không trích cạnh hàng loạt; không tạo DILA ID; không suy số đời; chứng minh không đổi production (git status + DB mtime/hash trước–sau).
  (5) Báo cáo theo mẫu mục 8 của plan; daoanh-qa kiểm độc lập; DỪNG chờ Admin chỉ đạo trước Giai đoạn 3.
revert: >
  Xoá thư mục research/thiendang-thepho/, docs/reports/thiendang-thepho/, scripts/thiendang_thepho/ (chỉ chứa file của task này); git revert commit của T429.
outcome: >
  2026-10-20: RC thẩm định kế hoạch (9 điểm sửa), Admin phê chuẩn 03:46. Tạo task + plan. Chưa làm.
  Ghi chú: T428 từng bị trùng (BUG-046; import Places/Districts) nên task này lấy T429; task import đã đổi sang T430.
---

# T429 — Thiền Đăng Thế Phổ 禪燈世譜: Giai đoạn 0–2

## Mục tiêu

Khảo sát, đóng băng nguồn và giải mã cấu trúc sơ đồ của 禪燈世譜 (CBETA X86n1601, 9 quyển) trong vùng cách ly. Mục đích là chuẩn bị dựng dataset phả hệ có provenance. Chưa đưa vào DB chính, TTL hay HOME.

- Kế hoạch đầy đủ (đã gồm 9 điểm sửa): `docs/plans/T429-thiendang-thepho-plan.md`
- Thẩm định: `docs/reports/THIENDANG-THEPHO-PLAN-REVIEW-2026-10-20.md`

## Liên quan

T410 (luật màu: nguồn này **không** được tính vào "≥ 2 nguồn khớp" khi chưa duyệt phụ thuộc nguồn) · T414 (từ vựng quan hệ) ·
T422–T426 (đích tích hợp về sau: `lineage_edge_assertions` + `entity_source_ids`).

## Các bước

- [x] RC thẩm định kế hoạch + đọc thử XML (2026-10-20)
- [x] Admin phê chuẩn (2026-10-20 03:46)
- [ ] Giai đoạn 0 — khảo sát hệ thống, bản đồ tái sử dụng
- [ ] Giai đoạn 1 — đóng băng nguồn, hash, quyền
- [ ] Giai đoạn 2 — giải mã cấu trúc, chốt R01–R07 bằng ví dụ thật
- [ ] daoanh-qa kiểm độc lập
- [ ] Báo cáo Admin, chờ chỉ đạo Giai đoạn 3
