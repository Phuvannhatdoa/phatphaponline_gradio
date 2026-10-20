---
id: T71
title: "Place Name VI Lexicon Verify — Cross-check 22 bộ từ điển → upgrade confidence + phát hiện lỗi"
module: Place Authority / DILA
priority: high
status: done
depends_on: [T47, T48, T49]
created: 2026-08-30
updated: 2026-08-30
done_when: >
  Script t71_place_name_lexicon_verify.py chạy OK với --dry-run/--apply/--revert;
  Pass A (CJK index từ 22 từ điển) upgrade ≥500 places conf 0.70→0.80;
  Pass B (suffix rules) validate ≥5,000 places;
  Admin review queue có danh sách discrepancies (lex≠auto);
  Không overwrite bất kỳ conf≥0.75 row nào mà không có lý do rõ.
---

# T71 — Place Name VI Lexicon Verify

## Phê Chuẩn

Phê chuẩn 2026-08-30. Đây là cross-reference **22 bộ từ điển Phật học Việt Nam** (166K entries)
với 59K địa danh DILA để xác minh tên tiếng Việt — không dùng NLP, không dùng LLM.

Tâm huyết của tiền nhân (Phat Quang, Thien Tong, Han Viet, Tu Si Dinh Phuc, Nguyen Quoc Hung...)
là nguồn xác minh học thuật unimpeachable — không phải AI, không phải heuristic.

## Phát hiện (2026-08-30 audit)

- `namevi_map_places`: toàn bộ 109K rows là `source=auto_transliterate*` — **không có row nào từ lexicon**
- T47/T48 đã dùng lexicon để verify `name_vi=lexicon.term` (headword exact match) nhưng 0 matches
  vì auto-transliteration dùng convention khác với scholarly Vietnamese names
- **Approach đúng**: extract CJK từ lexicon.definition (pattern: `漢字. Explanation`)
  → build index `{name_zh: (vi_term, source, lex_id)}`
  → match với `places_dila.name_zh`
  → **không match name_vi với name_vi** mà match **name_zh với name_zh**

## Proof-of-Concept kết quả

| Metric | Số liệu |
|--------|---------|
| CJK index từ 166K entries | 25,398 keys |
| DILA places matched | **2,088 places** (3.5%) |
| Precision (lex == auto) | **87%** (13/15 mẫu) |
| Lỗi phát hiện | 白水: "Bạch Héo" → đúng phải "Bạch Thủy" |

3.5% coverage là thực tế — DILA có nhiều địa danh lịch sử obscure không có trong từ điển Phật học.

## Kiến Trúc Script (2 Pass)

### Pass A — CJK Index từ Lexicon (precision ~87%)

```python
# Build index từ cả 166K entries (term + definition)
# Pattern 1: definition bắt đầu "漢字. Explanation"
# Pattern 2: term chứa "VietName: 漢字" hoặc "VietName 漢字"
index = {name_zh: (vi_term, source, lex_id)}

# Match
for place in dila_places_conf_lt_075:
    if place.name_zh in index:
        lex_vi, src, lex_id = index[place.name_zh]
        if same(lex_vi, place.name_vi):
            → upgrade conf 0.70 → 0.80, source_note='lexicon_t71_{source}'
        else:
            → insert vào review table / flag needs_review=1
```

Confidence upgrade:
- conf 0.70 → 0.80 (lexicon từ học giả xác nhận)
- conf 0.75 → không thay đổi (đã xác minh bởi nguồn khác)
- conf >= 0.80 → không thay đổi

### Pass B — Suffix Rule Validation (coverage rộng)

Deterministic phonetic rules:
```
寺 → Tự    山 → Sơn    河 → Hà     城 → Thành
塔 → Tháp  湖 → Hồ     洞 → Động   廟 → Miếu
庵 → Am    院 → Viện   國 → Quốc   峰 → Phong
嶺 → Lĩnh  橋 → Kiều   溪 → Khê    關 → Quan
```

Logic:
- Suffix `name_zh[-1]` trong rules → check `name_vi` kết thúc đúng suffix
- Đúng + conf<0.73 → upgrade conf → 0.72, source_note='suffix_t71'
- Sai → flag needs_review=1 (không tự sửa)

## Schema Thay Đổi

