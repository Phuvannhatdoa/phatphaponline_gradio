---
id: T456
title: Autocomplete cho ô Search HOME (/daoanh/) — gợi ý kinh lục DILA, người, địa danh khi gõ
status: pending
created: 2026-10-22
updated: 2026-10-22
owner: daoanh-debugger
module: Frontend / Search
priority: high
parent: T453
depends_on: [T453, T416, T450]
plan_approved_at: "2026-10-22 (Admin: 'cho b thành tasknumber mới' — tạo task; triển khai cần duyệt phương án)."
done_when: >
  (1) Gõ ≥ 2 ký tự trong #heroSearch → dropdown gợi ý sau debounce ~200 ms, 3 nhóm có biểu tượng:
      📖 kinh (dila_catalog_works: title_vi/title_zh/cbeta_id), 🧘 người (people/dila_catalog_contributors),
      📍 địa danh (tái dùng /daoanh/api/public/autocomplete — T416/T450).
  (2) Mỗi gợi ý: tên Việt + tên Hán + mã; phím ↑/↓/Enter/Esc; click → hiện kết quả (không bắt buộc bấm "Tìm").
  (3) API gợi ý < 200 ms cho mọi chuỗi (đo bằng curl, như mốc T450); không LIKE '%q%' quét toàn bảng khi có FTS.
  (4) Không regression: bấm "Tìm" vẫn chạy như T453; luồng gõ-từng-ký-tự T404 không vỡ.
  (5) Backup app.py/index.html; lint/e2e PASS; daoanh-qa ĐẠT; Admin xác nhận DONE.
revert: >
  Khôi phục app.py/index.html từ docs/sessions/<ngày>/T456/*.bak; nếu tạo bảng FTS mới → DROP bảng đó (additive).
---

## Mô tả
Thêm gợi ý (autocomplete) cho ô Search trang chủ `/daoanh/`: khi gõ từ 2 ký tự, hiện dropdown ba nhóm — kinh lục DILA, người, địa danh — chọn bằng phím hoặc click. API gợi ý phải dưới 200 ms và không quét LIKE toàn bảng khi có FTS; luồng "Tìm" của T453 và gõ-từng-ký-tự của T404 phải giữ nguyên. Task phụ thuộc Gate 0 (khôi phục code backend DILA đã mất) và T450.

### Trạng thái hiện tại
- Đã làm: chốt phương án và điểm chạm code (`n4-plan.md`, mục T456); chưa có code.
- Chưa làm: Gate 0; đo timing và kiểm FTS5 trên bản copy DB; route `/daoanh/api/public/suggest`; UI dropdown; backup `app.py`/`index.html`; verify.
- Bị chặn bởi: Gate 0 — code backend DILA của T453 chưa từng được commit; khối route `/daoanh/api/public/dila_works` và khối DILA trong `api_global_search` chỉ còn trong backup `docs/sessions/2026-10-25/T445-coder/backup/app.py` (xem `docs/sessions/2026-10-26/gate0-report.md`). DB đã đủ bảng: `dila_catalog_works` 5.747 · `dila_catalog_contributors` 5.589 · `dila_catalog_places` 765. T450 đang pending.

### Câu hỏi cần Admin quyết
- Q1 (Gate 0, chặn T456): ai khôi phục code backend T453 từ backup T445-coder, khi nào, và có đưa lại luồng DILA lên HOME (đảo ngược T467) không? — chưa có đáp án.
- Q4a: tạo bảng FTS5 mới cho kinh lục (ghi DB, additive) hay chỉ dùng LIKE prefix (không ghi DB, chậm hơn)? — chưa có đáp án.
- Q4b: T450 (pending) làm trước, hay T456 đi trước? — chưa có đáp án.

# T456 — Autocomplete ô Search trang chủ

## Bối cảnh
T453 đưa 5.747 bộ kinh lục DILA (+ thẻ người, "Xem tất cả") lên ô Search HOME nhưng người dùng vẫn phải bấm "Tìm".
Admin yêu cầu gợi ý ngay khi gõ (2026-10-22).

## Phương án đề xuất
- Route mới `/daoanh/api/public/suggest?q=` trả `{works:[…≤5], people:[…≤5], places:[…≤5]}`.
- Kinh lục: FTS5 trên `dila_catalog_works(title_vi, title_zh, cbeta_id)` (bảng ảo additive `dila_catalog_works_fts`)
  hoặc prefix-index nếu FTS không khả thi — đo trước trên bản copy DB (như T450).
- Người: `people` + `dila_catalog_contributors` (ưu tiên người có tác phẩm trong kinh lục).
- Địa danh: gọi lại logic `/daoanh/api/public/autocomplete`.
- UI: dropdown dưới #heroSearch, cùng phong cách biểu tượng của panel T453.

## Câu hỏi cho Admin
1. Tạo bảng FTS5 mới cho kinh lục (ghi DB, additive) hay chỉ dùng LIKE prefix (không ghi DB, chậm hơn)?
