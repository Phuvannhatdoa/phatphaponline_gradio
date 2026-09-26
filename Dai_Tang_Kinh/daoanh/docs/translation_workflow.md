# Translation Workflow — 3-Layer Model

**Last updated:** 2026-05-21

---

## Overview

The translation system operates in 3 layers, from automatic → semi-automatic → manual.

| Layer | Method | Speed | Quality | User Editable? |
|-------|--------|-------|---------|----------------|
| **Layer 1: RAW** | DILA source (Chinese/Han text) | Instant | Source truth | No |
| **Layer 2: AUTO** | Transliteration + AI translation | Seconds | Approximate | Yes (copy to Layer 3) |
| **Layer 3: MANUAL** | Editor input in dashboard | Human-paced | Authoritative | Yes (primary editable field) |

---

## Layer 1: RAW (Chinese Source)

### Data Sources

| Field | Source | Example |
|-------|--------|---------|
| `name_zh` | DILA TEI `<placeName>` | 勝境關 |
| `raw_tei` | DILA TEI full XML | `<ns0:place>...</ns0:place>` |
| `district` | DILA `<district>` | 中國-雲南省-曲靖市-富源縣 |
| `country` | DILA parsed | China |

### Frontend Display

- `TRÍ THỨC GỐC (SQLITE VPS)` block → `parseTeiFields()` shows labeled fields:
  - Tên Hán chính / Tên Hán khác / Đơn vị hành chính / Tọa độ / Địa chỉ / Ghi chú gốc / Phân loại
- `DILA RAW (SQLITE)` panel → `sqliteInfo` shows raw `country`, `district`, `geo`

---

## Layer 2: AUTO (Transliteration + AI)

### A. Chinese → Han-Viet Transliteration

**Endpoint:** `GET /daoanh/api/public/transliterate?text=...`

1. Check cache (per-string)
2. Call `/transliterate` API
3. Apply `adminMapping` overrides:

```javascript
const adminMapping = {
  '中國': 'Trung Quốc', '中国': 'Trung Quốc',
  '省': 'Tỉnh ', '市': 'Thành phố ', '縣': 'Huyện ',
  '区': 'Quận ', '區': 'Quận ', '镇': 'Trấn ', '鎮': 'Trấn ',
  '村': 'Thôn ', '乡': 'Xã ', '鄉': 'Xã '
};
```

### B. District/Country Translation

**Function:** `processTransResult(rawText, countryHint)` (frontend)

1. Try backend `POST /daoanh/api/admin/parse_district` (rule-based)
2. Fallback: split by `-`, map Chinese→Vietnamese using `adminMapping`
3. Reorder: `long lat` → `lat, long`

**Example:**
```
Input:  中國-雲南省-曲靖市-富源縣
Output: 富源縣, 曲靖市, 雲南省, Trung Quốc
```

### C. Historical Context Translation

**Endpoint:** `POST /daoanh/api/admin/translate_context`

1. Source: `extractHanContextFromTei(rawTei)` → `<note>` + `<bibl>` content
2. Strip `<ns0:ref>` tags → keep URL/text
3. Send to Gemini 2.0 Flash (free tier)
4. Fallback: GoogleTranslator
5. Result displayed in `BỐI CẢNH LỊCH SỬ & KHẢO CỔ` block

### D. Lexicon-Based Suggestion

**Flow:** `ai_judge` endpoint → lexicon lookup

1. `suggest_api = han_name` (Chinese name)
2. Normalize → `key_norm` lookup in `lexicon` table
3. Skip self-match (Chinese term matching itself)
4. `definition LIKE` fallback if key_norm empty
5. API fallback if still empty
6. Return as `candidates` array with source flags: `[Lexicon]`, `[Hán]`, `[API]`

### E. Quick Transliterate Button

**Function:** `handleQuickTransliterate()`

1. Get `name_zh` → transliterate to `name_vi`
2. Get `raw_district` → `processTransResult()` → `district_vi`, `country_vi`
3. Auto-save generated name to `namevi_map_places`
4. Populate form fields (not editable after our fix)

---

## Layer 3: MANUAL (Editor Input)

### Editable Fields (only)

| Field | UI Element | Location |
|-------|-----------|----------|
| `Ghi chú Việt ngữ (do editor nhập)` | `<textarea>` | BỐI CẢNH block |

### Non-Editable Fields (readOnly as of 2026-05-20)

| Field | Reason |
|-------|--------|
| `name_vi` | Derived from transliteration + lexicon |
| `district_vi` | Derived from DILA RAW (自動 từ DILA) |
| `country_vi` | Derived from DILA RAW (自動 từ DILA) |
| `gps_lat` / `gps_long` | From DILA RAW |
| All DILA/TEI fields | Source truth |

### Save Flow

1. Admin enters `note_vi` + reviews `name_vi`
2. `POST /daoanh/api/admin/namevi-map-places/save`
3. Body: `{ dila_id, name_vi, name_zh, note_vi, district_vi, country_vi, source, needs_review }`
4. Upsert into `namevi_map_places`
5. Place removed from pending queue
6. Auto-advance to next place in queue

---

## Translation Quality Indicators

| Visual | Meaning |
|--------|---------|
| Green border | Has `district_vi` / filled |
| Dashed border | Empty / needs attention |
| `DỊCH TỰ ĐỘNG (GEMINI FREE):` label | Auto-translated historical context |
| `[Lexicon]` / `[Hán]` / `[API]` buttons | Clickable suggestion sources |
| `Nguồn CBDB` block | CBDB place data + nút "Dịch thô (LLM)" → textarea vi_draft (chưa auto-save) |
