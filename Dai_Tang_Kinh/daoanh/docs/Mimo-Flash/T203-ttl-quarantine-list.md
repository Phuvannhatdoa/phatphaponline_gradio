---
id: T203
title: "File TTL có rdfs:label sai — 32 file cần move ra khỏi data/ttl, 11 file giữ lại"
module: Data / TTL Source
priority: high
status: pending_admin_apply
owner: claudecode
depends_on: [T200]
created: 2026-10-01
updated: 2026-09-30
---

# T203 — File TTL sai nhãn: 32 file cần move

> **TTL_DIR**: `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl`
> **Quarantine dir**: `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl_quarantine`
>
> **Cách xác định nhãn đúng (không suy đoán):** nhãn chuẩn của mỗi người tồn tại
> trong chính corpus dưới dạng triple
> `<ex:monk/SLUG> rdfs:label "TÊN ĐÚNG"@vi` ⇒ lấy từ nguồn, đếm số nguồn làm căn cứ.

## 1. Quy tắc phân loại

| TIER | Nguyên tắc | Số file | Hành động |
|------|-----------|---------|-----------|
| **TIER-1** | `rdfs:label` trùng tên **một người KHÁC** mà file khai báo (thầy/trò) ⇒ nhãn bị đảo sang người khác | **17** | **MOVE** |
| **TIER-2** | `rdfs:label` **không liên quan** tới nhãn chuẩn (khác hoàn toàn) | **15** | **MOVE** |
| **TIER-3** | chỉ khác **danh xưng / tiền tố / viết tắt** (vd `Cư Sĩ …`, `Am Chủ …`) ⇒ hợp lệ | 11 | **GIỮ** |

## 2. TIER-1 — SAI ĐẢO nhãn (17 file)

| # | File | Đường dẫn hiện tại | Nhãn SAI hiện tại | Nhãn ĐÚNG | Căn cứ |
|---|------|------------------|-------------------|----------|--------|
| 1 | `TS-An-Hoa-Van-Nhat.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\TS-An-Hoa-Van-Nhat.ttl` | Long Khánh Khánh Nhàn | **An Hóa Văn Nhất** | 5 nguồn |
| 2 | `TS-Co-Son-To-Tran.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\TS-Co-Son-To-Tran.ttl` | Thượng Phong Bản Tài | **Cổ Sơn Tổ Trân** | 1 nguồn |
| 3 | `TS-Coc-Son-Hai.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\TS-Coc-Son-Hai.ttl` | Thái Bình Huệ Cần Phật Giám | **Cốc Sơn Hải** | 1 nguồn |
| 4 | `TS-Dam-Chau-Bao-Cai-Uoc.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\TS-Dam-Chau-Bao-Cai-Uoc.ttl` | Nam Nhạc Huyền Thái | **Đàm Châu Bảo Cái Ước** | 5 nguồn |
| 5 | `TS-Dam-Chau-Van-Cai-Canh.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\TS-Dam-Chau-Van-Cai-Canh.ttl` | Đàm Châu Trung Vân Cái | **Đàm Châu Vân Cái Cảnh** | 2 nguồn |
| 6 | `TS-Di-Phong-Kinh-Ninh.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\TS-Di-Phong-Kinh-Ninh.ttl` | Nguyệt Khê Diệu Trừng | **Di Phong Kính Ninh** | 2 nguồn |
| 7 | `TS-Hoa-Tang-Tong-Dien.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\TS-Hoa-Tang-Tong-Dien.ttl` | Đại Huệ Tông Cảo | **Hoa Tạng Tông Diễn** | 1 nguồn |
| 8 | `TS-Khanh-Thien-Thu-Long.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\TS-Khanh-Thien-Thu-Long.ttl` | Thiện Khánh Thủ Long | **Khánh Thiện Thủ Long** | 1 nguồn |
| 9 | `TS-Long-Hoa-Te-Nhac.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\TS-Long-Hoa-Te-Nhac.ttl` | Kim Sơn Ðàm Dĩnh | **Long Hoa Tề Nhạc** | 2 nguồn |
| 10 | `TS-Minh-Hai-Phap-Bao.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\TS-Minh-Hai-Phap-Bao.ttl` | Nguyên Thiều Siêu Bạch | **Minh Hải Pháp Bảo** | 1 nguồn |
| 11 | `TS-Nam-Nhac-Minh-Toan.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\TS-Nam-Nhac-Minh-Toan.ttl` | Đạo Tuyên | **Nam Nhạc Minh Toản** | 3 nguồn |
| 12 | `TS-Nguyet-Chuong-Tri-Uyen.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\TS-Nguyet-Chuong-Tri-Uyen.ttl` | Bảo Ninh Nhân Dũng | **Nguyệt Chưởng Trí Uyên** | 1 nguồn |
| 13 | `TS-Tay-Kinh-Nghia-Phuoc.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\TS-Tay-Kinh-Nghia-Phuoc.ttl` | Tung Sơn Phổ Tịch | **Tây Kinh Nghĩa Phước** | 7 nguồn |
| 14 | `TS-Thai-Tu-Dong-Quang.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\TS-Thai-Tu-Dong-Quang.ttl` | Thái Tử Ðạo Nhất | **Thái Tử Đồng Quảng** | 3 nguồn |
| 15 | `TS-The-Nham-Ton-Tho.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\TS-The-Nham-Ton-Tho.ttl` | Nam Nhạc Huyền Thái | **Thê Nham Tồn Thọ** | 3 nguồn |
| 16 | `TS-Tinh-Nhan-Ke-Thanh.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\TS-Tinh-Nhan-Ke-Thanh.ttl` | Trí Hải Ðạo Bình | **Tịnh Nhân Kế Thành** | 6 nguồn |
| 17 | `TS-Tue-Nhat-Minh.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\TS-Tue-Nhat-Minh.ttl` | Hoàng Bá Vĩnh Thái | **Tuệ Nhật Minh** | 1 nguồn |

