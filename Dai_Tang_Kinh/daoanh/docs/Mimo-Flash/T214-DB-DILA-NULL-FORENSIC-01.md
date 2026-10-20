# T214 — DB DILA-NULL FORENSIC AUDIT

**Mode**: READ-ONLY FORENSIC AUDIT  
**Priority**: CRITICAL DATA-PROVENANCE CHECK  
**Date**: 2026-10-02  
**Status**: COMPLETE — NO DB MUTATIONS IN THIS TASK

---

## 1. Task Identity

| Field | Value |
|---|---|
| Task ID | T214 |
| Spec label | T214-DB-DILA-NULL-FORENSIC-01 |
| Triggered by | Pre-T212 anomaly: 33 rows in `vn_person_authority` had `dila_id=NULL` before T212 started |
| Question | When and how did 33 rows lose their dila_id? |
| Hard limits | READ-ONLY. 0 DB mutations. 0 code changes. 0 commits until report complete. |

---

## 2. DB Baseline (live, post-T212)

```
path:    data/lineage.db
size:    1,529,729,024 bytes
mtime:   2026-10-02 15:32:19
SHA256:  813cb17f296acc97b4b8286924ff9795e76dff478fbfd9f27931e556dc2a9ee9
SQLite:  3.50.4

vn_person_authority total: 1502
  dila_id IS NULL:          33
  dila_id = '':             211
  dila_id has value:        1258
```

---

## 3. Exact 33 NULL Rows Inventory

All 33 rows (alphabetical by id):

| id | name_vi | name_zh | status | historical dila_id (T206) |
|---|---|---|---|---|
| chung_son_dao_long | Chung Sơn Đạo Long | | pending | A030596 |
| cuu_danh_to | Cửu Đảnh Tố | | pending | A024897 |
| dam_chau_dai_xuyen | Đàm Châu Đại Xuyên | | pending | A020018 |
| dong_son_te_vi | Đông Sơn Tề Vĩ | | pending | A021350 |
| duong_chau_tue_giac | Dương Châu Tuệ Giác | | pending | A026824 |
| hoa_nghiem_dao_long | Hoa Nghiêm Đạo Long | | pending | A030596 |
| hoang_long_tri_minh | Cư Sĩ Thái Sử Hoàng Đình Kiên | | pending | A008471 |
| kinh_trieu_thi_loi | Kinh Triệu Thi Lợi | | pending | A025951 |
| lang_nha_tue_giac | Lang Nha Tuệ Giác | | pending | A026824 |
| lao_na_tu_dang_dai_hoang | Đại Hồng Tổ Chứng | | pending | A021291 |
| linh_thuu_tue_giac | Linh Thứu Tuệ Giác | | pending | A026824 |
| long_khanh_khanh_nhan | Long Khánh Khánh Nhàn | | pending | A014491 |
| ma_noa_la | Tôn Giả Ma Noa La | 摩拏羅 | pending | A008792 |
| nam_nhac_huyen_thai | Nam Nhạc Huyền Thái | 畲山兒無所知年年斫斷青山 | pending | A010511 |
| ngu_dai_tri_thong | Ngũ Đài Trí Thông | | pending | A045400 |
| nguu_dau_hue_phuong | Ngưu Đầu Huệ Phương | 慧方 | pending | A038165 |
| nguyet_chuong_tri_uyen | Nguyệt Chưởng Trí Uyên | | pending | A000108 |
| phap_nhu | Pháp Như | 法如 | pending | A045639 |
| phong_huyet_dien_chieu | Nam Viện Huệ Ngung | | auto_ttl | A004981 |
| phu_son_duc_tuyen | Phù Sơn Đức Tuyên | | pending | A047679 |
| quang_tue_duc_tuyen | Quảng Tuệ Đức Tuyên | | pending | A047679 |
| so_an_hue_phuong | Sở An Huệ Phương | | pending | A038165 |
| song_lam_duc_dung | Song Lâm Đức Dụng | | pending | A021326 |
| tay_vuc_quat_da_tam_tang | Tây Vực Quật Đa Tam Tạng | 窟多三藏 | pending | A002653 |
| thach_cung_hue_tang | Thạch Củng Huệ Tạng | 石鞏慧藏 | pending | A009478 |
| thai_tu_dong_quang | Thái Tử Đồng Quảng | | pending | A038615 |
| the_nham_ton_tho | Thê Nham Tồn Thọ | | pending | A010511 |
| tho_chau_tri_thong | Thọ Châu Trí Thông | 智通 | pending | A045400 |
| tinh_do_thien_tu | Tịnh Độ Thiện Tư | | pending | A021084 |
| tri_hai_dao_binh | Tịnh Nhân Kế Thành | | pending | A014617 |
| tu_to_phap_dien | Tứ Tổ Pháp Diễn | | pending | A021395 |
| tue_nhat_minh | Tuệ Nhật Minh | | pending | A043012 |
| van_cu_phap_nhu | Vân Cư Pháp Như | | pending | A045639 |

