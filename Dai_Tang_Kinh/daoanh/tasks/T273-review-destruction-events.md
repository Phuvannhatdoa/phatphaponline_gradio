---
id: T273
title: Rà soát 58 sự kiện hủy hoại (destruction events) t44_destruction_v2 cần xem
status: done
created: 2026-10-10
owner: claude-code
done_when: 58 dòng place_timeline_events (source=t44_destruction_v2, confidence=cung_menh_de_can_xem) đã được phân loại lại thành 3 nhóm (xác nhận / năm ước lượng / năm sai cần sửa), tổng place_timeline_events vẫn 4386, không dòng khác bị đổi.
revert: "UPDATE place_timeline_events SET confidence='cung_menh_de_can_xem', year=<giá trị cũ theo bảng backup trong docs/ROLLBACK.md> WHERE id IN (<58 id ghi trong báo cáo>)"
outcome: pending
done_at: "2026-10-10"
done_by: "Admin xác nhận 22 sự kiện năm ước lượng"
---

## 1. Bối cảnh

Admin đã duyệt đề xuất rà soát 58 sự kiện `place_timeline_events` có
`source='t44_destruction_v2'` và `confidence='cung_menh_de_can_xem'`.
Mục tiêu: phân loại lại theo câu gốc (label_zh) thành 3 nhóm, không đổi
dữ liệu khác, không xóa dòng.

## 2. Kế hoạch 3 nhóm (từ đề xuất đã duyệt)

- **Nhóm 1 — năm đúng (32 dòng):** giữ year, đặt
  `confidence='cung_menh_de_xac_nhan'`.
- **Nhóm 2 — năm ước lượng giữa niên hiệu (22 dòng):** giữ year, đặt
  `confidence='nam_uoc_luong'`. Nhận diện bằng câu gốc chứa
  中/間/初/末/年間/年中 (niên hiệu không có năm cụ thể).
- **Nhóm 3 — năm sai (4 dòng):** PL000000014762, PL000000014770,
  PL000000011841, PL000000057980 — đặt `year=NULL`,
  `confidence='nam_sai_can_sua'`, giữ nguyên label_zh.

## 3. Các bước

- [x] Backup DB (sqlite backup API) → data/backups/
- [x] Áp dụng UPDATE trong 1 transaction cho đúng 58 dòng theo 3 nhóm
- [x] Đếm lại theo confidence + verify tổng place_timeline_events=4386
- [x] Ghi docs/ROLLBACK.md (dòng mới + lệnh hoàn tác)
- [x] Ghi docs/sessions/2026-10-10_review-destruction.md
- [x] Thêm block T273 vào docs/tasktodo.md
- [x] Sửa scripts/build_t263_status.py đọc thêm checklist này vào "plan3"
- [x] Sửa dashboard/dashboard_process.html hiển thị plan3
- [x] Chạy lại dashboard build + node --check dashboard

Admin xác nhận DONE 2026-10-10. Lưu ý: PL000000003739 (năm 1864) đã được agent chuyển về nhóm xác nhận; Admin chưa ghi nhận riêng dòng này.
