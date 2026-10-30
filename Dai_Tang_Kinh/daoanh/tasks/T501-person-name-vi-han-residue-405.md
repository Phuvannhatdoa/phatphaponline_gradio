---
id: T501
title: 405 tên người còn sót chữ Hán trong people.name_vi (tách từ T455)
status: pending
created: 2026-10-30
updated: 2026-10-30
owner: daoanh-debugger
module: Data / Persons
priority: medium
parent: T455
split_from: T455
plan_approved_at: "2026-10-30 (Admin duyệt T455 phương án A — phần 532 tên sót Hán tách riêng thành task này; chưa duyệt phương án triển khai)."
done_when: >
  (1) Đo lại số dòng `people.name_vi` còn chữ Hán (mục tiêu: 405 → 0) và xuất CSV bằng chứng.
  (2) Chọn nguồn âm cho nhóm này: (a) sinh bản dịch Cloud mới cho các bản không có trong 26 tạng authority_catalog;
      hoặc (b) đọc bằng `hanviet_char_map` cho chữ có trong bảng + tra tay cho chữ hiến; hoặc
      (c) chấp nhận hiển thị song song tên Hán + tên Việt (UI thay vì dữ liệu).
  (3) Sửa theo lô, mỗi lô Admin duyệt; additive: giữ giá trị cũ trong `people_name_vi_history`
      (bảng đã tạo ở T455), source_id ZQLOCAL=5 cho tên Việt (KHÔNG gán DILA); KHÔNG sửa `people.name_zh`.
  (4) Backup DB → apply → verify → dòng ROLLBACK.md; daoanh-qa ĐẠT; Admin xác nhận DONE.
revert: >
  Khôi phục `people.name_vi` từ `people_name_vi_history.name_vi_old` (bảng đã có sẵn từ T455 batch `T455-planA-20261030`).
---

## Mô tả
Sau khi T455 áp dụng phương án A (2026-10-30), `people.name_vi` còn **405** dòng chứa chữ Hán. Đây là phần **không** nằm trong danh sách 794 dòng lệch đã xử lý — vì nhóm này **không có bản dịch Cloud** để đối chiếu (bản dịch Cloud chỉ phủ 26 tạng của `authority_catalog`).

### Trạng thái hiện tại (2026-10-30)
- **Đã làm**:
  - Đo trước apply: **422** dòng còn Hán · sau apply: **405** (giảm 17 = đúng số chữ Hán đã sửa ở T455)
  - Xác nhận: **0** dòng còn Hán thuộc batch T455 → nhóm 405 này là việc riêng, không sót lại
  - T453/T454/T455/T457 đều **DONE**; pipeline `npm run pipeline` **exit 0**; `dup:ids` **PASS**
- **Chưa làm**: chưa xuất CSV bằng chứng 405 dòng; chưa chọn nguồn âm; chưa sửa dòng nào.
- **Đang chờ**: Admin chọn phương án (a) / (b) / (c) ở mục `done_when` (2).

### Vì sao không gộp vào T455?
T455 chốt ở phương án A: sửa 260 dòng **có bằng chứng đối chiếu** (lô A 22 + lô C 236), giữ 534 lô B ghi chú alias. 405 dòng này **không có bản dịch Cloud** để so ⇒ không có bằng chứng khách quan ⇒ tách riêng, đồng thời **không** chặn T456.

### Bối cảnh kỹ thuật
- Bảng đọc chuẩn của dự án: `hanviet_char_map` (11.300 chữ, 552 chữ đa âm) — đọc **một chữ theo nghĩa thường**, không có ngoại lệ theo cả từ ⇒ **không** dùng được cho tên người Phật giáo (`樹`→"thụ" nhưng Long 龍**樹** phải là "Thọ").
- Chữ hiến không có trong bảng đọc (tra ở T455): `昰 竑 玘 霰 丏 哌 鸖 晙 屾 僼 蜞 頔 璹 橖 涑` — cần tra tay hoặc sinh bản dịch.
- Bảng lịch sử sẵn có: `people_name_vi_history` (794 dòng từ T455, có cột `name_vi_old` / `lot` / `action` / `batch_id`).

### Tài liệu liên quan
- Báo cáo gốc T455: `docs/reports/T455-analysis-794-mismatch.md`
- Báo cáo apply T455: `docs/reports/T455-apply-planA-report.md`
- Sổ undone: `docs/reports/UNDONE-2026-10-30.md` (mục A1)
- Script đo dùng lại: `scripts/t455_verify_apply.py` (đếm Hán còn lại) · `scripts/t455_apply_planA.py` (mẫu apply + revert)

### Câu hỏi cần Admin quyết
1. Chọn nguồn âm: **(a)** sinh bản dịch Cloud mới · **(b)** `hanviet_char_map` + tra tay chữ hiến · **(c)** hiển thị song song Hán + Việt (không sửa dữ liệu)?
2. Nếu (a): có được dùng Cloud cho nhóm không có sẵn bản dịch không, hay phải dùng nguồn khác (giấy phép)?
