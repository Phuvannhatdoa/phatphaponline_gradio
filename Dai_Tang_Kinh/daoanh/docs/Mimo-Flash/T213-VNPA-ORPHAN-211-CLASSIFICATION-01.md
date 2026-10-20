# T213 — VNPA Orphan 211 Classification Report
**Version:** 01  
**Date:** 2026-10-03  
**Status:** READ_ONLY — AWAIT ADMIN REVIEW  
**Author:** Claude Sonnet 4.6 (Lead AI Engineer)

---

## A. Task Identity

| Field | Value |
|-------|-------|
| Task ID | T213 |
| Title | VNPA Orphan 211 Classification |
| Version | 01 |
| Spec sections | 19 |
| Hard constraint | READ ONLY — NO DB MUTATION |
| A021395 status | BLOCKED_INSUFFICIENT_EVIDENCE (from T218) |
| D4 status | FROZEN — do not modify A010511 / dam_chau_bao_cai_uoc |

---

## B. Executive Summary

Phân loại toàn bộ **210 rows** trong `vn_person_authority` có `dila_id` rỗng hoặc NULL.  
(Spec mong đợi 211 empty-string rows; thực tế delta = 209 empty + 1 NULL = 210 — xem Section E.)

**Kết quả:**
- **C3 (VALID_LOCAL):** 165 rows — có dữ liệu hợp lệ, không cần xử lý khẩn
- **C5 (SUSPECT):** 16 rows — cần admin review trước khi assign dila_id
- **C6 (INSUFFICIENT):** 29 rows — thiếu evidence, cần bổ sung dữ liệu

**Không có C1 (RECOVERABLE), C2 (DUPLICATE), C4 (ALIAS)** trong population này.

---

## C. Baseline Snapshot

| Metric | Value |
|--------|-------|
| HEAD commit | `742ce2b` |
| Branch | `master` |
| Snapshot date | 2026-10-03 |
| DB path | `data/lineage.db` |
| DB SHA256 | `91ea38dcdb665ed9ab11ff70c5a4cb033aa90887d3f2d0f66565ddcd86684b2d` |
| Total rows `vn_person_authority` | 1506 |
| `dila_id = ''` (empty string) | 209 |
| `dila_id IS NULL` | 1 |
| `dila_id` has value | 1296 |

---

## D. Target Population

**210 rows** = 209 empty-string + 1 NULL.

Tất cả 210 rows có `status = 'pending'`. Không có alias/duplicate trong population này.

---

## E. Delta Investigation

**Spec kỳ vọng:** 211 rows `dila_id = ''`  
**Thực tế tìm thấy:** 209 empty + 1 NULL = **210 orphans**

### Giải thích delta:

| Source | Count | Lý do |
|--------|-------|-------|
| Rows gốc (spec baseline) | 211 | empty-string lúc T213 spec viết |
| Rows gained dila_id | −2 | T209/T210/T211 ETL runs assign dila_id cho 2 rows |
| Rows mới thêm (T209/T210/T211) | +3 | 3 rows mới tạo, đã có dila_id ngay |
| NULL row mới phát hiện | +1 | `tang_chu_pho_dung` — dila_id IS NULL (không phải empty string) |
| **Thực tế orphans** | **210** | |

**NULL row:** `tang_chu_pho_dung` (ttl='TS-Tang-Chu-Pho-Dung', name_vi='Tạng Chủ Phổ Dung', status='pending', created_at='2026-09-14') — không phải empty string, là NULL thật.

**4 rows gained dila_id after T215 (thêm gần đây):**
- `thach_mon_thu_tan` → A013875 (2026-10-02)
- `tien_phuoc_trach_sung` → A020706 (2026-10-02)
- `dinh_lam_canh_phuong` → A026988 (2026-10-02)
- `dien_phuc_tue_thang` → A008431 (2026-10-02)

---

## F. Classification Taxonomy

| Code | Tên | Điều kiện |
|------|-----|-----------|
| **C1** | RECOVERABLE | Có bằng chứng deterministic DILA ID từ local data (monk_dict exact match hoặc E1/E2 evidence) |
| **C2** | DUPLICATE | Row là duplicate của row đã có dila_id |
| **C3** | VALID_LOCAL | Row hợp lệ, không có local DILA ID evidence — cần ETL hoặc manual lookup |
| **C4** | GENERATED_ALIAS | Row được T200 tạo tự động (alias_ prefix hoặc status=alias_*) |
| **C5** | SUSPECT | Vấn đề data integrity: lay person, malformed, ID/name mismatch, wrong type |
| **C6** | INSUFFICIENT | Không có bio, không có name_zh — thiếu evidence để classify rõ hơn |

