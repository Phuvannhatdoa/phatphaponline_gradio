---
id: T51
title: "Nhân Vật Học Portal — Person Biographies + Lineage Browsing"
module: Person Authority / Marcus SNA / UI
priority: high
status: in_progress
depends_on: [T04, T22.1, T28]
created: 2026-08-26
updated: 2026-08-28
done_when: >
  Home page có portal nhân vật — duyệt tăng ni theo triều đại/dòng truyền thừa/khu vực,
  hiển thị tiểu sử đầy đủ (people.bio), cây truyền thừa Marcus (marcus_networks),
  liên kết kinh điển + địa danh. Không ghi đè tab Nhân Vật/Truyền Thừa hiện có.
---

# T51 — Nhân Vật Học Portal

> **Lưu ý:** Task này được tạo mới 2026-08-26. Số T51 trước đây thuộc về
> "CBETA Content Enhancement" — đã được đổi thành T53.

## Mục tiêu
Biến đổi dữ liệu nhân vật (48K persons + Marcus SNA) thành portal duyệt độc lập cho Tăng/Ni học Phật.

## Hiện Trạng (Codebase)
- `people` table: 48,673 persons, `bio` column có tiểu sử đầy đủ từ DILA Authority
- `place_person_link` + `place_person_bibl` (T28/T40): nhân vật ↔ địa danh
- `marcus_networks` (11,169 edges) + `marcus_reference` (18,127): dòng truyền thừa thầy-trò
- `marcus_people_link` (18,121): bridge DILA ↔ Marcus
- Tab Nhân Vật/Truyền Thừa trên places.html — place-centric (đã tồn tại, KHÔNG ghi đè)
- API: `/daoanh/api/places/<id>/persons`, `/daoanh/api/monk/<id>/graph`

## Khoảng Trống (Gap)
- Không có portal duyệt nhân vật **độc lập** (từ trang chủ)
- Không có bộ lọc theo triều đại / dòng truyền thừa / khu vực
- Không có trang tiểu sử riêng (bio đầy đủ) cho từng nhân vật
- Data đang gắn chặt vào place-centric UI

## Subtasks

### T51a — Nhân Vật Portal Backend API
- Route mới: `GET /daoanh/api/persons/browse?dynasty=&lineage=&region=&q=&page=`
- Source: `people` + JOIN `people_dynasty` (nếu có), `place_person_link`, `marcus_people_link`
- Trả về: id, name_zh, name_vi, dynasty, birth/death, bio preview, has_marcus_lineage, place_count
- **KHÔNG đụng** route `/api/places/<id>/persons` hiện có

### T51b — Trang Tiểu Sử Nhân Vật
- Route: `GET /daoanh/api/person/<dila_id>/profile`
- Kết hợp: DILA bio + Marcus lineage + CBETA citations + địa danh liên quan
- Frontend: panel tiểu sử trên portal (không ghi đè bio Kinh Điển tab sẵn có)

### T51c — Bộ Lọc & Duyệt Trang Chủ
- Home page thêm section "🧑 Nhân Vật"
- Filters: triều đại (dropdown từ `dynasty`), dòng truyền thừa (Marcus), khu vực (địa danh)
- Kết quả dạng card: ảnh đại diện (nếu có) + tên Hán/Việt + triều đại + dòng

### T51d — Liên Kết Nhân Vật ↔ Kinh Điển
- Khi xem nhân vật → "Nhân vật này xuất hiện trong [N] kinh" (từ `passage_entity`/`person_mentions`)
- Liên kết `/daoanh/api/cbeta/<sigla>/person` tồn tại (CBETA Person Search)

### T51e — Phả Hệ Marcus Trong Portal
- Dùng lại `marcus_networks` + vis-network (đã có trong places.html)
- Mỗi profile nhân vật có sub-tab "Dòng Truyền Thừa" vẽ cây Marcus
- Click thầy/trò → nhảy đến profile khác

## API Changes
- New: `GET /daoanh/api/persons/browse`
- New: `GET /daoanh/api/person/<dila_id>/profile`

## Frontend
- Update: `home.html` — section Nhân Vật
- New: trình duyệt nhân vật + panel tiểu sử

