---
id: T448
title: "Kế hoạch fix tuần tự bug UI/GIS (BUG-037 T412 → T416 autocomplete → QA T406)"
status: in_progress
created: 2026-10-21
updated: 2026-10-21
owner: null
module: UI / GIS / Places / Backend Perf
priority: high
depends_on: [T412, T416, T406]
dispatch: approved
plan_approved_at: "2026-10-21 (Admin: 'phê chuẩn đề xuất này... fix tuần tự các bug này')"
done_when: >
  (1) T412 (BUG-037): cây Pháp hệ hiện tên đầy đủ theo TTL (Mã Tổ Đạo Nhất),
      không có TTL mới dùng tên DILA — theo đúng done_when của T412, chỉ phần
      code (bước 1-4, KHÔNG ghi DB); phần sửa mapping DB trình Admin duyệt riêng.
  (2) T416: áp đề xuất (B) INDEXED BY hint tại app.py route autocomplete
      (code-only, không ghi DB); đề xuất (A) ANALYZE là DB write → trình Admin duyệt.
  (3) T406: daoanh-qa kiểm độc lập phần session khác đã sửa (flyTo isFinite guard)
      → trình Admin xác nhận DONE.
  (4) Mỗi bug: backup file trước khi sửa (docs/sessions/YYYY-MM-DD/), QA độc lập
      bằng daoanh-qa, Admin xác nhận DONE từng bug trước khi chuyển bug kế.
  (5) Revert được: git revert <sha> cho mỗi bug; không schema change khi chưa duyệt.
---

# T448 — Kế hoạch fix tuần tự bug UI/GIS (điều phối)

Admin phê chuẩn 2026-10-21: "fix tuần tự các bug này" theo đề xuất scan task undone.

## Thứ tự thực hiện + lý do

| # | Bug | Tình trạng thật khi khảo sát | Lý do thứ tự |
|---|-----|------------------------------|--------------|
| 1 | **T412 (BUG-037)** — tên node cây 2 chữ "Đạo Nhất" thay vì TTL full name "Mã Tổ Đạo Nhất" | `pending`, `dispatch: approved`, chưa ai làm | Bug hiển thị prominent, Admin ưu tiên high |
| 2 | **T416** — autocomplete 1–9s → <500ms | Phase profile ĐÃ XONG (outcome có root cause + đề xuất A/B); còn implement | Có sẵn phân tích, chỉ áp hint code |
| 3 | **T406** — flyTo NaN | Session khác đã sửa gần xong (checkbox 4/6); còn QA + Admin | Chỉ chạy QA độc lập, không đụng code |

## Tránh xung đột session song song

- T406: KHÔNG sửa code (session khác đang sở hữu) — chỉ chạy `daoanh-qa` đọc.
- T412: kiểm file đang được ai giữ trước khi sửa; backup trước.
- T416: chỉ sửa app.py route autocomplete; backup app.py trước.

## Quy trình từng bug (theo harness HARNESS_WORKFLOW.md)

1. Backup file → 2. daoanh-debugger sửa theo phạm vi file task → 3. daoanh-qa kiểm
độc lập → 4. trình Admin xác nhận DONE (pipip khi cần Admin) → 5. mới chuyển bug kế.

## Revert

Thuần git: `git revert <sha-từng-bug>`. Chi tiết từng con sẽ ghi vào
`docs/ROLLBACK.md` khi commit. T416 nếu áp (A) ANALYZE: phải backup DB + ghi
`docs/ROLLBACK.md` trước (ANALYZE chỉ ghi sqlite_stat1, additive, không mất data).