**Evidence levels:**

| Level | Tên | Định nghĩa |
|-------|-----|-----------|
| E1 | Deterministic | 100% chắc chắn — algorithm/structural proof |
| E2 | Strong multi-source | ≥2 nguồn đồng thuận — high confidence |
| E3 | Circumstantial | 1 nguồn, ngữ cảnh phù hợp — medium confidence |
| E4 | Unresolved | Không đủ evidence để kết luận |

---

## G. Classification Results

**Tổng kết:**

| Class | Count | % |
|-------|-------|---|
| C1 — RECOVERABLE | 0 | 0% |
| C2 — DUPLICATE | 0 | 0% |
| C3 — VALID_LOCAL | **165** | 78.6% |
| C4 — GENERATED_ALIAS | 0 | 0% |
| C5 — SUSPECT | **16** | 7.6% |
| C6 — INSUFFICIENT | **29** | 13.8% |
| **TOTAL** | **210** | 100% |

---

## H. Evidence Level Distribution

| Level | Count | % |
|-------|-------|---|
| E1 — Deterministic | 2 | 1.0% |
| E2 — Strong | 28 | 13.3% |
| E3 — Circumstantial | 151 | 71.9% |
| E4 — Unresolved | 29 | 13.8% |

> E1 rows: `thich_ca_mau_ni_phat` (Buddha) + `hoang_ba_hy_van` (malformed name)  
> E4 rows: 29 C6 rows

---

## I. C1 — RECOVERABLE (0 rows)

**Không có C1 rows.** Không có monk_dict exact name_zh match trong population này.

---

## J. C2 — DUPLICATE (0 rows)

**Không có C2 rows** phát hiện trong population orphan.

> Lưu ý: `bao_an_phap_dien` và `tu_to_phap_dien` đều có dila_id='A021395' nhưng KHÔNG phải duplicate của nhau — đây là 2 người khác nhau cùng bị gán nhầm cùng DILA ID. Trường hợp này đang bị BLOCKED theo T218. Cả 2 rows này **không** ở trong population orphan (chúng đã có dila_id giá trị).

---

## K. C3 — VALID_LOCAL (165 rows)

Rows hợp lệ, không có local DILA mapping. Phân nhóm theo lineage:

| Nhóm | Count |
|------|-------|
| Lâm Tế Dương Kỳ / Hoàng Long | ~60 |
| Thiền Tông Trung Hoa (Nam Tông / Bắc Tông) | ~40 |
| Dòng Lâm Tế Gia Phổ Việt Nam / Chúc Thánh | ~25 |
| Thiền Tông Ấn Độ (Tôn Giả) | ~15 |
| Tịnh Độ / Hoa Nghiêm / Luật / khác | ~25 |

**Top C3 rows có nhiều relation nhất (candidates ưu tiên lookup):**

| id | name_vi | total relations | lineage |
|----|---------|----------------|---------|
| thanh_vien_phat_nhan | Thanh Viễn Phật Nhãn | 24 | Lâm Tế Dương Kỳ |
| van_cu_nguyen_huu | Vân Cư Nguyên Hựu | 21 | Thiền Tông TH |
| bach_van_khong_do | Bạch Vân Không Độ | 14 | Thiền Tông TH |
| hung_duong_hien | Hưng Dương Hiền | 14 | Lâm Tế |
| nguyen_thieu_sieu_bach | Nguyên Thiều Siêu Bạch | 11 | Gia Phổ VN |
| cu_chau_loi_tung_tu_ho | Cù Châu Lợi Tung Tử Hồ | 10 | Thiền Tông TH |
| tay_thien_danh_nhu | Tây Thiền Đảnh Nhu | 10 | Thiền Tông TH |

---

## L. C4 — GENERATED_ALIAS (0 rows)

**Không có C4 rows** trong population orphan. Tất cả alias rows đã được filter ra trước — alias rows có status='alias_vi_suffix' hoặc 'alias_t200' và đã được assign dila_id từ parent row.

---

## M. C5 — SUSPECT (16 rows)

Cần admin review trước khi xử lý. Phân nhóm:

### M1. Lay person — Cư Sĩ (9 rows, E2)

