# T202-POST-REVIEW-02 — Revision của T202-POST-REVIEW-01 (2026-10-10)

**Status**: CURRENT · **Date**: 2026-10-10 · **Task**: `tasks/T271-t202-post-review-revision.md`
**Mode**: READ-ONLY — 0 code, 0 DB mutation, 0 schema. Bằng chứng: `data/lineage.db` (mode=ro) + git history + code.

**Thay thế**: `docs/Mimo-Flash/X-T202-POST-REVIEW-01.md` (2026-10-01) — kiểm lại toàn bộ claim của bản 01 so với thực tế hôm nay.

---

## 0. Verdict tổng quan

| Claim bản 01 | Kết quả | Bằng chứng |
|---|---|---|
| §A Git baseline discrepancy (+2 commits: a2d1afe/748d17d/6efc89d) | ✅ ĐÚNG | `git log`: commits tồn tại đúng thứ tự; a41eb7a=T200 pass-2 |
| §B T201 root-cause `pd.dila_id`→`pd.id` | ✅ ĐÚNG | `canonical_lock.py:878,901-911` |
| §B `is_valid_vi` lọc row corrupt → không lock | ✅ ĐÚNG | `canonical_lock.py:124,134` return `len>0 and not isascii`; vòng lặp gate `is_valid_vi(cvi or '')` |
| §B A001984 clean → LOCKED | ✅ ĐÚNG | `canonical_decision` A001984 admin_approved/1.0/verified; LOCK_THRESHOLD=1.0 (`canonical_lock.py:789,812`) |
| §C 41 tests (23+18) | ✅ ĐÚNG | `test_t166_matrix.py`=23, `test_t166_canonical_lock.py`=18 |
| §D P8 gate OFF (nhánh P8 DORMANT) | ✅ ĐÚNG (giới hạn nhánh P8) | `app.py:19007` `_P8_PILOT_GATE_ENABLED=False`; gate `if _p8_active` chỉ bao prompt/parse |
| §D/E/H/J "zero external LLM" | ❌ **QUY CHỤP** | `_t73_call_gemini` gọi Groq **ngoài** gate P8 — xem §1 |
| §B/H/I #1#2 PL corrupt → ADMIN REVIEW | ⚠️ **STALE — ĐÃ FIX T206** | §2 |
| §B `places_dila.location` cột | ❌ sai tên cột | §3 |
| §E inventory 34 nhóm / 1506 row / 211 orphans | ⚠️ **STALE** | §4 — DB nay 1507 / 31 nhóm / 210+1 |
| §F tie-break A021395 `bao_an_phap_dien` thắng | ✅ ĐÚNG (theo T200 default) | `vnpa_lookup.py:37-49` VNPA_STATUS_RANK pending(1)<alias_vi_suffix(3), id ASC ↔ §5 nuance |
| §F phân loại các nhóm | ⚠️ **STALE** | §4/§5 — 6 nhóm đã hết trùng, 4 nhóm mới xuất hiện |

---

## 1. ❌ §D "zero external LLM" — BỊ QUY CHỤP (quan trọng nhất)

Bản 01 kết luận "E. Đường gửi DILA content sang external LLM? NO" và "0 external LLM call".
**Đây là phát hiện theo 1 đường (nhánh P8) nhưng diễn đạt như tuyệt đối.**

Thực tế `app.py:20749` — route dịch mô tả địa danh:

```python
_p8_active = _p8_pilot_active(request)          # 20732
...
prompt = _t73_build_style_prompt(...)           # 20739
if _p8_active: ...                              # 20741 — chỉ gắn entity-instr vào prompt
note_vi_raw, model_id, err_type = _t73_call_gemini(  # 20749 — LUÔN gọi (ngoài if _p8_active)
    prompt, source_type='place_note', source_text=note_zh, conn=conn, ...)
```

`_t73_call_gemini` → `requests.post(GROQ_URL, ...)` (`app.py:19229/19250`). Gate P8 **không chặn**
gọi LLM — nó chỉ quyết định có thêm XML entity instruction + hậu xử lý output hay không.
Các call site Groq ngoài P8: `app.py` 2980, 3021, 9467, 19250, 19922, 20952, 21106, 21535, 23461, 23813.

⇒ Khi có translation API key (Groq), nội dung DILA (place note / bio / web summary...) **vẫn được gửi ra LLM ngoài**.
**Kết luận đúng cần ghi:** *"Không có external LLM call qua nhánh P8; nhưng ứng dụng vẫn gọi LLM ở nhánh dịch
thông thường khi cấu hình key — xem `docs/reports/T202-logic-review-20261009/README.md`."*