## 3. TIER-2 — SAI KHÁC (15 file)

| # | File | Đường dẫn hiện tại | Nhãn SAI hiện tại | Nhãn ĐÚNG | Căn cứ |
|---|------|------------------|-------------------|----------|--------|
| 1 | `TS-Bao-An-Thanh.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\TS-Bao-An-Thanh.ttl` | Báo Ân Thành | **Thanh Nguyên Như** | 1 nguồn |
| 2 | `TS-Bao-Phuoc-Ban-Quyen.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\TS-Bao-Phuoc-Ban-Quyen.ttl` | Bảo Phước Bản Quyền | **Tuệ An Tuệ Uyên** | 17 nguồn |
| 3 | `TS-Bien-Dam-Hieu-Lieu.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\TS-Bien-Dam-Hieu-Lieu.ttl` | Tây Vực Quật Đa Tam Tạng | **Biển Đam Hiểu Liễu** | 1 nguồn |
| 4 | `TS-Chieu-Hien-Hoi-Thong.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\TS-Chieu-Hien-Hoi-Thong.ttl` | Chùa Linh Ẩn | **Chiêu Hiền Hội Thông** | 1 nguồn |
| 5 | `TS-Cuu-Danh-To.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\TS-Cuu-Danh-To.ttl` | Long Hoa Ðạo Sơ | **Cửu Đảnh Tố** | 1 nguồn |
| 6 | `TS-Dam-Chau-Dai-Xuyen.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\TS-Dam-Chau-Dai-Xuyen.ttl` | Phụng Tường Phật Đà | **Đàm Châu Đại Xuyên** | 1 nguồn |
| 7 | `TS-Dang-Van-Sieu-Cap.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\TS-Dang-Van-Sieu-Cap.ttl` | Am Chủ Tích Thúy Vĩnh | **Đăng Vân Siêu Cập** | 1 nguồn |
| 8 | `TS-Dong-Son-Te-Vi.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\TS-Dong-Son-Te-Vi.ttl` | Giác A | **Đông Sơn Tề Vĩ** | 1 nguồn |
| 9 | `TS-Kinh-Trieu-Thi-Loi.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\TS-Kinh-Trieu-Thi-Loi.ttl` | Đàm Châu Hoa Lâm | **Kinh Triệu Thi Lợi** | 1 nguồn |
| 10 | `TS-Phung-Tuong-Thach-Tru.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\TS-Phung-Tuong-Thach-Tru.ttl` | Vân Môn Hải Yến | **Phụng Tường Thạch Trụ** | 3 nguồn |
| 11 | `TS-Thach-Cung-Hue-Tang.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\TS-Thach-Cung-Hue-Tang.ttl` | Ngũ Đài Ẩn Phong | **Thạch Củng Huệ Tạng** | 1 nguồn |
| 12 | `TS-Thien-Dong-Pho-Giao.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\TS-Thien-Dong-Pho-Giao.ttl` | Long Nha Tông Mật | **Thiên Đồng Phổ Giao** | 6 nguồn |
| 13 | `TS-Tho-Thanh-So-Van.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\TS-Tho-Thanh-So-Van.ttl` | Nguyệt Chưởng Trí Uyên | **Thọ Thánh Sở Văn** | 1 nguồn |
| 14 | `TS-Tien-Phuoc-Trach-Sung.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\TS-Tien-Phuoc-Trach-Sung.ttl` | Hoàng Long Ðức Phùng | **Tiến Phước Trạch Sùng** | 7 nguồn |
| 15 | `TS-Tri-Chau-Lo-To-Giao.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\TS-Tri-Chau-Lo-To-Giao.ttl` | Trì Châu Lỗ Tổ Giáo | **Am Chủ Phúc Bồn** | 1 nguồn |

