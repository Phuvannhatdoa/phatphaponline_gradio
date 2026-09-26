---
id: T74
title: "Place Desc VI — Gemini Batch Translate DILA notes → Tiếng Việt"
module: Place Authority / Content
priority: medium
status: pending
depends_on: []
created: 2026-08-30
updated: 2026-08-30
done_when: ≥5,000 rows trong place_desc_vi_draft có desc_vi_draft tiếng Việt thực sự (không phải Hán/Anh); batch translate script hoạt động với rate limiting; admin có thể preview + approve
---

# T74 — Place Desc VI: Gemini Batch Translate

## Vấn đề

`place_desc_vi_draft` hiện có **14,000 rows** nhưng nội dung là tiếng Hán/Anh gốc từ
`places_dila.note`. Không phục vụ được người dùng Việt.

| Hiện tại | Mong muốn |
|----------|----------|
| 14,000 rows tiếng Hán/Anh | 14,000 rows tiếng Việt |
| desc_vi_draft = copy note gốc | desc_vi_draft = bản dịch tiếng Việt |
| 0 người dùng Việt đọc được | Người dùng Việt tra địa danh có mô tả |

## Gemini API

Đã có sẵn trong `app.py` lines 1065, 1105. Rate limit Gemini Flash free: ~15 RPM.
Batch 100 records/phiên = ~7 phút. Toàn bộ 14,000 rows = ~16 giờ tự động.

## Chiến lược

### Ưu tiên dịch

1. **note_category = '寺廟、佛塔、佛教文化地點'** (11,886 rows) — cao nhất
2. **note_category = '地點'** (3,459 rows)
3. Phần còn lại

### Prompt Gemini

```
Dịch đoạn mô tả sau về địa danh Phật giáo sang tiếng Việt học thuật.
Giữ tên riêng (chùa, núi, sông, nhân vật) theo phiên âm Hán-Việt.
Giữ năm tháng và số liệu nguyên bản.
Ngắn gọn, súc tích. Tối đa 300 từ.

Tên địa danh: {name_zh} ({name_vi})
Loại: {note_category}
Văn bản gốc:
{note_text}
```

### Script cần viết

`scripts/t74_gemini_translate_places.py`

```
python t74_gemini_translate_places.py --dry-run --limit 10   # xem mẫu 10
python t74_gemini_translate_places.py --apply --limit 100    # dịch 100 rows
python t74_gemini_translate_places.py --apply --all          # dịch toàn bộ (overnight)
python t74_gemini_translate_places.py --stats                # trạng thái hiện tại
```

## Acceptance Criteria

- [ ] Script với --dry-run / --apply / --limit / --stats
- [ ] Rate limiting: 1 request/4s (≤15 RPM, tránh 429)
- [ ] Retry on 429 với exponential backoff
- [ ] Resume: skip rows đã có desc_vi_draft tiếng Việt (detect bằng ký tự Hán)
- [ ] ≥5,000 rows translated (batch 1 overnight)
- [ ] Log `data/t74_translate_log.json` với progress
- [ ] Admin có thể xem translated content trong admin page

## Note kỹ thuật

Gemini API key hardcoded trong app.py — cần đọc từ đó hoặc dùng biến môi trường.
Script KHÔNG import app.py — tự đọc key từ config/env.

Detect "đã dịch": check `desc_vi_draft` có chứa ký tự `[^\x00-ɏḀ-ỿ]`
(ngoài Latin + Latin Extended) → nếu có nhiều Hán tự thì chưa dịch.

## Rollback

```sql
UPDATE place_desc_vi_draft
SET desc_vi_draft = NULL, updated_at = datetime('now')
WHERE desc_source = 'gemini_translate';
```

Hoặc đơn giản chạy lại T66 script để reset về DILA note gốc.

## Liên quan

- T66 (done): tạo 14,000 rows với DILA note gốc (tiếng Hán)
- T73 (pending): admin review UI — có thể dùng chung UI để review place_desc cũng
- Gemini key: `app.py` line 1065
