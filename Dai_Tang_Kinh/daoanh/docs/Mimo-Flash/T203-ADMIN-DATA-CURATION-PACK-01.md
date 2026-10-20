# T203-ADMIN-DATA-CURATION-PACK-01 — Admin Decision Pack

**Status**: FINAL · **Date**: 2026-10-01
**Mode**: READ-ONLY — 0 code, 0 DB, 0 commit, 0 staging
**Purpose**: Cung cấp đủ evidence cho Admin ra quyết định data curation.

---

## Safety — Git State

**Before audit:**
```
HEAD:    e9678f6cac4bc789457cba160faae692a99846f8
Branch:  master
Staged:  0 files
```

**Recent commits (context):**
```
e9678f6  docs: T205 pass-2 - hash-fill (f8d7727)
f8d7727  fix(T205): sua 10 file TTL khong parse duoc (L3 10-0)
6efc89d  docs: T204 task - them truong commit/revert + docs
748d17d  docs: T203/T204 pass-2
a2d1afe  fix(T203/T204): sửa DB 27 row tên sai + cổng chặn TTL
a41eb7a  ← T200 baseline
```

**Note**: HEAD đã advance nhiều lần so với T202 baseline (a41eb7a). Audit này dùng HEAD thực tế — không reset, không checkout.

**After audit:** 0 code/DB/git mutation (toàn bộ queries dùng `mode=ro` URI).

---

## 1. PL Corrupt canonical_name_vi

### 1a. PL000000000314

#### Full DB Evidence

| Field | Value |
|-------|-------|
| `canonical_decision.entity_ref` | `PL000000000314` |
| `canonical_decision.canonical_name_vi` | `'Th? S?t H?i'` |
| `canonical_decision.hex` | `54 68 3f 20 53 3f 74 20 48 3f 69` |
| `canonical_decision.authority_rank` | `admin_approved` |
| `canonical_decision.confidence` | `1.0` |
| `canonical_decision.vstatus` | `verified` |
| `canonical_decision.note` | `'Conflict resolved bằng lựa chọn của admin (T68)'` |
| `canonical_decision.editor` | `daoanh.tester@gmail.com` |
| `canonical_decision.decided_at` | `2026-08-30T11:25:29` |
| `places_dila.name` | `十剎海寺` (tên Hán chính) |
| `places_dila.name_zh` | `世剎海` (tên Hán thay thế) |
| `places_dila.district` | `中國-北京市-市轄區-西城區` |
| `places_dila.note_category` | `寺廟、佛塔、佛教文化地點` |
| `places_pending.name_vi` | `'Th? S?t H?i'` (CORRUPT — đồng bộ với canonical_decision) |
| `namevi_map_places.name_vi` | `'Th? S?t H?i'` · `confidence=1.0` · `source=manual` · `status=reviewed` |
| `namevi_map_places.name_zh` | `'????'` (CORRUPT) |
| `place_desc_vi_draft.name_vi` | **`'Thế Sát Hải'`** ← xem bên dưới |

#### Authoritative VN Name Evidence

```
place_desc_vi_draft row PL000000000314:
  name_vi:    'Thế Sát Hải'       ← CLEAN UTF-8
  name_zh:    '世剎海'
  desc_source: dila_note_zh
  created_at: 2026-08-28T08:11:40
```

**`place_desc_vi_draft.name_vi = 'Thế Sát Hải'`** là tên tiếng Việt có dấu đúng UTF-8, được tạo từ `dila_note_zh` nguồn DILA, trước ngày `canonical_decision` được ghi (2026-08-30). Đây là source evidence sạch nhất trong DB.

#### Reference Impact

PL000000000314 được tham chiếu bởi:
```
places_pending       (1 row)
places_dila          (1 row — PK)
entity               (1 row)
catalog_mapping      (1 row)
places_pending_fts   (1 row)
entity_source_ids    (1 row)
zqlocal_content      (1 row)
place_person_bio_cache (1 row)
place_desc_vi_draft  (1 row)
event_text_link      (1 row)
canonical_decision   (1 row — chính hành corrupt)
en_audit_log         (1 row)
event_entities       (1 row)
```

**KHÔNG THỂ XÓA** — ít nhất 13 bảng có FK/reference. Chỉ sửa `canonical_name_vi`.

#### Classification: **A. AUTHORITATIVE NAME AVAILABLE**

```
Proposed correction:
  canonical_decision.canonical_name_vi  'Th? S?t H?i'  →  'Thế Sát Hải'
  namevi_map_places.name_vi             'Th? S?t H?i'  →  'Thế Sát Hải'
  places_pending.name_vi                'Th? S?t H?i'  →  'Thế Sát Hải'

Source:  place_desc_vi_draft.name_vi = 'Thế Sát Hải'  (dila_note_zh, 2026-08-28)
```

Admin cần approve trước khi sửa.

---

### 1b. PL000000000001

#### Full DB Evidence