> **Tất cả created_at = '2026-09-28T15:09:08'** (trừ phong_huyet_dien_chieu = '2026-09-14 09:14:06').  
> Không có `updated_at` column trong schema.

---

## 4. T212 Exoneration

**KẾT LUẬN: T212 ĐƯỢC MINH OAN HOÀN TOÀN.**

T212 backup được lấy **TRƯỚC KHI** apply bất kỳ mutation nào. Backup đó đã chứa 33 NULL rows.

| Backup | Timestamp | NULL rows |
|---|---|---|
| T206 | 2026-10-02 00:53 | **0** (all 33 had values) |
| T207 | 2026-10-02 08:38 | **0** (all 33 had values) |
| T208 | 2026-10-02 11:25 | **1** (nguyet_chuong_tri_uyen already NULL) |
| T212 (PRE-APPLY) | 2026-10-02 15:30 | **33** (all NULL before T212 ran) |

```
T212 backup SHA256: 88008c3f59f49702ef66bd350672a8e80bddc171c513293426b3756b62456160
```

T212 mutations = 4 DELETE rows (`alias_A009319`, `alias_A010534`, `alias_A020120`, `alias_A044094`). Các row này KHÔNG có trong 33 NULL rows. T212 không động đến bất kỳ row nào trong danh sách 33 này.

---

## 5. Timeline Reconstruction

```
2026-10-02 00:53  [T206 backup] — 0 NULL rows. Tất cả 33 dila_ids còn nguyên vẹn.
2026-10-02 08:38  [T207 backup] — 0 NULL rows. Không thay đổi.
                  [WINDOW A: 08:38 → 11:25]
                    Commit cd56a1e fix(T207): verify CJK
                    Commit 6230c40 fix(T208): khoá lexicon.key_norm_alt
                    Commit aec1b1b fix(T209): guard TTL L6+L7
                    Commit 790d8fd docs(T210): báo cáo TTL
                  → nguyet_chuong_tri_uyen (A000108) bị set NULL (1 row)
2026-10-02 11:25  [T208 backup] — 1 NULL row (nguyet_chuong_tri_uyen).
                  [WINDOW B: 11:25 → 15:30]
                    Commit 9c6e131 fix(T211): sửa subject URI 7 file TTL (15:09:21)
                    Commit 887968e docs T211 pass-2
                    Commit 27e9b6a docs HANDOFF
                  → 32 rows thêm bị set NULL
2026-10-02 15:09  T211 committed. Message: "5 URI chưa có trong DB, ETL sẽ tạo row mới"
2026-10-02 15:30  [T212 backup PRE-APPLY] — 33 NULL rows
2026-10-02 15:32  [T212 apply] — 4 alias rows deleted. T212 không đụng NULL rows.
```

---

## 6. Root Cause Analysis

### 6A. Primary Candidate: `etl_ttl_person_authority.py` sau T211

**Script**: `scripts/etl_ttl_person_authority.py`  
**Cơ chế nguy hiểm**: Dòng 437 dùng `INSERT OR REPLACE INTO vn_person_authority`.

`INSERT OR REPLACE` trong SQLite = DELETE row cũ + INSERT row mới (nếu PRIMARY KEY `id` trùng).

Khi T211 sửa subject URI trong 7 TTL files, có thể:
1. Script được chạy để re-import TTL files đã sửa
2. `INSERT OR REPLACE` xóa các rows hiện có (kèm dila_id)
3. Row mới được insert với `dila_id` từ `ttl_mapping`
4. Nếu `ttl_mapping` không có entry cho các rows này (hoặc entry có dila_id=NULL) → row mới có dila_id=NULL hoặc `''`

