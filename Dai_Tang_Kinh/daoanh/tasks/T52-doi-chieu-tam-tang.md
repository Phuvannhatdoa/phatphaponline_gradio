---
id: T52
title: "Đối Chiếu Tam Tạng — Cross-Tradition Text Comparison UI"
module: Tam Tạng / Commercial References / UI
priority: high
status: done
depends_on: [T34, T35, T36, T37, T38]
created: 2026-08-26
updated: 2026-09-11
done_when: >
  Giao diện so sánh cùng 1 đoạn kinh hiển thị song song Hán/Pali/Tạng/Sanskrit,
  data realtime từ DharmaNexus + SAT + 84000, fake data 84000/VRI đã được xử lý bởi T34 Phase A,
  liên kết SuttaCentral/PTS numbering. Không ghi đè các route crossref đơn lẻ hiện có.
---

# T52 — Đối Chiếu Tam Tạng

> **Lưu ý:** Task này được tạo mới 2026-08-26. Số T52 trước đây thuộc về
> "CBETA Analytics & Admin Dashboard" — đã được đổi thành T54.

## Mục tiêu
Xây giao diện so sánh "Tam Tạng" — hiển thị song song cùng 1 đoạn kinh qua nhiều truyền thống.

## Hiện Trạng (Codebase) — Infrastructure Đã Có
- `T36` DharmaNexus parallels: `GET /daoanh/api/cbeta/<sigla>/parallels` — realtime Hán/Pali/Tạng/Sanskrit
- `T38` Toh-CBETA crossref: `GET /daoanh/api/cbeta/<sigla>/toh` — 10 curated pairs
- `T35` SAT crossref: `GET /daoanh/api/cbeta/<sigla>/sat` — 2,913 rows → badge "Xem trên SAT"
- `T37` Pali place ref: `GET /daoanh/api/places/<id>/pali` — 15 Indian sites + SuttaCentral link
- Source chips: 84000/Kanripo/SAT đã có trên places.html
- `T34` Tam Tạng Integration spec — gồm Phase A (xóa fake data 84000/VRI)

## Khoảng Trống (Gap)
- Chưa có **UI so sánh side-by-side** cùng 1 đoạn kinh qua các truyền thống
- DharmaNexus/SuttaCentral link ra ngoài, chưa render inline
- 84000/VRI data FAKE cần T34 Phase A cleanup trước
- PTS numbering (DN/MN/SN/AN/KN) chưa hiển thị như chuẩn tham chiếu

## Subtasks

### T52a — Chuẩn Bị Dữ Liệu ✅ DONE (2026-09-11, verify đủ điều kiện)
- Verify T34 Phase A đã xóa xong fake 84000/VRI rows (bảng: `eight_four_thousand`, `eight_four_thousand_place_map`, `vri_tipitaka_catalog`, `vri_place_mapping`, `vri_cached_texts`)
- Đảm bảo `toh_cbeta_crossref` + `sat_crossref` + `pali_place_ref` còn nguyên
- Nếu thiếu → bổ sung crossref cụ thể cho các kinh phổ biến (Tâm Kinh, Kim Cang...)
- **Trạng thái 2026-08-29:** chưa chạy — blocked chờ admin duyệt xóa ~80 rows fake (T34 Phase A).
- **Verified 2026-09-11:** T34 Phase A đã admin duyệt (commit `76d9914`, tasktodo T34 DONE 2026-09-10) → 5 bảng fake = 0 (`eight_four_thousand`, `eight_four_thousand_place_map`, `vri_tipitaka_catalog`, `vri_place_mapping`, `vri_cached_texts`); crossref nguyên vẹn: `toh_cbeta_crossref`=10 · `sat_crossref`=2,913 · `pali_place_ref`=15 · `kanripo_catalog`=101 (real). Không cần bổ sung crossref (đủ 3 nhóm). Read-only, 0 ALTER.

### T52b — Đoạn Đối Chiếu Backend ✅ DONE (2026-08-29, route live)
- Route: `GET /daoanh/api/cbeta/<sigla>/compare?lang=vi&traditions=han,pali,tang` — app.py:11690-11876
- Gọi đồng thời: CBETA (han) + DharmaNexus (parallels) + SAT (badge) + 84000 (tang) + SuttaCentral (pali)
- Trả về: array các phiên bản {tradition, title, text/preview, link_source, ref_code}
- Helper `_t52_normalize_sigla` (chấp nhận `251`/`T0251`/`T08n0251`/`T50n2060`) + map `_PALI_REF_MAP` (T52d)
- **Test thật:** `T0251` → 4 versions (tang/sat/parallels/pali; han vắng vì chưa import — graceful); `T51n2076` → han(local)+sat.
- Additive, read-only; KHÔNG đụng fake data T34.