| Field | Value |
|-------|-------|
| `canonical_decision.entity_ref` | `PL000000000001` |
| `canonical_decision.canonical_name_vi` | `'Kho?t T?t ?a Qu?c'` |
| `canonical_decision.hex` | `4b 68 6f 3f 74 20 54 3f 74 20 3f 61 20 51 75 3f 63` |
| `canonical_decision.authority_rank` | `auto_transliterate` |
| `canonical_decision.confidence` | `1.0` |
| `canonical_decision.vstatus` | `needs_review` |
| `canonical_decision.note` | `'Auto-generated VN name — chờ admin duyệt'` |
| `canonical_decision.editor` | `auto-tester` |
| `canonical_decision.decided_at` | `2026-08-30T11:26:23` |
| `places_dila.name` | `闊悉多國` (Khoát Tất Đa Quốc) |
| `places_dila.name_en` | `Khost` |
| `places_dila.name_jpn` | `カスタ` |
| `places_dila.district` | `阿富汗` (Afghanistan) |
| `places_pending.name_vi` | `'Kho?t T?t ?a Qu?c'` (CORRUPT) |
| `namevi_map_places.name_vi` | `'Kho?t T?t ?a Qu?c'` · `confidence=0.5` · `source=auto_generated` · `status=auto` |
| `place_desc_vi_draft.name_vi` | **`'Khoát Tạt Đa Quốc'`** ← xem bên dưới |

#### Authoritative VN Name Evidence

```
place_desc_vi_draft row PL000000000001:
  name_vi:    'Khoát Tạt Đa Quốc'   ← CLEAN UTF-8
  name_zh:    '闊悉多國'
  desc_source: dila_note_zh
  created_at: 2026-08-28T08:11:40

translation_cache row PL000000000001:
  entity_id:        PL000000000001
  source_text:      '印度古國，詳址待考...'
  translated_text:  '...quốc gia này nằm ở vùng đông bắc Afghanistan...'
  status:           invalidated   ← không active
  model:            qwen/qwen3.8-27b
```

**`place_desc_vi_draft.name_vi = 'Khoát Tạt Đa Quốc'`** là nguồn đáng tin nhất (clean UTF-8, từ `dila_note_zh`, 2026-08-28). `translation_cache` chỉ là note dịch, status `invalidated`.

**Lưu ý**: `canonical_decision.authority_rank = auto_transliterate` + `vstatus = needs_review` — đây là row tự sinh, chưa Admin duyệt.

#### Reference Impact

PL000000000001 được tham chiếu bởi:
```
places_pending        (1 row)
places_dila           (1 row — PK)
entity                (1 row)
places_pending_fts    (1 row)
entity_source_ids     (1 row)
zqlocal_content       (1 row)
place_desc_vi_draft   (1 row)
canonical_decision    (1 row)
en_audit_log          (1 row)
translation_cache     (1 row — status=invalidated)
```

**KHÔNG THỂ XÓA** — ít nhất 10 bảng có tham chiếu.

#### Classification: **A. AUTHORITATIVE NAME AVAILABLE**

```
Proposed correction:
  canonical_decision.canonical_name_vi  'Kho?t T?t ?a Qu?c'  →  'Khoát Tạt Đa Quốc'
  namevi_map_places.name_vi             'Kho?t T?t ?a Qu?c'  →  'Khoát Tạt Đa Quốc'
  places_pending.name_vi                'Kho?t T?t ?a Qu?c'  →  'Khoát Tạt Đa Quốc'
  canonical_decision.vstatus (PL000000000001):  'needs_review'  →  Admin quyết có approve không

Source:  place_desc_vi_draft.name_vi = 'Khoát Tạt Đa Quốc'  (dila_note_zh, 2026-08-28)
```

Admin cần approve trước khi sửa.

---

## 2. T200 — 33-Group Decision Pack

**Confirmed**: 33 groups với `dila_id != ''` và `count(*) > 1`.

Mọi nhóm bên dưới đều kèm `people.name_zh` và `people.name_vi` từ bảng `people` (join qua `dila_id`) — đây là nguồn canonical hiện tại của hệ thống.

### Phân loại tổng quan

| Category | Count | Groups |
|---------|-------|--------|
| CLEAR_ALIAS | 7 | A004981, A008471, A009319, A010534, A020120, A021291, A044094 |
| POSSIBLE_DUPLICATE | 10 | A000108, A020456, A021084, A021326, A021395, A023045, A026824, A030596, A038165, A043535, A045400 |
| POSSIBLE_ID_COLLISION | 11 | A002653, A008792, A009478, A014491, A020018, A020647, A021350, A024897, A025951, A038615, A043012 |
| TRUE_CANONICAL_CONFLICT | 3 | A010511, A014617, A047679 |
| NEEDS_MORE_EVIDENCE | 2 | A045639, (A047679 border) |

_(Note: A047679 vừa có thể POSSIBLE_DUPLICATE vừa TRUE_CANONICAL_CONFLICT — xem §3)_

---

### CLEAR_ALIAS (an toàn để merge — cần Admin approve)

