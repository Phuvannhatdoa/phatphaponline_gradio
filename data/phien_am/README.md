# Phiên âm Hán-Việt tên người DILA (Person Authority) — âm Nam

Nguồn: `Buddhist_Studies_Person_Authority.xml` (2026-10), 49.487 người; 49.335 người có tên Hán dùng được.
Mỗi người lấy 1 tên: `persName` chính (zho-Hant); chỉ khi thiếu mới lấy tên khác (3 người); 1 người chỉ có kana bị bỏ.

## Trạng thái: CHƯA THẨM ĐỊNH HỌC THUẬT
Âm từng chữ do mô hình (Claude) viết trực tiếp, rồi đối chiếu máy với các từ điển có trong repo `master`:
*Từ Điển Hán Việt* (Nguyễn Quốc Hùng), *Từ Điển Thiền Tông Hán Việt* (Hân Mẫn, Thông Thiền),
*Danh Từ Thiền Học* (HT Duy Lực), *Phật Quang Từ Điển*, *Từ Điển Phật Học Đạo Uyển*.
Chưa dùng được: *Tiểu Sử Danh Tăng Việt Nam* (.doc nhị phân). Đối chiếu máy không thay thế người thẩm định.

| Tầng | Ý nghĩa | Số người |
|---|---|---|
| 1 | Mọi chữ có âm khớp từ điển (cho phép biến thể Bắc/Nam), không còn chữ đa âm chưa giải quyết | 45.418 |
| 2 | Ghép được nhưng ≥1 chữ không có trong từ điển (chưa đối chiếu đủ) | 616 |
| 3 | Còn chữ đa âm / lệch từ điển / âm đoán / lệch ở cấp tên — **admin cần duyệt** | 2.994 |
| 4 | Có chữ chưa có âm trong từ điển: dùng **âm ước lượng của mô hình** hoặc giữ nguyên chữ Hán — **admin cần duyệt** | 307 |

Tầng 3-4 vẫn có `name_vi` tạm để dùng trong lúc chờ duyệt (251 tên tầng 4 còn chứa chữ Hán chưa đọc được).
Danh sách duyệt: `review_needed.tsv` (3.301 dòng; cột `name_vi_da_duyet` để trống cho admin).

## Quy ước đã chốt
- 慧 = **Huệ**.
- **Âm Nam.** Gồm hai nhóm, ghi rõ nguồn trong `charmap_hanviet.tsv` (cột `tinh_trang`, `am_bac_goc`):
  - `am_nam_co_tu_dien` (17 chữ): âm Nam chiếm ≥60% với ≥3 mục trong từ điển Phật học của repo — 盛 Thạnh, 威 Oai, 命 Mạng,
    樹/受/授 Thọ, 座 Tọa, 嶺/領 Lãnh, 鏡 Cảnh, 宏 Hoằng, 廓 Quách, 操 Tháo, 迥 Quýnh, 焰 Diệm, 湊 Tấu, 激 Kích.
  - `am_nam_pho_bien_mo_hinh` (9 chữ): âm Nam phổ biến trong pháp danh miền Nam, **do mô hình bổ sung, không có số liệu từ điển trong repo**
    (thậm chí Thiền Tông Hán Việt dùng âm Bắc cho các chữ này) — 性 Tánh, 仁 Nhơn, 福 Phước, 眞/真 Chơn, 本 Bổn, 正 Chánh, 生 Sanh, 貴 Quới.
    Muốn đổi về Bắc, sửa các dòng này trong bảng chữ và chạy lại.
- Khác biệt Bắc/Nam trong từ điển không bị tính là lỗi (ghi `biến-thể-phương-ngữ`).

## Số liệu đối chiếu
- Cấp tên: 3.600 tên khớp đúng một cặp Hán–Việt trong từ điển; 1.967 tên có tiêu đề tiếng Việt trùng tiêu đề từ điển;
  217 tên chỉ khác biến thể phương ngữ; 44 tên tự sửa theo từ điển Phật học (白居易 Bạch Cư Dị, 康僧會 Khương Tăng Hội, 道場 Đạo Tràng…);
  25 tên lệch với từ điển tổng quát nhưng **không tự sửa** (ghi ở `review`, ví dụ 西施: mô hình Thí, từ điển Thi).
- Số khớp trực tiếp cấp tên giảm so với bản âm Bắc vì âm Nam khác âm từ điển ở các chữ trên.
- Tập tên có sẵn trong từ điển thiên về nhân vật nổi tiếng nên không đại diện cho cả 49 nghìn tên.
- Cấp chữ (4.297 chữ): 3.417 khớp, 184 lệch (giữ cả hai âm), 192 không có trong từ điển, 240 chữ rút âm từ từ ghép trong từ điển,
  39 chữ hiếm là **ước lượng của mô hình** (`mo_hinh_uoc_luong`, độ tin cậy thấp nhất), còn lại chưa có âm.

## Quy tắc ghép từ đã áp dụng (`<rule>` trong XML; do mô hình soạn, chưa có nguồn xác nhận độc lập)
般若→Bát Nhã, 迦葉→Ca Diếp, 耶舍→Da Xá, 菩提→Bồ Đề, 無著→Vô Trước, 相如→Tương Như, họ kép (司馬, 令狐, 耶律, 沮渠…).
Tên Nhật/Hàn đọc theo Hán-Việt như tên Trung; chưa phân biệt. Chữ đa âm (行, 長, 藏, 梵, 沈…): lấy âm đầu, `alternatives` liệt kê tổ hợp khác.

## File
- `vn_person_name_vi.xml` — kết quả (`dila_id`, `name_zh`, `name_vi`, `tier`, `review`, `evidence`, `rule`, `alternatives`).
- `review_needed.tsv` — tầng 3-4 để admin duyệt (UTF-8 BOM, mở được bằng Excel).
- `charmap_hanviet.tsv` — bảng chữ, âm sử dụng, tình trạng, âm Bắc gốc, âm trong từ điển.
- `import_name_vi.py` — nạp vào `vn_person_authority.name_vi`. Mặc định chạy thử, chỉ điền ô trống, nạp cả 4 tầng;
  `--tier-column <cột>` ghi thêm tầng để lọc dòng cần duyệt; tự sao lưu khi `--apply`.