### T52c — UI So Sánh Side-by-Side ✅ DONE (2026-09-01)
- Implement: tab Giáo Lý trong `places.html` — `renderGiaolyTab` + `giaolyCbetaCompare` + `giaolySwitchTrad`
- UI: input mã CBETA + nút "So Sánh" → gọi `/daoanh/api/cbeta/<sigla>/compare` → tabs ngang theo truyền thống
- Chips: source_label, ref_code, link ngoài ↗ Xem toàn văn
- Auto-suggest từ `GET /daoanh/api/places/<id>/pali` nếu địa danh có Pali ref
- **Test thật 2026-09-01:** T0251 → 4 versions (Pali/藏/SAT/DharmaNexus), tab switching OK, title "Bát Nhã Ba La Mật Đa Tâm Kinh"
- Không có scroll sync (dropped — tabs không song song)

### T52d — PTS Numbering Reference ✅ DONE (2026-09-01, via T52c)
- Render `badge_label`, `ref_code` (PTS sutta), `note` trong tab Pali của giaolyCbetaCompare
- Test: T0251 → badge "Pali tham chiếu", 📌 note "Tâm Kinh — không có tương đương Pali..."
- Các text có PTS mapping (T0209→MN 10, T0222→DN 22): ref_code hiển thị đúng trong chip

### T52e — Liên Kết Từ Place ✅ DONE (2026-09-01)
- Chip `🪷 Pali` trong entity sidebar: ẩn mặc định, hiện async cho 15 địa danh có Pali ref
- Tooltip: "Isipatana / Migadāya · SC: sn56.11 — nhấn để xem Đối Chiếu Tam Tạng"
- Click → switch sang tab Giáo Lý (đã có auto-suggest từ T52c)
- Bug fix: API trả về `refs` (không phải `pali_refs`) → fix check cả hai field
- Test: Vườn Nai (PL000000048403) → chip visible; Thiếu Lâm Tự (PL000000023255) → chip hidden ✓

## API Changes
- New: `GET /daoanh/api/cbeta/<sigla>/compare` ✅ live 2026-08-29

## Frontend
- Update: `places.html` tab Giáo Lý — thêm section đối chiếu (T52c, chưa làm)
- (Chờ T54 mới có Home CBETA tab; T52 không phụ thuộc)

## Không Xung Đột Với
- T35/T36/T37/T38 — chỉ dùng lại, không sửa routes
- T34 — T52 cần T34 Phase A hoàn tất (fake data cleanup)
- T54 — Home CBETA tab (T54c) độc lập với so sánh của T52

## Build Log

### 2026-08-29 — Phase 1: Compare Backend (T52b) ✅
**Status chuyển `pending` → `in_progress` (T52b done, T52c/d-e còn lại)**

- **Backend (app.py, thêm trước `# ===== INITIALIZE DIRECTORIES`, additive read-only):**
  - `GET /daoanh/api/cbeta/<sigla>/compare` (T52b) — app.py:11690-11876
    - Helper `_t52_normalize_sigla` — normalize `251`/`T0251`/`T08n0251`/`T50n2060` → `{sh, dn, cbeta_full}`
    - Traverse version array theo truyền thống, filter `traditions=` query
    - `han`: từ `cbeta_content_index` (cbeta.db) preview ≤1200 ký tự + `has_local`
    - `tang`: từ `toh_cbeta_crossref` (T38, `needs_review=0`) → url 84000 + ref `Toh N`
    - `sat`: từ `sat_crossref` (T35) → url 21dzk + `has_unique`
    - `parallels`: từ `dharmanexus_{sigla}.json` cache (T36) hoặc gọi `/parallels` local
    - `pali`: từ `_PALI_REF_MAP` curated → link SuttaCentral + ref `pts_sutta`
  - `_PALI_REF_MAP` (T52d backend) — curated `{pali_title, sc_uid, pts_sutta, note}` cho 0251/0235/0262/0209/0222/0221
- **Test thật (server live PID 14740):**
  - `T0251` → 4 versions: tang(Toh 21, 84000) / sat(21dzk SAT) / parallels(ZH_T08_0251, DharmaNexus) / pali(SuttaCentral). Han vắng vì Tâm Kinh chưa import local — graceful (đúng mong đợi).
  - `T51n2076` → 2 versions: han(`has_local=True`, preview 185) / sat. DharmaNexus không có trong map static → giới hạn đúng.
- **Không đụng:** fake data T34 (5 bảng 84000/VRI), route cũ T35-T38.
- **Chưa làm tuần này (next):** T52c UI side-by-side `places.html` (`renderGiaolyTab` tại places.html:1537 vẫn stub); T52d hoàn thiện map + render; T52e link từ Địa Danh; T52a chờ T34 Phase A.
- **Revert:** `git revert <hash>` (atomic commit này).

## Estimated Effort: ~14 hours
