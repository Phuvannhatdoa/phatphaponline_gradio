---
id: T49
title: Place VI_NAME Character Pipeline Fix — Char Map Errors + Confidence Upgrade
module: Place Authority / Việt hóa
priority: high
status: done
depends_on: [T24]
created: 2026-08-25
updated: 2026-08-27
done_when: Tất cả VI_NAME entries nâng confidence 0.5→0.65; char mapping sai đã fix; 690 entries lỗi đã flag
---

# T49 — Place VI_NAME Character Pipeline Fix

## Vấn Đề

Toàn bộ 118,293 VI_NAME entries được tạo bởi character-level Hán→Việt auto-transliterate.
Pipeline hiện tại có 2 lỗi format hệ thống:

### Lỗi 1 — Capitalization sai

```
Hiện tại (sai):  "thiếu lâm tự"  hoặc  "Thiếu lâm tự"
Đúng:            "Thiếu Lâm Tự"
```

Vietnamese place names: **mỗi âm tiết đều viết hoa** (Title Case cho tên riêng).

### Lỗi 2 — Buddhist suffix không chuẩn

Character pipeline transliterate thô:
- `寺` → `tự` (chữ thường) — nên là `Tự` trong ngữ cảnh tên riêng
- `院` → `viện` — nên là `Viện`
- `山` → `sơn` — nên là `Sơn`

Nhưng quan trọng hơn: convention PG Việt Nam dùng đúng âm đọc:

| Hán | Âm pipeline | Convention PG VN | Ghi chú |
|-----|------------|-----------------|---------|
| 寺 | tự | **Tự** | Đúng âm, chỉ cần capitalize |
| 院 | viện | **Viện** | Đúng |
| 山 | sơn | **Sơn** | Đúng |
| 塔 | tháp | **Tháp** | Đúng |
| 宮 | cung | **Cung** | Đúng |
| 觀 | quán | **Quán** | Đúng |
| 廟 | miếu | **Miếu** | Đúng |
| 庵 | am | **Am** | Đúng — Am (không phải Nham) |
| 祠 | từ | **Từ** | Đúng — Từ đường |
| 堂 | đường | **Đường** | Đúng — Phật đường |

## Impact

| Metric | Trước T49 | Sau T49 |
|--------|-----------|---------|
| Entries conf=0.5 | 118,293 | 0 |
| Entries conf=0.65 | 0 | **118,293** |
| Format đúng (Title Case) | ~? | ~100% |

**T49 là task ROI cao nhất trong chuỗi T47-T49:** chỉ 1 ngày, fix 118K entries.

## Implementation

```python
# scripts/t49_place_vi_pipeline_fix.py

import sqlite3, re, unicodedata

# Vietnamese title case: capitalize mỗi âm tiết
def vi_title_case(s: str) -> str:
    if not s:
        return s
    # Split by space, capitalize first letter of each token
    tokens = s.split()
    result = []
    for tok in tokens:
        if tok:
            # Capitalize first character (unicode-aware)
            result.append(tok[0].upper() + tok[1:])
    return ' '.join(result)

# Buddhist suffix normalization (không cần — title case đã xử lý)
# Nhưng check một số âm đọc sai cần sửa thủ công:
KNOWN_FIXES = {
    ' am ': ' Am ',
    ' nham ': ' Nham ',  # 岩 đọc là Nham, không phải Am
}

conn = sqlite3.connect('data/lineage.db')

cur = conn.execute('''
    SELECT id, content FROM zqlocal_content
    WHERE content_type = "VI_NAME" AND confidence = "0.5"
''')

updates = []
for row_id, content in cur:
    if not content:
        continue
    fixed = vi_title_case(content)
    # Apply known fixes
    for old, new in KNOWN_FIXES.items():
        fixed = fixed.replace(old, new)
    if fixed != content:
        updates.append((fixed, '0.65', 'pipeline_fix_t49', row_id))
    else:
        # Already correct format — just upgrade confidence
        updates.append((content, '0.65', 'pipeline_fix_t49', row_id))

print(f"Sẽ update {len(updates)} entries")
changed = sum(1 for u in updates if u[0] != conn.execute(
    'SELECT content FROM zqlocal_content WHERE id=?', (u[3],)
).fetchone()[0])
print(f"Trong đó nội dung thay đổi: {changed}")

import sys
if '--apply' in sys.argv:
    # Backup trước
    conn.executemany('''
        UPDATE zqlocal_content
        SET content = ?, confidence = ?, source_note = ?
        WHERE id = ? AND confidence = "0.5"
    ''', updates)
    conn.commit()
    print(f"Done. Updated {conn.total_changes} rows.")
```

## Thứ Tự Khuyến Nghị

**T49 nên chạy TRƯỚC T47:**
- T49 fix format → tên đã đúng Title Case
- T47 verify → so sánh với lexicon.term (vốn cũng Title Case)
- Match rate T47 sẽ tăng sau khi T49 chuẩn hóa

## Scope Limits

- KHÔNG thay đổi âm đọc của ký tự (chỉ capitalize, không transliterate lại)
- KHÔNG sửa entries đã có confidence > 0.5 (giữ nguyên T47/T48 đã verify)
- KHÔNG sửa schema hay structure `zqlocal_content`
- Dry-run bắt buộc trước `--apply`

## Kết Quả Thực Tế (2026-08-27)

**Phát hiện bổ sung:** Premise sai — data đã Title Case từ trước. Vấn đề thực là char mapping sai trong `hanviet_fallback`.

**Chars sai đã fix (thêm vào custom_hanviet_override):**
| Char | Fallback (sai) | Override (đúng) |
|------|---------------|-----------------|
| 永 | vắng | **Vĩnh** |
| 澄 | chừng | **Trừng** |
| 觀 | quan | **Quán** |

**DB changes:**

| Metric | Trước | Sau | Ghi chú |
|--------|-------|-----|---------|
| custom_hanviet_override rows | 2,448 | 2,451 | +3 |
| zqlocal conf=0.5 | 118,293 | 690 | 690 còn lại = untranslated chars |
| zqlocal conf=0.65 | 0 | 116,514 | clean machine quality |
| zqlocal conf=0.75 | 0 | 1,089 | re-transliterated (永/澄/觀 fixed) |
| namevi_map_places updated | - | 1,091 | cùng 3 chars |

**Revert:** `cp docs/sessions/2026-08-27/lineage_pre_T49.db.bak data/lineage.db`

## Acceptance Criteria

- [x] `scripts/t49_charmap_fix.py` viết xong với dry-run mode
- [x] Dry-run xem sample changes — hợp lý (Vắng→Vĩnh, Quan→Quán)
- [x] Backup DB: `docs/sessions/2026-08-27/lineage_pre_T49.db.bak`
- [x] Chạy `--apply`: 116,514 entries conf→0.65, 1,089 entries conf→0.75
- [x] 690 entries untranslated chars đã flag (`generated_by='has_untranslated_chars'`)
- [x] custom_hanviet_override +3 entries (永/澄/觀)
- [x] Cập nhật session log 2026-08-27

## Thứ Tự Implement Chuỗi T47–T49

```
T49 (fix format, conf 0.5→0.65)
  ↓
T47 (verify vs lexicon, conf 0.65→0.75/0.85)
  ↓
T48 (reverse index từ definitions, thêm ~200 pairs mới)
```

## Liên Quan

- T47: Place VI_NAME verification (chạy SAU T49)
- T48: Reverse index từ lexicon.definition
- T46: Tương tự cho Person name_vi — T49 là bản place của T46
- T24: `zqlocal_content` layer architecture
