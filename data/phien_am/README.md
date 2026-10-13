# Phiên âm Hán-Việt tên người DILA (Person Authority)

Nguồn: `Buddhist_Studies_Person_Authority.xml` (2026-10), 49.487 người; 49.335 người có tên Hán dùng được.
Mỗi người lấy 1 tên: `persName` chính (zho-Hant); chỉ khi thiếu mới lấy tên khác (3 người); 1 người chỉ có kana bị bỏ.

## Trạng thái: CHƯA THẨM ĐỊNH HỌC THUẬT
Âm từng chữ do mô hình (Claude) viết trực tiếp, rồi đối chiếu máy với các từ điển có trong repo `master`:
*Từ Điển Hán Việt* (Nguyễn Quốc Hùng), *Từ Điển Thiền Tông Hán Việt* (Hân Mẫn, Thông Thiền),
*Danh Từ Thiền Học* (HT Duy Lực), *Phật Quang Từ Điển*, *Từ Điển Phật Học Đạo Uyển*.
Chưa dùng được: *Tiểu Sử Danh Tăng Việt Nam* (định dạng .doc nhị phân). Đối chiếu máy không thay thế người thẩm định.

| Tầng | Ý nghĩa | Số người |
|---|---|---|
| 1 | Mọi chữ có âm khớp từ điển, không còn chữ đa âm chưa giải quyết | 45.422 |
| 2 | Ghép được nhưng ≥1 chữ không có trong từ điển (chưa đối chiếu đủ) | 616 |
| 3 | Còn chữ đa âm / lệch từ điển / âm đoán / lệch ở cấp tên — **cần người duyệt** (cột `review`) | 3.005 |
| 4 | Còn chữ chưa có âm — `name_vi` để trống, bản dở ở `name_vi_partial` | 292 |

Chứng cứ cấp tên (phần tử `<evidence>`): 3.780 tên khớp đúng một cặp Hán–Việt trong từ điển;
2.134 tên có tiêu đề tiếng Việt trùng với tiêu đề trong từ điển. Phần lớn tên còn lại chỉ có chứng cứ cấp chữ.
Ghi chú đo lường: tập tên có sẵn trong từ điển thiên về nhân vật nổi tiếng, nên tỷ lệ khớp ở đó
**không** đại diện cho cả 49 nghìn tên. Tầng 1 nghĩa là từng chữ khớp từ điển, **không** phải cả tên đã được thẩm định.

Đối chiếu bảng 4.297 chữ: 3.417 khớp từ điển, 184 lệch (giữ cả hai âm), 192 không có trong từ điển,
240 chữ trước đây thiếu hoặc đoán nay rút âm từ các từ ghép trong từ điển, 242 chữ vẫn chưa có âm (hiếm, phần lớn xuất hiện 1 lần),
4 chữ sửa theo từ điển (銳 Nhuệ, 戴 Đái, 瑾 Cẩn, 郝 Hác).
Cấp tên: 48 tên tự sửa theo từ điển Phật học (ví dụ 白居易 Bạch Cư Dị, 康僧會 Khương Tăng Hội, 道場 Đạo Tràng);
35 tên chỉ khác biến thể phương ngữ; 23 tên lệch với từ điển tổng quát nhưng **không tự sửa** (ghi ở `review`, ví dụ 西施: mô hình Thí, từ điển Thi).

## Quy ước đã chốt
- 慧 = **Huệ** (người dùng chốt).

## Còn chờ quyết định
- Âm Bắc hay Nam: từ điển Thiền Tông Hán Việt dùng Thạnh/Oai/Mạng/Nhơn/Tánh; bản này dùng Thịnh/Uy/Mệnh/Nhân/Tính. Các khác biệt này không tính là lỗi (ghi `biến-thể-phương-ngữ`).
- 行 (Hạnh/Hành), 長, 藏, 梵, 沈… các chữ đa âm: đang lấy âm đầu; `alternatives` liệt kê các tổ hợp khác.
- Quy tắc ghép từ đã áp dụng (xem `<rule>`): 般若→Bát Nhã, 迦葉→Ca Diếp, 耶舍→Da Xá, 菩提→Bồ Đề, 無著→Vô Trước, 相如→Tương Như, họ kép (司馬, 令狐, 耶律, 沮渠…). Do mô hình soạn, chưa có nguồn xác nhận độc lập.
- Tên Nhật/Hàn đọc theo Hán-Việt như tên Trung; chưa phân biệt.

## File
- `vn_person_name_vi.xml` — kết quả (`dila_id`, `name_zh`, `name_vi`, `tier`, `review`, `evidence`, `rule`, `alternatives`).
- `review_needed.tsv` — tầng 3, 4 và các tên có ghi chú, để người duyệt lọc.
- `charmap_hanviet.tsv` — bảng chữ, âm đề xuất, tình trạng và âm trong từ điển.
- `import_name_vi.py` — nạp vào `vn_person_authority.name_vi` (chạy thử mặc định, chỉ điền ô trống, chỉ tầng 1-2, tự sao lưu khi `--apply`).