## 4. TIER-3 — GIỮ LẠI, KHÔNG move (11 file)

| File | Đường dẫn hiện tại | Nhãn trong file | Nhãn chuẩn | Vì sao giữ |
|------|------------------|----------------|-----------|-----------|
| `Bo-Tat-Long-Tho.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\Bo-Tat-Long-Tho.ttl` | Bồ Tát Long Thọ | Long Thọ | danh xưng / tiền tố hợp lệ |
| `Bo-Tat-Ma-Minh.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\Bo-Tat-Ma-Minh.ttl` | Bồ Tát Mã Minh | Mã Minh | danh xưng / tiền tố hợp lệ |
| `Cs-Anh-Cong-Ha-Tung.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\Cs-Anh-Cong-Ha-Tung.ttl` | Anh Công Hạ Tủng | Cư Sĩ Anh Công Hạ Tủng | danh xưng / tiền tố hợp lệ |
| `Cs-Ly-Doan-Nguyen.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\Cs-Ly-Doan-Nguyen.ttl` | Lý Ðoan Nguyện | Cư Sĩ Tiết Sứ Lý Ðoan Nguyện | danh xưng / tiền tố hợp lệ |
| `Cs-Ly-Tuan-Uc.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\Cs-Ly-Tuan-Uc.ttl` | Lý Tuân Úc | Cư Sĩ Phù Mã Lý Tuân Úc | danh xưng / tiền tố hợp lệ |
| `Cs-Ngo-Tuan.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\Cs-Ngo-Tuan.ttl` | Ngô Tuân | Cư Sĩ Bí Thư Ngô Tuân | danh xưng / tiền tố hợp lệ |
| `TS-Hoang-Long-Tri-Minh.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\TS-Hoang-Long-Tri-Minh.ttl` | Cư Sĩ Thái Sử Hoàng Ðình Kiên | Hoàng Long Trí Minh | danh xưng / tiền tố hợp lệ |
| `TS-Kien-Chau-Xu-Triet.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\TS-Kien-Chau-Xu-Triet.ttl` | Kiền Châu Xứ Triệt | Kiền Châu Xứ Vy | gần giống — có thể là pháp danh |
| `TS-Lao-Na-Tu-Dang-Dai-Hoang.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\TS-Lao-Na-Tu-Dang-Dai-Hoang.ttl` | Đại Hồng Tổ Chứng | Lão Na Từ Đăng Đại Hoằng | danh xưng / tiền tố hợp lệ |
| `TS-Loc-Mon-Tue-Chieu.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\TS-Loc-Mon-Tue-Chieu.ttl` | Lộc Môn Tuệ Chiêu | Sơn Chủ Lộc Môn Tuệ Chiêu | danh xưng / tiền tố hợp lệ |
| `TS-Van-Mon-Hai-An.ttl` | `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl\TS-Van-Mon-Hai-An.ttl` | Vân Môn Hải Yến | Vân Môn Hải Án | gần giống — có thể là pháp danh |