## Không Xung Đột Với
- T28 (Nhân Vật/Truyền Thừa tabs — place-centric, giữ nguyên)
- T04 (marcus-glossaries-link — chỉ dùng dữ liệu, không sửa)
- T43 (bio cache — dùng lại, không rebuild)

## Estimated Effort: ~16 hours

---

## Build Log

### 2026-08-28 — Phase 1: Portal Browse + Profile (T51a/T51b/T51c/T51e) ✅
**Status chuyển `pending` → `in_progress`**

**Backend (app.py — 2 route mới, additive, read-only):**
- `GET /daoanh/api/persons/browse` (T51a) — đặt sau route `api_places_persons`
  - Filter: `q` (name_vi/zh/en LIKE), `dynasty` (chính xác), `sect`, `has_lineage` (1/0)
  - Sort: `name` | `dynasty` (mặc định) | `places`
  - Subquery không nhân dòng: `place_count`, `origin_count`, `has_lineage` (EXISTS marcus_people_link), `bio_preview` (substr 220)
  - Trả về `counts` (total_people, with_lineage) + `filters` (dynasties, sects)
  - **KHÔNG đụng** route `/api/places/<id>/persons` hiện có
- `GET /daoanh/api/person/<dila_id>/profile` (T51b)
  - Kết hợp: `people.bio` + Marcus lineage (teacher/student kèm CBETA `ref`) + địa danh (place_person_link + person_origin_link) + kinh điển (place_person_bibl)
  - Query phụ wrapped try/except (không fail khi thiếu bảng synthetic)

**Frontend (home.html):**
- `loadTabContent` — thêm nhánh `if (tab === 'persons') { loadPersonBrowser(contentArea) }` (giữ pattern catalog browser)
- T51c: `loadPersonBrowser` + `fetchPersons` + `renderPersonResults` — bộ lọc q/dynasty/has_lineage, bảng card nhân vật, phân trang
- T51e: `loadPersonProfile` + `renderPersonProfile` — tiểu sử đầy đủ, đồ thị truyền thừa (thầy/trò có citation), địa danh liên quan, kinh điển liên quan; `← Quay lại danh sách`

### 2026-08-28 — Phase 1b: T51d (Nhân vật ↔ Kinh điển) ✅
- Backend: thêm `mentions` vào `/daoanh/api/person/<id>/profile`
  - Query `cbeta_person_mentions` theo `dila_person_id` EXACT match (không fuzzy — content integrity)
  - GROUP BY `cbeta_text_sigla`, đếm số quyển (juan) mỗi kinh; giới hạn 50
  - Title tra từ `cbeta.db` (DB riêng) qua `get_cbeta_conn()` — đúng pattern endpoint admin sẵn có
  - Các query phụ wrap try/except (không fail cả profile khi thiếu bảng)
- Frontend (home.html): section "Nhân Vật Xuất Hiện Trong N Kinh" — chip sigla + title + số quyển

**Ghi chú triển khai:**
- Toàn bộ 5 subtask T51a-e đã code xong. Còn lại: verify runtime + git commit (blocker shell).
- **Blocker**: Shell/PowerShell vẫn không phản hồi (env-level) → chưa chạy `npm run pipeline` / chưa verify runtime. Cần admin chạy manual.

### 2026-08-28 — Phase 1c: Verify + Fix bug JavaScript 🐛
- **Verify home.html inline JS**: acorn + `node --check` → cả 2 script block đều parse OK. `npm run test` ✅, `scripts/e2e-test.js` ✅ (placevn, index, dashboard_process). `npm run lint` fail do quirk nguồn `get_format` (có sẵn, không liên quan T51). `app.py`: `ast.parse` OK.
- **Fix bug có sẵn (không thuộc T51):** home.html main script vốn KHÔNG parse được do block `clusters.forEach(cluster => {` (~dòng 84) thiếu `});` đóng — `});` tại dòng ~101 chỉ đóng `summary.addEventListener(...)`. Đã thêm `});` đóng forEach → script cân bằng (trước đó thừa `{`/`(` làm toàn bộ script sau bị nuốt sai context).
- **Trạng thái:** code hoàn chỉnh, parse/unit/e2e OK. Sẵn sàng commit T51.

