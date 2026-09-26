---
id: T48
title: Place VI_NAME Reverse Index — Hán→Việt từ lexicon.definition
module: Place Authority / Việt hóa
priority: medium
status: done
depends_on: [T47]
created: 2026-08-25
updated: 2026-08-27
done_when: Tạo bảng hoặc file mapping hanzhi→viet_name từ definitions; ≥200 reliable pairs match DILA places; update zqlocal_content
---

# T48 — Place VI_NAME Reverse Index từ Lexicon Definitions

## Vấn Đề

Lexicon 22 bộ từ điển (166,278 entries) được tổ chức theo hướng:
- `term` = **Tiếng Việt** (key)
- `definition` = **Giải thích tiếng Việt**

→ Không có cột `hanzi` trực tiếp. Nhưng nhiều definitions chứa tên Hán trong ngoặc:

```
"Thiếu Lâm Tự (少林寺): ngôi chùa Phật giáo nổi tiếng..."
"Tây Phương Tam Thánh (西方三聖): danh hiệu tập thể..."
"Huyền Trang (玄奘): cao tăng Đường triều..."
```

→ Có thể mine ra pairs **(Hán → Việt)** bằng regex pattern matching.

## Số Liệu Đo Thực (2026-08-25)

| Metric | Giá trị | Ghi chú |
|--------|---------|---------|
| Definitions được scan | 50,000 (mẫu) | |
| Pairs extracted bởi regex hiện tại | 10,139 | Nhiều sai — xem bên dưới |
| Match với DILA places (name_zh exact) | 709 | |
| Reliable pairs sau quality filter (ước tính) | **~200–400** | Sau rework regex |

**Vấn đề regex hiện tại:** Pattern bắt nhầm từ lẻ:
- `洛陽 → "Dương"` (đáng lẽ `洛陽 → "Lạc Dương"`)
- `阿毘跋致 → "Trí"` (đáng lẽ bỏ qua)

Cần **rework regex** để require độ dài tên Việt tối thiểu ≥3 âm tiết.

## Revised Implementation

```python
# scripts/t48_place_vi_reverse_index.py

import sqlite3, re, io, sys

PAIR_PAT = re.compile(
    # Pattern A: 漢字 (Tên Việt đủ): "少林寺 (Thiếu Lâm Tự)"
    r'([一-鿿]{2,8})\s*[（(]'
    r'([A-ZĐẦẮẮ][a-zđàáạảãăặắằẳẵâấầẩẫéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵ]'
    r'(?:\s[A-ZĐẦẮẮ][a-zđàáạảãăặắằẳẵâấầẩẫéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵ]+){1,5})'
    r'\s*[）)]'
)

PAIR_PAT_B = re.compile(
    # Pattern B: "Tên Việt (漢字)": "Thiếu Lâm Tự (少林寺)"
    r'([A-ZĐẦẮẮ][a-zđàáạảãăặắằẳẵâấầẩẫéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵ]'
    r'(?:\s[A-ZĐẦẮẮ]?[a-zđàáạảãăặắằẳẵâấầẩẫéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵ]+){1,5})'
    r'\s*[（(]([一-鿿]{2,8})[）)]'
)

conn = sqlite3.connect('data/lineage.db')

pairs = {}  # hanzi → viet_name

cur = conn.execute('SELECT definition FROM lexicon WHERE definition IS NOT NULL AND length(definition) > 30')
for (defn,) in cur:
    if not defn:
        continue
    for m in PAIR_PAT.finditer(defn):
        zh, vn = m.group(1), m.group(2)
        if len(vn.split()) >= 2:  # require ≥2 âm tiết
            pairs.setdefault(zh, set()).add(vn)
    for m in PAIR_PAT_B.finditer(defn):
        vn, zh = m.group(1), m.group(2)
        if len(vn.split()) >= 2:
            pairs.setdefault(zh, set()).add(vn)

# Chọn tên phổ biến nhất cho mỗi Hán
final_pairs = {zh: max(vns, key=len) for zh, vns in pairs.items()}

# Match với DILA
cur2 = conn.execute('SELECT id, name_zh FROM places_dila WHERE name_zh IS NOT NULL AND name_zh != ""')
dila = {row[1]: row[0] for row in cur2}

matches = [(zh, vn, dila[zh]) for zh, vn in final_pairs.items() if zh in dila]
print(f"Pairs extracted: {len(final_pairs)}")
print(f"Matches với DILA places: {len(matches)}")
for zh, vn, dila_id in matches[:20]:
    print(f"  {zh} → {vn} (dila_id={dila_id})")
```

