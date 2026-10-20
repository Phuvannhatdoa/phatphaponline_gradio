# T207-ADMIN-CURATION-DECISION-GATE-01

**Status**: FINAL · **Date**: 2026-10-02
**Mode**: READ-ONLY — 0 DB mutation, 0 code change, 0 commit
**Baseline**: HEAD=`9641215` (T206 PASS)

---

## SECTION 1 — T206 Closed State Verification

| entity_ref | canonical_name_vi | is_valid_vi | authority_rank | vstatus | lock.status | lock.level |
|---|---|---|---|---|---|---|
| `PL000000000314` | `'Thế Sát Hải'` | `True` | `admin_approved` | `verified` | **LOCKED** | **1.0** |
| `PL000000000001` | `'Khoát Tạt Đa Quốc'` | `True` | `auto_transliterate` | `needs_review` | CANDIDATE | 0.7 |

`safe_errors()` = `[]` ✓

**T206 state confirmed. Do not modify either row.**

---

## SECTION 2 — T200: 33 Duplicate DILA-ID Groups

**Confirmed**: 33 groups với `dila_id != ''` và `COUNT(*) > 1`. Matches T203 inventory exactly.
**vn_person_authority total rows**: 1506

All data verified from live DB (read-only). Arranged by T203 classification.

---

### 2A — CLEAR_ALIAS (7 groups)

Cùng tên gốc, row thừa có thể xóa sau khi Admin approve.

**Current T200 behavior**: `VNPA_STATUS_RANK` → `pending` (rank 1) thắng `alias_vi_suffix` (rank 3) thắng `auto_ttl` (rank 2). `id ASC` tie-break.

| dila_id | Row 1 (id / name_vi / name_zh / status) | Row 2 (id / name_vi / name_zh / status) | Tie-break winner |
|---|---|---|---|
| **A004981** | `phong_huyet_dien_chieu` / `Nam Viện Huệ Ngung` / `` / `auto_ttl` | `nam_vien_hue_ngung` / `Nam Viện Huệ Ngung` / `` / `pending` | `nam_vien_hue_ngung` |
| **A009319** | `alias_A009319` / `Tung Sơn Phổ Tịch` / `嵩山普寂` / `alias_vi_suffix` | `tung_son_pho_tich` / `Tung Sơn Phổ Tịch` / `普寂` / `pending` | `tung_son_pho_tich` |
| **A010534** | `alias_A010534` / `Huyền Sách` / `玄策` / `alias_vi_suffix` | `vu_chau_huyen_sach` / `Vụ Châu Huyền Sách` / `玄策` / `pending` | `vu_chau_huyen_sach` |
| **A020120** | `alias_A020120` / `Đàm Châu Trung Vân Cái` / `中雲蓋` / `alias_vi_suffix` | `dam_chau_trung_van_cai` / `Đàm Châu Trung Vân Cái` / `` / `pending` | `dam_chau_trung_van_cai` |
| **A021291** | `dai_hong_to_chung` / `Đại Hồng Tổ Chứng` / `` / `auto_ttl` | `lao_na_tu_dang_dai_hoang` / `Đại Hồng Tổ Chứng` / `` / `pending` | `lao_na_tu_dang_dai_hoang` |
| **A044094** | `alias_A044094` / `Ngô Hưng Pháp Hải` / `法海` / `alias_vi_suffix` | `thieu_chau_phap_hai` / `Thiều Châu Pháp Hải` / `法海` / `pending` | `thieu_chau_phap_hai` |
| **A008471** | `hoang_dinh_kien` / `Cư Sĩ Thái Sử Hoàng Đình Kiên` / `` / `pending` | `hoang_long_tri_minh` / `Cư Sĩ Thái Sử Hoàng Đình Kiên` / `` / `pending` | `hoang_dinh_kien` (id ASC) |

**people table cross-reference (all confirm same person)**:

| dila_id | people.name_zh | people.name_vi |
|---|---|---|
| A004981 | 慧顒 | Tuệ Ngung |
| A009319 | 嵩山普寂 | Tung Sơn Phổ Tịch |
| A010534 | 玄策 | Huyền Sách |
| A020120 | 中雲蓋 | Trung Vân Cái |
| A021291 | 祖證 | Tổ Chứng |
| A044094 | 法海 | Pháp Hải |
| A008471 | 黃庭堅 | Hoàng Đình Kiên |