## 5. Lệnh thực hiện

```powershell
# xem trước
python -X utf8 scripts/t203_quarantine_ttl.py --stats
python -X utf8 scripts/t203_quarantine_ttl.py --dry-run

# move 32 file sang E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\ttl_quarantine
python -X utf8 scripts/t203_quarantine_ttl.py --apply

# hoàn tác
python -X utf8 scripts/t203_quarantine_ttl.py --revert
```

## 6. Kiểm chứng phần còn lại

| Kiểm tra | Kết quả |
|----------|---------|
| Triple nhãn chuẩn của file bị move còn ở file giữ lại? | **0 mất** ✅ |
| File còn lại có nhãn lệch tên sau khi bỏ tiền tố hợp lệ? | 44 (toàn là biến thể `Am Chủ …`/`Cư Sĩ …`) — không phải lỗi |
| File còn lại rdflib parse được? | **9 file KHÔNG** ⚠ (xem §7) |
| File bị move còn bị file khác tham chiếu? | 32/32 (vai thầy/trò) — triple quan hệ **vẫn còn**, chỉ mất file riêng |

## 7. ⚠ Vấn đề CÒN LẠI (không do 32 file này, cần task riêng)

1. **9 file TTL rdflib KHÔNG parse được** ⇒ `etl_ttl_person_authority.py` **bỏ qua im lặng** (try/except) ⇒ các vị đó không bao giờ vào DB:
   - `TS-Ban-Son-Bao-Tich.ttl`
   - `TS-Dai-Hue-Tong-Cao.ttl`
   - `TS-Dai-Xa-Nhu-Truong.ttl`
   - `TS-Minh-Hoang-Tu-Dung.ttl`
   - `TS-Thanh-Dang-Minh-Luong.ttl`
   - `TS-Tin-Tuong-Tong-Hien.ttl`
   - `TS-Tuyet-Giau-Chon-Phac.ttl`
   - `TS-Van-Cai-Thu-Tri.ttl`
   - `TS-Van-Thu-Tuyen-Nang.ttl`
   (`0-template.ttl` cũng fail nhưng đó là template, không tính)

2. **302 file TTL chứa ký tự `Ð` (U+00D0) thay cho `Đ` (U+0110)** — 590 ký tự. Làm nhiễu mọi so khớp tên. **Không** sửa tự động (cần rà từng file).

3. **16/33 nhóm `dila_id` trùng là 2 người THẬT bị gán chung `dila_id`** — lỗi `match_person()` (thử 2 `tail-N` quá lỏng) trong `etl_ttl_full_import.py`. **Sửa/move TTL không giải quyết được** nhóm này.

## 8. ⚠ Hệ quả khi move

- `scripts/etl_ttl_person_authority.py` **xoá hết** `vn_person_authority` rồi nạp lại từ `TTL_DIR` ⇒ 32 vị trong danh sách sẽ **mất khỏi DB** ở lần ETL kế.
- `scripts/etl_ttl_full_import.py` chỉ `INSERT OR IGNORE` + skip nếu `ttl_filename` đã có ⇒ **không** tự xoá dòng cũ ⇒ cần quyết định có xoá dòng DB tương ứng hay không.
- TTL **không được git track** (`.gitignore` có `data/`) ⇒ **không có `git revert`**; script ghi `manifest.json` trong thư mục quarantine để `--revert`.

