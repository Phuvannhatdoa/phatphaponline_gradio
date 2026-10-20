---
id: T355
title: "BUG-033 — Số đời sai khi click node trước Đại Giám Huệ Năng (chain dài 48 entity)"
module: Lineage / places.html
priority: high
status: done
depends_on: []
created: 2026-10-11
updated: 2026-10-11
bug_id: BUG-033
done_when: >
  Mở URL chain dài (48 entity) với focus A010081 (Đại Giám Huệ Năng, đời thứ 33 theo Thiền tông).
  Click vào bất kỳ node nào trước Huệ Năng (ví dụ Hoằng Nhẫn, Phương Dụng, v.v.).
  Panel "Truyền Thừa" hiển thị số đời < 33 (vì node ở trên Huệ Năng).
  Screenshot trước/sau + network log API.
  Không regression trên các node khác.
---

# BUG-033 (T355) — Số đời tính sai khi click node trước Đại Giám Huệ Năng

## Triệu chứng (Admin báo)

**URL:** `http://localhost:8080/daoanh/places.html?mode=lineage&focus=A010081&lm=tree&chain=A001719%2CA003666%2CA004015%2CA016638%2CA019795%2CA019798%2CA019968%2CA001707%2CA005612%2CA009251%2CA010065%2CA010066%2CA010075%2CA010119%2CA010129%2CA010293%2CA011235%2CA014100%2CA019796%2CA019797%2CA019799%2CA019966%2CA019967%2CA019969%2CA019972%2CA019974%2CA019975%2CA019976%2CA019977%2CA019978%2CA025981%2CA025982%2CA025983%2CA025984%2CA025988%2CA025991%2CA025994%2CA025995%2CA025996%2CA025997%2CA025998%2CA025999%2CA026000%2CA026001%2CA026002%2CA026003%2CA040183%2CA009589`

**Root entity:** Đại Giám Huệ Năng (A010081), đời thứ 33 theo Thiền tông (Ma Ha Ca Diếp).

**Thao tác:** Click vào node trước Huệ Năng trong cây (ví dụ Hoằng Nhẫn, Phương Dụng, v.v.).

**Hiện tại:** Panel "Truyền Thừa Thiền Tông · Đời thứ N" trả số đời không chính xác (không < 33).

**Kỳ vọng:** Node ở trên Huệ Năng phải có số đời < 33 (vì Huệ Năng = 33 là con của chúng).

## Phạm vi dự kiến

- URL có 48 entity trong `chain` (dài bất thường so với T354 có 3 entity).
- Logic tính số đời có thể chỉ đúng cho chuỗi ngắn, sai cho chain dài / nhiều nhánh.
- Kiểm tra `generation_engine_v2.py` và `places-generation-v2.js` xem có xử lý sai chain dài không.

## Ràng buộc

- Không git add/commit/push.
- Test local dùng `127.0.0.1`, không dùng `localhost`.
- Bằng chứng bắt buộc: click thật trên UI + screenshot trước/sau + network log.
- Admin đã restart `app.py` rồi (từ sửa T354/BUG-032).
