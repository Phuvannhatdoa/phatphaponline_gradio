# T215 — 9 hồ sơ đồng bộ và lỗi TTL còn lại (2026-10-02)

9/9 metadata, DILA ID, tiểu sử Việt, số đời và cạnh thầy đã xác minh khớp TTL → DB → API. DB đã có bản đúng nên phiên này không ghi lại DB. Đã phục hồi TTL Nguyên Liên từ self-edge trở lại Thủ Sơn Tỉnh Niệm A004983; có backup và rollback guard. Không đổi số đời. Kết quả từng case: [nine-db-api-check.json](nine-db-api-check.json), [nine-db-readback.json](nine-db-readback.json).

Audit đọc từng file: **1038/1038 RDF hợp lệ**, 1238 assertions thầy/trò, **0 self-edge** theo bộ trích xuất hiện có. RDF hợp lệ không chứng minh nội dung đúng. Template không tính. Cờ ttl_changed=false/source_db_changed=false trong summary chỉ mô tả audit đọc, không phủ nhận sửa Nguyên Liên trước audit.

## Lỗi cụ thể cần xử lý trước

| File | Bằng chứng | Hướng xử lý đề xuất |
|---|---|---|
| TS-Di-Phong-Kinh-Ninh.ttl | Dòng6 URI bach_van_khong_do; dòng7 tên Nguyệt Khê Diệu Trừng; dòng16 thầy nguyet_khe_dieu_trung. URI và tên không khớp hồ sơ file; tạo cạnh quay về Bạch Vân. | Khóa đúng DILA của Di Phong, xác minh tiểu sử rồi sửa riêng subject/P1/nhãn/event, không replace toàn file. |
| TS-Dot-Khong-Tri-Ban.ttl | Dòng6/8 dùng bach_van_khong_do, dòng7 Đột Không Trí Bản; dòng16 thầy di_phong_kinh_ninh. | Tách URI của Trí Bản sau xác minh DILA; giữ target thầy đã được kiểm chứng. |
| TS-Truong-Vien.ttl | Dòng6/8 dùng phat_y_linh_nhac, dòng7 Trường Viễn. | Xác minh DILA rồi tách chủ thể; tránh ghi đè Phật Ý Linh Nhạc. |
| TS-Dai-Xa-Nhu-Truong.ttl | Dòng7/473 khai báo cùng phong_huyet_dien_chieu, nhãn Nam Viện Huệ Ngung; thầy Tổ Đức Bảo Tạng và Tuyết Đậu Chơn Phác trong hai khối. | Kiểm nguồn Việt của Như Trường, bỏ khối sao chép sai chỉ khi có chứng cứ; khóa ID trước sync. |
| TS-Minh-Hoang-Tu-Dung.ttl; TS-Tuyet-Giau-Chon-Phac.ttl | Cũng hai khối chủ thể và trùng phong_huyet_dien_chieu. | Kiểm từng khối/tiểu sử/DILA; không xem hai khai báo cùng URI là hai người độc lập. |
| TS-Phuc-Chau-Dai-An.ttl | Dòng6/8 URI ex:monk/ rỗng, dòng7 nhãn rỗng, dòng15 thầy rỗng. | Bỏ qua import, bổ sung đúng người/thầy từ nguồn; không đoán ID từ tên file. |
| TS-Phuoc-Chau-Dai-An.ttl | Dòng6–8 lại chứa Bách Trượng Hoài Hải, trùng file Bách Trượng. | Phân biệt Phuc/Phuoc; kiểm nội dung thực và file trùng trước đổi tên hoặc phục hồi Đại An. |

## Thống kê cờ kiểm tra (không cộng thành số lỗi chắc chắn)

| Mã | Số phát hiện toàn corpus |
|---|---:|
| IDENTIFIER_DIFFERENT | 101 |
| FILENAME_SUBJECT_DIFFERENT | 85 |
| DILA_UNRESOLVED | 214 |
| MULTIPLE_MAIN | 3 |
| MAIN_UNSUPPORTED | 1 |
| SUBJECT_COLLISION | 6 |
| DILA_NOT_CONFIRMED | 474 |
| ENDPOINT_NO_MAIN_FILE | 20 |
| GENERATION_NOT_COMPARABLE | 20 |
| GENERATION_REVIEW | 26 |
| DIRECTED_CYCLE | 3 |

6 nhóm subject trùng, 15 file tham gia; một số có thể là alias hoặc file lặp hợp lệ, chưa tự kết luận sai danh tính. MULTIPLE_MAIN là nhiều khai báo khối chủ thể, không bảo đảm nhiều URI khác nhau. 101 P1 khác subject và 85 tên file khác subject là cờ cần kiểm quy ước định danh, không được tự đồng nhất. 214 DILA_UNRESOLVED và 474 DILA_NOT_CONFIRMED là tình trạng ánh xạ local, chưa xác minh web từng người. 26 cặp đời cần review, 20 cặp không so được và 20 cặp thiếu file endpoint: không tự tăng/giảm đời.

## Ba đường chứng minh vòng (có thể giao nhau)

### Vòng 1

`bach_van_khong_do → co_chuyet_nguyen_hau → vo_minh_te_ngo → nguyet_khe_dieu_trung → bach_van_khong_do`

| Thầy → trò | File khai báo |
|---|---|
| bach_van_khong_do → co_chuyet_nguyen_hau | TS-Bach-Van-Khong-Do.ttl (hasDisciple); TS-Co-Chuyet-Nguyen-Hau.ttl (hasTeacher) |
| co_chuyet_nguyen_hau → vo_minh_te_ngo | TS-Co-Chuyet-Nguyen-Hau.ttl (hasDisciple); TS-Vo-Minh-Te-Ngo.ttl (hasTeacher) |
| vo_minh_te_ngo → nguyet_khe_dieu_trung | TS-Nguyet-Khue-Dieu-Trung.ttl (hasTeacher); TS-Vo-Minh-Te-Ngo.ttl (hasDisciple) |
| nguyet_khe_dieu_trung → bach_van_khong_do | TS-Di-Phong-Kinh-Ninh.ttl (hasTeacher) |

### Vòng 2

`bach_van_khong_do → co_chuyet_nguyen_hau → vo_minh_te_ngo → nguyet_khe_dieu_trung → di_phong_kinh_ninh → bach_van_khong_do`

| Thầy → trò | File khai báo |
|---|---|
| bach_van_khong_do → co_chuyet_nguyen_hau | TS-Bach-Van-Khong-Do.ttl (hasDisciple); TS-Co-Chuyet-Nguyen-Hau.ttl (hasTeacher) |
| co_chuyet_nguyen_hau → vo_minh_te_ngo | TS-Co-Chuyet-Nguyen-Hau.ttl (hasDisciple); TS-Vo-Minh-Te-Ngo.ttl (hasTeacher) |
| vo_minh_te_ngo → nguyet_khe_dieu_trung | TS-Nguyet-Khue-Dieu-Trung.ttl (hasTeacher); TS-Vo-Minh-Te-Ngo.ttl (hasDisciple) |
| nguyet_khe_dieu_trung → di_phong_kinh_ninh | TS-Nguyet-Khue-Dieu-Trung.ttl (hasDisciple) |
| di_phong_kinh_ninh → bach_van_khong_do | TS-Dot-Khong-Tri-Ban.ttl (hasTeacher) |

### Vòng 3

`bach_van_thu_doan → ngu_to_phap_dien → vien_ngo_khac_can → ho_khau_thieu_long → thien_dong_dam_hoa → mat_am_han_kiet → pha_am_to_tien → vo_chuan_su_pham → tuyet_nham_to_kham → cao_phong_nguyen_dieu → trung_phong_minh_bon → thien_nham_nguyen_truong → van_phong_thoi_uy → to_duc_bao_tang → phong_huyet_dien_chieu → thu_son_tinh_niem → phan_duong_thien_chieu → thach_suong_so_vien → duong_ky_phuong_hoi → bach_van_thu_doan`

| Thầy → trò | File khai báo |
|---|---|
| bach_van_thu_doan → ngu_to_phap_dien | TS-Bach-Van-Thu-Doan.ttl (hasDisciple); TS-Ngu-To-Phap-Dien.ttl (hasTeacher) |
| ngu_to_phap_dien → vien_ngo_khac_can | TS-Vien-Ngo-Khac-Can.ttl (hasTeacher) |
| vien_ngo_khac_can → ho_khau_thieu_long | TS-Ho-Khau-Thieu-Long.ttl (hasTeacher) |
| ho_khau_thieu_long → thien_dong_dam_hoa | TS-Ho-Khau-Thieu-Long.ttl (hasDisciple); TS-Thien-Dong-Dam-Hoa.ttl (hasTeacher) |
| thien_dong_dam_hoa → mat_am_han_kiet | TS-Mat-Am-Han-Kiet.ttl (hasTeacher) |
| mat_am_han_kiet → pha_am_to_tien | TS-Mat-Am-Han-Kiet.ttl (hasDisciple); TS-Pha-Am-To-Tien.ttl (hasTeacher) |
| pha_am_to_tien → vo_chuan_su_pham | TS-Pha-Am-To-Tien.ttl (hasDisciple); TS-Vo-Chuan-Su-Pham.ttl (hasTeacher) |
| vo_chuan_su_pham → tuyet_nham_to_kham | TS-Tuyet-Nham-To-Kham.ttl (hasTeacher); TS-Vo-Chuan-Su-Pham.ttl (hasDisciple) |
| tuyet_nham_to_kham → cao_phong_nguyen_dieu | TS-Cao-Phong-Nguyen-Dieu.ttl (hasTeacher); TS-Tuyet-Nham-To-Kham.ttl (hasDisciple) |
| cao_phong_nguyen_dieu → trung_phong_minh_bon | TS-Cao-Phong-Nguyen-Dieu.ttl (hasDisciple); TS-Trung-Phong-Minh-Bon.ttl (hasTeacher) |
| trung_phong_minh_bon → thien_nham_nguyen_truong | TS-Thien-Nham-Nguyen-Truong.ttl (hasTeacher); TS-Trung-Phong-Minh-Bon.ttl (hasDisciple) |
| thien_nham_nguyen_truong → van_phong_thoi_uy | TS-Thien-Nham-Nguyen-Truong.ttl (hasDisciple); TS-Van-Phong-Thoi-Uy.ttl (hasTeacher) |
| van_phong_thoi_uy → to_duc_bao_tang | TS-To-Duc-Bao-Tang.ttl (hasTeacher); TS-Van-Phong-Thoi-Uy.ttl (hasDisciple) |
| to_duc_bao_tang → phong_huyet_dien_chieu | TS-Dai-Xa-Nhu-Truong.ttl (hasTeacher); TS-Minh-Hoang-Tu-Dung.ttl (hasTeacher); TS-Tuyet-Giau-Chon-Phac.ttl (hasTeacher) |
| phong_huyet_dien_chieu → thu_son_tinh_niem | TS-Phong-Huyet-Dien-Chieu.ttl (hasDisciple); TS-Thu-Son-Tinh-Niem.ttl (hasTeacher) |
| thu_son_tinh_niem → phan_duong_thien_chieu | TS-Phan-Duong-Thien-Chieu.ttl (hasTeacher); TS-Thu-Son-Tinh-Niem.ttl (hasDisciple) |
| phan_duong_thien_chieu → thach_suong_so_vien | TS-Phan-Duong-Thien-Chieu.ttl (hasDisciple); TS-Thach-Suong-So-Vien.ttl (hasTeacher) |
| thach_suong_so_vien → duong_ky_phuong_hoi | TS-Duong-Ky-Phuong-Hoi.ttl (hasTeacher) |
| duong_ky_phuong_hoi → bach_van_thu_doan | TS-Bach-Van-Thu-Doan.ttl (hasTeacher) |

Hai vòng đầu đóng qua URI Bạch Vân bị dùng ở Di Phong/Đột Không. Vòng dài đóng qua URI Phong Huyệt bị dùng trong nhóm Đại Xá/Minh Hoằng/Tuyết Giàu. Cần kiểm các cạnh đó trước; không xóa mọi cạnh trong vòng. Cạnh đã xác minh thuộc nhóm9 vẫn có thể xuất hiện trên vòng do cạnh sai ở file khác.

## Danh sách từng file ngoài nhóm9