---

### 2B — POSSIBLE_DUPLICATE (10 groups)

Tên lõi khớp `people.name_vi`, tiền tố chùa/địa điểm khác nhau. Khả năng 1 người nhiều tiền tố.

| dila_id | people.name_zh | people.name_vi | Rows (id / name_vi / status) | T200 winner |
|---|---|---|---|---|
| **A020456** | 智嵩 | Trí Tung | `alias_A020456` / Tam Giao Trí Tung / `alias_vi_suffix`; `thiet_phat_tri_tung` / Thiết Phật Trí Tung / `pending` | `thiet_phat_tri_tung` |
| **A021084** | 善孜 | Thiện Tư | `tho_ninh_thien_tu` / Thọ Ninh Thiện Tư / `auto_ttl`; `tinh_do_thien_tu` / Tịnh Độ Thiện Tư / `pending` | `tinh_do_thien_tu` |
| **A021326** | 德用 | Đức Dụng | `pho_minh_duc_dung` / Phổ Minh Đức Dụng / `auto_ttl`; `song_lam_duc_dung` / Song Lâm Đức Dụng / `pending` | `song_lam_duc_dung` |
| **A021395** | 法演 | Pháp Diễn | 3 rows — xem §4 priority detail | — |
| **A023045** | 法達 | Pháp Đạt | `alias_A023045` / Hồng Châu Pháp Đạt / `alias_vi_suffix`; `duc_vuong_phap_dat` / Dục Vương Pháp Đạt / `pending` | `duc_vuong_phap_dat` |
| **A026824** | 慧覺 | Tuệ Giác | `duong_chau_tue_giac` / Dương Châu Tuệ Giác / `pending`; `lang_nha_tue_giac` / Lang Nha Tuệ Giác / `pending`; `linh_thuu_tue_giac` / Linh Thứu Tuệ Giác / `pending` | `duong_chau_tue_giac` (id ASC) |
| **A030596** | 道龍 | Đạo Long | `chung_son_dao_long` / Chung Sơn Đạo Long / `pending`; `hoa_nghiem_dao_long` / Hoa Nghiêm Đạo Long / `pending` | `chung_son_dao_long` (id ASC) |
| **A043535** | 普明 | Phổ Minh | `alias_A043535` / Đẳng Giác Phổ Minh / `alias_vi_suffix`; `ky_ngan_pho_minh` / Kỳ Ngạn Phổ Minh / `pending` | `ky_ngan_pho_minh` |
| **A045400** | 智通 | Trí Thông | `ngu_dai_tri_thong` / Ngũ Đài Trí Thông / `pending`; `tho_chau_tri_thong` / Thọ Châu Trí Thông / `pending` (name_zh=智通) | `ngu_dai_tri_thong` (id ASC) |
| **A038165** | 惠芳 | Huệ Phương | `nguu_dau_hue_phuong` / Ngưu Đầu Huệ Phương / `pending` (name_zh=`慧方`); `so_an_hue_phuong` / Sở An Huệ Phương / `pending` | `nguu_dau_hue_phuong` (id ASC) |

**Lưu ý A038165**: `nguu_dau_hue_phuong.name_zh='慧方'` ≠ `people.name_zh='惠芳'` — khác chữ (慧 vs 惠), khả năng ETL typo.

---

### 2C — POSSIBLE_ID_COLLISION (11 groups)

Tên lõi **không** khớp `people.name_vi`. Khả năng 2 người khác nhau chung dila_id.