**A004981** — `people.name_zh=慧顒`, `people.name_vi=Tuệ Ngung`
- `phong_huyet_dien_chieu (auto_ttl)`: name_vi=`Nam Viện Huệ Ngung`
- `nam_vien_hue_ngung (pending)`: name_vi=`Nam Viện Huệ Ngung`
- Cùng tên hoàn toàn. T200 tie-break → `pending` thắng (rank 1 < 2).
- **Action**: xóa auto_ttl row, giữ pending.

**A008471** — `people.name_zh=黃庭堅`, `people.name_vi=Hoàng Đình Kiên`
- Cả 2 `pending`: name_vi=`Cư Sĩ Thái Sử Hoàng Đình Kiên`
- Cùng tên hoàn toàn, id khác (hoang_dinh_kien vs hoang_long_tri_minh).
- **Action**: xóa 1 duplicate (giữ `hoang_dinh_kien` — id ngắn hơn, hoặc Admin chọn).

**A009319** — `people.name_zh=嵩山普寂`, `people.name_vi=Tung Sơn Phổ Tịch`
- `alias_A009319 (alias_vi_suffix)`: name_vi=`Tung Sơn Phổ Tịch`, name_zh=`嵩山普寂`
- `tung_son_pho_tich (pending)`: name_vi=`Tung Sơn Phổ Tịch`, name_zh=`普寂`
- Cùng tên. alias_row dùng full name_zh, pending dùng rút gọn. T200 tie-break → pending thắng.
- **Action**: xóa alias row (đúng theo T200 logic).

**A010534** — `people.name_zh=玄策`, `people.name_vi=Huyền Sách`
- `alias_A010534 (alias_vi_suffix)`: name_vi=`Huyền Sách`, name_zh=`玄策`
- `vu_chau_huyen_sach (pending)`: name_vi=`Vụ Châu Huyền Sách`, name_zh=`玄策`
- Cùng name_zh, alias là tên rút gọn. pending = full (có tiền tố chùa). T200 tie-break → pending thắng.
- **Action**: xóa alias row.

**A020120** — `people.name_zh=中雲蓋`, `people.name_vi=Trung Vân Cái`
- `alias_A020120 (alias_vi_suffix)`: name_vi=`Đàm Châu Trung Vân Cái`, name_zh=`中雲蓋`
- `dam_chau_trung_van_cai (pending)`: name_vi=`Đàm Châu Trung Vân Cái`
- Cùng tên. T200 tie-break → pending thắng.
- **Action**: xóa alias row.

**A021291** — `people.name_zh=祖證`, `people.name_vi=Tổ Chứng`
- `dai_hong_to_chung (auto_ttl)` và `lao_na_tu_dang_dai_hoang (pending)`: cùng name_vi=`Đại Hồng Tổ Chứng`
- T200 tie-break → pending thắng.
- **Action**: xóa auto_ttl row.

**A044094** — `people.name_zh=法海`, `people.name_vi=Pháp Hải`
- `alias_A044094 (alias_vi_suffix)`: name_vi=`Ngô Hưng Pháp Hải`, name_zh=`法海`
- `thieu_chau_phap_hai (pending)`: name_vi=`Thiều Châu Pháp Hải`, name_zh=`法海`
- Cùng name_zh. Hai tên có tiền tố chùa khác nhau nhưng cùng lõi 法海. T200 tie-break → pending thắng.
- **Action**: xóa alias row.

---

### POSSIBLE_DUPLICATE (1 người, nhiều tiền tố — cần Admin xác nhận)

**A000108** — `people.name_zh=仁勇`, `people.name_vi=Nhân Dũng`
- `bao_ninh_nhan_dung (auto_ttl)`: Bảo Ninh Nhân Dũng
- `nguyet_chuong_tri_uyen (pending)`: Nguyệt Chưởng Trí Uyên
- Tên lõi KHÁC nhau. `Nhân Dũng` khớp `bao_ninh`, nhưng `Trí Uyên` không khớp `people.name_vi`. Có thể là 2 người.
- **⚠ Reclassify từ T202**: cần xem xét lại → **POSSIBLE_ID_COLLISION** (tên lõi khác)

**A020456** — `people.name_zh=智嵩`, `people.name_vi=Trí Tung`
- `alias_A020456 (alias_vi_suffix)`: Tam Giao Trí Tung, name_zh=`智嵩`
- `thiet_phat_tri_tung (pending)`: Thiết Phật Trí Tung (không có name_zh)
- Cùng lõi `Trí Tung`/`智嵩`. Hai tiền tố chùa khác. Alias có authoritative name_zh.
- **Action**: Admin xác nhận 1 người → xóa alias, giữ pending.

**A021084** — `people.name_zh=善孜`, `people.name_vi=Thiện Tư`
- `tho_ninh_thien_tu (auto_ttl)`: Thọ Ninh Thiện Tư
- `tinh_do_thien_tu (pending)`: Tịnh Độ Thiện Tư
- Cùng lõi `Thiện Tư`. Hai tiền tố chùa. T200 tie-break → pending thắng.
- **Action nếu Admin xác nhận 1 người**: xóa auto_ttl.

