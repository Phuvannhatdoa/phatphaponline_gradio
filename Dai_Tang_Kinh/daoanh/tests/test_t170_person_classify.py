# -*- coding: utf-8 -*-
"""T170 — unit tests classify_person_diff + preprocess R2/R3/R4 (SPEC §3.2 + §3bis).

Chạy: python -X utf8 tests/test_t170_person_classify.py   (không cần DB, không cần API key)
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.t170_classify import (  # noqa: E402
    classify_person_diff, split_brackets, fold_cjk, extract_vi_core,
)

PASS = 0
FAIL = 0


def check(name, cond, detail=''):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f'  ✅ {name}')
    else:
        FAIL += 1
        print(f'  ❌ {name} {detail}')


print('=== T170 R2 — split_brackets (stack lồng) ===')
clean, meta, unc = split_brackets('一行(俗姓張, 一作張遂(唐))')
check('R2 lồng: clean_zh="一行"', clean == '一行', repr(clean))
check('R2 lồng: meta giữ cả 2 span', '俗姓張' in meta and '一作張遂(唐)' in meta, repr(meta))
check('R2 lồng: is_uncertain=0', unc == 0, repr(unc))

clean, meta, unc = split_brackets('一行(未詳')
check('R2 chưa đóng ngoặc → is_uncertain=1', unc == 1, repr(unc))
check('R2 chưa đóng ngoặc: clean sạch', clean == '一行', repr(clean))

print('\n=== T170 R3 — fold_cjk ===')
folded, changed = fold_cjk('惠能')
check('R3 惠→慧', folded == '慧能' and changed, repr(folded))
folded, changed = fold_cjk('慧能')
check('R3 không đổi khi canonical', folded == '慧能' and not changed, repr(folded))

print('\n=== T170 R4 — extract_vi_core (title loop multi-token) ===')
check('R4 prefix: "Tam Tạng Pháp Sư Huyền Trang" → "huyen trang"',
      extract_vi_core('Tam Tạng Pháp Sư Huyền Trang') == 'huyen trang',
      repr(extract_vi_core('Tam Tạng Pháp Sư Huyền Trang')))
check('R4 suffix: "Huệ Năng Thiền Sư" → "hue nang"',
      extract_vi_core('Huệ Năng Thiền Sư') == 'hue nang',
      repr(extract_vi_core('Huệ Năng Thiền Sư')))
check('R4 không cắt khi không có title',
      extract_vi_core('Thanh Vân') == 'thanh van', repr(extract_vi_core('Thanh Vân')))

print('\n=== T170 classify_person_diff — ưu tiên Sanskrit / title / fallback ===')
got, reason, hint = classify_person_diff('菩提達磨', 'Bồ Đề Đạt Ma', 'Bồ Đề Đạt Ma')
check('Sanskrit khớp → NONE + auto_verified_sanskrit',
      got == 'NONE' and hint == 'auto_verified_sanskrit', f'{got}/{hint} · {reason}')

got, reason, hint = classify_person_diff('菩提達磨', 'Bồ Đề Đạt Ma', 'Đạt Ma')
check('Sanskrit reading lệch → SANSKRIT_VARIANT',
      got == 'SANSKRIT_VARIANT', f'{got} · {reason}')

got, reason, hint = classify_person_diff('菩提達多', 'Bồ Đề Đạt Đa', 'Bồ Đề Đạt Đa')
check('indicator 菩提 không khớp registry → SANSKRIT_UNMAPPED (needs_lexicon_review)',
      got == 'SANSKRIT_UNMAPPED' and hint == 'needs_lexicon_review', f'{got}/{hint} · {reason}')

got, reason, hint = classify_person_diff('慧遠', 'Thích Huệ Viễn', 'Huệ Viễn')
check('core bằng nhau khác title → TITLE_VARIANT + auto_title_aligned',
      got == 'TITLE_VARIANT' and hint == 'auto_title_aligned', f'{got}/{hint} · {reason}')

got, reason, hint = classify_person_diff('降龍', 'Giáng Long', 'Hàng Long')
check('fallback R1: đa âm 降 giáng↔hàng → POLYPHONIC_CHAR',
      got == 'POLYPHONIC_CHAR', f'{got} · {reason}')

got, reason, hint = classify_person_diff('開元路', 'Khai Nguyên Lộ', 'KHAI NGUYÊN LỘ ')
check('format-only lệch → FORMAT_NORMALIZED + auto_verified',
      got == 'FORMAT_NORMALIZED' and hint == 'auto_verified', f'{got}/{hint} · {reason}')

got, reason, hint = classify_person_diff('一行', 'Nhất Hạnh', 'Nhất Hạnh')
check('đồng nhất → NONE', got == 'NONE', f'{got} · {reason}')

print(f'\nT170 classify_person_diff: {PASS} PASS · {FAIL} FAIL')
sys.exit(1 if FAIL else 0)