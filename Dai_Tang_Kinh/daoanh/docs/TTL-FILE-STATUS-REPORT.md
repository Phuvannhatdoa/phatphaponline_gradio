# Báo cáo trạng thái FILE TTL

> Sinh tự động bằng `scripts/t210_ttl_file_report.py` — **đừng sửa tay**,
> hãy chạy lại script để cập nhật.
>
> **Cập nhật:** 2026-10-02 21:07 · **Corpus:** 1038 file

## Tóm tắt

| Nhóm | Số file | Mức độ | Cần Admin làm |
|---|---|---|---|
| A. File đã **mất** (DB còn tham chiếu) | 10 | 🔴 Cao | **Cấp lại bản gốc** |
| B. File **rỗng** / không parse được | 0 | 🔴 Cao | Khôi phục backup |
| C. File **URI sai** (ghi đè lẫn nhau) | 8 | 🟠 Trung bình | Duyệt sửa URI |
| D. File **nhãn sai** | 24 | 🟠 Trung bình | Sửa nhãn |
| E. File **đã sửa** xong (T205/T206) | 10 | ✅ Đã xong | — |

**Preflight hiện tại:** BLOCKING = 29 (L1 11 · L2 13 · L3 0 · L6 0 · L7 5) · WARNING = 24 (L4 0 · L5 24)

---

## A. 🔴 File đã MẤT — DB còn tham chiếu, không còn trên đĩa

| # | Tên file (thiếu `.ttl`) | Số row DB còn trỏ tới |
|---|---|---|
| 1 | `TS-Chuong-Hiep-Chanh-Tri.ttl` | 1 |
| 2 | `TS-Duong-Ki-Phuong-Hoi.ttl` | 1 |
| 3 | `TS-Phap-Kiem-Minh-Giac.ttl` | 1 |
| 4 | `TS-Phap-Mon-Phat-Da.ttl` | 1 |
| 5 | `TS-Thiet-Bao-Cam-Ung.ttl` | 1 |
| 6 | `TS-Thiet-Dam-Chanh-Luan.ttl` | 3 |
| 7 | `TS-Thiet-Dang-Bao-Quang.ttl` | 1 |
| 8 | `TS-Thiet-Dinh-An-Triem.ttl` | 1 |
| 9 | `TS-Thiet-The-Triem-An.ttl` | 1 |
| 10 | `TS-Toan-Y-Pho-Hue.ttl` | 1 |

> **Không có backup** cho các file này (T205/T206 chỉ backup file đã sửa).
> Cần bản gốc từ Admin.

---

## B. 🔴 File RỖNG hoặc không parse được

_Không có — toàn bộ 1038 file đều parse được._

> **Đã xử lý 1 vụ:** `TS-Dai-Xa-Nhu-Truong.ttl` bị xoá rỗng (0 byte) ngày
> 2026-10-02, đã khôi phục từ backup `data/backups/t205_ttl_20261001_203559/`.

---

## C. 🟠 File có URI sai — nhiều file dùng chung 1 subject

Nguyên nhân: lỗi copy-paste khi sinh TTL — **URI giữ từ người trước**,
còn **nhãn thì đúng**. Hậu quả: các file ghi đè lẫn nhau, ETL chỉ nạp
file cuối, **các file kia mất im lặng**.

| File | URI đang khai báo | URI đúng (theo tên file) | Nhãn trong file |
|---|---|---|---|
| `TS-Dai-Ninh-Dao-Khoan.ttl` | `dao_ninh_dao_khoan` | `dai_ninh_dao_khoan` | Đại Ninh Đạo Khoan ⚠️ |
| `TS-Dai-Xa-Nhu-Truong.ttl` | `phong_huyet_dien_chieu` | `dai_xa_nhu_truong` | Nam Viện Huệ Ngung ⚠️ |
| `TS-Di-Phong-Kinh-Ninh.ttl` | `bach_van_khong_do` | `di_phong_kinh_ninh` | Nguyệt Khê Diệu Trừng ⚠️ |
| `TS-Dot-Khong-Tri-Ban.ttl` | `bach_van_khong_do` | `dot_khong_tri_ban` | Đột Không Trí Bản ⚠️ |
| `TS-Linh-Cuu.ttl` | `thach_cuu` | `linh_cuu` | Thạch Cữu ⚠️ |
| `TS-Minh-Hoang-Tu-Dung.ttl` | `phong_huyet_dien_chieu` | `minh_hoang_tu_dung` | Nam Viện Huệ Ngung ⚠️ |
| `TS-Phuoc-Chau-Dai-An.ttl` | `bach_truong_hoai_hai` | `phuoc_chau_dai_an` | Bách_Trượng_Hoài_Hải ⚠️ |
| `TS-Tuyet-Giau-Chon-Phac.ttl` | `phong_huyet_dien_chieu` | `tuyet_giau_chon_phac` | Nam Viện Huệ Ngung ⚠️ |

> ⚠️ = cả **nhãn** cũng không khớp tên file ⇒ cần Admin xác nhận,
> không sửa cơ học được.

### Nhóm đặc biệt: 3 file cùng subject `phong_huyet_dien_chieu`

| File | generationOrder | hasTeacher | Nhãn |
|---|---|---|---|
| `TS-Tuyet-Giau-Chon-Phac.ttl` | 60, 69 | to_duc_bao_tang, dao_man_moc_tran | Nam Viện Huệ Ngung |
| `TS-Dai-Xa-Nhu-Truong.ttl` | 60, 70 | tuyet_dau_chon_phac, to_duc_bao_tang | Nam Viện Huệ Ngung |
| `TS-Minh-Hoang-Tu-Dung.ttl` | 60, 71 | dai_xa_nhu_truong, to_duc_bao_tang | Nam Viện Huệ Ngung |
| `TS-Phong-Huyet-Dien-Chieu.ttl` | 41 | nam_vien_hue_ngung | Phong Huyệt Diên Chiểu |