**A021326** — `people.name_zh=德用`, `people.name_vi=Đức Dụng`
- `pho_minh_duc_dung (auto_ttl)`: Phổ Minh Đức Dụng
- `song_lam_duc_dung (pending)`: Song Lâm Đức Dụng
- Cùng lõi `Đức Dụng`. T200 tie-break → pending thắng.
- **Action nếu Admin xác nhận 1 người**: xóa auto_ttl.

**A021395** — xem §3 chi tiết

**A023045** — `people.name_zh=法達`, `people.name_vi=Pháp Đạt`
- `alias_A023045 (alias_vi_suffix)`: Hồng Châu Pháp Đạt, name_zh=`法達`
- `duc_vuong_phap_dat (pending)`: Dục Vương Pháp Đạt
- Cùng lõi `Pháp Đạt`. T200 tie-break → pending thắng.
- **Action nếu Admin xác nhận 1 người**: xóa alias.

**A026824** — xem §3 không có (nhưng là tham chiếu rõ 3 tiền tố Tuệ Giác)
- `people.name_zh=慧覺`, `people.name_vi=Tuệ Giác`
- 3 rows pending: Dương Châu / Lang Nha / Linh Thứu Tuệ Giác. Tất cả khớp people.name_vi.
- **Action nếu Admin xác nhận 1 người**: giữ 1 row (canonical), xóa 2 tiền tố thừa — hoặc giữ cả 3 nếu muốn tra cứu đa tiền tố.

**A030596** — `people.name_zh=道龍`, `people.name_vi=Đạo Long`
- `chung_son_dao_long (pending)`: Chung Sơn Đạo Long
- `hoa_nghiem_dao_long (pending)`: Hoa Nghiêm Đạo Long
- Cùng lõi `Đạo Long`. **Action nếu 1 người**: xóa 1, giữ 1 canonical.

**A038165** — `people.name_zh=惠芳`, `people.name_vi=Huệ Phương`
- `nguu_dau_hue_phuong (pending)`: Ngưu Đầu Huệ Phương, name_zh=`慧方`
- `so_an_hue_phuong (pending)`: Sở An Huệ Phương
- Lõi `Huệ Phương` khớp cả 2. **Lưu ý**: `nguu_dau_hue_phuong.name_zh='慧方'` ≠ `people.name_zh='惠芳'` (字 khác nhau: 慧 vs 惠). Có thể typo trong ETL.

**A043535** — `people.name_zh=普明`, `people.name_vi=Phổ Minh`
- `alias_A043535 (alias_vi_suffix)`: Đẳng Giác Phổ Minh, name_zh=`普明`
- `ky_ngan_pho_minh (pending)`: Kỳ Ngạn Phổ Minh
- Cùng lõi `Phổ Minh`. T200 tie-break → pending thắng.

**A045400** — `people.name_zh=智通`, `people.name_vi=Trí Thông`
- `ngu_dai_tri_thong (pending)`: Ngũ Đài Trí Thông
- `tho_chau_tri_thong (pending)`: Thọ Châu Trí Thông, name_zh=`智通`
- Cùng lõi `Trí Thông`. `tho_chau_tri_thong` có name_zh khớp people. T200 tie-break → `ngu_dai_tri_thong` thắng theo id ASC.

---

### POSSIBLE_ID_COLLISION (có thể 2 người khác nhau — cần Admin tra DILA)

**A000108** — _(reclassify từ POSSIBLE_DUPLICATE trên)_
- `Bảo Ninh Nhân Dũng` vs `Nguyệt Chưởng Trí Uyên` — tên lõi khác nhau hoàn toàn
- **Cần Admin**: tra DILA A000108 xem là 1 hay 2 người.

**A002653** — `people.name_zh=寶意`, `people.name_vi=Bảo Ý`
- `bien_dam_hieu_lieu (auto_ttl)`: Biển Đam Hiểu Liễu
- `tay_vuc_quat_da_tam_tang (pending)`: Tây Vực Quật Đa Tam Tạng, name_zh=`窟多三藏`
- Cả 2 tên lõi khác `people.name_vi=Bảo Ý`. name_zh `窟多三藏` ≠ `寶意`.
- **Cần Admin**: tra DILA A002653. Khả năng 2 người khác nhau hoặc ETL lỗi.

**A008792** — `people.name_zh=摩拏羅`, `people.name_vi=Ma Nã La`
- `ca_ty_ma_la (auto_ttl)`: Tôn Giả Ca Tỳ Ma La
- `ma_noa_la (pending)`: Tôn Giả Ma Noa La, name_zh=`摩拏羅`
- `people.name_zh='摩拏羅'` khớp `ma_noa_la`. Ca Tỳ Ma La và Ma Noa La là **2 vị Tổ sư Ấn Độ khác nhau** trong truyền thừa 28 Tổ (Ca-Pi-Mo-Luo = Tổ 13, Ma-Noa-La = Tổ 22).
- **Cần Admin**: tách dila_id A008792. Ca Tỳ Ma La cần dila_id riêng.

