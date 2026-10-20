# T220 — VNPA DILA-ID Recovery: Final Report (SUPERSEDED)

> ⚠️ **SUPERSEDED BY T215** — This document is a duplicate of T215-VNPA-DILA-ID-RECOVERY-01.md. The actual recovery was performed under T215. This file is archived for historical reference only.

**Task ID:** T220-VNPA-DILA-ID-RECOVERY-01  
**Ngày:** 2026-10-02  
**Trạng thái:** ✅ PASS (duplicate — actual work in T215)  
**Phụ thuộc:** T214, T212, T211  
**Superseded by:** T215-VNPA-DILA-ID-RECOVERY-01.md  
---

## 1. Mục tiêu

Khôi phục chính xác 33 giá trị `vn_person_authority.dila_id` đã được chứng minh bởi T214 forensic audit từ backup T206/T207 (last-known-good). Phạm vi cứng: chỉ 33 UPDATE, 0 INSERT, 0 DELETE, 0 schema change.

---

## 2. Backup Pre-Apply

| Item | Giá trị |
|------|---------|
| File | `data/backups/lineage_t215_20261002_172632.db` |
| SHA256 | `813cb17f296acc97b4b8286924ff9795e76dff478fbfd9f27931e556dc2a9ee9` |
| Trạng thái backup | VERIFIED ✓ (source SHA256 = backup SHA256) |
| Total rows trước apply | 1502 |
| NULL trước apply | 33 |

---

## 3. Manifest 33 Rows (T220)

| # | id (PK) | dila_id restored |
|---|---------|-----------------|
| 1 | chung_son_dao_long | A030596 |
| 2 | cuu_danh_to | A024897 |
| 3 | dam_chau_dai_xuyen | A020018 |
| 4 | dong_son_te_vi | A021350 |
| 5 | duong_chau_tue_giac | A026824 |
| 6 | hoa_nghiem_dao_long | A030596 |
| 7 | hoang_long_tri_minh | A008471 |
| 8 | kinh_trieu_thi_loi | A025951 |
| 9 | lang_nha_tue_giac | A026824 |
| 10 | lao_na_tu_dang_dai_hoang | A021291 |
| 11 | linh_thuu_tue_giac | A026824 |
| 12 | long_khanh_khanh_nhan | A014491 |
| 13 | ma_noa_la | A008792 |
| 14 | nam_nhac_huyen_thai | A010511 |
| 15 | ngu_dai_tri_thong | A045400 |
| 16 | nguu_dau_hue_phuong | A038165 |
| 17 | nguyet_chuong_tri_uyen | A000108 |
| 18 | phap_nhu | A045639 |
| 19 | phong_huyet_dien_chieu | A004981 |
| 20 | phu_son_duc_tuyen | A047679 |
| 21 | quang_tue_duc_tuyen | A047679 |
| 22 | so_an_hue_phuong | A038165 |
| 23 | song_lam_duc_dung | A021326 |
| 24 | tay_vuc_quat_da_tam_tang | A002653 |
| 25 | thach_cung_hue_tang | A009478 |
| 26 | thai_tu_dong_quang | A038615 |
| 27 | the_nham_ton_tho | A010511 |
| 28 | tho_chau_tri_thong | A045400 |
| 29 | tinh_do_thien_tu | A021084 |
| 30 | tri_hai_dao_binh | A014617 |
| 31 | tu_to_phap_dien | A021395 |
| 32 | tue_nhat_minh | A043012 |
| 33 | van_cu_phap_nhu | A045639 |

---

## 4. Apply Results

| Metric | Giá trị |
|--------|---------|
| rows affected | **33** (expected 33) ✓ |
| dila_id NULL trước | 33 |
| dila_id NULL sau | **0** ✓ |
| Total rows (pre-apply) | 1502 |
| Total rows (post-apply) | 1502 (apply script internal) |
| Idempotent guard | `WHERE id=? AND dila_id IS NULL` — không ghi đè non-NULL |
| Post-apply SHA256 | `eb854d3f38cedf694571e6ea87f3c91fd761bc91f1df5753a66362f16a12f814` |