| dila_id | people.name_zh | people.name_vi | Rows và vấn đề |
|---|---|---|---|
| **A000108** | 仁勇 | Nhân Dũng | `bao_ninh_nhan_dung` (Bảo Ninh Nhân Dũng) khớp; `nguyet_chuong_tri_uyen` (Nguyệt Chưởng Trí Uyên) không khớp 仁勇 |
| **A002653** | 寶意 | Bảo Ý | `bien_dam_hieu_lieu` (Biển Đam Hiểu Liễu) không khớp; `tay_vuc_quat_da_tam_tang` (name_zh=窟多三藏) không khớp 寶意 |
| **A009478** | 隱峯 | Ẩn Phong | `ngu_dai_an_phong` khớp; `thach_cung_hue_tang` (name_zh=石鞏慧藏) là người khác (**Thạch Củng Huệ Tạng ≠ Ẩn Phong**) |
| **A014491** | 慶閑 | Khánh Nhàn | `long_khanh_khanh_nhan` khớp; `an_hoa_van_nhat` (An Hóa Văn Nhất) không khớp 慶閑 |
| **A020018** | 佛陀 | Phật Đà | `phung_tuong_phat_da` khớp; `dam_chau_dai_xuyen` (Đàm Châu Đại Xuyên) không khớp 佛陀 |
| **A020647** | 宗密 | Tông Mật | `alias_A020647` (Long Nha Tông Mật / name_zh=宗密) khớp; `thien_dong_pho_giao` (Thiên Đồng Phổ Giao) không khớp 宗密 |
| **A021350** | 覺阿 | Giác A | `giac_a` khớp; `dong_son_te_vi` (Đông Sơn Tề Vĩ) không khớp 覺阿 |
| **A024897** | 道初 | Đạo Sơ | `long_hoa_dao_so` khớp; `cuu_danh_to` (Cửu Đảnh Tố) không khớp 道初 |
| **A025951** | 華林 | Hoa Lâm | `dam_chau_hoa_lam` khớp; `kinh_trieu_thi_loi` (Kinh Triệu Thi Lợi) không khớp 華林 |
| **A038615** | 道一 | Đạo Nhất | `thai_tu_dao_nhat` khớp; `thai_tu_dong_quang` (Thái Tử Đồng Quảng) không khớp 道一 |
| **A043012** | 永泰 | Vắng Thái | `hoang_ba_vinh_thai` (永泰/Vĩnh Thái) khớp; `tue_nhat_minh` (Tuệ Nhật Minh) không khớp |
| **A008792** | 摩拏羅 | Ma Nã La | `ma_noa_la` (name_zh=摩拏羅) khớp; `ca_ty_ma_la` (Ca Tỳ Ma La) là **Tổ thứ 13** ≠ Ma Noa La **Tổ thứ 22** trong 28 Tổ — 2 người khác nhau |

_(A008792 thực chất là True ID Collision nhưng cần DILA xác nhận)_

---

### 2D — TRUE_CANONICAL_CONFLICT (3 groups)

| dila_id | vấn đề | Detail |
|---|---|---|
| **A010511** | 3 tên hoàn toàn khác nhau, 2 rows sai dila_id | Xem §5 priority detail |
| **A014617** | Cả 2 tên lõi không khớp `people.name_vi='Đạo Bình'` | `tang_chu_pho_dung` (Tạng Chủ Phổ Dung) ≠ 道平; `tri_hai_dao_binh` (Tịnh Nhân Kế Thành) ≠ 道平 |
| **A047679** | 2 tên khác nhau, insufficient DILA evidence | Xem §3 priority detail |

---

### 2E — NEEDS_MORE_EVIDENCE (2 groups)

| dila_id | people | issue | rows |
|---|---|---|---|
| **A045639** | 惠明 / Pháp Như | `phap_nhu.name_zh='法如'` ≠ `people.name_zh='惠明'` — có thể typo ETL hoặc 2 người | `phap_nhu` (Pháp Như / 法如); `van_cu_phap_nhu` (Vân Cư Pháp Như / ``) |
| **A047679** | 德宣 / Đức Tuyên | Cả 2 rows `name_zh=''`, không có DILA XML evidence | Xem §3 |

---

## SECTION 3 — Priority Decision: A047679

**Evidence state**: **INSUFFICIENT**

```
DB rows (read-only, verified):
  id=phu_son_duc_tuyen
    name_vi='Phù Sơn Đức Tuyên'  name_zh=''  status=pending
    people.name_zh='德宣'  people.name_vi='Đức Tuyên'

  id=quang_tue_duc_tuyen
    name_vi='Quảng Tuệ Đức Tuyên'  name_zh=''  status=pending
    people.name_zh='德宣'  people.name_vi='Đức Tuyên'

canonical_decision: (none)
```

