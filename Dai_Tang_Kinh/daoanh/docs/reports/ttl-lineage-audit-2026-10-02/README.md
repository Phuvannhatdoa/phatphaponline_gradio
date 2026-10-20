# Kiểm tra toàn bộ TTL local — 2026-10-02

Đã đọc từng file; DB nguồn mở read-only. Chưa sửa TTL hoặc DB.

## Phạm vi và giới hạn

- 1037 file dữ liệu; bỏ qua 0-template.ttl.
- 1036 file nhận diện được subject; 1 file chưa nhận diện.
- 1238 khai báo quan hệ (chưa loại trùng).
- Không có rdflib: đây là audit sơ bộ theo cấu trúc, chưa chứng nhận RDF.
- DILA đối chiếu từ DB local với ánh xạ hiện có; chưa kiểm chứng web từng vị.
- Một cạnh thiếu trong DILA không chứng minh cạnh TTL sai.
- Số đời so sánh chỉ khi tên hệ truyền thừa khớp; chưa xác minh quy ước bắt đầu đếm.

## Thống kê

| Phát hiện | Số mục |
|---|---:|
| IDENTIFIER_DIFFERENT | 101 |
| FILENAME_SUBJECT_DIFFERENT | 89 |
| DILA_UNRESOLVED | 254 |
| MULTIPLE_MAIN | 3 |
| MAIN_UNSUPPORTED | 1 |
| SUBJECT_COLLISION | 10 |
| DILA_NOT_CONFIRMED | 437 |
| ENDPOINT_NO_MAIN_FILE | 26 |
| GENERATION_NOT_COMPARABLE | 17 |
| GENERATION_REVIEW | 30 |
| SELF_EDGE | 9 |
| DIRECTED_CYCLE | 12 |

9 self-edge nằm trong 12 cycle witnesses; 3 đường vòng còn lại có nhiều người. Không cộng các nhóm để suy ra số file lỗi.

## SELF_EDGE

- {"code":"SELF_EDGE","teacher":"dien_phuc_tue_thang","disciple":"dien_phuc_tue_thang","files":["TS-Dien-Phuc-Tue-Thang.ttl"]}
- {"code":"SELF_EDGE","teacher":"dong_son_pham_ngon","disciple":"dong_son_pham_ngon","files":["TS-Dong-Son-Trach-Ngon.ttl"]}
- {"code":"SELF_EDGE","teacher":"hoang_long_duc_phung","disciple":"hoang_long_duc_phung","files":["TS-Tien-Phuoc-Trach-Sung.ttl"]}
- {"code":"SELF_EDGE","teacher":"hung_hoa_nhan_nhac","disciple":"hung_hoa_nhan_nhac","files":["TS-Hung-Hoa-Nhan-Nhac.ttl"]}
- {"code":"SELF_EDGE","teacher":"phan_duong_thien_chieu","disciple":"phan_duong_thien_chieu","files":["TS-Phan-Duong-Thien-Chieu.ttl"]}
- {"code":"SELF_EDGE","teacher":"quang_tue_nguyen_lien","disciple":"quang_tue_nguyen_lien","files":["TS-Quang-Tue-Nguyen-Lien.ttl"]}
- {"code":"SELF_EDGE","teacher":"thuy_nham_tri_tai","disciple":"thuy_nham_tri_tai","files":["TS-Thuy-Nham-Tri-Tai.ttl"]}
- {"code":"SELF_EDGE","teacher":"tri_hai_dao_binh","disciple":"tri_hai_dao_binh","files":["TS-Tinh-Nhan-Ke-Thanh.ttl"]}
- {"code":"SELF_EDGE","teacher":"vo_chuan_su_pham","disciple":"vo_chuan_su_pham","files":["TS-Vo-Chuan-Su-Pham.ttl"]}

## DIRECTED_CYCLE

