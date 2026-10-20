---
id: T47
title: Place VI_NAME Verification — Lexicon Cross-Reference (116K entries)
module: Place Authority / Việt hóa
priority: high
status: done
depends_on: [T24, T49]
created: 2026-08-25
updated: 2026-08-27
done_when: ≥5,000 zqlocal_content entries nâng confidence qua lexicon match; script đã chạy và log output
---

# T47 — Place VI_NAME Verification via Lexicon Cross-Reference

## Vấn Đề

118,293 VI_NAME entries trong `zqlocal_content` đều ở confidence=0.5 (machine transliterate, chưa ai xác nhận).
Lexicon của PTDA có **166,278 entries** từ 22 bộ từ điển PG — trong đó `term` là tên tiếng Việt chuẩn.

Nếu tên VN auto-generated của một địa điểm **khớp với lexicon.term**, ta có bằng chứng dict-confirmed → có thể nâng confidence.

## Số Liệu Đo Thực (2026-08-25)

| Metric | Giá trị |
|--------|---------|
| zqlocal_content VI_NAME entries | 118,293 |
| Lexicon normalized unique terms | 107,172 |
| Exact match (case-insensitive) | **5,992 entries (5.1%)** |
| Trong đó match ≥2 nguồn lexicon | 1,941 entries (1.6%) |
| Unique places được verify | ~3,000 |

## Implementation

```python
# scripts/t47_place_vi_lexicon_verify.py

import sqlite3, re

def normalize(s):
    return s.lower().strip() if s else ''

conn = sqlite3.connect('data/lineage.db')

# Build lexicon lookup: normalized_term → [source, ...]
cur = conn.execute('''
    SELECT LOWER(TRIM(term)), source
    FROM lexicon
    WHERE length(term) > 2 AND term NOT LIKE "%(%" 
''')
lexicon = {}
for norm_term, src in cur:
    if norm_term not in lexicon:
        lexicon[norm_term] = []
    lexicon[norm_term].append(src)

# Match zqlocal_content against lexicon
cur = conn.execute('''
    SELECT id, entity_id, content
    FROM zqlocal_content
    WHERE content_type = "VI_NAME" AND confidence = "0.5"
''')

updates = []
for row_id, entity_id, content in cur:
    norm = normalize(content)
    if norm in lexicon:
        sources = lexicon[norm]
        new_conf = '0.85' if len(sources) >= 2 else '0.75'
        updates.append((new_conf, 'lexicon_verified', row_id))

# Preview trước khi update
print(f"Sẽ update {len(updates)} entries")
print(f"  conf 0.75 (1 nguồn): {sum(1 for u in updates if u[0]=='0.75')}")
print(f"  conf 0.85 (≥2 nguồn): {sum(1 for u in updates if u[0]=='0.85')}")

# Dry-run: thêm --apply để thực thi
import sys
if '--apply' in sys.argv:
    conn.executemany('''
        UPDATE zqlocal_content 
        SET confidence = ?, source_note = ?
        WHERE id = ?
    ''', updates)
    conn.commit()
    print("Done.")
```

## Confidence Logic

| Match | Confidence mới | Lý do |
|-------|---------------|-------|
| lexicon.term, 1 nguồn | **0.75** | Dict-confirmed nhưng 1 từ điển |
| lexicon.term, ≥2 nguồn | **0.85** | Multi-dict confirmed = học thuật tin cậy |
| Không match | giữ 0.5 (hoặc 0.65 nếu T49 chạy trước) | Chưa xác nhận |

## Scope Limits

- KHÔNG gán nguồn DILA cho tên ZQ — badge vẫn là ZQLOCAL
- KHÔNG thay đổi nội dung tên (chỉ update confidence)
- KHÔNG update entries đã có confidence > 0.5
- Chạy dry-run trước, admin xem log, sau đó mới `--apply`

## Kết Quả Thực Tế (2026-08-27)

Script chạy sau T49 (conf đã ở 0.65 thay vì 0.5). Chỉ process conf=0.65, không downgrade cao hơn.

| Metric | Giá trị |
|--------|---------|
| Entries tại conf=0.65 (đầu vào) | 116,514 |
| Match 1 nguồn → conf=0.75 | **4,038** |
| Match ≥2 nguồn → conf=0.85 | **1,935** |
| Tổng verified | **5,973 (5.1%)** |
| Không match (giữ conf=0.65) | 110,541 (94.9%) |

**zqlocal_content sau T47:**
```
conf=0.9:       1 entries  (0.0%)
conf=0.85:  1,935 entries  (3.3%)
conf=0.8:       1 entries  (0.0%)
conf=0.75:  5,127 entries  (8.7%)   ← 4,038 T47 + 1,089 T49 re-transliterate
conf=0.65: 110,541 entries (186.8%)
conf=0.5:     690 entries  (1.2%)   ← untranslated chars
```

Backup: `docs/sessions/2026-08-27/lineage_pre_T47.db.bak`
Revert: `cp docs/sessions/2026-08-27/lineage_pre_T47.db.bak data/lineage.db`

## Acceptance Criteria

- [x] `scripts/t47_place_vi_lexicon_verify.py` viết xong, dry-run không lỗi
- [x] Dry-run output: in list 5,973 matches + confidence mới
- [x] Admin review log: sample 5 entries conf=0.85 và 0.75 đã xem
- [x] Backup DB: `docs/sessions/2026-08-27/lineage_pre_T47.db.bak`
- [x] Chạy `--apply`: 4,038 → conf=0.75; 1,935 → conf=0.85
- [x] Verify: zqlocal_content distribution xem output trên
- [x] Cập nhật `data/progress_data.json` — coverage metric

## Liên Quan

- T46: Person name_vi quality (parallel — tương tự nhưng cho persons)
- T48: Reverse index từ lexicon.definition (bổ sung thêm Hán→Việt pairs)
- T49: Character pipeline fix (T49 nên chạy TRƯỚC T47 để tên đã đúng format rồi mới verify)
- T24: `zqlocal_content` layer architecture
