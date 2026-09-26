---
id: T96
title: "Per-Segment Translation System"
module: CBETA Reader / Translation Engine
priority: high
status: in_progress
depends_on: [T94, T95]
created: 2026-09-05
updated: 2026-09-05
done_when: >
  Mỗi text_passages segment có thể được dịch độc lập qua API;
  frontend hiển thị bilingual pairs (Han + Vi) theo từng segment;
  "Dịch 5 đoạn kế" button hoạt động;
  bản dịch lưu vào translation_segments với passage_id FK;
  không có duplicate translation jobs.
---

# T96 — Per-Segment Translation System

## Bối cảnh

**Vấn đề hiện tại:**
- T95 đã import 9,316 text_passages vào DB (từ CBETA T50n2060)
- Passage `0-0457a-` (Thiếu Lâm Tự) có 59 segments đánh số
- Bản dịch Việt hiện tại là 1 blob tổng trong `passage.vi_text` — không liên kết đến segment nào
- `translation_segments` table đã có FK `passage_id → text_passages.passage_id` nhưng rỗng

**Mấu chốt:** Dịch, lưu, hiển thị và theo dõi tiến độ đều phải dùng cùng 1 đơn vị là **segment** (`text_passages` row).

## Data flow

```
text_passages (9316 rows, passage_id = daoanh:cbeta:T50n2060:0457a:p0001)
    ↓ translate per segment (Groq API)
translation_segments (0 rows hiện tại)
    ↓ display
places.html DaiTang reader — fulltext tab
```

## Status machine

`translation_segments.translation_status`:
```
pending → queued → translating → done
                              → failed → queued (retry)
done → reviewed (sau khi admin verify)
```

## Acceptance criteria

- [ ] API `GET /daoanh/api/passages/<passage_id>/segments` trả về 59 segments + status từng cái
- [ ] API `POST /daoanh/api/passages/<passage_id>/translate-next` dịch 1 segment pending tiếp theo
- [ ] Prompt per-segment strict: chỉ dịch đoạn mục tiêu, không gộp, không suy diễn
- [ ] Job dedup: không tạo 2 jobs cho cùng 1 segment đang `queued/translating`
- [ ] Frontend: hiển thị bilingual pairs theo thứ tự sequence_no
- [ ] Auto-translate 3 segments đầu khi mở passage lần đầu (chưa có bản dịch)
- [ ] "Dịch 5 đoạn kế" button + progress indicator
- [ ] Status badge: ⏳ pending / 🔄 translating / ✅ done / ❌ failed / 👤 reviewed
- [ ] Bản dịch toàn phần (legacy blob) collapse vào accordion
- [ ] Rollback: git revert hoặc disable endpoint

## Schema (dùng lại translation_segments từ T94)

```sql
-- translation_segments đã có cols cần thiết:
-- passage_id TEXT → FK text_passages.passage_id
-- translation_text TEXT
-- translation_status TEXT DEFAULT 'draft'
-- translator_type TEXT (sẽ set = 'ai_groq')
-- model_name TEXT
-- prompt_version TEXT
-- created_at, updated_at DATETIME

-- Không cần tạo bảng mới — dùng translation_segments với:
-- passage_id = 'daoanh:cbeta:T50n2060:0457a:p0001'
-- translation_status ∈ {pending, queued, translating, done, failed, reviewed}
```

## API spec

### GET /daoanh/api/passages/<canonical_ref_encoded>/segments

Params: `canonical_ref` = loc_ref (e.g. `0-0457a-`), URL-encoded

Response:
```json
{
  "ok": true,
  "canonical_ref": "0-0457a-",
  "total": 59,
  "translated": 3,
  "segments": [
    {
      "passage_id": "daoanh:cbeta:T50n2060:0457a:p0001",
      "sequence_no": 1033,
      "original_zh": "竊聞...",
      "translation_id": "ts-abc123",
      "translation_vi": "...",
      "translation_status": "done",
      "model_name": "qwen/qwen3-8b"
    },
    {
      "passage_id": "daoanh:cbeta:T50n2060:0457a:p0002",
      "sequence_no": 1034,
      "original_zh": "...",
      "translation_id": null,
      "translation_vi": null,
      "translation_status": "pending"
    }
  ]
}
```

### POST /daoanh/api/passages/translate-segment

Body: `{"passage_id": "daoanh:cbeta:T50n2060:0457a:p0001"}`

Response:
```json
{
  "ok": true,
  "passage_id": "...",
  "translation_id": "ts-xyz",
  "translation_vi": "...",
  "model_name": "qwen/qwen3-8b",
  "status": "done"
}
```

Error (duplicate):
```json
{"ok": false, "error": "already_queued", "translation_id": "ts-existing"}
```

## Prompt per-segment (strict)

```
Bạn là dịch giả Hán-Việt chuyên ngành Phật học. Dịch đoạn Hán văn sau sang tiếng Việt.

Quy tắc:
- Chỉ dịch đoạn này, không giải thích, không thêm thông tin ngoài
- Giữ nguyên tên riêng Hán-Việt phổ thông (Thiếu Lâm, Bồ Đề Đạt Ma, v.v.)
- Không dịch passage_id
- Trả về JSON: {"translation_vi": "..."}

Đoạn {sequence_no}/{total} — {canonical_ref}:
{original_zh}
```

## Frontend spec

Trong fulltext tab (`#dt-tab-fulltext`), thay thế block Vi:

```
[Hán đoạn 01] 竊聞六爻...          [✅ Tiểu đoạn đã dịch]
[Vi  đoạn 01] Nghe rằng sáu quẻ... 

[Hán đoạn 02] 自古聖人...          [⏳ Chưa dịch]
[Vi  đoạn 02] [button: Dịch đoạn này]

...

[▼ Bản dịch toàn phần (cũ)] (collapsed accordion, legacy vi_text blob)
[button: Dịch 5 đoạn kế tiếp]  [progress: 3/59]
```

## Implementation phases

### Phase A — Backend API (app.py)
- GET segments endpoint
- POST translate-segment endpoint  
- Groq API call per-segment với strict prompt
- Dedup check (translation_status = queued/translating)

### Phase B — Frontend UI (places.html)
- `dtRenderSegments(segments)` — bilingual pairs
- Auto-translate 3 segments đầu
- Status badges
- "Dịch 5 đoạn kế" button + `dtTranslateNext(n)`
- Legacy blob → collapsible

## Rollback

```bash
git revert HEAD  # rollback UI changes
# API endpoints: đơn giản là bỏ qua, không ảnh hưởng data cũ
# DB: translation_segments rows có thể xóa nếu cần:
# DELETE FROM translation_segments WHERE translator_type = 'ai_groq' AND passage_id LIKE 'daoanh:cbeta:%'
```
