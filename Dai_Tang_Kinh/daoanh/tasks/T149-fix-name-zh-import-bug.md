---
id: T149
title: "Fix bug import_dila_person lấy alt name thay vì main persName cho name_zh (28,273 rows sai)"
module: data-import
priority: critical
status: done
depends_on: [T148]
created: 2026-09-16
updated: 2026-09-16
done_when:
  - "[x] Xác định root cause: import script không check type='alternative', ghi đè name_zh bằng alt name cuối"
  - "[x] Fix import_dila_person.py: chỉ lấy persName không có type attribute"
  - "[x] Fix import_person_authority.py: dùng xml:id thật, skip type='alternative'"
  - "[x] Audit toàn bộ 48,673 rows: 28,255 (58%) bị sai"
  - "[x] Fix trực tiếp trên DB: 28,273 rows (28,255 alt name + 7 trailing space + 13 true mismatch) → correct"
  - "[x] Verify final: 48,611 match hoàn toàn, 62 giữ nguyên (XML non-CJK main name)"
  - "[x] Browser verified: A000001 (金總持) name_zh đúng, A002613 (道生) đúng"
---

## Mô tả

Toàn bộ 28,255/48,673 rows trong bảng `people` bị lưu sai `name_zh` — lưu alt name
(type="alternative") thay vì main persName từ DILA XML.

### Root cause

**`src_python/db/import_dila_person.py`** loop qua TẤT CẢ `persName` elements không phân
biệt `type`:

```python
# BUG (trước fix):
for name in names:
    lang = name.get('{http://www.w3.org/XML/1998/namespace}lang')
    text = (name.text or '').strip()
    if lang == 'zho-Hant' and text:
        name_zh = text  # ← overwrite mỗi lần, lấy element CUỐI (thường là alt name)
```

DILA XML format: phần tử `persName` đầu tiên = main canonical name (không có `type`);
các phần tử tiếp theo có `type="alternative"` = biệt hiệu, pháp hiệu, tên khác.

Ví dụ A000001 (金總持):
```xml
<persName xml:lang="zho-Hant">金總持</persName>         <!-- main -->
<persName xml:lang="zho-Hant" type="alternative">金揔持</persName>
<persName xml:lang="zho-Hant" type="alternative">寶輪大師</persName>
<persName xml:lang="zho-Hant" type="alternative">明因妙善普濟法師</persName>
```

Bug: DB lưu `明因妙善普濟法師` thay vì `金總持`.

### Fix trong code

**`src_python/db/import_dila_person.py`** (lines 72-89):
```python
# FIX: chỉ lấy main persName (không có type="alternative")
for name in names:
    lang = name.get('{http://www.w3.org/XML/1998/namespace}lang')
    ptype = name.get('type', '')  # '' = main, 'alternative' = alt
    text = (name.text or '').strip()
    if not ptype and text:  # ← chỉ xét khi không có type attribute
        if lang == 'zho-Hant' and not name_zh:
            name_zh = text
        elif lang == 'vie' and not name_vi:
            name_vi = text
        elif lang == 'eng' and not name_en:
            name_en = text
        elif lang == 'jpn' and not name_ja:
            name_ja = text
if not name_zh:
    continue
```

**`src_python/etl/import_person_authority.py`** (lines 44-56):
```python
# FIX: dùng xml:id thật thay vì sequential, skip alt names
pid = p.get('id') or p.get('{http://www.w3.org/XML/1998/namespace}id')
if not pid:
    continue
name = ''
for pn in p.findall('persName'):
    if pn.get('type', '') == 'alternative':
        continue  # skip alt names
    if pn.text and pn.text.strip():
        name = pn.text.strip()[:100]
        break
```

## DB Fix trực tiếp (2026-09-16)

Vì DB hiện tại có dữ liệu curated (`bio_vi`, `source_id`, quan hệ lineage v.v.) không có trong
XML, KHÔNG rebuild lại table mà fix trực tiếp:

| Bước | Script | Rows fixed |
|------|--------|-----------|
| Audit | `check_name_zh2.py` | 28,255 mismatch phát hiện |
| Fix alt name | `fix_name_zh.py` | 28,255 → SET name_zh = XML main name |
| Analyze 82 còn lại | `analyze_82.py` | 7 trailing space + 62 non-CJK XML (giữ) + 13 mismatch |
| Fix trailing space | `analyze_82.py` | 7 → strip trailing space |
| Fix 13 mismatch | `fix_13.py` | 13 → SET name_zh = XML main name |
| **Tổng** | | **28,273 rows corrected** |

### Kết quả verify cuối (`verify_final.py`)
- 48,611 rows: DB == XML main name ✓
- 62 rows: XML main name là non-CJK (Japanese/Sanskrit/Pali/Latin) → giữ CJK DB value ✓
- 0 rows sai còn lại

## Lưu ý quan trọng: name_vi cần re-seed

28,273 rows đã fix `name_zh` nhưng `name_vi` cũ được tạo bằng phiên âm từ `name_zh` sai
→ `name_vi` cho 28,273 rows này cũng sai.

**Việc cần làm sau**: chạy `seed_persons_namevi.py` lại cho 28,273 rows bị ảnh hưởng.
Tracking: tạo task riêng T150.

## Rollback

**Code** (script fix): `git revert --no-edit <sha_commit3>` (commit "fix: T149 import name_zh")
→ phục hồi 2 script về trạng thái bug.

**DB data**: không thể rollback qua git (SQLite binary không track trong git).
Để rollback DB, cần restore từ backup snapshot hoặc chạy lại import đầy đủ với script cũ
(không khuyến nghị — sẽ mất bio_vi và dữ liệu curated).
