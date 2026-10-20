# T273 — Rà soát 58 sự kiện hủy hoại cần xem (2026-10-10)

## Bối cảnh

Admin duyệt đề xuất rà soát 58 dòng `place_timeline_events` có
`source='t44_destruction_v2' AND confidence='cung_menh_de_can_xem'`
(nhóm "cần xem" ghi lúc T44 lượt trước, chưa được xác nhận năm).

## Backup

- `data/backups/lineage.T273-review-20261010_184054.db` (`PRAGMA quick_check`='ok', tổng `place_timeline_events`=4386 trước sửa)
- Mapping 58 dòng trước sửa (id/dila_id/year/label_zh): `data/backups/T273_58rows_before.json`

## Phân loại

Dựa trên câu gốc `label_zh` (chữ Hán), không suy diễn thêm:

### Nhóm 1 — năm đúng, xác nhận (32 dòng) → `confidence='cung_menh_de_xac_nhan'`

Các dòng có năm cụ thể, rõ ràng trong câu gốc (ví dụ "咸豐五年（1855）", "會昌五年", "明弘治四年廢"...). Bao gồm cả `PL000000003739` (1864, "於清代同治三年（公元1864年）的大火中全都化為了灰燼") — ký tự 中 ở đây nghĩa là "giữa/trong [đám cháy]", không phải mốc niên hiệu mơ hồ, năm đã rõ qua 同治三年/公元1864年.

### Nhóm 2 — năm ước lượng giữa niên hiệu (22 dòng) → `confidence='nam_uoc_luong'`

Nhận diện bằng câu gốc chứa 中/間/初/末 gắn với tên niên hiệu (không có số năm cụ thể trong niên hiệu đó):

| dila_id | year (giữ) | label_zh |
|---|---|---|
| PL000000009158 | 843 | 會昌中廢 |
| PL000000011665 | 1544 | 明嘉靖年間寺廢 |
| PL000000012166 | 1891 | 可惜左塔已在清光緒年間圮廢 |
| PL000000012917 | 1544 | 明嘉靖中廢 |
| PL000000013059 | 1337 | 至元中燬 |
| PL000000013094 | 1544 | 嘉靖間廢 |
| PL000000014339 | 1122 | 宣和間燬 |
| PL000000014341 | 843 | 唐會昌中廢 |
| PL000000014713 | 843 | 唐會昌中廢 |
| PL000000014763 | 843 | 唐會昌中廢 |
| PL000000014782 | 843 | 會昌中廢 |
| PL000000017622 | 843 | 唐會昌年間（841-846）遭火劫荒廢 |
| PL000000019392 | 1544 | 明嘉靖中廢 |
| PL000000023594 | 843 | 會昌中廢 |
| PL000000042331 | 710 | 睿宗景雲中廢 |
| PL000000042418 | 622 | 唐武德初廢 |
| PL000000042430 | 611 | 大業中廢 |
| PL000000049633 | 843 | 唐會昌中廢 |
| PL000000057291 | 1856 | 咸豐年間又毀於大火 |
| PL000000057651 | 843 | 會昌中廢 |
| PL000000057758 | 1072 | 神宗熙寧末廢其院 |
| PL000000060273 | 1856 | 清咸豐中毀於兵火 |

Lưu ý: ban đầu máy phân loại theo chữ "中/間/初/末" đã bắt nhầm `PL000000003739`
vào nhóm này (do câu có chữ "大火中"). Đã rà lại và sửa về Nhóm 1 vì năm
1864 đã rõ ràng, không mơ hồ.

### Nhóm 3 — năm sai cần sửa (4 dòng) → `year=NULL`, `confidence='nam_sai_can_sua'`, giữ nguyên `label_zh`

| dila_id | year cũ | label_zh | lý do sai |
|---|---|---|---|
| PL000000014762 | 1413 | 永樂初廢 | 永樂 bắt đầu 1403, "初" (đầu niên hiệu) không khớp 1413 |
| PL000000014770 | 1383 | 國朝洪武初廢 | 洪武 bắt đầu 1368, "初" không khớp 1383 |
| PL000000011841 | 1354 | 至正末燬于兵 | 至正 kết thúc 1370, "末" (cuối niên hiệu) không khớp 1354 |
| PL000000057980 | 1354 | 至正末兵廢 | cùng lý do trên |

## Kết quả ghi DB

Transaction duy nhất, 58 UPDATE theo `id` (không đụng dòng khác):

```
source='t44_destruction_v2' theo confidence sau ghi:
  cung_menh_de           = 44  (không đổi, ngoài phạm vi)
  cung_menh_de_xac_nhan   = 32  (Nhóm 1)
  nam_uoc_luong           = 22  (Nhóm 2)
  nam_sai_can_sua         = 4   (Nhóm 3)
  tổng t44_destruction_v2 = 102 (không đổi)

place_timeline_events tổng = 4386 (không đổi)
```

## Tài liệu/dashboard đã cập nhật

- `docs/ROLLBACK.md` — dòng mới + lệnh hoàn tác dùng `data/backups/T273_58rows_before.json`
- `docs/tasktodo.md` — block `<!-- T273:START -->...<!-- T273:END -->`
- `scripts/build_t263_status.py` — đọc thêm checklist T273 vào khóa `plan3`
- `dashboard/dashboard_process.html` — hiển thị danh sách `plan3` cạnh plan hiện có

## Limitation / chưa chắc

- Ngưỡng "khoảng 18 dòng" Admin nêu cho Nhóm 2 thực tế là 22 dòng (sau khi rà
  đúng theo ký tự 中/間/初/末 trong niên hiệu) — admin cần xác nhận lại danh
  sách 22 dòng trên có đúng ý không.
- Nhóm 1 thực tế 32 dòng (ước tính Admin "khoảng 30").
- Chưa chạy lại UI (`places.html` Events tab) để xác nhận hiển thị không bị
  vỡ với `confidence` mới — nằm ngoài phạm vi 4 bước được giao (chỉ DB +
  docs + dashboard).