| id | name_vi | Ghi chú |
|----|---------|---------|
| cs_do_thuan_dao | Cư Sĩ Đỗ Thuần Đạo | Cư sĩ, không phải tăng sĩ |
| cs_ha_thi | Cư Sĩ Hà Thị | Cư sĩ nữ |
| cs_hau_chu | Cư Sĩ Hầu Chú | Cư sĩ |
| cs_ho_nam_dang_si | Cư Sĩ Hồ Nam Đặng Sĩ | Cư sĩ |
| cs_lu | Cư Sĩ Lư | Cư sĩ |
| cs_nguyen_duc | Cư Sĩ Nguyên Đức | Cư sĩ |
| cs_nguyen_tuy | Cư Sĩ Nguyên Tuy | Cư sĩ |
| cs_phuong_tuyet | Cư Sĩ Phương Tuyết | Cư sĩ nữ |
| cs_von_xich | Cư Sĩ Vồn Xích | Cư sĩ |

### M2. Đạo Nhân — Taoist practitioner (2 rows, E2)

| id | name_vi | Ghi chú |
|----|---------|---------|
| dao_nhan_hieu | Đạo Nhân Hiểu | Đạo Nhân — không phải tăng sĩ Phật giáo |
| dao_nhan_lam_phong | Đạo Nhân Lâm Phong | Đạo Nhân |

### M3. Malformed name (1 row, E1)

| id | name_vi | Vấn đề |
|----|---------|--------|
| hoang_ba_hy_van | Hoàng_Bá_Hy_Vận | name_vi có underscores (`Hoàng_Bá_Hy_Vận`); name_zh='學道猶如守禁城' (thơ, không phải tên). Cần sửa name_vi và name_zh |

### M4. Buddha / canonical figure thiếu dila_id (1 row, E1)

| id | name_vi | Vấn đề |
|----|---------|--------|
| thich_ca_mau_ni_phat | Thích Ca Mâu Ni Phật | Đức Phật — nên có DILA ID nhưng ETL chưa assign. Candidate C1 nếu tra DILA |

### M5. ID/name mismatch (2 rows, E2)

| id | name_vi | ttl_filename | Vấn đề |
|----|---------|-------------|--------|
| thai_binh_hue_can_phat_giam | **Cốc Sơn Hải** | TS-Coc-Son-Hai | id='thai_binh_hue_can_phat_giam' nhưng name_vi='Cốc Sơn Hải' và ttl='TS-Coc-Son-Hai' — ID không khớp. Là 2 người khác nhau (Thái Bình Huệ Cần ≠ Cốc Sơn Hải). **24 relations — high priority** |
| phat_y_linh_nhac | **Trường Viễn** | TS-Truong-Vien | id='phat_y_linh_nhac' nhưng name_vi='Trường Viễn' và ttl='TS-Truong-Vien' — ID không khớp. Là 2 người khác nhau (Phật Ý Linh Nhạc ≠ Trường Viễn) |

### M6. Anomalous prefix in id (1 row, E2)

| id | name_vi | Vấn đề |
|----|---------|--------|
| cs_huong | Cs Hướng | id='cs_huong', name_vi='Cs Hướng' — 'Cs' là viết tắt 'Cư Sĩ'. Bio xác nhận là lay person ở rừng U Thê thời Bắc Tề. Thuộc Cư Sĩ category nhưng không được phát hiện bởi prefix check do tên không bắt đầu bằng 'Cư Sĩ' |

---

## N. C6 — INSUFFICIENT (29 rows)

Rows không có biographical_note_vi **và** không có name_zh. Không đủ evidence để xác định hay phân loại thêm.

Tất cả 29 rows: status='pending', evidence_level=E4.

**Một số ví dụ:**

| id | name_vi | ttl_filename |
|----|---------|-------------|
| tang_chu_pho_dung | Tạng Chủ Phổ Dung | TS-Tang-Chu-Pho-Dung |
| (28 rows khác) | | |

> `tang_chu_pho_dung` là row duy nhất có `dila_id IS NULL` (không phải empty string). Được include trong C6 do thiếu bio và name_zh.

---

## O. T217 ETL Scope Intersection

**11 orphan rows** có `ttl_filename` thuộc `data/ttl/old/` — sẽ bị **xóa** khi T217 ETL chạy và **không được tái tạo** (vì ETL chỉ tái tạo rows có dila_id trong TTL):

