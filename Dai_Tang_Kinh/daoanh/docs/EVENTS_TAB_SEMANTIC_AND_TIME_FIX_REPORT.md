# EVENTS TAB — Semantic & Time Fix Report

**Date:** 2026-09-06  
**Scope:** Tab ⚡ Sự Kiện trong `places.html` — sửa nhãn sai và phân loại semantic đúng  
**Affected file:** `places.html` — function `renderSukienTab(d)` (lines ~6296–6375)  
**Backup:** `docs/sessions/2026-09-06/places.html.bak`

---

## 1. Audit (Bước 1 — Không sửa DB)

### API endpoint

```
GET /daoanh/api/places/<place_id>/events
```

Định nghĩa tại `app.py` line 6274. Trả về:

```json
{
  "ok": true,
  "dila_id": "PL000000023255",
  "total": 55,
  "nexus_events": [...],   // 24 rows từ nexus_events (cbeta_co_mention)
  "text_links": [...]      // 31 rows từ event_text_link (event_type='person_place')
}
```

### Dữ liệu thực tế cho PL000000023255 (少林寺 / Thiếu Lâm Tự)

| Nguồn bảng | Số rows | event_year |
|---|---|---|
| `nexus_events` (cbeta_co_mention) | 24 | NULL toàn bộ |
| `event_text_link` (person_place) | 31 | NULL toàn bộ |
| **Tổng** | **55** | — |

### Điều tra 4 records user báo cáo (ppb:6248, ppb:6250, T50n2061_p0767c03, T50n2061_p0781c28)

Kết quả query DB xác nhận:
- 4 records này **KHÔNG thuộc** PL000000023255 (Thiếu Lâm Tự)
- Thuộc **PL000000017997** (南安 / Nam An)
- `A001536` = Đạo Thông / 道通, `A003677` = Chân Giác / 真覺 (alias Nghĩa Tồn / 義存)
- `ppb:6248` / `ppb:6250` là nexus_events entries (co-mention level)
- `T50n2061_p0767c03` / `T50n2061_p0781c28` là event_text_link entries (exact CBETA ref)
- Không phải duplicate của nhau — là 2 loại citation khác nhau cùng person+place

### Phân loại toàn bộ 55 rows PL000000023255 theo ui-evidence-rules.md

| Kind | Count | Nguồn |
|---|---|---|
| `dated_event` | 0 | — |
| `undated_event` | 0 | — |
| `place_person_relation` | 31 | `event_text_link`, event_type='person_place' |
| `textual_mention` | 24 | `nexus_events`, evidence_type='cbeta_co_mention' |
| `unresolved` | 0 | — |
| Duplicate | 0 | 2 citation type khác nhau, không trùng |

---

## 2. Root Cause Bug

`renderSukienTab()` trong `places.html` có 3 lỗi semantic:

**Lỗi 1 — Header sai:**
```javascript
// CŨ (SAI):
html += '<div ...>Sự Kiện Liên Quan</div>';
```
"Sự Kiện Liên Quan" ngụ ý có sự kiện lịch sử xảy ra tại địa danh. Thực tế toàn bộ 55 rows là textual_mention / place_person_relation — đây là co-mention trong kinh điển, không phải event.

**Lỗi 2 — Count subtitle sai:**
```javascript
// CŨ (SAI):
html += `<div ...>${total} sự kiện có bằng chứng kinh điển</div>`;
```
Gọi textual_mention và place_person_relation là "sự kiện" vi phạm ui-evidence-rules.md.

**Lỗi 3 — Footer text sai:**
```javascript
// CŨ (SAI):
html += '...mọi sự kiện trỏ về passage/ref cụ thể.';
```

---

## 3. Fix Applied (Bước 2)

### Thay đổi trong `renderSukienTab(d)`:

**Phân loại semantic:**
```javascript
const textualMentions = d.nexus_events || [];  // cbeta_co_mention → textual_mention
const placeRelations = d.text_links || [];      // person_place → place_person_relation
const mentionCount = textualMentions.length + placeRelations.length;
const eventCount = 0;  // dated/undated events: 0 trong data hiện tại
```

**Header conditional:**
```javascript
const headerTitle = eventCount > 0 ? 'Sự Kiện Liên Quan' : 'ĐỀ CẬP TRONG KINH ĐIỂN';
const headerSub = eventCount > 0
    ? `${eventCount} sự kiện đã xác minh · Nguồn: CBETA`
    : `${mentionCount} trích dẫn có liên hệ với địa danh này · Nguồn: CBETA`;
```

**Badge trong mỗi card:**
```
[Đề cập trong văn bản]
```
Thêm vào đầu chip row của cả hai section (textualMentions + placeRelations).

**Thời gian không xác định:**
```
Thời gian: Chưa xác định từ nguồn hiện có.
```
Hiển thị khi `event_year` / `year` là NULL — thay vì bỏ trống hoặc hiển thị không có.

**Footer:**
```
Nguồn: CBETA · evidence-first — mọi trích dẫn trỏ về passage/ref cụ thể.
```

### Backward compatible:
- Khi DB sau này có dated_event / undated_event: `eventCount > 0` → header tự chuyển sang "Sự Kiện Liên Quan"
- Section labels giữ nguyên: "Tăng Nhân Đề Cập Trong Kinh Điển" (nexus) / "Trích Dẫn Kinh Điển Cụ Thể" (text_links)
- Không sửa DB, không sửa API

---

## 4. Files Changed

| File | Action |
|---|---|
| `places.html` | Fix `renderSukienTab()` lines 6296–6375 |
| `docs/sessions/2026-09-06/places.html.bak` | Backup bản gốc |
| `docs/EVENTS_TAB_SEMANTIC_AND_TIME_FIX_REPORT.md` | Report này |

---

## 5. Constraints Tuân Thủ

- KHÔNG sửa DB / raw data
- KHÔNG bịa fact, KHÔNG suy diễn từ tên người/tên sách
- KHÔNG làm hỏng tab/place khác (chỉ sửa function `renderSukienTab`)
- KHÔNG chạy git add/commit/push
- Query SQLite dùng Python (không dùng PowerShell sqlite)