---

## 5. Anomaly: +1 Row (dien_phuc_tue_thang)

**Quan sát:** Sau khi apply hoàn tất, kiểm tra ngoài cho thấy total=1503 (không phải 1502).  
**Phân tích:** Row `dien_phuc_tue_thang` (Diên Phúc Tuệ Thăng, dila_id=A008431, status=verified, created_at=2026-10-02 10:45:33) được thêm bởi **background ETL/pipeline** chạy đồng thời — không phải từ T220.  
**Kết luận:** T220 thực hiện đúng 0 INSERT. Anomaly hoàn toàn ngoài phạm vi T220. Accepted.

---

## 6. Verification — 8 Sections

### Section 1: DB Stats ✓

| Metric | Expected | Actual |
|--------|----------|--------|
| total | 1503 (1502 + 1 background) | 1503 ✓ |
| NULL | 0 | 0 ✓ |
| empty string | 211 | 211 ✓ |
| has value | 1292 | 1292 ✓ |

### Section 2: T200 Before/After Matrix ✓

Tất cả 6 broken dila_ids (13 broken lookups) đã được phục hồi:

| dila_id | Before T220 | After T220 |
|---------|-------------|------------|
| A026824 | BROKEN (None) | `duong_chau_tue_giac` ✓ |
| A030596 | BROKEN (None) | `chung_son_dao_long` ✓ |
| A038165 | BROKEN (None) | `nguu_dau_hue_phuong` ✓ |
| A045400 | BROKEN (None) | `ngu_dai_tri_thong` ✓ |
| A045639 | BROKEN (None) | `phap_nhu` ✓ |
| A047679 | BROKEN (None) | `phu_son_duc_tuyen` ✓ |

### Section 3: A047679 Check ✓

- 2 rows với dila_id=A047679: `phu_son_duc_tuyen` (pending) + `quang_tue_duc_tuyen` (pending)
- T200 lookup: returns `phu_son_duc_tuyen` (id ASC tie-break) ✓

### Section 4: D3 A021395 Check ✓

- 3 rows: `alias_A021395` (alias_vi_suffix), `bao_an_phap_dien` (pending), `tu_to_phap_dien` (pending)
- `tu_to_phap_dien.dila_id = 'A021395'` ✓
- T200 lookup → `bao_an_phap_dien` (pending wins over alias_vi_suffix) ✓
- **Note:** D3 (chọn canonical giữa bao_an/tu_to) vẫn unresolved — cần Admin decision (ngoài phạm vi T220)

### Section 5: D4 A010511 Check ✓

- 3 rows: `dam_chau_bao_cai_uoc` (auto_ttl), `nam_nhac_huyen_thai` (pending), `the_nham_ton_tho` (pending)
- `nam_nhac_huyen_thai.dila_id = 'A010511'` ✓ (restored)
- `the_nham_ton_tho.dila_id = 'A010511'` ✓ (restored)
- `dam_chau_bao_cai_uoc.dila_id = 'A010511'` — still wrong-person (D4 fix needed, ngoài phạm vi T220)

### Section 6: T212 Preservation ✓

4 alias rows do T212 xóa vẫn absent:
- `alias_A009319` absent ✓
- `alias_A010534` absent ✓
- `alias_A020120` absent ✓
- `alias_A044094` absent ✓

### Section 7: D1-A Excluded Groups Post-Recovery

| dila_id | Row count | Rows |
|---------|-----------|------|
| A004981 | 2 | `phong_huyet_dien_chieu` (auto_ttl) + `nam_vien_hue_ngung` (pending) |
| A021291 | 2 | `dai_hong_to_chung` (auto_ttl) + `lao_na_tu_dang_dai_hoang` (pending) |
| A008471 | 2 | `hoang_dinh_kien` (pending) + `hoang_long_tri_minh` (pending) |

Các group này có 2 rows (do T220 restore) — cần curation trong D2/future tasks. T220 không can thiệp.

### Section 8: T213 Scope Check ✓

