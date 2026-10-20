---
id: T353
title: "Kế hoạch M0–M5 và REALITY_CHECK — đối chiếu với trạng thái thật"
module: Plan
priority: p2
status: pending
created: 2026-10-10
updated: 2026-10-10
owner: claude-code
parent: docs/integration (phủ toàn bộ)
depends_on: [T322]
done_when: |
  Mỗi module M0–M5 có ghi trạng thái thật và trỏ tới task T283–T322 tương ứng. REALITY_CHECK có số liệu đo lại.
  Admin xác nhận DONE. Không tự đánh DONE.
revert: |
  Chỉ sửa tài liệu; sao lưu trước trong docs/sessions/2026-10-10/.
outcome: >
  2026-10-10: tạo để phủ các file kế hoạch còn lại. Chưa bắt đầu.
---

# T353 — Kế hoạch M0–M5 và REALITY_CHECK

## 1. Danh sách file phủ bởi task này

- `docs/integration/00_PLAN_OVERVIEW.md`
- `docs/integration/REALITY_CHECK.md`
- `docs/integration/M0_nen_dev_an_toan.md`
- `docs/integration/M1_source_hub_license_gate.md`
- `docs/integration/M2_dong_bo_authority.md`
- `docs/integration/M3_dia_ly_gps_crossref.md`
- `docs/integration/M4_doi_chieu_kinh_dien.md`
- `docs/integration/M5_ghi_nguon_tuan_thu.md`

## 2. Việc cần làm

- M1: đã có T231 (done). Ghi rõ 2 ETL còn lại (T287).
- M0: làm một phần. Ghi rõ T283–T286 còn lại.
- M2, M3, M4: chưa có code. Ghi rõ task blocked tương ứng (T293–T304).
- M5: có credits.html. Ghi rõ T290–T292.
- REALITY_CHECK và 00_PLAN: cập nhật số liệu đo lại (xem T322).

## 3. Ràng buộc

- Không xóa file. Không git commit/push.

## 4. Các bước

- [ ] **Bước 1 —** đối chiếu từng module với trạng thái thật
- [ ] **Bước 2 —** ghi trạng thái và task liên quan vào từng file
- [ ] **Bước 3 —** Admin xác nhận
