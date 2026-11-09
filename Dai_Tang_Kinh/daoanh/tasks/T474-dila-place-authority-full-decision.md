---
id: T474
title: "Nạp toàn bộ Place Authority DILA (117.847) vào bảng bổ sung; đánh dấu địa danh chưa phiên âm theo lô nguồn"
status: pending
created: 2026-10-26
updated: 2026-10-26
owner: coordinator
module: Data / Places / Authority
priority: medium
depends_on: [T368b, T443]
done_when: >
  (1) Đọc read-only file nguồn authority_place.2026-10/Buddhist_Studies_Place_Authority.xml (117.847 place); ghi SHA256 trước và sau.
  (2) Tạo bảng bổ sung `dila_place_authority` (additive) với các cột: place_id, name_zh, name_vi (có thể rỗng), translation_status (done/missing), source_file, batch_id, source_hash. KHÔNG ghi vào places_dila hay places cũ.
  (3) Nạp đủ 117.847 dòng. Dòng đã có bản Việt trong places_dila: đánh dấu done và trỏ về bản đó; dòng chưa có: name_vi rỗng, translation_status=missing.
  (4) Chia lô theo file nguồn hoặc khoảng place_id; xuất danh sách lô chưa phiên âm kèm tên file XML gốc để Admin upload cho Claude session phiên âm.
  (5) Dry-run báo cáo (số dòng, số done, số missing theo lô); backup DB; --apply sau khi Admin duyệt; có rollback.
  (6) Sau khi Claude session trả bản phiên âm: nạp lại theo place_id, không đổi place_id, không đổi name_zh.
  (7) daoanh-qa ĐẠT; Admin xác nhận DONE.
revert: >
  DROP bảng dila_place_authority (additive). Không đụng places_dila, places, places_pending.
---

## Đính chính 2026-10-26 (quan trọng)
- Con số 117.847 là số mọi thẻ `<place>` trong XML, không phải số địa danh. Số địa danh thật có `xml:id` duy nhất là **59.375**.
- Trong đó **59.167** đã có trong `places_dila`. Chỉ còn **208 địa danh mới** cần nạp.
- Vì vậy không có 58.680 dòng "thiếu" như mô tả cũ. Gói 23 file XML đã tạo nhầm đã bị xoá.
- Việc còn lại: xác định tên Việt cho các địa danh hiện có (kiểm trong `namevi_map_places`) và nạp 208 địa danh mới.

## Mô tả
Admin quyết định nạp toàn bộ 117.847 địa danh DILA vào PTDA. Địa danh nào đã có tên Việt trong `places_dila` (59.167) thì đánh dấu đã phiên âm. Địa danh chưa có tên Việt thì vẫn nạp tên gốc Hán (name_zh) và đánh dấu `missing`. Danh sách `missing` theo lô kèm tên file XML gốc để Admin upload cho Claude session phiên âm.

## Nguồn (đã có trên máy)
- `data/dila_import/authority_place.2026-10/Buddhist_Studies_Place_Authority.xml` (117.847 place).
- Bản trùng số lượng trong `data/dila_import/Authority-Databases-master/.../authority_place/`.

## Thiết kế
- Bảng mới `dila_place_authority` (additive). Lý do: `places_dila` đang nuôi màn hình HOME và tab Place; không đưa 58.680 dòng chưa phiên âm vào đó để tránh hiển thị tên thiếu.
- Khóa: place_id (không đổi).
- Trạng thái: `done` (đã có bản Việt) hoặc `missing` (chỉ có tên Hán).

## Phạm vi
- Trong: nạp, đánh dấu, xuất danh sách lô, nạp lại bản phiên âm sau khi Claude trả về.
- Ngoài: sửa `places_dila`, `places`, `places_pending`; sửa tọa độ; hiển thị ra HOME trước khi Admin duyệt.

## Rủi ro
- Nhiều dòng `missing` sẽ hiện trong tra cứu nội bộ nếu không lọc; cần lọc theo `translation_status` khi hiển thị.
- Tên Hán trùng nhau giữa các place_id khác nhau; khóa luôn là place_id.