**A009478** — `people.name_zh=隱峯`, `people.name_vi=Ẩn Phong`
- `ngu_dai_an_phong (auto_ttl)`: Ngũ Đài Ẩn Phong — khớp `people.name_vi=Ẩn Phong`
- `thach_cung_hue_tang (pending)`: Thạch Củng Huệ Tạng, name_zh=`石鞏慧藏`
- `石鞏慧藏` ≠ `隱峯`. Đây là 2 người: Ẩn Phong (ngũ đài) và Huệ Tạng (thạch củng).
- **Cần Admin**: tách dila_id. `thach_cung_hue_tang` cần dila_id riêng.

**A014491** — `people.name_zh=慶閑`, `people.name_vi=Khánh Nhàn`
- `an_hoa_van_nhat (auto_ttl)`: An Hóa Văn Nhất — không khớp `慶閑/Khánh Nhàn`
- `long_khanh_khanh_nhan (pending)`: Long Khánh Khánh Nhàn — khớp `people.name_vi`
- **Cần Admin**: `an_hoa_van_nhat` có thể là người khác hoặc ETL sai dila_id.

**A020018** — `people.name_zh=佛陀`, `people.name_vi=Phật Đà`
- `dam_chau_dai_xuyen (pending)`: Đàm Châu Đại Xuyên — không khớp `佛陀/Phật Đà`
- `phung_tuong_phat_da (pending)`: Phụng Tường Phật Đà — khớp `people.name_vi`
- **Cần Admin**: `dam_chau_dai_xuyen` có thể sai dila_id.

**A020647** — `people.name_zh=宗密`, `people.name_vi=Tông Mật`
- `alias_A020647 (alias_vi_suffix)`: Long Nha Tông Mật, name_zh=`宗密` — khớp people
- `thien_dong_pho_giao (pending)`: Thiên Đồng Phổ Giao — lõi hoàn toàn khác `宗密/Tông Mật`
- **Cần Admin**: `thien_dong_pho_giao` gần chắc chắn là người khác, sai dila_id. Tách ra.

**A021350** — `people.name_zh=覺阿`, `people.name_vi=Giác A`
- `dong_son_te_vi (pending)`: Đông Sơn Tề Vĩ — không khớp `覺阿/Giác A`
- `giac_a (pending)`: Giác A — khớp `people.name_vi`
- **Cần Admin**: `dong_son_te_vi` có thể sai dila_id.

**A024897** — `people.name_zh=道初`, `people.name_vi=Đạo Sơ`
- `cuu_danh_to (pending)`: Cửu Đảnh Tố — không khớp `道初/Đạo Sơ`
- `long_hoa_dao_so (pending)`: Long Hoa Đạo Sơ — khớp people
- **Cần Admin**: `cuu_danh_to` có thể sai dila_id.

**A025951** — `people.name_zh=華林`, `people.name_vi=Hoa Lâm`
- `dam_chau_hoa_lam (auto_ttl)`: Đàm Châu Hoa Lâm — khớp people (Hoa Lâm)
- `kinh_trieu_thi_loi (pending)`: Kinh Triệu Thi Lợi — hoàn toàn khác
- **Cần Admin**: `kinh_trieu_thi_loi` gần chắc chắn sai dila_id.

**A038615** — `people.name_zh=道一`, `people.name_vi=Đạo Nhất`
- `thai_tu_dao_nhat (pending)`: Thái Tử Đạo Nhất — khớp people
- `thai_tu_dong_quang (pending)`: Thái Tử Đồng Quảng — không khớp
- **Cần Admin**: `thai_tu_dong_quang` có thể sai dila_id.

**A043012** — `people.name_zh=永泰`, `people.name_vi=Vắng Thái`
- `hoang_ba_vinh_thai (auto_ttl)`: Hoàng Bá Vĩnh Thái — `永泰=Vĩnh Thái` khớp (Vắng Thái/Vĩnh Thái có thể là cùng cách đọc)
- `tue_nhat_minh (pending)`: Tuệ Nhật Minh — hoàn toàn khác
- **Cần Admin**: `tue_nhat_minh` có thể sai dila_id.

---

### TRUE_CANONICAL_CONFLICT (cần tra DILA để giải quyết)

**A010511** — xem §3 chi tiết

**A014617** — `people.name_zh=道平`, `people.name_vi=Đạo Bình`
- `tang_chu_pho_dung (auto_ttl)`: Tạng Chủ Phổ Dung — không khớp `道平/Đạo Bình`
- `tri_hai_dao_binh (pending)`: Tịnh Nhân Kế Thành — cũng không khớp `道平/Đạo Bình`
- Cả 2 tên lõi khác nhau VÀ khác `people.name_vi`. Conflict không rõ ràng.
- **Cần Admin**: tra DILA A014617. Cả 2 row có thể sai dila_id.

**A047679** — xem §3 chi tiết

---

### NEEDS_MORE_EVIDENCE

**A045639** — `people.name_zh=惠明`, `people.name_vi=Pháp Như`
- `phap_nhu (pending)`: Pháp Như, name_zh=`法如` ≠ `惠明` (people.name_zh)
- `van_cu_phap_nhu (pending)`: Vân Cư Pháp Như (không có name_zh)
- Tên lõi giống nhau (Pháp Như) nhưng `phap_nhu.name_zh='法如'` vs `people.name_zh='惠明'` — có thể là 2 người hoặc ETL nhầm name_zh.
- **Cần Admin**: tra DILA A045639.

