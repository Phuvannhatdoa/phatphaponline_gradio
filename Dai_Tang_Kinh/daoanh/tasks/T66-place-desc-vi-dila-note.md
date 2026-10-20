---
id: T66
title: "Place Description VI — DILA note (14,000 Chinese descriptions → place_desc_vi_draft)"
module: Place Authority / DILA
priority: medium
status: done
depends_on: [T48, T64]
created: 2026-08-27
updated: 2026-08-28
done_when: >
  ≥12,000 DILA places có bản ghi trong place_desc_vi_draft từ places_dila.note;
  bảng place_desc_vi_draft tồn tại;
  script có --dry-run, --apply, --revert;
  admin có thể review note tiếng Hán và copy → namevi_map_places.note_vi
---

# T66 — Place Description VI: DILA Note → Draft Table

## Phê Chuẩn

Phê chuẩn 2026-08-28. T66 tạo `place_desc_vi_draft` từ `places_dila.note`
(14,010 mô tả địa lý học thuật tiếng Hán của DILA).

## Pivot từ Kế Hoạch Gốc

**Kế hoạch gốc (T61):** Dùng lexicon ĐỊA DANH (15,863 entries).
**Kết quả audit 2026-08-28:** Lexicon ĐỊA DANH = khái niệm Phật học (Bồ Đề = giác ngộ,
Chân Như = suchness...), KHÔNG phải mô tả địa lý. Matches không usable.

**Nguồn thực chất hơn:** `places_dila.note` — 14,010 mô tả tiếng Hán từ DILA Authority:
- Mô tả lịch sử, địa lý, khảo cổ (ví dụ: "印度古國，詳址待考..." / "始建年代：公元...")
- Avg 70 chars, max 1,740 chars
- Đây là dữ liệu học thuật đáng tin từ DILA (không phải tự động sinh)

## Workflow Admin

```
places_dila.note (Hán)
    ↓ T66 copy → place_desc_vi_draft.desc_vi_draft (Hán, admin_approved=0)
    ↓ Admin đọc + tóm tắt/dịch
    ↓ Update desc_vi_draft (Việt) + admin_approved=1
    ↓ Copy → namevi_map_places.note_vi
```

## Schema

```sql
CREATE TABLE IF NOT EXISTS place_desc_vi_draft (
    place_id       TEXT PRIMARY KEY,  -- places_dila.id = namevi_map_places.dila_id
    name_vi        TEXT,              -- từ namevi_map_places
    name_zh        TEXT,              -- từ places_dila
    note_category  TEXT,              -- từ places_dila
    desc_vi_draft  TEXT,              -- ban đầu = places_dila.note (Hán); admin sẽ Việt hóa
    desc_source    TEXT,              -- 'dila_note_zh' | 'lexicon_diadanh'
    char_count     INTEGER,
    admin_approved INTEGER DEFAULT 0,
    admin_note     TEXT,
    created_at     TEXT,
    updated_at     TEXT
)
```

## Kết Quả Ước Tính

| Pass | Nguồn | Rows | Chất lượng |
|------|-------|------|-----------|
| Primary | `places_dila.note` | ~14,000 | ⭐⭐⭐ Học thuật DILA |
| Bonus | Lexicon ĐỊA DANH Pali source (Tu-Dien-Danh-Tu-Rieng-Pali) filtered | TBD | ⭐⭐ |

## Script

**File:** `scripts/t66_place_desc_vi_dila_note.py`

```
Usage:
    python scripts/t66_place_desc_vi_dila_note.py          # dry-run
    python scripts/t66_place_desc_vi_dila_note.py --apply  # insert vào DB
    python scripts/t66_place_desc_vi_dila_note.py --revert # xóa tất cả T66 rows
    python scripts/t66_place_desc_vi_dila_note.py --stats  # thống kê hiện tại
```

## Kết Quả Thực Thi (2026-08-28)

| Metric | Kết quả |
|--------|---------|
| Inserted | **14,000 rows** |
| Source | places_dila.note (tiếng Hán, học thuật DILA) |
| Avg char_count | 70 chars/entry |
| Admin approved | 0 (chờ review) |
| Top categories | 寺廟佛塔 5,093 / 歷史地名 2,645 / 地點 2,523 / 山峰 1,431 |

**Revert:** `python scripts/t66_place_desc_vi_dila_note.py --revert`  
**Log:** `data/t66_import_log.json`

## Acceptance Criteria

- [x] Audit: xác nhận lexicon ĐỊA DANH không phù hợp (2026-08-28)
- [x] `scripts/t66_place_desc_vi_dila_note.py` chạy OK với --dry-run
- [x] ≥12,000 rows → **14,000 ✓**
- [x] `desc_source='dila_note_zh'` ghi đúng cho từng row
- [x] `--revert` có thể xóa sạch T66 rows
- [ ] Admin review 30 samples → content usable cho translation
- [x] `namevi_map_places.note_vi` không bị tự động overwrite

## Liên Quan

- **T48 (Done):** Reverse index lexicon → DILA places (foundation)
- **T64:** Wikidata P571 import — `places_dila.note` thường có founding date info → T64b
- **T65 (Done):** Person Bio VI Phase 2 — same pattern, khác entity
- **T66b (Future):** Auto-translate 200 top places note_zh → note_vi via Gemini
- `namevi_map_places.note_vi`: destination column sau admin approve