**Ghi chú đối chiếu:** `docs/reports/T202-logic-review-20261009/README.md` (2026-10-09) **đã bắt đúng** lỗ logic này.

---

## 2. ⚠️ §B/H/I PL corrupt — ĐÃ FIX bởi T206 (2026-10-02)

Tại ngày bản 01 (2026-10-01), 2 row `canonical_decision` bị corrupt đúng như 01 mô tả.
Nhưng **ngày 2026-10-02 commit `9641215` (T206) đã sửa DB**:

| entity_ref | Bản 01 (10-01) | DB hôm nay (10-10) | Trạng thái lock |
|---|---|---|---|
| PL000000000314 | `'Th? S?t H?i'` corrupt | `'Thế Sát Hải'` admin_approved/1.0/verified | **LOCKED** (level 1.0 ≥ 1.0) |
| PL000000000001 | `'Kho?t T?t ?a Qu?c'` corrupt | `'Khoát Tạt Đa Quốc'` auto_transliterate/1.0/needs_review | **CANDIDATE** (level 0.7 < 1.0) |

- `canonical_decision` hiện có **3 row**: 2 row trên + A001984 (`'Quy Sơn Linh Hựu'` verified). Tổng corrrupt chứa `?` = **0**.
- 2 mục "HIGH · ADMIN REVIEW REQUIRED" trong §I bản 01 ⇒ **đã đóng** (T206).
- `PL000000000001` còn lại ở mức `needs_review`, hiện chưa được admin duyệt → xem §6 mục 6.

---

## 3. ❌ §B "places_dila.location" — sai tên cột

Bản 01 dòng: `location: 116.359041 39.910958 (西城區, Bắc Kinh)`.
Xác minh schema `places_dila` (PRAGMA): **không có cột `location`**. Cột đúng:

`location_xml` (TEI `<geo cert="low">116.359041 39.910958</geo>` 西城區 · place `PLD000002`) ·
`geo_lat` · `geo_long` · `place_key` · `district`.

- Tọa độ 116.359041 / 39.910958 (Bắc Kinh, 西城區) — **đúng**, chỉ sai tên cột trong 01.
- `name='十剎海寺'` vs `name_zh='世剎海'` — **mismatch có thật trong data nguồn** (primary vs alternative).

---

## 4. ⚠️ §E Inventory — dữ liệu mới 2026-10-10

Nguồn: `vn_person_authority` (read-only). **Nhóm `dila_id=''` hay NULL → orphan.**

```
total=1507 · distinct dila_id=1263 · dila_id='' =210 · dila_id IS NULL =1
status histogram: auto_ttl 589 · alias_vi_suffix 446 · pending 443 · verified 22 · alias_zh_match 7
```

**So với bản 01 (34 nhóm = 33 non-empty + 211 empty):**

- 6 nhóm cũ đã **hết trùng** (mỗi id giờ 1 row):
  - A009319, A010534, A020120, A004981 → alias row bị **DELETE** (T212 `38fa4cb` "D1-A DELETE 4 CLEAR_ALIAS alias rows").
  - A014617 → `tri_hai_dao_binh` verified `'Trí Hải Đạo Bình'` (zh=智海道平); `tang_chu_pho_dung` được tách → `dila_id=NULL` (orphan mới).
  - A044094 → `thieu_chau_phap_hai` còn 1 row (`'Thiều Châu Pháp Hải'` zh=法海).
- **4 nhóm MỚI** (txuất hiện sau ETL T220/T223-era): A003623, A003636, A004697, A021287 → chi tiết §5.

### 4.1 31 nhóm duplicate (dila_id non-empty, size≥2) + winner theo `VNPA_STATUS_RANK`

Winner = min theo `(rank, id)` với rank: verified=0 < pending=1 < auto_ttl=2 < alias_vi_suffix=3 < alias_zh_match=4.