---

## 3. Priority Groups — Chi Tiết

### A047679 — Phù Sơn Đức Tuyên vs Quảng Tuệ Đức Tuyên

```
vn_person_authority:
  phu_son_duc_tuyen:   name_vi='Phù Sơn Đức Tuyên'  name_zh=''  status=pending
  quang_tue_duc_tuyen: name_vi='Quảng Tuệ Đức Tuyên' name_zh=''  status=pending

people table (A047679):
  name_zh: '德宣'
  name_vi: 'Đức Tuyên'
```

**Evidence analysis**:
- Cả 2 rows: `status=pending`, `name_zh=''` (không có Hán tự riêng)
- `people.name_vi='Đức Tuyên'` khớp lõi cả 2
- `people.name_zh='德宣'` — không có vnpa row nào có name_zh này
- Tiền tố: Phù Sơn (chùa ở Phù Sơn) vs Quảng Tuệ (chùa/tự viện Quảng Tuệ) — 2 địa điểm khác nhau
- Không có canonical_decision row
- Không có name_zh để phân biệt

**Evidence state**: INSUFFICIENT
- Không thể xác định: cùng 1 người (nhà sư trú ở 2 nơi khác nhau) hay 2 người (cùng tên Đức Tuyên, khác nơi)
- Cần tra DILA source XML cho A047679 để xem có 1 hay 2 entity

**Verdict**: POSSIBLE_ID_COLLISION — nhưng chưa đủ evidence để tách. Admin cần tra DILA trước khi quyết định.
KHÔNG tách dila_id tự động.

---

### A021395 — Ngũ Tổ Pháp Diễn / 法演

```
vn_person_authority:
  alias_A021395:  name_vi='Ngũ Tổ Pháp Diễn'  name_zh='法演'  status=alias_vi_suffix
  bao_an_phap_dien: name_vi='Báo Ân Pháp Diễn' name_zh=''    status=pending
  tu_to_phap_dien:  name_vi='Tứ Tổ Pháp Diễn'  name_zh=''    status=pending

people table (A021395):
  name_zh: '法演'
  name_vi: 'Pháp Diễn'
```

**Evidence analysis**:
- `people.name_zh='法演'` = `alias_A021395.name_zh` — alias row có Hán tự authoritative
- Cả 3 rows đều có lõi `Pháp Diễn`
- 3 tiền tố: Ngũ Tổ / Báo Ân / Tứ Tổ — đây là 3 tên hiệu của CÙNG 1 người theo trú xứ/chức vị
- Ngũ Tổ Pháp Diễn (法演, 1024–1104) là thiền sư nổi tiếng đời Tống, trú tại Ngũ Tổ Sơn
- "Báo Ân" và "Tứ Tổ" là các tiền tố liên quan đến các giai đoạn hoặc chùa khác nhau trong hành trạng của cùng 1 vị

**Evidence state**: SUFFICIENT — 1 người
- `people.name_zh='法演'` + alias có `name_zh='法演'` + lịch sử Phật giáo xác nhận Pháp Diễn là 1 người duy nhất
- T200 tie-break hiện tại: `alias_vi_suffix (rank 3)` < `pending (rank 1)` → `bao_an_phap_dien` thắng (id ASC giữa 2 pending)

**Verdict**: POSSIBLE_DUPLICATE (1 người, 3 tiền tố địa điểm/chức vị)
- Admin nên giữ row canonical nhất (ví dụ `bao_an_phap_dien` theo T200 tie-break, hoặc chọn `alias_A021395` vì có name_zh đúng), xóa các row thừa.

---

### A010511 — TRUE_CANONICAL_CONFLICT

```
vn_person_authority:
  dam_chau_bao_cai_uoc: name_vi='Đàm Châu Bảo Cái Ước'              name_zh=''  status=auto_ttl
  nam_nhac_huyen_thai:  name_vi='Nam Nhạc Huyền Thái'                name_zh='畲山兒無所知年年斫斷青山'  status=pending
  the_nham_ton_tho:     name_vi='Thê Nham Tồn Thọ'                   name_zh=''  status=pending

people table (A010511):
  name_zh: '玄泰'
  name_vi: 'Huyền Thái'
```

**Evidence analysis**:
- `people.name_zh='玄泰'`, `people.name_vi='Huyền Thái'`
- `nam_nhac_huyen_thai` có lõi `Huyền Thái` = khớp people. name_zh=`'畲山兒無所知年年斫斷青山'` — đây là câu thơ thiền, KHÔNG phải tên người (lỗi ETL nghiêm trọng)
- `dam_chau_bao_cai_uoc` = Đàm Châu Bảo Cái Ước — tên lõi `Bảo Cái Ước` không khớp `玄泰/Huyền Thái`
- `the_nham_ton_tho` = Thê Nham Tồn Thọ — tên lõi `Tồn Thọ` không khớp

