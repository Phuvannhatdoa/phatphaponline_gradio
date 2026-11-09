---
id: T209
title: Guard L6 (file TTL rỗng) + L7 (subject URI trùng giữa các file) + phục hồi file bị mất
status: done
created: 2026-10-02
owner: agent
module: daoanh
depends_on: T205, T206
commit: "083b77b3135eccfe96f4ae624442eb8916fccb7e"
revert: "git revert --no-edit <sha_T209>"
---

# T209 — Guard mất dữ liệu TTL (L6/L7) + phục hồi file bị xoá rỗng

> Trigger: khảo sát 3 file TTL trùng người (`phong_huyet_dien_chieu`) để gộp,
> phát hiện `TS-Dai-Xa-Nhu-Truong.ttl` **còn 0 byte** — file bị xoá sạch bởi
> tiến trình/session khác. TTL **không git track** ⇒ mất thật, không `git revert`
> được, chỉ cứu được nhờ backup file-level của T205.

---

## 1. Sự cố: file TTL bị xoá rỗng

| Mục | Chi tiết |
|---|---|
| File | `TS-Dai-Xa-Nhu-Truong.ttl` |
| Trạng thái | **0 byte** |
| Hậu quả | ETL mất 1 vị tu sĩ; `git status`/`git revert` **không thấy** vì TTL nằm trong `data/` bị `.gitignore` |
| Phục hồi | `data/backups/t205_ttl_20261001_203559/` (39.831 byte) → chạy lại `t205_repair_broken_ttl.py --apply` |

Sau khi phục hồi: 18 triple, `generationOrder=70`, corpus **1037/1037 parse OK**.

> **Lưu ý:** backup T205 được tạo **trước** T206 nên bản phục hồi còn `Ð` (U+00D0)
> → phải chạy lại `t206_fix_mojibake.py --apply` (đã làm, sửa 2 ký tự).

**Bài học:** backup phục hồi phải hiểu nó thuộc thời điểm nào. Backup "trước khi
sửa" của T205 không chứa fix của T206.

---

## 2. Guard L6 — file TTL rỗng (chặn)

`check_empty()` trong `scripts/t204_ttl_preflight.py`:
- file **0 byte** → `L6` blocking
- file parse được nhưng **không có triple nào** → `L6` blocking

Đưa vào `preflight()` ⇒ **ETL bị chặn** trước khi nạp, không âm thầm mất dữ liệu.

## 3. Guard L7 — cùng một subject URI ở nhiều file (chặn)

`check_subject_collision()`: quét **khai báo đầu tiên** `<ex:monk/X> a <bkg:Monk>`
của mỗi file; nếu một slug xuất hiện ở **>1 file** ⇒ `L7` blocking.

> **Phải chỉ lấy khai báo ĐẦU TIÊN.** Một file có thể khai báo thêm nhiều tu sĩ
> ở khối thứ hai (do lỗi dính dòng CSV mà T205 gặp) — đó không phải chủ đề của
> file. Lấy tất cả sẽ báo **16 false positive**; chỉ lấy đầu tiên còn **15**.

### Vì sao L7 nghiêm trọng
Các file ghi đè lẫn nhau trên cùng một URI ⇒ **chỉ file cuối cùng được nạp**,
các file kia **mất im lặng**, không có bất kỳ cảnh báo nào.

---

## 4. Phát hiện lớn: **URI sai trong file nguồn**

15 slug bị trùng, lan sang **22 file**. Nguyên nhân là lỗi copy-paste khi sinh
TTL: subject URI bị giữ từ người trước, còn nhãn thì đúng.

Ví dụ (tên file → URI thật trong file → nhãn):

| File | URI đang khai báo | Nhãn trong file |
|---|---|---|
| `TS-Bich-Thien-Thanh-Khong.ttl` | `bach_van_khong_do` | Bích Thiên Thanh Không |
| `TS-Di-Phong-Kinh-Ninh.ttl` | `bach_van_khong_do` | Nguyệt Khê Diệu Trừng |
| `TS-Dot-Khong-Tri-Ban.ttl` | `bach_van_khong_do` | Đột Không Trí Bản |
| `TS-Vo-Huyen-Tinh-Xung.ttl` | `bach_van_khong_do` | Vô Huyễn Tịnh Xung |
| `TS-Vo-Tan-Tue-Hai.ttl` | `bach_van_khong_do` | Vô Tận Tuệ Hải |
| `TS-Dien-Phuc-Tue-Thang.ttl` | `duc_vuong_doan_du` | Diên Phúc Tuệ Thăng |
| `TS-Dong-Son-Trach-Ngon.ttl` | `dong_son_pham_ngon` | Động Sơn Trạch Ngôn |

5 file `bach_van_khong_do` dồn về **một** URI ⇒ 4 vị tu sĩ bị mất khi ETL.

### KHÔNG tự sửa — vì sao
Sửa URI là đổi **danh tính ontology**: `vn_person_authority` sẽ sinh row MỚI, row
cũ thành orphan. Đây là quyết định của Admin, không phải việc đoán tên. Hơn nữa
vẫn còn nhóm mà **cả tên file lẫn nhãn đều khác URI** (ví dụ 3 file
`phong_huyet_dien_chieu` với `generationOrder` 69/70/71, đều nhãn
"Nam Viện Huệ Ngung" nhưng tên file là 3 người khác nhau) — nhóm này **phải do
Admin xác nhận** mới gộp được.