**Lưu ý về `''` vs NULL**: Dòng 399: `person['dila_id'] = dila_map.get(key, '')`. Nếu key không có trong `dila_map`, kết quả là `''` (empty string), không phải NULL. Tuy nhiên, nếu `ttl_mapping.dila_id` là NULL cho một số entries, Python sqlite3 trả về `None` → `dila_map[key] = None` → INSERT với `dila_id=None` = SQL NULL.

**T211 commit message note**: "5 URI còn lại chưa có trong DB nên ETL sẽ tạo row mới" — xác nhận ETL được dự kiến chạy sau T211.

### 6B. Không tìm thấy explicit UPDATE

Grep toàn bộ `*.py` không tìm thấy:
```
UPDATE vn_person_authority SET dila_id = NULL
UPDATE vn_person_authority SET dila_id=NULL
```

Không có script nào trực tiếp SET dila_id=NULL cho `vn_person_authority`. Mutation phải xảy ra qua INSERT OR REPLACE (delete+reinsert) hoặc một cơ chế gián tiếp.

### 6C. WINDOW A (1 row: nguyet_chuong_tri_uyen)

Giữa T207 (08:38) và T208 (11:25), chỉ 1 row bị NULL. Commits trong window này chủ yếu là doc/fix không liên quan ETL. Khả năng: chạy thử `etl_ttl_person_authority.py` cho một file cụ thể, hoặc manual SQL.

### 6D. WINDOW B (32 rows)

Giữa T208 (11:25) và T212 start (15:30), T211 commit tại 15:09 sửa 7 TTL files. **Root cause chính xác nhất = chạy `etl_ttl_person_authority.py` sau T211 commit**, khi script này REPLACE 32 rows với NULL dila_id vì `ttl_mapping` không cover đủ.

---

## 7. Impact Analysis

### 7A. T200 Lookup Impact

T200 `lookup_by_dila(conn, dila_id)` tìm trong `vn_person_authority` theo `VNPA_STATUS_RANK`.

**20 rows COVERED** (T200 vẫn hoạt động nhờ row khác có cùng dila_id):

| Row bị NULL | dila_id | Row còn dila_id |
|---|---|---|
| cuu_danh_to | A024897 | long_hoa_dao_so |
| dam_chau_dai_xuyen | A020018 | phung_tuong_phat_da |
| dong_son_te_vi | A021350 | giac_a |
| hoang_long_tri_minh | A008471 | hoang_dinh_kien |
| kinh_trieu_thi_loi | A025951 | dam_chau_hoa_lam |
| lao_na_tu_dang_dai_hoang | A021291 | dai_hong_to_chung |
| long_khanh_khanh_nhan | A014491 | an_hoa_van_nhat |
| ma_noa_la | A008792 | ca_ty_ma_la |
| nam_nhac_huyen_thai | A010511 | dam_chau_bao_cai_uoc ⚠️ WRONG PERSON |
| nguyet_chuong_tri_uyen | A000108 | bao_ninh_nhan_dung |
| phong_huyet_dien_chieu | A004981 | nam_vien_hue_ngung |
| song_lam_duc_dung | A021326 | pho_minh_duc_dung |
| tay_vuc_quat_da_tam_tang | A002653 | bien_dam_hieu_lieu |
| thach_cung_hue_tang | A009478 | ngu_dai_an_phong |
| thai_tu_dong_quang | A038615 | thai_tu_dao_nhat |
| the_nham_ton_tho | A010511 | dam_chau_bao_cai_uoc ⚠️ WRONG PERSON |
| tinh_do_thien_tu | A021084 | tho_ninh_thien_tu |
| tri_hai_dao_binh | A014617 | tang_chu_pho_dung |
| tu_to_phap_dien | A021395 | alias_A021395, bao_an_phap_dien |
| tue_nhat_minh | A043012 | hoang_ba_vinh_thai |

**13 rows BROKEN** (T200 lookup trả về None/sai vì không có row khác):

| Row bị NULL | dila_id bị mất | Tình trạng |
|---|---|---|
| chung_son_dao_long | A030596 | BROKEN |
| hoa_nghiem_dao_long | A030596 | BROKEN |
| duong_chau_tue_giac | A026824 | BROKEN |
| lang_nha_tue_giac | A026824 | BROKEN |
| linh_thuu_tue_giac | A026824 | BROKEN |
| ngu_dai_tri_thong | A045400 | BROKEN |
| tho_chau_tri_thong | A045400 | BROKEN |
| nguu_dau_hue_phuong | A038165 | BROKEN |
| so_an_hue_phuong | A038165 | BROKEN |
| phap_nhu | A045639 | BROKEN |
| van_cu_phap_nhu | A045639 | BROKEN |
| phu_son_duc_tuyen | A047679 | BROKEN ← D2 critical |
| quang_tue_duc_tuyen | A047679 | BROKEN ← D2 critical |