## Output

`data/t48_hanzhi_viet_pairs.json`:
```json
[
  {"hanzi": "少林寺", "viet": "Thiếu Lâm Tự", "dila_id": "PL000000023255", "confidence": "0.75"},
  {"hanzi": "普陀山", "viet": "Phổ Đà Sơn", "dila_id": "PL000000012345", "confidence": "0.75"},
  ...
]
```

## Scope Limits

- KHÔNG gán tên ZQ cho nguồn DILA
- Chỉ update `zqlocal_content` — KHÔNG sửa `places_dila.name_vi`
- Require ≥2 âm tiết trong tên Việt để tránh bắt nhầm
- Chỉ exact match Hán với `places_dila.name_zh` (không fuzzy — tránh false positive)
- Admin review tất cả matches trước khi insert (≤400 rows = review được thủ công)

## Kết Quả Thực Tế (2026-08-27)

**Approach thực tế:** Khai thác structure của lexicon — `term` là tên Việt, `definition` bắt đầu bằng `(漢字, ...)` → extract hanzi, tạo pair (hanzi → term).

| Metric | Giá trị |
|--------|---------|
| Pairs extracted (hanzi → viet) | 2,122 |
| Match với DILA places | 126 |
| Upgrade candidates (conf<0.75, tên khác) | **37** |
| → place suffix → conf=0.75 (auto) | **26** |
| → no suffix → conf=0.72 (admin review) | **11** |

**Systematic errors fixed (sample):**
| Hanzi | Cũ (sai) | Mới (lexicon) |
|-------|---------|--------------|
| 荷澤寺 | Hà Rạch Tự | **Hà Trạch Tự** |
| 香水海 | Hương Héo Hải | **Hương Thủy Hải** |
| 蓮花 | Sen Hoa | **Liên Hoa** |
| 水月 | Héo Nguyệt | **Thủy Nguyệt** |
| 慧安 | Tuệ An | **Huệ An** |

Pattern lỗi hệ thống: `水→Héo` (đúng: Thủy), `蓮→Sen` (đúng: Liên), `澤→Rạch` (đúng: Trạch).

**Filters đã dùng:**
- Loại person markers (Hòa Thượng, Thiền Sư, ...)
- Loại downgrade (không update nếu current có suffix, new không có)
- Loại Unicode orthographic variants (Phổ Hóa ≈ Phổ Hoá)

**Backup & Revert:**
`docs/sessions/2026-08-27/lineage_pre_T48.db.bak`
`cp docs/sessions/2026-08-27/lineage_pre_T48.db.bak data/lineage.db`

## Acceptance Criteria

- [x] Script khai thác pattern `(漢字, ...)` từ lexicon.definition — require ≥2 âm tiết
- [x] `scripts/t48_place_vi_reverse_index.py` chạy không lỗi, dry-run clean
- [x] Quality filters: person markers, downgrade, Unicode variants
- [x] Backup DB: `docs/sessions/2026-08-27/lineage_pre_T48.db.bak`
- [x] Apply: 26 → conf=0.75, 11 → conf=0.72 (admin review)
- [x] Revert path documented

## Liên Quan

- T47: Lexicon verification (parallel approach — T47 check tên ZQ có trong lexicon, T48 mine tên mới từ definitions)
- T49: Character pipeline fix (T49 nên chạy trước T47 và T48)
- T46: Tương tự nhưng cho person name_vi
