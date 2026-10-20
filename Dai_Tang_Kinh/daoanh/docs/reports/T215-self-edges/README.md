# T215 — Hồ sơ 9 cạnh tự nối

Ngày kiểm: 2026-10-02. Đây là đề xuất có bằng chứng, chưa apply TTL/DB. Số đời mọi case giữ nguyên.

Kế hoạch: [T215](../../../tasks/T215-dila-ttl-evidence-and-self-edges.md).

## Diên Phúc Tuệ Thăng

- File: TS-Dien-Phuc-Tue-Thang.ttl
- Subject tự nối: `dien_phuc_tue_thang`
- DILA đề xuất: A008431 — 延福慧升
- Trạng thái: Có căn cứ đề xuất quan hệ; cần kiểm ánh xạ DB

### Chi tiết sai trong file

```ttl
# dòng 6
<ex:monk/dien_phuc_tue_thang> a <bkg:Monk> ;
# dòng 7
rdfs:label "Diên Phúc Tuệ Thăng"@vi ;
# dòng 8
crm:P1_is_identified_by <ex:monk/dien_phuc_tue_thang> ;
# dòng 25
bkg:generationOrder 50;
# dòng 26
bkg:hasTeacher <ex:monk/dien_phuc_tue_thang> ,
# dòng 32
<ex:monk/dien_phuc_tue_thang> rdfs:label "Dục Vương Đoan Dụ"@vi .
# dòng 33
<ex:monk/tinh_tu_su_nhat> rdfs:label "Tịnh Từ Sư Nhất"@vi .
# dòng 34
<ex:monk/dao_trang_phap_toan> rdfs:label "Đạo Tràng Pháp Toàn"@vi .
# dòng 35
<ex:monk/thanh_luong_than> rdfs:label "Thanh Lương Thản"@vi .
```

### Căn cứ và đề nghị cập nhật

DILA ghi 延福慧升 là pháp tự 佛智端裕; hai trang xác nhận hai chiều. Backup T211 cho thấy target và nhãn của thầy đã bị đổi cùng URI chính.

Khôi phục target hasTeacher về duc_vuong_doan_du và nhãn Dục Vương Đoan Dụ; ánh xạ người chính tới A008431, thầy A007993 sau khi kiểm tra tác động DB. Chỉ sửa vị trí subject/định danh của người chính, không thay toàn bộ URI trong file.

Giữ nguyên; chưa có 3 dữ liệu độc lập chứng minh số hiện tại sai và số thay thế đúng.

