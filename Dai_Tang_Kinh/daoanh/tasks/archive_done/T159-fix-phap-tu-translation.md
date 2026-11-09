---
id: T159
title: "Fix 法嗣 → pháp tự trong pipeline dịch DILA card"
module: translation
priority: high
status: done
depends_on: [T158, T123]
created: 2026-09-21
updated: 2026-09-21
done_when: |
  1. translation_glossary có 法嗣→pháp tự (is_locked=1)
  2. Post-edit regex xử lý "Pháp嗣" → "Pháp tự" trong output LLM
  3. 3 cached records (A020035, A020037, A020039) đã được patch
  4. Không còn chuỗi "嗣" Hán văn trong bất kỳ bản dịch tiếng Việt nào
---

## Bug description

**Triệu chứng**: DILA card bio_concise_vi chứa "Pháp嗣" thay vì "pháp tự".
- A020039: `bio_han = "孝義性空禪師法嗣。"` → `bio_vi = "Pháp嗣 của Thiền Sư Cát Châu Tính Không."`
- A020037: `"Pháp嗣 của Thiền Sư Thiên Nhiên ở núi Đan Hà"`
- A020035: `"Pháp嗣 của Thiền Sư Thiên Nhiên Đan Hà"`

**Root cause**: `translation_rules` có `TERM_PHAP_SI` active nhưng chỉ là text instruction —
AI split 法→Pháp, để 嗣 nguyên Hán. 法嗣 không có trong `translation_glossary` (GLOSSARY LOCK)
nên resolver không inject trước khi call LLM.

**Fix**: 3-part:
1. Add 法嗣→pháp tự vào `translation_glossary` (is_locked=1) → GlossaryResolver inject vào LOCK
2. Post-edit regex sau LLM output: `Pháp嗣` / `pháp嗣` → `Pháp tự` / `pháp tự`
3. Patch 3 cached records

## Acceptance criteria

- [x] translation_glossary: id tồn tại với term_zh='法嗣', term_vi='pháp tự', is_locked=1
- [x] Post-edit function `_post_edit_hanzi_leakage` trong app.py
- [x] 3 cache records patched: không còn "嗣" trong translated_text
- [x] Validate: 3 cache records patched — A020039 = "Pháp tự của Thiền Sư Cát Châu Tính Không."
- [x] Syntax OK

## Done — Admin xác nhận: 2026-09-21