- {"code":"DIRECTED_CYCLE","path":["bach_van_khong_do","co_chuyet_nguyen_hau","vo_minh_te_ngo","nguyet_khe_dieu_trung","bach_van_khong_do"]}
- {"code":"DIRECTED_CYCLE","path":["bach_van_khong_do","co_chuyet_nguyen_hau","vo_minh_te_ngo","nguyet_khe_dieu_trung","di_phong_kinh_ninh","bach_van_khong_do"]}
- {"code":"DIRECTED_CYCLE","path":["dien_phuc_tue_thang","dien_phuc_tue_thang"]}
- {"code":"DIRECTED_CYCLE","path":["hung_hoa_nhan_nhac","hung_hoa_nhan_nhac"]}
- {"code":"DIRECTED_CYCLE","path":["thuy_nham_tri_tai","thuy_nham_tri_tai"]}
- {"code":"DIRECTED_CYCLE","path":["phan_duong_thien_chieu","phan_duong_thien_chieu"]}
- {"code":"DIRECTED_CYCLE","path":["bach_van_thu_doan","ngu_to_phap_dien","vien_ngo_khac_can","ho_khau_thieu_long","thien_dong_dam_hoa","mat_am_han_kiet","pha_am_to_tien","vo_chuan_su_pham","tuyet_nham_to_kham","cao_phong_nguyen_dieu","trung_phong_minh_bon","thien_nham_nguyen_truong","van_phong_thoi_uy","to_duc_bao_tang","phong_huyet_dien_chieu","thu_son_tinh_niem","phan_duong_thien_chieu","thach_suong_so_vien","duong_ky_phuong_hoi","bach_van_thu_doan"]}
- {"code":"DIRECTED_CYCLE","path":["hoang_long_duc_phung","hoang_long_duc_phung"]}
- {"code":"DIRECTED_CYCLE","path":["dong_son_pham_ngon","dong_son_pham_ngon"]}
- {"code":"DIRECTED_CYCLE","path":["tri_hai_dao_binh","tri_hai_dao_binh"]}
- {"code":"DIRECTED_CYCLE","path":["vo_chuan_su_pham","vo_chuan_su_pham"]}
- {"code":"DIRECTED_CYCLE","path":["quang_tue_nguyen_lien","quang_tue_nguyen_lien"]}

## GENERATION_REVIEW

