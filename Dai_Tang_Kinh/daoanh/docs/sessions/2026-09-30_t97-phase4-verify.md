# Session 2026-09-30 — T97 Phase 4: Verify Tab Niên Đại (places)

## Tasks hoàn thành

### T97 Phase 4 — E2E Verify Tab Niên Đại cho địa điểm
**Status:** ✅ VERIFIED (task đã `status: done` từ session trước)

**Bối cảnh:**
Session trước phát hiện routing bug: `/daoanh/places/` (trailing slash) serve `places/index.html` cũ (32KB)
thay vì `places.html` đầy đủ (685KB). Fix: dùng URL `/daoanh/places` (không có trailing slash).

**Kết quả verify tại `http://localhost:8080/daoanh/places`:**

| Kiểm tra | Kết quả |
|----------|---------|
| URL đúng | `/daoanh/places` (không trailing slash) → load `places.html` 685KB ✓ |
| Thiếu Lâm Tự (PL000000023255) | Load thành công, panel hiện đầy đủ info ✓ |
| Tab ⏱ Niên Đại click | Active, trigger `loadTimelineTab()` ✓ |
| `/api/places/PL000000023255/timeline` | 200 OK, trả SỰ KIỆN LỊCH SỬ 4 events (495 CE) ✓ |
| `/api/places/PL000000023255/time-mentions` | 200 OK, trả 4 mentions (477年, 495年×3) ✓ |
| Render section "NHẮC ĐẾN NIÊN ĐẠI (DILA RAW)" | Hiển thị đúng mentions với precision, CE năm ✓ |
| Empty state `PL000000099999/time-mentions` | `{ok:true, total:0, mentions:[]}` — không lỗi ✓ |

**Lỗi không liên quan T97:**
- `POST /api/place/PL023255/translate` → 500/503: Do Gemini API key hết hạn (T74 blocker, đã biết)

**Vấn đề data quality còn lại (không block task):**
- 98 reign_era time_mentions có `normalized_start = NULL` (query LIKE không match era_name format)
- Có thể fix sau trong scripts/t97_parse_time_mentions.py — bổ sung lookup era → year range

## Tasks đang dở

- T22 (in_progress): NLP Fosi Zhi Founding Dates — Layer B/C/E
- T34 (in_progress): Tam Tạng Integration — chờ admin OK xóa ~80 fake rows
- T50 (blocked): CBETA cleanup — cần Groq key
- T74 (blocked): Place Desc VI Gemini Translate — cần Gemini API key mới
- T95, T96 (in_progress): CBETA Translation Pipeline

## Todo tiếp theo

1. Fix reign_era NULL (98 rows) trong t97_parse_time_mentions.py nếu cần data quality cao hơn
2. Giải quyết T74 blocker (Gemini API key)
3. Xem xét T34 — xóa fake data sau khi admin confirm
