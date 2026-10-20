---
id: T406B
title: "Đo lại JOIN places(name_zh) không-filter chậm hơn sau index (18,72s vs 3,64s) — xác nhận cache, không phải regression"
status: deferred
created: 2026-10-15
updated: 2026-10-19
owner: unassigned
parent: T405
module: Backend / DB performance
priority: low
depends_on: []
done_when: >
  (1) Đo lại phép `LEFT JOIN places g ON g.name_zh = p.name_zh` KHÔNG có điều kiện lọc (full-table join,
  đúng kiểu đo trong T405 outcome), lặp lại nhiều lần với cache OS ấm và lạnh, ghi rõ thời gian từng lần.
  (2) Xác nhận bằng EXPLAIN QUERY PLAN rằng idx_places_name_zh vẫn được dùng đúng cho truy vấn có điều kiện
  lọc thật (q=... như /daoanh/api/places/search) — đây là case thực tế dùng trong app, không phải case
  full-table không lọc.
  (3) Nếu xác nhận chênh lệch 18,72s/3,64s chỉ do cache, ghi kết luận vào task và đóng — không cần sửa code.
  (4) Nếu phát hiện index thật sự làm chậm một truy vấn thực tế nào khác (có điều kiện lọc, dùng trong route
  nào đó), ghi rõ route + câu query + đề xuất sửa (ví dụ composite index, query hint) — không tự sửa khi
  chưa có route thực tế bị ảnh hưởng.
  (5) Không tạo/xoá index khác ngoài phạm vi đo. daoanh-qa kiểm độc lập; Admin xác nhận DONE.
---

# T406B — Xác nhận JOIN không-filter chậm hơn sau index là do cache, không phải regression

## Nguồn phát hiện

Trong lúc đo T405 (`tasks/T405-places-name-zh-index.md`, outcome), phép đo "JOIN toàn bảng (không IN filter,
đúng kiểu T404 đo 'phép nối riêng')" cho kết quả: TRƯỚC 3,64s/514594 dòng, SAU 18,72s — chênh lệch được ghi
nhận là "do cache OS ấm/lạnh tại thời điểm đo, không ảnh hưởng kết luận EXPLAIN" nhưng chưa được xác nhận lại
bằng phép đo có kiểm soát.

## Vì sao tách task riêng

T405 đã đóng (Admin xác nhận DONE, mục tiêu chính — API places/search <2s — đã đạt và xác nhận bằng
EXPLAIN + curl). Việc đo lại full-table join không-filter không nằm trong done_when của T405 và không phải
route thực tế nào trong app dùng full-table join không điều kiện — nhưng cần xác nhận rõ để không bỏ sót
một regression thật nếu có.

## Các bước

- [ ] Đo lại JOIN không-filter 3-5 lần, cache ấm và lạnh riêng biệt, ghi log thời gian
- [ ] EXPLAIN QUERY PLAN cho truy vấn thực tế (có filter q=...) xác nhận vẫn dùng idx_places_name_zh
- [ ] Rà các route khác trong app.py có dùng JOIN places(name_zh) — kiểm có route nào chậm hơn không
- [ ] Ghi kết luận: cache hay regression thật; nếu regression thật, đề xuất task sửa riêng (không tự sửa)
- [ ] daoanh-qa kiểm độc lập
- [ ] Admin xác nhận DONE
