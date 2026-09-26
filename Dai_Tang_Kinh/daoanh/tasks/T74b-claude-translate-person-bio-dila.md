---
id: T74b
title: "Person Bio VI — Claude Haiku Batch Translate DILA bio → Tiếng Việt"
module: DILA Authority
priority: high
status: blocked
depends_on: [T73]
created: 2026-08-31
updated: 2026-08-31
done_when: ≥20,000 rows trong person_bio_vi_draft có bio_vi_draft tiếng Việt thực sự từ DILA (source='claude_haiku'); script hoạt động rate-limit + resume; admin bulk-approve ≥5,000 rows; copy sang people.bio_vi
---

# T74b — Person Bio VI: Claude Haiku Batch Translate DILA

## Vấn đề

`people.bio` có **48,180 rows** tiểu sử tiếng Hán từ DILA — 98.9% coverage.  
`people.bio_vi` = 0 rows — người dùng Việt không đọc được tiểu sử nào.

T63/T65 chỉ match được 2,093 bios từ từ điển Việt (4.3%) — **không phải dịch DILA, không scale được**.

T74b dịch trực tiếp `people.bio` (Hán DILA) → `person_bio_vi_draft` bằng Claude Haiku.

## Lý do chọn Claude Haiku (không phải Gemini)

| Tiêu chí | Claude Haiku | Gemini Flash |
|---|---|---|
| Hán-Việt Phật học | ✅ Chuẩn, nhất quán | ⚠️ Đôi khi mix Pinyin |
| Văn phong hàn lâm | ✅ Đúng tông Phật học | ⚠️ Đôi khi hiện đại quá |
| Tên tu sĩ nổi tiếng | ✅ Huệ Năng, Huyền Trang đúng | ⚠️ Có thể sai với ít biết |
| Model stability | ✅ Anthropic không deprecate đột ngột | ❌ Google đã deprecate 3 model trong 1 năm |
| Chi phí 48k bios | ~$23 (Haiku 4.5) | Free nhưng key bị leak |

## Chiến lược

### Bước 1 — Lọc bios có giá trị (~20-25k rows)

```sql
SELECT id, name_zh, name_vi, dynasty, bio
FROM people
WHERE bio IS NOT NULL
  AND LENGTH(bio) > 80
  AND bio NOT GLOB '*http*'       -- loại bỏ bios chỉ có URL
  AND source_origin = 'DILA'
ORDER BY LENGTH(bio) DESC
```

Bỏ qua bios chỉ có trích dẫn thư mục (URL, ký hiệu) — không có nội dung dịch.

### Bước 2 — Claude Haiku dịch (không inject tên từ DB)

**Lý do không inject tên_vi từ DB:** `name_vi` hiện tại là auto-transliterate (confidence 0.5)  
— có thể sai. Claude đã biết tên nổi tiếng (Huệ Năng, Huyền Trang, Đạt Ma) từ training data.  
Inject tên sai sẽ làm bản dịch sai.

**Prompt:**
```
Dịch đoạn tiểu sử Phật học sau sang tiếng Việt học thuật.
Dùng phiên âm Hán-Việt chuẩn cho tên riêng.
Giữ nguyên năm tháng, số liệu, ký hiệu tông phái.
Văn phong trang trọng, súc tích.

Nhân vật: {name_zh} ({dynasty})
---
{bio}
```

### Bước 3 — Lưu vào person_bio_vi_draft

```sql
INSERT OR IGNORE INTO person_bio_vi_draft
  (person_id, name_vi, name_zh, bio_vi_draft, source_name, match_type, char_count)
VALUES (?, ?, ?, ?, 'claude_haiku_dila', 'ai_translate', ?)
```

Không overwrite rows đã có `admin_approved=1`.

### Bước 4 — Admin bulk-approve qua T73 UI

`/daoanh/admin/bio-review` đã có bulk-approve. Admin duyệt batch theo dynasty/sect.

### Bước 5 — Copy sang people.bio_vi

```bash
python scripts/t73_copy_approved_bio_vi.py --apply
```

## Script cần viết

`scripts/t74b_claude_translate_bios.py`

```
python t74b_claude_translate_bios.py --dry-run --limit 10   # xem 10 mẫu
python t74b_claude_translate_bios.py --apply --limit 100    # dịch 100 rows test
python t74b_claude_translate_bios.py --apply --all          # dịch toàn bộ (overnight)
python t74b_claude_translate_bios.py --stats                # trạng thái hiện tại
```

## Chi phí ước tính

| Hạng mục | Số lượng | Đơn giá | Tổng |
|---|---|---|---|
| Input: 22k bios × 150 tokens | 3.3M tokens | $0.80/MTok | ~$2.6 |
| Output: 22k bios × 200 tokens | 4.4M tokens | $4.00/MTok | ~$17.6 |
| **Tổng** | | | **~$20** |

Model: `claude-haiku-4-5-20251001` (Haiku 4.5 — latest)  
Rate limit: 1 request/2s (≤30 RPM, Haiku tier thường cao hơn)

## Blockers

- **BLOCKER:** Cần Claude API key từ `console.anthropic.com` (khác với Claude Code Pro subscription)
- Gemini API key cũ đã bị Google block (leaked) — không dùng được
- Sau khi có key: đặt vào `.env` hoặc env var `ANTHROPIC_API_KEY`; **KHÔNG hardcode vào app.py**

## Rollback

```sql
DELETE FROM person_bio_vi_draft
WHERE source_name = 'claude_haiku_dila' AND admin_approved = 0;
```

Hoặc dùng flag `--revert` trong script.

## Liên quan

- T63/T65 (done): bios từ từ điển Việt — 2,093 rows, giữ nguyên (nguồn khác)
- T73 (done): admin review UI — dùng lại để approve T74b output
- T74 (pending): tương tự nhưng cho place_desc_vi_draft (cũng cần API key mới)
- Sau T74b: xây `translation_glossary` verified — correction từ admin → feed vào future translations

## Acceptance Criteria

- [ ] Script với --dry-run / --apply / --limit / --stats / --revert
- [ ] Rate limiting: 1 request/2s, retry on 429 với exponential backoff
- [ ] Resume: skip rows đã có bio_vi_draft (source='claude_haiku_dila')
- [ ] Lọc đúng: bỏ bios chỉ có URL/trích dẫn (LENGTH > 80, no http)
- [ ] ≥20,000 rows translated (batch overnight)
- [ ] Log `data/t74b_translate_log.json` với progress + errors
- [ ] Admin bulk-approve ≥5,000 rows qua T73 UI
- [ ] `people.bio_vi` có ≥5,000 rows sau copy
