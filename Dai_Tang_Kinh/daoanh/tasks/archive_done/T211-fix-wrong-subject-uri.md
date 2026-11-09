---
id: T211
title: Sửa subject URI sai trong 7 file TTL (chỉ nhóm nhãn khớp tên file)
status: done
created: 2026-10-02
owner: agent
module: daoanh
depends_on: T209, T210
commit: 9c6e131
revert: 'python -X utf8 scripts/t211_fix_wrong_subject_uri.py --revert data/backups/t211_uri_20261002_145746'
---

# T211 — Sửa subject URI sai (nhóm an toàn)

> Admin phê chuẩn build T210 (báo cáo trạng thái file), trong đó nhóm C là
> "URI sai — cần duyệt". Task này xử lý **phần có thể chứng minh bằng dữ liệu**;
> phần còn lại chờ Admin.

---

## 1. Bối cảnh

Lỗi copy-paste khi sinh TTL: **URI giữ từ người trước, còn nhãn thì đúng**.
Nhiều file dùng chung một `ex:monk/X` ⇒ ETL chỉ nạp file cuối, **các file kia
mất im lặng**. Guard **L7** của T209 chặn việc này.

## 2. Vì sao chỉ sửa 7 / 21 file

Sửa `ex:monk/X` là **đổi danh tính ontology**: `vn_person_authority` sẽ sinh
row MỚI, row CŨ thành orphan. Chỉ an toàn khi có bằng chứng **hai chiều**:

> **nhãn trong file == tên file** ⇒ URI mới là lỗi gõ

| Nhóm | Điều kiện | Hậu quả | Số file |
|------|-----------|----------|--------|
| **1 — SỬA ĐƯỢC** | nhãn khớp tên file **100%** | URI là lỗi gõ | **7** |
| 2 — CẦN ADMIN | cả nhãn cũng lệch | file đặt tên sai HOẶC nội dung sai | 14 |

### Đã sửa 7 file
| File | URI cũ (sai) | URI mới |
|---|---|---|
| `TS-Bich-Thien-Thanh-Khong.ttl` | `bach_van_khong_do` | `bich_thien_thanh_khong` |
| `TS-Vo-Huyen-Tinh-Xung.ttl` | `bach_van_khong_do` | `vo_huyen_tinh_xung` |
| `TS-Vo-Tan-Tue-Hai.ttl` | `bach_van_khong_do` | `vo_tan_tue_hai` |
| `TS-Dien-Phuc-Tue-Thang.ttl` | `duc_vuong_doan_du` | `dien_phuc_tue_thang` |
| `TS-Vo-Chuan-Su-Pham.ttl` | `pha_am_to_tien` | `vo_chuan_su_pham` |
| `TS-Truong-Linh-Thu-Trac.ttl` | `phap_luan_ung_doan` | `truong_linh_thu_trac` |
| `TS-Van-Mon-Hai-An.ttl` | `van_mon_hai_yen` | `van_mon_hai_an` |

### Kiểm tra chéo trước khi ghi
2 URI mới **đã tồn tại trong DB** với **đúng nhãn tương ứng**:

| URI mới | `name_vi` trong DB | Nhãn trong TTL | Kết luận |
|---|---|---|---|
| `vo_chuan_su_pham` | Vô Chuẩn Sư Phạm | Vô Chuẩn Sư Phạm | Khớp → **nối lại đúng người** |
| `truong_linh_thu_trac` | Trường Linh Thủ Trác | Trường Linh Thủ Trác | Khớp → **nối lại đúng người** |

5 URI mới còn lại chưa có trong DB ⇒ ETL sẽ tạo row mới (đúng như mong đợi).

## 3. Kết quả

- **L7: 15 → 10 slug trùng.**
- Nhóm 1 còn **0** file URI sai.
- Corpus **1037/1037 parse OK**, mỗi file **giữ nguyên số triple** (chỉ đổi tên
  URI, không đổi cấu trúc) — có kiểm tra và **rollback từng file** nếu lệch.