T209 chỉ **phát hiện + chặn**, không sửa dữ liệu.

---

## 5. Phát hiện thêm: 10 file TTL mà DB vẫn tham chiếu đã mất

`vn_person_authority` còn 1.015 `ttl_filename`, trong đó **10 không còn file trên đĩa**:

```
TS-Chuong-Hiep-Chanh-Tri     TS-Duong-Ki-Phuong-Hoi     TS-Phap-Kiem-Minh-Giac
TS-Phap-Mon-Phat-Da          TS-Thiet-Bao-Cam-Ung       TS-Thiet-Dam-Chanh-Luan
TS-Thiet-Dang-Bao-Quang      TS-Thiet-Dinh-An-Triem     TS-Thiet-The-Triem-An
TS-Toan-Y-Pho-Hue
```

Không có backup của các file này (T205/T206 chỉ backup file đã sửa) ⇒ **cần bản
gốc từ Admin**. Corpus giảm 1038 → 1037 data file trong lúc các session khác
đang chạy song song.

---

## 6. Test

`tests/test_t203_ttl_guard.py`: **27/27 PASS** (thêm 5 assert cho L6/L7):
- L6 bắt file 0 byte, không báo lỗi trên file tốt
- L7 bắt subject trùng 2 file, không báo lỗi khi slug duy nhất
- **L7 chỉ lấy subject đầu tiên** (khối phụ không bị đếm)
- Bỏ hardcode `1038` trong assert corpus (số file biến động do session khác)

## 7. Revert
```bash
git revert --no-edit <sha_T209>    # chỉ code + docs, không đụng TTL/DB
```

---

## 8b. Trạng thái đo đọc lại 2026-10-02 (sau commit `083b77b3135eccfe96f4ae624442eb8916fccb7e`)

Các con số đẽ liệt kệ trong §4/§8 là **số lúc
2026-10-02 sáng**, đã các session khác sửa tiếp. Để **không**
sửa ngược để giữ lịch sử phát hiện; bảng dưới đây mới:

| Chề | T209 ghi | Hiện tại |
|---|---|---|
| Corpus data file | 1.037 | **1.038** |
| File 0 byte | 1 (`TS-Dai-Xa-Nhu-Truong`) | **0** |
| Slug trùng (L7) | 15 slug / 22 file | **5 slug / 13 file** |
| File URI sai | 22 | **8** (T211 đã sửa 7) |
| Nhãn sai | 15 | **24** |
| L1 / L2 | 15 / 15 | **11 / 13** |
| L5 | 12 | **24** |

Preflight: **BLOCKING 29** (L1 11 · L2 13 · L3 0 · L6 0 · L7 5) ·
**WARNING 24** (L4 0 · L5 24).

**Các 5 slug L7 còn lại** (đểu tiến sửa, đã cả 5 slug đểu
của T209):

| Slug trùng | File dùng chung |
|---|---|
| `bach_van_khong_do` | `TS-Bach-Van-Khong-Do` (chỡ), `TS-Di-Phong-Kinh-Ninh`, `TS-Dot-Khong-Tri-Ban` |
| `phong_huyet_dien_chieu` | `TS-Phong-Huyet-Dien-Chieu` (chủ), `TS-Dai-Xa-Nhu-Truong`, `TS-Minh-Hoang-Tu-Dung`, `TS-Tuyet-Giau-Chon-Phac` |
| `bach_truong_hoai_hai` | `TS-Bach-Truong-Hoai-Hai` (chủ), `TS-Phuoc-Chau-Dai-An` |
| `dao_ninh_dao_khoan` | `TS-Dao-Ninh-Dao-Khoan` (chủ), `TS-Dai-Ninh-Dao-Khoan` |
| `thach_cuu` | `TS-Thach-Cuu` (chủ), `TS-Linh-Cuu` |

Đểu chố **13 file** = 5 "chủ sở" (URI đúng) + **8 "kế áp cáo"**
(URI sai) — khởp đúng với nhóm trong `docs/TTL-FILE-STATUS-REPORT.md` nhóm C=8.
Để 8 file kế áp cáo **đểu cần Admin duyệt** để sửa.

> **Rảt quan trộng:** guard L6/L7 (`check_empty`, `check_subject_collision`) đã
> đưọc commit vào `scripts/t204_ttl_preflight.py`. TTL **không git track**
> nên 2 guard này là lưới an toän duy nhất — mất chúng có thát sự
> mất dữ liệu.

## 8. Còn lại (cần Admin)
1. **Xác nhận 22 file URI sai** ở §4 — có thể sửa cơ học theo tên file cho phần
   lớn, nhưng cần duyệt vì đổi danh tính ontology.
2. **Quyết định 3 file `phong_huyet_dien_chieu`** (gen 69/70/71) — 3 người hay 1?
3. **Cấp lại 10 file TTL đã mất** ở §5.
4. **L1 = 15, L2 = 15** — nhãn sai, vẫn chặn ETL.
5. **L5 = 12** nhóm `dila_id` trùng.
6. `app.py` còn WIP session khác ⇒ T210 (nối truy vấn 2 bước `key_norm_alt`) chờ.