- {"code":"GENERATION_REVIEW","teacher":"co_chuyet_nguyen_hau","disciple":"vo_minh_te_ngo","teacher_gen":58,"disciple_gen":58,"lineage":"Dòng Lâm Tế Dương Kỳ","files":["TS-Co-Chuyet-Nguyen-Hau.ttl","TS-Vo-Minh-Te-Ngo.ttl"]}
- {"code":"GENERATION_REVIEW","teacher":"coc_an_uan_thong","disciple":"kim_son_vien_thong","teacher_gen":43,"disciple_gen":45,"lineage":"Tông Lâm Tế Trung Hoa","files":["TS-Kim-Son-Vien-Thong.ttl"]}
- {"code":"GENERATION_REVIEW","teacher":"dien_phuc_tue_thang","disciple":"dien_phuc_tue_thang","teacher_gen":50,"disciple_gen":50,"lineage":"Dòng Lâm Tế Dương Kỳ","files":["TS-Dien-Phuc-Tue-Thang.ttl"]}
- {"code":"GENERATION_REVIEW","teacher":"giap_son_hieu_thuan","disciple":"kham_son_pho_so","teacher_gen":47,"disciple_gen":47,"lineage":"Dòng Lâm Tế Hoàng Long","files":["TS-Giap-Son-Hieu-Thuan.ttl","TS-Kham-Son-Pho-So.ttl"]}
- {"code":"GENERATION_REVIEW","teacher":"ha_son_thu_tuan","disciple":"phan_luong_quy","teacher_gen":49,"disciple_gen":49,"lineage":"Dòng Lâm Tế Dương Kỳ","files":["Cs-Phan-Luong-Quy.ttl"]}
- {"code":"GENERATION_REVIEW","teacher":"ha_son_thu_tuan","disciple":"tru_nham_lieu_van","teacher_gen":49,"disciple_gen":49,"lineage":"Dòng Lâm Tế Dương Kỳ","files":["TS-Ha-Son-Thu-Tuan.ttl","TS-Tru-Nham-Lieu-Van.ttl"]}
- {"code":"GENERATION_REVIEW","teacher":"kien_long_chieu_khanh","disciple":"ngoc_tuyen_thien_sieu","teacher_gen":46,"disciple_gen":46,"lineage":"Dòng Lâm Tế Hoàng Long","files":["TS-Ngoc-Tuyen-Thien-Sieu.ttl"]}
- {"code":"GENERATION_REVIEW","teacher":"mat_am_han_kiet","disciple":"linh_an_sung_nhac","teacher_gen":51,"disciple_gen":51,"lineage":"Dòng Lâm Tế Dương Kỳ","files":["TS-Linh-An-Sung-Nhac.ttl"]}
- {"code":"GENERATION_REVIEW","teacher":"mat_am_han_kiet","disciple":"tien_phuc_dao_sinh","teacher_gen":51,"disciple_gen":51,"lineage":"Dòng Lâm Tế Dương Kỳ","files":["TS-Tien-Phuc-Dao-Sinh.ttl"]}
- {"code":"GENERATION_REVIEW","teacher":"nguu_dau_phap_dung","disciple":"chung_son_dam_thoi","teacher_gen":32,"disciple_gen":2,"lineage":"Ngưu Đầu Tông Trung Hoa","files":["TS-Chung-Son-Dam-Thoi.ttl","TS-Nguu-Dau-Phap-Dung.ttl"]}
- {"code":"GENERATION_REVIEW","teacher":"nguu_dau_phap_dung","disciple":"nguu_dau_tri_nham","teacher_gen":32,"disciple_gen":2,"lineage":"Ngưu Đầu Tông Trung Hoa","files":["TS-Nguu-Dau-Tri-Nham.ttl"]}
- {"code":"GENERATION_REVIEW","teacher":"phan_duong_thien_chieu","disciple":"phan_duong_thien_chieu","teacher_gen":43,"disciple_gen":43,"lineage":"Tông Lâm Tế Trung Hoa","files":["TS-Phan-Duong-Thien-Chieu.ttl"]}
- {"code":"GENERATION_REVIEW","teacher":"phu_son_phap_vien","disciple":"hanh_nhac_phung_nang","teacher_gen":44,"disciple_gen":46,"lineage":"Tông Lâm Tế Trung Hoa","files":["TS-Hanh-Nhac-Phung-Nang.ttl","TS-Phu-Son-Phap-Vien.ttl"]}
- {"code":"GENERATION_REVIEW","teacher":"phu_son_phap_vien","disciple":"hoa_nghiem_pho_tu","teacher_gen":44,"disciple_gen":46,"lineage":"Tông Lâm Tế Trung Hoa","files":["TS-Hoa-Nghiem-Pho-Tu.ttl"]}
- {"code":"GENERATION_REVIEW","teacher":"phu_son_phap_vien","disciple":"hung_hoa_thieu_thanh","teacher_gen":44,"disciple_gen":46,"lineage":"Tông Lâm Tế Trung Hoa","files":["TS-Hung-Hoa-Thieu-Thanh.ttl"]}
- {"code":"GENERATION_REVIEW","teacher":"phu_son_phap_vien","disciple":"thu_son_xu_khe","teacher_gen":44,"disciple_gen":46,"lineage":"Tông Lâm Tế Trung Hoa","files":["TS-Thu-Son-Xu-Khe.ttl"]}
- {"code":"GENERATION_REVIEW","teacher":"quang_nam_dao_thuong","disciple":"chuong_chau_la_han","teacher_gen":37,"disciple_gen":37,"lineage":"Thiền Tông Trung Hoa - Nam Tông","files":["TS-Chuong-Chau-La-Han.ttl"]}
- {"code":"GENERATION_REVIEW","teacher":"quang_nam_dao_thuong","disciple":"quang_nam_dao_ngo","teacher_gen":37,"disciple_gen":37,"lineage":"Thiền Tông Trung Hoa - Nam Tông","files":["TS-Quang-Nam-Dao-Ngo.ttl","TS-Quang-Nam-Dao-Thuong.ttl"]}
- {"code":"GENERATION_REVIEW","teacher":"quang_tue_nguyen_lien","disciple":"quang_tue_nguyen_lien","teacher_gen":43,"disciple_gen":43,"lineage":"Tông Lâm Tế Trung Hoa","files":["TS-Quang-Tue-Nguyen-Lien.ttl"]}
- {"code":"GENERATION_REVIEW","teacher":"song_phong_tinh_hoi","disciple":"linh_son_ngan_van","teacher_gen":46,"disciple_gen":46,"lineage":"Tông Lâm Tế Trung Hoa","files":["TS-Linh-Son-Ngan-Van.ttl"]}
- {"code":"GENERATION_REVIEW","teacher":"song_phong_tinh_hoi","disciple":"quang_quoc_van_tan","teacher_gen":46,"disciple_gen":46,"lineage":"Tông Lâm Tế Trung Hoa","files":["TS-Quang-Quoc-Van-Tang.ttl","TS-Song-Phong-Tinh-Hoi.ttl"]}
- {"code":"GENERATION_REVIEW","teacher":"thach_dau_tu_hoi","disciple":"van_cu_duc_hoi","teacher_gen":49,"disciple_gen":49,"lineage":"Dòng Lâm Tế Dương Kỳ","files":["TS-Thach-Dau-Tu-Hoi.ttl","TS-Van-Cu-Duc-Hoi.ttl"]}
- {"code":"GENERATION_REVIEW","teacher":"thach_suong_khanh_chu","disciple":"loc_thanh","teacher_gen":38,"disciple_gen":38,"lineage":"Thiền Tông Trung Hoa - Nam Tông","files":["TS-Thach-Suong-Khanh-Chu.ttl"]}
- {"code":"GENERATION_REVIEW","teacher":"thach_suong_so_vien","disciple":"song_phong_tinh_hoi","teacher_gen":44,"disciple_gen":46,"lineage":"Tông Lâm Tế Trung Hoa","files":["TS-Song-Phong-Tinh-Hoi.ttl"]}
- {"code":"GENERATION_REVIEW","teacher":"thuy_nham_kha_chan","disciple":"hung_duong_hien","teacher_gen":45,"disciple_gen":47,"lineage":"Tông Lâm Tế Trung Hoa","files":["TS-Hung-Duong-Hien.ttl"]}
- {"code":"GENERATION_REVIEW","teacher":"thuy_nham_tri_tai","disciple":"thuy_nham_tri_tai","teacher_gen":44,"disciple_gen":44,"lineage":"Tông Lâm Tế Trung Hoa","files":["TS-Thuy-Nham-Tri-Tai.ttl"]}
- {"code":"GENERATION_REVIEW","teacher":"van_cu_nguyen_huu","disciple":"tu_do_trong_tuyen","teacher_gen":46,"disciple_gen":48,"lineage":"Dòng Lâm Tế Hoàng Long","files":["TS-Tu-Do-Trong-Tuyen.ttl"]}
- {"code":"GENERATION_REVIEW","teacher":"van_nien_dam_bi","disciple":"long_hoa_ban","teacher_gen":51,"disciple_gen":51,"lineage":"Dòng Lâm Tế Hoàng Long","files":["TS-Van-Nien-Dam-Bi.ttl"]}
- {"code":"GENERATION_REVIEW","teacher":"vinh_xuong_giac_thua","disciple":"phuong_lai_xuong_vien","teacher_gen":82,"disciple_gen":82,"lineage":"Dòng Lâm Tế Dương Kỳ","files":["TS-Phuong-Lai-Xuong-Vien.ttl","TS-Vinh-Xuong-Giac-Thua.ttl"]}
- {"code":"GENERATION_REVIEW","teacher":"vo_chuan_su_pham","disciple":"vo_chuan_su_pham","teacher_gen":53,"disciple_gen":53,"lineage":"Dòng Lâm Tế Dương Kỳ","files":["TS-Vo-Chuan-Su-Pham.ttl"]}

