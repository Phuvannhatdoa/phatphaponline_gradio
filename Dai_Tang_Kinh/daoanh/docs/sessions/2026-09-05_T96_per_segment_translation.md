# Session 2026-09-05 — T96 Per-Segment Translation System

**Task:** T96  
**Files:** `app.py` (backend), `daoanh/places.html` (frontend)  
**DB:** `translation_segments` (reuse T94 table) — additive, không xóa data cũ

---

## Bối cảnh

Passage `0-0457a-` (Thiếu Lâm Tự) có 59 segments trong `text_passages`.
Bản dịch Việt trước đây là 1 blob tổng không liên kết segment.
T96 implement dịch từng segment, lưu riêng, hiển thị bilingual.

---

## Backend (app.py)

### Routes mới

| Route | Method | Mô tả |
|-------|--------|-------|
| `/daoanh/api/segments/<canonical_ref>` | GET | Trả 59 segments + translation_status từng cái |
| `/daoanh/api/segments/translate` | POST | Dịch 1 segment bằng Groq, dedup, lưu translation_segments |

### Dedup logic

1. Kiểm tra `translation_status='done'` → trả `from_cache=True`
2. Kiểm tra `translation_status IN ('queued','translating')` → HTTP 409 `already_queued`
3. Nếu chưa có → INSERT queued → Groq call → UPDATE done/failed

### Groq key

Đọc từ `_llm_config_read()['groq_key']` trước, fallback `GROQ_API_KEY` env.

---

## Frontend (places.html)

### Functions mới

| Function | Mô tả |
|----------|-------|
| `dtTranslateSegment(unitId, pIdx)` | Dịch 1 segment, update badge, re-render |
| `dtTranslateNextN(n, pIdx)` | Dịch n segments missing theo thứ tự sequential |
| `dtAutoTranslate(pIdx)` | Auto-translate đầu 3 nếu < 3 đoạn đã dịch |

### UI changes

- Vi pane unit row: thêm `<button>Dịch</button>` cho missing/failed
- `in_progress` badge: hiển thị "⏳ Đang dịch…"
- `dtUnitActions`: thay batch job buttons → "🤖 Dịch 5 đoạn kế"
- Progress bar `#dt-seg-trans-progress` hidden/shown khi dịch batch
- Auto-translate trigger trong `dtLoadUnits` success handler

---

## Verify

```
GET /segments/0-0457a-: ok=True total=59 translated=1 (trước test)
POST /segments/translate p0001: ok=True status=done vi="Xin nghe. Sáu hào thăm dò..."
Dedup test: ok=True from_cache=True (không gọi Groq lại)
Browser: 59 units, 4 needs_review (auto-translate 3 + 1 trước), 58 "Dịch" buttons
"Dịch 5 đoạn kế" button: present
No console errors
```

---

## Rollback

```bash
git revert HEAD  # rollback UI + API
# DB: xóa T96 translations nếu cần:
# DELETE FROM translation_segments WHERE translator_type = 'ai_groq' AND translation_id LIKE 'ts-%'
```