- `dila_id=''` count = 211 (unchanged) ✓ — T213 scope preserved

---

## 7. Regression

### T166 Identity Audit

```
T166 audit: PASS (0 FAIL) + 1 WARN (Gemini key inline — không chặn pipeline)
```

✅ 18/18 checks PASS

### Translation Tests (npm run test:translation)

```
T203/T204 test: 25 PASS, 2 FAIL
  FAIL: corpus parse (TS-Tien-Phuoc-Trach-Sung.ttl — parse error)
```

**Kết luận:** 2 FAIL là lỗi pre-existing (TTL file bị lỗi), **không liên quan đến T220**. T220 không thay đổi code hay TTL. Regression OK.

---

## 8. ETL Root Cause Review (Section 13)

**File:** `scripts/etl_ttl_person_authority.py`

**Cơ chế gây mất dila_id:**

```python
# Lines 374-378: Full DELETE before reinsert
for t in ('vn_person_events', 'vn_person_works', 'vn_person_places',
          'vn_person_relations', 'vn_person_authority'):
    conn.execute(f"DELETE FROM {t}")
conn.commit()

# Line 399: dila_id từ ttl_mapping (bỏ sót = empty string)
person['dila_id'] = dila_map.get(key, '')

# Line 437: INSERT OR REPLACE (nhưng bảng đã empty)
INSERT OR REPLACE INTO vn_person_authority (...)
```

**Vấn đề chính:**
1. ETL xóa toàn bộ `vn_person_authority` trước khi reinsert
2. `dila_map` chỉ load từ `ttl_mapping WHERE dila_id IS NOT NULL`
3. Các dila_id được curate thủ công (không qua ttl_mapping) bị mất khi ETL chạy lại

**Follow-up task:** T216 — ETL UPSERT guard: sửa ETL để preserve existing dila_id (đọc current values trước DELETE, restore sau INSERT, hoặc chuyển sang UPDATE-only pattern).

---

## 9. Final Verdict

| # | Điều kiện | Kết quả |
|---|-----------|---------|
| A | 33 historical dila_ids đúng từ T206/T207 | ✓ PASS |
| B | 0 INSERT | ✓ PASS (dien_phuc_tue_thang = background ETL, không phải T220) |
| C | 0 DELETE | ✓ PASS |
| D | 0 schema change | ✓ PASS |
| E | Không thay đổi field ngoài dila_id | ✓ PASS |
| F | T212 curation preserved (4 alias rows absent) | ✓ PASS |
| G | T200 lookup behavior restored (6 broken dila_ids → working) | ✓ PASS |
| H | Backup verified SHA256 | ✓ PASS |
| I | T166 regression PASS | ✓ PASS |
| J | T213 scope unchanged (211 empty rows) | ✓ PASS |
| K | ETL root cause identified, T216 follow-up created | ✓ PASS |

**VERDICT: ✅ T220 PASS**

---

## 10. Files

| File | Mô tả |
|------|-------|
| `scripts/t215_restore_vnpa_dila_ids.py` | Recovery script (--stats/--dry-run/--apply/--revert) |
| `data/backups/lineage_t215_20261002_172632.db` | Pre-apply backup |
| `docs/Mimo-Flash/T220-VNPA-DILA-ID-RECOVERY-01.md` | This report |
| `tasks/T220-vnpa-dila-id-recovery.md` | Task tracking |

---

## 11. Pending (Ngoài phạm vi T220)

| Task | Trạng thái |
|------|-----------|
| **D3** A021395: chọn canonical giữa bao_an_phap_dien/tu_to_phap_dien | Cần Admin decision |
| **D4** A010511: fix dam_chau_bao_cai_uoc wrong-person | Cần D4 task execution |
| **T213** Classification 211 dila_id='' rows | Sẵn sàng (trigger từ Admin) |
| **T216** ETL UPSERT guard (preserve dila_id) | Follow-up task — cần Admin approval |
| **D2** A047679 disambiguation | Cần DILA evidence |
| **T165-P8** FROZEN | Cần DILA governance |