> 3 file này là **3 đời liên tiếp** (thầy → trò) nhưng dùng chung 1 URI.
> DB hiện chỉ có **1 row** (`phong_huyet_dien_chieu`). Cần Admin xác nhận:
> **3 người** (tách URI theo tên file) hay **1 người** (3 file trùng lặp)?

---

## D. 🟠 File có NHÃN sai

| # | File | Mã |
|---|---|---|
| 1 | `TS-An-Hoa-Van-Nhat.ttl` | L1 |
| 2 | `TS-Bao-An-Thanh.ttl` | L2 |
| 3 | `TS-Bao-Phuoc-Ban-Quyen.ttl` | L2 |
| 4 | `TS-Bien-Dam-Hieu-Lieu.ttl` | L2 |
| 5 | `TS-Chieu-Hien-Hoi-Thong.ttl` | L2 |
| 6 | `TS-Cuu-Danh-To.ttl` | L2 |
| 7 | `TS-Dam-Chau-Bao-Cai-Uoc.ttl` | L1 |
| 8 | `TS-Dam-Chau-Van-Cai-Canh.ttl` | L1 |
| 9 | `TS-Dang-Van-Sieu-Cap.ttl` | L2 |
| 10 | `TS-Di-Phong-Kinh-Ninh.ttl` | L1 |
| 11 | `TS-Dong-Son-Te-Vi.ttl` | L2 |
| 12 | `TS-Khanh-Thien-Thu-Long.ttl` | L1 |
| 13 | `TS-Kinh-Trieu-Thi-Loi.ttl` | L2 |
| 14 | `TS-Minh-Hai-Phap-Bao.ttl` | L1 |
| 15 | `TS-Nam-Nhac-Minh-Toan.ttl` | L1 |
| 16 | `TS-Phung-Tuong-Thach-Tru.ttl` | L2 |
| 17 | `TS-Tay-Kinh-Nghia-Phuoc.ttl` | L1 |
| 18 | `TS-Thach-Cung-Hue-Tang.ttl` | L2 |
| 19 | `TS-Thai-Tu-Dong-Quang.ttl` | L1 |
| 20 | `TS-The-Nham-Ton-Tho.ttl` | L1 |
| 21 | `TS-Thien-Dong-Pho-Giao.ttl` | L2 |
| 22 | `TS-Tho-Thanh-So-Van.ttl` | L2 |
| 23 | `TS-Tri-Chau-Lo-To-Giao.ttl` | L2 |
| 24 | `TS-Tue-Nhat-Minh.ttl` | L1 |

> Chi tiết nhãn chuẩn: `docs/Mimo-Flash/T203-ttl-quarantine-list.md`

---

## E. ✅ File đã SỬA xong

| Nhóm | File | Việc đã làm |
|---|---|---|
| T205 — cú pháp | `TS-Ban-Son-Bao-Tich.ttl` | thêm `@prefix ex:`, vô hiệu dòng CSV dính, đóng statement |
| T205 — cú pháp | `TS-Dai-Hue-Tong-Cao.ttl` | thêm `@prefix ex:`, vô hiệu dòng CSV dính, đóng statement |
| T205 — cú pháp | `TS-Dai-Xa-Nhu-Truong.ttl` | thêm `@prefix ex:`, vô hiệu dòng CSV dính, đóng statement |
| T205 — cú pháp | `TS-Minh-Hoang-Tu-Dung.ttl` | thêm `@prefix ex:`, vô hiệu dòng CSV dính, đóng statement |
| T205 — cú pháp | `TS-Tin-Tuong-Tong-Hien.ttl` | thêm `@prefix ex:`, vô hiệu dòng CSV dính, đóng statement |
| T205 — cú pháp | `TS-Thanh-Dang-Minh-Luong.ttl` | thêm `@prefix ex:`, vô hiệu dòng CSV dính, đóng statement |
| T205 — cú pháp | `TS-Tinh-Nhan-Ke-Thanh.ttl` | thêm `@prefix ex:`, vô hiệu dòng CSV dính, đóng statement |
| T205 — cú pháp | `TS-Tuyet-Giau-Chon-Phac.ttl` | thêm `@prefix ex:`, vô hiệu dòng CSV dính, đóng statement |
| T205 — cú pháp | `TS-Van-Cai-Thu-Tri.ttl` | thêm `@prefix ex:`, vô hiệu dòng CSV dính, đóng statement |
| T205 — cú pháp | `TS-Van-Thu-Tuyen-Nang.ttl` | thêm `@prefix ex:`, vô hiệu dòng CSV dính, đóng statement |
| T206 — mojibake | 302 file | `Ð` (U+00D0) → `Đ` (U+0110), 590 ký tự |
| T207 — DB | 22 cột / 1.469 row | cùng loại lỗi trong DB + khôi phục tra cứu |

---

## Việc Admin cần làm (theo thứ tự ưu tiên)

1. **Cấp lại 10 file TTL đã mất** (nhóm A) — không thể phục hồi bằng kỹ thuật.
2. **Quyết định 3 file `phong_huyet_dien_chieu`** — 3 người hay 1?
3. **Sửa 8 file URI sai** (nhóm C) — duyệt trước vì đổi danh tính ontology.
4. **Sửa 24 nhãn** (nhóm D) để ETL chạy được.

> ETL vẫn bị chặn cho tới khi L1/L2 = 0. Guard L6/L7 hiện đang **chặn**
> đúng — không phải lỗi.
