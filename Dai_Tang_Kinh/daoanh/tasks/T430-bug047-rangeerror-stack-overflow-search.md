---
id: T430
title: "Bug verify: BUG-047: RangeError stack overflow khi gõ 'Nghĩa Huyền' trong search (lineage mode)"
status: done
created: 2026-10-20
updated: 2026-10-20
done_when: "Gõ 'Nghĩa Huyền' trong search tại /daoanh/places?mode=lineage&focus=A003627&lm=tree không còn RangeError; console sạch; daoanh-qa xác nhận bằng browser thật."
---

## Triệu chứng

Route: `http://127.0.0.1:8080/daoanh/places?mode=lineage&focus=A003627&lm=tree`
Action: gõ "Nghĩa Huyền" vào ô search.

Console error:
```
RangeError: Maximum call stack size exceeded
  at VM30 places:7137:150
  at Array.reduce (<anonymous>)
  at w (VM30 places:7137:135)
  at VM30 places:7137:165
```

Infinite recursion ở hàm `w()` (minified, dòng 7137 của bundle runtime — cần map
về tên hàm thật trong `daoanh/places.html`), gọi lại chính nó qua `Array.reduce`.

## Nguyên nhân nghi ngờ

- Có thể là bug trong logic search/filter/sort (hàm đệ quy không có điều kiện dừng
  đúng, hoặc duyệt cây theo quan hệ cha-con bị cycle).
- Nghi vấn liên quan đến BUG-038/T424: TTL Lâm Tế Nghĩa Huyền nối nhầm A032162,
  có thể để lại cạnh vòng (A032162 → A003627 hoặc tương tự) trong
  `lineage_edge_assertions`, khiến hàm build-ancestor-spine hoặc search-expand
  đệ quy vô hạn khi gặp entity "Nghĩa Huyền".
- Cần kiểm tra: `lineage_edge_assertions` có cạnh self-loop hoặc cycle quanh
  A003627 / A032162 không; hàm JS nào trong `places.html` dùng `.reduce()` đệ quy
  khi search match tên "Nghĩa Huyền".

## Phạm vi dự kiến

- `daoanh/places.html` (hàm search/filter JS liên quan, dòng ~7137 bundle — tìm
  tên hàm thật trong source chưa minify nếu có, hoặc trace theo logic).
- Có thể liên quan `daoanh/app.py` nếu root cause là data trả về từ API có cycle.
- KHÔNG sửa data TTL gốc để vá — nếu root cause là data cycle trong DB
  (`lineage_edge_assertions`), sửa ở lớp resolver/DB theo đúng rule, không hard-code
  trong component.

## Việc cần làm

1. daoanh-debugger: mở browser thật, reproduce, audit root cause theo luồng
   raw data → DB → API → resolver → component → UI state. Xác định hàm `w()`
   thật là gì, có cycle data không, fix đúng lớp.
2. daoanh-qa: kiểm chứng bằng browser thật (click/gõ thật, screenshot trước/sau,
   network log), xác nhận không còn RangeError và không regression search/lineage
   khác (ví dụ case BUG-040/041 đã fix trước đó).