**Analysis**:
- Cả 2 rows: `status=pending`, `name_zh=''`
- `people.name_zh='德宣'` khớp lõi cả 2 (Đức Tuyên = 德宣)
- Tiền tố: `Phù Sơn` ≠ `Quảng Tuệ` — 2 địa điểm/tự viện khác nhau
- Không có `canonical_decision` row
- Không có `name_zh` riêng để phân biệt từng row

**Possible interpretations**:
- A: Cùng 1 người (Đức Tuyên 德宣) trú ở 2 nơi khác nhau tại các thời điểm khác nhau
- B: 2 người khác nhau tình cờ cùng tên Đức Tuyên và cùng được DILA gán ID A047679
- C: ETL lỗi — 1 trong 2 rows sai dila_id

**Without DILA source XML**: không thể xác định.

**→ DILA EVIDENCE REQUIRED. NO MUTATION.**

---

## SECTION 4 — Priority Decision: A021395

**Evidence state**: SUFFICIENT — 1 người với 3 tiền tố tự viện

```
DB rows (read-only, verified):
  id=alias_A021395
    name_vi='Ngũ Tổ Pháp Diễn'  name_zh='法演'  status=alias_vi_suffix
    people.name_zh='法演'  people.name_vi='Pháp Diễn'

  id=bao_an_phap_dien
    name_vi='Báo Ân Pháp Diễn'  name_zh=''  status=pending
    people.name_zh='法演'  people.name_vi='Pháp Diễn'

  id=tu_to_phap_dien
    name_vi='Tứ Tổ Pháp Diễn'  name_zh=''  status=pending
    people.name_zh='法演'  people.name_vi='Pháp Diễn'

canonical_decision: (none)
```

**Analysis**:
- `people.name_zh='法演'` = `alias_A021395.name_zh='法演'` → alias row có Hán tự authoritative
- Cả 3 rows: cùng `people` record (dila_id=A021395 → people.id=A021395)
- Tất cả có lõi `Pháp Diễn` (法演)
- 3 tiền tố tự viện: Ngũ Tổ (Tứ Tổ Sơn, Hồ Bắc) / Báo Ân (chùa Báo Ân) / Tứ Tổ (chùa Tứ Tổ)
- T200 tie-break hiện tại: `pending` (rank 1) > `alias_vi_suffix` (rank 3) → `bao_an_phap_dien` hoặc `tu_to_phap_dien` thắng theo id ASC (= `bao_an_phap_dien`)

**T200 hiện tại chọn**: `bao_an_phap_dien` (Báo Ân Pháp Diễn) làm tên hiển thị.

**Vấn đề**: `alias_A021395` có `name_zh='法演'` đúng nhất, nhưng bị T200 xếp rank thấp hơn `pending`.

**Admin choices** (không tự chọn):
1. Giữ nguyên T200 behavior → `Báo Ân Pháp Diễn` hiển thị
2. Chọn `alias_A021395` (Ngũ Tổ Pháp Diễn / 法演) làm canonical → cần thêm `canonical_decision` row cho A021395
3. Tạo new canonical row trong `canonical_decision` với `canonical_name_vi='Ngũ Tổ Pháp Diễn'`
4. Xóa 2 row thừa (pending) sau khi chọn canonical

**→ ADMIN SELECT CANONICAL ROW. NO MUTATION.**

---

## SECTION 5 — Priority Decision: A010511

**Evidence state**: CONFIRMED — TRUE_CANONICAL_CONFLICT

```
DB rows (read-only, verified):
  id=dam_chau_bao_cai_uoc
    name_vi='Đàm Châu Bảo Cái Ước'  name_zh=''  status=auto_ttl
    people.name_zh='玄泰'  people.name_vi='Huyền Thái'

  id=nam_nhac_huyen_thai
    name_vi='Nam Nhạc Huyền Thái'  name_zh='畲山兒無所知年年斫斷青山'  status=pending
    people.name_zh='玄泰'  people.name_vi='Huyền Thái'

  id=the_nham_ton_tho
    name_vi='Thê Nham Tồn Thọ'  name_zh=''  status=pending
    people.name_zh='玄泰'  people.name_vi='Huyền Thái'

canonical_decision: (none)
```