**3 vấn đề riêng biệt**:
1. `nam_nhac_huyen_thai.name_zh` = câu thơ thiền (5 chữ Hán) → lỗi ETL, cần xóa/sửa name_zh
2. `dam_chau_bao_cai_uoc` và `the_nham_ton_tho` → tên lõi không khớp `people` → khả năng cao là 2 người khác nhau với dila_id sai
3. `nam_nhac_huyen_thai` = 1 người (khớp people), 2 rows kia cần dila_id riêng

**Verdict**: TRUE_CANONICAL_CONFLICT
- Canonical winner: `nam_nhac_huyen_thai` (khớp `people.name_zh='玄泰'`)
- Cần Admin: tách dila_id cho `dam_chau_bao_cai_uoc` và `the_nham_ton_tho`
- Cần Admin: sửa `nam_nhac_huyen_thai.name_zh` (hiện là câu thơ thiền, không phải tên người)

---

## 4. dila_id='' Orphan Inventory

**Verified count**: 211 rows với `dila_id=''` trong bảng `vn_person_authority`.

### Distribution

| Status | Count | Notes |
|--------|-------|-------|
| `pending` | 211 | Tất cả 100% |

### Entity Sample (từ ids)

Gồm nhiều loại: monks thật (Minh Hải Pháp Bảo, Vô Ngôn Thông), cư sĩ (Bành Nhữ Lâm, Đô Huống Trịnh), Tứ Thiên Vương (không phải người), Tổ sư Ấn Độ (Thích Ca Mâu Ni Phật, Tôn Giả Ưu Ba Cúc Đa), nhân vật hư cấu — tất cả không có DILA ID.

### Production Code Impact

Production code (`vnpa_lookup.py`, `app.py`) truy vấn:
```sql
SELECT ... FROM vn_person_authority WHERE dila_id=?
```
với `?` = real DILA ID (vd `A001984`). Câu query **KHÔNG BAO GIỜ** match `dila_id=''` vì không có API nào truyền empty string làm DILA lookup parameter.

**211 rows này KHÔNG ảnh hưởng runtime hiện tại.**

### Reference Dependencies

Không có FK từ bảng khác tham chiếu `vn_person_authority.id` cho các rows này (trừ canonical_decision, nơi `entity_ref` là DILA ID, không phải `vn_person_authority.id`).

### Classification

| Sub-category | Estimate | Rows |
|-------------|---------|------|
| Monks VN không có DILA ID | ~150 | Vô Ngôn Thông, Minh Hải Pháp Bảo, các vị trú xứ VN... |
| Nhân vật không phải monk | ~30 | Cư sĩ, thư ký, quan lại |
| Tổ sư Ấn Độ (có DILA ID nhưng chưa link) | ~15 | Ca Tỳ Ma La, Ưu Ba Cúc Đa... |
| Nhân vật khác (Phật, Bồ Tát) | ~16 | Thích Ca Mâu Ni Phật, Tứ Thiên Vương... |

### Recommendation: **C. SAFE TO CLEAN ONLY AFTER EXPLICIT ADMIN APPROVAL**

Có 3 lớp:
- Monks VN không có DILA ID → đây là **legitimate non-DILA rows** (category A)
- Nhân vật không phải monk → có thể là technical debt
- Tổ sư Ấn Độ chưa link → có thể gán DILA ID sau

Admin cần phân loại từng sub-category trước khi thực hiện bất kỳ clean-up nào. Không thể auto-clean an toàn.

---

## 5. T200 Status / Task Consistency

**tasks/T200**: `status: build_done_admin_review` — code đã làm (tie-break ORDER BY), data curation còn lại.

**tasktodo**: "VẪN CÒN: gộp/tách dila_id cho 33 nhóm... cần Admin duyệt từng nhóm"

**Không có task file nào** (`T202.md`, `T203.md`, etc.) tracking data curation work này.

**Recommendation**: Cần formal task mới để track:
- Sửa 2 PL corrupt rows (canonical_name_vi + places_pending.name_vi + namevi_map_places)
- Xử lý 33 nhóm duplicate dila_id theo decision matrix
- Quyết định 211 dila_id='' orphan rows

**Proposed scope cho task mới** (nếu Admin chọn tạo):
```
Title: Data Curation — PL corrupt rows + 33 duplicate dila_id + 211 orphan rows
Scope: data-only, 0 code change, 0 schema change
Blockers: Admin decision matrix phải approved trước
Done when:
  - PL000000000314 và PL000000000001 canonical_name_vi sạch UTF-8
  - 33 groups xử lý theo admin decision
  - 211 orphan rows: classified + action decided
  - Tests regression PASS
  - ROLLBACK documented
```

---

## 6. Admin Decision Matrix