812 file có ít nhất một cờ, không phải 812 file đã chứng minh sai. JSON có SHA256 và số dòng: [other-files.json](other-files.json). Bản thô: [findings.jsonl](findings.jsonl); truy vết: [cycles.json](cycles.json).

| File | Cờ |
|---|---|
| Bo-Tat-Long-Tho.ttl | IDENTIFIER_DIFFERENT, FILENAME_SUBJECT_DIFFERENT |
| Bo-Tat-Ma-Minh.ttl | IDENTIFIER_DIFFERENT, FILENAME_SUBJECT_DIFFERENT |
| Cs-Banh-Nhu-Lam.ttl | DILA_UNRESOLVED |
| Cs-Cap-Su-Phung-Tiep.ttl | FILENAME_SUBJECT_DIFFERENT |
| Cs-De-Hinh-Quach-Tuong-Chanh.ttl | FILENAME_SUBJECT_DIFFERENT, DILA_UNRESOLVED |
| Cs-Do-Huong-Trinh.ttl | DILA_UNRESOLVED |
| Cs-Doi-Dao-Thuan.ttl | DILA_NOT_CONFIRMED |
| Cs-Giang-Chau-Ly-Bot.ttl | DILA_NOT_CONFIRMED |
| Cs-Hoang-Dinh-Kien.ttl | DILA_NOT_CONFIRMED |
| Cs-Hoang-Ngan-Tiet.ttl | DILA_NOT_CONFIRMED |
| Cs-Huong.ttl | FILENAME_SUBJECT_DIFFERENT, DILA_UNRESOLVED |
| Cs-Long-Ho-Vuong-Tieu.ttl | DILA_NOT_CONFIRMED |
| Cs-Luu-Ngan-Tu.ttl | DILA_NOT_CONFIRMED |
| Cs-Ly-Binh.ttl | DILA_NOT_CONFIRMED |
| Cs-Ly-Di-Ton.ttl | DILA_NOT_CONFIRMED |
| Cs-Ly-Doan-Nguyen.ttl | DILA_NOT_CONFIRMED |
| Cs-Ly-Hao.ttl | DILA_NOT_CONFIRMED |
| Cs-Mac-Tuong-Thieu-Hu.ttl | DILA_UNRESOLVED |
| Cs-Ngo-Tuan.ttl | DILA_NOT_CONFIRMED |
| Cs-Ngo-Vi-Minh.ttl | DILA_NOT_CONFIRMED |
| Cs-Pham-Huyen-Quan.ttl | DILA_NOT_CONFIRMED |
| Cs-Pham-Xung.ttl | DILA_UNRESOLVED |
| Cs-Phan-Luong-Quy.ttl | DILA_UNRESOLVED, GENERATION_REVIEW |
| Cs-Phuoc-Chau-Nam.ttl | FILENAME_SUBJECT_DIFFERENT, DILA_UNRESOLVED |
| Cs-Quan-Van-Vuong-Thieu.ttl | DILA_NOT_CONFIRMED |
| Cs-Tang-Khai.ttl | DILA_UNRESOLVED |
| Cs-Thuong-Anh.ttl | DILA_NOT_CONFIRMED |
| Cs-Tien-Doan-Le.ttl | DILA_NOT_CONFIRMED |
| Cs-Trieu-Lenh-Cam.ttl | DILA_UNRESOLVED |
| Cs-Truong-Cuu-Thanh.ttl | DILA_NOT_CONFIRMED |
| Cs-Tuong-Chau-Bang-Uan.ttl | DILA_NOT_CONFIRMED |
| Cs-Tuong-Quoc-Bui-Huu.ttl | FILENAME_SUBJECT_DIFFERENT |
| Cs-Ty-Bo-Ton.ttl | DILA_UNRESOLVED |
| Cs-Van-Cong-Duong-Uc.ttl | DILA_NOT_CONFIRMED |
| Cs-Van-Dinh-Ho-An-Quoc.ttl | DILA_NOT_CONFIRMED |
| Cs-Xu-Mat-Tu-Phu.ttl | DILA_NOT_CONFIRMED |
| Hiep-Ton-Gia.ttl | IDENTIFIER_DIFFERENT |
| Thich-Ca-Mau-Ni-Phat.ttl | IDENTIFIER_DIFFERENT, DILA_UNRESOLVED |
| Ton-Gia-A-Nan.ttl | FILENAME_SUBJECT_DIFFERENT |
| Ton-Gia-Ba-Tu-Ban-Dau.ttl | IDENTIFIER_DIFFERENT, FILENAME_SUBJECT_DIFFERENT |
| Ton-Gia-Ba-Tu-Mat.ttl | IDENTIFIER_DIFFERENT, FILENAME_SUBJECT_DIFFERENT |
| Ton-Gia-Ba-Xa-Tu-Da.ttl | IDENTIFIER_DIFFERENT, FILENAME_SUBJECT_DIFFERENT |
| Ton-Gia-Bat-Nha-Da-La.ttl | IDENTIFIER_DIFFERENT, FILENAME_SUBJECT_DIFFERENT |
| Ton-Gia-Bat-Nhu-Mat-Da.ttl | IDENTIFIER_DIFFERENT, FILENAME_SUBJECT_DIFFERENT |
| Ton-Gia-Bo-De-Dat-Ma.ttl | FILENAME_SUBJECT_DIFFERENT, DILA_NOT_CONFIRMED |
| Ton-Gia-Ca-Na-De-Ba.ttl | IDENTIFIER_DIFFERENT, FILENAME_SUBJECT_DIFFERENT |
| Ton-Gia-Ca-Ty-Ma-La.ttl | IDENTIFIER_DIFFERENT, FILENAME_SUBJECT_DIFFERENT |
| Ton-Gia-Cuu-Ma-La-Da.ttl | IDENTIFIER_DIFFERENT, FILENAME_SUBJECT_DIFFERENT |
| Ton-Gia-Da-Da-Xa-Da.ttl | IDENTIFIER_DIFFERENT, FILENAME_SUBJECT_DIFFERENT, DILA_UNRESOLVED |
| Ton-Gia-Dai-Giam-Hue-Nang.ttl | FILENAME_SUBJECT_DIFFERENT, DILA_NOT_CONFIRMED |
| Ton-Gia-Dao-Tin.ttl | IDENTIFIER_DIFFERENT, FILENAME_SUBJECT_DIFFERENT, DILA_UNRESOLVED |
| Ton-Gia-De-Da-Ca.ttl | IDENTIFIER_DIFFERENT, FILENAME_SUBJECT_DIFFERENT |
| Ton-Gia-Di-Gia-Ca.ttl | IDENTIFIER_DIFFERENT, FILENAME_SUBJECT_DIFFERENT |
| Ton-Gia-Hac-Lac-Na.ttl | IDENTIFIER_DIFFERENT, FILENAME_SUBJECT_DIFFERENT |
| Ton-Gia-Hoang-Mai-Hoang-Nhan.ttl | IDENTIFIER_DIFFERENT, FILENAME_SUBJECT_DIFFERENT |
| Ton-Gia-Hue-Kha.ttl | IDENTIFIER_DIFFERENT, FILENAME_SUBJECT_DIFFERENT |
| Ton-Gia-La-Hau-La-Da.ttl | IDENTIFIER_DIFFERENT, FILENAME_SUBJECT_DIFFERENT, DILA_UNRESOLVED |
| Ton-Gia-Ma-Ha-Ca-Diep.ttl | IDENTIFIER_DIFFERENT, FILENAME_SUBJECT_DIFFERENT |
| Ton-Gia-Ma-Noa-La.ttl | IDENTIFIER_DIFFERENT, FILENAME_SUBJECT_DIFFERENT |
| Ton-Gia-Phat-Da-Mat-Da.ttl | IDENTIFIER_DIFFERENT, FILENAME_SUBJECT_DIFFERENT |
| Ton-Gia-Phat-Da-Nan-De.ttl | IDENTIFIER_DIFFERENT, FILENAME_SUBJECT_DIFFERENT |
| Ton-Gia-Phu-Na-Da-Xa.ttl | IDENTIFIER_DIFFERENT, FILENAME_SUBJECT_DIFFERENT |
| Ton-Gia-Su-Tu-Ty-Kheo.ttl | IDENTIFIER_DIFFERENT, FILENAME_SUBJECT_DIFFERENT, DILA_UNRESOLVED |
| Ton-Gia-Tang-Gia-Nan-De.ttl | IDENTIFIER_DIFFERENT, FILENAME_SUBJECT_DIFFERENT |
| Ton-Gia-Tang-Xan.ttl | IDENTIFIER_DIFFERENT, FILENAME_SUBJECT_DIFFERENT |
| Ton-Gia-Thuong-Na-Hoa-Tu.ttl | IDENTIFIER_DIFFERENT, FILENAME_SUBJECT_DIFFERENT |
| Ton-Gia-Uu-Ba-Cuc-Da.ttl | IDENTIFIER_DIFFERENT, FILENAME_SUBJECT_DIFFERENT, DILA_UNRESOLVED |
| Ton-Gia-Xa-Da-Da.ttl | IDENTIFIER_DIFFERENT, FILENAME_SUBJECT_DIFFERENT |
| TS-Am-Chu-Dong-Phong.ttl | DILA_NOT_CONFIRMED |
| TS-Am-Chu-Duc-Son-Tong-Thap.ttl | FILENAME_SUBJECT_DIFFERENT |
| TS-Am-Chu-Ho-Khe.ttl | DILA_UNRESOLVED |
| TS-Am-Chu-Kiem-Mon-An-Phan.ttl | FILENAME_SUBJECT_DIFFERENT |
| TS-Am-Chu-Phap-Hai-Giac-Nhan.ttl | FILENAME_SUBJECT_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Am-Chu-Phuc-Bon.ttl | DILA_NOT_CONFIRMED |
| TS-Am-Chu-Quy-Tong-Chi-Chi.ttl | FILENAME_SUBJECT_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Am-Chu-Sam-Duong.ttl | DILA_NOT_CONFIRMED |
| TS-Am-Chu-Thach-Dau-Hoai-Chi.ttl | FILENAME_SUBJECT_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Am-Chu-Tu-Ngon.ttl | DILA_NOT_CONFIRMED |
| TS-An-Hoa-Van-Nhat.ttl | DILA_NOT_CONFIRMED |
| TS-An-Quoc-Huyen-Dinh.ttl | IDENTIFIER_DIFFERENT |
| TS-An-Tinh-Ngan-Sam.ttl | DILA_NOT_CONFIRMED |
| TS-Ba-Tieu-Coc-Tuyen.ttl | DILA_NOT_CONFIRMED |
| TS-Ba-Tieu-Hue-Thanh.ttl | DILA_NOT_CONFIRMED |
| TS-Bac-Giang-Tay-Lan-Nhuong.ttl | DILA_UNRESOLVED |
| TS-Bac-Son-Tu-Kinh.ttl | DILA_UNRESOLVED |
| TS-Bach-Duong-Phap-Thuan.ttl | DILA_NOT_CONFIRMED |
| TS-Bach-Linh.ttl | DILA_NOT_CONFIRMED |
| TS-Bach-Loc-Hien-Doan.ttl | DILA_NOT_CONFIRMED |
| TS-Bach-Nhan-Minh-Triet.ttl | DILA_NOT_CONFIRMED |
| TS-Bach-Tao-Nghiem.ttl | DILA_UNRESOLVED |
| TS-Bach-Truong-Di-The.ttl | DILA_NOT_CONFIRMED |
| TS-Bach-Truong-Duy-Chanh.ttl | DILA_UNRESOLVED |
| TS-Bach-Truong-Duy-Chinh.ttl | DILA_NOT_CONFIRMED |
| TS-Bach-Truong-Hoai-Hai.ttl | SUBJECT_COLLISION |
| TS-Bach-Truong-Nguyen-Tuc.ttl | DILA_NOT_CONFIRMED |
| TS-Bach-Van-Khong-Do.ttl | DILA_UNRESOLVED, SUBJECT_COLLISION |
| TS-Bach-Van-Thu-Doan.ttl | DILA_NOT_CONFIRMED |
| TS-Ban-Giac-Nha-Chau.ttl | DILA_UNRESOLVED |
| TS-Ban-Tich-Van-Quan.ttl | DILA_UNRESOLVED |
| TS-Bao-An-Phap-Dien.ttl | DILA_NOT_CONFIRMED |
| TS-Bao-An-Thanh.ttl | DILA_NOT_CONFIRMED |
| TS-Bao-Ban-Tue-Nguyen.ttl | DILA_NOT_CONFIRMED |
| TS-Bao-Cai-Tu-Can.ttl | DILA_NOT_CONFIRMED |
| TS-Bao-Hoa-Hien.ttl | DILA_NOT_CONFIRMED |
| TS-Bao-Ninh-Nhan-Dung.ttl | DILA_NOT_CONFIRMED |
| TS-Bao-Ninh-Vien-Co.ttl | DILA_UNRESOLVED |
| TS-Bao-Phuoc-Ban-Quyen.ttl | DILA_NOT_CONFIRMED |
| TS-Bao-Phuoc-Thu.ttl | DILA_UNRESOLVED |
| TS-Bao-Than-Huu-Thuy.ttl | DILA_UNRESOLVED |
| TS-Bao-Tho-Dien-Chieu.ttl | DILA_UNRESOLVED |
| TS-Bao-Tho-Doi-Thu-Hai.ttl | FILENAME_SUBJECT_DIFFERENT, DILA_UNRESOLVED |
| TS-Bao-Tu-Tan-Anh.ttl | DILA_UNRESOLVED |
| TS-Bao-Ung-Phap-Chieu.ttl | DILA_NOT_CONFIRMED |
| TS-Bat-Nha-Thien-Doan.ttl | DILA_NOT_CONFIRMED |
| TS-Bich-Phong-Tanh-Kim.ttl | DILA_UNRESOLVED |
| TS-Bich-Thien-Thanh-Khong.ttl | DILA_UNRESOLVED |
| TS-Bien-Dam-Hieu-Lieu.ttl | IDENTIFIER_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Bo-De-Quang-Dung.ttl | DILA_NOT_CONFIRMED |
| TS-Bon-Khe.ttl | IDENTIFIER_DIFFERENT, DILA_UNRESOLVED |
| TS-Bon-Qua-Khoang-Vien.ttl | DILA_UNRESOLVED, GENERATION_NOT_COMPARABLE |
| TS-Bon-Tri-Minh-Giac.ttl | DILA_NOT_CONFIRMED |
| TS-Bong-Lai-Vien.ttl | DILA_NOT_CONFIRMED |
| TS-Can-Le.ttl | DILA_NOT_CONFIRMED |
| TS-Can-Nguyen-Vien.ttl | DILA_NOT_CONFIRMED |
| TS-Can-Phong-Vien-Tue.ttl | DILA_NOT_CONFIRMED |
| TS-Can-Tu-Son-Sung-Hue.ttl | IDENTIFIER_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Canh-Thanh-Cu-To.ttl | DILA_NOT_CONFIRMED |
| TS-Cao-Am-Vien-Thanh.ttl | DILA_NOT_CONFIRMED |
| TS-Cao-An-Dai-Ngu.ttl | DILA_NOT_CONFIRMED |
| TS-Cat-Chau-Chi-Quan.ttl | DILA_NOT_CONFIRMED |
| TS-Cat-Chau-Chi-Thanh.ttl | IDENTIFIER_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Cat-Chau-Tanh-Khong.ttl | DILA_UNRESOLVED |
| TS-Chan-Nhu-Phuong.ttl | DILA_NOT_CONFIRMED |
| TS-Chanh-Nhac-Bon-Sieu.ttl | DILA_UNRESOLVED |
| TS-Chanh-Phap-Hy-Ninh.ttl | DILA_UNRESOLVED |
| TS-Chanh-Phap-Kien.ttl | DILA_NOT_CONFIRMED |
| TS-Chanh-Truyen-Huyen-Huu.ttl | DILA_UNRESOLVED |
| TS-Chieu-De-Tue-Lang.ttl | DILA_NOT_CONFIRMED |
| TS-Chieu-Giac-Dao-Nguyen.ttl | DILA_NOT_CONFIRMED |
| TS-Chieu-Giac-Dao-To.ttl | DILA_NOT_CONFIRMED |
| TS-Chieu-Giac-Thieu-An.ttl | DILA_NOT_CONFIRMED |
| TS-Chieu-Giac-Thuan-Bach.ttl | DILA_NOT_CONFIRMED |
| TS-Chieu-Giac-Thuong-Tong.ttl | DILA_NOT_CONFIRMED |
| TS-Chieu-Hien-Hoi-Thong.ttl | IDENTIFIER_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Chung-Nam-Phong-Duc.ttl | DILA_UNRESOLVED |
| TS-Chung-Nam-Su-To-Van-Te.ttl | DILA_NOT_CONFIRMED |
| TS-Chung-Son-Dam-Thoi.ttl | IDENTIFIER_DIFFERENT, GENERATION_REVIEW, DILA_NOT_CONFIRMED |
| TS-Chung-Son-Dao-Long.ttl | DILA_NOT_CONFIRMED |
| TS-Chuong-Chau-La-Han.ttl | GENERATION_REVIEW, DILA_NOT_CONFIRMED |
| TS-Chuong-Kinh-Hoai-Uan.ttl | DILA_NOT_CONFIRMED |
| TS-Co-Chuyet-Nguyen-Hau.ttl | DILA_UNRESOLVED, GENERATION_REVIEW |
| TS-Co-Luong-Nhan-Phon.ttl | DILA_UNRESOLVED |
| TS-Co-Son-To-Tran.ttl | DILA_UNRESOLVED |
| TS-Co-Tu.ttl | DILA_NOT_CONFIRMED |
| TS-Coc-An-Uan-Thong.ttl | DILA_NOT_CONFIRMED |
| TS-Cong-An-To-Chau.ttl | DILA_NOT_CONFIRMED |
| TS-Cu-Chau-Loi-Tu-Ho.ttl | FILENAME_SUBJECT_DIFFERENT, DILA_UNRESOLVED |
| TS-Cuu-Danh-To.ttl | DILA_NOT_CONFIRMED |
| TS-Cuu-Danh-Tue-Tuyen.ttl | DILA_NOT_CONFIRMED |
| TS-Cuu-Phong-Hy-Quang.ttl | DILA_UNRESOLVED |
| TS-Cuu-Phong-Tu-Tue.ttl | DILA_NOT_CONFIRMED |
| TS-Cuu-Tien-Phap.ttl | DILA_UNRESOLVED |
| TS-Cuu-Tong-Phap-Minh.ttl | DILA_NOT_CONFIRMED |
| TS-Da-Phu-Dao-Xuyen.ttl | DILA_NOT_CONFIRMED |
| TS-Dai-An-Thanh-Can.ttl | DILA_NOT_CONFIRMED |
| TS-Dai-Chau-Hue-Hai.ttl | DILA_NOT_CONFIRMED |
| TS-Dai-Dong-Quang-Trung.ttl | DILA_NOT_CONFIRMED |
| TS-Dai-Duong.ttl | DILA_NOT_CONFIRMED |
| TS-Dai-Giac-Nguy-Phu.ttl | DILA_UNRESOLVED |
| TS-Dai-Hoan-Tu-Trung.ttl | FILENAME_SUBJECT_DIFFERENT, DILA_UNRESOLVED |
| TS-Dai-Hue-Tong-Cao.ttl | DILA_NOT_CONFIRMED |
| TS-Dai-Mai-Phap-Thuong.ttl | DILA_NOT_CONFIRMED |
| TS-Dai-Ninh-Dao-Khoan.ttl | FILENAME_SUBJECT_DIFFERENT, SUBJECT_COLLISION |
| TS-Dai-Quy-Canh-Vung.ttl | DILA_NOT_CONFIRMED |
| TS-Dai-Quy-Dinh-Thuyen.ttl | DILA_NOT_CONFIRMED |
| TS-Dai-Quy-Giam.ttl | DILA_UNRESOLVED |
| TS-Dai-Quy-Hanh.ttl | DILA_UNRESOLVED |
| TS-Dai-Quy-Hoai-Tu.ttl | DILA_NOT_CONFIRMED |
| TS-Dai-Quy-Mo-Triet.ttl | GENERATION_NOT_COMPARABLE, DILA_NOT_CONFIRMED |
| TS-Dai-Quy-Phap-Bao.ttl | DILA_NOT_CONFIRMED |
| TS-Dai-Quy-Phap-Thai.ttl | DILA_NOT_CONFIRMED |
| TS-Dai-Quy-Te-Tuan.ttl | DILA_UNRESOLVED |
| TS-Dai-Quy-Thien-Qua.ttl | DILA_NOT_CONFIRMED |
| TS-Dai-Quy-To-Xuan.ttl | DILA_NOT_CONFIRMED |
| TS-Dai-Thua-Tue-Qua.ttl | DILA_NOT_CONFIRMED |
| TS-Dai-Trung-Lap-Chi.ttl | FILENAME_SUBJECT_DIFFERENT |
| TS-Dai-Trung-Tuong-Phu-Hai.ttl | DILA_UNRESOLVED |
| TS-Dai-Tuy-Nguyen-Tinh.ttl | DILA_NOT_CONFIRMED |
| TS-Dai-Xa-Nhu-Truong.ttl | MULTIPLE_MAIN, FILENAME_SUBJECT_DIFFERENT, SUBJECT_COLLISION |
| TS-Dam-Chau-Dai-Xuyen.ttl | DILA_NOT_CONFIRMED |
| TS-Dam-Chau-Hoa-Lam.ttl | DILA_NOT_CONFIRMED |
| TS-Dam-Chau-Long-Son.ttl | DILA_NOT_CONFIRMED |
| TS-Dam-Chau-Thach-Suong-Lam.ttl | DILA_NOT_CONFIRMED |
| TS-Dam-Chau-Tong-An.ttl | DILA_NOT_CONFIRMED |
| TS-Dam-Chau-Truong-Ty-Khoang.ttl | DILA_UNRESOLVED |
| TS-Dam-Chau-Tu-Khue.ttl | FILENAME_SUBJECT_DIFFERENT, DILA_UNRESOLVED |
| TS-Dam-Chau-Van-Cai-Canh.ttl | DILA_NOT_CONFIRMED |
| TS-Dam-Chau-Van-Dien.ttl | DILA_NOT_CONFIRMED |
| TS-Dam-Chau-Van-Trung-Cai.ttl | FILENAME_SUBJECT_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Dang-Giac-Pho-Minh.ttl | DILA_NOT_CONFIRMED |
| TS-Dang-Van-Sieu-Cap.ttl | DILA_UNRESOLVED |
| TS-Dao-Gia-Song-Khe-Dien.ttl | FILENAME_SUBJECT_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Dao-Man-Moc-Tran.ttl | DILA_UNRESOLVED |
| TS-Dao-Minh-Hue-Sam.ttl | DILA_UNRESOLVED |
| TS-Dao-Ngo-Ngo-Chan.ttl | DILA_NOT_CONFIRMED |
| TS-Dao-Ngo-Trong-Vien.ttl | DILA_NOT_CONFIRMED |
| TS-Dao-Ngo-Vien-Tri.ttl | DILA_NOT_CONFIRMED |
| TS-Dao-Ninh-Dao-Khoan.ttl | SUBJECT_COLLISION |
| TS-Dao-Trang-Cu-Tue.ttl | DILA_NOT_CONFIRMED |
| TS-Dao-Trang-Minh-Bien.ttl | DILA_NOT_CONFIRMED |
| TS-Dao-Trang-Phap-Nhu.ttl | DILA_NOT_CONFIRMED |
| TS-Dao-Trang-Phap-Toan.ttl | DILA_NOT_CONFIRMED |
| TS-Dao-Trang-Pho-Nham.ttl | DILA_NOT_CONFIRMED |
| TS-Dao-Trang-Tue-Lam.ttl | DILA_NOT_CONFIRMED |
| TS-Dao-Tuyen.ttl | IDENTIFIER_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Dao-Xuoc.ttl | IDENTIFIER_DIFFERENT |
| TS-Dau-Suat-Chi-An.ttl | DILA_NOT_CONFIRMED |
| TS-Dau-Suat-Tue-Chieu.ttl | DILA_NOT_CONFIRMED |
| TS-Dau-Tu-Dai_Dong.ttl | DILA_NOT_CONFIRMED |
| TS-Dau-Tu-Vien-Tu.ttl | DILA_NOT_CONFIRMED |
| TS-Di-Phong-Kinh-Ninh.ttl | FILENAME_SUBJECT_DIFFERENT, DILA_UNRESOLVED, SUBJECT_COLLISION, ENDPOINT_NO_MAIN_FILE |
| TS-Diem-Quan-Te-An.ttl | DILA_UNRESOLVED |
| TS-Dien-Khanh-Hong-Chuan.ttl | DILA_UNRESOLVED |
| TS-Dien-Khanh-Phap-Doan.ttl | DILA_NOT_CONFIRMED |
| TS-Dien-Khanh-Thuc.ttl | DILA_UNRESOLVED |
| TS-Dien-Triet-Hu-Van.ttl | DILA_NOT_CONFIRMED |
| TS-Diep-Huyen-Quy-Tinh.ttl | GENERATION_REVIEW |
| TS-Dieu-Khoa-Dao-Lam.ttl | IDENTIFIER_DIFFERENT |
| TS-Dieu-Lien-Thanh-Hoa.ttl | DILA_UNRESOLVED |
| TS-Dinh-Bao-Phong-Tri.ttl | DILA_UNRESOLVED |
| TS-Dinh-Chau-Thien-Thoi.ttl | DILA_NOT_CONFIRMED |
| TS-Dinh-Chau-Thuy-Duong.ttl | DILA_UNRESOLVED |
| TS-Dinh-Hue-Sieu-Tin.ttl | DILA_NOT_CONFIRMED |
| TS-Dinh-Phong-Qua-Thanh.ttl | DILA_UNRESOLVED |
| TS-Do-Luong-Ton-Thuc.ttl | IDENTIFIER_DIFFERENT, DILA_UNRESOLVED |
| TS-Doan-Huc-Nhu-Hoang.ttl | DILA_NOT_CONFIRMED |
| TS-Doan-Kieu-Dieu-Luan.ttl | DILA_NOT_CONFIRMED |
| TS-Doan-Truc-Trong-Hoa.ttl | DILA_NOT_CONFIRMED |
| TS-Doan-Vien-Chieu-Hoa.ttl | DILA_UNRESOLVED |
| TS-Dong-An.ttl | DILA_NOT_CONFIRMED |
| TS-Dong-Dinh-Tue-Nguyet.ttl | DILA_NOT_CONFIRMED |
| TS-Dong-Lam-Dao-Nhan.ttl | DILA_NOT_CONFIRMED |
| TS-Dong-Lam-Tu-Tuan.ttl | DILA_NOT_CONFIRMED |
| TS-Dong-Minh-Thien.ttl | DILA_NOT_CONFIRMED |
| TS-Dong-Son-Cat.ttl | DILA_NOT_CONFIRMED |
| TS-Dong-Son-Giac.ttl | DILA_NOT_CONFIRMED |
| TS-Dong-Son-Te-Vi.ttl | DILA_NOT_CONFIRMED |
| TS-Dong-Thien-Tu-Nhac.ttl | DILA_NOT_CONFIRMED |
| TS-Dot-Khong-Tri-Ban.ttl | FILENAME_SUBJECT_DIFFERENT, DILA_UNRESOLVED, SUBJECT_COLLISION, ENDPOINT_NO_MAIN_FILE |
| TS-Duc-Son-Tuyen-Giam.ttl | ENDPOINT_NO_MAIN_FILE |
| TS-Duc-Thien-Nhan-Hoi.ttl | DILA_NOT_CONFIRMED |
| TS-Duc-Vuong-Dai-Quan.ttl | DILA_NOT_CONFIRMED |
| TS-Duc-Vuong-Doan-Du.ttl | DILA_NOT_CONFIRMED |
| TS-Duc-Vuong-Duc-Quang.ttl | DILA_NOT_CONFIRMED |
| TS-Duc-Vuong-Phap-Dat.ttl | DILA_NOT_CONFIRMED |
| TS-Duc-Vuong-Tuan-Phac.ttl | DILA_NOT_CONFIRMED |
| TS-Duoc-Lam-Thach-Quan.ttl | DILA_UNRESOLVED |
| TS-Duoc-Son-Duy-Nghiem.ttl | ENDPOINT_NO_MAIN_FILE |
| TS-Duong-Chau-Tue-Giac.ttl | DILA_NOT_CONFIRMED |
| TS-Duong-Ky-Chan-Thuc.ttl | DILA_NOT_CONFIRMED |
| TS-Duong-Ky-Phuong-Hoi.ttl | GENERATION_NOT_COMPARABLE, DILA_NOT_CONFIRMED |
| TS-Duy-Sieu-Nang-Xan.ttl | DILA_UNRESOLVED |
| TS-Duy-Thanh-Linh-Nguyen.ttl | DILA_NOT_CONFIRMED |
| TS-Duyen-Chau-Hang-Ma-Tang.ttl | IDENTIFIER_DIFFERENT, FILENAME_SUBJECT_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Giac-A.ttl | DILA_NOT_CONFIRMED |
| TS-Giac-Am-To-Thi.ttl | DILA_UNRESOLVED |
| TS-Giang-Tay-Bai-Tho.ttl | DILA_UNRESOLVED |
| TS-Giang-Tay-Chi-Triet.ttl | IDENTIFIER_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Giao-Trung-Di-Quang.ttl | DILA_NOT_CONFIRMED |
| TS-Giap-Son-Hieu-Thuan.ttl | GENERATION_REVIEW, DILA_NOT_CONFIRMED |
| TS-Ha-Bac-Tri-Hoang.ttl | IDENTIFIER_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Ha-Son-Nhien.ttl | DILA_NOT_CONFIRMED |
| TS-Ha-Son-Thu-Tuan.ttl | DILA_UNRESOLVED, GENERATION_REVIEW |
| TS-Ha-Trach-Than-Hoi.ttl | IDENTIFIER_DIFFERENT, GENERATION_NOT_COMPARABLE, DILA_NOT_CONFIRMED |
| TS-Ha-Trung-Cong-Ky.ttl | DILA_NOT_CONFIRMED |
| TS-Hac-Lam-Huyen-To.ttl | IDENTIFIER_DIFFERENT |
| TS-Hac-Nhan.ttl | DILA_UNRESOLVED |
| TS-Hai-Hoi-Thu-Tung.ttl | DILA_UNRESOLVED |
| TS-Han-Chau-Da-Dia.ttl | DILA_NOT_CONFIRMED |
| TS-Hang-Chau-Da-Phuoc.ttl | DILA_UNRESOLVED |
| TS-Hang-Chau-Thien-Long.ttl | DILA_NOT_CONFIRMED |
| TS-Hanh-Nhac-Dao-Bien.ttl | DILA_NOT_CONFIRMED |
| TS-Hanh-Nhac-Phung-Nang.ttl | GENERATION_REVIEW |
| TS-Hien-Ninh-Vien-Tri.ttl | DILA_NOT_CONFIRMED |
| TS-Ho-Khau-Nguyen-Tinh.ttl | DILA_NOT_CONFIRMED |
| TS-Ho-Khau-Thieu-Long.ttl | DILA_NOT_CONFIRMED |
| TS-Ho-Nam-Dong-Tu-Nhu-Hoi.ttl | DILA_NOT_CONFIRMED |
| TS-Ho-Quoc-Canh-Nguyen.ttl | DILA_NOT_CONFIRMED |
| TS-Ho-Quoc-Canh-Tan.ttl | DILA_NOT_CONFIRMED |
| TS-Ho-Quoc-Te-Nguyet.ttl | DILA_NOT_CONFIRMED |
| TS-Ho-Quoc-Tue-Ban.ttl | DILA_NOT_CONFIRMED |
| TS-Hoa-Duoc-Nguyen-Cung.ttl | DILA_NOT_CONFIRMED |
| TS-Hoa-Lam-Thien-Giac.ttl | DILA_NOT_CONFIRMED |
| TS-Hoa-Nghiem-Dao-Long.ttl | DILA_NOT_CONFIRMED |
| TS-Hoa-Nghiem-Pho-Tu.ttl | GENERATION_REVIEW, DILA_NOT_CONFIRMED |
| TS-Hoa-Nghiem-To-Giac.ttl | DILA_NOT_CONFIRMED |
| TS-Hoa-Son-Duc-Pho.ttl | DILA_NOT_CONFIRMED |
| TS-Hoa-Son-Hue-Phuong.ttl | DILA_NOT_CONFIRMED |
| TS-Hoa-Tang-An-Dan.ttl | DILA_NOT_CONFIRMED |
| TS-Hoa-Tang-Giac-Thong.ttl | ENDPOINT_NO_MAIN_FILE, DILA_NOT_CONFIRMED |
| TS-Hoa-Tang-Tong-Dien.ttl | DILA_NOT_CONFIRMED |
| TS-Hoa-Tang-Tri-Tham.ttl | DILA_NOT_CONFIRMED |
| TS-Hoac-Am-Su-The.ttl | DILA_NOT_CONFIRMED |
| TS-Hoang-Ba-Dao-Toan.ttl | DILA_NOT_CONFIRMED |
| TS-Hoang-Ba-Duy-Thang.ttl | DILA_NOT_CONFIRMED |
| TS-Hoang-Ba-Hy-Van.ttl | IDENTIFIER_DIFFERENT, DILA_UNRESOLVED |
| TS-Hoang-Lien-Nghia-So.ttl | DILA_NOT_CONFIRMED |
| TS-Hoang-Long-Duc-Phung.ttl | DILA_NOT_CONFIRMED |
| TS-Hoang-Long-Hue-Nam.ttl | DILA_NOT_CONFIRMED, GENERATION_NOT_COMPARABLE |
| TS-Hoang-Long-Ngo-Tan.ttl | DILA_NOT_CONFIRMED |
| TS-Hoang-Long-Nhu-Hieu.ttl | DILA_NOT_CONFIRMED |
| TS-Hoang-Long-Phap-Trung.ttl | DILA_NOT_CONFIRMED |
| TS-Hoang-Long-Tri-Minh.ttl | DILA_NOT_CONFIRMED |
| TS-Hoanh-Hoa-Nguyen-Ngo.ttl | DILA_NOT_CONFIRMED |
| TS-Hoat-Ngo-Long-Tham.ttl | DILA_UNRESOLVED |
| TS-Hoi-Duong-To-Tam.ttl | DILA_NOT_CONFIRMED |
| TS-Hong-Chau-Dong-Son-Tue.ttl | DILA_UNRESOLVED |
| TS-Hong-Chau-Me-Linh.ttl | DILA_NOT_CONFIRMED |
| TS-Hong-Chau-Phat-Dat.ttl | IDENTIFIER_DIFFERENT, FILENAME_SUBJECT_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Hong-Chau-Tay-Son-Luong.ttl | DILA_NOT_CONFIRMED |
| TS-Hong-Chau-Thuy-Lao.ttl | DILA_UNRESOLVED |
| TS-Hong-Phuoc-Tu-Giao.ttl | DILA_UNRESOLVED |
| TS-Hue-Doan.ttl | IDENTIFIER_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Hung-Duong-Hien.ttl | DILA_UNRESOLVED, GENERATION_NOT_COMPARABLE, GENERATION_REVIEW |
| TS-Hung-Giao-Than.ttl | DILA_UNRESOLVED |
| TS-Hung-Giao-Tue-Thuan.ttl | DILA_UNRESOLVED |
| TS-Hung-Hoa-Phap-Trung.ttl | DILA_NOT_CONFIRMED |
| TS-Hung-Hoa-Thieu-Thanh.ttl | GENERATION_REVIEW, DILA_NOT_CONFIRMED |
| TS-Hung-Hoa-Ton-Tuong.ttl | DILA_NOT_CONFIRMED |
| TS-Hung-Phuoc-Khuong-Nguyen.ttl | DILA_UNRESOLVED |
| TS-Hung-Quoc-Khe-Nha.ttl | DILA_NOT_CONFIRMED |
| TS-Huong-Duong-Hy-An.ttl | DILA_UNRESOLVED |
| TS-Huong-Son-Duy-Duc.ttl | DILA_NOT_CONFIRMED |
| TS-Huu-Thanh-Phap-Cu.ttl | DILA_UNRESOLVED |
| TS-Huyen-Sa-Hop-Van.ttl | DILA_NOT_CONFIRMED |
| TS-Huyen-Sa-Tang-Chieu.ttl | DILA_NOT_CONFIRMED |
| TS-Huyen-Sach.ttl | DILA_NOT_CONFIRMED |
| TS-Ich-Chau-Truong-Binh.ttl | DILA_UNRESOLVED |
| TS-Ich-Chau-Ung-Thien.ttl | DILA_NOT_CONFIRMED |
| TS-Ke-Lam-Dao-Nghia.ttl | DILA_NOT_CONFIRMED |
| TS-Khai-Nguyen-Chi-Khiem.ttl | DILA_NOT_CONFIRMED |
| TS-Khai-Nguyen-Tu-Kha.ttl | DILA_UNRESOLVED, ENDPOINT_NO_MAIN_FILE |
| TS-Khai-Phuoc-Dao-Ninh.ttl | DILA_NOT_CONFIRMED |
| TS-Khai-Phuoc-Tong-Triet.ttl | GENERATION_NOT_COMPARABLE, DILA_NOT_CONFIRMED |
| TS-Khai-Thien-Dao-Khiem.ttl | DILA_NOT_CONFIRMED |
| TS-Khai-Tien-Hanh-Anh.ttl | DILA_UNRESOLVED |
| TS-Kham-Son-Pho-So.ttl | GENERATION_REVIEW |
| TS-Khanh-Thien-Pho-Nang.ttl | DILA_NOT_CONFIRMED |
| TS-Khanh-Thien-Thu-Long.ttl | FILENAME_SUBJECT_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Khanh-Thien-Tong-Chan.ttl | DILA_NOT_CONFIRMED |
| TS-Khoan-Tinh.ttl | DILA_UNRESOLVED |
| TS-Khong-That-Tri-Thong.ttl | DILA_NOT_CONFIRMED |
| TS-Khuong-Son-Phuong.ttl | DILA_NOT_CONFIRMED |
| TS-Kiem-Mon-Nam-Tu-Tao.ttl | DILA_NOT_CONFIRMED |
| TS-Kien-Chau-Xu-Triet.ttl | DILA_UNRESOLVED |
| TS-Kien-Long-Chieu-Khanh.ttl | DILA_NOT_CONFIRMED |
| TS-Kim-Chau-Thao.ttl | DILA_NOT_CONFIRMED |
| TS-Kim-Lang-Phap-Tri.ttl | IDENTIFIER_DIFFERENT |
| TS-Kim-Son-Dam-Dinh.ttl | DILA_NOT_CONFIRMED |
| TS-Kim-Son-Vien-Thong.ttl | GENERATION_REVIEW, DILA_NOT_CONFIRMED |
| TS-Kim-Thang-Van.ttl | DILA_NOT_CONFIRMED |
| TS-Kinh-Son-Bao-An.ttl | DILA_NOT_CONFIRMED |
| TS-Kinh-Son-Dao-Kham.ttl | IDENTIFIER_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Kinh-Son-Dao-Xung.ttl | DILA_UNRESOLVED |
| TS-Kinh-Son-Giam-Tong.ttl | DILA_UNRESOLVED |
| TS-Kinh-Son-Hanh-Doan.ttl | DILA_UNRESOLVED |
| TS-Kinh-Son-Hong-Nhan.ttl | DILA_NOT_CONFIRMED |
| TS-Kinh-Son-Lieu-Minh.ttl | DILA_NOT_CONFIRMED |
| TS-Kinh-Son-Nguyen-Hy.ttl | DILA_NOT_CONFIRMED |
| TS-Kinh-Son-Nhu-Diem.ttl | DILA_NOT_CONFIRMED |
| TS-Kinh-Son-Tri-Sach.ttl | DILA_NOT_CONFIRMED |
| TS-Kinh-Trieu-Duy-Khoan.ttl | DILA_UNRESOLVED |
| TS-Kinh-Trieu-Hoang-Bien.ttl | DILA_NOT_CONFIRMED |
| TS-Kinh-Trieu-Hung-Binh.ttl | DILA_NOT_CONFIRMED |
| TS-Kinh-Trieu-Me-Ho.ttl | DILA_UNRESOLVED |
| TS-Kinh-Trieu-Thao-Duong.ttl | DILA_NOT_CONFIRMED |
| TS-La-Han-He-Nam.ttl | DILA_NOT_CONFIRMED |
| TS-La-Phu-Hy.ttl | DILA_UNRESOLVED |
| TS-Lac-Dam-Buu-Long.ttl | DILA_UNRESOLVED |
| TS-Lac-Dam-Canh-Tuong.ttl | GENERATION_NOT_COMPARABLE, DILA_NOT_CONFIRMED |
| TS-Lac-Dam-Duy-Kien.ttl | DILA_NOT_CONFIRMED |
| TS-Lac-Dam-Hieu-Nguyet.ttl | DILA_NOT_CONFIRMED |
| TS-Lac-Dam-Hong-Anh.ttl | DILA_NOT_CONFIRMED |
| TS-Lac-Dam-Khac-Van.ttl | DILA_NOT_CONFIRMED |
| TS-Lac-Dam-Phap-Hoi.ttl | DILA_NOT_CONFIRMED |
| TS-Lac-Dam-Thien-Thanh.ttl | DILA_NOT_CONFIRMED |
| TS-Lac-Dam-Thuong-Hung.ttl | DILA_NOT_CONFIRMED |
| TS-Lac-Kinh-Hac-Gian.ttl | DILA_UNRESOLVED |
| TS-Lang-Chau-Co-De.ttl | DILA_NOT_CONFIRMED |
| TS-Lang-Chau-Hoai-Chinh.ttl | DILA_NOT_CONFIRMED |
| TS-Lang-Nha-Phuong-Duyet.ttl | DILA_NOT_CONFIRMED |
| TS-Lang-Nha-Tri-Thien.ttl | DILA_NOT_CONFIRMED |
| TS-Lang-Nha-Tue-Giac.ttl | DILA_NOT_CONFIRMED |
| TS-Lang-Nha-Vinh-Khoi.ttl | FILENAME_SUBJECT_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Lang-Son-Tue-On.ttl | DILA_NOT_CONFIRMED |
| TS-Lenh-Nhan-Minh-That.ttl | DILA_NOT_CONFIRMED |
| TS-Liem-Tuyen-Dam-Tu.ttl | DILA_NOT_CONFIRMED |
| TS-Lien-Van-Dao-Nang.ttl | DILA_NOT_CONFIRMED |
| TS-Lieu-Quan-Thiet-Duyet.ttl | FILENAME_SUBJECT_DIFFERENT, DILA_UNRESOLVED, ENDPOINT_NO_MAIN_FILE |
| TS-Linh-An-Chi-Thien.ttl | DILA_NOT_CONFIRMED |
| TS-Linh-An-Dao-An.ttl | DILA_NOT_CONFIRMED |
| TS-Linh-An-Duc-Tu.ttl | DILA_NOT_CONFIRMED |
| TS-Linh-An-Lieu-Dien.ttl | DILA_NOT_CONFIRMED |
| TS-Linh-An-Sung-Nhac.ttl | DILA_NOT_CONFIRMED, GENERATION_REVIEW |
| TS-Linh-An-Tue-Vien.ttl | DILA_NOT_CONFIRMED |
| TS-Linh-Cuu.ttl | FILENAME_SUBJECT_DIFFERENT, SUBJECT_COLLISION |
| TS-Linh-Kieu.ttl | DILA_NOT_CONFIRMED |
| TS-Linh-Nham-Lieu-Tanh.ttl | DILA_UNRESOLVED |
| TS-Linh-Nham-Trong-Xac.ttl | DILA_UNRESOLVED |
| TS-Linh-Son-Ngan-Van.ttl | GENERATION_REVIEW |
| TS-Linh-Thuu-Tue-Giac.ttl | DILA_NOT_CONFIRMED |
| TS-Linh-Van-Chi-Can.ttl | DILA_NOT_CONFIRMED |
| TS-Lo-Son-Phap-Chan.ttl | GENERATION_NOT_COMPARABLE, DILA_NOT_CONFIRMED |
| TS-Lo-To-Bao-Van.ttl | DILA_NOT_CONFIRMED |
| TS-Loc-Mon-Tue-Chieu.ttl | DILA_NOT_CONFIRMED |
| TS-Loc-Thanh.ttl | DILA_UNRESOLVED |
| TS-Loi-Son.ttl | DILA_NOT_CONFIRMED |
| TS-Long-An-Nhu-Hai.ttl | DILA_NOT_CONFIRMED |
| TS-Long-Dam-Sung-Tin.ttl | DILA_NOT_CONFIRMED |
| TS-Long-Dam-Tri-Vien.ttl | DILA_NOT_CONFIRMED |
| TS-Long-Hoa-Ban.ttl | DILA_UNRESOLVED |
| TS-Long-Hoa-Dao-So.ttl | DILA_NOT_CONFIRMED |
| TS-Long-Khanh-Khanh-Nhan.ttl | DILA_NOT_CONFIRMED |
| TS-Long-Minh-Hien.ttl | DILA_NOT_CONFIRMED |
| TS-Long-Mon-Chieu.ttl | DILA_UNRESOLVED |
| TS-Long-Nha-Tong-Mat.ttl | DILA_NOT_CONFIRMED |
| TS-Long-Tuong-Hy-Lien.ttl | DILA_UNRESOLVED |
| TS-Long-Tuong-Si-Khue.ttl | DILA_NOT_CONFIRMED |
| TS-Long-Tuyen-Quy.ttl | DILA_UNRESOLVED |
| TS-Long-Vuong-Thien-Tuy.ttl | DILA_UNRESOLVED |
| TS-Lung-Chau-Quoc-Thanh-Phung.ttl | DILA_UNRESOLVED |
| TS-Lung-Nhung-Tri-Vien.ttl | ENDPOINT_NO_MAIN_FILE |
| TS-Luong-Phong-Dong-Uyen.ttl | DILA_NOT_CONFIRMED |
| TS-Luong-Son-Hoai.ttl | DILA_UNRESOLVED |
| TS-Luong-Son-Su-Vien.ttl | DILA_NOT_CONFIRMED |
| TS-Ly-Thon-Tu-Man.ttl | DILA_NOT_CONFIRMED |
| TS-Ma-Coc-Bao-Triet.ttl | DILA_NOT_CONFIRMED |
| TS-Ma-Dau-Than-Tang.ttl | DILA_NOT_CONFIRMED |
| TS-Ma-To-Dao-Nhat.ttl | IDENTIFIER_DIFFERENT |
| TS-Mat-Am-Han-Kiet.ttl | DILA_UNRESOLVED |
| TS-Me-Lanh.ttl | DILA_UNRESOLVED |
| TS-Me-Thuong.ttl | DILA_UNRESOLVED |
| TS-Minh-Chau-Quan-Tong.ttl | IDENTIFIER_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Minh-Hai-Phap-Bao.ttl | DILA_UNRESOLVED, GENERATION_NOT_COMPARABLE |
| TS-Minh-Hanh-Tai-Tai.ttl | DILA_UNRESOLVED, ENDPOINT_NO_MAIN_FILE |
| TS-Minh-Hoang-Tu-Dung.ttl | MULTIPLE_MAIN, FILENAME_SUBJECT_DIFFERENT, SUBJECT_COLLISION |
| TS-Minh-Khe-Dao-Hanh.ttl | FILENAME_SUBJECT_DIFFERENT, DILA_UNRESOLVED |
| TS-Minh-Nhan-Dam-Ngoan.ttl | DILA_NOT_CONFIRMED |
| TS-Mong-Khe.ttl | DILA_UNRESOLVED |
| TS-Mong-Son-Dao-Minh.ttl | IDENTIFIER_DIFFERENT, FILENAME_SUBJECT_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Muc-Chau-Dao-Minh.ttl | DILA_NOT_CONFIRMED |
| TS-Muc-Chau-Tran-Thao.ttl | DILA_NOT_CONFIRMED |
| TS-Nam-Dai-Duang-Cung.ttl | FILENAME_SUBJECT_DIFFERENT |
| TS-Nam-Dang-Phap-Khong.ttl | DILA_NOT_CONFIRMED |
| TS-Nam-Duong-Hue-Trung.ttl | IDENTIFIER_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Nam-Minh-Dao-Quang.ttl | DILA_NOT_CONFIRMED |
| TS-Nam-Nguyen-Dao-Minh.ttl | DILA_NOT_CONFIRMED |
| TS-Nam-Nhac-Hoai-Nhuong.ttl | IDENTIFIER_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Nam-Nhac-Minh-Toan.ttl | IDENTIFIER_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Nam-Nham-Thang.ttl | DILA_NOT_CONFIRMED |
| TS-Nam-Phong-Van-Bien.ttl | DILA_NOT_CONFIRMED |
| TS-Nam-Thap-Quang-Dung.ttl | IDENTIFIER_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Nam-Thien-Vo-Nhiem.ttl | DILA_NOT_CONFIRMED |
| TS-Nang-Nhan-Thieu-Ngo.ttl | DILA_NOT_CONFIRMED |
| TS-Nang-Nhan-To-Nguyen.ttl | DILA_NOT_CONFIRMED |
| TS-Nga-Ho-Dai-Nghia.ttl | DILA_NOT_CONFIRMED |
| TS-Ngac-Chau-Phu-Dung.ttl | DILA_NOT_CONFIRMED |
| TS-Ngac-Chau-Vo-Dang.ttl | DILA_NOT_CONFIRMED |
| TS-Ngo-Hung-Phap-Hai.ttl | IDENTIFIER_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Ngo-Thanh-Cu-Tinh.ttl | FILENAME_SUBJECT_DIFFERENT, DILA_UNRESOLVED |
| TS-Ngo-Thap-Tam.ttl | DILA_UNRESOLVED |
| TS-Ngo-Tu-Tam-Khong.ttl | DILA_NOT_CONFIRMED |
| TS-Ngoc-Tuyen-Dam-Y.ttl | DILA_NOT_CONFIRMED |
| TS-Ngoc-Tuyen-Ngo-Khong.ttl | DILA_NOT_CONFIRMED |
| TS-Ngoc-Tuyen-Than-Tu.ttl | IDENTIFIER_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Ngoc-Tuyen-Thien-Sieu.ttl | DILA_UNRESOLVED, GENERATION_REVIEW |
| TS-Ngoc-Tuyen-Tong-Lien.ttl | DILA_NOT_CONFIRMED |
| TS-Ngu-Dai-An-Phong.ttl | DILA_NOT_CONFIRMED |
| TS-Ngu-Dai-Cu-Phuong.ttl | IDENTIFIER_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Ngu-Dai-Tri-Thong.ttl | DILA_NOT_CONFIRMED |
| TS-Ngu-Due-Linh-Mac.ttl | DILA_UNRESOLVED |
| TS-Ngu-Phong-Thuong-Quan.ttl | DILA_UNRESOLVED |
| TS-Ngu-To-Bieu-Tu.ttl | DILA_NOT_CONFIRMED |
| TS-Ngu-To-Hieu-Thuong.ttl | DILA_NOT_CONFIRMED |
| TS-Ngu-To-Phap-Dien.ttl | DILA_NOT_CONFIRMED |
| TS-Nguong-Son-Hanh-Vy.ttl | DILA_UNRESOLVED |
| TS-Nguong-Son-Thanh-Gian.ttl | DILA_NOT_CONFIRMED |
| TS-Nguu-Dau-Hue-Phuong.ttl | IDENTIFIER_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Nguu-Dau-Hue-Trung.ttl | IDENTIFIER_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Nguu-Dau-Phap-Dung.ttl | IDENTIFIER_DIFFERENT, GENERATION_REVIEW, DILA_NOT_CONFIRMED |
| TS-Nguu-Dau-Tri-Nham.ttl | IDENTIFIER_DIFFERENT, GENERATION_REVIEW, DILA_NOT_CONFIRMED |
| TS-Nguu-Dau-Tri-Oai.ttl | IDENTIFIER_DIFFERENT |
| TS-Nguyen-Le.ttl | DILA_NOT_CONFIRMED |
| TS-Nguyen-Thieu-Sieu-Bach.ttl | DILA_UNRESOLVED, GENERATION_NOT_COMPARABLE |
| TS-Nguyet-Chau-Than-Giam.ttl | DILA_UNRESOLVED |
| TS-Nguyet-Chuong-Tri-Uyen.ttl | DILA_NOT_CONFIRMED |
| TS-Nguyet-Danh-Dao-Luan.ttl | DILA_NOT_CONFIRMED |
| TS-Nguyet-Khue-Dieu-Trung.ttl | FILENAME_SUBJECT_DIFFERENT, ENDPOINT_NO_MAIN_FILE, DILA_NOT_CONFIRMED |
| TS-Nhac-Son-Am-Chu-To.ttl | DILA_UNRESOLVED |
| TS-Nhan-Tho-Tu-Tran.ttl | DILA_NOT_CONFIRMED |
| TS-Nhat-Tu.ttl | DILA_UNRESOLVED |
| TS-O-Cuu.ttl | DILA_UNRESOLVED |
| TS-O-Nhai-So.ttl | DILA_UNRESOLVED |
| TS-On-Chau-Phat-Ao.ttl | DILA_NOT_CONFIRMED |
| TS-Phap-Kinh-Ngo-Trung.ttl | DILA_UNRESOLVED |
| TS-Phap-Luan-Ngan-Tu.ttl | GENERATION_NOT_COMPARABLE |
| TS-Phap-Luan-Ung-Doan.ttl | DILA_NOT_CONFIRMED |
| TS-Phap-Luan-Van-Duc.ttl | DILA_NOT_CONFIRMED |
| TS-Phap-Nhu.ttl | IDENTIFIER_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Phap-So.ttl | DILA_UNRESOLVED |
| TS-Phap-Tanh-An-Tong.ttl | IDENTIFIER_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Phap-Thach-Tue-Khong.ttl | DILA_NOT_CONFIRMED |
| TS-Phat-Bao-Phap-Hoa.ttl | DILA_UNRESOLVED |
| TS-Phat-Quang-Nhu-Man.ttl | DILA_NOT_CONFIRMED |
| TS-Phat-Quat-Duy-Tac.ttl | IDENTIFIER_DIFFERENT, DILA_NOT_CONFIRMED, ENDPOINT_NO_MAIN_FILE |
| TS-Phat-Y-Linh-Nhac.ttl | DILA_UNRESOLVED, SUBJECT_COLLISION |
| TS-Pho-Chieu-Hieu-Kham.ttl | GENERATION_NOT_COMPARABLE |
| TS-Pho-Minh-Duc-Dung.ttl | DILA_NOT_CONFIRMED |
| TS-Pho-Tu-Sung-Tran.ttl | DILA_NOT_CONFIRMED |
| TS-Phong-Huyet-Dien-Chieu.ttl | SUBJECT_COLLISION |
| TS-Phu-Boi.ttl | DILA_NOT_CONFIRMED |
| TS-Phu-Dung-Thai-Duc.ttl | DILA_UNRESOLVED |
| TS-Phu-Son-Duc-Tuyen.ttl | DILA_NOT_CONFIRMED |
| TS-Phu-Son-Phap-Vien.ttl | GENERATION_REVIEW |
| TS-Phuc-Chau-Dai-An.ttl | MAIN_UNSUPPORTED |
| TS-Phuc-Nguu-Tu-Tai.ttl | DILA_NOT_CONFIRMED |
| TS-Phuc-Tien-Nhan-Kiem.ttl | IDENTIFIER_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Phung-The-Tue-Quan.ttl | DILA_NOT_CONFIRMED |
| TS-Phung-Tuong-Thach-Tru.ttl | FILENAME_SUBJECT_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Phuoc-Chau-Dai-An.ttl | FILENAME_SUBJECT_DIFFERENT, SUBJECT_COLLISION |
| TS-Phuoc-Chau-Pho-Quang.ttl | DILA_NOT_CONFIRMED |
| TS-Phuoc-Chau-Song-Phong.ttl | DILA_NOT_CONFIRMED |
| TS-Phuoc-Khe.ttl | DILA_UNRESOLVED |
| TS-Phuoc-Nghiem-Bao-Tong.ttl | DILA_NOT_CONFIRMED |
| TS-Phuoc-Nghiem-Tri.ttl | DILA_NOT_CONFIRMED |
| TS-Phuoc-Nghiem-Tu-Cam.ttl | DILA_NOT_CONFIRMED |
| TS-Phuoc-Nghiem-Van-Dien.ttl | DILA_UNRESOLVED |
| TS-Phuong-Bien.ttl | IDENTIFIER_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Phuong-Lai-Xuong-Vien.ttl | DILA_UNRESOLVED, GENERATION_REVIEW |
| TS-Phuong-Son-Tue-Bao.ttl | DILA_NOT_CONFIRMED |
| TS-Phuong-Van-Minh-Thong.ttl | DILA_NOT_CONFIRMED |
| TS-Qua-Lang-Tuyen-Thap.ttl | IDENTIFIER_DIFFERENT |
| TS-Quan-Khe-Chi-Nhan.ttl | DILA_NOT_CONFIRMED, GENERATION_NOT_COMPARABLE |
| TS-Quan-Son-Giac.ttl | DILA_NOT_CONFIRMED |
| TS-Quan-Son-Pho-Tinh.ttl | DILA_NOT_CONFIRMED |
| TS-Quang-Chau-Chi-Dao.ttl | IDENTIFIER_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Quang-Giao-Ke-Chan.ttl | DILA_UNRESOLVED |
| TS-Quang-Hieu-Dam.ttl | DILA_UNRESOLVED |
| TS-Quang-Hieu-Duc-Chu.ttl | DILA_NOT_CONFIRMED |
| TS-Quang-Hieu-Duy-Sang.ttl | DILA_NOT_CONFIRMED |
| TS-Quang-Hieu-Ngo-So.ttl | DILA_NOT_CONFIRMED |
| TS-Quang-Hieu-Pho-An.ttl | DILA_NOT_CONFIRMED |
| TS-Quang-Hieu-Qua-Man.ttl | DILA_NOT_CONFIRMED |
| TS-Quang-Hieu-Tri-Vien.ttl | DILA_NOT_CONFIRMED |
| TS-Quang-Hieu-Tue-Lan.ttl | GENERATION_NOT_COMPARABLE, DILA_NOT_CONFIRMED |
| TS-Quang-Nam-Dao-Ngo.ttl | GENERATION_REVIEW, DILA_NOT_CONFIRMED |
| TS-Quang-Nam-Dao-Thuong.ttl | GENERATION_REVIEW, DILA_NOT_CONFIRMED |
| TS-Quang-Nguyet-Duc-Bao.ttl | DILA_NOT_CONFIRMED |
| TS-Quang-Phap-Nguyen.ttl | DILA_NOT_CONFIRMED |
| TS-Quang-Quoc-Van-Tang.ttl | FILENAME_SUBJECT_DIFFERENT, GENERATION_REVIEW |
| TS-Quang-Tue-Duc-Tuyen.ttl | DILA_NOT_CONFIRMED |
| TS-Quoc-Thanh-Hanh-Co.ttl | DILA_UNRESOLVED |
| TS-Quy-Duong-Vo-Lieu.ttl | DILA_NOT_CONFIRMED |
| TS-Quy-Phong-Tu-Quynh.ttl | DILA_UNRESOLVED |
| TS-Quy-Son-Hieu-Tan.ttl | DILA_NOT_CONFIRMED |
| TS-Quy-Son-Linh-Huu.ttl | DILA_NOT_CONFIRMED |
| TS-Quy-Son-Tri-Chan.ttl | DILA_NOT_CONFIRMED |
| TS-Quy-Tong-Kha-Tuyen.ttl | DILA_NOT_CONFIRMED |
| TS-Quy-Tong-Tri-Thuong.ttl | DILA_NOT_CONFIRMED |
| TS-Sieu-Hoa-Tinh.ttl | DILA_UNRESOLVED |
| TS-So-An-Hue-Phuong.ttl | DILA_NOT_CONFIRMED |
| TS-So-Son-Nhu-Ban.ttl | DILA_NOT_CONFIRMED |
| TS-Son-Chu-Dong-Lam-Uc.ttl | DILA_UNRESOLVED |
| TS-Son-Chu-Khai-Thanh-Bao-Tinh.ttl | FILENAME_SUBJECT_DIFFERENT |
| TS-Song-Lam-Bang.ttl | FILENAME_SUBJECT_DIFFERENT, DILA_UNRESOLVED |
| TS-Song-Lam-Duc-Dung.ttl | DILA_NOT_CONFIRMED |
| TS-Song-Lanh-Hoa.ttl | DILA_UNRESOLVED |
| TS-Song-Phong-Canh-Te.ttl | DILA_NOT_CONFIRMED |
| TS-Song-Phong-Co.ttl | DILA_NOT_CONFIRMED |
| TS-Song-Phong-Tinh-Hoi.ttl | GENERATION_REVIEW |
| TS-Sung-Phuoc-Dien-Giao.ttl | DILA_NOT_CONFIRMED |
| TS-Sung-Thang-Ky.ttl | DILA_UNRESOLVED |
| TS-Tac-Xuyen.ttl | DILA_NOT_CONFIRMED |
| TS-Tam-Binh-Nghia-Trung.ttl | DILA_NOT_CONFIRMED |
| TS-Tam-Giac-Linh-Khue.ttl | DILA_NOT_CONFIRMED |
| TS-Tam-Giac-Tue-Trach.ttl | DILA_NOT_CONFIRMED |
| TS-Tam-Giao-Tri-Tung.ttl | DILA_NOT_CONFIRMED |
| TS-Tam-Tang-Na-De.ttl | IDENTIFIER_DIFFERENT |
| TS-Tam-Thanh-Hue-Nhien.ttl | DILA_NOT_CONFIRMED |
| TS-Tam-Thanh-Ke-Xuong.ttl | DILA_NOT_CONFIRMED |
| TS-Tam-To-Phap-Tong.ttl | DILA_NOT_CONFIRMED |
| TS-Tan-Ca-La-Tri.ttl | FILENAME_SUBJECT_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Tan-Chau-Hoac-Son.ttl | DILA_UNRESOLVED |
| TS-Tan-La-Dai-Chung.ttl | DILA_NOT_CONFIRMED |
| TS-Tan-La-Phap-Lang.ttl | IDENTIFIER_DIFFERENT, ENDPOINT_NO_MAIN_FILE |
| TS-Tang-Chu-Pho-Dung.ttl | DILA_UNRESOLVED |
| TS-Tang-Na.ttl | IDENTIFIER_DIFFERENT |
| TS-Tao-Khe-Linh-Thao.ttl | IDENTIFIER_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Tay-Kinh-Nghia-Phuoc.ttl | IDENTIFIER_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Tay-Su-Cung-Than.ttl | DILA_NOT_CONFIRMED |
| TS-Tay-Thap-Quang-Muc.ttl | DILA_NOT_CONFIRMED |
| TS-Tay-Thien-Danh-Nhu.ttl | DILA_UNRESOLVED |
| TS-Tay-Thien-Hy-Tu.ttl | DILA_UNRESOLVED |
| TS-Tay-Thien-Thu-Tinh.ttl | DILA_NOT_CONFIRMED |
| TS-Tay-Viem-Dam-Tang.ttl | DILA_NOT_CONFIRMED |
| TS-Tay-Vuc-Quat-Da-Tam-Tang.ttl | IDENTIFIER_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Te-Phong.ttl | DILA_UNRESOLVED |
| TS-Thach-Co-Dong-Chau.ttl | DILA_NOT_CONFIRMED |
| TS-Thach-Cung-Hue-Tang.ttl | DILA_NOT_CONFIRMED |
| TS-Thach-Cuu.ttl | SUBJECT_COLLISION |
| TS-Thach-Dau-Tu-Hoi.ttl | DILA_NOT_CONFIRMED, GENERATION_REVIEW |
| TS-Thach-Lam.ttl | DILA_NOT_CONFIRMED |
| TS-Thach-Mon-Nhac.ttl | FILENAME_SUBJECT_DIFFERENT, DILA_UNRESOLVED |
| TS-Thach-Mon-Thu-Tan.ttl | GENERATION_REVIEW |
| TS-Thach-Phat-Hien-Trong.ttl | DILA_UNRESOLVED |
| TS-Thach-Phat-Tue-Minh.ttl | DILA_NOT_CONFIRMED |
| TS-Thach-Suong-Dai-Thien.ttl | DILA_NOT_CONFIRMED |
| TS-Thach-Suong-Khanh-Chu.ttl | DILA_NOT_CONFIRMED, GENERATION_REVIEW |
| TS-Thach-Suong-So-Vien.ttl | DILA_NOT_CONFIRMED |
| TS-Thach-Suong-Tanh-Khong.ttl | DILA_UNRESOLVED |
| TS-Thach-Suong-Tong-Giam.ttl | DILA_NOT_CONFIRMED |
| TS-Thach-Ton-Thu-Ton.ttl | FILENAME_SUBJECT_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Thai-Binh-Hue-Can-Phat-Giam.ttl | DILA_UNRESOLVED |
| TS-Thai-Son-Tri-Kien.ttl | DILA_NOT_CONFIRMED |
| TS-Thai-Tu-Dao-Nhat.ttl | DILA_NOT_CONFIRMED |
| TS-Thai-Tu-Dong-Quang.ttl | DILA_NOT_CONFIRMED |
| TS-Than-Danh-Hong-Nhan.ttl | DILA_UNRESOLVED |
| TS-Than-Nhien.ttl | DILA_NOT_CONFIRMED |
| TS-Thang-Nghiep-Duy-Huong.ttl | DILA_UNRESOLVED |
| TS-Thang-Nhan-Ham-Tinh.ttl | DILA_UNRESOLVED |
| TS-Thanh-An-Thanh-Nguyen.ttl | DILA_NOT_CONFIRMED |
| TS-Thanh-Binh-Linh-Tuan.ttl | DILA_NOT_CONFIRMED |
| TS-Thanh-Luong-Duc-Hong.ttl | DILA_UNRESOLVED |
| TS-Thanh-Nguyen-Duy-Tin.ttl | DILA_NOT_CONFIRMED |
| TS-Thanh-Nguyen-Hanh-Tu.ttl | DILA_NOT_CONFIRMED |
| TS-Thanh-Nguyen-Nhu.ttl | DILA_NOT_CONFIRMED |
| TS-Thanh-Thien-Hoang-Chinh.ttl | IDENTIFIER_DIFFERENT, ENDPOINT_NO_MAIN_FILE |
| TS-Thanh-Vien-Phat-Nhan.ttl | DILA_UNRESOLVED |
| TS-Thao-Xao-Thong-Thanh.ttl | DILA_UNRESOLVED |
| TS-Thao-Y-Nham-Khanh.ttl | DILA_NOT_CONFIRMED |
| TS-Thien-Dong-Dam-Hoa.ttl | DILA_NOT_CONFIRMED |
| TS-Thien-Dong-Pho-Giao.ttl | DILA_NOT_CONFIRMED |
| TS-Thien-Dong-Thanh-Toai.ttl | GENERATION_NOT_COMPARABLE |
| TS-Thien-Dong-Tinh-Toan.ttl | DILA_NOT_CONFIRMED |
| TS-Thien-Hoang-Dao-Ngo.ttl | DILA_NOT_CONFIRMED |
| TS-Thien-Ninh-Pham-Tu.ttl | DILA_NOT_CONFIRMED |
| TS-Thien-Ninh-Quynh.ttl | DILA_UNRESOLVED |
| TS-Thien-Phong-Giac.ttl | DILA_NOT_CONFIRMED |
| TS-Thien-Phuc.ttl | IDENTIFIER_DIFFERENT |
| TS-Thien-Thai-Van-Cu-Tri.ttl | IDENTIFIER_DIFFERENT |
| TS-Thien-Tru-Sung-Hue.ttl | IDENTIFIER_DIFFERENT |
| TS-Thien-Tu-Thuong-Khai.ttl | DILA_NOT_CONFIRMED |
| TS-Thien-Tue-Bao-Chuong.ttl | DILA_UNRESOLVED, GENERATION_NOT_COMPARABLE |
| TS-Thien-Vuong-Dao-Ngo.ttl | DILA_NOT_CONFIRMED |
| TS-Thiep-Chau-Mau-Nguyen.ttl | DILA_NOT_CONFIRMED |
| TS-Thieu-Chau-Khong-Nguyen.ttl | DILA_UNRESOLVED |
| TS-Thieu-Chau-Phap-Hai.ttl | IDENTIFIER_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Tho-Chau-Dao-Tho.ttl | IDENTIFIER_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Tho-Chau-Thieu-Tong.ttl | FILENAME_SUBJECT_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Tho-Chau-Tri-Thong.ttl | IDENTIFIER_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Tho-Ninh-Thien-Tu.ttl | DILA_NOT_CONFIRMED |
| TS-Tho-Thanh-So-Van.ttl | DILA_NOT_CONFIRMED |
| TS-Thu-Dao-Tuc-Tien.ttl | DILA_UNRESOLVED |
| TS-Thu-Son-Hoai-Chi.ttl | DILA_NOT_CONFIRMED |
| TS-Thu-Son-Xu-Khe.ttl | GENERATION_REVIEW, DILA_NOT_CONFIRMED |
| TS-Thua-Hy-Ung-Duyet.ttl | GENERATION_NOT_COMPARABLE, DILA_NOT_CONFIRMED |
| TS-Thua-Thien-Tri-Duc.ttl | DILA_NOT_CONFIRMED |
| TS-Thua-Thien-Tu-Hien.ttl | DILA_NOT_CONFIRMED |
| TS-Thua-Thien-Tue-Lien.ttl | DILA_NOT_CONFIRMED |
| TS-Thuan-Kiet-Tanh-Khue.ttl | DILA_UNRESOLVED |
| TS-Thuong-Chau-Me-Thuong.ttl | DILA_UNRESOLVED |
| TS-Thuong-Lam-Thuan.ttl | DILA_UNRESOLVED |
| TS-Thuong-Phong-Ban-Tai.ttl | DILA_UNRESOLVED |
| TS-Thuong-Phong-Tho-Tu.ttl | DILA_NOT_CONFIRMED |
| TS-Thuong-Phong-Tue-Hoa.ttl | DILA_UNRESOLVED |
| TS-Thuong-Phuong-Nhat-Ich.ttl | DILA_NOT_CONFIRMED |
| TS-Thuy-Khong.ttl | DILA_UNRESOLVED |
| TS-Thuy-Nham-Nhu-Thang.ttl | GENERATION_NOT_COMPARABLE, DILA_NOT_CONFIRMED |
| TS-Thuy-Nham-Quang-Muc.ttl | DILA_NOT_CONFIRMED |
| TS-Thuy-Vi-Vo-Hoc.ttl | DILA_NOT_CONFIRMED |
| TS-Tich-Thuy-Vinh.ttl | DILA_UNRESOLVED |
| TS-Tiem-Nguyen-Trong-Hung.ttl | DILA_NOT_CONFIRMED |
| TS-Tien-Phuc-Dao-Sinh.ttl | GENERATION_REVIEW |
| TS-Tien-Phuoc-Dao-Anh.ttl | DILA_NOT_CONFIRMED |
| TS-Tien-Phuoc-Luong.ttl | DILA_UNRESOLVED |
| TS-Tien-Phuoc-Ngo-Ban.ttl | DILA_NOT_CONFIRMED |
| TS-Tien-Thien.ttl | DILA_NOT_CONFIRMED |
| TS-Tieu-Dao.ttl | DILA_NOT_CONFIRMED |
| TS-Tieu-Ong-Dieu-Tram.ttl | FILENAME_SUBJECT_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Tin-Chau-Tri-Thuong.ttl | IDENTIFIER_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Tin-Tuong-Gioi-Tu.ttl | DILA_NOT_CONFIRMED |
| TS-Tin-Tuong-Tong-Hien.ttl | DILA_NOT_CONFIRMED |
| TS-Tinh-Do-Thien-Tu.ttl | DILA_NOT_CONFIRMED |
| TS-Tinh-Nhan-Dao-Trang.ttl | DILA_UNRESOLVED |
| TS-Tinh-Tru-Chan-Tinh.ttl | DILA_NOT_CONFIRMED |
| TS-Tinh-Tu-Cu-Gian.ttl | DILA_NOT_CONFIRMED |
| TS-Tinh-Tu-Dam-Mat.ttl | DILA_NOT_CONFIRMED |
| TS-Tinh-Tu-Ngan-Sung.ttl | DILA_NOT_CONFIRMED |
| TS-Tinh-Tu-Van.ttl | DILA_UNRESOLVED |
| TS-To-An-Mat-Hoang.ttl | DILA_UNRESOLVED, ENDPOINT_NO_MAIN_FILE |
| TS-To-Dat-Tri-Tam.ttl | DILA_UNRESOLVED |
| TS-To-Nhan-Thien-Truong.ttl | DILA_UNRESOLVED |
| TS-To-Tong-Vien-Quang.ttl | ENDPOINT_NO_MAIN_FILE |
| TS-Ton-Gia-Mat-Dien-De-Ca.ttl | IDENTIFIER_DIFFERENT, FILENAME_SUBJECT_DIFFERENT |
| TS-Tong-Son.ttl | DILA_UNRESOLVED |
| TS-Tong-Thien-Ban-Thuy.ttl | DILA_UNRESOLVED |
| TS-Trac-Chau-Cap-Y.ttl | DILA_NOT_CONFIRMED |
| TS-Tran-Chau-Dai-Bi.ttl | DILA_NOT_CONFIRMED |
| TS-Tran-Chau-Kim-Nguu.ttl | DILA_NOT_CONFIRMED |
| TS-Tran-Chau-Van-Tue.ttl | DILA_NOT_CONFIRMED |
| TS-Tri-Chau-Lo-To-Giao.ttl | GENERATION_NOT_COMPARABLE, DILA_NOT_CONFIRMED |
| TS-Tri-Gia-Chan-Tu.ttl | DILA_NOT_CONFIRMED |
| TS-Tri-Hai-Tri.ttl | DILA_NOT_CONFIRMED |
| TS-Tri-Mon-Hoi-Han.ttl | DILA_UNRESOLVED |
| TS-Trieu-Chau-Dai-Dien.ttl | DILA_NOT_CONFIRMED |
| TS-Tru-Nham-Lieu-Van.ttl | DILA_UNRESOLVED, GENERATION_REVIEW |
| TS-Truc-Nguyen-Tong-Nguyen.ttl | DILA_NOT_CONFIRMED |
| TS-Truc-Vien-Phap-Hien.ttl | DILA_NOT_CONFIRMED |
| TS-Trung-Ap-Hong-An.ttl | DILA_NOT_CONFIRMED |
| TS-Trung-Dieu-Tri-Phong.ttl | IDENTIFIER_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Trung-Te-Thien-Nang.ttl | DILA_NOT_CONFIRMED |
| TS-Trung-Truc-Trung-Nhan.ttl | DILA_NOT_CONFIRMED |
| TS-Truong-Khanh-Dao-Hy.ttl | DILA_NOT_CONFIRMED |
| TS-Truong-Linh-Thu-Trac.ttl | DILA_NOT_CONFIRMED |
| TS-Truong-Thuy-Tu-Tuyen.ttl | DILA_NOT_CONFIRMED |
| TS-Truong-Vien.ttl | FILENAME_SUBJECT_DIFFERENT, DILA_UNRESOLVED, SUBJECT_COLLISION |
| TS-Truy-Chau-Thuy-Luc.ttl | DILA_NOT_CONFIRMED |
| TS-Tu-Bach-Chan-Kha.ttl | DILA_NOT_CONFIRMED |
| TS-Tu-Chau-Tri-San.ttl | IDENTIFIER_DIFFERENT, GENERATION_NOT_COMPARABLE |
| TS-Tu-Chau-Xu-Tich.ttl | IDENTIFIER_DIFFERENT, ENDPOINT_NO_MAIN_FILE |
| TS-Tu-Do-Trong-Tuyen.ttl | GENERATION_REVIEW |
| TS-Tu-Dong.ttl | DILA_UNRESOLVED |
| TS-Tu-Ho-Ly-Tong.ttl | DILA_UNRESOLVED |
| TS-Tu-Khong-Bon-Tinh.ttl | IDENTIFIER_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Tu-Ngoc-Dao-Thong.ttl | DILA_NOT_CONFIRMED |
| TS-Tu-Phuoc-Nhu-Bao.ttl | DILA_NOT_CONFIRMED |
| TS-Tu-To-Phap-Dien.ttl | DILA_NOT_CONFIRMED |
| TS-Tu-Van-Dao.ttl | DILA_UNRESOLVED |
| TS-Tu-Van-Hai-Tuan.ttl | DILA_UNRESOLVED |
| TS-Tue-An-Tue-Uyen.ttl | DILA_UNRESOLVED |
| TS-Tue-Lam-Duc-Ton.ttl | DILA_NOT_CONFIRMED |
| TS-Tue-Luc-Dong-Nguyen.ttl | DILA_UNRESOLVED |
| TS-Tue-Luc-Kha-Xuong.ttl | DILA_UNRESOLVED |
| TS-Tue-Nhat-Van-Nhan.ttl | FILENAME_SUBJECT_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Tue-Tinh-Ty-Tho.ttl | DILA_UNRESOLVED |
| TS-Tue-Vien.ttl | DILA_NOT_CONFIRMED |
| TS-Tung-Nhac-Hue-An.ttl | IDENTIFIER_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Tung-Nhac-Nguyen-Khue.ttl | IDENTIFIER_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Tung-Nhac-Pha-Tao-Doa.ttl | IDENTIFIER_DIFFERENT, DILA_UNRESOLVED |
| TS-Tung-Son-Lac-Kinh.ttl | DILA_UNRESOLVED |
| TS-Tung-Son-Pho-Tich.ttl | IDENTIFIER_DIFFERENT |
| TS-Tuong-Chau-Hue-Man.ttl | IDENTIFIER_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Tuong-Chau-Lich-Thon.ttl | DILA_NOT_CONFIRMED |
| TS-Tuong-Chau-Phap-Doan.ttl | DILA_NOT_CONFIRMED |
| TS-Tuong-Chau-Vuong-Kinh-So.ttl | DILA_NOT_CONFIRMED |
| TS-Tuong-Nhi-Vien-Giac.ttl | DILA_NOT_CONFIRMED |
| TS-Tuong-Son-Giac-Hai.ttl | DILA_NOT_CONFIRMED |
| TS-Tuong-Son-Thien-Truc.ttl | DILA_NOT_CONFIRMED |
| TS-Tuong-Thanh-Quang-Tung.ttl | DILA_UNRESOLVED |
| TS-Tuyen-Chau-Luc-Hoan.ttl | DILA_UNRESOLVED |
| TS-Tuyen-Minh-Phat-An.ttl | DILA_UNRESOLVED |
| TS-Tuyet-Dau-Phap-Nha.ttl | DILA_NOT_CONFIRMED |
| TS-Tuyet-Dau-Thuong-Thong.ttl | DILA_UNRESOLVED |
| TS-Tuyet-Dau-Tri.ttl | DILA_UNRESOLVED |
| TS-Tuyet-Giau-Chon-Phac.ttl | MULTIPLE_MAIN, FILENAME_SUBJECT_DIFFERENT, SUBJECT_COLLISION |
| TS-Tuyet-Phong-Uan-Van.ttl | DILA_UNRESOLVED |
| TS-Ty-Ni-Da-Luu-Chi.ttl | IDENTIFIER_DIFFERENT, DILA_UNRESOLVED, GENERATION_NOT_COMPARABLE, ENDPOINT_NO_MAIN_FILE |
| TS-U-Chau-Dam-Khong.ttl | DILA_NOT_CONFIRMED |
| TS-U-Chau-Hong-Loa.ttl | DILA_UNRESOLVED |
| TS-Van-Cai-Thu-Tri.ttl | DILA_NOT_CONFIRMED |
| TS-Van-Cai-Tri-Ban.ttl | DILA_NOT_CONFIRMED |
| TS-Van-Cu-Duc-Hoi.ttl | GENERATION_REVIEW |
| TS-Van-Cu-Duc-Thang.ttl | DILA_NOT_CONFIRMED |
| TS-Van-Cu-Nang.ttl | DILA_UNRESOLVED |
| TS-Van-Cu-Nguyen-Huu.ttl | DILA_UNRESOLVED |
| TS-Van-Cu-Phap-Nhu.ttl | DILA_NOT_CONFIRMED |
| TS-Van-Cu-Thien-Ngo.ttl | DILA_NOT_CONFIRMED |
| TS-Van-Cu-Tong-Chan.ttl | DILA_NOT_CONFIRMED |
| TS-Van-Cu-Tu-Vien.ttl | DILA_NOT_CONFIRMED |
| TS-Van-Mon-Hai-An.ttl | DILA_UNRESOLVED |
| TS-Van-Muc-Thien-Le.ttl | FILENAME_SUBJECT_DIFFERENT |
| TS-Van-Nham-Thien-Du.ttl | DILA_NOT_CONFIRMED |
| TS-Van-Nien-Dam-Bi.ttl | GENERATION_REVIEW |
| TS-Van-Nien-Dao-Nhan.ttl | DILA_NOT_CONFIRMED |
| TS-Van-Phong-Dao-Vien.ttl | DILA_NOT_CONFIRMED |
| TS-Van-Phong-Thoi-Uy.ttl | DILA_UNRESOLVED |
| TS-Van-Phong-Tue-Xuong.ttl | DILA_UNRESOLVED |
| TS-Van-Son.ttl | DILA_NOT_CONFIRMED |
| TS-Van-Tho-Phap-Thuyen.ttl | DILA_NOT_CONFIRMED |
| TS-Van-Tho-Tu-Ho.ttl | DILA_NOT_CONFIRMED |
| TS-Van-Tho-Ung-Thanh.ttl | GENERATION_NOT_COMPARABLE |
| TS-Van-Thu-Tuyen-Nang.ttl | DILA_NOT_CONFIRMED |
| TS-Ve-Quoc-Kinh-Trieu-Dao.ttl | DILA_UNRESOLVED |
| TS-Vien-Ngo-Khac-Can.ttl | DILA_NOT_CONFIRMED |
| TS-Vien-Van-Chuyet-Cong.ttl | DILA_UNRESOLVED |
| TS-Vinh-An-Dieu-Hy.ttl | GENERATION_NOT_COMPARABLE, DILA_NOT_CONFIRMED |
| TS-Vinh-Gia-Huyen-Giac.ttl | IDENTIFIER_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Vinh-Phuoc-Dien-Chieu.ttl | DILA_UNRESOLVED |
| TS-Vinh-Xuong-Giac-Thua.ttl | DILA_UNRESOLVED, GENERATION_REVIEW |
| TS-Vo-Dang-Phat-Phat-Nham-Huy.ttl | FILENAME_SUBJECT_DIFFERENT, DILA_NOT_CONFIRMED |
| TS-Vo-Huyen-Tinh-Xung.ttl | DILA_UNRESOLVED |
| TS-Vo-Minh-Te-Ngo.ttl | GENERATION_REVIEW, DILA_NOT_CONFIRMED |
| TS-Vo-Mon-Hue-Khai.ttl | ENDPOINT_NO_MAIN_FILE |
| TS-Vo-Ngon-Thong.ttl | DILA_UNRESOLVED, ENDPOINT_NO_MAIN_FILE |
| TS-Vo-Tan-Tue-Hai.ttl | DILA_UNRESOLVED, ENDPOINT_NO_MAIN_FILE |
| TS-Vo-Tuyen-Son-Chinh.ttl | DILA_NOT_CONFIRMED |
| TS-Vo-Vi-Tong-Thai.ttl | DILA_NOT_CONFIRMED |
| TS-Vu-Chau-Huyen-Sach.ttl | IDENTIFIER_DIFFERENT, DILA_NOT_CONFIRMED |
| TSN-Mat-Son-Lieu-Nhien.ttl | FILENAME_SUBJECT_DIFFERENT, DILA_NOT_CONFIRMED |
| TSN-Phap-Chau-Ke-Thi.ttl | FILENAME_SUBJECT_DIFFERENT, DILA_NOT_CONFIRMED |
| TSN-Tinh-Cu-Dieu-Dao.ttl | FILENAME_SUBJECT_DIFFERENT, DILA_NOT_CONFIRMED |
| TSN-Tu-Tho-Dieu-Tong.ttl | FILENAME_SUBJECT_DIFFERENT, DILA_NOT_CONFIRMED |

## Kiểm tra và trạng thái

Chín case chính hoàn tất đồng bộ phạm vi metadata/thầy đã xác minh. T215 toàn corpus vẫn in_progress. Quan hệ đệ tử chưa được chứng nhận toàn bộ. Pipeline: xem [pipeline.log](pipeline.log) và validation.json; không suy kết quả pipeline từ kiểm RDF/API.

Kết quả cuối: pipeline exit1 vì EPERM unlink test-results/.last-run.json. Retry runtime output riêng: 2/2 PASS; nút Mapping Tên Việt không có nên không kiểm được luồng click đó. DB/API9/9, HTTP Dashboard/báo cáo200. Bộ compliance báo2 metric fail nhưng script không chặn pipeline; không chứng nhận compliance toàn hệ thống. Memory37700 không kết nối được, đã lưu session local.
