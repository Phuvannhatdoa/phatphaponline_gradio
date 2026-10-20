# T52a — Verify CBETA Data Prep (Đối Chiếu Tam Tạng) — DONE

> **Ngày:** 2026-09-11 · **Trạng thái:** ✅ DONE (read-only, 0 ALTER, 0 migration)
> **Unblock:** T34 Phase A admin-approve 2026-09-10 (commit `76d9914`, tasktodo T34 DONE)

## Bối cảnh
T52 (Đối Chiếu Tam Tạng) đã có backend T52b + UI T52c/d/e từ trước (2026-08-29 → 09-01).
**T52a** (chuẩn bị dữ liệu) bị block vì chờ admin duyệt xóa fake data 84000/VRI (T34 Phase A).
Ngày 2026-09-10 Lee duyệt T34 Phase A ✅ → T52a giờ có thể verify.

## Verify (read-only, `data/lineage.db`)

### 1. Fake 84000/VRI — phải = 0
| bảng | count |
|------|------|
| `eight_four_thousand` | **0** ✅ |
| `eight_four_thousand_place_map` | **0** ✅ |
| `vri_tipitaka_catalog` | **0** ✅ |
| `vri_place_mapping` | **0** ✅ |
| `vri_cached_texts` | **0** ✅ |

### 2. Crossref — phải còn nguyên
| bảng | count | ghi chú |
|------|------|---------|
| `toh_cbeta_crossref` | **10** ✅ | T38 curated pairs |
| `sat_crossref` | **2,913** ✅ | T35 SAT crossref |
| `pali_place_ref` | **15** ✅ | T37 Pali sites |
| `kanripo_catalog` | **101** ✅ | real ETL (T34 giữ) |

### 3. Kết luận
- Đủ 3 nhóm crossref cho compare UI → **không cần bổ sung thêm** (Tâm Kinh/Kim Cang đã phủ qua T52b `_PALI_REF_MAP` + toh + sat).
- Không cần ghi DB. 0 ALTER, 0 migration.

## Files
- `tasks/T52-doi-chieu-tam-tang.md` — T52a → ✅ DONE (thêm build log)
- `docs/tasktodo.md` — dòng T52 → **T52 ✅ DONE (2026-09-11)**

## Revert
Không có thay đổi code/DB → revert = `git revert <commit này>` (docs-only).