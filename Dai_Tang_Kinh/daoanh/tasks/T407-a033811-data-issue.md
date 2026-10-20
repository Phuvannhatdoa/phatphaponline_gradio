---
id: T407
title: "A033811: name_vi='Lâm Tế Tông' nhưng name_zh='大慧' (lệch nguồn/identity)"
status: pending
created: 2026-10-15
updated: 2026-10-15
owner: unassigned
parent: T404
module: Data / Identity
priority: medium
depends_on: []
done_when: >
  (1) Xác định đúng lớp lỗi: entity_claims của A033811 có name_vi="Lâm Tế Tông" (ZQLOCAL, source_id=5)
  ghép với name_zh="大慧" (DILA, source_id=1) — kiểm xem đây là lỗi crosswalk/mapping (hai record khác nhau
  bị gán cùng ID), lỗi ZQ phiên âm sai nguồn, hay bản ghi DILA gốc đã sai.
  (2) Trace raw data gốc: DILA A033811 thật sự tên gì (name_zh gốc), và ZQ đã phiên âm name_vi từ đâu — không
  đoán, phải tra ngược nguồn.
  (3) Fix tại đúng lớp (DB crosswalk/mapping nếu lỗi join; KHÔNG sửa raw DILA TTL nếu lỗi là do raw đổi; KHÔNG
  hard-code lại name_vi/name_zh trong component để vá hiển thị).
  (4) Không merge/suy theo tên — nếu cần sửa join key, dùng ID DILA ổn định, không dùng tên làm khoá.
  (5) Kiểm case khác tương tự (homonym "Lâm Tế" nhiều ID) không bị ảnh hưởng ngoài ý muốn.
  (6) daoanh-qa kiểm độc lập; Admin xác nhận DONE.
---

# T407 — A033811: name_vi/name_zh lệch nguồn

## Nguồn phát hiện

Ghi nhận ngoài phạm vi khi làm T404 (places.html autocomplete): `tasks/T404-places-search-autocomplete-jank.md`
mục "Phát hiện ngoài phạm vi" #3 — khi gõ "Lâm Tế" trong autocomplete, một dòng gợi ý A033811 hiển thị
`name_vi="Lâm Tế Tông"` nhưng `name_zh="大慧"` (Đại Huệ — một pháp hiệu khác, không liên quan "Lâm Tế").

## Phạm vi điều tra (chưa biết root cause, audit trước)

- Query `entity_claims`/bảng liên quan cho `dila_id='A033811'` xem có bao nhiêu claim name_vi/name_zh,
  nguồn nào (source_id), thời điểm ghi.
- Đối chiếu DILA Authority gốc cho A033811 (tên Hán thật).
- Đối chiếu bảng crosswalk/namevi_map xem có nhầm join giữa hai ID khác nhau không.

## Ràng buộc

Không sửa raw DILA/TTL để vá UI. Không dùng LLM đoán/dịch lại tên. Không hard-code display value trong
places.html hay component khác — sửa từ DB/API lên nếu xác định được lỗi ở lớp mapping.

## Các bước

- [ ] Audit: query DB cho A033811, trace nguồn từng field name_vi/name_zh
- [ ] Xác định lớp lỗi (data/mapping/crosswalk)
- [ ] Backup bảng liên quan trước khi sửa (nếu sửa DB)
- [ ] Fix đúng lớp, kiểm case tương tự không regression
- [ ] daoanh-qa kiểm độc lập
- [ ] Admin xác nhận DONE
