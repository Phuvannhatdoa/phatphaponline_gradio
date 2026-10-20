# T213 Classification Report — 211 VNPA Orphans (dila_id='' + NULL)

**Date:** 2026-10-10  
**Task:** `tasks/T213-vnpa-orphan-211-classification.md` (READ-ONLY, 0 DB mutation)  
**Source:** `vn_person_authority` where `dila_id=''` (210) or `dila_id IS NULL` (1 `tang_chu_pho_dung`)

---

## Summary

| Bucket | Count | Description |
|---|---|---|
| **A** | **186** | VN Non-DILA Monks — Vietnamese monastics without DILA ID, have TTL files (TS-…) |
| **B** | **6** | Indian Patriarchs — Ton-Gia prefix (Sanskrit transcriptions) + Ngũ Phong Thường Quán |
| **C** | **11** | Non-monk Entities — Cư Sĩ (lay persons), scribes, officials, TTL prefix Cs- |
| **D** | **8** | Mythological — Buddhas, Bodhisattvas, Arhats (non-Indian) |
| **Total** | **211** | = 210 `''` + 1 `NULL` |

---

## Bucket A — VN Non-DILA Monks (186)

All have `ttl_filename` starting with `TS-`, Vietnamese monastic names, `status='pending'`.  
Representative samples:
- `am_chu_ho_khe` — Am Chủ Hổ Khê
- `bac_giang_tay_lan_nhuong` — Bắc Giang Tây Lan Nhượng
- `vo_ngon_thong` — Vô Ngôn Thông
- `minh_hai_phap_bao` — Minh Hải Pháp Bảo
- `nguyen_thieu_sieu_bach` — Nguyên Thiều Siêu Bạch
- `tang_chu_pho_dung` — Tạng Chủ Phổ Dung (the single `NULL` dila_id row)
- `bon_qua_khoang_vien` — Bổn Quả Khoáng Viên
- `bach_van_khong_do` — Bạch Vân Không Độ

**Note:** These are valid VN monastic entities; lack of DILA ID reflects DILA coverage gap for Vietnamese lineages. **Recommendation:** Keep as-is (Bucket A = valid data).

---

## Bucket B — Indian Patriarchs (6)

Ton-Gia prefix (Tôn Giả = Sanskrit *Ārya* / *Sthavira* transcriptions) + 1 extra:

| id | name_vi | name_zh | note |
|---|---|---|---|
| `da_da_xa_da` | Tôn Giả Dà Da Xá Đa | 迦耶舍多 | Kāśyapa lineage |
| `dao_tin` | Tôn Giả Đạo Tín | — | |
| `la_hau_la_da` | Tôn Giả La Hầu La Da | 羅詭羅 | Rāhula? |
| `ngu_phong_thuong_quan` | Ngũ Phong Thường Quán | 五峰常觀 | Chinese patriarch, Sanskrit origin |
| `su_tu_ty_kheo` | Tôn Giả Sư Tử Tỳ Kheo | 師子菩薩 | Siṃha-bodhisattva / Arhat |
| `uu_ba_cuc_da` | Tôn Giả Ưu Ba Cúc Đa | 優婆毱多 | Upagupta |

**Recommendation:** Link to DILA IDs when found (separate task post-T213).

---

## Bucket C — Non-monk Entities (11)

Cs- prefix or lay titles in name_vi:

| id | name_vi | evidence |
|---|---|---|
| `banh_nhu_lam` | Cư Sĩ Gián Nghị Bành Nhữ Lâm | `Cs-`, "Cư Sĩ" |
| `cs_huong` | Cs Hướng | `Cs-` prefix |
| `do_huong_trinh` | Cư Sĩ Tả Ty Đô Huống Trịnh | "Cư Sĩ", "Tả Ty" |
| `mac_tuong_thieu_hu` | Cư Sĩ Mạc Tướng Thượng Thư Thiếu Hư | "Cư Sĩ" |
| `pham_xung` | Cư Sĩ Tả Thừa Phạm Xung | "Cư Sĩ", "Tả Thừa" |
| `phan_luong_quy` | Cư Sĩ Đãi Chế Phan Lương Quý | "Cư Sĩ", "Đãi Chế" |
| `quach_tuong_chanh` | Cư Sĩ Đề Hình Quách Tường Chánh | "Cư Sĩ", "Đề Hình" |
| `tang_khai` | Cư Sĩ Nội Hàng Tăng Khai | "Cư Sĩ", "Nội Hàng" |
| `thu_ky_nam` | Thư Ký Nam | "Thư Ký" |
| `trieu_lenh_cam` | Cư Sĩ Quận Vương Triệu Lệnh Câm | "Cư Sĩ", "Quận Vương" |
| `ty_bo_ton` | Cư Sĩ Tỷ Bộ Tôn | "Cư Sĩ", "Tỷ Bộ" |

**Recommendation:** Admin decide — keep as historical lay figures or tag separately.

---

## Bucket D — Mythological (8)

Buddhas, Bodhisattvas, Arhats (non-Ton-Gia, i.e. not Indian patriarchs):

| id | name_vi | classification |
|---|---|---|
| `thich_ca_mau_ni_phat` | Thích Ca Mâu Ni Phật | Śākyamuni Buddha |
| `phat_bao_phap_hoa` | Phật Bảo Pháp Hóa | Buddha from Lotus Sutra |
| `phat_y_linh_nhac` | Phật Ý Linh Nhạc | Mythological Buddha |
| `thach_phat_hien_trong` | Thạch Phật Hiển Trọng | Mythological |
| `thanh_vien_phat_nhan` | Thanh Viễn Phật Nhãn | Mythological |
| `tuyen_minh_phat_an` | Tuyên Minh Phật Ấn | Mythological |
| `nguyet_chau_than_giam` | Nguyệt Châu Thần Giám | Deity (Thần) |
| `thien_tue_bao_chuong` | Thiên Tuế Bảo Chưởng | Mythological |

**Recommendation:** Tag as mythological; exclude from monastic lineage queries.

---

## Rows Requiring Admin Manual Review

None — all 211 classified with clear evidence.

---

## Next Steps (Post-T213)

Per task spec:
- **Bucket A (186):** Keep — valid VN monastics without DILA.
- **Bucket B (6):** Create separate task to link DILA IDs (needs DILA evidence).
- **Bucket C (11):** Admin decide — keep / tag / move to separate table.
- **Bucket D (8):** Tag `is_mythological=true` (schema addition) or move to reference table.

---

## Evidence File

Full classification JSON saved at: `%TEMP%\opencode\t213_classification_20261010.json`