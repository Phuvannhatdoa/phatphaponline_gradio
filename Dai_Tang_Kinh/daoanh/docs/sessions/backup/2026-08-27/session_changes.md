# Session Changes — 2026-08-27

## Tóm Tắt
Phiên làm việc 2026-08-27. Hoàn thành T49 — Place VI_NAME Character Map Fix.
Tạo task files T47/T48/T49 (phiên trước). T49 done ngay phiên này.

## Git Commits

| Hash | Nội dung | Revertable? |
|------|---------|------------|
| (pending) | feat(T49): charmap fix + conf upgrade — 116K VI_NAME 0.5→0.65 | `git revert <hash>` |

---

## T49 — Place VI_NAME Character Map Fix (Done)

### Phát hiện (thay đổi scope)

Premise ban đầu của T49 sai: data đã có Title Case từ trước.
Vấn đề thực phát hiện khi audit:
1. `hanviet_fallback` có 3 char mapping SAI: `永→vắng`, `澄→chừng`, `觀→quan`
2. 935 entries (thực đo: 692) có ký tự CJK chưa dịch được

### Chars Sai Đã Fix

| Char | Sai (fallback) | Đúng (override) | Places DILA bị ảnh hưởng |
|------|---------------|-----------------|--------------------------|
| 永 | vắng | **Vĩnh** | 636 |
| 澄 | chừng | **Trừng** | 37 |
| 觀 | quan | **Quán** | 418 |

Ví dụ: `永濟寺` → `Vĩnh Tế Tự` (trước: `Vắng Tế Tự`)

### DB Changes

| Table | Metric | Trước | Sau | Delta |
|-------|--------|-------|-----|-------|
| custom_hanviet_override | rows | 2,448 | 2,451 | +3 |
| zqlocal_content | conf=0.5 | 118,293 | 690 | -117,603 |
| zqlocal_content | conf=0.65 | 0 | 116,514 | +116,514 |
| zqlocal_content | conf=0.75 | 0 | 1,089 | +1,089 |
| namevi_map_places | updated | - | 1,091 | +1,091 |

### Script

`scripts/t49_charmap_fix.py` — dry-run by default, `--apply` để thực thi.

Revert: `cp docs/sessions/2026-08-27/lineage_pre_T49.db.bak data/lineage.db`

### Tác Động Việt Hóa

| Sau task | conf≥0.65 | conf≥0.75 |
|----------|-----------|-----------|
| Trước T49 | 0% | 0% |
| Sau T49 | **~99.4%** | **~0.9%** |

690 entries còn conf=0.5 = chứa ký tự hiếm chưa có trong dict (cần T29 mở rộng hoặc admin tay).

### Backup

`docs/sessions/2026-08-27/lineage_pre_T49.db.bak`

---

---

## T47 — Place VI_NAME Verification via Lexicon Cross-Reference (Done)

### Mục Tiêu

Kiểm tra 116,514 VI_NAME entries (conf=0.65, sau T49) đối chiếu với 22 bộ từ điển Phật giáo (166,278 entries).  
Nếu tên VN auto-generated khớp `lexicon.term` (case-insensitive) → nâng confidence.

### Kết Quả

| Metric | Giá trị |
|--------|---------|
| Entries đầu vào (conf=0.65) | 116,514 |
| Match 1 nguồn lexicon → conf=0.75 | **4,038** |
| Match ≥2 nguồn lexicon → conf=0.85 | **1,935** |
| Tổng verified | **5,973 (5.1%)** |
| Không match (giữ conf=0.65) | 110,541 |

**Distribution zqlocal_content sau T47:**
```
conf=0.85:  1,935 entries  (3.3% of 59,167 places)
conf=0.75:  5,127 entries  (8.7%)  ← 4,038 T47 + 1,089 T49 re-transliterate
conf=0.65: 110,541 entries
conf=0.5:     690 entries  ← untranslated chars (cần T29/admin)
```

### Tác Động Việt Hóa Tích Lũy (sau T49 + T47)

| Mức tin cậy | Trước T49 | Sau T49 | Sau T47 |
|-------------|-----------|---------|---------|
| conf≥0.85 | 0% | 0% | **3.3%** |
| conf≥0.75 | 0% | 0.9% | **12.0%** |
| conf≥0.65 | 0% | 99.4% | **99.4%** |
| conf=0.5 (unverified) | 100% | 0.6% | 0.6% |

### Script

`scripts/t47_place_vi_lexicon_verify.py` — dry-run by default, `--apply` để thực thi.

### Backup & Revert

Backup: `docs/sessions/2026-08-27/lineage_pre_T47.db.bak`  
Revert: `cp docs/sessions/2026-08-27/lineage_pre_T47.db.bak data/lineage.db`

---

---

## T48 — Place VI_NAME Reverse Index từ Lexicon Definitions (Done)

### Mục Tiêu