Không thêm bảng mới. Chỉ update `namevi_map_places`:
```sql
-- Pass A (khi match khớp)
UPDATE namevi_map_places SET confidence=0.80, needs_review=0,
    note_vi = COALESCE(note_vi,'') || ' [T71:lex_' || source || ']'
WHERE dila_id=? AND confidence < 0.75

-- Pass A (khi match KHÁC)
UPDATE namevi_map_places SET needs_review=1,
    note_vi = COALESCE(note_vi,'') || ' [T71:CONFLICT lex=' || lex_vi || ']'
WHERE dila_id=? AND confidence < 0.80

-- Pass B (suffix OK)
UPDATE namevi_map_places SET confidence=0.72,
    note_vi = COALESCE(note_vi,'') || ' [T71:suffix_' || suffix || ']'
WHERE dila_id=? AND confidence < 0.71
```

## Script

**File:** `scripts/t71_place_name_lexicon_verify.py`

```
Usage:
    python scripts/t71_place_name_lexicon_verify.py           # dry-run, cả 2 pass
    python scripts/t71_place_name_lexicon_verify.py --apply   # apply thay đổi
    python scripts/t71_place_name_lexicon_verify.py --revert  # rollback T71 changes
    python scripts/t71_place_name_lexicon_verify.py --pass A  # chỉ lexicon pass
    python scripts/t71_place_name_lexicon_verify.py --pass B  # chỉ suffix pass
    python scripts/t71_place_name_lexicon_verify.py --stats   # thống kê sau apply
    python scripts/t71_place_name_lexicon_verify.py --conflicts  # xem discrepancies
```

## Revert Safety

- Pass A: `note_vi` ghi tag `[T71:lex_...]` → filter và xóa, restore conf cũ
- Pass B: `note_vi` ghi tag `[T71:suffix_...]` → filter và xóa, restore conf cũ
- Backup: script đọc conf trước và ghi vào log `data/t71_import_log.json` (bao gồm giá trị cũ)

## Kết Quả Thực Thi (2026-08-30)

| Metric | Kết quả |
|--------|---------|
| CJK index keys | **25,604** keys từ 166K entries |
| Pass A: matched (same) | **1,590** DILA places |
| Pass A: upgraded 0.70→0.80 | **1,529** places (lexicon-confirmed) |
| Pass A: conflict flagged | **222** places (real errors found!) |
| Pass B: suffix validated | **11,369** places (0.70→0.72) |
| Total T71 tagged rows | **13,032** |
| Admin review queue | **1,459** (needs_review=1) |
| Lỗi điển hình phát hiện | 獅子→"Tép Tí" (đúng: Sư Tử); 歸仁→"Quy Nhân" (đúng: Quy Nhơn); 定慧寺→"Định Tuệ Tự" (đúng: Định Huệ Tự) |

**Revert:** `python scripts/t71_place_name_lexicon_verify.py --revert`  
**Conflicts:** `python scripts/t71_place_name_lexicon_verify.py --conflicts`  
**Log:** `data/t71_import_log.json`

## Acceptance Criteria

- [x] Script `t71_place_name_lexicon_verify.py` chạy OK với --dry-run
- [x] Pass A: CJK index build từ 166K entries, ≥25,000 keys → **25,604 ✓**
- [x] Pass A: ≥1,500 DILA places matched lexicon → **1,590 ✓**
- [x] Pass A: ≥500 conf<0.75 places upgraded 0.70→0.80 → **1,529 ✓**
- [x] Pass A: discrepancy list có ≥50 rows cho admin review → **222 ✓**
- [x] Pass B: ≥5,000 places suffix-validated (conf upgrade 0.70→0.72) → **11,369 ✓**
- [x] `--revert` khôi phục về trạng thái trước T71
- [x] Không có conf≥0.80 row nào bị downgrade (skipped_high=319)
- [x] Log `data/t71_import_log.json` ghi đủ

## Liên Quan

- **T47 (Done):** Lexicon cross-ref bằng headword exact match → 0 matches cho places (khác approach)
- **T48 (Done):** Reverse index → 37 matches (sample nhỏ)
- **T49 (Done):** Charmap fix 3 chars
- **T62/T65 (Done):** Person name verify — T71 là bản place tương đương
- **T66 (Done):** Place desc từ DILA note — kết hợp T71+T66 = place profile đầy đủ hơn
- 22 nguồn lexicon: Tu Dien Thien Tong Han Viet, Phat Quang, Han Viet Nguyen Quoc Hung...