**3 vấn đề phân biệt**:

**Vấn đề 1 — name_zh ETL lỗi**:
- `nam_nhac_huyen_thai.name_zh = '畲山兒無所知年年斫斷青山'`
- Đây là một câu thơ thiền (4+4+4+4 chữ), **không phải tên người**
- `people.name_zh='玄泰'` là tên đúng cho Huyền Thái

**Vấn đề 2 — dila_id sai trên 2 rows**:
- `dam_chau_bao_cai_uoc`: lõi `Bảo Cái Ước` ≠ `玄泰/Huyền Thái`
- `the_nham_ton_tho`: lõi `Tồn Thọ` ≠ `玄泰/Huyền Thái`
- Chỉ `nam_nhac_huyen_thai` có lõi `Huyền Thái` khớp `people.name_zh='玄泰'`

**Vấn đề 3 — T200 current winner**:
- T200 tie-break → `pending` wins → cả `nam_nhac_huyen_thai` lẫn `the_nham_ton_tho` đều `pending`
- id ASC: `d` < `n` < `t` → `dam_chau_bao_cai_uoc` (auto_ttl) < `nam_nhac_huyen_thai` < `the_nham_ton_tho`
- Actual winner = `nam_nhac_huyen_thai` (status=pending, id < `the_nham_ton_tho`) ✓ đúng
- Nhưng `the_nham_ton_tho` vẫn pollute DB và có thể confuse future ETL

**Proposed interpretations for Admin**:
- A: Confirm `nam_nhac_huyen_thai` (Huyền Thái) là canonical cho A010511. Sửa `name_zh` từ câu thơ sang `玄泰`. Tách `dam_chau_bao_cai_uoc` và `the_nham_ton_tho` sang dila_id riêng (hoặc xóa nếu là ETL artifact).
- B: Giữ nguyên hiện trạng (T200 chọn đúng tên nhưng DB có 3 rows nhiễu).
- C: Yêu cầu thêm evidence từ DILA trước khi quyết định.

**→ ADMIN APPROVAL REQUIRED. NO MUTATION.**

---

## SECTION 6 — 211 dila_id='' Rows

**Verified count**: 211 rows

```
dila_id = '' : 211 rows
dila_id IS NULL : 0 rows
status breakdown : pending: 211 (100%)
```

**Production impact**: NONE — runtime queries `WHERE dila_id=?` với real DILA IDs, không bao giờ truyền empty string.

**Sample (10 rows)**:
```
am_chu_ho_khe / Am Chủ Hổ Khê
bac_giang_tay_lan_nhuong / Bắc Giang Tây Lan Nhượng
bac_son_tu_kinh / Bắc Sơn Tử Kinh
bach_tao_nghiem / Bạch Tảo Nghiễm
bach_truong_duy_chanh / Bách Trượng Duy Chánh
bach_van_khong_do / Bạch Vân Không Độ
ban_giac_nha_chau / Bản Giác Nhã Châu
ban_tich_van_quan / Bản Tịch Văn Quan
banh_nhu_lam / Cư Sĩ Gián Nghị Bành Nhữ Lâm
bao_ninh_vien_co / Bảo Ninh Viên Cơ
```

**Proposed classification buckets** (chưa gán — chỉ mô tả):

| Bucket | Description | Estimate |
|---|---|---|
| **A. Non-DILA VN Monks** | Thiền sư/tăng nhân VN không có dila_id (Vô Ngôn Thông, Minh Hải Pháp Bảo, Bắc Giang…) | ~150 |
| **B. Indian Patriarchs not yet linked** | Tổ sư Ấn Độ có DILA ID nhưng ETL chưa link (Ca Tỳ Ma La, Ưu Ba Cúc Đa…) | ~15 |
| **C. Non-monk entities** | Cư sĩ, quan lại, thư ký (Bành Nhữ Lâm, Cư Sĩ Gián Nghị…) | ~30 |
| **D. Mythological/Canonical** | Phật, Bồ Tát, Tứ Thiên Vương (nếu có) | ~16 |