**Unique broken dila_ids**: A026824, A030596, A038165, A045400, A045639, A047679 (6 dila_ids)

### 7B. Critical dila_ids (từ T208 decisions)

| dila_id | Status trong live DB |
|---|---|
| A021395 | alias_A021395 (alias_vi_suffix) + bao_an_phap_dien (pending) — D3 UNBLOCKED |
| A010511 | dam_chau_bao_cai_uoc (auto_ttl) — WRONG PERSON, D4 plan unchanged |
| A047679 | **KHÔNG CÓ ROW NÀO** — cả phu_son_duc_tuyen và quang_tue_duc_tuyen đều NULL |

**A047679 nghiêm trọng nhất**: D2 trong T208 defer "cần DILA evidence". Sau T214, cả 2 rows đều mất dila_id. T200 lookup cho A047679 hiện = BROKEN.

### 7C. Scope T213 không bị ảnh hưởng

33 NULL rows khác với 211 empty-string rows. T213 vẫn scope = 211 `dila_id=''` rows. T214 không thay đổi scope T213.

---

## 8. Recovery Path

**Đầy đủ và khả thi.** Tất cả 33 giá trị historical dila_id đã được xác định từ T206/T207 backups.

### Recovery script (CHƯA THỰC HIỆN — cần Admin approve)

```sql
-- Restore 33 dila_id values from T206 backup
UPDATE vn_person_authority SET dila_id='A030596' WHERE id='chung_son_dao_long';
UPDATE vn_person_authority SET dila_id='A024897' WHERE id='cuu_danh_to';
UPDATE vn_person_authority SET dila_id='A020018' WHERE id='dam_chau_dai_xuyen';
UPDATE vn_person_authority SET dila_id='A021350' WHERE id='dong_son_te_vi';
UPDATE vn_person_authority SET dila_id='A026824' WHERE id='duong_chau_tue_giac';
UPDATE vn_person_authority SET dila_id='A030596' WHERE id='hoa_nghiem_dao_long';
UPDATE vn_person_authority SET dila_id='A008471' WHERE id='hoang_long_tri_minh';
UPDATE vn_person_authority SET dila_id='A025951' WHERE id='kinh_trieu_thi_loi';
UPDATE vn_person_authority SET dila_id='A026824' WHERE id='lang_nha_tue_giac';
UPDATE vn_person_authority SET dila_id='A021291' WHERE id='lao_na_tu_dang_dai_hoang';
UPDATE vn_person_authority SET dila_id='A026824' WHERE id='linh_thuu_tue_giac';
UPDATE vn_person_authority SET dila_id='A014491' WHERE id='long_khanh_khanh_nhan';
UPDATE vn_person_authority SET dila_id='A008792' WHERE id='ma_noa_la';
UPDATE vn_person_authority SET dila_id='A010511' WHERE id='nam_nhac_huyen_thai';
UPDATE vn_person_authority SET dila_id='A045400' WHERE id='ngu_dai_tri_thong';
UPDATE vn_person_authority SET dila_id='A038165' WHERE id='nguu_dau_hue_phuong';
UPDATE vn_person_authority SET dila_id='A000108' WHERE id='nguyet_chuong_tri_uyen';
UPDATE vn_person_authority SET dila_id='A045639' WHERE id='phap_nhu';
UPDATE vn_person_authority SET dila_id='A004981' WHERE id='phong_huyet_dien_chieu';
UPDATE vn_person_authority SET dila_id='A047679' WHERE id='phu_son_duc_tuyen';
UPDATE vn_person_authority SET dila_id='A047679' WHERE id='quang_tue_duc_tuyen';
UPDATE vn_person_authority SET dila_id='A038165' WHERE id='so_an_hue_phuong';
UPDATE vn_person_authority SET dila_id='A021326' WHERE id='song_lam_duc_dung';
UPDATE vn_person_authority SET dila_id='A002653' WHERE id='tay_vuc_quat_da_tam_tang';
UPDATE vn_person_authority SET dila_id='A009478' WHERE id='thach_cung_hue_tang';
UPDATE vn_person_authority SET dila_id='A038615' WHERE id='thai_tu_dong_quang';
UPDATE vn_person_authority SET dila_id='A010511' WHERE id='the_nham_ton_tho';
UPDATE vn_person_authority SET dila_id='A045400' WHERE id='tho_chau_tri_thong';
UPDATE vn_person_authority SET dila_id='A021084' WHERE id='tinh_do_thien_tu';
UPDATE vn_person_authority SET dila_id='A014617' WHERE id='tri_hai_dao_binh';
UPDATE vn_person_authority SET dila_id='A021395' WHERE id='tu_to_phap_dien';
UPDATE vn_person_authority SET dila_id='A043012' WHERE id='tue_nhat_minh';
UPDATE vn_person_authority SET dila_id='A045639' WHERE id='van_cu_phap_nhu';
```