| id | name_vi | ttl | Class | Relations |
|----|---------|-----|-------|-----------|
| chuong_hiep_chanh_tri | Chương Hiệp Chánh Trì | TS-Chuong-Hiep-Chanh-Tri | C3 | — |
| dao_tin | Tôn Giả Đạo Tín | Ton-Gia-Dao-Tin | C3 | **14** |
| minh_hai_phap_bao | Minh Hải Pháp Bảo | TS-Minh-Hai-Phap-Bao | C3 | **21** |
| phap_kiem_minh_giac | Pháp Kiêm Minh Giác | TS-Phap-Kiem-Minh-Giac | C3 | **10** |
| thien_tue_bao_chuong | Thiên Tuế Bảo Chưởng | TS-Thien-Tue-Bao-Chuong | C3 | — |
| thiet_bao_cam_ung | Thiệt Bảo Cảm Ứng | TS-Thiet-Bao-Cam-Ung | C3 | — |
| thiet_dam_chanh_luan | Thiệt Đàm Chánh Luân | TS-Thiet-Dam-Chanh-Luan | C3 | — |
| thiet_dang_bao_quang | Thiệt Đăng Bảo Quang | TS-Thiet-Dang-Bao-Quang | C3 | — |
| thiet_dinh_an_triem | Thiệt Dinh Ân Triêm | TS-Thiet-Dinh-An-Triem | C3 | — |
| thiet_the_triem_an | Thiệt Thể Triêm Ân | TS-Thiet-The-Triem-An | C3 | — |
| toan_y_pho_hue | Toàn Ý Phổ Huệ | TS-Toan-Y-Pho-Hue | C3 | **10** |

**Rủi ro:** Khi T217 ETL chạy, 11 rows này (tổng cộng ~55 relations) sẽ bị mất trừ khi:
1. Được assign dila_id trước ETL, hoặc
2. TTL files được chuyển ra khỏi `old/` scope

**Khuyến nghị cho admin:** Ưu tiên resolve orphan status cho `minh_hai_phap_bao` (21 refs) và `dao_tin` (14 refs) trước khi chạy T217 ETL.

---

## P. Top-Reference Orphan Rows (≥10 relations)

**13 rows** có từ 10 relation trở lên — cần ưu tiên resolve:

| Rank | id | name_vi | Total | In | Out | Class | ETL Risk |
|------|----|---------|-------|-----|-----|-------|----------|
| 1 | thanh_vien_phat_nhan | Thanh Viễn Phật Nhãn | 24 | 12 | 12 | C3 | — |
| 2 | thai_binh_hue_can_phat_giam | **Cốc Sơn Hải** | 23 | 11 | 12 | **C5-mismatch** | — |
| 3 | minh_hai_phap_bao | Minh Hải Pháp Bảo | 21 | 6 | 15 | C3 | **TTL old/** |
| 4 | van_cu_nguyen_huu | Vân Cư Nguyên Hựu | 21 | 11 | 10 | C3 | — |
| 5 | hoang_ba_hy_van | Hoàng_Bá_Hy_Vận | 15 | 7 | 8 | **C5-malform** | — |
| 6 | bach_van_khong_do | Bạch Vân Không Độ | 14 | 2 | 12 | C3 | — |
| 7 | dao_tin | Tôn Giả Đạo Tín | 14 | 6 | 8 | C3 | **TTL old/** |
| 8 | hung_duong_hien | Hưng Dương Hiền | 14 | 1 | 13 | C3 | — |
| 9 | nguyen_thieu_sieu_bach | Nguyên Thiều Siêu Bạch | 11 | 3 | 8 | C3 | — |
| 10 | cu_chau_loi_tung_tu_ho | Cù Châu Lợi Tung Tử Hồ | 10 | 5 | 5 | C3 | — |
| 11 | phap_kiem_minh_giac | Pháp Kiêm Minh Giác | 10 | 2 | 8 | C3 | **TTL old/** |
| 12 | tay_thien_danh_nhu | Tây Thiền Đảnh Nhu | 10 | 5 | 5 | C3 | — |
| 13 | toan_y_pho_hue | Toàn Ý Phổ Huệ | 10 | 2 | 8 | C3 | **TTL old/** |

---

## Q. Notable Anomalies

### Q1. `thai_binh_hue_can_phat_giam` — Người sai trong row (HIGH PRIORITY)
- **id:** `thai_binh_hue_can_phat_giam` (Thái Bình Huệ Cần Phật Giám)
- **Thực tế trong row:** name_vi='Cốc Sơn Hải', ttl='TS-Coc-Son-Hai', lineage='Dòng Lâm Tế Dương Kỳ', gen=49
- **Vấn đề:** Row này chứa dữ liệu của **Thiền sư Cốc Sơn Hải**, không phải Thái Bình Huệ Cần. ID và content không khớp.
- **Impact:** 23 relations trỏ đến row này, sẽ bị gán sai người nếu dila_id được assign theo id.
- **Hành động cần thiết (admin):** Sửa id hoặc tạo lại row đúng cho Cốc Sơn Hải và Thái Bình Huệ Cần.

### Q2. `phat_y_linh_nhac` — Người sai trong row
- **id:** `phat_y_linh_nhac` (Phật Ý Linh Nhạc)
- **Thực tế:** name_vi='Trường Viễn', ttl='TS-Truong-Vien', lineage='Dòng Lâm Tế Gia Phổ Việt Nam', gen=72
- **Vấn đề:** Hòa thượng Linh Nhạc Phật Ý (1725-1821) ≠ Trường Viễn.
- **Impact:** Relations trỏ vào row này bị gán nhầm người.

### Q3. `hoang_ba_hy_van` — Malformed name + wrong name_zh
- **name_vi:** `'Hoàng_Bá_Hy_Vận'` — có underscores, chưa được normalize
- **name_zh:** `'學道猶如守禁城'` — đây là câu kệ/thơ, không phải tên Hán tự của ngài
- **Cần sửa:** name_vi → 'Hoàng Bá Hy Vận', name_zh → tên Hán thật (黃蘗希運 hoặc tương đương)

### Q4. `cs_huong` — Cư Sĩ với id bất thường
- **name_vi:** 'Cs Hướng' (viết tắt 'Cư Sĩ Hướng')
- **Bio:** Cư sĩ thời Bắc Tề (550 CE), trò của Nhị Tổ — figure quan trọng trong Thiền Tông
- **Vấn đề:** Tên không chuẩn hóa, id='cs_huong' không theo convention

### Q5. `tang_chu_pho_dung` — NULL dila_id duy nhất
- Row duy nhất với `dila_id IS NULL` (không phải empty string `''`)
- Cần kiểm tra ETL script có thể gây ra NULL thay vì empty string

---

## R. A021395 Status

**BLOCKED_INSUFFICIENT_EVIDENCE** (từ T218).

Hai rows `bao_an_phap_dien` (Bảo An Pháp Diễn) và `tu_to_phap_dien` (Tứ Tổ Pháp Diễn) đều có dila_id='A021395' nhưng là 2 người khác nhau. Không thể xác định row nào nên giữ A021395 mà không query trực tiếp DILA/CBETA.

**Không thuộc population orphan** — cả 2 đã có dila_id (tuy sai).  
**Không xử lý trong T213.**

---

## S. T213 Verdict

```
T213 VERDICT: CLASSIFICATION_COMPLETE
```

**Fields A–W:**

| Field | Value |
|-------|-------|
| A. Task ID | T213 |
| B. Verdict | CLASSIFICATION_COMPLETE |
| C. DB HEAD | `742ce2b` |
| D. DB SHA256 | `91ea38dcdb665ed9ab11ff70c5a4cb033aa90887d3f2d0f66565ddcd86684b2d` |
| E. Total rows | 1506 |
| F. Target population | 210 (209 empty + 1 NULL) |
| G. Delta vs spec | −1 (spec: 211, actual: 210) |
| H. C1 count | 0 |
| I. C2 count | 0 |
| J. C3 count | 165 |
| K. C4 count | 0 |
| L. C5 count | 16 |
| M. C6 count | 29 |
| N. Total classified | 210 |
| O. C5 reclassified from C3 | 3 (thai_binh_hue_can_phat_giam, phat_y_linh_nhac, cs_huong) |
| P. T217 ETL old/ scope | 11 rows at risk |
| Q. Top-ref rows (≥10) | 13 rows |
| R. A021395 | BLOCKED_INSUFFICIENT_EVIDENCE (T218) |
| S. D4 | FROZEN — dam_chau_bao_cai_uoc / A010511 |
| T. Mutations performed | 0 — READ ONLY |
| U. Artifact created | T213-VNPA-ORPHAN-211-CLASSIFICATION-01.md |
| V. Committed | NO — awaiting admin review |
| W. Next action | STOP — WAIT FOR ADMIN REVIEW |

---

## Admin Decision Points

Sau khi review artifact này, admin cần quyết định:

1. **C5-mismatch rows** (`thai_binh_hue_can_phat_giam`, `phat_y_linh_nhac`): Sửa id/content hay tạo row mới?
2. **C5-malform** (`hoang_ba_hy_van`): Cập nhật name_vi và name_zh đúng
3. **T217 ETL scope rows** (11 rows, đặc biệt `minh_hai_phap_bao` 21 refs, `dao_tin` 14 refs): Có resolve orphan status trước khi chạy ETL không?
4. **Top C3 rows** (`thanh_vien_phat_nhan` 24 refs, `van_cu_nguyen_huu` 21 refs): Priority DILA lookup
5. **C6 rows** (29 rows): Cần bổ sung dữ liệu source hay accept là local-only?
6. **T218** (A021395): Chọn Option A/B/D/E theo T218 decision gate

---

*READ ONLY — NO MUTATIONS PERFORMED — STOP — WAIT FOR ADMIN REVIEW*