**Evidence needed**: từng row cần xem text/biography để classify chính xác. Không thể auto-classify.

**→ 0 MUTATION. ADMIN CLASSIFICATION REQUIRED.**

---

## SECTION 7 — Mutation Safety Verification

```
git branch:  master
HEAD:        9641215555ed78c2bdece73297a0f30a468182e3
staged:      0 (no new staged files this session)
```

**DB state post-T206**:
```
DB path:   data/lineage.db
DB size:   1,500,381,184 bytes
SHA256:    c397285c585448dc0e829ac53d84e2da3e45a1fd2168546b1aa95ca5517da135
  (different from pre-T206 50fd01fc… — expected, T206 mutated 2 rows)
canonical_decision rows: 3 (unchanged from T206)
vn_person_authority rows: 1506 (unchanged)
```

**T207 mutations**: ZERO ✓

---

## SECTION 8 — Admin Decision Form

---

### DECISION 1 — T200: 33 Duplicate DILA-ID Groups

**Status**: ADMIN CURATION REQUIRED

| Category | Count | Admin Action Required |
|---|---|---|
| CLEAR_ALIAS | 7 | Approve xóa duplicate row từng nhóm (A004981, A008471, A009319, A010534, A020120, A021291, A044094) |
| POSSIBLE_DUPLICATE | 10 | Xác nhận 1 người → approve xóa row thừa |
| POSSIBLE_ID_COLLISION | 11 | Tra DILA source → approve tách dila_id nếu 2 người (ưu tiên: A008792, A009478, A020647) |
| TRUE_CANONICAL_CONFLICT | 3 | Xem DECISION 4 (A010511), DECISION 2 (A047679), và A014617 riêng |
| NEEDS_MORE_EVIDENCE | 2 | A045639, A047679 |

**Immediate safe action**: 7 CLEAR_ALIAS rows — tên giống nhau hoàn toàn, không rủi ro nhầm người. Admin có thể approve loại bỏ duplicate rows mà không cần tra DILA.

**Affected rows (CLEAR_ALIAS)**:

| dila_id | Remove row | Keep row |
|---|---|---|
| A004981 | `phong_huyet_dien_chieu` | `nam_vien_hue_ngung` |
| A009319 | `alias_A009319` | `tung_son_pho_tich` |
| A010534 | `alias_A010534` | `vu_chau_huyen_sach` |
| A020120 | `alias_A020120` | `dam_chau_trung_van_cai` |
| A021291 | `dai_hong_to_chung` | `lao_na_tu_dang_dai_hoang` |
| A044094 | `alias_A044094` | `thieu_chau_phap_hai` |
| A008471 | `hoang_long_tri_minh` | `hoang_dinh_kien` |

**→ APPROVE / DEFER**

---

### DECISION 2 — A047679: Phù Sơn Đức Tuyên vs Quảng Tuệ Đức Tuyên

**Status**: DILA EVIDENCE REQUIRED

Rows:
```
phu_son_duc_tuyen   / Phù Sơn Đức Tuyên  / name_zh=''  / pending
quang_tue_duc_tuyen / Quảng Tuệ Đức Tuyên / name_zh='' / pending
people.name_zh=德宣 / people.name_vi=Đức Tuyên
```

No canonical_decision row. Không đủ evidence từ DB hiện tại.

**→ DILA EVIDENCE REQUIRED / DEFER đến khi có DILA XML**

---

### DECISION 3 — A021395: Ngũ Tổ / Báo Ân / Tứ Tổ Pháp Diễn

**Status**: ADMIN SELECT CANONICAL ROW

Rows:
```
alias_A021395  / Ngũ Tổ Pháp Diễn  / name_zh=法演 / alias_vi_suffix  ← has Hanzi
bao_an_phap_dien / Báo Ân Pháp Diễn / name_zh=''  / pending          ← T200 winner
tu_to_phap_dien  / Tứ Tổ Pháp Diễn  / name_zh=''  / pending
people.name_zh=法演 / people.name_vi=Pháp Diễn
```

T203 interpretation: 1 người (Pháp Diễn 法演), 3 tiền tố.