| dila_id | n | Winner (status) | Các row khác |
|---|---|---|---|
| A010511 | 3 | `nam_nhac_huyen_thai` Nam Nhạc Huyền Thái (pending) | dam_chau_bao_cai_uoc (auto_ttl, zh=''), the_nham_ton_tho (pending, zh='') |
| A021395 | 3 | `bao_an_phap_dien` Báo Ân Pháp Diễn (pending) | alias_A021395 Ngũ Tổ Pháp Diễn (alias, zh=法演), tu_to_phap_dien Tứ Tổ Pháp Diễn (pending) |
| A026824 | 3 | `duong_chau_tue_giac` Dương Châu Tuệ Giác (pending) | lang_nha_tue_giac, linh_thuu_tue_giac (pending) |
| A000108 | 2 | `bao_ninh_nhan_dung` Bảo Ninh Nhân Dũng (verified) | nguyet_chuong_tri_uyen (pending) |
| A002653 | 2 | `tay_vuc_quat_da_tam_tang` Tây Vực Quật Đa Tam Tạng (pending, zh=窟多三藏) | bien_dam_hieu_lieu (auto_ttl) |
| A003623 | 2 | `ma_to_dao_nhat` Mã Tổ Đạo Nhất (verified, zh=馬祖道一) | alias_A003623 (alias, zh=馬祖道一) |
| A003636 | 2 | `phuoc_chau_dai_an` Phước Châu Đại An (verified, zh=福州大安) | phuc_chau_dai_an (auto_ttl, **TTL trống**) |
| A004697 | 2 | `vo_chuan_su_pham` Vô Chuẩn Sư Phạm (verified, zh=無準師範) | alias_A004697 (alias, zh=師範, TTL trống) |
| A008471 | 2 | `hoang_dinh_kien` Cư Sĩ Thái Sử Hoàng Đình Kiên (pending) | hoang_long_tri_minh (pending) |
| A008792 | 2 | `ma_noa_la` Tôn Giả Ma Noa La (pending, zh=摩拏羅) | ca_ty_ma_la (auto_ttl) |
| A009478 | 2 | `thach_cung_hue_tang` Thạch Củng Huệ Tạng (pending, zh=石鞏慧藏) | ngu_dai_an_phong (auto_ttl) |
| A014491 | 2 | `long_khanh_khanh_nhan` Long Khánh Khánh Nhàn (pending) | an_hoa_van_nhat (auto_ttl) |
| A020018 | 2 | `dam_chau_dai_xuyen` Đàm Châu Đại Xuyên (pending) | phung_tuong_phat_da (pending) |
| A020456 | 2 | `thiet_phat_tri_tung` Thiết Phật Trí Tung (pending) | alias_A020456 Tam Giao Trí Tung (alias, zh=智嵩) |
| A020647 | 2 | `thien_dong_pho_giao` Thiên Đồng Phổ Giao (pending) | alias_A020647 Long Nha Tông Mật (alias, zh=宗密) |
| A021084 | 2 | `tinh_do_thien_tu` Tịnh Độ Thiện Tư (pending) | tho_ninh_thien_tu (auto_ttl) |
| A021287 | 2 | `thach_suong_tong_giam` Thạch Sương Tông Giám (auto_ttl) | alias_A021287 (alias, zh=宗鑑) |
| A021291 | 2 | `lao_na_tu_dang_dai_hoang` Đại Hồng Tổ Chứng (pending) | dai_hong_to_chung (auto_ttl) |
| A021326 | 2 | `song_lam_duc_dung` Song Lâm Đức Dụng (pending) | pho_minh_duc_dung (auto_ttl) |
| A021350 | 2 | `dong_son_te_vi` Đông Sơn Tề Vĩ (pending) | giac_a (pending) |
| A023045 | 2 | `duc_vuong_phap_dat` Dục Vương Pháp Đạt (pending) | alias_A023045 Hồng Châu Pháp Đạt (alias, zh=法達) |
| A024897 | 2 | `cuu_danh_to` Cửu Đảnh Tố (pending) | long_hoa_dao_so (pending) |
| A025951 | 2 | `kinh_trieu_thi_loi` Kinh Triệu Thi Lợi (pending) | dam_chau_hoa_lam (auto_ttl) |
| A030596 | 2 | `chung_son_dao_long` Chung Sơn Đạo Long (pending) | hoa_nghiem_dao_long (pending) |
| A038165 | 2 | `nguu_dau_hue_phuong` Ngưu Đầu Huệ Phương (pending, zh=慧方) | so_an_hue_phuong (pending) |
| A038615 | 2 | `thai_tu_dao_nhat` Thái Tử Đạo Nhất (pending) | thai_tu_dong_quang (pending) |
| A043012 | 2 | `tue_nhat_minh` Tuệ Nhật Minh (pending) | hoang_ba_vinh_thai (auto_ttl) |
| A043535 | 2 | `ky_ngan_pho_minh` Kỳ Ngạn Phổ Minh (pending) | alias_A043535 Đẳng Giác Phổ Minh (alias, zh=普明) |
| A045400 | 2 | `ngu_dai_tri_thong` Ngũ Đài Trí Thông (pending) | tho_chau_tri_thong (pending, zh=智通) |
| A045639 | 2 | `phap_nhu` Pháp Như (pending, zh=法如) | van_cu_phap_nhu (pending) |
| A047679 | 2 | `phu_son_duc_tuyen` Phù Sơn Đức Tuyên (pending) | quang_tue_duc_tuyen (pending) |

