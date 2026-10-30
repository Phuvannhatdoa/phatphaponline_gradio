---
id: T502
title: 534 alias lô B — tra từ điển 534 tên người theo so_lan (tách từ T455)
status: pending
created: 2026-10-30
updated: 2026-10-30
owner: daoanh-debugger
module: Data / Persons
priority: low
parent: T455
split_from: T455
plan_approved_at: "2026-10-30 (Admin duyệt T455 phương án A — phần 534 alias lô B tách riêng thành task này; chưa duyệt phương án triển khai.)"
done_when: >
  (1) Xuất CSV 534 dòng alias (đã có sẵn trong `people_name_vi_history` với `action='kept_alias'`,
      batch `T455-planA-20261030`) kèm `name_zh_catalog`, `name_vi_old` (ZQ), `name_vi_new` (Cloud), `so_lan`.
  (2) Chia 3 lô theo so_lan: L1 ≥ 20 lần (ưu tiên cao — chiếm phần lớn lượt hiển thị), L2 5–19, L3 < 5.
  (3) Tra từ điển từng dòng L1 (mẫu 20 dòng/lô trình Admin duyệt) → sửa `people.name_vi` theo tên chuẩn,
      ghi `people_name_vi_history` (action='updated'); KHÔNG sửa `people.name_zh`; source_id=5 (ZQLOCAL).
  (4) Backup DB → apply từng lô → verify → dòng ROLLBACK.md; daoanh-qa ĐẠT; Admin xác nhận DONE.
revert: >
  Khôi phục `people.name_vi` từ `people_name_vi_history.name_vi_old` cho các dòng của batch tương ứng.
---

## Mô tả
534/794 dòng có tên Việt ZQ **khác Cloud** theo *quy ước đọc cả từ* — **không phải lỗi kỹ thuật**:

| Kiểu | Ví dụ | Ghi chú |
|---|---|---|
| ZQ đọc theo **nghĩa chữ** | 龍樹 → "Long **Thụ**" · 著 → "Vô **Trứ**" · 般若 → "**Bàn Nhược**" | ZQ là máy phiên âm tự động (confidence 0,5) |
| Cloud đọc theo **cách gọi quen thuộc VN** | 龍樹 → "Long **Thọ**" · 著 → "Vô **Trước**" · 般若 → "**Bát Nhã**" | cách gọi phổ biến trong kinh lục Việt Nam |
| Chỉ khác **dấu gạch nối** | "Cưu Ma La Thập" vs "Cưu-ma-la-thập" | 64/534 dòng |

Đã **giữ nguyên theo ZQ** (phương án A) và ghi chú alias trong `people_name_vi_history` (`action='kept_alias'`) để sau này tra mà không mất thông tin.

### Trạng thái hiện tại (2026-10-30)
- **Đã làm**:
  - Đo: **478/534** dòng khác nhau ≤ 1 từ (sai 1 chữ âm đọc) · **64/534** chỉ khác gạch nối · **0/534** còn sót Hán
  - Đối chiếu `hanviet_char_map`: **không phân định được** (269 nghiêng ZQ / 314 nghiêng Cloud / 113 hòa) ⇒ không có bằng chứng tự động
  - Toàn bộ 534 dòng đã ghi trong `people_name_vi_history` (`action='kept_alias'`, `batch_id='T455-planA-20261030'`)
- **Chưa làm**: chưa chia lô theo `so_lan`; chưa tra từ điển dòng nào; chưa sửa dòng nào.
- **Đang chờ**: Admin duyệt cách chia lô + mẫu 20 dòng/lô.

### Vì sao không tự động quyết được?
`hanviet_char_map` là bảng đọc **một chữ theo nghĩa thông thường** (dùng cho địa danh: tự, chùa…), **không** có ngoại lệ theo cả từ. Với tên người Phật giáo, cách đọc cả từ khác hẳn:

| Chữ | charmap đọc | Đọc đúng trong tên Phật | Ai đúng? |
|---|---|---|---|
| 樹 | `thụ` | Long **Thọ** | Cloud |
| 畏 | `uý` | Thiện Vô **Úy** | Cloud |
| 著 | `trứ` | Vô **Trước** | Cloud |
| 頂 | `đỉnh` | Quán **Đảnh** | Cloud |
| 般若 | `bàn`/`Nhược` | **Bát Nhã** | Cloud |
| 錩 | `xuổng` | Phương Quảng **Cẩn** | Cloud |
| 閻 | `Diêm` | **Xà-na** Quật-đa | Cloud |

Chỉ 552/11.300 chữ (4,9 %) là đa âm — nhưng chính các chữ đa âm lại nằm trong tên ⇒ lỗi nằm ở tầng "đọc cả từ", không phải tầng "đọc chữ" ⇒ **cần người duyệt**.

### Tài liệu liên quan
- Báo cáo gốc T455: `docs/reports/T455-analysis-794-mismatch.md` (mục "Lô B")
- Báo cáo apply T455: `docs/reports/T455-apply-planA-report.md`
- Sổ undone: `docs/reports/UNDONE-2026-10-30.md` (mục A2)
- CSV 3 lô: `docs/sessions/2026-10-28-t455/name_vi_mismatch_B.csv` (534 dòng, có cột `so_lan`)

### Câu hỏi cần Admin quyết
1. Chia lô theo `so_lan` như đề xuất (L1 ≥ 20 / L2 5–19 / L3 < 5) OK chứ?
2. Có chấp nhận quy ước **Cloud** (cách gọi quen thuộc VN) làm chuẩn cho nhóm này không? Nếu không thì cần quy ước thứ 3 (tra từ điển thủ công 534 dòng).
3. Có tra từ điển song song 2 nguồn (chẳng hạn `Phật Tự Điển` + `Cồn Khúc Thế Tự Pháp Tính Từ Điển`) không, hay chỉ 1 nguồn?