## SUBJECT_COLLISION

- {"code":"SUBJECT_COLLISION","subject":"bach_truong_hoai_hai","count":2,"files":"TS-Bach-Truong-Hoai-Hai.ttl,TS-Phuoc-Chau-Dai-An.ttl"}
- {"code":"SUBJECT_COLLISION","subject":"bach_van_khong_do","count":3,"files":"TS-Bach-Van-Khong-Do.ttl,TS-Di-Phong-Kinh-Ninh.ttl,TS-Dot-Khong-Tri-Ban.ttl"}
- {"code":"SUBJECT_COLLISION","subject":"dao_ninh_dao_khoan","count":2,"files":"TS-Dai-Ninh-Dao-Khoan.ttl,TS-Dao-Ninh-Dao-Khoan.ttl"}
- {"code":"SUBJECT_COLLISION","subject":"dong_son_pham_ngon","count":2,"files":"TS-Dong-Son-Pham-Ngon.ttl,TS-Dong-Son-Trach-Ngon.ttl"}
- {"code":"SUBJECT_COLLISION","subject":"hoang_long_duc_phung","count":2,"files":"TS-Hoang-Long-Duc-Phung.ttl,TS-Tien-Phuoc-Trach-Sung.ttl"}
- {"code":"SUBJECT_COLLISION","subject":"hung_hoa_nhan_nhac","count":2,"files":"TS-Dinh-Lam-Canh-Phuong.ttl,TS-Hung-Hoa-Nhan-Nhac.ttl"}
- {"code":"SUBJECT_COLLISION","subject":"phat_y_linh_nhac","count":2,"files":"TS-Phat-Y-Linh-Nhac.ttl,TS-Truong-Vien.ttl"}
- {"code":"SUBJECT_COLLISION","subject":"phong_huyet_dien_chieu","count":4,"files":"TS-Dai-Xa-Nhu-Truong.ttl,TS-Minh-Hoang-Tu-Dung.ttl,TS-Phong-Huyet-Dien-Chieu.ttl,TS-Tuyet-Giau-Chon-Phac.ttl"}
- {"code":"SUBJECT_COLLISION","subject":"thach_cuu","count":2,"files":"TS-Linh-Cuu.ttl,TS-Thach-Cuu.ttl"}
- {"code":"SUBJECT_COLLISION","subject":"tri_hai_dao_binh","count":2,"files":"TS-Tinh-Nhan-Ke-Thanh.ttl,TS-Tri-Hai-Dao-Binh.ttl"}

## MAIN_UNSUPPORTED

- {"code":"MAIN_UNSUPPORTED","file":"TS-Phuc-Chau-Dai-An.ttl"}

## Tiếp theo

1. Kiểm tra RDF trong môi trường có rdflib, xử lý file chưa nhận diện.
2. Xác minh định danh các file va chạm trước khi xác minh cạnh.
3. Đối chiếu DILA chính thức và nguồn Việt cho từng cạnh/đời có cờ.
4. Tạo change-set có bằng chứng, backup và rollback trước khi đồng bộ riêng dữ liệu TTL.
5. Kiểm tra DB/API và audit lại sau mỗi lô.

Chi tiết toàn bộ: findings.jsonl. Index file, hash SHA256, đời, tông, cạnh: index.sqlite.

## Validation

Audit hoàn tất (exit 0 nghĩa là quét xong, không nghĩa là dữ liệu sạch). Pipeline exit 1 do Python thiếu flask ở T178 (67/68 PASS). RDF chưa được validate vì thiếu rdflib. Preflight nhãn cũ: 12 L1, 15 L2, 9 L7; xem existing-preflight.json.