**Nguồn**: T206 backup (`lineage_t206_20261002_005334.db`) xác nhận bởi T207 backup (100% match).  
**Xác minh sau restore**: 33 rows → từ dila_id IS NULL → có dila_id value. vn_person_authority total không đổi (vẫn 1502).

**Lưu ý D4**: `nam_nhac_huyen_thai.dila_id` restore về A010511, nhưng D4 plan đã chuẩn bị `dam_chau_bao_cai_uoc.dila_id=A010511` (WRONG person còn đó). Recovery task này cần coordinate với D4 fix.

---

## 9. Verdict và Blockers Cleared

### VERDICT: FORENSIC COMPLETE

```
T214 VERDICT: FORENSIC AUDIT COMPLETE — ROOT CAUSE IDENTIFIED (PLAUSIBLE), RECOVERY PATH CLEAR
```

### T212 Exoneration
✅ **T212 EXONERATED**: Mutation xảy ra TRƯỚC T212. T212 backup pre-apply đã chứa 33 NULL rows.

### Root Cause
🔍 **PRIMARY CANDIDATE**: `etl_ttl_person_authority.py` (`INSERT OR REPLACE`) được chạy sau T211 commit (15:09:21), overwrite 32 existing rows với dila_id NULL/empty. Mechanism chính xác (NULL vs '') cần verify với `ttl_mapping` table state.

🔍 **WINDOW A** (1 row giữa T207-T208): cơ chế tương tự hoặc manual SQL, chưa xác định chính xác.

### Blockers Cleared

| Task | Trạng thái sau T214 |
|---|---|
| D3 (A021395) | **UNBLOCKED** — alias_A021395 và bao_an_phap_dien vẫn có dila_id=A021395 |
| D4 (A010511) | **PARTIALLY UNBLOCKED** — plan D4 vẫn valid; recovery 33 rows cần coordinate trước khi D4 apply |
| D2 (A047679) | **MORE URGENT** — cả 2 rows mất dila_id; T200 lookup A047679 broken |
| T213 | **UNBLOCKED** — scope không thay đổi (211 empty-string rows, không phải NULL rows) |

### Next Actions (Admin approve cần)

1. **T215** (đề xuất): Restore 33 dila_ids từ T206 backup → 33 UPDATE statements ở mục 8  
2. **D3** (sau T215): Admin chọn Option A hoặc B → execute D3 mutation  
3. **D4** (sau T215): Execute [4A][4B][4C][4D] với coordinate D4+recovery  
4. **D2** (A047679 nghiêm trọng): Tìm DILA evidence cho `phu_son_duc_tuyen` và `quang_tue_duc_tuyen`

---

## 10. Forensic Evidence Summary

| Evidence | Value |
|---|---|
| T206 backup NULL rows | 0 |
| T207 backup NULL rows | 0 |
| T208 backup NULL rows | 1 (nguyet_chuong_tri_uyen) |
| T212 pre-apply backup NULL rows | 33 |
| T212 mutations | 4 DELETE (alias rows only, không overlap với 33 NULL rows) |
| Historical dila_ids recovered | 33/33 (100%) |
| T200 broken lookups | 13 rows (6 unique dila_ids) |
| T200 covered (still works) | 20 rows |
| T200 returns WRONG person | 2 rows (A010511 → dam_chau_bao_cai_uoc) |
| Scripts with INSERT OR REPLACE on vn_person_authority | etl_ttl_person_authority.py:437 |
| Scripts with explicit UPDATE vn_person_authority SET dila_id=NULL | NONE FOUND |

---

*T214 Forensic Audit · READ-ONLY · 2026-10-02 · Thực hiện: Claude Code*