- [DILA A008431](https://authority.dila.edu.tw/person/search.php?aid=A008431)
- [DILA A007993](https://authority.dila.edu.tw/person/search.php?aid=A007993)

Hash UTF-8 SHA256: `1edefd87cc1fbc8098766156e1917d1ea19cf8e8b811bc28db59607e8e2999dd`

## Động Sơn Trạch Ngôn

- File: TS-Dong-Son-Trach-Ngon.ttl
- Subject tự nối: `dong_son_pham_ngon`
- DILA đề xuất: A020683 — 洞山擇言
- Trạng thái: Đề xuất có điều kiện; ánh xạ local khác DILA chính thức

### Chi tiết sai trong file

```ttl
# dòng 6
<ex:monk/dong_son_pham_ngon> a <bkg:Monk> ;
# dòng 7
rdfs:label "Động Sơn Trạch Ngôn"@vi ;
# dòng 8
crm:P1_is_identified_by <ex:monk/dong_son_pham_ngon> ;
# dòng 23
bkg:generationOrder 48;
# dòng 24
bkg:hasTeacher <ex:monk/dong_son_pham_ngon> ;
# dòng 27
<ex:monk/bao_phuoc_ban_quyen> rdfs:label "Tuệ An Tuệ Uyên"@vi .
# dòng 28
<ex:monk/hoang_long_hue_nam> rdfs:label "Hoàng Long Huệ Nam"@vi .
# dòng 29
<ex:monk/lac_dam_khac_van> rdfs:label "Lặc Đàm Khắc Văn"@vi .
# dòng 30
<ex:monk/dong_son_pham_ngon> rdfs:label "Đông Sơn Phạm Ngôn"@vi .
```

### Căn cứ và đề nghị cập nhật

DILA của 梵言 liệt kê 擇言 là đệ tử và liên kết A020683; index chính thức nêu alias 洞山擇言. Trang riêng A020683 không fetch được qua web tool.

Đề xuất đổi subject/P1 thành dong_son_trach_ngon; giữ hasTeacher dong_son_pham_ngon. DILA chính thức đề xuất A020683 cho trò, A020673 cho thầy; không dùng A010985/A021072 local trước khi xác minh ánh xạ và nội dung tiểu sử.

Giữ nguyên; chưa có 3 dữ liệu độc lập chứng minh số hiện tại sai và số thay thế đúng.

- [DILA A020673](https://authority.dila.edu.tw/person/search.php?aid=A020673)
- [DILA A020683](https://authority.dila.edu.tw/person/search.php?aid=A020683)

Hash UTF-8 SHA256: `384ab7bb9bfd1526880e3a218e874195788452b11571109d1ea9561da2ec3aa7`

## Tiến Phước Trạch Sùng

- File: TS-Tien-Phuoc-Trach-Sung.ttl
- Subject tự nối: `hoang_long_duc_phung`
- DILA đề xuất: A020706 — 薦福擇崇
- Trạng thái: Ứng viên có căn cứ DILA; cần khóa danh tính TTL

### Chi tiết sai trong file

```ttl
# dòng 6
<ex:monk/hoang_long_duc_phung> a <bkg:Monk> ;
# dòng 7
rdfs:label "Hoàng Long Đức Phùng"@vi ;
# dòng 8
crm:P1_is_identified_by <ex:monk/hoang_long_duc_phung> ;
# dòng 45
bkg:generationOrder 50;
# dòng 46
bkg:hasTeacher <ex:monk/hoang_long_duc_phung> ;
# dòng 49
<ex:monk/hoang_long_ngo_tan> rdfs:label "Hoàng Long Ngộ Tân"@vi .
# dòng 50
<ex:monk/tien_phuoc_trach_sung> rdfs:label "Tiến Phước Trạch Sùng"@vi .
# dòng 51
<ex:monk/co_son_tang_tuan> rdfs:label "Cổ Sơn Tăng Tuân"@vi .
# dòng 52
<ex:monk/pho_hien_nguyen_to> rdfs:label "Phổ Hiền Nguyên Tố"@vi .
# dòng 53
<ex:monk/duy_thanh_linh_nguyen> rdfs:label "Duy Thanh Linh Nguyên"@vi .
```

### Căn cứ và đề nghị cập nhật

DILA ghi 薦福擇崇 và thầy 德逢, liên kết A014665. TTL hiện chủ thể Hoàng Long Đức Phùng tự nhận mình làm thầy.

Đề xuất subject/P1 tien_phuoc_trach_sung, tên chính Tiến Phước Trạch Sùng; giữ hasTeacher hoang_long_duc_phung (A014665). Chưa áp dụng vì cần đối chiếu tiểu sử TTL với alias 薦福擇崇; không chỉ dựa tên file.

Giữ nguyên; chưa có 3 dữ liệu độc lập chứng minh số hiện tại sai và số thay thế đúng.

- [DILA A020706](https://authority.dila.edu.tw/person/search.php?aid=A020706)

Hash UTF-8 SHA256: `fcc27b112cec236139e6874a37e6f9f31040df8160f170a5e19193db684da1cb`

## Hưng Hóa Nhân Nhạc

- File: TS-Hung-Hoa-Nhan-Nhac.ttl
- Subject tự nối: `hung_hoa_nhan_nhac`
- DILA đề xuất: A014436 — 興化仁岳
- Trạng thái: Danh tính DILA có căn cứ; DB local mâu thuẫn

### Chi tiết sai trong file

```ttl
# dòng 6
<ex:monk/hung_hoa_nhan_nhac> a <bkg:Monk> ;
# dòng 7
rdfs:label "Hưng Hóa Nhân Nhạc"@vi ;
# dòng 8
crm:P1_is_identified_by <ex:monk/hung_hoa_nhan_nhac> ;
# dòng 47
bkg:generationOrder 45;
# dòng 48
bkg:hasTeacher <ex:monk/phu_son_phap_vien> ;
# dòng 49
bkg:hasDisciple <ex:monk/hung_hoa_nhan_nhac> ,
# dòng 54
<ex:monk/huong_nghiem_dong_phu> rdfs:label "Hương Nghiêm Động Phu"@vi .
# dòng 55
<ex:monk/the_thang_ke_sieu> rdfs:label "Thê Thắng Kế Siêu"@vi .
# dòng 56
<ex:monk/truong_khanh_tue_xiem> rdfs:label "Trường Khánh Tuệ Xiêm"@vi .
# dòng 57
<ex:monk/ban_giac_nha_chau> rdfs:label "Bản Giác Nhã Châu"@vi .
# dòng 58
<ex:monk/dinh_lam_tue_sam> rdfs:label "Định Lâm Tuệ Sâm"@vi .
# dòng 59
<ex:monk/thu_son_xu_khe> rdfs:label "Thủ Sơn Xử Khuê"@vi .
# dòng 60
<ex:monk/hung_hoa_thieu_thanh> rdfs:label "Hưng Hóa Thiệu Thanh"@vi .
# dòng 61
<ex:monk/hung_hoa_nhan_nhac> rdfs:label "Hưng Hóa Nhân Nhạc"@vi .
# dòng 62
<ex:monk/diep_huyen_quy_tinh> rdfs:label "Diệp Huyện Quy Tỉnh"@vi .
```

### Căn cứ và đề nghị cập nhật

DILA A014436 ghi 興化仁岳 là pháp tự 法遠, liệt kê 紹清、景芳、處珪; không có bản thân 仁岳.

Đề xuất loại phần tử hung_hoa_nhan_nhac khỏi hasDisciple, giữ các trò khác có căn cứ; không tự thêm đệ tử. Xác minh lại VPA trước đồng bộ vì slug này đang mang tên Định Lâm Cảnh Phượng và chưa có DILA ID. Thầy Phù Sơn Pháp Viễn A004017 đã được DILA xác nhận.

Giữ nguyên; chưa có 3 dữ liệu độc lập chứng minh số hiện tại sai và số thay thế đúng.

- [DILA A014436](https://authority.dila.edu.tw/person/search.php?aid=A014436)
- [DILA A004017](https://authority.dila.edu.tw/person/search.php?aid=A004017)

Hash UTF-8 SHA256: `1aecae0dc00e6e1dcec1712a2c6a2e15474ceba93e457c6a5362410e8dd11901`

## Phần Dương Thiện Chiêu

- File: TS-Phan-Duong-Thien-Chieu.ttl
- Subject tự nối: `phan_duong_thien_chieu`
- DILA đề xuất: A004984 — 汾陽善昭
- Trạng thái: Quan hệ đề xuất đã đối chiếu DILA hai chiều

### Chi tiết sai trong file

```ttl
# dòng 6
<ex:monk/phan_duong_thien_chieu> a <bkg:Monk> ;
# dòng 7
rdfs:label "Phần Dương Thiện Chiêu"@vi ;
# dòng 8
crm:P1_is_identified_by <ex:monk/phan_duong_thien_chieu> ;
# dòng 330
bkg:generationOrder 43;
# dòng 331
bkg:hasTeacher <ex:monk/phan_duong_thien_chieu> ;
# dòng 332
bkg:hasDisciple <ex:monk/thach_suong_so_vien> ,
# dòng 344
<ex:monk/thach_suong_so_vien> rdfs:label "Thạch Sương Sở Viên"@vi .
# dòng 345
<ex:monk/nam_vien_hue_ngung> rdfs:label "Nam Viện Huệ Ngung"@vi .
# dòng 346
<ex:monk/thai_tu_dao_nhat> rdfs:label "Thái Tử Đạo Nhất"@vi .
# dòng 347
<ex:monk/thien_thanh_hao_thai> rdfs:label "Thiên Thánh Hạo Thái"@vi .
# dòng 348
<ex:monk/long_dam_tri_vien> rdfs:label "Long Đàm Trí Viên"@vi .
# dòng 349
<ex:monk/long_mon_chieu> rdfs:label "Long Môn Chiếu"@vi .
# dòng 350
<ex:monk/long_hoa_hieu_ngu> rdfs:label "Long Hoa Hiểu Ngu"@vi .
# dòng 351
<ex:monk/phap_hoa_toan_cu> rdfs:label "Pháp Hoa Toàn Cử"@vi .
# dòng 352
<ex:monk/ba_tieu_coc_tuyen> rdfs:label "Ba Tiêu Cốc Tuyền"@vi .
# dòng 353
<ex:monk/lang_nha_tue_giac> rdfs:label "Lang Nha Tuệ Giác"@vi .
# dòng 354
<ex:monk/dai_ngu_thu_chi> rdfs:label "Đại Ngu Thủ Chi"@vi .
# dòng 355
<ex:monk/thach_suong_phap_vinh> rdfs:label "Thạch Sương Pháp Vĩnh"@vi .
```

### Căn cứ và đề nghị cập nhật

DILA của 善昭 nêu thầy 省念; trang 省念 nêu đệ tử 善昭. Alias đầy đủ 汾陽善昭, 首山省念.

Thay duy nhất target hasTeacher phan_duong_thien_chieu bằng thu_son_tinh_niem; xác minh endpoint tương ứng A004983. Giữ số đời 43.

Giữ nguyên; chưa có 3 dữ liệu độc lập chứng minh số hiện tại sai và số thay thế đúng.

- [DILA A004984](https://authority.dila.edu.tw/person/search.php?aid=A004984)
- [DILA A004983](https://authority.dila.edu.tw/person/search.php?aid=A004983)

Hash UTF-8 SHA256: `44046af67af3bb5d76a53b02da2c85c274ddb8ad0636f303ea670c64c62ad6eb`

## Quảng Tuệ Nguyên Liên

- File: TS-Quang-Tue-Nguyen-Lien.ttl
- Subject tự nối: `quang_tue_nguyen_lien`
- DILA đề xuất: A014349 — 廣慧元璉
- Trạng thái: Quan hệ đề xuất đã đối chiếu DILA hai chiều

### Chi tiết sai trong file

```ttl
# dòng 6
<ex:monk/quang_tue_nguyen_lien> a <bkg:Monk> ;
# dòng 7
rdfs:label "Quảng Tuệ Nguyên Liên"@vi ;
# dòng 8
crm:P1_is_identified_by <ex:monk/quang_tue_nguyen_lien> ;
# dòng 105
bkg:generationOrder 43;
# dòng 106
bkg:hasTeacher <ex:monk/quang_tue_nguyen_lien> ;
# dòng 107
bkg:hasDisciple <ex:monk/hoa_nghiem_dao_long> ,
# dòng 113
<ex:monk/hoa_nghiem_dao_long> rdfs:label "Hoa Nghiêm Đạo Long"@vi .
# dòng 114
<ex:monk/tue_luc_tue_nam> rdfs:label "Tuệ Lực Tuệ Nam"@vi .
# dòng 115
<ex:monk/quang_tue_duc_tuyen> rdfs:label "Quảng Tuệ Đức Tuyên"@vi .
# dòng 116
<ex:monk/van_cong_duong_uc> rdfs:label "Cư Sĩ Văn Công Dương Ức"@vi .
# dòng 117
<ex:monk/nhuan_vuong_xu_binh> rdfs:label "Nhuận Vương Xứ Bình"@vi .
# dòng 118
<ex:monk/loc_mon_tue_chieu> rdfs:label "Sơn Chủ Lộc Môn Tuệ Chiêu"@vi .
# dòng 119
<ex:monk/thu_son_hoai_chi> rdfs:label "Thủ Sơn Hoài Chí"@vi .
# dòng 120
<ex:monk/tam_giao_tri_tung> rdfs:label "Tam Giao Trí Tung"@vi .
# dòng 121
<ex:monk/quang_tue_nguyen_lien> rdfs:label "Quảng Tuệ Nguyên Liên"@vi .
```

### Căn cứ và đề nghị cập nhật

DILA của 元璉 ghi thầy 省念; trang 省念 có đệ tử 元璉. DILA alias 廣慧元璉.

Thay duy nhất target hasTeacher quang_tue_nguyen_lien bằng thu_son_tinh_niem (A004983); xác minh VPA cho người chính A014349 trước đồng bộ. Giữ số đời 43.

Giữ nguyên; chưa có 3 dữ liệu độc lập chứng minh số hiện tại sai và số thay thế đúng.

- [DILA A014349](https://authority.dila.edu.tw/person/search.php?aid=A014349)
- [DILA A004983](https://authority.dila.edu.tw/person/search.php?aid=A004983)

Hash UTF-8 SHA256: `53adb71503b3d019d8a48343a5ac57a97d0cf6d823e0819f2dea039105d362c5`

## Thụy Nham Trí Tài

- File: TS-Thuy-Nham-Tri-Tai.ttl
- Subject tự nối: `thuy_nham_tri_tai`
- DILA đề xuất: chưa xác minh
- Trạng thái: Chưa xác minh — bỏ qua

### Chi tiết sai trong file

```ttl
# dòng 6
<ex:monk/thuy_nham_tri_tai> a <bkg:Monk> ;
# dòng 7
rdfs:label "Thụy Nham Trí Tài"@vi ;
# dòng 8
crm:P1_is_identified_by <ex:monk/thuy_nham_tri_tai> ;
# dòng 52
bkg:generationOrder 44;
# dòng 53
bkg:hasTeacher <ex:monk/diep_huyen_quy_tinh> ;
# dòng 54
bkg:hasDisciple <ex:monk/thuy_nham_tri_tai> ;
# dòng 57
<ex:monk/than_danh_hong_nhan> rdfs:label "Thần Đảnh Hồng Nhân"@vi .
# dòng 58
<ex:monk/quang_van_dieu_tri> rdfs:label "Quang Vân Diệu Trí"@vi .
# dòng 59
<ex:monk/quang_tue_duc_tuyen> rdfs:label "Quảng Tuệ Đức Tuyên"@vi .
# dòng 60
<ex:monk/khai_thanh_bao_tinh> rdfs:label "Sơn Chủ Khai Thánh Bảo Tình"@vi .
# dòng 61
<ex:monk/nhuan_vuong_xu_binh> rdfs:label "Nhuận Vương Xứ Bình"@vi .
# dòng 62
<ex:monk/loc_mon_tue_chieu> rdfs:label "Sơn Chủ Lộc Môn Tuệ Chiêu"@vi .
# dòng 63
<ex:monk/thach_mon_thu_tan> rdfs:label "Thạch Môn Thủ Tấn"@vi .
# dòng 64
<ex:monk/thuy_nham_tri_tai> rdfs:label "Thụy Nham Trí Tài"@vi .
# dòng 65
<ex:monk/diep_huyen_quy_tinh> rdfs:label "Diệp Huyện Quy Tỉnh"@vi .
```

### Căn cứ và đề nghị cập nhật

Local có A026976/智才 nhưng web tool không truy cập được bản ghi; tìm alias chưa cho chứng cứ đủ tin cậy. Không dùng kết quả thiếu làm kết luận DILA không có người này.

BỎ QUA cập nhật học thuật. Giữ nguyên TTL/DB, ghi cạnh tự nối không hợp lệ để xác minh. Không đoán trò thay cho thuy_nham_tri_tai; chưa xác nhận được A026976 trên DILA chính thức.

Giữ nguyên; chưa có 3 dữ liệu độc lập chứng minh số hiện tại sai và số thay thế đúng.


Hash UTF-8 SHA256: `cd7bf58bd968617463685adec3553259bf15ca39be32540bbdc99535be8c0dc6`

## Tịnh Nhân Kế Thành

- File: TS-Tinh-Nhan-Ke-Thanh.ttl
- Subject tự nối: `tri_hai_dao_binh`
- DILA đề xuất: A026926 — 淨因繼成
- Trạng thái: DILA xác nhận quan hệ; phải xử lý ánh xạ local trước

### Chi tiết sai trong file

```ttl
# dòng 7
<ex:monk/tri_hai_dao_binh> a <bkg:Monk> ;
# dòng 8
rdfs:label "Trí Hải Đạo Bình"@vi ;
# dòng 9
crm:P1_is_identified_by <ex:monk/tri_hai_dao_binh> ;
# dòng 110
bkg:generationOrder 48;
# dòng 111
bkg:hasTeacher <ex:monk/tri_hai_dao_binh>  ;
# dòng 112
bkg:hasDisciple <ex:monk/thuy_nham_nhu_thang> ,
# dòng 117
<ex:monk/tri_hai_dao_binh> rdfs:label "Trí Hải Đạo Bình"@vi .
# dòng 118
<ex:monk/tinh_nhan_ke_thanh> rdfs:label "Tịnh Nhân Kế Thành"@vi .
# dòng 119
<ex:monk/da_phu_dao_xuyen> rdfs:label "Dã Phụ Đạo Xuyên"@vi .
# dòng 120
<ex:monk/thuy_nham_nhu_thang> rdfs:label "Thụy Nham Như Thắng"@vi .
```

### Căn cứ và đề nghị cập nhật

DILA A026926 alias 淨因繼成, thầy 智海道平 A014617; trang thầy liệt kê 繼成. Cả subject và nhãn hiện bị gán sang thầy.

Đề xuất sửa subject/P1 thành tinh_nhan_ke_thanh, nhãn chính Tịnh Nhân Kế Thành; giữ target thầy tri_hai_dao_binh nhưng xác minh ánh xạ thầy A014617. Không ghi đè row tri_hai_dao_binh đang mang tên trò trong DB.

Giữ nguyên; chưa có 3 dữ liệu độc lập chứng minh số hiện tại sai và số thay thế đúng.

- [DILA A026926](https://authority.dila.edu.tw/person/search.php?aid=A026926)
- [DILA A014617](https://authority.dila.edu.tw/person/search.php?aid=A014617)

Hash UTF-8 SHA256: `080c8cb7b201227ed048baadd4966940e3aa39280933072f81d248627dea5913`

## Vô Chuẩn Sư Phạm

- File: TS-Vo-Chuan-Su-Pham.ttl
- Subject tự nối: `vo_chuan_su_pham`
- DILA đề xuất: A004697 — 無準師範
- Trạng thái: DILA xác nhận quan hệ; ánh xạ local cần sửa có kiểm soát

### Chi tiết sai trong file

```ttl
# dòng 6
<ex:monk/vo_chuan_su_pham> a <bkg:Monk> ;
# dòng 7
rdfs:label "Vô Chuẩn Sư Phạm"@vi ;
# dòng 8
crm:P1_is_identified_by <ex:monk/vo_chuan_su_pham> ;
# dòng 15
bkg:generationOrder 53;
# dòng 16
bkg:hasTeacher <ex:monk/vo_chuan_su_pham> ;
# dòng 17
bkg:hasDisciple <ex:monk/tuyet_nham_to_kham> ,
# dòng 21
<ex:monk/tuyet_nham_to_kham> rdfs:label "Tuyết Nham Tổ Khâm"@vi .
# dòng 22
<ex:monk/doan_kieu_dieu_luan> rdfs:label "Đoạn Kiều Diệu Luân"@vi .
# dòng 23
<ex:monk/vo_chuan_su_pham> rdfs:label "Phá Am Tổ Tiên"@vi .
```

### Căn cứ và đề nghị cập nhật

DILA 無準師範 là pháp tự 破庵祖先; trang thầy có đệ tử 師範. Backup T211 cho thấy target và nhãn thầy bị thay cùng URI subject.

Khôi phục target hasTeacher pha_am_to_tien và nhãn Phá Am Tổ Tiên; ánh xạ đúng A004697 (người chính), A004696 (thầy) cần rà tác động trước khi áp dụng. A045360 local khác ID chính thức được xác nhận, chưa xác định nội dung A045360 ngoài web.

Giữ nguyên; chưa có 3 dữ liệu độc lập chứng minh số hiện tại sai và số thay thế đúng.

- [DILA A004697](https://authority.dila.edu.tw/person/search.php?aid=A004697)
- [DILA A004696](https://authority.dila.edu.tw/person/search.php?aid=A004696)

Hash UTF-8 SHA256: `1277df86f81ba8d5b7fd39def519ddd1166fe13e0fb2aa84a9f87ad632f7d0ad`


## Kiểm lại Diên Phúc sau Admin sửa

Hồ sơ đầu ở trên là snapshot trước sửa. Kết quả mới nhất: [Diên Phúc recheck](dien-phuc-recheck-2026-10-02.md). Đã hết tự nối nhưng còn3 đồng môn trong hasTeacher; chưa submit DB. cases.json và Dashboard đã cập nhật trạng thái mới.


## Kết quả mới nhất — Tuệ Thăng đã sync

Admin đã sửa hasTeacher chỉ còn Đoan Dụ, chốt đời50 và yêu cầu đồng bộ. Đã sync Tuệ Thăng A008431 và trả metadata thầy A007993 đời49. DB/API PASS; 8 TTL assertions dùng A045939 bị rejected. Backup và rollback: data/backups/T215-dien-phuc-sync-20261002. Hồ sơ recheck trước đó là lịch sử, trạng thái hiện tại ở cases.json/Dashboard. 8 hồ sơ khác chưa apply.
