---
id: T80
title: "Lô 1 — hoàn thiện 17 task đang dở (3 phase, ~5 tuần)"
module: Harness / Điều phối
priority: high
status: in_progress
depends_on: []
created: 2026-10-11
updated: 2026-10-11
desc: "Admin phê chuẩn giải pháp tối ưu 3 phase (2026-10-11): Phase 1 (3-5 ngày T265+T276), Phase 2 (2-3 tuần bug+13 task song hành), Phase 3 (1 tuần QA+bàn giao)."
done_when: >
  Phase 1 DONE: T265 Lô D (Admin duyệt 45 dòng CSV, gắn 118 quyết định) + T276 (2 điểm SPEC);
  Phase 2 DONE: BUG-032/033/031 + T274→T275→T270→T232 + 6 task độc lập (T50, T22, T121, T167, T266, T269) + T100, T73 + T277;
  Phase 3 DONE: QA kiểm toàn bộ, Admin xác nhận từng task, bàn giao tài liệu;
  docs/plans/GIAI_PHAP_TOI_UU_2026-10-11.md, docs/plans/T265_LO_D_CSV_WORKFLOW.md, docs/progress.md cập nhật theo tiến độ.
---

# T80 — Lô 1: hoàn thiện 17 task đang dở (3 Phase)

> **Admin phê chuẩn ngày 2026-10-11** — Giải pháp tối ưu 3 phase (~5 tuần, 25-30 ngày làm việc):
> - **Phase 1 (3-5 ngày):** T265 Lô D + T276
> - **Phase 2 (2-3 tuần):** Bug + 13 task Lô 1 song hành
> - **Phase 3 (1 tuần):** QA + bàn giao
> 
> Chi tiết: [docs/plans/GIAI_PHAP_TOI_UU_2026-10-11.md](../docs/plans/GIAI_PHAP_TOI_UU_2026-10-11.md) | CSV Workflow: [T265_LO_D_CSV_WORKFLOW.md](../docs/plans/T265_LO_D_CSV_WORKFLOW.md)

## Phạm vi

| Nhóm | Task |
|---|---|
| Dữ liệu & pipeline | T22 (founding date 59K places), T50 (CBETA cleanup), T272 (data curation pack v2), T277 (archive 230 file không dùng) |
| Truyền thừa / TTL | T270 (nối pháp TTL + Marcus), T274 (quy tắc TTL dòng Việt Nam), T275 (neo số đời từ TTL), T232 (tính số đời đa hệ) |
| Dịch & AI | T167 (engine dịch có ràng buộc), T266 (T74b Gemini draft), T269 (rules dịch Admin cho mọi AI) |
| Admin / UI / giao diện | T73 (review bio_vi), T100 (16 tab học thuật), T121 (Wikidata geo queue), T139 (Zen lineage gateway) |
| Quyết định & spec | T265 (H3 năm, 285 dòng CONFLICT), T276 (sửa SPEC T170 theo review) |

## Quy tắc chạy

1. Mỗi task: ghi mô tả bug/task trước khi sửa, backup file vào `daoanh/docs/sessions/YYYY-MM-DD/`.
2. Sửa code qua `daoanh-debugger` (hoặc `tich-hop` cho nguồn dữ liệu), kiểm chứng qua `daoanh-qa`.
3. Không tự đánh DONE. Chỉ đổi `status: done` sau khi Admin xác nhận.
4. Không git add/commit/push khi chưa có lệnh rõ ràng.

## Tiến độ

Xem [docs/plans/LO1_PLAN_2026-10-11.md](../docs/plans/LO1_PLAN_2026-10-11.md), mục "Tiến độ".