Khai thác pairs (漢字 → Tiếng Việt) từ lexicon structure: `term` = Tên Việt, `definition` bắt đầu bằng `(漢字, romanization):`. Nếu hanzi match `places_dila.name_zh` → update `zqlocal_content` với tên chuẩn từ từ điển (thay tên auto-transliterate sai).

### Kết Quả

| Metric | Giá trị |
|--------|---------|
| Pairs extracted | 2,122 |
| Match với DILA | 126 |
| Upgrades (conf<0.75, tên khác) | **37** |
| → conf=0.75 (place suffix) | **26** |
| → conf=0.72 (admin review) | **11** |

**Lỗi hệ thống đã fix:** 水→Héo→Thủy, 蓮→Sen→Liên, 澤→Rạch→Trạch (do hanviet_fallback thiếu context)

**zqlocal_content sau T48:**
```
conf=0.85:  1,935 entries
conf=0.75:  5,153 entries  ← +26 T48
conf=0.72:     11 entries  ← admin review
conf=0.65: 110,504 entries
conf=0.5:     690 entries
```

### Script

`scripts/t48_place_vi_reverse_index.py` — dry-run / `--apply` / `--review`

### Backup & Revert

Backup: `docs/sessions/2026-08-27/lineage_pre_T48.db.bak`  
Revert: `cp docs/sessions/2026-08-27/lineage_pre_T48.db.bak data/lineage.db`

---

---

## Entity Unified API Bug Fix (2026-08-27)

### Vấn đề
`/daoanh/api/entity/<id>/unified` thiếu `canonical_name` và `canonical_name_vi` trong response.
Frontend `places.html` hiển thị raw entity_id thay vì tên Việt.

### Root Cause
1. Fallback query chỉ lấy `alias_zh AS canonical_label` — thiếu `alias_vi`
2. Logic gán `canonical_name_vi` từ `namevi_map_places` có thể overwrite `None` nếu không tìm thấy

### Fix (app.py line ~10516)
- Fallback query: thêm `alias_vi AS canonical_name_vi`
- Logic: chỉ overwrite nếu namevi_map_places có giá trị; giữ alias_vi làm fallback

### Kết quả
`/daoanh/api/entity/PL000000023255/unified` → `canonical_name: "少林寺"`, `canonical_name_vi: "Thiếu Lâm Tự"`
Frontend `itemNameVi` hiển thị đúng "Thiếu Lâm Tự"

---

## T51d — CBETA Aggregate Mention Stats (2026-08-27)

### Kết quả

| Metric | Giá trị |
|--------|---------|
| cbeta_place_mention_stats rows | **26,484** |
| passage_entity total links | 378,483 |
| Top place | Bắc Kinh (590 mentions) |
| Thiếu Lâm Tự | 30 mentions (T50n2060, T50n2061, T51n2076) |

### Changes
- NEW: `cbeta_place_mention_stats` table (26,484 rows)
- NEW: `scripts/t51d_build_aggregates.py`
- NEW: `GET /daoanh/api/admin/cbeta/aggregates` endpoint
- UPDATE: `entity_unified` — thêm `cbeta_mention_count` field

---

---

## T52 — CBETA Analytics & Admin Dashboard (2026-08-27)

### T52a — Admin CBETA Dashboard (Done)
- NEW: `admin/cbeta-dashboard.html`
  - 7 stat cards: catalog total, passages imported, translated, entity links, SAT, Toh, fuzzy
  - Progress bars: 5 metrics với color-coded fill
  - Chart.js bar chart: phân bố theo triều đại (top 8)
  - Table: top 10 places theo CBETA mention count (từ `/admin/cbeta/aggregates`)
  - "Làm mới" button gọi lại cả 2 API
- UPDATE: `admin/index.html` — thêm section "Đại Tạng Kinh" với link cbeta-dashboard.html

### T52c — Home Page Catalog Browser (Done — carried from earlier)
- UPDATE: `home.html` — tab Đại Tạng có catalog browser
  - Search, dynasty filter, paginated table (25/page), SAT external links

### T52d — Weekly Quality Snapshot (Done)
- NEW: `scripts/t52_weekly_quality_snapshot.py`
- Output: `docs/cbeta_quality_log.jsonl`
- Metrics: catalog, import coverage, SAT %, Toh %, fuzzy approval, vi_name confidence distribution

---

## Revert Guide

| Thay đổi | Cách revert |
|---|---|
| T49: DB (namevi_map_places + zqlocal_content) | `cp docs/sessions/2026-08-27/lineage_pre_T49.db.bak data/lineage.db` |
| T47: DB (zqlocal_content confidence) | `cp docs/sessions/2026-08-27/lineage_pre_T47.db.bak data/lineage.db` |
| custom_hanviet_override (T49) | DELETE WHERE added_by='T49-charmap-fix-2026-08-27' |
| Scripts | `git revert <commit-hash>` |
