# -*- coding: utf-8 -*-
"""Hash-fill commit cho T209 + cap nhat so lieu da troi trong task doc.

T209 §4 ghi "15 slug / 22 file" va §8 ghi "L1=15, L2=15, L5=12" — do la so luc
2026-10-02 truoc khi cac session khac sua tiep. Bai nay ghi them bang "trang
thai hien tai" de agent sau khong phai do lai, va khong xoa so lieu lich su.
"""
import io
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REL = 'tasks/T209-ttl-empty-and-subject-collision-guard.md'
SHA = sys.argv[1] if len(sys.argv) > 1 else 'TBD'


def main():
    p = os.path.join(BASE, REL)
    s = io.open(p, encoding='utf-8').read()

    a = 'commit: TBD'
    b = 'commit: "%s"' % SHA
    if a in s:
        s = s.replace(a, b, 1)
    elif b not in s:
        print('[FAIL] khong tim thay truong commit')
        return 1

    marker = '\n## 8. C\u00f2n l\u1ea1i (c\u1ea7n Admin)'
    block = (
        '\n---\n\n## 8b. Tr\u1ea1ng th\u00e1i \u0111o \u0111\u1ecdc l\u1ea1i 2026-10-02 (sau commit `%s`)\n\n'
        'C\u00e1c con s\u1ed1 \u0111\u1ebd li\u1ec7t k\u1ec7 trong \u00a74/\u00a78 l\u00e0 **s\u1ed1 l\u00fac\n'
        '2026-10-02 s\u00e1ng**, \u0111\u00e3 c\u00e1c session kh\u00e1c s\u1eeda ti\u1ebfp. \u0110\u1ec3 **kh\u00f4ng**\n'
        's\u1eeda ngược \u0111\u1ec3 gi\u1eef l\u1ecbch s\u1eed ph\u00e1t hi\u1ec7n; b\u1ea3ng d\u01b0\u1edbi \u0111\u00e2y m\u1edbi:\n\n'
        '| Ch\u1ec1 | T209 ghi | Hi\u1ec7n t\u1ea1i |\n|---|---|---|\n'
        '| Corpus data file | 1.037 | **1.038** |\n'
        '| File 0 byte | 1 (`TS-Dai-Xa-Nhu-Truong`) | **0** |\n'
        '| Slug tr\u00f9ng (L7) | 15 slug / 22 file | **5 slug / 13 file** |\n'
        '| File URI sai | 22 | **8** (T211 \u0111\u00e3 s\u1eeda 7) |\n'
        '| Nh\u00e3n sai | 15 | **24** |\n'
        '| L1 / L2 | 15 / 15 | **11 / 13** |\n'
        '| L5 | 12 | **24** |\n\n'
        'Preflight: **BLOCKING 29** (L1 11 \u00b7 L2 13 \u00b7 L3 0 \u00b7 L6 0 \u00b7 L7 5) \u00b7\n'
        '**WARNING 24** (L4 0 \u00b7 L5 24).\n\n'
        '**C\u00e1c 5 slug L7 c\u00f2n l\u1ea1i** (\u0111\u1ec3u ti\u1ebfn s\u1eeda, \u0111\u00e3 c\u1ea3 5 slug \u0111\u1ec3u\n'
        'c\u1ee7a T209):\n\n'
        '| Slug tr\u00f9ng | File d\u00f9ng chung |\n|---|---|\n'
        '| `bach_van_khong_do` | `TS-Bach-Van-Khong-Do` (ch\u1ee1), '
        '`TS-Di-Phong-Kinh-Ninh`, `TS-Dot-Khong-Tri-Ban` |\n'
        '| `phong_huyet_dien_chieu` | `TS-Phong-Huyet-Dien-Chieu` (ch\u1ee7), '
        '`TS-Dai-Xa-Nhu-Truong`, `TS-Minh-Hoang-Tu-Dung`, `TS-Tuyet-Giau-Chon-Phac` |\n'
        '| `bach_truong_hoai_hai` | `TS-Bach-Truong-Hoai-Hai` (ch\u1ee7), `TS-Phuoc-Chau-Dai-An` |\n'
        '| `dao_ninh_dao_khoan` | `TS-Dao-Ninh-Dao-Khoan` (ch\u1ee7), `TS-Dai-Ninh-Dao-Khoan` |\n'
        '| `thach_cuu` | `TS-Thach-Cuu` (ch\u1ee7), `TS-Linh-Cuu` |\n\n'
        '\u0110\u1ec3u ch\u1ed1 **13 file** = 5 "ch\u1ee7 s\u1edf" (URI \u0111\u00fang) + **8 "k\u1ebf \u00e1p c\u00e1o"**\n'
        '(URI sai) \u2014 kh\u1edfp \u0111\u00fang v\u1edbi nh\u00f3m trong `docs/TTL-FILE-STATUS-REPORT.md` nh\u00f3m C=8.\n'
        '\u0110\u1ec3 8 file k\u1ebf \u00e1p c\u00e1o **\u0111\u1ec3u c\u1ea7n Admin duy\u1ec7t** \u0111\u1ec3 s\u1eeda.\n\n'
        '> **R\u1ea3t quan tr\u1ed9ng:** guard L6/L7 (`check_empty`, `check_subject_collision`) \u0111\u00e3\n'
        '> \u0111\u01b0\u1ecdc commit v\u00e0o `scripts/t204_ttl_preflight.py`. TTL **kh\u00f4ng git track**\n'
        '> n\u00ean 2 guard n\u00e0y l\u00e0 l\u01b0\u1edbi an to\u00e4n duy nh\u1ea5t \u2014 m\u1ea5t ch\u00fang c\u00f3 th\u00e1t s\u1ef1\n'
        '> m\u1ea5t d\u1eef li\u1ec7u.\n' % SHA
    )
    if '## 8b.' not in s:
        assert marker in s, 'khong tim thay moc §8'
        s = s.replace(marker, block + marker, 1)
    else:
        print('[SKIP] da co §8b')

    io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
    print('OK  %s  (commit=%s, them §8b)' % (REL, SHA))
    return 0


if __name__ == '__main__':
    sys.exit(main())