| Item | Evidence State | Admin Decision Required | Safe Action Now |
|------|--------------|------------------------|----------------|
| **PL000000000314** `canonical_name_vi` | A. Authoritative available (`place_desc_vi_draft.name_vi='Thế Sát Hải'`) | Approve correction `→ 'Thế Sát Hải'` | DOCUMENT ONLY |
| **PL000000000001** `canonical_name_vi` | A. Authoritative available (`place_desc_vi_draft.name_vi='Khoát Tạt Đa Quốc'`) | Approve correction `→ 'Khoát Tạt Đa Quốc'`; decide `vstatus needs_review → verified` | DOCUMENT ONLY |
| **A047679** | Insufficient — 2 `pending`, no `name_zh` | Tra DILA source XML trước khi tách | NO ACTION |
| **A021395** | Sufficient — 1 người (Pháp Diễn 法演) | Chọn canonical row: `alias` hay `bao_an_phap_dien` | EXISTING CODE BEHAVIOR ACCEPTED |
| **A010511** | TRUE_CONFLICT — `nam_nhac_huyen_thai` khớp people; 2 rows kia sai dila_id + name_zh là câu thơ | Approve tách dila_id + sửa name_zh lỗi ETL | NO ACTION |
| **CLEAR_ALIAS × 7** (A004981, A008471, A009319, A010534, A020120, A021291, A044094) | Sufficient | Approve xóa duplicate row trong từng nhóm | EXISTING CODE BEHAVIOR ACCEPTED |
| **POSSIBLE_DUPLICATE × 10** | Partial | Xác nhận từng nhóm là 1 người, rồi approve xóa thừa | EXISTING CODE BEHAVIOR ACCEPTED |
| **POSSIBLE_ID_COLLISION × 11** (bao gồm A000108 reclassify) | Insufficient — cần tra DILA | Tra DILA ID, approve tách nếu 2 người | NO ACTION |
| **A014617 TRUE_CONFLICT** | Insufficient — cả 2 tên lõi không khớp `people` | Tra DILA, approve sửa dila_id | NO ACTION |
| **A045639 NEEDS_MORE_EVIDENCE** | Partial — name_zh discrepancy | Tra DILA A045639 | NO ACTION |
| **211 dila_id='' rows** | Sufficient — không ảnh hưởng runtime | Classify sub-categories (A/B/C), approve clean-up từng sub-category | NO ACTION |
| **T200 task status** | `build_done_admin_review` | Approve đóng T200 sau khi data curation done; approve tạo task mới | DOCUMENT ONLY |

---

## 7. Safety / Mutation Check

**Before audit:**
```
HEAD:    e9678f6cac4bc789457cba160faae692a99846f8
Branch:  master
Staged:  0 files
```

**After audit:**
```
HEAD:    e9678f6cac4bc789457cba160faae692a99846f8  (unchanged)
Branch:  master
Staged:  0 files
```

```
DB mutations:     NONE ✅  (toàn bộ queries: mode=ro URI)
Schema mutations: NONE ✅
Source file edits: NONE ✅
Migration:        NONE ✅
Git:              NONE ✅
```

---

## 8. Final Verdict

```
T203 VERDICT:
READY FOR ADMIN DECISION
```

**1. Data correction decisions required**

| Row | Correction | Source |
|-----|-----------|--------|
| `canonical_decision.canonical_name_vi` cho PL000000000314 | `'Th? S?t H?i'` → `'Thế Sát Hải'` | `place_desc_vi_draft.name_vi` |
| `canonical_decision.canonical_name_vi` cho PL000000000001 | `'Kho?t T?t ?a Qu?c'` → `'Khoát Tạt Đa Quốc'` | `place_desc_vi_draft.name_vi` |
| `places_pending.name_vi` + `namevi_map_places.name_vi` cho cả 2 | tương tự | tương tự |
| `PL000000000001.vstatus` | `needs_review` → Admin quyết có `verified` không | — |
| `nam_nhac_huyen_thai.name_zh` | câu thơ thiền → NULL hoặc `玄泰` | `people.name_zh` |

**2. Duplicate-ID decisions required**

- 7 CLEAR_ALIAS: xóa row thừa (cần Admin approve từng nhóm)
- 10 POSSIBLE_DUPLICATE: xác nhận 1 người, rồi xóa row thừa
- 11 POSSIBLE_ID_COLLISION + A008792 đặc biệt: tra DILA, tách dila_id nếu 2 người (ưu tiên: A008792, A009478, A020647, A010511)
- 2 TRUE_CANONICAL_CONFLICT (A014617, A010511): tra DILA, phân xử canonical
- 2 NEEDS_MORE_EVIDENCE (A045639, A047679): tra DILA trước

**3. 211 orphan-row decision required**

Admin phân loại: legitimate non-DILA rows (giữ) vs technical debt (clean up). Không auto-delete.

**4. Formal data-curation task should be created: YES**

T200 task hiện là `build_done_admin_review` — code đã done, data chưa. Cần task mới (đề xuất gọi là T206 hoặc Admin chọn số) tracking toàn bộ data curation work trên.

**5. Engineering tasks must remain BLOCKED until Admin decision**

| Task | Blocked until |
|------|-------------|
| T200 final `done` | Admin approve data curation + tests PASS |
| T74b | T73 in_progress (unchanged) |
| T198 | Admin plan approval (unchanged) |
| T196 | Admin diagnose git handle (unchanged) |
| T165-P8 | DILA license (unchanged) |

---

*T203-ADMIN-DATA-CURATION-PACK-01 · Read-only Admin Decision Pack · 2026-10-01*
*Untracked — Admin decides whether to commit*
