---
id: T411
bug_id: BUG-036
title: "Bug verify: BUG-036: Pane 'Nguồn & chứng cứ' — bỏ danh sách chữ 'Nguồn truyền thừa (Y-fork)' rối, chỉ thể hiện bằng màu trên cây"
status: done
created: 2026-10-15
updated: 2026-10-20
owner: code (Hermes giao)
module: Nexus Visualization
priority: medium
depends_on: [T410]
dispatch: approved
plan_approved_at: "2026-10-15 (Admin: 'đoạn thông tin này nhìn rất là rối, không thể cung cấp dạng thuần túy kĩ thuật như vậy được. Hãy thể hiện bằng màu sắc trên bản đồ là được … thể hiện thông tin truyền thừa bằng màu sắc này là được')"
done_when: >
  (1) Pane phải "Nguồn & chứng cứ" không còn khối "Nguồn truyền thừa (Y-fork)" liệt kê từng cạnh dạng
  "nhận pháp từ / truyền cho … · Tím (Marcus+DILA) (2/4: Marcus, DILA)" (hàm `_t381PersonYForkBadges` ~dòng 6624,
  được đẩy vào pane tại ~dòng 8363).
  (2) Thông tin nguồn truyền thừa vẫn đọc được bằng màu nét trên cây (theo bảng 3 màu theo số nguồn, T410) + chú thích 3 màu ở panel
  trái; tooltip khi rê chuột lên cạnh vẫn giữ (nếu Admin không yêu cầu bỏ).
  (3) Các mục khác của pane "Nguồn & chứng cứ" (tiểu sử nguồn DILA, trích dẫn…) giữ nguyên, không lỗi bố cục.
  (4) Bằng chứng trình duyệt thật trên route Admin báo (A004980): ảnh trước/sau; grep places.html không còn tiêu đề
  "Nguồn truyền thừa (Y-fork)"; console không lỗi JS mới.
  (5) daoanh-qa kiểm độc lập; Admin xác nhận DONE.
revert: >
  git revert --no-edit <sha_T411>, hoặc chép lại docs/sessions/<ngày>/places.html.bak-before-T411.
outcome: >
  2026-10-15: RC kiểm hiện trạng (chỉ đọc), tạo task. Chưa sửa.
  2026-10-19: Admin gửi lại yêu cầu "Bug verify: BUG-036" với route case khác (focus=A009460).
  Giao daoanh-debugger sửa, daoanh-qa kiểm độc lập.
---

# T411 / BUG-036 — Bỏ danh sách chữ "Nguồn truyền thừa (Y-fork)" ở pane phải

## Mục tiêu

Admin thấy khối liệt kê từng cạnh thầy–trò kèm tên màu và "2/4: Marcus, DILA" quá kỹ thuật, rối. Thông tin này chỉ cần
thể hiện bằng **màu nét trên cây** (3 màu theo số nguồn, xem T410).

## Hiện trạng (RC kiểm 2026-10-15, chỉ đọc)

Route: `http://127.0.0.1:8080/daoanh/places?mode=lineage&focus=A004980&lm=tree&chain=…` — pane phải có khối
"Nguồn truyền thừa (Y-fork)" (thấy trong ảnh `docs/sessions/2026-10-15/BUG-035-036/before-A004980.jpg`).

| Chỗ | Vị trí (places.html) |
|---|---|
| Hàm dựng khối chữ | `_t381PersonYForkBadges(pid)` ~6624–6646 |
| Nơi chèn vào pane | `ev.push(_t381PersonYForkBadges(pid));` ~8363 |

Gợi ý cách làm: bỏ dòng `ev.push(...)` (và hàm nếu không còn ai gọi). Cân nhắc giữ **một dòng ngắn** chỉ khi có cạnh chỉ
1 nguồn, ví dụ "⚠ Có cạnh chỉ 1 nguồn ghi nhận — xem nét đứt trên cây" — chỉ làm nếu Admin đồng ý (hỏi trong báo cáo).

## Mặc định đã ghi (2026-10-15 03:46)

Câu "giữ 1 dòng cảnh báo ngắn khi có cạnh chỉ 1 nguồn?" Admin chưa trả lời ⇒ mặc định **bỏ hẳn** (không giữ dòng cảnh
báo). Admin đổi ý thì báo lại trước khi Hermes làm.

## Phạm vi

Được sửa: `places.html` (khối pane nguồn). Cấm: ghi DB, sửa app.py, deploy, push. Làm sau T410 (cùng file).
Sao lưu trước khi sửa vào `docs/sessions/<ngày>/places.html.bak-before-T411`.

## Các bước

- [x] RC kiểm hiện trạng + chụp ảnh trước (2026-10-15)
- [ ] Sao lưu places.html
- [ ] Bỏ khối "Nguồn truyền thừa (Y-fork)" khỏi pane
- [ ] Ảnh sau + grep + console sạch
- [ ] daoanh-qa kiểm độc lập
- [ ] Admin xác nhận DONE