**Tổng kết winner:** verified 4 (A000108, A003623, A003636, A004697) · auto_ttl 1 (A021287) · pending 26.

### 4.2 Orphans

- `dila_id=''`: **210** row, **toàn bộ status=pending**.
- `dila_id IS NULL`: **1** row — `id=tang_chu_pho_dung` `'Tạng Chủ Phổ Dung'` (pending).
- Tổng orphan ≈ **211** (trùng số bản 01 nhưng thành phần khác: 210="" + 1=NULL).

---

## 5. ⚠️ §F phân loại — cập nhật theo dữ liệu mới

- **4 nhóm MỚI cần review** (chưa nằm trong bản 01):
  - A003623 Mã Tổ Đạo Nhất: verified + alias cùng tên → **alias row khả năng thừa** (CLEAR_ALIAS-style).
  - A003636: `phuc_chau_dai_an` (auto_ttl, **không có ttl_filename**) vs `phuoc_chau_dai_an` verified — khác "Phúc/Phước"; không-TTL row cần audit.
  - A004697 Vô Chuẩn Sư Phạm: verified + alias (zh=師範, không TTL).
  - A021287: auto_ttl không zh vs alias (zh=宗鑑).
- **A021395 nuance** (bản 01 kết luận pending `bao_an_phap_dien` thắng — vẫn đúng theo tie-break): nhưng T212/T218 chỉ ra `alias_A021395` có `name_zh='法演'` **đúng**, dila thật của Ngũ Tổ Pháp Diễn = **A036842** ("alias row không có thực thể hậu thuẫn tại A021395") → kết luận tie-break mang tính "T200 default", **không phải canonical**; cần tách theo T212/T218.
- **A010511 data rác**: `nam_nhac_huyen_thai` có `name_zh='畲山兒無所知年年斫斷青山'` (garbled, giờ là 1 trong 3 row của nhóm 3) → **nên dọn** (T220/T223-era liên quan).

---

## 6. Mở — chờ Admin (beyond T271)

1. **210 orphans** `dila_id=''` (toàn bộ pending) + `tang_chu_pho_dung` NULL — quyết giữ/dọn theo T213 phân loại.
2. **4 nhóm MỚI**: phân loại CLEAR_ALIAS / tách dila / cần TTL.
3. **zh rác A010511** — dọn `name_zh`.
4. **A047679** (Phù Sơn/Quảng Tuệ Đức Tuyên) + **A026824** (Dương Châu/Lang Nha/Linh Thứu Tuệ Giác) — cần domain knowledge.
5. **A021395** — quyết tách theo T212/T218 (A036842).
6. **PL000000000001** `'Khoát Tạt Đa Quốc'` auto_transliterate/needs_review — admin duyệt.
7. **Guard chặn external LLM** (nếu Admin muốn dừng hẳn): gate cấp ứng dụng, không chỉ P8 — quyết định sản phẩm (translation đang phụ thuộc Groq).

---

## 7. Nguồn (đầy đủ)

- Bản cũ: `docs/Mimo-Flash/X-T202-POST-REVIEW-01.md` · review-song-hành: `docs/reports/T202-logic-review-20261009/README.md`
- Code: `canonical_lock.py` (124/134/772-798/789/808-812/878/901-911/1034-1037) · `vnpa_lookup.py` (37-49) · `app.py` (19007, 19229-19250, 20732-20758, GROQ call sites)
- Git: `a41eb7a` (T200 pass-2) · `a2d1afe`/`748d17d`/`6efc89d` (§A 01) · `9641215` (T206 fix PL) · `38fa4cb` (T212 DELETE 4 CLEAR_ALIAS) · `2262e74` (T207) · `6230c40` (T208) · `92100d1` (T225)
- DB: `data/lineage.db` (vn_person_authority, canonical_decision, places_dila) — scan read-only `scripts` mentioned in session.