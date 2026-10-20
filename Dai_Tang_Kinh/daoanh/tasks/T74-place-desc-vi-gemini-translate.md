---
id: T74
title: "Place Desc VI — Groq Batch Translate DILA notes → Tiếng Việt"
module: Place Authority / Content
priority: medium
status: done
depends_on: []
created: 2026-08-30
updated: 2026-09-28
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

---

# 🚀 BUILD — 2026-09-28 · T74-BUILD — REBUILD Groq (đã done)

## Phát hiện audit (thay đổi premise so với SPEC 2026-08-30)

| Cũ (SPEC) | Mới (thực tế audit) |
|-----------|---------------------|
| Gemini API (app.py 1065/1105) | **Key chết 403/404 (T50)** → chuẩn hoá **Groq `qwen/qwen3.8-27b`** |
| `scripts/t74_gemini_translate_places.py` | **`scripts/t74_groq_translate_places.py`** (đã build + test) |
| Resume bằng detect Hán trong desc_vi_draft | Resume bằng **marker `desc_source='t74_groq'`** (đáng tin, 1 query) |
| Rollback `WHERE desc_source='gemini_translate'` | Rollback **restore `places_dila.note`** qua `UPDATE ... FROM places_dila` |
| `batch_translate_places.py` cũ (Gemini) | Bỏ — không dùng |

## Script: `scripts/t74_groq_translate_places.py`

- Rút từ skeleton hardened T169/T170: **batch 25 · `:cursor` · RPM adaptive
  (≤5 → 3.0s, else 2.2s ~27 RPM < 30) · retry 429/5xx backoff · atomic `with con` ·
  mock/limit/force**.
- Prompt: self-contained (name_zh/name_vi + note_category + văn bản gốc ≤4000 chars);
  giữ tên riêng Hán-Việt, giữ ngày/số, thuần Việt, ≤300 từ, KHÔNG Hán tự/Hán/latin.
- Guard chất lượng: output còn **Hán tự → `still_han`, huỷ, giữ bản gốc**
  (không ghi đè dữ liệu sai); `empty`, `too_long` tương tự.
- Ghi: `desc_vi_draft=VI`, `desc_source='t74_groq'`, `char_count`, `updated_at`.
  Bản gốc KHÔNG mất — phục hồi từ `places_dila.note` (place_id = id).
- `PLand`: 0 schema change (không thêm cột).

## CLI

```
python scripts/t74_groq_translate_places.py --stats          # trạng thái
python scripts/t74_groq_translate_places.py --samples=5      # preview mẫu row chưa dịch
python scripts/t74_groq_translate_places.py --dry-run=10     # xem row sẽ xử lý
python scripts/t74_groq_translate_places.py --mock --limit=5 # smoke khô (DB temp)
python scripts/t74_groq_translate_places.py --limit=100      # dịch 100 row
python scripts/t74_groq_translate_places.py                  # dịch toàn bộ (~560 batch)
python scripts/t74_groq_translate_places.py --force --limit=N  # single-pass xử lý lại row t74_groq
```

## Tests (18/18 PASS)

`tests/test_t74_groq_translate_places.py` (red-team, mock, DB temp):
guard Hán/normalize/prompt · stats · resume marker · run lại = 0 · English row cũng dịch ·
`--force` **single-pass** (guard loop vô hạn — row vừa update vẫn khớp scope force) ·
UPDATE không đè desc_source lạ (`other` → 0 row) · revert SQL khôi phục Hán + English gốc.

Chained vào `test:translation` (`npm run test:t74`). `npm run pipeline`: tất cả PASS
(guard/lint/test/translation/uat/compliance/gov/audit/e2e) — chỉ `e2e:runtime` EPERM
`.last-run.json` pre-existing (không thuộc T74).

## Chạy full trên VPS (14,000 rows)

1. **Bắt buộc `npm run guard` PASS** (SSOT repo root guard).
2. Cần `GROQ_API_KEY` (env) hoặc `groq_key` trong `data/llm_config.json`.
3. `python scripts/t74_groq_translate_places.py --stats` (14,000 chưa dịch).
4. `python scripts/t74_groq_translate_places.py --limit=200` (smoke live).
5. `python scripts/t74_groq_translate_places.py` (overnight, tự resume; Ctrl+C an toàn).

## Rollback (khôi phục bản gốc)

```sql
UPDATE place_desc_vi_draft
SET desc_vi_draft=d.note, desc_source='dila_note_zh', updated_at=datetime('now')
FROM places_dila d
WHERE d.id=place_desc_vi_draft.place_id AND place_desc_vi_draft.desc_source='t74_groq';
```

> Lưu ý khó: SQLite `UPDATE ... FROM` KHÔNG cho alias target (`UPDATE x pd FROM` → "near pd" syntax error).
> Viết đúng dạng `UPDATE place_desc_vi_draft SET ... FROM places_dila d WHERE d.id=place_desc_vi_draft.place_id`.

## Git: <sha_T74>