Options:
- **[3A]**: Giữ T200 behavior → tên hiển thị = `Báo Ân Pháp Diễn`
- **[3B]**: Chọn `alias_A021395` (có name_zh=法演) → thêm canonical_decision row `A021395 / Ngũ Tổ Pháp Diễn / admin_approved`
- **[3C]**: Xóa 2 pending rows, giữ alias_A021395

**→ ADMIN SELECT OPTION [3A] / [3B] / [3C]**

---

### DECISION 4 — A010511: Nam Nhạc Huyền Thái / TRUE_CANONICAL_CONFLICT

**Status**: ADMIN APPROVAL REQUIRED — có thể split sau

Rows:
```
dam_chau_bao_cai_uoc / Đàm Châu Bảo Cái Ước / name_zh=''                         / auto_ttl
nam_nhac_huyen_thai  / Nam Nhạc Huyền Thái   / name_zh=畲山兒無所知年年斫斷青山  / pending ← lõi khớp people
the_nham_ton_tho     / Thê Nham Tồn Thọ      / name_zh=''                         / pending
people.name_zh=玄泰 / people.name_vi=Huyền Thái
```

Issues requiring Admin decision:

- **[4A]**: Sửa `nam_nhac_huyen_thai.name_zh` từ câu thơ thiền → `玄泰` (hoặc xóa field)
- **[4B]**: Tách `dam_chau_bao_cai_uoc` → dila_id riêng (hoặc xóa nếu là ETL artifact)
- **[4C]**: Tách `the_nham_ton_tho` → dila_id riêng (hoặc xóa nếu là ETL artifact)
- **[4D]**: Thêm `canonical_decision` row `A010511 / Nam Nhạc Huyền Thái / admin_approved`

Admin must approve each action separately. **NO MUTATION without explicit approval.**

**→ APPROVE [4A] / [4B] / [4C] / [4D] individually, or DEFER**

---

### DECISION 5 — 211 dila_id='' Rows

**Status**: RETAIN / CLASSIFY / CLEANUP LATER

Current state: 211 rows, status=pending, no production impact.

Admin options:
- **[5A]**: Retain as-is indefinitely (safe, no action needed)
- **[5B]**: Classify row by row into buckets A/B/C/D (requires manual review)
- **[5C]**: Batch-assign bucket labels via new column `entity_category` (requires schema change — NOT in T206/T207 scope)
- **[5D]**: Delete identified ETL artifacts (requires per-row Admin approval)

**→ APPROVE [5A] (retain) / SELECT CLEANUP APPROACH for later task**

---

## SECTION 9 — Final Verdict

```
T207 VERDICT:
READY FOR ADMIN DECISION
```

**Current states** (read-only verified, 2026-10-02):

| Item | State |
|---|---|
| **T206** | CLOSED ✓ |
| **PL000000000314** | LOCKED (level=1.0, admin_approved) — DO NOT MODIFY |
| **PL000000000001** | CANDIDATE (level=0.7, auto_transliterate, vstatus=needs_review) — DO NOT MODIFY |
| **T200** | ADMIN CURATION REQUIRED — 33 groups awaiting Admin decision |
| **A047679** | UNRESOLVED — DILA evidence required |
| **A021395** | UNRESOLVED — Admin select canonical row |
| **A010511** | UNRESOLVED — Admin approval required before any mutation |
| **A014617** | UNRESOLVED — both rows don't match people.name_vi; DILA check required |
| **A008792** | UNRESOLVED — Ca Tỳ Ma La ≠ Ma Noa La; DILA check required |
| **A009478** | UNRESOLVED — Thạch Củng Huệ Tạng ≠ Ẩn Phong; DILA check required |
| **211 dila_id=''** | UNTOUCHED — pending Admin classification |
| **T165-P8** | FROZEN — DILA license required |
| **T196** | BLOCKED — Admin diagnose git handle |
| **T198** | BLOCKED — Admin approval pending |

---

*T207-ADMIN-CURATION-DECISION-GATE-01 · Read-only Decision Gate · 2026-10-02*
*0 DB mutation · 0 code change · HEAD: 9641215*
