# Session Changes 2026-09-20

## Files modified

### daoanh/app.py

**Task H — Fix tab Nhân Vật hiển thị bio_vi stale (mismatch với admin Dashboard)**

Root cause: `api_places_persons` (Source 1 + Source 3) đọc `p.bio_vi` từ bảng `people` trực tiếp.
Khi admin re-translate (POST `/api/person/<id>/translate`) → `translation_cache` cập nhật version mới nhưng
`people.bio_vi` KHÔNG được cập nhật (vì điều kiện `AND (bio_vi IS NULL OR bio_vi='')` trong update query).
→ NHÂN VẬT tab hiển thị bản cũ từ `people.bio_vi`, admin Dashboard hiển thị bản mới từ `translation_cache` → mismatch.

**Fix: Option B — đọc từ `translation_cache` thay vì `people.bio_vi` trong 2 queries:**

1. **Source 1** (line ~6406, curated `place_person_link`):
   - Cũ: `p.bio_vi` trong SELECT
   - Mới: `COALESCE((SELECT tc.translated_text FROM translation_cache tc WHERE tc.entity_id = l.person_id AND tc.source_type = 'person_bio' AND tc.status != 'invalidated' ORDER BY tc.id DESC LIMIT 1), p.bio_vi) AS bio_vi`

2. **Source 3** (line ~6451, `place_person_bio_cache`):
   - Cũ: `p.bio_vi` trong SELECT  
   - Mới: COALESCE correlated subquery như Source 1 (với `ppbc.person_id`)

Lý do chọn Option B thay vì Option A (fix sync condition):
- Option A chỉ hoạt động khi POST translate được gọi; nếu admin chỉ xem (GET) mà không dịch lại, `people.bio_vi` vẫn stale
- Option B luôn đọc từ nguồn mới nhất, không phụ thuộc vào việc có POST hay không
- Không có rủi ro overwrite admin-edited bio

## Verified

- ✅ `GET /daoanh/api/places/PL000000023255/persons` → A001361 `bio_vi` length = 639, text = "Ngài là vương tử nước Hương Chí thuộc Nam Thiên Trúc..."
- ✅ `GET /daoanh/api/person/A001361/translate` → `bio_vi` length = 639, cùng text
- ✅ Hai endpoint đồng bộ: NHÂN VẬT tab và admin Dashboard hiển thị cùng bản dịch
- ✅ Tab NHÂN VẬT `places.html?fly=34.5885,112.9343&select=PL000000023255` → card Bồ Đề Đạt Ma hiển thị bio tiếng Việt đầy đủ, khớp admin Dashboard

---

## Task I — AI Dịch places.html: chỉ dịch tiểu sử, không lưu vào DB cho admin

**Hai vấn đề:**
1. places.html "🌐 AI Dịch" gọi `/translate` (bio-only) → các phần khác (Thầy = teacher relations, Ghi chú năm tháng) vẫn để hán tự
2. Bản dịch lưu vào `translation_cache` với `source_type='person_bio'` → admin/person.html tìm `source_type='dila_card'` (từ `/dila_translate`) → không thấy "phần đã dịch"

**Fix A** (`api_person_dila_full` — app.py line ~16568):
- Thêm lookup `people.name_vi` cho mỗi relation trong relations list
- Trả về `name_vi` cùng với `name` (Hán) cho teacher/student names
- DB query: `SELECT id, name_vi FROM people WHERE id IN (?,...)`

**Fix B** (`_renderDilaExtra` — places.html line ~5927):
- Cũ: `_escHtml(r.name || r.person_id)` → hiển thị tên Hán
- Mới: `_escHtml(r.name_vi || r.name || r.person_id)` → hiển thị tên Việt (nếu có), kèm tên Hán trong ngoặc
- Kết quả: A009460 teachers → "Thạch Đầu Hy Thiên (希遷)", "Tiên Kính Sơn Hòa Thượng (道欽)"

**Fix C** (`doPersonTranslate` — places.html line ~8171):
- Cũ: POST `/translate` → chỉ lưu `source_type='person_bio'`
- Mới: POST `/dila_translate` trước (dịch toàn bộ DILA card: bio, relations, active_at, listbibl) → lưu `source_type='dila_card'`
- Fallback: nếu `/dila_translate` trả về 404 (không có DILA XML) → fallback sang `/translate`
- Card hiển thị `vi.bio_concise_vi` thay vì `d.bio_vi`

