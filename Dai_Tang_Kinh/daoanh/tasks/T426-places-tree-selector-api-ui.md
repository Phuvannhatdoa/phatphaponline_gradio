---
id: T426
title: "3 cây — Bước 5: API + giao diện chọn 'Cây DILA / Cây Marcus / Cây TTL / Chồng cây' trên /daoanh/places"
status: pending
created: 2026-10-19
updated: 2026-10-19
owner: code (Hermes giao)
parent: T422
module: Lineage / Generation
priority: high
depends_on: [T425]
dispatch: approved
plan_approved_at: "2026-10-19 (Admin: “3 cây trên HOME”: http://localhost:8080/daoanh/places, Tạo 5 task theo thứ tự trên: ok)"
db_write: "Không ghi DB (chỉ đọc VIEW)."
done_when: >
  (1) API `/daoanh/api/monk/<id>/lineage-tree?trees=dila,marcus,ttl&overlay=1` đọc VIEW T425; không truyền tham số thì giữ hành vi cũ.
  (2) Giao diện: bộ chọn 4 nút "Cây DILA / Cây Marcus / Cây TTL / Chồng cây"; nhãn nguồn trên cạnh và nút; chú thích theo T410 (màu theo nguồn).
  (3) Kiểm trình duyệt thật 2 nhân vật (A004980 Hưng Hóa Tồn Tưởng, A009460 Đơn Hà): ảnh 4 chế độ; cây TTL hiện được thiền sư không có DILA ID (ptda:).
  (4) daoanh-qa kiểm; Admin xác nhận DONE.
revert: >
  git revert, hoặc chép lại bản sao app.py, places.html (docs/sessions/<ngày>/*.bak-before-T426).
outcome: >
  2026-10-19: RC tạo task theo đánh giá DB, chưa làm.
---

# T426 — 3 cây — Bước 5: API + giao diện chọn "Cây DILA / Cây Marcus / Cây TTL / Chồng cây" trên /daoanh/places

## Mục tiêu

Trên http://127.0.0.1:8080/daoanh/places (chế độ Pháp hệ) người dùng chọn xem từng cây hoặc chồng cây; gộp với T410 (màu/nét/chú thích), T412 (tên TTL), T413 (trục chính).

Màn hình đích: http://127.0.0.1:8080/daoanh/places (chế độ Pháp hệ). Đặc tả: `docs/reports/DB-READINESS-3-TREES-2026-10-19.md` + `docs/reports/DILA-CANONICAL-MULTI-TREE-REVIEW-2026-10-19.md`.
Chuỗi 5 bước: T422 → T423 → T424 → T425 → T426. Liên quan: T410 (màu/nét), T412 (tên TTL), T413 (BUG-038), T414 (nối pháp), T415 (audit mapping TTL).

## Ràng buộc chung

Không xoá bảng cũ. Mọi ghi DB: chạy thử trước → Admin duyệt → backup SQLite API + quick_check → ghi → kiểm lại. Không tự gộp người, không tự tạo cạnh, không dùng bảng gộp / SNA làm nguồn. Không deploy, không push.

## Màu cạnh (Admin chốt 2026-10-19 07:02–07:03, chi tiết ở T410)

DILA = xanh · Marcus = vàng · TTL = đỏ · từ 2 nguồn trở lên ghi giống nhau (cùng ID thầy, trò) = "nhiều nguồn khớp": trắng/bạc trên nền tối, đen trên nền sáng (Admin 07:17, 07:25) · chưa rõ chiều = xám nét chấm.
Ở chế độ **Cây DILA / Marcus / TTL** mọi cạnh mang màu nguồn đó; ở **Chồng cây** màu theo bảng trên. Nét liền/đứt và
độ dày Main tree theo T410.

## Các bước

- [ ] API `/daoanh/api/monk/<id>/lineage-tree?trees=dila,marcus,ttl&overlay=1` đọc VIEW T425; không truyền tham số thì giữ hành vi cũ.
- [ ] Giao diện: bộ chọn 4 nút "Cây DILA / Cây Marcus / Cây TTL / Chồng cây"; nhãn nguồn trên cạnh và nút; chú thích theo T410 (màu theo nguồn).
- [ ] Kiểm trình duyệt thật 2 nhân vật (A004980 Hưng Hóa Tồn Tưởng, A009460 Đơn Hà): ảnh 4 chế độ; cây TTL hiện được thiền sư không có DILA ID (ptda:).
- [ ] daoanh-qa kiểm; Admin xác nhận DONE.
