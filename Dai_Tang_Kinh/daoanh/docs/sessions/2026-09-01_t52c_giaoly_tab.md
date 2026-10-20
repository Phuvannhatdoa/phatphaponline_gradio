# Session 2026-09-01 — T52c/T52d: Giáo Lý Tab Đối Chiếu Tam Tạng

## Tóm tắt

Implement tab Giáo Lý trong `places.html` với UI so sánh kinh điển Tam Tạng.

## Thay đổi

### places.html

**loadTabData** (line 1089): `renderGiaolyTab(null)` → `renderGiaolyTab({ placeId })`

**renderGiaolyTab** (thay stub `_renderPendingTab`):
- Async, render input CBETA + nút "So Sánh"
- Auto-suggest từ `/daoanh/api/places/<id>/pali` nếu có Pali ref
- Enter key listener

**giaolyCbetaCompare(siglaSuggested)**:
- Fetch `GET /daoanh/api/cbeta/<sigla>/compare?lang=vi`
- Build tab ngang theo `ORDER = ['han','pali','tang','sat','parallels']`
- Mỗi tradition: badge_label chip + ref_code + link ↗ + title + text/preview + 📌 note

**giaolySwitchTrad(trad)**:
- Switch active tab (cyan border + color)

**Bug fix**: `v.source_label` → `v.badge_label` (API trả `badge_label`)

**T52d**: thêm `v.note` block (📌) — render PTS note cho Pali versions

**Placeholder typo fix**: "Chọn địa Gang" → "Chọn địa danh"

## Test kết quả

- T0251 (Tâm Kinh): 4 versions — Pali/藏/SAT/DharmaNexus
- Pali: badge "Pali tham chiếu", title "Prajñāpāramitā Hṛdaya", note "Tâm Kinh — không có tương đương Pali Nikāya..."
- Tab switch: 藏 → "Bát Nhã Ba La Mật Đa Tâm Kinh", link 84000.io

## Commits

- `962e0a7` feat(T52c): Giáo Lý tab — Đối Chiếu Tam Tạng UI
- `109d627` fix(T52c/d): badge_label + PTS note render