## Verified (Task H + Task I)

- ✅ Task H: `api_places_persons` Sources 1+3 dùng COALESCE từ translation_cache → NHÂN VẬT tab đồng bộ với admin Dashboard
- ✅ Task I Fix A: `GET /api/person/A009460/dila_full` → `relations[0].name_vi = "Thạch Đầu Hy Thiên"`
- ✅ Task I Fix B: `_renderDilaExtra` hiển thị "Thạch Đầu Hy Thiên (希遷)" thay vì "希遷"
- ✅ Task I Fix C: Click "🌐 AI Dịch" cho Nhị Tổ (A003881) → POST `/dila_translate` → 200 OK → saved
- ✅ GET `/api/person/A003881/dila_translate` → `{from_cache: true, vi.bio_concise_vi: "Tục họ Cơ, là Nhị Tổ..."}`
- ✅ Card Nhị Tổ trong NHÂN VẬT tab hiển thị bio tiếng Việt sau khi nhấn AI Dịch

---

## Task J — Fix `_linDichAI` trong lineage inspector: mở rộng phạm vi dịch

**Vấn đề:** Nút "AI Dịch" trong lineage inspector (tiểu sử DILA) chỉ gọi `/translate` (bio-only, lưu `source_type='person_bio'`) → admin/person.html không thấy "BẢN DỊCH TIẾNG VIỆT" vì tìm `source_type='dila_card'`; các field khác (active_at, mentioned_in, works, occupation) vẫn hiện Hán tự.

**Fix D** (`_linDichAI` — places.html line 5798):
- Cũ: POST `/translate` → chỉ cập nhật `#lin-bv-view` với `d.bio_vi`
- Mới: POST `/dila_translate` → lưu `source_type='dila_card'` vào DB → cập nhật `#lin-bv-view` với `vi.bio_concise_vi` → gọi `_loadDilaExtra(pid)` để re-render toàn bộ inspector với bản dịch
- Fallback: nếu `/dila_translate` trả lỗi (không có DILA XML) → fallback POST `/translate` (bio-only)

**Fix E** (`_loadDilaExtra` — places.html line 5836):
- Cũ: chỉ fetch `dila_full`, gọi `_renderDilaExtra(el2, d)`
- Mới: `Promise.all([dila_full, dila_translate GET])` → truyền `vi = tv.vi` xuống render
- `bioExtText` ưu tiên `vi.bio_extensive_vi` nếu có, kèm flag 🇻🇳 trong label

**Fix F** (`_renderDilaExtra` — places.html line 5869):
- Thêm tham số `vi` (default `{}`)
- occupation → `vi.occupation_vi || d.occupation` + label 🇻🇳
- place_of_origin → `vi.place_of_origin_vi || d.place_of_origin` + label 🇻🇳
- bio_extensive → `vi.bio_extensive_vi || d.bio_extensive` + label 🇻🇳
- works_tripitaka → `vi.works_tripitaka_vi || d.works_tripitaka` + label 🇻🇳
- works_by → `vi.works_by_vi || d.works_by` + label 🇻🇳
- mentioned_in → `vi.mentioned_in_vi` (ưu tiên trước `mentioned_in_refs`, trước `d.mentioned_in`) + label 🇻🇳
- active_at → `vi.active_at_vi || d.active_at` + label 🇻🇳

**Kết quả:**
- Click "AI Dịch" trong lineage inspector → POST `/dila_translate` → lưu vào DB
- Inspector re-load với tất cả field dịch sang tiếng Việt (có badge 🇻🇳)
- admin/person.html lần sau GET thấy `from_cache=true` → hiện "BẢN DỊCH TIẾNG VIỆT"
- Lần sau mở inspector: `_loadDilaExtra` auto GET `/dila_translate` → hiện bản dịch cached ngay mà không cần click nữa

## Session context

- Tiếp nối 2026-09-18 (Task G: fix mentioned_in_refs)
- Task H: NHÂN VẬT tab stale bio_vi — hoàn thành 2026-09-20
- Task I: AI Dịch toàn bộ DILA card + lưu DB — hoàn thành 2026-09-20
- Task J: Fix lineage inspector AI Dịch → dịch toàn bộ DILA fields — hoàn thành 2026-09-20
