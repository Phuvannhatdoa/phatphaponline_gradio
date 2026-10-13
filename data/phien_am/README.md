# Phiên âm Hán-Việt tên người DILA (Person Authority)

Nguồn: `Buddhist_Studies_Person_Authority.xml` (2026-10), 49.487 người; 49.335 người có tên Hán dùng được.
Mỗi người lấy 1 tên: `persName` chính (zho-Hant); chỉ khi thiếu mới lấy tên khác (3 người), tên chỉ có kana bị bỏ (1 người).

## Trạng thái: CHƯA THẨM ĐỊNH HỌC THUẬT
Âm từng chữ do mô hình (Claude) viết trực tiếp, sau đó **đối chiếu từng chữ** với
*Từ Điển Hán Việt* (Nguyễn Quốc Hùng) có trong repo `master`. Đây là đối chiếu máy, không thay thế người thẩm định.

| Tầng | Ý nghĩa | Số người |
|---|---|---|
| 1 | Mọi chữ có âm khớp từ điển, không còn chữ đa âm | 43.167 |
| 2 | Ghép được, nhưng ≥1 chữ không có trong từ điển (chưa đối chiếu đủ) | 910 |
| 3 | Còn chữ đa âm / lệch từ điển / âm đoán — **cần người duyệt** (cột `review`) | 4.711 |
| 4 | Còn chữ chưa có âm — `name_vi` để trống, bản dở ở `name_vi_partial` | 547 |

Đối chiếu bảng 4.297 chữ: 3.417 khớp, 184 lệch (giữ cả hai âm để duyệt), 204 không có trong từ điển,
30 âm đoán chưa chắc, 4 sửa theo từ điển (銳 Nhuệ, 戴 Đái, 瑾 Cẩn, 郝 Hác), 458 chưa có âm.

## Quy ước còn chờ chốt
- 慧: đang để **Huệ** (có thể Tuệ) — ~830 tên có chữ này, ghi chú trong `review`.
- 行 (Hạnh/Hành), 長, 藏, 梵, 沈… các chữ đa âm: đang lấy âm đầu, gắn cờ `review` kèm âm thay thế.
- Quy tắc ghép từ đã áp dụng (xem `<rule>` trong XML): 般若→Bát Nhã, 迦葉→Ca Diếp, 耶舍→Da Xá, 菩提→Bồ Đề,
  無著→Vô Trước, 相如→Tương Như, họ kép (司馬, 令狐, 耶律, 沮渠…).
- Tên Nhật/Hàn đọc theo Hán-Việt như tên Trung; chưa phân biệt.

## File
- `vn_person_name_vi.xml` — kết quả (`dila_id`, `name_zh`, `name_vi`, `tier`, `review`, `rule`).
- `review_needed.tsv` — tầng 3, 4 và các tên có 慧, để người duyệt lọc.
- `charmap_hanviet.tsv` — bảng chữ, âm đề xuất, âm từ điển, tình trạng đối chiếu.
- `import_name_vi.py` — nạp vào `vn_person_authority.name_vi` (chạy thử mặc định, chỉ điền ô trống, chỉ tầng 1-2, tự sao lưu khi `--apply`).