- `crm:P1_is_identified_by` được đồng bộ theo (nếu không sẽ còn URI cũ sót).
- `bach_van_khong_do` **được giữ** cho `TS-Bach-Van-Khong-Do.ttl` của chính nó.

## 4. ⚠️ DB CHƯA ĐỒNG BỘ — cần Admin

Tôi **không sửa DB**. ETL đang bị chặn bởi L1/L2, và nhãn là việc curation của
Admin. Việc này sẽ tự xảy ra khi chạy lại ETL.

**Tuy nhiên sửa URI đã LỘ RA 1 lỗi nhãn trước đây bị che giấu:**
```
TS-Dien-Phuc-Tue-Thang.ttl  id=duc_vuong_doan_du
   DB đang có : 'Diên Phúc Tuệ Thăng'
   Đúng ra    : 'Dục Vương Đoan Dụ'   (theo TS-Duc-Vuong-Doan-Du.ttl)
```
Trước khi sửa URI, file này "chiếm" URI `duc_vuong_doan_du` nên classifier T203
không thấy sai lệch. Sau khi URI đúng, sai lệch hiện rõ.

Khi nào Admin duyệt nhãn: chạy
```bash
python -X utf8 scripts/t203_sync_vnpa_name.py --dry-run
python -X utf8 scripts/t203_sync_vnpa_name.py --apply
```

## 5. Test

`tests/test_t211_wrong_subject_uri.py`: **15/15 PASS** — chạy trên thư mục TTL
tạm, **không đụng corpus thật**. Chứng minh: chỉ sửa nhóm an toàn; không sửa nhóm
cần Admin; `P1_is_identified_by` đồng bộ; số triple không đổi; revert khôi phục
đúng nội dung gốc.

`tests/test_t203_ttl_guard.py`: **27/27 PASS** — sửa 2 assert bị sai:
- "co canh bao L4/L5" → L4/L5 đã về **0**, warnings rỗng là trạng thái ĐÚNG
- "DB da sync: plan == 0" → sửa URI làm lộ lỗi nhãn bị che giấu ⇒ `plan > 0` là
  ĐÚNG, phải chạy t203 sync

## 6. Đã tạo

| File | Vai trò |
|------|---------|
| `scripts/t211_fix_wrong_subject_uri.py` | `--stats/--dry-run/--apply/--verify/--revert` |
| `scripts/probe_t211.py` | phân loại 2 nhóm (bằng chứng) |
| `tests/test_t211_wrong_subject_uri.py` | 15/15 PASS |
| `package.json` | `test:t211` → nối `test:translation` |

## 7. Revert

```bash
git revert --no-edit <sha_T211>                                          # code+docs
python -X utf8 scripts/t211_fix_wrong_subject_uri.py \
    --revert data/backups/t211_uri_20261002_145746                       # TTL (1 lệnh)
```

TTL không git track ⇒ **bắt buộc** dùng backup file-level để revert.

## 8. Còn lại (cần Admin)

1. **13 file nhóm 2** — URI sai VÀ nhãn cũng lệch, cần quyết định của Admin.
   Đáng chú ý: `TS-Dai-Xa-Nhu-Truong` / `TS-Minh-Hoang-Tu-Dung` /
   `TS-Tuyet-Giau-Chon-Phac` (gen 69/70/71, chung URI `phong_huyet_dien_chieu`,
   nhãn đều "Nam Viện Huệ Ngung" nhưng tên file là 3 người khác nhau).
2. **10 file TTL đã mất** (T209/T210 nhóm A) — cần bản gốc.
3. **L1 = 13, L2 = 15** — nhãn sai, chặn ETL.
4. **L4 = 0, L5 = 0** ✅ — mojibake và `dila_id` trùng đã sạch.
5. **T210**: nối truy vấn 2 bước `key_norm_alt` — chờ `app.py` hết WIP.